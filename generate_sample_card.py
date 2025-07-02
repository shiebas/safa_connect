#!/usr/bin/env python
"""
Generate a sample card image that you can view directly
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_global.settings')
django.setup()

from membership_cards.card_generator import SAFACardGenerator

def generate_sample_card():
    print("Generating sample SAFA card...")
    
    # Create card generator instance
    generator = SAFACardGenerator()
    
    # Test with a sample member
    class SampleMember:
        id = 1
        first_name = "John"
        last_name = "Doe"
        safa_id = "SA123456"
        status = "Active"
        expiry_date = None
        
        def get_full_name(self):
            return f"{self.first_name} {self.last_name}"
    
    sample_member = SampleMember()
    
    try:
        # Generate card image
        card_image = generator.generate_card_image(sample_member)
        
        # Save to a file you can view
        output_path = "sample_safa_card.png"
        card_image.save(output_path, "PNG")
        
        print(f"✅ Sample card saved as: {output_path}")
        print(f"✅ Card size: {card_image.size}")
        print(f"✅ File size: {os.path.getsize(output_path)} bytes")
        
        # Generate mobile version too
        mobile_card_io = generator.generate_mobile_card(sample_member)
        with open("sample_safa_card_mobile.png", "wb") as f:
            f.write(mobile_card_io.getvalue())
        
        print(f"✅ Mobile card saved as: sample_safa_card_mobile.png")
        
        print("\n🎯 Open these files to see your new card design!")
        print("- sample_safa_card.png (full resolution)")
        print("- sample_safa_card_mobile.png (mobile version)")
        
    except Exception as e:
        print(f"❌ Error generating card: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_sample_card()
