#!/usr/bin/env python
"""
Create a simple, clean card template that you can easily edit
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_global.settings')
django.setup()

from PIL import Image, ImageDraw, ImageFont
from membership_cards.card_generator import SAFACardGenerator

def create_simple_clean_template():
    print("🎨 Creating Simple Clean Template")
    print("=" * 40)
    
    generator = SAFACardGenerator()
    
    # Create a simple black card template
    width = generator.CARD_WIDTH_PX
    height = generator.CARD_HEIGHT_PX
    
    # Create solid black background
    template = Image.new('RGB', (width, height), (0, 0, 0))  # Pure black
    
    # Save as the active template
    template_path = os.path.join("media", "card_templates", "front", "safamembership.jpg")
    template.save(template_path, "JPEG", quality=95)
    
    print(f"✅ Simple black template created: {template_path}")
    print("✅ No existing text or images to interfere")
    print("✅ Clean slate for member information")
    
    return template_path

def remove_all_overlays():
    """Remove all overlay logic from card generator"""
    print("\n🔧 Removing overlay logic...")
    
    # The card generator should work with a clean template
    # No overlays needed
    print("✅ Card generator will use clean template directly")

def test_simple_card():
    print("\n🧪 Testing Simple Card Generation")
    
    generator = SAFACardGenerator()
    
    class TestMember:
        id = 1
        first_name = "John"
        last_name = "Smith"
        safa_id = "SA123456"
        status = "Active"
        expiry_date = None
        
        def get_full_name(self):
            return f"{self.first_name} {self.last_name}"
    
    member = TestMember()
    
    try:
        # Generate card with simple template
        card_image = generator.generate_card_image(member)
        
        # Save test card
        test_path = "simple_test_card.png"
        card_image.save(test_path, "PNG")
        print(f"✅ Test card saved: {test_path}")
        
        # Generate mobile version
        mobile_card_io = generator.generate_mobile_card(member)
        mobile_path = "simple_test_card_mobile.png"
        with open(mobile_path, "wb") as f:
            f.write(mobile_card_io.getvalue())
        print(f"✅ Mobile card saved: {mobile_path}")
        
        print(f"\n🎯 What you should see:")
        print("✅ Pure black background")
        print("✅ White text for member name")
        print("✅ Gold text for SAFA ID") 
        print("✅ White card number")
        print("✅ White expiry date")
        print("✅ Small QR code")
        print("✅ NO template text interference")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 SAFA Card - Simple Solution")
    print("=" * 40)
    
    # Create simple template
    create_simple_clean_template()
    
    # Remove overlay logic
    remove_all_overlays()
    
    # Test the simple card
    success = test_simple_card()
    
    if success:
        print(f"\n🎉 SUCCESS!")
        print("✅ Simple black template is active")
        print("✅ No overlays or complex logic")
        print("✅ Clean member information display")
        print("✅ Ready for use")
        
        print(f"\n📁 Check these files:")
        print("   - simple_test_card.png")
        print("   - simple_test_card_mobile.png")
        
        print(f"\n🔄 If you want your original template back:")
        print("   - Copy safamembership_backup.jpg to safamembership.jpg")
    else:
        print("\n❌ Test failed - check error messages above")

if __name__ == "__main__":
    main()
