class AdminFormErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        # Check if the error is about 'CustomUserForm' field 'province'
        if (isinstance(exception, ValueError) and 
            "has no field named 'province'" in str(exception) and
            "CustomUserForm" in str(exception)):
            # Return to the admin form page with a helpful error message
            from django.contrib import messages
            from django.shortcuts import redirect
            
            # Get the current path
            current_path = request.path
            
            # Add error message
            messages.error(request, "Error: The 'province' field is missing. Please use 'province_id' instead.")
            
            # Redirect back to the same page
            return redirect(current_path)
        
        return None