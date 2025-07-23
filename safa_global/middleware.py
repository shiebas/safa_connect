from django.http import HttpResponse

class DebugRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(f"DEBUG: Request received for path: {request.path}")
        response = self.get_response(request)
        return response