from django.contrib import admin
from django.utils.html import format_html
from .models import PDFDocument, PDFExtractedData

class PDFDocumentAdmin(admin.ModelAdmin):
    """Admin configuration for PDFDocument model"""
    list_display = ('original_filename', 'file_size_display', 'num_pages', 'status', 'created', 'modified')
    list_filter = ('status', 'created')
    search_fields = ('original_filename', 'error_message')
    readonly_fields = ('file_size_display', 'num_pages', 'created', 'modified')

    def file_size_display(self, obj):
        """Display file size in a human-readable format"""
        size_bytes = obj.file_size
        if size_bytes is None:
            return "Unknown"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0 or unit == 'GB':
                break
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} {unit}"

    file_size_display.short_description = 'File Size'

class PDFExtractedDataAdmin(admin.ModelAdmin):
    """Admin configuration for PDFExtractedData model"""
    list_display = ('pdf_document', 'created', 'modified')
    search_fields = ('pdf_document__original_filename',)
    readonly_fields = ('created', 'modified', 'data_preview')

    def data_preview(self, obj):
        """Display a preview of the extracted data"""
        if not obj.data_json:
            return "No data available"

        # Create a simple HTML representation of the data
        html = "<div style='max-height: 400px; overflow-y: auto;'>"
        html += "<h3>Extracted Data Preview</h3>"

        # Add structured data if available
        if 'structured_data' in obj.data_json and obj.data_json['structured_data']:
            html += "<h4>Structured Data</h4>"
            html += "<table style='width: 100%; border-collapse: collapse;'>"
            html += "<tr><th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Field</th><th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Value</th></tr>"

            for key, values in obj.data_json['structured_data'].items():
                html += f"<tr><td style='border: 1px solid #ddd; padding: 8px;'>{key}</td><td style='border: 1px solid #ddd; padding: 8px;'>"

                if isinstance(values, list):
                    if len(values) == 1:
                        html += f"{values[0]}"
                    else:
                        html += "<ul>"
                        for value in values:
                            html += f"<li>{value}</li>"
                        html += "</ul>"
                else:
                    html += f"{values}"

                html += "</td></tr>"

            html += "</table>"

        # Add text preview if available
        if 'text' in obj.data_json and obj.data_json['text']:
            html += "<h4>Text Preview</h4>"
            # Show only the first 500 characters of the text
            text = obj.data_json['text']
            preview = text[:500] + "..." if len(text) > 500 else text
            html += f"<pre style='background-color: #f8f9fa; padding: 10px; border-radius: 5px;'>{preview}</pre>"

        html += "</div>"
        return format_html(html)

    data_preview.short_description = 'Data Preview'

# Register the models with the admin site
admin.site.register(PDFDocument, PDFDocumentAdmin)
admin.site.register(PDFExtractedData, PDFExtractedDataAdmin)
