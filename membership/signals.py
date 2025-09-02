# membership/signals.py - CORRECTED VERSION
# Simplified to work with the new SAFA models without complex dependencies

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

# Import the corrected models
from .models import (
    Member, SAFASeasonConfig, SAFAFeeStructure, Invoice, InvoiceItem,
    RegistrationWorkflow, ClubMemberQuota, MemberSeasonHistory,
    OrganizationSeasonRegistration
)




# ============================================================================
# MEMBER MANAGEMENT SIGNALS
# ============================================================================

@receiver(post_save, sender=Member)
def handle_member_creation(sender, instance, created, **kwargs):
    """Handle member creation and updates"""
    
    if created:
        print(f"✅ New member created: {instance.get_full_name()} ({instance.safa_id})")
        
        # Create registration workflow tracker
        try:
            workflow, workflow_created = RegistrationWorkflow.objects.get_or_create(
                member=instance
            )
            if workflow_created:
                print(f"✅ Created workflow tracker for {instance.get_full_name()}")
        except Exception as e:
            print(f"❌ Failed to create workflow for {instance.get_full_name()}: {str(e)}")
        
        # Invoice creation is now handled directly in the views to prevent duplicates
        # and ensure proper season configuration
        print(f"✅ Member {instance.get_full_name()} created - invoice will be created by view")
    
    # Update club quotas whenever member is saved
    if instance.current_club and instance.current_season:
        try:
            update_club_quotas_for_member(instance)
        except Exception as e:
            print(f"❌ Failed to update club quotas for {instance.get_full_name()}: {str(e)}")


@receiver(post_delete, sender=Member)
def handle_member_deletion(sender, instance, **kwargs):
    """Handle member deletion"""
    
    print(f"🗑️ Member deleted: {instance.get_full_name()} ({instance.safa_id})")
    
    # Update club quotas when member is deleted
    if instance.current_club and instance.current_season:
        try:
            update_club_quotas_for_member(instance, deleted=True)
        except Exception as e:
            print(f"❌ Failed to update club quotas after deletion: {str(e)}")


def update_club_quotas_for_member(member, deleted=False):
    """Update club member quotas when member is saved or deleted"""
    
    if not member.current_club or not member.current_season:
        return
    
    try:
        quota, created = ClubMemberQuota.objects.get_or_create(
            club=member.current_club,
            season_config=member.current_season,
            defaults={
                'max_senior_players': 30,
                'max_junior_players': 50,
                'max_officials': 20,
            }
        )
        
        if created:
            print(f"✅ Created quota tracker for {member.current_club.name}")
        
        # Update the counts
        quota.update_counts()
        
        if not deleted:
            print(f"✅ Updated quotas for {member.current_club.name}")
        
    except Exception as e:
        print(f"❌ Error updating club quotas: {str(e)}")


# ============================================================================
# SEASON CONFIGURATION SIGNALS
# ============================================================================

@receiver(post_save, sender='geography.Province')
@receiver(post_save, sender='geography.Region')
@receiver(post_save, sender='geography.LocalFootballAssociation')
@receiver(post_save, sender='geography.Club')
def handle_organization_status_change(sender, instance, created, **kwargs):
    """Handle organization status changes and create invoices when they become active"""
    
    # Only proceed if this is a status change to ACTIVE
    if not created and 'status' in kwargs.get('update_fields', []):
        if instance.status == 'ACTIVE':
            print(f"✅ Organization {instance.name} ({instance.get_model_name()}) became ACTIVE")
            
            # Get the active season
            try:
                from .safa_config_models import SAFASeasonConfig
                active_season = SAFASeasonConfig.get_active_season()
                
                if active_season:
                    # Check if invoice already exists for this organization and season
                    from .models import Invoice
                    existing_invoice = Invoice.objects.filter(
                        content_type__model=instance.get_model_name().lower(),
                        object_id=instance.id,
                        season_config=active_season,
                        invoice_type='ORGANIZATION_MEMBERSHIP'
                    ).first()
                    
                    if not existing_invoice:
                        # Create organization invoice
                        invoice = Invoice.create_organization_invoice(
                            organization=instance,
                            season_config=active_season
                        )
                        if invoice:
                            print(f"✅ Created invoice {invoice.invoice_number} for {instance.name}")
                        else:
                            print(f"❌ Failed to create invoice for {instance.name}")
                    else:
                        print(f"ℹ️ Invoice already exists for {instance.name} in {active_season.season_year}")
                else:
                    print(f"⚠️ No active season found - cannot create invoice for {instance.name}")
                    
            except Exception as e:
                print(f"❌ Error creating organization invoice: {str(e)}")
        else:
            print(f"ℹ️ Organization {instance.name} status changed to {instance.status}")

