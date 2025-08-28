"""
Document Access Tracking Middleware
Tracks all document downloads and applies watermarks
"""

import os
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse, FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from .models import DocumentAccessLog, CustomUser
from .watermark_utils import create_watermarked_document
import tempfile
import mimetypes

logger = logging.getLogger(__name__)

class DocumentAccessMiddleware(MiddlewareMixin):
    """Middleware to track and watermark document access"""
    
    def process_request(self, request):
        """Intercept document requests for tracking and watermarking"""
        
        # Check if this is a media file request
        if not request.path.startswith('/media/'):
            return None
            
        # Skip non-authenticated users
        if not request.user.is_authenticated:
            return None
            
        # Get file information
        file_path = request.path.replace('/media/', '')
        full_path = os.path.join('media', file_path)
        
        # Check if file exists
        if not os.path.exists(full_path):
            return None
            
        # Determine if this is a document that should be tracked
        trackable_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension not in trackable_extensions:
            return None
            
        # Log the access attempt
        self.log_document_access(request, file_path, 'view')
        
        # For download requests (determined by query parameter or specific paths)
        if request.GET.get('download') == '1' or '/download/' in request.path:
            return self.handle_document_download(request, full_path, file_path)

        # If it's not a download request, serve the file for viewing
        try:
            # We must use FileResponse for efficiency, especially with large files.
            # It streams the file instead of loading it all into memory.
            response = FileResponse(open(full_path, 'rb'))
            content_type, _ = mimetypes.guess_type(full_path)
            if content_type:
                response['Content-Type'] = content_type
            return response
        except FileNotFoundError:
            # This should have been caught by os.path.exists, but as a fallback.
            return None
        except Exception as e:
            logger.error(f"Error serving file {full_path}: {e}")
            return None
    
    def log_document_access(self, request, file_path, action='view', success=True, watermarked=False):
        """Log document access to database"""
        try:
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
            
            # Get file info
            file_name = os.path.basename(file_path)
            file_size = None
            try:
                file_size = os.path.getsize(os.path.join('media', file_path))
            except:
                pass
                
            # Determine document type
            doc_type = 'unknown'
            if 'player' in file_path.lower():
                doc_type = 'player_document'
            elif 'official' in file_path.lower():
                doc_type = 'official_document'
            elif 'certification' in file_path.lower():
                doc_type = 'certification'
            elif 'profile' in file_path.lower():
                doc_type = 'profile_photo'
            
            # Create log entry
            DocumentAccessLog.objects.create(
                user=request.user,
                document_name=file_name,
                document_type=doc_type,
                document_owner=self.determine_document_owner(file_path),
                action=action,
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                file_size=file_size,
                watermarked=watermarked,
                success=success,
                notes=f"Accessed via {request.method} {request.path}"
            )
            
        except Exception as e:
            logger.error(f"Failed to log document access: {str(e)}")
    
    def determine_document_owner(self, file_path):
        """Try to determine who the document belongs to"""
        try:
            # Try to extract from path structure
            path_parts = file_path.split('/')
            for part in path_parts:
                if '@' in part and '.' in part:  # Looks like email
                    return part
                if part.startswith('player_') or part.startswith('official_'):
                    return part
            return "Unknown"
        except:
            return "Unknown"
    
    def handle_document_download(self, request, full_path, file_path):
        """Handle document download with watermarking"""
        try:
            file_name = os.path.basename(file_path)
            file_extension = os.path.splitext(file_name)[1]
            
            # Create watermarked version
            watermarked_path = create_watermarked_document(
                request.user, 
                full_path, 
                file_name
            )
            
            if watermarked_path:
                # Log successful watermarked download
                self.log_document_access(request, file_path, 'download', True, True)
                
                # Serve watermarked file
                try:
                    with open(watermarked_path, 'rb') as f:
                        response = HttpResponse(f.read())
                        
                    # Set appropriate headers
                    content_type, _ = mimetypes.guess_type(file_name)
                    if content_type:
                        response['Content-Type'] = content_type
                    
                    response['Content-Disposition'] = f'attachment; filename="SAFA_PROTECTED_{file_name}"'
                    response['X-SAFA-Watermarked'] = 'true'
                    
                    # Clean up temporary file
                    try:
                        os.unlink(watermarked_path)
                    except:
                        pass
                        
                    return response
                    
                except Exception as e:
                    logger.error(f"Failed to serve watermarked file: {str(e)}")
                    # Clean up on error
                    try:
                        os.unlink(watermarked_path)
                    except:
                        pass
            
            # Fallback: serve original file but log as non-watermarked
            self.log_document_access(request, file_path, 'download', True, False)
            
            with open(full_path, 'rb') as f:
                response = HttpResponse(f.read())
                
            content_type, _ = mimetypes.guess_type(file_name)
            if content_type:
                response['Content-Type'] = content_type
                
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            response['X-SAFA-Watermarked'] = 'false'
            
            return response
            
        except Exception as e:
            logger.error(f"Document download failed: {str(e)}")
            # Log failed attempt
            self.log_document_access(request, file_path, 'download', False, False)
            raise Http404("Document not available")


def track_document_access(user, document_path, action='view'):
    """Utility function to manually track document access"""
    try:
        file_name = os.path.basename(document_path)
        file_size = None
        try:
            file_size = os.path.getsize(document_path)
        except:
            pass
            
        DocumentAccessLog.objects.create(
            user=user,
            document_name=file_name,
            document_type='manual_access',
            document_owner='System',
            action=action,
            ip_address='127.0.0.1',
            user_agent='System Access',
            file_size=file_size,
            watermarked=False,
            success=True,
            notes=f"Manual tracking: {action}"
        )
    except Exception as e:
        logger.error(f"Manual document tracking failed: {str(e)}")
