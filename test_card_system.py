"""
Test script for SAFA digital card generation
Run this to verify the card system is working
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_connect.settings')
django.setup()

from membership.models import Member
from membership_cards.card_generator import SAFACardGenerator

def test_card_generation():
    """Test the digital card generation system"""
    print("🎯 Testing SAFA Digital Card Generation System")
    print("=" * 50)
    
    # Check if template exists
    generator = SAFACardGenerator()
    template_path = generator.template_path
    
    print(f"📁 Template Path: {template_path}")
    if os.path.exists(template_path):
        print("✅ Card template found!")
    else:
        print("❌ Card template NOT found!")
        print(f"   Please ensure your template is at: {template_path}")
        return False
    
    # Find a member with SAFA ID for testing
    test_member = Member.objects.filter(safa_id__isnull=False).first()
    
    if not test_member:
        print("❌ No members with SAFA IDs found for testing")
        print("   Please assign SAFA IDs to members first")
        return False
    
    print(f"👤 Test Member: {test_member.get_full_name()}")
    print(f"🆔 SAFA ID: {test_member.safa_id}")
    
    try:
        # Test mobile card generation
        print("\n📱 Testing mobile card generation...")
        mobile_card = generator.generate_mobile_card(test_member)
        print(f"✅ Mobile card generated successfully! Size: {len(mobile_card.read())} bytes")
        
        # Test print card generation
        print("\n🖨️ Testing print-ready PDF generation...")
        print_card = generator.generate_print_card_pdf(test_member)
        print(f"✅ Print card generated successfully! Size: {len(print_card.read())} bytes")
        
        # Test high-res digital card
        print("\n🖼️ Testing high-resolution digital card...")
        digital_card = generator.generate_card_image(test_member)
        print(f"✅ Digital card generated successfully! Dimensions: {digital_card.size}")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("=" * 50)
        print("Your SAFA digital card system is ready to use!")
        print(f"📍 Access your card at: /membership-cards/my-card/")
        print(f"🔧 Admin management at: /membership-cards/admin/")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during card generation: {str(e)}")
        print("   Please check your template and dependencies")
        return False

if __name__ == "__main__":
    success = test_card_generation()
    sys.exit(0 if success else 1)
