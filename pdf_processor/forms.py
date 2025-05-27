from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import PDFDocument

class PDFUploadForm(forms.ModelForm):
    """Form for uploading PDF documents"""
    
    class Meta:
        model = PDFDocument
        fields = ['file']
        
    def clean_file(self):
        """Validate that the uploaded file is a PDF"""
        file = self.cleaned_data.get('file')
        if file:
            # Check file extension
            if not file.name.lower().endswith('.pdf'):
                raise ValidationError(_('File must be a PDF document.'))
            
            # Check file size (limit to 10MB)
            if file.size > 10 * 1024 * 1024:  # 10MB in bytes
                raise ValidationError(_('File size must be under 10MB.'))
                
            return file
        else:
            raise ValidationError(_('No file was submitted.'))