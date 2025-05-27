from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
import json
import os

class PDFDocument(TimeStampedModel):
    """Model to store uploaded PDF documents"""

    STATUS_CHOICES = (
        ('PENDING', _('Pending')),
        ('PROCESSING', _('Processing')),
        ('COMPLETED', _('Completed')),
        ('FAILED', _('Failed')),
    )

    file = models.FileField(upload_to='pdf_documents/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text=_('File size in bytes'))
    num_pages = models.PositiveIntegerField(default=0, help_text=_('Number of pages in the PDF'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True)

    def __str__(self):
        return self.original_filename

    def save(self, *args, **kwargs):
        # Set original filename if not already set
        if not self.original_filename and self.file:
            self.original_filename = os.path.basename(self.file.name)

        # Set file size if not already set
        if not self.file_size and self.file:
            self.file_size = self.file.size

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the file from storage when the model instance is deleted
        if self.file:
            storage, path = self.file.storage, self.file.path
            super().delete(*args, **kwargs)
            storage.delete(path)
        else:
            super().delete(*args, **kwargs)

class PDFExtractedData(TimeStampedModel):
    """Model to store data extracted from PDF documents"""

    pdf_document = models.OneToOneField(PDFDocument, on_delete=models.CASCADE, related_name='extracted_data')
    data_json = models.JSONField(default=dict, help_text=_('Extracted data in JSON format'))

    def __str__(self):
        return f"Extracted data for {self.pdf_document.original_filename}"

    @property
    def data(self):
        """Return the data as a Python dictionary"""
        return self.data_json

    @data.setter
    def data(self, value):
        """Set the data from a Python dictionary"""
        self.data_json = value
