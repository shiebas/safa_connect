import qrcode
from PIL import Image, ImageDraw
import io
import base64
from django.conf import settings
from django.core.files.base import ContentFile
import os

def generate_qr_with_logo(qr_data, logo_path=None, profile_image=None, size=300):
    """
    Generate QR code with SAFA branding (Yellow, White, Black)
    """
    
    # Debug: Log what we're encoding
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Generating QR for data: {qr_data[:100]}... (length: {len(qr_data)})")
    
    # Create QR code with high error correction (allows logo overlay)
    qr = qrcode.QRCode(
        version=None,  # Let it auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium (15% error correction)
        box_size=8,  # Smaller box size for more data
        border=4,
    )
    
    try:
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create basic QR image with SAFA colors
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to RGBA for better handling
        qr_img = qr_img.convert('RGBA')
        
        # Resize to desired size
        qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Add SAFA logo overlay if available (but smaller to avoid scan issues)
        if logo_path and os.path.exists(logo_path):
            logo = Image.open(logo_path)
            add_safa_logo_to_qr(qr_img, logo, size)
        
        logger.info(f"QR code generated successfully for data length: {len(qr_data)}")
        return qr_img
        
    except Exception as e:
        logger.error(f"QR generation failed: {str(e)}")
        # Return a simple QR without logo as fallback
        qr_simple = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr_simple.add_data(qr_data)
        qr_simple.make(fit=True)
        return qr_simple.make_image(fill_color="black", back_color="white")

def add_safa_logo_to_qr(qr_img, logo, qr_size):
    """Add SAFA logo to center of QR code with yellow border - smaller size"""
    try:
        # Calculate logo size (smaller - max 15% of QR code)
        logo_size = int(qr_size * 0.15)
        
        # Resize logo maintaining aspect ratio
        logo = logo.convert('RGBA')
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        
        # Create yellow border around logo (smaller border)
        border_size = 4
        bordered_size = logo_size + (border_size * 2)
        
        # Create yellow background
        yellow_bg = Image.new('RGBA', (bordered_size, bordered_size), (255, 215, 0, 255))
        
        # Paste logo on yellow background
        logo_pos = (border_size, border_size)
        yellow_bg.paste(logo, logo_pos, logo)
        
        # Calculate position (center of QR code)
        pos = ((qr_size - bordered_size) // 2, (qr_size - bordered_size) // 2)
        
        # Paste logo with yellow border onto QR code
        qr_img.paste(yellow_bg, pos, yellow_bg)
        
    except Exception as e:
        # If logo overlay fails, continue without it
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Logo overlay failed: {str(e)}")

def add_profile_to_qr(qr_img, profile_image, qr_size):
    """Add profile picture to corner with SAFA yellow border"""
    try:
        # Open profile image
        if hasattr(profile_image, 'path'):
            profile = Image.open(profile_image.path)
        else:
            profile = Image.open(profile_image)
        
        # Convert to RGBA
        profile = profile.convert('RGBA')
        
        # Calculate profile size (smaller than logo)
        profile_size = int(qr_size * 0.12)
        
        # Resize and make circular
        profile = profile.resize((profile_size, profile_size), Image.Resampling.LANCZOS)
        
        # Create circular mask
        mask = Image.new('L', (profile_size, profile_size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, profile_size, profile_size), fill=255)
        
        # Apply mask
        output = Image.new('RGBA', (profile_size, profile_size), (0, 0, 0, 0))
        output.paste(profile, (0, 0))
        output.putalpha(mask)
        
        # Add yellow border
        border_size = 3
        bordered_size = profile_size + (border_size * 2)
        yellow_border = Image.new('RGBA', (bordered_size, bordered_size), (255, 215, 0, 255))
        
        # Create circular yellow border
        border_mask = Image.new('L', (bordered_size, bordered_size), 0)
        border_draw = ImageDraw.Draw(border_mask)
        border_draw.ellipse((0, 0, bordered_size, bordered_size), fill=255)
        yellow_border.putalpha(border_mask)
        
        # Paste profile on yellow border
        yellow_border.paste(output, (border_size, border_size), output)
        
        # Position in top-right corner
        pos = (qr_size - bordered_size - 10, 10)
        qr_img.paste(yellow_border, pos, yellow_border)
        
    except Exception as e:
        # If profile processing fails, continue without it
        pass

def qr_to_base64(qr_img):
    """Convert QR image to base64 string for web display"""
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def save_qr_image(qr_img, filename):
    """Save QR image to file"""
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    return ContentFile(buffer.getvalue(), name=filename)
