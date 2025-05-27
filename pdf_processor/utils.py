import os
import io
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
import PyPDF2
from pdfminer.high_level import extract_text
from pdf2image import convert_from_path, convert_from_bytes
import pytesseract
from django.conf import settings
from .models import PDFDocument, PDFExtractedData

logger = logging.getLogger(__name__)

class PDFParser:
    """Utility class for parsing PDF files and extracting data"""
    
    def __init__(self, pdf_document: PDFDocument):
        """
        Initialize the PDF parser with a PDFDocument instance
        
        Args:
            pdf_document: The PDFDocument instance to parse
        """
        self.pdf_document = pdf_document
        self.file_path = pdf_document.file.path
        self.extracted_data = {}
    
    def extract_text_with_pdfminer(self) -> str:
        """
        Extract text from PDF using pdfminer.six
        
        Returns:
            str: Extracted text from the PDF
        """
        try:
            text = extract_text(self.file_path)
            return text
        except Exception as e:
            logger.error(f"Error extracting text with pdfminer: {str(e)}")
            self.pdf_document.status = 'FAILED'
            self.pdf_document.error_message = f"Error extracting text: {str(e)}"
            self.pdf_document.save()
            return ""
    
    def extract_text_with_pypdf2(self) -> str:
        """
        Extract text from PDF using PyPDF2
        
        Returns:
            str: Extracted text from the PDF
        """
        try:
            text = ""
            with open(self.file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                self.pdf_document.num_pages = len(reader.pages)
                self.pdf_document.save()
                
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text()
            return text
        except Exception as e:
            logger.error(f"Error extracting text with PyPDF2: {str(e)}")
            self.pdf_document.status = 'FAILED'
            self.pdf_document.error_message = f"Error extracting text: {str(e)}"
            self.pdf_document.save()
            return ""
    
    def extract_text_with_ocr(self) -> str:
        """
        Extract text from PDF using OCR (Optical Character Recognition)
        Useful for scanned PDFs or PDFs with images
        
        Returns:
            str: Extracted text from the PDF
        """
        try:
            text = ""
            # Convert PDF to images
            images = convert_from_path(self.file_path)
            
            # Extract text from each image using OCR
            for i, image in enumerate(images):
                text += pytesseract.image_to_string(image)
                text += f"\n--- Page {i+1} ---\n"
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text with OCR: {str(e)}")
            self.pdf_document.status = 'FAILED'
            self.pdf_document.error_message = f"Error extracting text with OCR: {str(e)}"
            self.pdf_document.save()
            return ""
    
    def extract_metadata(self) -> Dict[str, Any]:
        """
        Extract metadata from the PDF
        
        Returns:
            Dict[str, Any]: Dictionary containing PDF metadata
        """
        try:
            metadata = {}
            with open(self.file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                if reader.metadata:
                    for key, value in reader.metadata.items():
                        # Remove the leading '/' from keys
                        clean_key = key[1:] if key.startswith('/') else key
                        metadata[clean_key] = value
            return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return {}
    
    def extract_structured_data(self, text: str) -> Dict[str, Any]:
        """
        Extract structured data from the PDF text using regex patterns
        
        Args:
            text: The text extracted from the PDF
            
        Returns:
            Dict[str, Any]: Dictionary containing structured data
        """
        data = {}
        
        # Example patterns for common data types
        # These should be customized based on the specific PDFs being processed
        patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            'id_number': r'\b\d{13}\b',  # South African ID number pattern
            'name': r'Name:?\s*([A-Za-z\s]+)',
            'surname': r'Surname:?\s*([A-Za-z\s]+)',
        }
        
        for key, pattern in patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                data[key] = matches
        
        return data
    
    def process(self) -> Dict[str, Any]:
        """
        Process the PDF document and extract all available data
        
        Returns:
            Dict[str, Any]: Dictionary containing all extracted data
        """
        try:
            self.pdf_document.status = 'PROCESSING'
            self.pdf_document.save()
            
            # Extract text using different methods
            text_pdfminer = self.extract_text_with_pdfminer()
            text_pypdf2 = self.extract_text_with_pypdf2()
            
            # Use the text from the method that extracted more content
            text = text_pdfminer if len(text_pdfminer) > len(text_pypdf2) else text_pypdf2
            
            # If text extraction failed or returned very little text, try OCR
            if len(text) < 100:  # Arbitrary threshold
                text = self.extract_text_with_ocr()
            
            # Extract metadata
            metadata = self.extract_metadata()
            
            # Extract structured data
            structured_data = self.extract_structured_data(text)
            
            # Combine all extracted data
            self.extracted_data = {
                'text': text,
                'metadata': metadata,
                'structured_data': structured_data
            }
            
            # Save the extracted data
            extracted_data_obj, created = PDFExtractedData.objects.get_or_create(
                pdf_document=self.pdf_document,
                defaults={'data_json': self.extracted_data}
            )
            
            if not created:
                extracted_data_obj.data = self.extracted_data
                extracted_data_obj.save()
            
            # Update the document status
            self.pdf_document.status = 'COMPLETED'
            self.pdf_document.save()
            
            return self.extracted_data
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            self.pdf_document.status = 'FAILED'
            self.pdf_document.error_message = f"Error processing PDF: {str(e)}"
            self.pdf_document.save()
            return {'error': str(e)}

def process_pdf(pdf_document_id: int) -> Dict[str, Any]:
    """
    Process a PDF document by its ID
    
    Args:
        pdf_document_id: The ID of the PDFDocument to process
        
    Returns:
        Dict[str, Any]: The extracted data
    """
    try:
        pdf_document = PDFDocument.objects.get(id=pdf_document_id)
        parser = PDFParser(pdf_document)
        return parser.process()
    except PDFDocument.DoesNotExist:
        logger.error(f"PDF document with ID {pdf_document_id} does not exist")
        return {'error': f"PDF document with ID {pdf_document_id} does not exist"}
    except Exception as e:
        logger.error(f"Error processing PDF document with ID {pdf_document_id}: {str(e)}")
        return {'error': str(e)}