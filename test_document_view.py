from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import os
from django.conf import settings

@login_required
def test_document_download(request):
    """Test view to download our test document through the protection system"""
    # This will trigger our middleware for testing
    test_file_path = os.path.join(settings.MEDIA_ROOT, 'test_document.txt')
    
    if not os.path.exists(test_file_path):
        raise Http404("Test document not found")
    
    # Read the file content
    with open(test_file_path, 'r') as f:
        content = f.read()
    
    # Return as attachment to trigger download
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="test_document.txt"'
    
    return response
