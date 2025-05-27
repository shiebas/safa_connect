from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, View
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from .models import PDFDocument, PDFExtractedData
from .forms import PDFUploadForm
from .utils import PDFParser, process_pdf

class PDFUploadView(LoginRequiredMixin, CreateView):
    """View for uploading PDF documents"""
    model = PDFDocument
    form_class = PDFUploadForm
    template_name = 'pdf_processor/pdf_upload.html'
    success_url = reverse_lazy('pdf_processor:pdf-list')

    def form_valid(self, form):
        """Process the form if it's valid"""
        # Set initial values for the PDF document
        pdf_document = form.save(commit=False)
        pdf_document.original_filename = form.cleaned_data['file'].name
        pdf_document.file_size = form.cleaned_data['file'].size
        pdf_document.status = 'PENDING'
        pdf_document.save()

        # Add a success message
        messages.success(self.request, _('PDF document uploaded successfully.'))

        # Redirect to the detail view for the new document
        return HttpResponseRedirect(reverse('pdf_processor:pdf-detail', kwargs={'pk': pdf_document.pk}))

class PDFListView(LoginRequiredMixin, ListView):
    """View for listing PDF documents"""
    model = PDFDocument
    template_name = 'pdf_processor/pdf_list.html'
    context_object_name = 'pdf_documents'
    paginate_by = 10

    def get_queryset(self):
        """Return the queryset of PDF documents"""
        return PDFDocument.objects.all().order_by('-created')

class PDFDetailView(LoginRequiredMixin, DetailView):
    """View for displaying PDF document details"""
    model = PDFDocument
    template_name = 'pdf_processor/pdf_detail.html'
    context_object_name = 'pdf_document'

    def get_context_data(self, **kwargs):
        """Add extracted data to the context"""
        context = super().get_context_data(**kwargs)
        pdf_document = self.get_object()

        # Check if extracted data exists
        try:
            extracted_data = pdf_document.extracted_data
            context['extracted_data'] = extracted_data.data
        except PDFExtractedData.DoesNotExist:
            context['extracted_data'] = None

        return context

class PDFProcessView(LoginRequiredMixin, View):
    """View for processing a PDF document"""

    def get(self, request, pk):
        """Process the PDF document"""
        pdf_document = get_object_or_404(PDFDocument, pk=pk)

        # Check if the document is already being processed
        if pdf_document.status == 'PROCESSING':
            messages.warning(request, _('This document is already being processed.'))
            return redirect('pdf_processor:pdf-detail', pk=pk)

        # Process the PDF document
        try:
            pdf_document.status = 'PROCESSING'
            pdf_document.save()

            # Process the PDF
            parser = PDFParser(pdf_document)
            parser.process()

            messages.success(request, _('PDF document processed successfully.'))
        except Exception as e:
            pdf_document.status = 'FAILED'
            pdf_document.error_message = str(e)
            pdf_document.save()
            messages.error(request, _('Error processing PDF document: {}').format(str(e)))

        return redirect('pdf_processor:pdf-detail', pk=pk)

class PDFDataExportView(LoginRequiredMixin, View):
    """View for exporting extracted data as JSON"""

    def get(self, request, pk):
        """Export the extracted data as JSON"""
        pdf_document = get_object_or_404(PDFDocument, pk=pk)

        try:
            extracted_data = pdf_document.extracted_data
            return JsonResponse(extracted_data.data)
        except PDFExtractedData.DoesNotExist:
            return JsonResponse({'error': 'No extracted data found for this document'}, status=404)

def pdf_upload_success(request):
    """Simple view to show a success message after PDF upload"""
    return render(request, 'pdf_processor/pdf_upload_success.html')