# ============================================================================
# INVOICE MANAGEMENT SIGNALS
# ============================================================================

@receiver(post_save, sender=SAFASeasonConfig)
def handle_season_config_changes(sender, instance, created, **kwargs):
    """Handle season configuration creation and updates"""
    
    if created:
        print(f"✅ New season created: {instance.season_year}")
        
        # Create default fee structures for new season
        try:
            create_default_fee_structures(instance)
        except Exception as e:
            print(f"❌ Failed to create fee structures for season {instance.season_year}: {str(e)}")
    
    # Handle season activation
    if instance.is_active:
        try:
            # Deactivate all other seasons
            SAFASeasonConfig.objects.exclude(pk=instance.pk).update(is_active=False)
            print(f"✅ Season {instance.season_year} activated - other seasons deactivated")
            
            # Handle renewal season logic
            if instance.is_renewal_season:
                handle_renewal_season_activation(instance)
                
        except Exception as e:
            print(f"❌ Error handling season activation: {str(e)}")


def create_default_fee_structures(season_config):
    """Create default fee structures for a new season"""
    
    # Get previous season's fee structures as template
    previous_season = SAFASeasonConfig.objects.filter(
        season_year=season_config.season_year - 1
    ).first()
    
    # Default fee amounts (in case no previous season exists)
    default_fees = {
        'ASSOCIATION': Decimal('50000.00'),
        'PROVINCE': Decimal('25000.00'),
        'REGION': Decimal('15000.00'),
        'LFA': Decimal('10000.00'),
        'CLUB': Decimal('5000.00'),
        'PLAYER_JUNIOR': Decimal('100.00'),
        'PLAYER_SENIOR': Decimal('200.00'),
        'OFFICIAL_REFEREE': Decimal('250.00'),
        'OFFICIAL_COACH': Decimal('200.00'),
        'OFFICIAL_GENERAL': Decimal('150.00'),
        'OFFICIAL_SECRETARY': Decimal('150.00'),
        'OFFICIAL_TREASURER': Decimal('150.00'),
        'OFFICIAL_COMMITTEE': Decimal('100.00'),
    }
    
    created_count = 0
    
    for entity_type, default_amount in default_fees.items():
        # Try to get amount from previous season
        annual_fee = default_amount
        
        if previous_season:
            prev_fee = SAFAFeeStructure.objects.filter(
                season_config=previous_season,
                entity_type=entity_type
            ).first()
            if prev_fee:
                annual_fee = prev_fee.annual_fee
        
        # Create fee structure
        fee_structure, created = SAFAFeeStructure.objects.get_or_create(
            season_config=season_config,
            entity_type=entity_type,
            defaults={
                'annual_fee': annual_fee,
                'is_pro_rata': True,
                'minimum_fee': annual_fee / 4,  # 25% minimum
                'description': f'Annual {entity_type.replace("_", " ").title()} membership fee',
                'created_by': season_config.created_by
            }
        )
        
        if created:
            created_count += 1
    
    print(f"✅ Created {created_count} fee structures for season {season_config.season_year}")


