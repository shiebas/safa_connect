from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import resolve
from django.utils import timezone
from accounts.models import DocumentAccessLog
from utils.document_watermark import DocumentWatermarker
import os
import tempfile

class AdminFormErrorMiddleware(MiddlewareMixin):
    """
    Middleware to handle admin form errors gracefully
    """
    def process_exception(self, request, exception):
        # Handle admin form errors
        if request.path.startswith('/admin/') and hasattr(exception, 'message_dict'):
            # Add error messages for admin forms
            for field, errors in exception.message_dict.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            
            # Redirect back to the form
            return HttpResponseRedirect(request.get_full_path())
        
        # Let other exceptions pass through
        return None
    
    def process_request(self, request):
        return None
    
    def process_response(self, request, response):
        return response


class DocumentAccessMiddleware(MiddlewareMixin):
    """
    Middleware to track document access and apply watermarks
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.watermarker = DocumentWatermarker()
        # Document paths that should be tracked and watermarked
        self.tracked_paths = [
            '/media/id_documents/',
            '/media/passport_documents/', 
            '/media/sa_passport_documents/',
            '/media/profile_pictures/',
            '/media/certification_documents/',
            '/media/club_documents/',
        ]
        super().__init__(get_response)
    
    def process_request(self, request):
        """Check if this is a document download request"""
        if not request.user.is_authenticated:
            return None
            
        # Check if this is a tracked document path
        is_tracked_document = any(path in request.path for path in self.tracked_paths)
        
        if is_tracked_document and request.method == 'GET':
            # This is a document access attempt
            return self._handle_document_access(request)
        
        return None
    
    def _handle_document_access(self, request):
        """Handle document access with logging and watermarking"""
        try:
            # Get the file path from URL
            file_path = request.path.replace('/media/', '')
            full_path = os.path.join('media', file_path)
            
            if not os.path.exists(full_path):
                raise Http404("Document not found")
            
            # Determine document type and owner
            doc_type, doc_owner = self._determine_document_info(request.path)
            
            # Check if user has permission to access this document
            if not self._check_document_permission(request.user, file_path, doc_type):
                # Log unauthorized access attempt
                self._log_document_access(
                    request, file_path, doc_type, doc_owner, 
                    action='view', success=False, 
                    notes="Unauthorized access attempt"
                )
                raise Http404("Document not found")
            
            # Log successful access
            self._log_document_access(
                request, file_path, doc_type, doc_owner,
                action='download', success=True, watermarked=True
            )
            
            # Apply watermark and serve document
            return self._serve_watermarked_document(request, full_path)
            
        except Exception as e:
            # Log failed access
            self._log_document_access(
                request, request.path, 'other', 'unknown',
                action='download', success=False,
                notes=f"Error: {str(e)}"
            )
            raise
    
    def _determine_document_info(self, path):
        """Determine document type and owner from path"""
        if 'id_documents' in path:
            return 'player_id', self._extract_owner_from_path(path)
        elif 'passport_documents' in path:
            return 'player_passport', self._extract_owner_from_path(path)
        elif 'sa_passport_documents' in path:
            return 'player_sa_passport', self._extract_owner_from_path(path)
        elif 'profile_pictures' in path:
            return 'player_profile', self._extract_owner_from_path(path)
        elif 'certification_documents' in path:
            return 'official_cert', self._extract_owner_from_path(path)
        elif 'club_documents' in path:
            return 'club_document', self._extract_owner_from_path(path)
        else:
            return 'other', 'unknown'
    
    def _extract_owner_from_path(self, path):
        """Extract document owner from file path"""
        # Try to extract meaningful owner info from filename
        filename = os.path.basename(path)
        # This could be enhanced to look up actual player/official names
        return filename.split('_')[0] if '_' in filename else 'unknown'
    
    def _check_document_permission(self, user, file_path, doc_type):
        """Check if user has permission to access this document"""
        # Implement your permission logic here
        # For now, basic role-based access
        if user.is_superuser:
            return True
        
        # Club admins can access their club's documents
        if user.role == 'CLUB_ADMIN':
            return True  # Add more specific logic as needed
        
        # LFA and higher admins can view documents in their jurisdiction
        if user.role in ['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_COUNTRY']:
            return True
        
        return False
    
    def _log_document_access(self, request, file_path, doc_type, doc_owner, 
                           action='view', success=True, watermarked=False, notes=''):
        """Log document access to database"""
        try:
            # Get file size
            file_size = None
            if success and os.path.exists(os.path.join('media', file_path)):
                file_size = os.path.getsize(os.path.join('media', file_path))
            
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
            
            DocumentAccessLog.objects.create(
                user=request.user,
                document_type=doc_type,
                document_name=os.path.basename(file_path),
                document_owner=doc_owner,
                action=action,
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                file_size=file_size,
                watermarked=watermarked,
                success=success,
                notes=notes
            )
        except Exception as e:
            # Don't fail the request if logging fails
            print(f"Failed to log document access: {e}")
    
    def _serve_watermarked_document(self, request, file_path):
        """Serve document with watermark applied"""
        try:
            # Create watermarked copy
            watermarked_content = self.watermarker.create_watermarked_copy(
                open(file_path, 'rb'), request.user
            )
            
            # Determine content type
            content_type = 'application/octet-stream'
            if file_path.lower().endswith('.pdf'):
                content_type = 'application/pdf'
            elif file_path.lower().endswith(('.jpg', '.jpeg')):
                content_type = 'image/jpeg'
            elif file_path.lower().endswith('.png'):
                content_type = 'image/png'
            
            # Create response with watermarked content
            response = HttpResponse(watermarked_content, content_type=content_type)
            
            # Set filename for download
            filename = os.path.basename(file_path)
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            
            return response
            
        except Exception as e:
            print(f"Error serving watermarked document: {e}")
            # Fall back to serving original file
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
                return response
