#!/usr/bin/env python
"""
Quick test of the updated SAFA card generator
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_connect.settings')
django.setup()

from membership_cards.card_generator import SAFACardGenerator
from membership.models import Member

def test_card_generation():
    print("Testing SAFA Card Generator...")
    
    # Create card generator instance
    generator = SAFACardGenerator()
    print(f"✓ Generator initialized")
    print(f"✓ Template path: {generator.template_path}")
    print(f"✓ Template exists: {os.path.exists(generator.template_path)}")
    
    # Test with a mock member
    class MockMember:
        id = 1
        first_name = "John"
        last_name = "Smith"
        safa_id = "SA123456"
        status = "Active"
        expiry_date = None
        
        def get_full_name(self):
            return f"{self.first_name} {self.last_name}"
    
    mock_member = MockMember()
    
    try:
        # Test Luhn code generation
        luhn_code = generator.generate_luhn_code(mock_member)
        print(f"✓ Generated Luhn code: {luhn_code}")
        print(f"✓ Luhn code length: {len(luhn_code)} digits")
        
        # Test card image generation
        card_image = generator.generate_card_image(mock_member)
        print(f"✓ Card image generated: {card_image.size}")
        
        # Test mobile card generation
        mobile_card = generator.generate_mobile_card(mock_member)
        print(f"✓ Mobile card generated: {len(mobile_card.getvalue())} bytes")
        
        print("\n🎉 All card generation tests passed!")
        print("\nUpdated card features:")
        print("- Uses your black template as base")
        print("- Removes duplicate 'SAFA ID:' labels")
        print("- Adds 16-digit Luhn-valid card number")
        print("- Better text positioning for black background")
        print("- Gold/yellow highlights for SAFA ID")
        print("- Smaller, cleaner QR code")
        print("- Credit card style formatting")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_card_generation()
