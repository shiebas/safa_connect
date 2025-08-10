from .models import Invoice, InvoiceItem, InvoicePayment
from geography.models import Club
from accounts.models import CustomUser
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
from geography.models import Association, Province, Region, LocalFootballAssociation, Club
from .safa_invoice_manager import SAFAInvoiceManager
from .config_models import SAFASeasonConfig, SAFAFeeStructure


@receiver(post_save, sender=Player)
def create_player_invoice(sender, instance, created, **kwargs):
    """
    Auto-create SAFA invoice when player is created
    """
    if created:
        try:
            invoice = SAFAInvoiceManager.create_member_invoice(instance)
            print(f"✅ Created player invoice: {invoice.invoice_number} for {instance.get_full_name()}")
        except Exception as e:
            print(f"❌ Failed to create player invoice for {instance.get_full_name()}: {str(e)}")


@receiver(post_save, sender=Official)
def create_official_invoice(sender, instance, created, **kwargs):
    """
    Auto-create SAFA invoice when official is created
    """
    if created:
        try:
            invoice = SAFAInvoiceManager.create_member_invoice(instance)
            print(f"✅ Created official invoice: {invoice.invoice_number} for {instance.get_full_name()}")
        except Exception as e:
            print(f"❌ Failed to create official invoice for {instance.get_full_name()}: {str(e)}")


@receiver(post_save, sender=Club)
def create_club_invoice(sender, instance, created, **kwargs):
    """
    Auto-create SAFA invoice when club is created
    """
    if created:
        try:
            invoice = SAFAInvoiceManager.create_organization_invoice(instance, 'CLUB')
            print(f"✅ Created club invoice: {invoice.invoice_number} for {instance.name}")
        except Exception as e:
            print(f"❌ Failed to create club invoice for {instance.name}: {str(e)}")


@receiver(post_save, sender=LocalFootballAssociation)
def create_lfa_invoice(sender, instance, created, **kwargs):
    """
    Auto-create SAFA invoice when LFA is created
    """
    if created:
        try:
            invoice = SAFAInvoiceManager.create_organization_invoice(instance, 'LFA')
            print(f"✅ Created LFA invoice: {invoice.invoice_number} for {instance.name}")
        except Exception as e:
            print(f"❌ Failed to create LFA invoice for {instance.name}: {str(e)}")


@receiver(post_save, sender=Region)
def create_region_invoice(sender, instance, created, **kwargs):
    """
    Auto-create SAFA invoice when region is created
    """
    if created:
        try:
            invoice = SAFAInvoiceManager.create_organization_invoice(instance, 'REGION')
            print(f"✅ Created region invoice: {invoice.invoice_number} for {instance.name}")
        except Exception as e:
            print(f"❌ Failed to create region invoice for {instance.name}: {str(e)}")


@receiver(post_save, sender=Province)
def create_province_invoice(sender, instance, created, **kwargs):
    """
    Auto-create SAFA invoice when province is created
    """
    if created:
        try:
            invoice = SAFAInvoiceManager.create_organization_invoice(instance, 'PROVINCE')
            print(f"✅ Created province invoice: {invoice.invoice_number} for {instance.name}")
        except Exception as e:
            print(f"❌ Failed to create province invoice for {instance.name}: {str(e)}")


@receiver(post_save, sender=Association)
def create_association_invoice(sender, instance, created, **kwargs):
    """
    Auto-create SAFA invoice when association is created
    """
    if created:
        try:
            invoice = SAFAInvoiceManager.create_organization_invoice(instance, 'ASSOCIATION')
            print(f"✅ Created association invoice: {invoice.invoice_number} for {instance.name}")
        except Exception as e:
            print(f"❌ Failed to create association invoice for {instance.name}: {str(e)}")


@receiver(post_save, sender=Invoice)
def update_member_status_on_payment(sender, instance, **kwargs):
    """
    Update member status when invoice is fully paid
    """
    if instance.status == 'PAID' and not getattr(instance, '_member_activated', False):
        try:
            # Mark as activated to prevent recursion
            instance._member_activated = True
            
            # Activate the member
            if instance.player:
                if not instance.player.is_approved:
                    instance.player.is_approved = True
                    instance.player.status = 'ACTIVE'
                    instance.player.save()
                    print(f"✅ Activated player: {instance.player.get_full_name()}")
            
            elif instance.official:
                if not instance.official.is_approved:
                    instance.official.is_approved = True
                    instance.official.status = 'ACTIVE'
                    instance.official.save()
                    print(f"✅ Activated official: {instance.official.get_full_name()}")
                    
        except Exception as e:
            print(f"❌ Failed to activate member for invoice {instance.invoice_number}: {str(e)}")