def handle_renewal_season_activation(season_config):
    """Handle renewal season activation"""
    
    try:
        # Mark active members as needing renewal
        active_members = Member.objects.filter(status='ACTIVE')
        renewal_count = active_members.update(status='PENDING')
        
        print(f"✅ Season {season_config.season_year} renewal: {renewal_count} members marked for renewal")
        
        # Generate renewal invoices for active members
        invoice_count = 0
        for member in active_members:
            try:
                # Check if member already has invoice for this season
                existing_invoice = member.invoices.filter(
                    season_config=season_config,
                    status__in=['PENDING', 'PAID']
                ).first()
                
                if not existing_invoice:
                    # Use simple calculation for club-admin-created members, complex for regular registrations
                    if hasattr(member, 'registration_method') and member.registration_method == 'CLUB':
                        Invoice.create_simple_member_invoice(member)
                    else:
                        Invoice.create_member_invoice(member, season_config)
                    invoice_count += 1
                    
            except Exception as e:
                print(f"❌ Failed to create renewal invoice for {member.get_full_name()}: {str(e)}")
        
        print(f"✅ Generated {invoice_count} renewal invoices")
        
        # Mark renewal season as processed
        season_config.is_renewal_season = False
        season_config.save(update_fields=['is_renewal_season'])
        
    except Exception as e:
        print(f"❌ Error during renewal season processing: {str(e)}")


# ============================================================================
# INVOICE AND PAYMENT SIGNALS
# ============================================================================

@receiver(post_save, sender=Invoice)
def handle_invoice_changes(sender, instance, created, **kwargs):
    """Handle invoice creation and payment updates"""
    
    if created:
        print(f"✅ Invoice created: {instance.invoice_number} - R{instance.total_amount}")
    
    # Handle invoice payment completion
    if instance.status == 'PAID' and not getattr(instance, '_payment_processed', False):
        try:
            # Mark as processed to prevent recursion
            instance._payment_processed = True
            
            # Update member status when invoice is paid
            if instance.member:
                handle_member_payment_completion(instance.member, instance)
            
            # Update organization registration when invoice is paid
            if instance.organization:
                handle_organization_payment_completion(instance.organization, instance)
                
        except Exception as e:
            print(f"❌ Error processing invoice payment for {instance.invoice_number}: {str(e)}")


def handle_member_payment_completion(member, invoice):
    """Handle member payment completion"""
    
    try:
        # Update member status if needed
        if member.status == 'PENDING':
            member.status = 'ACTIVE'
            member.save(update_fields=['status'])
            print(f"✅ Member {member.get_full_name()} activated after payment")
        
        # Create or update season history
        history, created = MemberSeasonHistory.objects.get_or_create(
            member=member,
            season_config=invoice.season_config,
            defaults={
                'status': member.status,
                'club': member.current_club,
                'province': member.province,
                'region': member.region,
                'lfa': member.lfa,
                'registration_date': member.created,
                'registration_method': member.registration_method,
                'invoice_paid': True,
                'safa_approved': member.status == 'ACTIVE',
                'safa_approved_date': member.approved_date,
            }
        )
        
        if not created:
            # Update existing history
            history.invoice_paid = True
            history.save(update_fields=['invoice_paid'])
        
        # Copy associations for officials
        if member.role == 'OFFICIAL':
            history.associations.set(member.associations.all())
        
        # Update registration workflow
        try:
            workflow = member.workflow
            workflow.payment_status = 'COMPLETED'
            workflow.update_progress()
        except RegistrationWorkflow.DoesNotExist:
            pass
        
        print(f"✅ Updated season history for {member.get_full_name()}")
        
    except Exception as e:
        print(f"❌ Error handling member payment completion: {str(e)}")


