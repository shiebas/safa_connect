"""
SAFA Digital Membership Card Generator
Generates bank card sized membership cards with member data overlay
Standard credit card size: 85.60 × 53.98 mm (3.375" × 2.125")
"""

from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import io
import os
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm, inch
import qrcode
import tempfile
import logging

logger = logging.getLogger(__name__)

class SAFACardGenerator:
    """
    Generate SAFA membership cards with exact bank card dimensions
    Standard credit card size: 85.60 × 53.98 mm (3.375" × 2.125")
    """
    
    # Card dimensions in pixels at 300 DPI (print quality)
    CARD_WIDTH_PX = 1012  # 85.60mm at 300 DPI
    CARD_HEIGHT_PX = 638  # 53.98mm at 300 DPI
    
    # Card dimensions in mm
    CARD_WIDTH_MM = 85.60
    CARD_HEIGHT_MM = 53.98
    
    def __init__(self):
        self.template_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'safacard.png')
        self.font_paths = self._get_font_paths()
    
    def _get_font_paths(self):
        """Get system font paths for text rendering"""
        font_paths = {
            'regular': None,
            'bold': None
        }
        
        # Common font locations
        font_locations = [
            'C:/Windows/Fonts/',
            '/System/Library/Fonts/',
            '/usr/share/fonts/',
            '/usr/share/fonts/truetype/dejavu/',
            '/usr/share/fonts/TTF/',
            os.path.join(settings.STATIC_ROOT, 'fonts/') if settings.STATIC_ROOT else None,
        ]
        
        for location in font_locations:
            if location and os.path.exists(location):
                # Look for Arial or similar fonts
                for font_file in ['arial.ttf', 'Arial.ttf', 'Helvetica.ttf', 'DejaVuSans.ttf']:
                    font_path = os.path.join(location, font_file)
                    if os.path.exists(font_path) and not font_paths['regular']:
                        font_paths['regular'] = font_path
                
                for font_file in ['arialbd.ttf', 'Arial-Bold.ttf', 'Helvetica-Bold.ttf', 'DejaVuSans-Bold.ttf']:
                    font_path = os.path.join(location, font_file)
                    if os.path.exists(font_path) and not font_paths['bold']:
                        font_paths['bold'] = font_path
                
                if font_paths['regular'] and font_paths['bold']:
                    break
        
        return font_paths
    
    def generate_card_image(self, member, output_format='PNG'):
        """
        Generate a digital membership card image for a member.
        This method now checks for a custom template on the member's digital card.
        If a template is found, it uses the template's design and layout.
        Otherwise, it falls back to the default hardcoded design.
        
        Args:
            member: Member instance
            output_format: 'PNG', 'JPEG', or 'PDF'
            
        Returns:
            PIL Image
        """
        card_template = None
        if hasattr(member, 'digital_card') and member.digital_card and member.digital_card.template:
            card_template = member.digital_card.template

        # Determine template path and dimensions
        if card_template and hasattr(card_template.card_front_image, 'path'):
            template_path = card_template.card_front_image.path
            card_width = card_template.card_width
            card_height = card_template.card_height
        else:
            template_path = self.template_path
            card_width = self.CARD_WIDTH_PX
            card_height = self.CARD_HEIGHT_PX

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Card template not found: {template_path}")

        # Open and resize template
        template_image = Image.open(template_path)
        template_image = template_image.resize((card_width, card_height), Image.Resampling.LANCZOS)
        
        if template_image.mode != 'RGBA':
            template_image = template_image.convert('RGBA')
        
        draw = ImageDraw.Draw(template_image)
        
        # Load fonts
        try:
            if self.font_paths['regular']:
                font_regular = ImageFont.truetype(self.font_paths['regular'], 28)
                font_small = ImageFont.truetype(self.font_paths['regular'], 20)
            else:
                font_regular = ImageFont.load_default()
                font_small = ImageFont.load_default()
            if self.font_paths['bold']:
                font_bold = ImageFont.truetype(self.font_paths['bold'], 32)
            else:
                font_bold = font_regular
        except Exception as e:
            logger.warning(f"Font loading failed: {e}. Using default fonts.")
            font_regular, font_small, font_bold = ImageFont.load_default(), ImageFont.load_default(), ImageFont.load_default()

        # --- Member Data ---
        full_name = member.get_full_name().upper()
        safa_id = member.safa_id or "Not Assigned"
        luhn_code = self.generate_luhn_code(member)
        expiry_date = (datetime.now() + timedelta(days=365)).strftime("%m/%y")
        
        text_color = (255, 255, 255, 255)
        gold_color = (255, 215, 0, 255)

        # --- Positioning ---
        if card_template:
            name_pos = (card_template.name_position_x, card_template.name_position_y)
            # For other fields, we can either add them to the model or use default relative positioning
            id_pos = (name_pos[0], name_pos[1] + 40)
            card_pos = (name_pos[0], name_pos[1] + 80)
            expiry_pos = (card_width - 150, card_height - 50)
            qr_pos = (card_template.qr_position_x, card_template.qr_position_y)
        else:
            # Fallback to default positioning
            name_pos = (60, card_height - 180)
            id_pos = (60, card_height - 130)
            card_pos = (60, card_height - 90)
            expiry_pos = (card_width - 120, card_height - 50)
            qr_pos = (card_width - 62, 20)

        # --- Drawing Text ---
        draw.text(name_pos, full_name, font=font_bold, fill=text_color)
        draw.text(id_pos, safa_id, font=font_regular, fill=gold_color)
        formatted_luhn = f"{luhn_code[:4]} {luhn_code[4:8]} {luhn_code[8:12]} {luhn_code[12:16]}"
        draw.text(card_pos, formatted_luhn, font=font_regular, fill=text_color)
        draw.text((expiry_pos[0], expiry_pos[1] - 18), "VALID THRU", font=font_small, fill=text_color)
        draw.text(expiry_pos, expiry_date, font=font_regular, fill=text_color)
        
        # --- QR Code ---
        qr_data = f"SAFA:{safa_id}:{luhn_code}:{expiry_date}"
        qr = qrcode.QRCode(version=1, box_size=2, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").resize((40, 40), Image.Resampling.LANCZOS)
        
        # Add white background for QR code visibility
        qr_bg = Image.new('RGBA', (44, 44), (255, 255, 255, 255))
        template_image.paste(qr_bg, (qr_pos[0] - 2, qr_pos[1] - 2))
        template_image.paste(qr_img, qr_pos)

        return template_image

    def generate_mobile_card(self, member):
        """Generate mobile-optimized card (lower resolution for web display)"""
        card = self.generate_card_image(member)
        
        # Resize for mobile display (maintain aspect ratio)
        mobile_width = 400
        mobile_height = int((mobile_width * card.height) / card.width)
        mobile_card = card.resize((mobile_width, mobile_height), Image.Resampling.LANCZOS)
        
        # Save to BytesIO for web response
        img_io = io.BytesIO()
        mobile_card.save(img_io, format='PNG', quality=85, optimize=True)
        img_io.seek(0)
        
        return img_io
    
    def generate_print_card_pdf(self, member):
        """Generate print-ready PDF with exact bank card dimensions"""
        # Create PDF with card dimensions
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=(self.CARD_WIDTH_MM * mm, self.CARD_HEIGHT_MM * mm))
        
        # Generate high-res card image
        card_image = self.generate_card_image(member)
        
        # Save card image to temporary buffer
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = temp_file.name
            card_image.save(temp_path, format='PNG', dpi=(300, 300))
        
        try:
            # Add image to PDF at exact dimensions
            p.drawImage(temp_path, 0, 0, width=self.CARD_WIDTH_MM * mm, height=self.CARD_HEIGHT_MM * mm)
            p.save()
        finally:
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass
        
        buffer.seek(0)
        return buffer
    
    def save_member_card(self, member, card_type='digital'):
        """
        Save generated card to member's profile
        
        Args:
            member: Member instance
            card_type: 'digital', 'mobile', or 'print'
        """
        if card_type == 'mobile':
            card_data = self.generate_mobile_card(member)
            filename = f"member_{member.id}_card_mobile.png"
        elif card_type == 'print':
            card_data = self.generate_print_card_pdf(member)
            filename = f"member_{member.id}_card_print.pdf"
        else:  # digital
            card_image = self.generate_card_image(member)
            card_data = io.BytesIO()
            card_image.save(card_data, format='PNG', dpi=(300, 300))
            card_data.seek(0)
            filename = f"member_{member.id}_card.png"
        
        # Save to Django storage
        file_path = f"member_cards/{filename}"
        default_storage.save(file_path, ContentFile(card_data.read()))
        
        return file_path
    
    def bulk_generate_cards(self, members, card_type='digital'):
        """
        Generate cards for multiple members
        
        Args:
            members: QuerySet of Member instances
            card_type: 'digital', 'mobile', or 'print'
            
        Returns:
            List of generated file paths
        """
        generated_cards = []
        
        for member in members:
            try:
                # Only generate cards for members with SAFA IDs
                if member.safa_id:
                    file_path = self.save_member_card(member, card_type)
                    generated_cards.append({
                        'member': member,
                        'file_path': file_path,
                        'success': True
                    })
                else:
                    generated_cards.append({
                        'member': member,
                        'file_path': None,
                        'success': False,
                        'error': 'No SAFA ID assigned'
                    })
            except Exception as e:
                logger.error(f"Error generating card for member {member.id}: {str(e)}")
                generated_cards.append({
                    'member': member,
                    'file_path': None,
                    'success': False,
                    'error': str(e)
                })
        
        return generated_cards
    
    def generate_luhn_code(self, member):
        """Generate a 16-digit Luhn-valid code for the member"""
        import random
        
        # Start with member ID padded to create base
        base_id = str(member.id).zfill(6)
        
        # Create first 15 digits (prefix + member data + random)
        prefix = "5432"  # SAFA prefix
        member_part = base_id[:6]
        random_part = str(random.randint(10000, 99999))
        
        # Combine to make 15 digits
        partial_number = prefix + member_part + random_part
        partial_number = partial_number[:15]  # Ensure exactly 15 digits
        
        # Calculate Luhn check digit
        def luhn_checksum(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d * 2))
            return checksum % 10
        
        def is_luhn_valid(card_num):
            return luhn_checksum(card_num) == 0
        
        # Find the check digit that makes it valid
        for check_digit in range(10):
            test_number = partial_number + str(check_digit)
            if is_luhn_valid(test_number):
                return test_number
        
        # Fallback (should never happen)
        return partial_number + "0"
    
# Legacy support for existing code
def generate_physical_card_image(physical_card):
    """Legacy function - wrapper for new card generator"""
    generator = SAFACardGenerator()
    member = physical_card.user.member if hasattr(physical_card.user, 'member') else None
    if member:
        return generator.generate_card_image(member)
    else:
        raise ValueError("No member associated with this physical card")

def generate_print_ready_pdf(physical_cards):
    """Generate print-ready PDF with multiple cards"""
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
    except ImportError:
        raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")
    
    generator = SAFACardGenerator()
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
            member = physical_card.user.member if hasattr(physical_card.user, 'member') else None
            if not member:
                continue
                
            # Generate card image using new generator
            # This will automatically use the template on the digital_card if it exists
            card_img = generator.generate_card_image(member)
            
            # Use Django's temp directory instead of /tmp
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
            logger.error(f"Error generating card for {physical_card.card_number}: {str(e)}")
            continue
    
    p.save()
    buffer.seek(0)
    return buffer.getvalue()
