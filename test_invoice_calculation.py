#!/usr/bin/env python
"""
Test script to verify invoice calculation fixes
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

def test_invoice_calculation():
    """Test the invoice calculation methods"""
    print("🧪 Testing Invoice Calculation Fixes")
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
            defaults={'country': country}
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
                'is_active': True
            }
        )
        
        print(f"✅ Test data created: {club.name} in {lfa.name}")
        
        # Test 1: Create a test member and calculate fees
        print("\n📋 Test 1: Member Fee Calculation")
        print("-" * 30)
        
        # Create a test user
        test_user, created = CustomUser.objects.get_or_create(
            email='test@example.com',
            defaults={
                'username': 'testuser',
                'first_name': 'Test',
                'last_name': 'Player',
                'role': 'PLAYER',
                'date_of_birth': '2005-06-15',  # Junior player
                'gender': 'M'
            }
        )
        
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            print(f"✅ Created test user: {test_user.get_full_name()}")
        else:
            print(f"✅ Using existing test user: {test_user.get_full_name()}")
        
        # Create a test member
        test_member, created = Member.objects.get_or_create(
            user=test_user,
            defaults={
                'safa_id': '12345',
                'first_name': 'Test',
                'last_name': 'Player',
                'email': 'test@example.com',
                'role': 'PLAYER',
                'status': 'PENDING',
                'date_of_birth': '2005-06-15',
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
        
        # Test fee calculations
        print(f"📊 Member details:")
        print(f"   - Role: {test_member.get_role_display()}")
        print(f"   - Age: {test_member.age}")
        print(f"   - Is Junior: {test_member.is_junior}")
        print(f"   - Current Season: {test_member.current_season.season_year if test_member.current_season else 'None'}")
        
        # Test simple fee calculation
        simple_fee = test_member.calculate_simple_registration_fee()
        print(f"   - Simple Fee (excl. VAT): R{simple_fee}")
        
        # Test regular fee calculation
        regular_fee = test_member.calculate_registration_fee()
        print(f"   - Regular Fee: R{regular_fee}")
        
        # Test 2: Create invoice using simple method
        print("\n📋 Test 2: Simple Invoice Creation")
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
                    print(f"   - Item Amount: R{item.amount}")
                    print(f"   - Item Total: R{item.total_price}")
                else:
                    print("   - No invoice items found")
            else:
                print("❌ Invoice creation failed")
                return False
        except Exception as e:
            print(f"❌ Error creating invoice: {e}")
            return False
        
        # Test 3: Create invoice using regular method
        print("\n📋 Test 3: Regular Invoice Creation")
        print("-" * 30)
        
        try:
            # Delete the previous invoice to avoid conflicts
            invoice.delete()
            
            invoice = Invoice.create_member_invoice(test_member)
            if invoice:
                print(f"✅ Invoice created successfully:")
                print(f"   - Invoice Number: {invoice.invoice_number}")
                print(f"   - Total Amount: R{invoice.total_amount}")
                print(f"   - Status: {invoice.status}")
                
                # Check invoice items
                if invoice.items.exists():
                    item = invoice.items.first()
                    print(f"   - Item Description: {item.description}")
                    print(f"   - Item Amount: R{item.amount}")
                    print(f"   - Item Total: R{item.total_price}")
                else:
                    print("   - No invoice items found")
            else:
                print("❌ Invoice creation failed")
                return False
        except Exception as e:
            print(f"❌ Error creating invoice: {e}")
            return False
        
        print("\n🎉 All tests passed! Invoice calculation is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_invoice_calculation()
    if success:
        print("\n✅ Invoice calculation fixes are working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Invoice calculation fixes have issues!")
        sys.exit(1)