def handle_organization_payment_completion(organization, invoice):
    """Handle organization payment completion"""
    
    try:
        from django.contrib.contenttypes.models import ContentType
        
        # Update organization registration status
        content_type = ContentType.objects.get_for_model(organization)
        
        org_registration, created = OrganizationSeasonRegistration.objects.get_or_create(
            season_config=invoice.season_config,
            content_type=content_type,
            object_id=organization.pk,
            defaults={
                'status': 'PAID',
                'invoice': invoice,
            }
        )
        
        if not created and org_registration.status != 'PAID':
            org_registration.status = 'PAID'
            org_registration.invoice = invoice
            org_registration.save()
        
        org_name = getattr(organization, 'name', str(organization))
        print(f"✅ Organization {org_name} registration updated to PAID status")
        
    except Exception as e:
        print(f"❌ Error handling organization payment completion: {str(e)}")


@receiver(pre_save, sender=Invoice)
def handle_invoice_status_updates(sender, instance, **kwargs):
    """Handle invoice status updates before saving"""
    
    try:
        # Check if invoice is overdue
        if instance.due_date and instance.due_date < timezone.now().date():
            if instance.status in ['PENDING']:
                instance.status = 'OVERDUE'
        
        # Calculate outstanding amount
        if hasattr(instance, 'total_amount') and hasattr(instance, 'paid_amount'):
            instance.outstanding_amount = instance.total_amount - instance.paid_amount
            
    except Exception as e:
        print(f"❌ Error in invoice pre-save: {str(e)}")


# ============================================================================
# EXTERNAL MODEL SIGNALS (Only if available)
# ============================================================================

if EXTERNAL_MODELS_AVAILABLE:
    
    @receiver(post_save, sender=Player)
    def handle_player_creation(sender, instance, created, **kwargs):
        """Create SAFA member record when Player is created"""
        
        if created:
            try:
                # Check if Member already exists for this player
                if hasattr(instance, 'member_profile'):
                    return
                
                # Create corresponding Member record
                member = Member.objects.create(
                    user=getattr(instance, 'user', None),
                    first_name=instance.first_name,
                    last_name=instance.last_name,
                    email=instance.email,
                    phone_number=getattr(instance, 'phone_number', ''),
                    date_of_birth=instance.date_of_birth,
                    gender=getattr(instance, 'gender', ''),
                    id_number=getattr(instance, 'id_number', ''),
                    role='PLAYER',
                    status='PENDING',
                    registration_method='ADMIN',
                    current_season=SAFASeasonConfig.get_active_season(),
                    current_club=getattr(instance, 'club', None),
                )
                
                print(f"✅ Created SAFA member record for player: {instance.get_full_name()}")
                
            except Exception as e:
                print(f"❌ Failed to create SAFA member for player {instance.get_full_name()}: {str(e)}")
    
    
    @receiver(post_save, sender=Official)
    def handle_official_creation(sender, instance, created, **kwargs):
        """Create SAFA member record when Official is created"""
        
        if created:
            try:
                # Check if Member already exists for this official
                if hasattr(instance, 'member_profile'):
                    return
                
                # Create corresponding Member record
                member = Member.objects.create(
                    user=getattr(instance, 'user', None),
                    first_name=instance.first_name,
                    last_name=instance.last_name,
                    email=instance.email,
                    phone_number=getattr(instance, 'phone_number', ''),
                    date_of_birth=getattr(instance, 'date_of_birth', None),
                    gender=getattr(instance, 'gender', ''),
                    id_number=getattr(instance, 'id_number', ''),
                    role='OFFICIAL',
                    status='PENDING',
                    registration_method='ADMIN',
                    current_season=SAFASeasonConfig.get_active_season(),
                )
                
                # Set associations for officials
                if hasattr(instance, 'primary_association'):
                    member.associations.add(instance.primary_association)
                
                print(f"✅ Created SAFA member record for official: {instance.get_full_name()}")
                
            except Exception as e:
                print(f"❌ Failed to create SAFA member for official {instance.get_full_name()}: {str(e)}")
    
    
    @receiver(post_save, sender=Club)
    def handle_club_creation(sender, instance, created, **kwargs):
        """Create organization invoice when Club is created"""
        
        if created:
            try:
                active_season = SAFASeasonConfig.get_active_season()
                if not active_season:
                    return
                
                # Create organization invoice
                create_organization_invoice(instance, 'CLUB', active_season)
                
            except Exception as e:
                print(f"❌ Failed to create club invoice for {instance.name}: {str(e)}")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_organization_invoice(organization, entity_type, season_config):
    """Create invoice for organization registration"""
    
    try:
        from django.contrib.contenttypes.models import ContentType
        
        # Get fee structure for organization type
        fee_structure = SAFAFeeStructure.objects.filter(
            season_config=season_config,
            entity_type=entity_type
        ).first()
        
        if not fee_structure:
            print(f"❌ No fee structure found for {entity_type} in season {season_config.season_year}")
            return None
        
        # Check if invoice already exists
        content_type = ContentType.objects.get_for_model(organization)
        existing_invoice = Invoice.objects.filter(
            season_config=season_config,
            content_type=content_type,
            object_id=organization.pk,
            status__in=['PENDING', 'PAID']
        ).first()
        
        if existing_invoice:
            return existing_invoice
        
        # Create invoice
        invoice = Invoice.objects.create(
            season_config=season_config,
            content_type=content_type,
            object_id=organization.pk,
            invoice_type='ORGANIZATION_MEMBERSHIP',
            subtotal=fee_structure.annual_fee,
            vat_rate=season_config.vat_rate,
        )
        
        # Create line item
        InvoiceItem.objects.create(
            invoice=invoice,
            description=f"SAFA Membership - {fee_structure.get_entity_type_display()}",
            quantity=1,
            unit_price=fee_structure.annual_fee
        )
        
        org_name = getattr(organization, 'name', str(organization))
        print(f"✅ Created organization invoice {invoice.invoice_number} for {org_name}")
        
        return invoice
        
    except Exception as e:
        print(f"❌ Error creating organization invoice: {str(e)}")
        return None


