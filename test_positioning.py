#!/usr/bin/env python
"""
Enhanced card generator test with visual positioning guide
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_connect.settings')
django.setup()

from membership_cards.card_generator import SAFACardGenerator
from PIL import Image, ImageDraw

def create_positioning_guide():
    """Create a visual guide showing text placement areas"""
    print("Creating positioning guide...")
    
    generator = SAFACardGenerator()
    
    # Load the template
    template_path = generator.template_path
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return
    
    template = Image.open(template_path)
    template = template.resize((generator.CARD_WIDTH_PX, generator.CARD_HEIGHT_PX), Image.Resampling.LANCZOS)
    
    # Create overlay to show text positioning areas
    overlay = Image.new('RGBA', template.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Analyze safe areas
    try:
        safe_areas = generator.analyze_template_safe_areas(template)
        positions = generator.get_optimal_text_positions(template)
        
        print(f"✓ Found {len(safe_areas)} potential text areas")
        
        # Draw rectangles around safe areas
        for i, area in enumerate(safe_areas):
            left, top, right, bottom = area['region']
            color = (0, 255, 0, 100) if area['suitable_for_text'] else (255, 0, 0, 100)
            draw.rectangle([left, top, right, bottom], outline=color[:3], width=2)
            
            # Add brightness info
            brightness = int(area['brightness'])
            suitable = "✓" if area['suitable_for_text'] else "✗"
            draw.text((left + 5, top + 5), f"{suitable} {brightness}", fill=(255, 255, 255, 255))
        
        # Draw positioning markers
        markers = [
            (positions['name_pos'], "NAME", (255, 255, 0, 255)),
            (positions['id_pos'], "SAFA ID", (255, 215, 0, 255)),
            (positions['card_pos'], "CARD #", (255, 255, 255, 255)),
            (positions['expiry_pos'], "EXPIRY", (200, 200, 200, 255)),
            (positions['qr_pos'], "QR", (0, 255, 255, 255))
        ]
        
        for pos, label, color in markers:
            x, y = pos
            # Draw a small circle and label
            draw.ellipse([x-3, y-3, x+3, y+3], fill=color)
            draw.text((x+8, y-8), label, fill=color)
    
    except Exception as e:
        print(f"❌ Error analyzing template: {e}")
        return
    
    # Composite the overlay onto the template
    guide_image = Image.alpha_composite(template.convert('RGBA'), overlay)
    
    # Save the guide
    guide_path = "card_positioning_guide.png"
    guide_image.save(guide_path, "PNG")
    print(f"✓ Positioning guide saved: {guide_path}")
    
    return guide_path

def generate_improved_card():
    """Generate card with improved positioning"""
    print("\nGenerating improved card...")
    
    generator = SAFACardGenerator()
    
    # Test member
    class TestMember:
        id = 1
        first_name = "John"
        last_name = "Doe"
        safa_id = "SA123456"
        status = "Active"
        expiry_date = None
        
        def get_full_name(self):
            return f"{self.first_name} {self.last_name}"
    
    test_member = TestMember()
    
    try:
        # Generate the card
        card_image = generator.generate_card_image(test_member)
        
        # Save improved card
        card_path = "improved_safa_card.png"
        card_image.save(card_path, "PNG")
        print(f"✓ Improved card saved: {card_path}")
        
        # Also generate mobile version
        mobile_card_io = generator.generate_mobile_card(test_member)
        mobile_path = "improved_safa_card_mobile.png"
        with open(mobile_path, "wb") as f:
            f.write(mobile_card_io.getvalue())
        print(f"✓ Mobile card saved: {mobile_path}")
        
        return card_path, mobile_path
        
    except Exception as e:
        print(f"❌ Error generating card: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def main():
    print("🎯 SAFA Card Positioning Optimizer")
    print("=" * 50)
    
    # Create positioning guide
    guide_path = create_positioning_guide()
    
    # Generate improved card
    card_path, mobile_path = generate_improved_card()
    
    print("\n📊 Results:")
    print(f"1. Positioning Guide: {guide_path}")
    print(f"2. Full Resolution Card: {card_path}")
    print(f"3. Mobile Card: {mobile_path}")
    
    print("\n🔍 Positioning Guide Legend:")
    print("- Green rectangles: Safe areas for text (dark enough)")
    print("- Red rectangles: Avoid these areas (too bright)")
    print("- Colored dots: Actual text positions")
    print("- Numbers show brightness levels (lower = darker)")
    
    print("\n✨ Improvements made:")
    print("- Analyzes your template to find dark areas")
    print("- Positions text in safe zones")
    print("- Avoids overlapping template graphics")
    print("- Smaller QR code with background")
    print("- Better contrast and readability")

if __name__ == "__main__":
    main()