@receiver(post_save, sender=SAFASeasonConfig)
def create_default_fee_structures(sender, instance, created, **kwargs):
    """
    Create default fee structures when a new season is created
    """
    if created:
        try:
            # Get previous season's fee structures as template
            previous_season = SAFASeasonConfig.objects.filter(
                season_year=instance.season_year - 1
            ).first()
            
            default_fees = {
                'ASSOCIATION': '50000.00',
                'PROVINCE': '25000.00',
                'REGION': '15000.00',
                'LFA': '10000.00',
                'CLUB': '5000.00',
                'PLAYER_JUNIOR': '100.00',
                'PLAYER_SENIOR': '200.00',
                'OFFICIAL_REFEREE': '250.00',
                'OFFICIAL_COACH': '200.00',
                'OFFICIAL_GENERAL': '150.00',
                'OFFICIAL_SECRETARY': '150.00',
                'OFFICIAL_TREASURER': '150.00',
                'OFFICIAL_COMMITTEE': '100.00',
            }
            
            # Create fee structures
            for entity_type, amount in default_fees.items():
                # Try to get amount from previous season
                if previous_season:
                    prev_fee = SAFAFeeStructure.objects.filter(
                        season_config=previous_season,
                        entity_type=entity_type
                    ).first()
                    if prev_fee:
                        amount = prev_fee.annual_fee
                
                SAFAFeeStructure.objects.get_or_create(
                    season_config=instance,
                    entity_type=entity_type,
                    defaults={
                        'annual_fee': amount,
                        'is_pro_rata': True,
                        'description': f'Annual {entity_type.replace("_", " ").title()} membership fee',
                        'created_by': instance.created_by
                    }
                )
            
            print(f"✅ Created default fee structures for season {instance.season_year}")
            
        except Exception as e:
            print(f"❌ Failed to create fee structures for season {instance.season_year}: {str(e)}")


