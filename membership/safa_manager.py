# membership/safa_manager.py
# Business logic for SAFA invoice system

from django.db import transaction
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.contenttypes.models import ContentType
from .safa_models import SAFAInvoice, SAFAInvoicePayment, SAFASeasonConfig, SAFAFeeStructure


class SAFAInvoiceManager:
    """
    Business logic for SAFA invoice operations
    Works with existing models without modifying them
    """
    
    @classmethod
    def get_active_season_config(cls):
        """Get active season configuration"""
        return SAFASeasonConfig.get_active_season()
    
    @classmethod
    def calculate_pro_rata_amount(cls, annual_amount, registration_date=None, season_config=None):
        """
        Calculate pro-rata amount based on registration date and season
        Returns: (pro_rata_amount, months_remaining, period_description)
        """
        if not season_config:
            season_config = cls.get_active_season_config()
        
        if not season_config:
            return annual_amount, 12, "Full Season"
        
        if not registration_date:
            registration_date = timezone.now().date()
        
        # Check if registration is within current season
        if registration_date < season_config.season_start_date:
            # Registration before season starts - full amount
            return annual_amount, 12, "Full Season"
        elif registration_date > season_config.season_end_date:
            # Registration after season ends - next season (full amount)
            return annual_amount, 12, "Next Season"
        
        # Calculate months remaining in current season
        months_in_season = (season_config.season_end_date.year - season_config.season_start_date.year) * 12 + \
                          (season_config.season_end_date.month - season_config.season_start_date.month) + 1
        
        # Calculate months from registration date to season end
        months_remaining = (season_config.season_end_date.year - registration_date.year) * 12 + \
                          (season_config.season_end_date.month - registration_date.month) + 1
        
        # Ensure at least 1 month
        months_remaining = max(1, min(months_remaining, months_in_season))
        
        # Calculate pro-rata amount
        pro_rata_amount = (annual_amount * Decimal(months_remaining) / Decimal(months_in_season)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        period_description = f"{months_remaining} months ({registration_date.strftime('%b %Y')} - {season_config.season_end_date.strftime('%b %Y')})"
        
        return pro_rata_amount, months_remaining, period_description
    
    @classmethod
    def create_member_invoice(cls, member, registration_date=None, season_config=None):
        """
        Create SAFA invoice for individual members (Players/Officials)
        """
        if not season_config:
            season_config = cls.get_active_season_config()
        
        if not season_config:
            raise ValueError("No active season configuration found")
        
        if not registration_date:
            registration_date = timezone.now().date()
        
        # Check if invoice already exists for this season
        existing_invoice = SAFAInvoice.objects.filter(
            season_config=season_config,
            member=member,
            invoice_type='REGISTRATION'
        ).first()
        
        if existing_invoice:
            return existing_invoice
        
        # Determine entity type for fee lookup
        if hasattr(member, 'date_of_birth') and member.date_of_birth:
            age = (registration_date - member.date_of_birth).days // 365
            entity_type = 'PLAYER_JUNIOR' if age < 18 else 'PLAYER_SENIOR'
        else:
            entity_type = 'PLAYER_SENIOR'  # Default
        
        # Check if member has specific role for officials
        if hasattr(member, 'role'):
            if 'official' in str(member.role).lower():
                entity_type = 'OFFICIAL_GENERAL'
            elif 'referee' in str(member.role).lower():
                entity_type = 'OFFICIAL_REFEREE'
            elif 'coach' in str(member.role).lower():
                entity_type = 'OFFICIAL_COACH'
        
        # Get fee structure
        fee_structure = SAFAFeeStructure.get_fee_for_entity(entity_type, season_config.season_year)
        if not fee_structure:
            raise ValueError(f"No fee structure found for {entity_type} in season {season_config.season_year}")
        
        annual_amount = fee_structure.annual_fee
        
        # Calculate pro-rata if applicable
        if fee_structure.is_pro_rata:
            pro_rata_amount, months_remaining, period_description = cls.calculate_pro_rata_amount(
                annual_amount, registration_date, season_config
            )
            
            # Check minimum fee
            if fee_structure.minimum_fee and pro_rata_amount < fee_structure.minimum_fee:
                pro_rata_amount = fee_structure.minimum_fee
                period_description = f"Minimum fee applied"
        else:
            pro_rata_amount = annual_amount
            months_remaining = 12
            period_description = "Full Season"
        
        # Create invoice
        with transaction.atomic():
            invoice = SAFAInvoice.objects.create(
                season_config=season_config,
                member=member,
                subtotal=pro_rata_amount,
                vat_rate=season_config.vat_rate,
                invoice_type='REGISTRATION',
                is_pro_rata=fee_structure.is_pro_rata and months_remaining < 12,
                pro_rata_months=months_remaining if fee_structure.is_pro_rata else None,
                issued_by=getattr(member, 'registering_admin', None)
            )
        
        return invoice
    
    @classmethod
    def create_organization_invoice(cls, organization, org_type, season_config=None, registration_date=None):
        """
        Create SAFA invoice for organizational entities (Clubs, LFAs, etc.)
        """
        if not season_config:
            season_config = cls.get_active_season_config()
        
        if not season_config:
            raise ValueError("No active season configuration found")
        
        if not registration_date:
            registration_date = timezone.now().date()
        
        # Check if invoice already exists for this season
        content_type = ContentType.objects.get_for_model(organization)
        existing_invoice = SAFAInvoice.objects.filter(
            season_config=season_config,
            content_type=content_type,
            object_id=organization.id,
            invoice_type='ANNUAL_FEE'
        ).first()
        
        if existing_invoice:
            return existing_invoice
        
        # Get fee structure
        fee_structure = SAFAFeeStructure.get_fee_for_entity(org_type.upper(), season_config.season_year)
        if not fee_structure:
            raise ValueError(f"No fee structure found for {org_type} in season {season_config.season_year}")
        
        annual_amount = fee_structure.annual_fee
        
        # Calculate pro-rata if applicable
        if fee_structure.is_pro_rata:
            pro_rata_amount, months_remaining, period_description = cls.calculate_pro_rata_amount(
                annual_amount, registration_date, season_config
            )
            
            # Check minimum fee
            if fee_structure.minimum_fee and pro_rata_amount < fee_structure.minimum_fee:
                pro_rata_amount = fee_structure.minimum_fee
                period_description = "Minimum fee applied"
        else:
            pro_rata_amount = annual_amount
            months_remaining = 12
            period_description = "Full Season"
        
        # Create invoice
        with transaction.atomic():
            invoice = SAFAInvoice.objects.create(
                season_config=season_config,
                content_type=content_type,
                object_id=organization.id,
                subtotal=pro_rata_amount,
                vat_rate=season_config.vat_rate,
                invoice_type='ANNUAL_FEE',
                is_pro_rata=fee_structure.is_pro_rata and months_remaining < 12,
                pro_rata_months=months_remaining if fee_structure.is_pro_rata else None,
            )
        
        return invoice
    
    @classmethod
    def process_payment(cls, invoice, amount, payment_method='EFT', payment_reference='', processed_by=None):
        """
        Process a payment against a SAFA invoice
        Returns: (payment_record, invoice_updated)
        """
        amount = Decimal(str(amount))
        
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero")
        
        if amount > invoice.outstanding_amount:
            raise ValueError(f"Payment amount (R{amount}) exceeds outstanding amount (R{invoice.outstanding_amount})")
        
        with transaction.atomic():
            # Create payment record
            payment = SAFAInvoicePayment.objects.create(
                safa_invoice=invoice,
                amount=amount,
                payment_method=payment_method,
                payment_reference=payment_reference,
                processed_by=processed_by
            )
            
            # Update invoice
            invoice.add_payment(amount, payment_method, payment_reference)
        
        return payment, invoice
    
    @classmethod
    def generate_season_renewal_invoices(cls, season_config=None):
        """
        Generate renewal invoices for all active entities for a new season
        """
        if not season_config:
            # Create next season config or get existing
            current_season = cls.get_active_season_config()
            if not current_season:
                raise ValueError("No active season configuration found")
            
            next_year = current_season.season_year + 1
            season_config, created = SAFASeasonConfig.objects.get_or_create(
                season_year=next_year,
                defaults={
                    'season_start_date': current_season.season_start_date.replace(year=next_year),