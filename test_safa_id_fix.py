#!/usr/bin/env python
"""
Test script to verify SAFA ID preservation fix
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_connect.settings')
django.setup()

from membership.models import Member, Invoice, SAFASeasonConfig
from accounts.models import CustomUser
from geography.models import Club, LocalFootballAssociation, Region, Province, Country, NationalFederation

def test_safa_id_preservation():
    """Test that manually entered SAFA IDs are preserved"""
    print("🧪 Testing SAFA ID Preservation Fix")
    print("=" * 50)
    
    # Check if we have an active season
    active_season = SAFASeasonConfig.get_active_season()
    if not active_season:
        print("❌ No active season found. Please create an active season first.")
        return False
    
    print(f"✅ Active season: {active_season.season_year}")
    
    # Create test data if needed
    try:
        # Get or create test country and federation
        country, _ = Country.objects.get_or_create(name='South Africa')
        national_federation, _ = NationalFederation.objects.get_or_create(
            name='SAFA', 
            defaults={'country': country}
        )
        
        # Get or create test province, region, LFA, club
        province, _ = Province.objects.get_or_create(
            name='Gauteng',
            defaults={'national_federation': national_federation}
        )
        
        region, _ = Region.objects.get_or_create(
            name='Johannesburg',
            defaults={'province': province}
        )
        
        lfa, _ = LocalFootballAssociation.objects.get_or_create(
            name='Johannesburg LFA',
            defaults={'region': region}
        )
        
        club, _ = Club.objects.get_or_create(
            name='Test Club',
            defaults={
                'localfootballassociation': lfa,
                'status': 'ACTIVE'
            }
        )
        
        print(f"✅ Test data created: {club.name} in {lfa.name}")
        
        # Test 1: Create user with manual SAFA ID
        print("\n📋 Test 1: Manual SAFA ID Preservation")
        print("-" * 30)
        
        manual_safa_id = "TEST1"
        
        from datetime import date
        
        # Create a test user with manual SAFA ID
        test_user, created = CustomUser.objects.get_or_create(
            email='test_manual@example.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'Manual',
                'role': 'PLAYER',
                'date_of_birth': date(2000, 6, 15),  # Senior player - use date object
                'safa_id': manual_safa_id  # Set manual SAFA ID
            }
        )
        
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            print(f"✅ Created test user: {test_user.get_full_name()} with SAFA ID: {test_user.safa_id}")
        else:
            print(f"✅ Using existing test user: {test_user.get_full_name()} with SAFA ID: {test_user.safa_id}")
        
        # Verify SAFA ID was preserved
        if test_user.safa_id == manual_safa_id:
            print(f"✅ SAFA ID preserved correctly: {test_user.safa_id}")
        else:
            print(f"❌ SAFA ID not preserved. Expected: {manual_safa_id}, Got: {test_user.safa_id}")
            return False
        
        # Test 2: Create member and verify SAFA ID
        print("\n📋 Test 2: Member SAFA ID Verification")
        print("-" * 30)
        
        # Create a test member
        test_member, created = Member.objects.get_or_create(
            user=test_user,
            defaults={
                'safa_id': manual_safa_id,
                'first_name': 'Test',
                'last_name': 'Manual',
                'email': 'test_manual@example.com',
                'role': 'PLAYER',
                'status': 'PENDING',
                'date_of_birth': date(2000, 6, 15),  # Use date object
                'gender': 'M',
                'current_club': club,
                'province': province,
                'region': region,
                'lfa': lfa,
                'national_federation': national_federation,
                'current_season': active_season,
                'registration_method': 'SELF'
            }
        )
        
        if created:
            print(f"✅ Created test member: {test_member.get_full_name()}")
        else:
            print(f"✅ Using existing test member: {test_member.get_full_name()}")
        
        # Verify member SAFA ID
        if test_member.safa_id == manual_safa_id:
            print(f"✅ Member SAFA ID preserved correctly: {test_member.safa_id}")
        else:
            print(f"❌ Member SAFA ID not preserved. Expected: {manual_safa_id}, Got: {test_member.safa_id}")
            return False
        
        # Test 3: Create invoice and verify unit price
        print("\n📋 Test 3: Invoice Unit Price Display")
        print("-" * 30)
        
        try:
            invoice = Invoice.create_simple_member_invoice(test_member)
            if invoice:
                print(f"✅ Invoice created successfully:")
                print(f"   - Invoice Number: {invoice.invoice_number}")
                print(f"   - Subtotal: R{invoice.subtotal}")
                print(f"   - VAT Amount: R{invoice.vat_amount}")
                print(f"   - Total Amount: R{invoice.total_amount}")
                print(f"   - Status: {invoice.status}")
                
                # Check invoice items
                if invoice.items.exists():
                    item = invoice.items.first()
                    print(f"   - Item Description: {item.description}")
                    print(f"   - Unit Price: R{item.unit_price}")
                    print(f"   - Quantity: {item.quantity}")
                    print(f"   - Total Price (excl. VAT): R{item.total_price}")
                    print(f"   - Amount (incl. VAT): R{item.amount}")
                    
                    # Verify unit price is set correctly
                    if item.unit_price > 0:
                        print(f"✅ Unit price is displayed correctly: R{item.unit_price}")
                    else:
                        print(f"❌ Unit price is not set correctly: R{item.unit_price}")
                        return False
                else:
                    print("   - No invoice items found")
                    return False
            else:
                print("❌ Invoice creation failed")
                return False
        except Exception as e:
            print(f"❌ Error creating invoice: {e}")
            return False
        
        print("\n🎉 All tests passed! SAFA ID preservation and unit price display are working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_safa_id_preservation()
    if success:
        print("\n✅ SAFA ID preservation fix is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ SAFA ID preservation fix has issues!")
        sys.exit(1)