def check_and_update_overdue_invoices():
    """Utility function to check and update overdue invoices"""
    
    try:
        today = timezone.now().date()
        
        # Find invoices that should be marked as overdue
        overdue_invoices = Invoice.objects.filter(
            due_date__lt=today,
            status='PENDING'
        )
        
        count = overdue_invoices.update(status='OVERDUE')
        
        if count > 0:
            print(f"✅ Marked {count} invoices as overdue")
        
        return count
        
    except Exception as e:
        print(f"❌ Failed to check overdue invoices: {str(e)}")
        return 0


def generate_missing_invoices_for_season(season_config):
    """Generate missing invoices for all entities in a season"""
    
    try:
        created_count = 0
        
        # Generate invoices for members without invoices
        members_without_invoices = Member.objects.filter(
            current_season=season_config,
            status__in=['ACTIVE', 'PENDING']
        ).exclude(
            invoices__season_config=season_config,
            invoices__status__in=['PENDING', 'PAID']
        )
        
        for member in members_without_invoices:
            try:
                # Use simple calculation for club-admin-created members, complex for regular registrations
                if hasattr(member, 'registration_method') and member.registration_method == 'CLUB':
                    Invoice.create_simple_member_invoice(member)
                else:
                    Invoice.create_member_invoice(member, season_config)
                created_count += 1
            except Exception as e:
                print(f"❌ Failed to create invoice for member {member.get_full_name()}: {str(e)}")
        
        # Generate invoices for organizations if external models are available
        if EXTERNAL_MODELS_AVAILABLE:
            # Generate for clubs
            clubs_without_invoices = Club.objects.filter(
                is_active=True
            ).exclude(
                invoice_organization__season_config=season_config,
                invoice_organization__status__in=['PENDING', 'PAID']
            )
            
            for club in clubs_without_invoices:
                try:
                    create_organization_invoice(club, 'CLUB', season_config)
                    created_count += 1
                except Exception as e:
                    print(f"❌ Failed to create invoice for club {club.name}: {str(e)}")
        
        print(f"✅ Generated {created_count} missing invoices for season {season_config.season_year}")
        return created_count
        
    except Exception as e:
        print(f"❌ Failed to generate missing invoices: {str(e)}")
        return 0


