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
        self.template_path = os.path.join(settings.MEDIA_ROOT, 'card_templates', 'front', 'safamembership.jpg')
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
        Generate a digital membership card image for a member
        
        Args:
            member: Member instance
            output_format: 'PNG', 'JPEG', or 'PDF'
            
        Returns:
            PIL Image
        """
        # Load template image
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Card template not found: {self.template_path}")
        
        # Open and resize template to exact card dimensions
        template = Image.open(self.template_path)
        template = template.resize((self.CARD_WIDTH_PX, self.CARD_HEIGHT_PX), Image.Resampling.LANCZOS)
        
        # Convert to RGBA for transparency support
        if template.mode != 'RGBA':
            template = template.convert('RGBA')
        
        # Create drawing context
        draw = ImageDraw.Draw(template)
        
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
            # Fallback to default fonts
            font_regular = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_bold = ImageFont.load_default()
        
        # Member data - ONLY show member information, no template text
        full_name = member.get_full_name().upper()
        safa_id = member.safa_id or "Not Assigned"
        
        # Generate 16-digit Luhn code for the card
        luhn_code = self.generate_luhn_code(member)
        
        # Calculate expiry date (1 year from now)
        expiry_date = (datetime.now() + timedelta(days=365)).strftime("%m/%y")
        
        # Text colors for dark background
        text_color = (255, 255, 255, 255)  # White text
        gold_color = (255, 215, 0, 255)    # Gold for SAFA ID
        
        # Simple, clean positioning that works on any dark template
        # Member Name (prominent, top area)
        name_x = 60
        name_y = self.CARD_HEIGHT_PX - 180
        
        # Handle long names by splitting
        if len(full_name) > 18:
            words = full_name.split()
            if len(words) > 1:
                mid = len(words) // 2
                line1 = ' '.join(words[:mid])
                line2 = ' '.join(words[mid:])
                draw.text((name_x, name_y), line1, font=font_bold, fill=text_color)
                draw.text((name_x, name_y + 32), line2, font=font_bold, fill=text_color)
            else:
                draw.text((name_x, name_y), full_name[:18], font=font_bold, fill=text_color)
        else:
            draw.text((name_x, name_y), full_name, font=font_bold, fill=text_color)
        
        # SAFA ID (below name, gold color)
        id_x = 60
        id_y = self.CARD_HEIGHT_PX - 130
        draw.text((id_x, id_y), safa_id, font=font_regular, fill=gold_color)
        
        # 16-digit card number (credit card style)
        card_x = 60
        card_y = self.CARD_HEIGHT_PX - 90
        formatted_luhn = f"{luhn_code[:4]} {luhn_code[4:8]} {luhn_code[8:12]} {luhn_code[12:16]}"
        draw.text((card_x, card_y), formatted_luhn, font=font_regular, fill=text_color)
        
        # Expiry Date (bottom right corner)
        expiry_x = self.CARD_WIDTH_PX - 120
        expiry_y = self.CARD_HEIGHT_PX - 50
        draw.text((expiry_x, expiry_y - 18), "VALID THRU", font=font_small, fill=text_color)
        draw.text((expiry_x, expiry_y), expiry_date, font=font_regular, fill=text_color)
        
        # Generate compact QR Code (top right corner)
        qr_data = f"SAFA:{safa_id}:{luhn_code}:{expiry_date}"
        qr = qrcode.QRCode(version=1, box_size=2, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_size = 40  # Small QR code
        qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        # Position QR code in top right corner
        qr_x = self.CARD_WIDTH_PX - qr_size - 20
        qr_y = 20
        
        # Add white background for QR code visibility
        qr_bg = Image.new('RGBA', (qr_size + 4, qr_size + 4), (255, 255, 255, 255))
        template.paste(qr_bg, (qr_x - 2, qr_y - 2))
        template.paste(qr_img, (qr_x, qr_y))
        
        return template
    
    def generate_mobile_card(self, member):
        """Generate mobile-optimized card (lower resolution for web display)"""
        card = self.generate_card_image(member)
        
        # Resize for mobile display (maintain aspect ratio)
        mobile_width = 400
        mobile_height = int((mobile_width * self.CARD_HEIGHT_PX) / self.CARD_WIDTH_PX)
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
    
    def analyze_template_safe_areas(self, template_image):
        """
        Analyze the template to find safe areas for text placement
        This helps avoid placing text over important design elements
        """
        # Convert to grayscale to analyze brightness
        gray = template_image.convert('L')
        width, height = gray.size
        
        # Sample key areas to find dark regions suitable for white text
        safe_areas = []
        
        # Define potential text regions (left, top, right, bottom)
        regions = [
            (40, height - 200, 400, height - 50),  # Bottom left area
            (width - 400, height - 200, width - 40, height - 50),  # Bottom right
            (40, 100, 400, 250),  # Middle left
            (width - 400, 100, width - 40, 250),  # Middle right
        ]
        
        for region in regions:
            left, top, right, bottom = region
            # Ensure bounds are within image
            left = max(0, min(left, width))
            top = max(0, min(top, height))
            right = max(0, min(right, width))
            bottom = max(0, min(bottom, height))
            
            if right > left and bottom > top:
                # Sample pixels in this region to check average brightness
                sample_count = 0
                brightness_sum = 0
                
                # Sample every 10th pixel to check brightness
                for y in range(top, bottom, 10):
                    for x in range(left, right, 10):
                        if x < width and y < height:
                            pixel = gray.getpixel((x, y))
                            brightness_sum += pixel
                            sample_count += 1
                
                avg_brightness = brightness_sum / sample_count if sample_count > 0 else 255
                
                safe_areas.append({
                    'region': (left, top, right, bottom),
                    'brightness': avg_brightness,
                    'suitable_for_text': avg_brightness < 100  # Dark enough for white text
                })
        
        return safe_areas
    
    def get_optimal_text_positions(self, template_image):
        """Get optimal text positions based on template analysis"""
        try:
            safe_areas = self.analyze_template_safe_areas(template_image)
            
            # Find the best area for main text (largest suitable area)
            suitable_areas = [area for area in safe_areas if area['suitable_for_text']]
            
            if suitable_areas:
                # Use the darkest area for best contrast
                best_area = min(suitable_areas, key=lambda x: x['brightness'])
                left, top, right, bottom = best_area['region']
                
                return {
                    'name_pos': (left + 10, bottom - 120),
                    'id_pos': (left + 10, bottom - 80),
                    'card_pos': (left + 10, bottom - 50),
                    'expiry_pos': (right - 120, bottom - 30),
                    'qr_pos': (self.CARD_WIDTH_PX - 60, 15)
                }
        except Exception as e:
            logger.warning(f"Template analysis failed: {e}")
        
        # Fallback to conservative positioning
        return {
            'name_pos': (50, self.CARD_HEIGHT_PX - 160),
            'id_pos': (50, self.CARD_HEIGHT_PX - 120),
            'card_pos': (50, self.CARD_HEIGHT_PX - 80),
            'expiry_pos': (self.CARD_WIDTH_PX - 140, self.CARD_HEIGHT_PX - 40),
            'qr_pos': (self.CARD_WIDTH_PX - 60, 15)
        }
    
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
    """Legacy function - generate print-ready PDF with multiple cards"""
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
            card_img = generator.generate_card_image(member)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
                card_img.save(temp_path, 'PNG', dpi=(300, 300))
            
            try:
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
                card_count += 1
                
            finally:
                # Clean up temp file
                try:
                    os.remove(temp_path)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Error generating card for {physical_card.card_number}: {str(e)}")
            continue
    
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

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
