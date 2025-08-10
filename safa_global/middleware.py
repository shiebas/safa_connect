from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.conf import settings

class DebugRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(f"DEBUG: Request received for path: {request.path}")
        response = self.get_response(request)
        return response

class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Add security headers
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response

class WWWRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().lower()
        
        # Redirect www to non-www in production
        if settings.DEBUG is False and host.startswith('www.'):
            new_host = host[4:]
            new_url = f"{request.scheme}://{new_host}{request.get_full_path()}"
            return HttpResponsePermanentRedirect(new_url)
        
        return self.get_response(request)
        