@receiver(post_save, sender=InvoicePayment)
def update_invoice_on_payment(sender, instance, created, **kwargs):
    """
    Update invoice totals when a payment is made
    """
    if created:
        try:
            invoice = instance.invoice
            
            # Recalculate paid amount
            total_paid = invoice.payments.filter(
                status='CONFIRMED'
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            # Update invoice
            invoice.paid_amount = total_paid
            invoice.outstanding_amount = invoice.total_amount - total_paid
            
            # Update status
            if invoice.paid_amount >= invoice.total_amount:
                invoice.status = 'PAID'
                if not invoice.payment_date:
                    invoice.payment_date = timezone.now()
            elif invoice.paid_amount > 0:
                invoice.status = 'PARTIALLY_PAID'
            
            invoice.save()
            
            print(f"✅ Updated invoice {invoice.invoice_number} - Paid: R{invoice.paid_amount}")
            
        except Exception as e:
            print(f"❌ Failed to update invoice on payment: {str(e)}")


# Management command signals for seasonal operations
@receiver(post_save, sender=SAFASeasonConfig)
def setup_seasonal_operations(sender, instance, created, **kwargs):
    """
    Setup seasonal operations when season becomes active
    """
    if instance.is_active and not created:  # Season was just activated
        try:
            from .models import InvoiceNote
            
            # Mark all members as needing renewal if this is a renewal season
            if instance.is_renewal_season:
                # Update all active members to pending renewal
                Player.objects.filter(status='ACTIVE').update(status='PENDING_RENEWAL')
                Official.objects.filter(status='ACTIVE').update(status='PENDING_RENEWAL')
                
                print(f"✅ Season {instance.season_year} activated - Members marked for renewal")
                
        except Exception as e:
            print(f"❌ Failed to setup seasonal operations: {str(e)}")


@receiver(pre_save, sender=Invoice)
def check_overdue_invoices(sender, instance, **kwargs):
    """
    Check and update overdue invoice status
    """
    if instance.due_date and instance.due_date < timezone.now().date():
        if instance.status in ['PENDING', 'PARTIALLY_PAID']:
            instance.status = 'OVERDUE'


# Custom signal for bulk operations
from django.dispatch import Signal

# Define custom signals
invoice_bulk_created = Signal()
member_bulk_activated = Signal()
season_renewal_completed = Signal()


@receiver(invoice_bulk_created)
def handle_bulk_invoice_creation(sender, invoice_list, **kwargs):
    """
    Handle post-processing after bulk invoice creation
    """
    try:
        total_amount = sum(invoice.total_amount for invoice in invoice_list)
        count = len(invoice_list)
        
        from .models import InvoiceNote
        
        # Create a summary note
        if invoice_list:
            season = invoice_list[0].season_config
            InvoiceNote.objects.create(
                invoice=invoice_list[0],  # Attach to first invoice as reference
                note_type='SYSTEM',
                subject=f'Bulk Invoice Generation - Season {season.season_year}',
                content=f'Generated {count} invoices totaling R{total_amount:,.2f} for season {season.season_year}',
                is_internal=True
            )
        
        print(f"✅ Bulk invoice creation completed: {count} invoices, R{total_amount:,.2f} total")
        
    except Exception as e:
        print(f"❌ Failed to handle bulk invoice creation: {str(e)}")


@receiver(member_bulk_activated)
def handle_bulk_member_activation(sender, member_list, **kwargs):
    """
    Handle post-processing after bulk member activation
    """
    try:
        players = [m for m in member_list if isinstance(m, Player)]
        officials = [m for m in member_list if isinstance(m, Official)]
        
        print(f"✅ Bulk activation completed: {len(players)} players, {len(officials)} officials")
        
        # Could add email notifications, reporting, etc. here
        
    except Exception as e:
        print(f"❌ Failed to handle bulk member activation: {str(e)}")


@receiver(season_renewal_completed)
def handle_season_renewal_completion(sender, season_config, invoice_count, **kwargs):
    """
    Handle completion of season renewal process
    """
    try:
        from .models import InvoiceNote
        
        # Create system note about renewal completion
        InvoiceNote.objects.create(
            invoice=None,  # System-wide note
            note_type='SYSTEM',
            subject=f'Season {season_config.season_year} Renewal Completed',
            content=f'Season renewal process completed. Generated {invoice_count} renewal invoices.',
            is_internal=True
        )
        
        # Mark season as renewal completed
        season_config.is_renewal_season = False
        season_config.save()
        
        print(f"✅ Season {season_config.season_year} renewal completed: {invoice_count} invoices generated")
        
    except Exception as e:
        print(f"❌ Failed to handle season renewal completion: {str(e)}")


# Signal for automatic overdue checking
from django.core.management.base import BaseCommand
from django.db.models import Q


def check_and_update_overdue_invoices():
    """
    Utility function to check and update overdue invoices
    Can be called from management commands or scheduled tasks
    """
    try:
        today = timezone.now().date()
        
        # Find invoices that should be marked as overdue
        overdue_invoices = Invoice.objects.filter(
            due_date__lt=today,
            status__in=['PENDING', 'PARTIALLY_PAID']
        )
        
        count = overdue_invoices.update(status='OVERDUE')
        
        if count > 0:
            print(f"✅ Marked {count} invoices as overdue")
            
            # Create system notes for overdue invoices
            from .models import InvoiceNote
            for invoice in overdue_invoices[:10]:  # Limit to prevent too many notes
                InvoiceNote.objects.create(
                    invoice=invoice,
                    note_type='SYSTEM',
                    subject='Invoice Marked as Overdue',
                    content=f'Invoice automatically marked as overdue on {today}. Due date was {invoice.due_date}.',
                    is_internal=True
                )
        
        return count
        
    except Exception as e:
        print(f"❌ Failed to check overdue invoices: {str(e)}")
        return 0


# Signal for payment plan installment due dates
def check_installment_due_dates():
    """
    Check and update installment due dates
    """
    try:
        from .models import InvoiceInstallment
        today = timezone.now().date()
        
        # Find installments that are now overdue
        overdue_installments = InvoiceInstallment.objects.filter(
            due_date__lt=today,
            status='PENDING'
        )
        
        count = overdue_installments.update(status='OVERDUE')
        
        if count > 0:
            print(f"✅ Marked {count} installments as overdue")
        
        return count
        
    except Exception as e:
        print(f"❌ Failed to check installment due dates: {str(e)}")
        return 0


# Helper function to manually trigger invoice generation
def trigger_missing_invoices():
    """
    Check for entities that should have invoices but don't
    """
    try:
        active_season = SAFASeasonConfig.get_active_season()
        if not active_season:
            print("❌ No active season found")
            return 0
        
        created_count = 0
        
        # Check players without invoices
        players_without_invoices = Player.objects.filter(
            status__in=['ACTIVE', 'PENDING']
        ).exclude(
            player_invoices__season_config=active_season
        )
        
        for player in players_without_invoices:
            try:
                invoice = SAFAInvoiceManager.create_member_invoice(player)
                created_count += 1
                print(f"✅ Created missing invoice for player: {player.get_full_name()}")
            except Exception as e:
                print(f"❌ Failed to create invoice for player {player.get_full_name()}: {str(e)}")
        
        # Check officials without invoices
        officials_without_invoices = Official.objects.filter(
            status__in=['ACTIVE', 'PENDING']
        ).exclude(
            official_invoices__season_config=active_season
        )
        
        for official in officials_without_invoices:
            try:
                invoice = SAFAInvoiceManager.create_member_invoice(official)
                created_count += 1
                print(f"✅ Created missing invoice for official: {official.get_full_name()}")
            except Exception as e:
                print(f"❌ Failed to create invoice for official {official.get_full_name()}: {str(e)}")
        
        # Check clubs without invoices
        clubs_without_invoices = Club.objects.filter(
            status='ACTIVE'
        ).exclude(
            club_invoices__season_config=active_season
        )
        
        for club in clubs_without_invoices:
            try:
                invoice = SAFAInvoiceManager.create_organization_invoice(club, 'CLUB')
                created_count += 1
                print(f"✅ Created missing invoice for club: {club.name}")
            except Exception as e:
                print(f"❌ Failed to create invoice for club {club.name}: {str(e)}")
        
        print(f"✅ Created {created_count} missing invoices")
        return created_count
        
    except Exception as e:
        print(f"❌ Failed to trigger missing invoices: {str(e)}")
        return 0
        