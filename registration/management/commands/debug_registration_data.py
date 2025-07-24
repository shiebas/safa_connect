from django.core.management.base import BaseCommand
from django.db.models import Count, Sum
from registration.models import Player, Official, PlayerClubRegistration
from membership.models import Invoice
from accounts.models import CustomUser
from django.db import models # Import models for Q object filter

class Command(BaseCommand):
    help = 'Debug registration and invoice data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== DEBUGGING REGISTRATION DATA ===\n'))
        
        # Check users with NATIONAL roles
        national_admins = CustomUser.objects.filter(role='NATIONAL_ADMIN')
        national_accounts = CustomUser.objects.filter(role='NATIONAL_ACCOUNTS')
        
        self.stdout.write(f"National Admins: {national_admins.count()}")
        for admin in national_admins:
            self.stdout.write(f"  - {admin.get_full_name()} ({admin.email})")
        
        self.stdout.write(f"National Accounts: {national_accounts.count()}")
        for account in national_accounts:
            self.stdout.write(f"  - {account.get_full_name()} ({account.email})")
        
        self.stdout.write("\n" + "="*50 + "\n")
        
        # Check Players
        total_players = Player.objects.count()
        pending_players = Player.objects.filter(is_approved=False, status='PENDING').count()
        approved_players = Player.objects.filter(is_approved=True, status='ACTIVE').count()
        
        self.stdout.write(f"PLAYERS:")
        self.stdout.write(f"  Total: {total_players}")
        self.stdout.write(f"  Pending Approval: {pending_players}")
        self.stdout.write(f"  Approved: {approved_players}")
        
        # Show some sample pending players
        if pending_players > 0:
            self.stdout.write("\n  Sample Pending Players (awaiting approval):")
            for player in Player.objects.filter(is_approved=False, status='PENDING').order_by('-date_joined')[:5]:
                invoice_status = "No Invoice"
                try:
                    invoice = Invoice.objects.get(player=player)
                    invoice_status = f"Invoice #{invoice.invoice_number} ({invoice.status})"
                except Invoice.DoesNotExist:
                    pass
                except Invoice.MultipleObjectsReturned:
                    invoice_status = "Multiple Invoices"
                self.stdout.write(f"    - {player.get_full_name()} (ID: {player.id}, SAFA: {player.safa_id}) - {invoice_status}")
        
        self.stdout.write("\n" + "="*50 + "\n")
        
        # Check Officials
        total_officials = Official.objects.count()
        pending_officials = Official.objects.filter(is_approved=False, status='PENDING').count()
        approved_officials = Official.objects.filter(is_approved=True, status='ACTIVE').count()
        
        self.stdout.write(f"OFFICIALS:")
        self.stdout.write(f"  Total: {total_officials}")
        self.stdout.write(f"  Pending Approval: {pending_officials}")
        self.stdout.write(f"  Approved: {approved_officials}")
        
        # Show some sample pending officials
        if pending_officials > 0:
            self.stdout.write("\n  Sample Pending Officials:")
            for official in Official.objects.filter(is_approved=False, status='PENDING')[:5]:
                self.stdout.write(f"    - {official.get_full_name()} (ID: {official.id}, SAFA: {official.safa_id})")
        
        self.stdout.write("\n" + "="*50 + "\n")
        
        # Check Invoices
        total_invoices = Invoice.objects.count()
        pending_invoices = Invoice.objects.filter(status='PENDING').count()
        paid_invoices = Invoice.objects.filter(status='PAID').count()
        overdue_invoices = Invoice.objects.filter(status='OVERDUE').count()
        
        total_amount = Invoice.objects.aggregate(total=Sum('amount'))['total'] or 0
        pending_amount = Invoice.objects.filter(status='PENDING').aggregate(total=Sum('amount'))['total'] or 0
        paid_amount = Invoice.objects.filter(status='PAID').aggregate(total=Sum('amount'))['total'] or 0
        
        self.stdout.write(f"INVOICES:")
        self.stdout.write(f"  Total: {total_invoices} (R{total_amount:.2f})")
        self.stdout.write(f"  Pending: {pending_invoices} (R{pending_amount:.2f})")
        self.stdout.write(f"  Paid: {paid_invoices} (R{paid_amount:.2f})")
        self.stdout.write(f"  Overdue: {overdue_invoices}")
        
        # Show some sample invoices
        if total_invoices > 0:
            self.stdout.write("\n  Sample Invoices:")
            for invoice in Invoice.objects.select_related('player', 'official')[:5]:
                member_name = invoice.player.get_full_name() if invoice.player else (
                    invoice.official.get_full_name() if invoice.official else "Unknown"
                )
                self.stdout.write(f"    - {invoice.invoice_number}: {member_name} - R{invoice.amount:.2f} ({invoice.status})")
        
        self.stdout.write("\n" + "="*50 + "\n")
        
        # Check Player Club Registrations
        total_registrations = PlayerClubRegistration.objects.count()
        active_registrations = PlayerClubRegistration.objects.filter(status='ACTIVE').count()
        pending_registrations = PlayerClubRegistration.objects.filter(status='PENDING').count()
        
        self.stdout.write(f"PLAYER CLUB REGISTRATIONS:")
        self.stdout.write(f"  Total: {total_registrations}")
        self.stdout.write(f"  Active: {active_registrations}")
        self.stdout.write(f"  Pending: {pending_registrations}")
        
        # Show some sample registrations
        if total_registrations > 0:
            self.stdout.write("\n  Sample Registrations:")
            for reg in PlayerClubRegistration.objects.select_related('player', 'club')[:5]:
                self.stdout.write(f"    - {reg.player.get_full_name()} -> {reg.club.name} ({reg.status})")
        
        self.stdout.write("\n" + "="*50 + "\n")
        
        # Check for potential issues
        self.stdout.write("POTENTIAL ISSUES:")
        
        # Players without SAFA IDs
        players_no_safa = Player.objects.filter(safa_id__isnull=True).count()
        if players_no_safa > 0:
            self.stdout.write(f"  - {players_no_safa} players without SAFA IDs")
        
        # Invoices without player or official
        orphaned_invoices = Invoice.objects.filter(player__isnull=True, official__isnull=True).count()
        if orphaned_invoices > 0:
            self.stdout.write(f"  - {orphaned_invoices} invoices without associated member")
        
        # Players with multiple active registrations
        from django.db.models import Count
        multi_registrations = Player.objects.annotate(
            active_count=Count('club_registrations', filter=models.Q(club_registrations__status='ACTIVE'))
        ).filter(active_count__gt=1).count()
        if multi_registrations > 0:
            self.stdout.write(f"  - {multi_registrations} players with multiple active club registrations")
        
        self.stdout.write(self.style.SUCCESS('\n=== DEBUG COMPLETE ==='))