"""
SAFA Document Watermarking Utility
Adds watermarks to documents to prevent unauthorized distribution
"""

import os
import io
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color
import PyPDF2
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import tempfile
import logging

logger = logging.getLogger(__name__)

class DocumentWatermarker:
    """Handles watermarking of various document types"""
    
    def __init__(self, user, document_type="SAFA Document"):
        self.user = user
        self.document_type = document_type
        self.watermark_text = self.generate_watermark_text()
        
    def generate_watermark_text(self):
        """Generate watermark text with user and timestamp"""
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
        return (
            f"SAFA CONFIDENTIAL\n"
            f"Downloaded by: {self.user.get_full_name()}\n"
            f"Email: {self.user.email}\n"
            f"SAFA ID: {self.user.safa_id or 'N/A'}\n"
            f"Downloaded: {timestamp}\n"
            f"UNAUTHORIZED DISTRIBUTION PROHIBITED\n"
            f"© South African Football Association"
        )
    
    def watermark_pdf(self, input_path, output_path):
        """Add watermark to PDF document"""
        try:
            # Create watermark PDF
            watermark_buffer = io.BytesIO()
            c = canvas.Canvas(watermark_buffer, pagesize=A4)
            
            # Set up watermark style
            c.setFillColor(Color(0.8, 0.8, 0.8, alpha=0.3))  # Light gray with transparency
            c.setFont("Helvetica", 10)
            
            # Position watermark (bottom right)
            x, y = 400, 50
            lines = self.watermark_text.split('\n')
            
            for i, line in enumerate(lines):
                c.drawString(x, y - (i * 12), line)
            
            # Add diagonal watermark across page
            c.saveState()
            c.setFillColor(Color(0.9, 0.9, 0.9, alpha=0.1))
            c.setFont("Helvetica-Bold", 36)
            c.rotate(45)
            c.drawString(200, -100, "SAFA CONFIDENTIAL")
            c.restoreState()
            
            c.save()
            watermark_buffer.seek(0)
            
            # Apply watermark to original PDF
            with open(input_path, 'rb') as input_file:
                original_pdf = PyPDF2.PdfReader(input_file)
                watermark_pdf = PyPDF2.PdfReader(watermark_buffer)
                output_pdf = PyPDF2.PdfWriter()
                
                watermark_page = watermark_pdf.pages[0]
                
                for page_num in range(len(original_pdf.pages)):
                    page = original_pdf.pages[page_num]
                    page.merge_page(watermark_page)
                    output_pdf.add_page(page)
                
                with open(output_path, 'wb') as output_file:
                    output_pdf.write(output_file)
            
            return True
            
        except Exception as e:
            logger.error(f"PDF watermarking failed: {str(e)}")
            return False
    
    def watermark_image(self, input_path, output_path):
        """Add watermark to image document"""
        try:
            with Image.open(input_path) as img:
                # Convert to RGBA if necessary
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Create watermark overlay
                overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(overlay)
                
                # Try to load a font, fall back to default if not available
                try:
                    font = ImageFont.truetype("arial.ttf", 20)
                    small_font = ImageFont.truetype("arial.ttf", 14)
                except:
                    font = ImageFont.load_default()
                    small_font = ImageFont.load_default()
                
                # Position watermark
                lines = self.watermark_text.split('\n')
                y_start = img.height - (len(lines) * 25) - 20
                
                for i, line in enumerate(lines):
                    if line.strip():
                        y = y_start + (i * 20)
                        draw.text((20, y), line, fill=(255, 255, 255, 180), font=small_font)
                        draw.text((18, y-2), line, fill=(0, 0, 0, 120), font=small_font)  # Shadow
                
                # Add diagonal watermark
                draw.text((img.width//2 - 100, img.height//2), 
                         "SAFA CONFIDENTIAL", 
                         fill=(200, 200, 200, 80), 
                         font=font)
                
                # Combine images
                watermarked = Image.alpha_composite(img, overlay)
                
                # Save as RGB if original was not RGBA
                if watermarked.mode == 'RGBA':
                    watermarked = watermarked.convert('RGB')
                
                watermarked.save(output_path, quality=95)
            
            return True
            
        except Exception as e:
            logger.error(f"Image watermarking failed: {str(e)}")
            return False
    
    def watermark_document(self, file_path, file_extension):
        """Watermark document based on file type"""
        try:
            # Create temporary file for watermarked version
            with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
                watermarked_path = temp_file.name
            
            success = False
            
            if file_extension.lower() == '.pdf':
                success = self.watermark_pdf(file_path, watermarked_path)
            elif file_extension.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                success = self.watermark_image(file_path, watermarked_path)
            else:
                # For unsupported file types, copy original and add text watermark info
                logger.warning(f"Watermarking not supported for {file_extension}")
                import shutil
                shutil.copy2(file_path, watermarked_path)
                success = True
            
            if success:
                return watermarked_path
            else:
                os.unlink(watermarked_path)
                return None
                
        except Exception as e:
            logger.error(f"Document watermarking failed: {str(e)}")
            return None

def create_watermarked_document(user, original_file_path, document_name):
    """
    Create a watermarked version of a document
    Returns the path to the watermarked file
    """
    try:
        file_extension = os.path.splitext(original_file_path)[1]
        watermarker = DocumentWatermarker(user, document_name)
        
        watermarked_path = watermarker.watermark_document(original_file_path, file_extension)
        
        if watermarked_path:
            logger.info(f"Document watermarked successfully: {document_name} for user {user.email}")
            return watermarked_path
        else:
            logger.error(f"Failed to watermark document: {document_name}")
            return None
            
    except Exception as e:
        logger.error(f"Watermarking error: {str(e)}")
        return None
