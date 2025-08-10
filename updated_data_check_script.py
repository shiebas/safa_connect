# updated_data_check_script.py
# Run this in Django shell: python manage.py shell < updated_data_check_script.py

print("🔍 CHECKING CURRENT DATABASE STATE (Updated for your structure)...")
print("="*60)

# Check Member counts
try:
    from membership.models import Member
    total_members = Member.objects.count()
    print(f"📊 Total Members: {total_members}")
    
    if total_members > 0:
        print("\nMember Details:")
        for i, member in enumerate(Member.objects.all(), 1):
            print(f"   {i}. {member.get_full_name()} (ID: {member.id})")
            print(f"      Type: {member.member_type}")
            print(f"      Status: {member.status}")
            print(f"      SAFA ID: {member.safa_id}")
            
            # Check if this member has Player/Official instances (both apps)
            
            # Check membership app Player
            try:
                from membership.models import Player as MemPlayer
                player = MemPlayer.objects.filter(id=member.id).first()
                if player:
                    print(f"      Has Membership Player: YES (ID: {player.id})")
                else:
                    print(f"      Has Membership Player: NO")
            except Exception as e:
                print(f"      Has Membership Player: ERROR - {e}")
            
            # Check registration app Player  
        
            # Check membership app Official
            try:
                from membership.models import Official as MemOfficial
                official = MemOfficial.objects.filter(id=member.id).first()
                if official:
                    print(f"      Has Membership Official: YES (ID: {official.id})")
                else:
                    print(f"      Has Membership Official: NO")
            except Exception as e:
                print(f"      Has Membership Official: ERROR - {e}")
            
            # Check registration app Official
          
            
except ImportError as e:
    print(f"❌ Cannot import Member model: {e}")

# Check Player counts (both locations)
print(f"⚽ PLAYER MODEL COUNTS:")

try:
    from membership.models import Player as MemPlayer  
    mem_players = MemPlayer.objects.count()
    print(f"   Membership App Players: {mem_players}")
    if mem_players > 0:
        for player in MemPlayer.objects.all():
            print(f"      - {player.get_full_name()} (ID: {player.id})")
except ImportError as e:
    print(f"   Membership Players: Import Error - {e}")

# Check Official counts (both locations)
print(f"\n🏅 OFFICIAL MODEL COUNTS:")


try:
    from membership.models import Official as MemOfficial
    mem_officials = MemOfficial.objects.count()
    print(f"   Membership App Officials: {mem_officials}")
    if mem_officials > 0:
        for official in MemOfficial.objects.all():
            print(f"      - {official.get_full_name()} (ID: {official.id})")
except ImportError as e:
    print(f"   Membership Officials: Import Error - {e}")

# Check Invoices (updated for your structure)
print(f"\n💰 INVOICE ANALYSIS:")
try:
    from membership.models import Invoice
    total_invoices = Invoice.objects.count()
    print(f"   Total Invoices: {total_invoices}")
    
    if total_invoices > 0:
        print("   Invoice Details:")
        for invoice in Invoice.objects.all():
            print(f"      Invoice #{invoice.invoice_number}: {invoice.invoice_type} - ${invoice.amount}")
            print(f"         Player linked: {'YES (ID: ' + str(invoice.player.id) + ')' if invoice.player else 'NO'}")
            print(f"         Official linked: {'YES (ID: ' + str(invoice.official.id) + ')' if invoice.official else 'NO'}")
            print(f"         Club linked: {'YES (' + invoice.club.name + ')' if invoice.club else 'NO'}")
            print(f"         Status: {invoice.status}")
    
    # Check problematic patterns
    player_invoices = Invoice.objects.filter(invoice_type='PLAYER_REGISTRATION').count()
    official_invoices = Invoice.objects.filter(invoice_type='OFFICIAL_REGISTRATION').count()
    
    print(f"\n   📊 Invoice Type Breakdown:")
    print(f"      Player Registration: {player_invoices}")
    print(f"      Official Registration: {official_invoices}")
    
    # Check orphaned invoices
    player_invoices_no_player = Invoice.objects.filter(
        invoice_type='PLAYER_REGISTRATION',
        player__isnull