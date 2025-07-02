#!/usr/bin/env python
"""
Generate a clean SAFA card without template text showing through
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_global.settings')
django.setup()

from membership_cards.card_generator import SAFACardGenerator

def generate_clean_card():
    print("🎯 Generating Clean SAFA Card")
    print("=" * 40)
    
    generator = SAFACardGenerator()
    
    # Test member
    class CleanMember:
        id = 1
        first_name = "John"
        last_name = "Smith"
        safa_id = "SA123456"
        status = "Active"
        expiry_date = None
        
        def get_full_name(self):
            return f"{self.first_name} {self.last_name}"
    
    member = CleanMember()
    
    try:
        print("✓ Template found:", os.path.exists(generator.template_path))
        print("✓ Template path:", generator.template_path)
        
        # Generate card
        card_image = generator.generate_card_image(member)
        
        # Save clean card
        output_path = "clean_safa_card.png"
        card_image.save(output_path, "PNG")
        print(f"✓ Clean card saved: {output_path}")
        
        # Generate mobile version
        mobile_card_io = generator.generate_mobile_card(member)
        mobile_path = "clean_safa_card_mobile.png"
        with open(mobile_path, "wb") as f:
            f.write(mobile_card_io.getvalue())
        print(f"✓ Mobile card saved: {mobile_path}")
        
        print("\n🎉 SUCCESS!")
        print("\nWhat you should see now:")
        print("✅ Your black template as background")
        print("✅ Dark overlay hiding template text")
        print("✅ ONLY member information displayed:")
        print("   - Member name (white, bold)")
        print("   - SAFA ID (gold/yellow)")
        print("   - 16-digit card number (white)")
        print("   - Expiry date (white, bottom right)")
        print("   - Small QR code (top right)")
        print("✅ NO template text showing through")
        
        print(f"\n📁 Open these files to see the clean design:")
        print(f"   - {output_path}")
        print(f"   - {mobile_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_clean_card()
