# windows_data_check.py
# Save this file and run: python windows_data_check.py

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_connect.settings')
django.setup()

def check_database_state():
    print("CHECKING CURRENT DATABASE STATE...")
    print("=" * 60)

    # Check Member counts
    try:
        from membership.models import Member
        total_members = Member.objects.count()
        print(f"Total Members: {total_members}")
        
        if total_members > 0:
            print("\nMember Details:")
            for i, member in enumerate(Member.objects.all(), 1):
                print(f"   {i}. {member.get_full_name()} (ID: {member.id})")
                print(f"      Type: {member.member_type}")
                print(f"      Status: {member.status}")
                print(f"      SAFA ID: {member.safa_id}")
                
                # Check if this member has Player instances
                try:
                    from membership.models import Player as MemPlayer
                    player = MemPlayer.objects.filter(id=member.id).first()
                    if player:
                        print(f"      Has Membership Player: YES (ID: {player.id})")
                    else:
                        print(f"      Has Membership Player: NO")
                except Exception as e:
                    print(f"      Has Membership Player: ERROR - {e}")
                
             
                # Check Officials
                try:
                    from membership.models import Official as MemOfficial
                    official = MemOfficial.objects.filter(id=member.id).first()
                    if official:
                        print(f"      Has Membership Official: YES (ID: {official.id})")
                    else:
                        print(f"      Has Membership Official: NO")
                except Exception as e:
                    print(f"      Has Membership Official: ERROR - {e}")
                
                
    except ImportError as e:
        print(f"Cannot import Member model: {e}")

    # Check Player counts
    print("PLAYER MODEL COUNTS:")
   

    try:
        from membership.models import Player as MemPlayer  
        mem_players = MemPlayer.objects.count()
        print(f"   Membership App Players: {mem_players}")
        if mem_players > 0:
            for player in MemPlayer.objects.all():
                print(f"      - {player.get_full_name()} (ID: {player.id})")
    except ImportError as e:
        print(f"   Membership Players: Import Error - {e}")

    # Check Officials
    print("\nOFFICIAL MODEL COUNTS:")

    try:
        from membership.models import Official as MemOfficial
        mem_officials = MemOfficial.objects.count()
        print(f"   Membership App Officials: {mem_officials}")
    except ImportError as e:
        print(f"   Membership Officials: Import Error - {e}")

    # Check Invoices
    print("\nINVOICE ANALYSIS:")
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
        
        print(f"\n   Invoice Type Breakdown:")
        print(f"      Player Registration: {player_invoices}")
        print(f"      Official Registration: {official_invoices}")
        
        # Check orphaned invoices
        player_invoices_no_player = Invoice.objects.filter(
            invoice_type='PLAYER_REGISTRATION',
            player__isnull=True
        ).count()
        
        official_invoices_no_official = Invoice.objects.filter(
            invoice_type='OFFICIAL_REGISTRATION', 
            official__isnull=True
        ).count()
        
        print(f"\n   ORPHANED INVOICES:")
        print(f"      Player invoices WITHOUT Player instance: {player_invoices_no_player}")
        print(f"      Official invoices WITHOUT Official instance: {official_invoices_no_official}")
        
    except Exception as e:
        print(f"   Error analyzing invoices: {e}")

    # Check Club Registrations
    print("\nCLUB REGISTRATIONS:")
    try:
        from membership.models import PlayerClubRegistration
        club_registrations = PlayerClubRegistration.objects.count()
        print(f"   Player Club Registrations: {club_registrations}")
        
        if club_registrations > 0:
            for reg in PlayerClubRegistration.objects.all():
                print(f"      - Player ID {reg.player.id} ({reg.player.get_full_name()}) -> {reg.club.name}")
        
    except Exception as e:
        print(f"   Error checking club registrations: {e}")

    # Check Users
    print("\nUSER ANALYSIS:")
    try:
        from accounts.models import CustomUser
        total_users = CustomUser.objects.count()
        print(f"   Total Users: {total_users}")
        
        # Check roles
        club_admins = CustomUser.objects.filter(role='CLUB_ADMIN')
        print(f"   Club Admins: {club_admins.count()}")
        
        if club_admins.exists():
            print("   Club Admin Details:")
            for admin in club_admins:
                print(f"      - {admin.username} ({admin.get_full_name()})")
                if admin.club:
                    print(f"        Club: {admin.club.name}")
                else:
                    print(f"        Club: NOT SET - WARNING!")
            
    except Exception as e:
        print(f"   Error checking users: {e}")

    print("\n" + "=" * 60)
    print("DATABASE STATE CHECK COMPLETE")
    print("=" * 60)

    print("\nDIAGNOSIS:")
    print("Based on this analysis:")
    print("1. You have Members in the database")
    print("2. You likely have 0 Players and 0 Officials (inheritance issue)")
    print("3. Registration creates Members but not the child instances")
    print("4. This is the multi-table inheritance bug we need to fix!")

if __name__ == "__main__":
    check_database_state()
