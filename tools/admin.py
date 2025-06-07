from django.contrib import admin
from django.urls import path
from . import views

# Reset admin site's get_urls to remove any previous patches
# This ensures we don't have duplicates from previous runs
if hasattr(admin.site, '_original_get_urls'):
    admin.site.get_urls = admin.site._original_get_urls

# Store the original get_urls once before we patch it
if not hasattr(admin.site, '_original_get_urls'):
    admin.site._original_get_urls = admin.site.get_urls

def get_custom_urls():
    """Generate custom admin URLs without duplicates"""
    urls = admin.site._original_get_urls()
    
    # Define our tool paths
    tool_urls = [
        path('tools/generate-all-safa-ids/', 
             admin.site.admin_view(views.generate_all_safa_ids), 
             name='tools_generate_all_safa_ids'),
        path('tools/safa-id-coverage/', 
             admin.site.admin_view(views.safa_id_coverage), 
             name='tools_safa_id_coverage'),
        path('tools/generate-qr-codes/', 
             admin.site.admin_view(views.generate_qr_codes), 
             name='tools_generate_qr_codes'),
    ]
    
    # Filter out any existing URLs with the same paths
    existing_paths = [url.pattern.regex.pattern for url in urls]
    unique_tool_urls = []
    
    for url in tool_urls:
        path_pattern = url.pattern.regex.pattern
        if path_pattern not in existing_paths:
            unique_tool_urls.append(url)
            existing_paths.append(path_pattern)
    
    # Return combined URLs (tools first for proper URL resolution)
    return unique_tool_urls + urls

# Replace the admin site's get_urls method with our custom one
admin.site.get_urls = get_custom_urls
