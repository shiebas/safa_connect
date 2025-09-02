#!/usr/bin/env python
"""
Test script for organization invoice creation
Run this from the Django shell: python manage.py shell < test_organization_invoices.py
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_connect.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from membership.models import Invoice, SAFASeasonConfig, SAFAFeeStructure
from geography.models import Province, Region, LocalFootballAssociation, Club

def test_organization_invoice_creation():
    """Test creating organization invoices"""
    print("🧪 Testing Organization Invoice Creation")
    print("=" * 50)
    
    # Get active season
    try:
        active_season = SAFASeasonConfig.get_active_season()
        if not active_season:
            print("❌ No active season found. Please create a season first.")
            return
        print(f"✅ Active season: {active_season.season_year}")
    except Exception as e:
        print(f"❌ Error getting active season: {e}")
        return
    
    # Check fee structures
    print("\n🔍 Checking fee structures...")
    entity_types = ['PROVINCE', 'REGION', 'LFA', 'CLUB']
    for entity_type in entity_types:
        fee_structure = SAFAFeeStructure.get_fee_for_entity(
            entity_type=entity_type,
            season_year=active_season.season_year
        )
        if fee_structure:
            print(f"✅ {entity_type}: R{fee_structure.annual_fee}")
        else:
            print(f"❌ {entity_type}: No fee structure found")
    
    # Test creating invoices for existing organizations
    print("\n🔍 Testing invoice creation...")
    
    # Test Province invoice
    try:
        province = Province.objects.filter(status='ACTIVE').first()
        if province:
            print(f"📋 Testing Province: {province.name}")
            invoice = Invoice.create_organization_invoice(
                organization=province,
                season_config=active_season
            )
            if invoice:
                print(f"✅ Created invoice {invoice.invoice_number} for {province.name}")
            else:
                print(f"❌ Failed to create invoice for {province.name}")
        else:
            print("⚠️ No active provinces found")
    except Exception as e:
        print(f"❌ Error creating province invoice: {e}")
    
    # Test Region invoice
    try:
        region = Region.objects.filter(status='ACTIVE').first()
        if region:
            print(f"📋 Testing Region: {region.name}")
            invoice = Invoice.create_organization_invoice(
                organization=region,
                season_config=active_season
            )
            if invoice:
                print(f"✅ Created invoice {invoice.invoice_number} for {region.name}")
            else:
                print(f"❌ Failed to create invoice for {region.name}")
        else:
            print("⚠️ No active regions found")
    except Exception as e:
        print(f"❌ Error creating region invoice: {e}")
    
    # Test LFA invoice
    try:
        lfa = LocalFootballAssociation.objects.filter(status='ACTIVE').first()
        if lfa:
            print(f"📋 Testing LFA: {lfa.name}")
            invoice = Invoice.create_organization_invoice(
                organization=lfa,
                season_config=active_season
            )
            if invoice:
                print(f"✅ Created invoice {invoice.invoice_number} for {lfa.name}")
            else:
                print(f"❌ Failed to create invoice for {lfa.name}")
        else:
            print("⚠️ No active LFAs found")
    except Exception as e:
        print(f"❌ Error creating LFA invoice: {e}")
    
    # Test Club invoice
    try:
        club = Club.objects.filter(status='ACTIVE').first()
        if club:
            print(f"📋 Testing Club: {club.name}")
            invoice = Invoice.create_organization_invoice(
                organization=club,
                season_config=active_season
            )
            if invoice:
                print(f"✅ Created invoice {invoice.invoice_number} for {club.name}")
            else:
                print(f"❌ Failed to create invoice for {club.name}")
        else:
            print("⚠️ No active clubs found")
    except Exception as e:
        print(f"❌ Error creating club invoice: {e}")
    
    # Test invoice retrieval methods
    print("\n🔍 Testing invoice retrieval methods...")
    
    try:
        # Get all organization invoices
        all_invoices = Invoice.get_national_admin_invoices(season_year=active_season.season_year)
        print(f"✅ National admin invoices: {all_invoices.count()}")
        
        # Get invoices by type
        for entity_type in ['province', 'region', 'localfootballassociation', 'club']:
            type_invoices = Invoice.get_organization_invoices(
                organization_type=entity_type,
                season_year=active_season.season_year
            )
            print(f"✅ {entity_type.title()} invoices: {type_invoices.count()}")
        
        # Test province admin invoices
        if province:
            province_invoices = Invoice.get_province_admin_invoices(
                province=province,
                season_year=active_season.season_year
            )
            print(f"✅ Province admin invoices for {province.name}: {province_invoices.count()}")
        
    except Exception as e:
        print(f"❌ Error testing invoice retrieval: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_organization_invoice_creation()
