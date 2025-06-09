from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
from django.http import HttpResponseRedirect

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