# ============================================================================
# CUSTOM SIGNALS FOR BUSINESS LOGIC
# ============================================================================

from django.dispatch import Signal

# Define custom signals
member_payment_completed = Signal()
organization_payment_completed = Signal()
season_renewal_started = Signal()
member_approved = Signal()


@receiver(member_payment_completed)
def handle_member_payment_completed_signal(sender, member, invoice, **kwargs):
    """Handle custom member payment completed signal"""
    
    try:
        print(f"🔔 Member payment completed signal: {member.get_full_name()}")
        
        # Send welcome email, SMS, etc.
        # Update external systems
        # Trigger other business processes
        
    except Exception as e:
        print(f"❌ Error handling member payment completed signal: {str(e)}")


@receiver(member_approved)
def handle_member_approved_signal(sender, member, approved_by, **kwargs):
    """Handle custom member approved signal"""
    
    try:
        print(f"🔔 Member approved signal: {member.get_full_name()}")
        
        # Send approval notification
        # Update workflow status
        if hasattr(member, 'workflow'):
            workflow = member.workflow
            workflow.safa_approval_status = 'COMPLETED'
            workflow.update_progress()
        
    except Exception as e:
        print(f"❌ Error handling member approved signal: {str(e)}")


# ============================================================================
# PERIODIC TASKS (Can be called from management commands)
# ============================================================================

def run_daily_maintenance():
    """Run daily maintenance tasks"""
    
    print("🔧 Running daily maintenance tasks...")
    
    # Check overdue invoices
    overdue_count = check_and_update_overdue_invoices()
    
    # Update club quotas for active season
    active_season = SAFASeasonConfig.get_active_season()
    if active_season:
        quotas = ClubMemberQuota.objects.filter(season_config=active_season)
        for quota in quotas:
            quota.update_counts()
        print(f"✅ Updated {quotas.count()} club quotas")
    
    # Clean up old workflow records
    # Send reminder emails
    # Generate reports
    
    print("🔧 Daily maintenance completed")


def run_monthly_maintenance():
    """Run monthly maintenance tasks"""
    
    print("🔧 Running monthly maintenance tasks...")
    
    # Generate monthly reports
    # Archive old records
    # Update statistics
    # Send monthly summaries
    
    print("🔧 Monthly maintenance completed")


# ============================================================================
# SIGNAL DEBUGGING
# ============================================================================

def enable_signal_debugging():
    """Enable detailed signal debugging"""
    
    import logging
    
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('membership.signals')
    
    # Log all signal handlers
    logger.debug("SAFA membership signals are enabled")


def disable_signals():
    """Disable signals temporarily (useful for data migrations)"""
    
    from django.db.models.signals import post_save, post_delete, pre_save
    
    # Disconnect all our signals
    post_save.disconnect(handle_member_creation, sender=Member)
    post_save.disconnect(handle_season_config_changes, sender=SAFASeasonConfig)
    post_save.disconnect(handle_invoice_changes, sender=Invoice)
    pre_save.disconnect(handle_invoice_status_updates, sender=Invoice)
    post_delete.disconnect(handle_member_deletion, sender=Member)
    
    print("⚠️ SAFA membership signals disabled")


def enable_signals():
    """Re-enable signals after they were disabled"""
    
    # Reconnect all our signals
    post_save.connect(handle_member_creation, sender=Member)
    post_save.connect(handle_season_config_changes, sender=SAFASeasonConfig)
    post_save.connect(handle_invoice_changes, sender=Invoice)
    pre_save.connect(handle_invoice_status_updates, sender=Invoice)
    post_delete.connect(handle_member_deletion, sender=Member)
    
    print("✅ SAFA membership signals enabled")