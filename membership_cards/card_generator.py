from PIL import Image, ImageDraw, ImageFont
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import os
from django.conf import settings

def generate_physical_card_image(physical_card):
    """Generate print-ready image for physical card"""
    
    template = physical_card.template
    user = physical_card.user
    
    if not template or not template.card_front_image:
        raise ValueError("No template assigned or template missing front image")
    
    # Open template image
    card_img = Image.open(template.card_front_image.path).convert('RGBA')
    
    # Resize to template dimensions
    card_img = card_img.resize((template.card_width, template.card_height), Image.Resampling.LANCZOS)
    
    # Create drawing context
    draw = ImageDraw.Draw(card_img)
    
    # Load fonts (cross-platform approach)
    try:
        # Try different font paths for different operating systems
        font_paths = [
            '/System/Library/Fonts/Arial.ttf',  # macOS
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Linux
            'C:/Windows/Fonts/arial.ttf',  # Windows
            '/usr/share/fonts/TTF/arial.ttf',  # Some Linux distributions
        ]
        
        name_font = None
        detail_font = None
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    name_font = ImageFont.truetype(font_path, 24)
                    detail_font = ImageFont.truetype(font_path, 16)
                    break
            except:
                continue
        
        # Fallback to default fonts if no system fonts found
        if not name_font:
            name_font = ImageFont.load_default()
            detail_font = ImageFont.load_default()
            
    except Exception:
        name_font = ImageFont.load_default()
        detail_font = ImageFont.load_default()
    
    # Add member name
    member_name = f"{user.name} {user.surname}".upper()
    draw.text(
        (template.name_position_x, template.name_position_y),
        member_name,
        fill='black',
        font=name_font
    )
    
    # Add member details
    details = [
        f"SAFA ID: {user.safa_id}",
        f"Card No: {physical_card.card_number}",
        f"Role: {user.get_role_display()}",
        f"Expires: {physical_card.user.membership_expires_date.strftime('%m/%Y') if physical_card.user.membership_expires_date else 'N/A'}"
    ]
    
    y_offset = template.name_position_y + 40
    for detail in details:
        draw.text((template.name_position_x, y_offset), detail, fill='black', font=detail_font)
        y_offset += 20
    
    # Add profile photo if available
    if user.profile_photo:
        try:
            profile = Image.open(user.profile_photo.path).convert('RGBA')
            # Make it square and resize
            profile = profile.resize((80, 80), Image.Resampling.LANCZOS)
            # Make circular
            mask = Image.new('L', (80, 80), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, 80, 80), fill=255)
            profile.putalpha(mask)
            
            card_img.paste(profile, (template.photo_position_x, template.photo_position_y), profile)
        except:
            pass
    
    # Add QR code if digital card exists
    if hasattr(user, 'digital_card') and user.digital_card.qr_image:
        try:
            qr_img = Image.open(user.digital_card.qr_image.path).convert('RGBA')
            qr_img = qr_img.resize((100, 100), Image.Resampling.LANCZOS)
            card_img.paste(qr_img, (template.qr_position_x, template.qr_position_y), qr_img)
        except:
            pass
    
    return card_img

def generate_print_ready_pdf(physical_cards):
    """Generate print-ready PDF with multiple cards"""
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
    except ImportError:
        raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Card dimensions in inches (standard credit card size)
    card_width = 3.375 * inch
    card_height = 2.125 * inch
    margin = 0.5 * inch
    
    cards_per_row = 2
    cards_per_col = 4
    
    x_positions = [margin, margin + card_width + 0.25*inch]
    y_positions = [
        letter[1] - margin - card_height,
        letter[1] - margin - 2*card_height - 0.25*inch,
        letter[1] - margin - 3*card_height - 0.5*inch,
        letter[1] - margin - 4*card_height - 0.75*inch
    ]
    
    card_count = 0
    for physical_card in physical_cards:
        try:
            # Generate card image
            card_img = generate_physical_card_image(physical_card)
            
            # Use Django's temp directory instead of /tmp
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
                card_img.save(temp_path, 'PNG', dpi=(300, 300))
            
            # Calculate position
            row = card_count // cards_per_row
            col = card_count % cards_per_row
            
            if row >= cards_per_col:
                p.showPage()  # New page
                row = 0
                card_count = 0
                col = card_count % cards_per_row
            
            x = x_positions[col]
            y = y_positions[row]
            
            # Add to PDF
            p.drawImage(temp_path, x, y, width=card_width, height=card_height)
            
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass
            
            card_count += 1
            
        except Exception as e:
            # Log error but continue with other cards
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating card for {physical_card.card_number}: {str(e)}")
            continue
    
    p.save()
    buffer.seek(0)
    return buffer.getvalue()
