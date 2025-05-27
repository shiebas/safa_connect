# PDF Processor

A Django app for extracting information from PDF files and storing it in the system.

## Features

- Upload PDF documents
- Extract text and structured data from PDFs
- Support for text-based PDFs, scanned documents (via OCR), and forms
- View and export extracted data in JSON format
- Integration with the Django admin interface

## Installation

1. Add the required dependencies to your requirements.txt file:
   ```
   PyPDF2==3.0.1
   pdfminer.six==20221105
   pdf2image==1.16.3
   pytesseract==0.3.10
   ```

2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Add 'pdf_processor' to your INSTALLED_APPS in settings.py:
   ```python
   INSTALLED_APPS = [
       # ...
       'pdf_processor',
       # ...
   ]
   ```

4. Include the pdf_processor URLconf in your project urls.py:
   ```python
   urlpatterns = [
       # ...
       path('pdf/', include('pdf_processor.urls', namespace='pdf_processor')),
       # ...
   ]
   ```

5. Run migrations to create the pdf_processor models:
   ```
   python manage.py migrate
   ```

## Usage

### Uploading PDFs

1. Navigate to the PDF upload page at `/pdf/upload/`
2. Select a PDF file to upload (max 10MB)
3. Click the "Upload" button

### Processing PDFs

1. After uploading a PDF, navigate to the PDF detail page
2. Click the "Process PDF" button to extract data from the PDF
3. Wait for the processing to complete

### Viewing Extracted Data

1. Navigate to the PDF detail page
2. View the extracted data in the following tabs:
   - Structured Data: Extracted fields like names, emails, dates, etc.
   - Metadata: PDF document metadata
   - Full Text: The complete text extracted from the PDF
   - Raw JSON: The complete extracted data in JSON format

### Exporting Data

1. Navigate to the PDF detail page
2. Click the "Export Data (JSON)" button to download the extracted data as a JSON file

## Supported PDF Types

- **Text-based PDFs**: PDFs with searchable text
- **Scanned documents**: PDFs containing scanned images (processed using OCR)
- **Forms and structured documents**: PDFs with form fields or structured data

## Technical Details

### Data Extraction Methods

The app uses multiple methods to extract data from PDFs:

1. **PyPDF2**: For basic text extraction and metadata
2. **pdfminer.six**: For more advanced text extraction
3. **pdf2image + pytesseract**: For OCR on scanned documents

### Structured Data Extraction

The app attempts to identify and extract structured data using regex patterns, including:

- Email addresses
- Phone numbers
- Dates
- ID numbers
- Names and surnames

### Data Storage

Extracted data is stored in a JSONField in the PDFExtractedData model, linked to the PDFDocument model.