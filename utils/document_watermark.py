"""
Document watermarking utilities for SAFA Connect system
Adds watermarks to documents when downloaded to track unauthorized distribution
"""
import os
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageColor import getcolor
import fitz  # PyMuPDF for PDF handling
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
import tempfile


class DocumentWatermarker:
    """Handle watermarking of documents with SAFA branding and user info"""
    
    def __init__(self):
        self.watermark_color = (255, 0, 0, 100)  # Red with transparency
        self.safa_color = (8, 107, 60, 120)  # SAFA Green with transparency
        self.font_size = 24
        self.diagonal_angle = 45
        
    def create_watermark_text(self, user, download_time=None, unauthorized_warning=True):
        """Create watermark text with user info and warnings"""
        if download_time is None:
            download_time = timezone.now()
        
        watermark_lines = [
            "SOUTH AFRICAN FOOTBALL ASSOCIATION",
            "SAFA GLOBAL SYSTEM",
            "",
            f"Downloaded by: {user.get_full_name()}",
            f"User ID: {user.safa_id or user.email}",
            f"Role: {user.get_role_display()}",
            f"Downloaded: {download_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
        
        if unauthorized_warning:
            watermark_lines.extend([
                "⚠️ CONFIDENTIAL DOCUMENT ⚠️",
                "UNAUTHORIZED DISTRIBUTION PROHIBITED",
                "This document contains confidential information",
                "Sharing without authorization is strictly forbidden",
                "All access is logged and monitored",
                "Report unauthorized use to: security@safa.net"
            ])
        
        return "\n".join(watermark_lines)
    
    def watermark_image(self, image_path, user, output_path=None):
        """Add watermark to image files (JPG, PNG)"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGBA for transparency support
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Create watermark overlay
                overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(overlay)
                
                # Get watermark text
                watermark_text = self.create_watermark_text(user)
                
                # Try to load a font, fallback to default
                try:
                    font = ImageFont.truetype("arial.ttf", self.font_size)
                except:
                    font = ImageFont.load_default()
                
                # Calculate text positioning
                text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                # Position watermark in bottom right corner
                x = img.width - text_width - 50
                y = img.height - text_height - 50
                
                # Draw semi-transparent background
                padding = 20
                draw.rectangle([
                    x - padding, y - padding,
                    x + text_width + padding, y + text_height + padding
                ], fill=(0, 0, 0, 128))
                
                # Draw watermark text
                draw.multiline_text((x, y), watermark_text, fill=self.watermark_color, font=font)
                
                # Composite the watermark onto the original image
                watermarked = Image.alpha_composite(img, overlay)
                
                # Save the watermarked image
                if output_path is None:
                    output_path = image_path
                
                # Convert back to RGB if saving as JPEG
                if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
                    watermarked = watermarked.convert('RGB')
                
                watermarked.save(output_path, quality=95)
                return output_path
                
        except Exception as e:
            print(f"Error watermarking image: {e}")
            return None
    
    def watermark_pdf(self, pdf_path, user, output_path=None):
        """Add watermark to PDF files"""
        try:
            doc = fitz.open(pdf_path)
            watermark_text = self.create_watermark_text(user)
            
            for page in doc:
                # Get page dimensions
                rect = page.rect
                
                # Create watermark text box in bottom right
                text_rect = fitz.Rect(
                    rect.width - 300, rect.height - 200,
                    rect.width - 20, rect.height - 20
                )
                
                # Add semi-transparent background rectangle
                page.draw_rect(text_rect, color=(0, 0, 0), fill=(1, 1, 1), width=1)
                
                # Add watermark text
                page.insert_textbox(
                    text_rect,
                    watermark_text,
                    fontsize=10,
                    color=(1, 0, 0),  # Red color
                    align=fitz.TEXT_ALIGN_LEFT
                )
                
                # Add diagonal watermark across the page
                diagonal_rect = fitz.Rect(50, rect.height/2 - 50, rect.width - 50, rect.height/2 + 50)
                page.insert_textbox(
                    diagonal_rect,
                    "SAFA CONFIDENTIAL - UNAUTHORIZED DISTRIBUTION PROHIBITED",
                    fontsize=20,
                    color=(0.8, 0.8, 0.8),  # Light gray
                    align=fitz.TEXT_ALIGN_CENTER,
                    rotate=45
                )
            
            # Save watermarked PDF
            if output_path is None:
                output_path = pdf_path
                
            doc.save(output_path)
            doc.close()
            return output_path
            
        except Exception as e:
            print(f"Error watermarking PDF: {e}")
            return None
    
    def watermark_document(self, file_path, user, output_path=None):
        """Watermark any supported document type"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in ['.jpg', '.jpeg', '.png']:
            return self.watermark_image(file_path, user, output_path)
        elif file_ext == '.pdf':
            return self.watermark_pdf(file_path, user, output_path)
        else:
            print(f"Unsupported file type for watermarking: {file_ext}")
            return None
    
    def create_watermarked_copy(self, original_file, user):
        """Create a watermarked copy of a Django FileField file"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_file.name)[1]) as temp_file:
                # Copy original file content to temp file
                for chunk in original_file.chunks():
                    temp_file.write(chunk)
                temp_file.flush()
                
                # Create output path for watermarked version
                watermarked_path = temp_file.name + '_watermarked' + os.path.splitext(original_file.name)[1]
                
                # Apply watermark
                result = self.watermark_document(temp_file.name, user, watermarked_path)
                
                if result:
                    # Read watermarked file
                    with open(watermarked_path, 'rb') as f:
                        watermarked_content = f.read()
                    
                    # Clean up temporary files
                    os.unlink(temp_file.name)
                    os.unlink(watermarked_path)
                    
                    return watermarked_content
                else:
                    # Clean up and return original if watermarking failed
                    os.unlink(temp_file.name)
                    original_file.seek(0)
                    return original_file.read()
                    
        except Exception as e:
            print(f"Error creating watermarked copy: {e}")
            # Return original file if watermarking fails
            original_file.seek(0)
            return original_file.read()


# Utility function for easy access
def add_watermark_to_document(file_path, user, output_path=None):
    """Convenience function to watermark a document"""
    watermarker = DocumentWatermarker()
    return watermarker.watermark_document(file_path, user, output_path)
