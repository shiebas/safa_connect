# membership/safa_invoice_manager.py
from django.db import transaction
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.contenttypes.models import ContentType
from .models import Invoice, InvoiceItem, InvoicePayment, InvoiceInstallment
from .config_models import SAFASeasonConfig, SAFAFeeStructure, SAFAPaymentPlan
from geography.models import Association, Province, Region, LocalFootballAssociation, Club

class SAFAInvoiceManager:
    """
    Comprehensive SAFA Invoice Management System
    Handles all invoice operations with proper VAT compliance and partial payments
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
        Create invoice for individual members (Players/Officials)
        """
        if not season_config:
            season_config = cls.get_active_season_config()
        
        if not season_config:
            raise ValueError("No active season configuration found")
        
        if not registration_date:
            registration_date = timezone.now().date()
        
        # Check if invoice already exists for this season
        existing_invoice = Invoice.objects.filter(
            season_config=season_config,
            player=member if isinstance(member, Player) else None,
            official=member if isinstance(member, Official) else None,
            invoice_type='REGISTRATION'
        ).first()
        
        if existing_invoice:
            return existing_invoice
        
        # Determine entity type for fee lookup
        if isinstance(member, Player):
            age = (registration_date - member.date_of_birth).days // 365
            entity_type = 'PLAYER_JUNIOR' if age < 18 else 'PLAYER_SENIOR'
        elif isinstance(member, Official):
            position_title = member.position.title.lower() if member.position else ""
            if 'referee' in position_title:
                entity_type = 'OFFICIAL_REFEREE'
            elif 'coach' in position_title:
                entity_type = 'OFFICIAL_COACH'
            elif 'secretary' in position_title:
                entity_type = 'OFFICIAL_SECRETARY'
            elif 'treasurer' in position_title:
                entity_type = 'OFFICIAL_TREASURER'
            elif 'committee' in position_title:
                entity_type = 'OFFICIAL_COMMITTEE'
            else:
                entity_type = 'OFFICIAL_GENERAL'
        else:
            entity_type = 'PLAYER_SENIOR'  # Default
        
        # Get fee structure
        fee_structure = SAFAFeeStructure.get_fee_for_entity(entity_type, season_config.season_year)
        if not fee_structure:
            raise ValueError(f"No fee structure found for {entity_type} in season {season_config.season_year}")
        
        annual_amount = fee_structure.annual_fee
        
        # Temporarily disable pro-rata calculation as per user request
        pro_rata_amount = annual_amount
        months_remaining = 12 # Not strictly needed if pro-rata is off, but for consistency
        period_description = "Full Season"
        is_pro_rata_active = False # New variable to control pro-rata logic

        # Create invoice
        with transaction.atomic():
            invoice = Invoice.objects.create(
                season_config=season_config,
                player=member if isinstance(member, Player) else None,
                official=member if isinstance(member, Official) else None,
                club=getattr(member, 'club', None),
                subtotal=pro_rata_amount,
                vat_rate=season_config.vat_rate,
                invoice_type='REGISTRATION',
                payment_terms=season_config.payment_due_days,
                is_pro_rata=is_pro_rata_active, # Use the new variable
                pro_rata_months=None, # Set to None if pro-rata is off
                issued_by=getattr(member, 'registering_admin', None)
            )
            
            # Create invoice item
            description = f"SAFA {entity_type.replace('_', ' ').title()} Registration - {season_config.season_year}"
            # Remove pro-rata description part
            
            InvoiceItem.objects.create(
                invoice=invoice,
                description=description,
                quantity=Decimal('1.00'),
                unit_price=pro_rata_amount,
                is_pro_rata=is_pro_rata_active, # Use the new variable
                original_amount=None, # Set to None if pro-rata is off
                pro_rata_period=None # Set to None if pro-rata is off
            )
        
        return invoice
    
    @classmethod
    def create_organization_invoice(cls, organization, org_type, season_config=None, registration_date=None):
        """
        Create invoice for organizational entities
        """
        if not season_config:
            season_config = cls.get_active_season_config()
        
        if not season_config:
            raise ValueError("No active season configuration found")
        
        if not registration_date:
            registration_date = timezone.now().date()
        
        # Check if invoice already exists for this season
        content_type = ContentType.objects.get_for_model(organization)
        existing_invoice = Invoice.objects.filter(
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
        
        # Create invoice with proper foreign key assignment
        invoice_data = {
            'season_config': season_config,
            'content_type': content_type,
            'object_id': organization.id,
            'subtotal': pro_rata_amount,
            'vat_rate': season_config.vat_rate,
            'invoice_type': 'ANNUAL_FEE',
            'payment_terms': season_config.payment_due_days,
            'is_pro_rata': fee_structure.is_pro_rata and months_remaining < 12,
            'pro_rata_months': months_remaining if fee_structure.is_pro_rata else None,
        }
        
        # Set specific foreign key based on organization type
        if isinstance(organization, Club):
            invoice_data['club'] = organization
        elif isinstance(organization, LocalFootballAssociation):
            invoice_data['lfa'] = organization
        elif isinstance(organization, Region):
            invoice_data['region'] = organization
        elif isinstance(organization, Province):
            invoice_data['province'] = organization
        elif isinstance(organization, Association):
            invoice_data['association'] = organization
        
        with transaction.atomic():
            invoice = Invoice.objects.create(**invoice_data)
            
            # Create invoice item
            description = f"SAFA {org_type.title()} Annual Membership - {season_config.season_year}"
            if fee_structure.is_pro_rata and months_remaining < 12:
                description += f" ({period_description})"
            
            InvoiceItem.objects.create(
                invoice=invoice,
                description=description,
                quantity=Decimal('1.00'),
                unit_price=pro_rata_amount,
                is_pro_rata=fee_structure.is_pro_rata and months_remaining < 12,
                original_amount=annual_amount if fee_structure.is_pro_rata and months_remaining < 12 else None,
                pro_rata_period=period_description if fee_structure.is_pro_rata and months_remaining < 12 else None
            )
        
        return invoice
    
    @classmethod
    def process_payment(cls, invoice, amount, payment_method='EFT', payment_reference='', processed_by=None):
        """
        Process a payment against an invoice
        Returns: (payment_record, invoice_updated)
        """
        amount = Decimal(str(amount))
        
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero")
        
        if amount > invoice.outstanding_amount:
            raise ValueError(f"Payment amount (R{amount}) exceeds outstanding amount (R{invoice.outstanding_amount})")
        
        with transaction.atomic():
            # Create payment record
            payment = InvoicePayment.objects.create(
                invoice=invoice,
                amount=amount,
                payment_method=payment_method,
                payment_reference=payment_reference,
                processed_by=processed_by,
                status='CONFIRMED'
            )
            
            # Update invoice
            invoice.add_payment(amount, payment_method, payment_reference)
            
            # Add note about payment
            from .models import InvoiceNote
            InvoiceNote.objects.create(
                invoice=invoice,
                note_type='PAYMENT',
                subject=f'Payment Received - R{amount}',
                content=f'Payment of R{amount} received via {payment_method}. Reference: {payment_reference}',
                created_by=processed_by
            )
        
        return payment, invoice
    
    @classmethod
    def create_payment_plan(cls, invoice, payment_plan):
        """
        Create installment schedule for an invoice based on payment plan
        """
        if invoice.payment_plan:
            raise ValueError("Invoice already has a payment plan")
        
        if invoice.total_amount < payment_plan.minimum_amount:
            raise ValueError(f"Invoice amount (R{invoice.total_amount}) is below minimum for this payment plan (R{payment_plan.minimum_amount})")
        
        # Calculate installment amount
        base_amount = invoice.total_amount
        processing_fees = payment_plan.installment_fee * payment_plan.number_of_installments
        total_with_fees = base_amount + processing_fees
        installment_amount = (total_with_fees / payment_plan.number_of_installments).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        with transaction.atomic():
            # Update invoice
            invoice.payment_plan = payment_plan
            invoice.save()
            
            # Create installments
            current_date = timezone.now().date()
            
            for i in range(payment_plan.number_of_installments):
                # Calculate due date based on frequency
                if payment_plan.frequency == 'MONTHLY':
                    due_date = current_date + timedelta(days=30 * (i + 1))
                elif payment_plan.frequency == 'QUARTERLY':
                    due_date = current_date + timedelta(days=90 * (i + 1))
                elif payment_plan.frequency == 'BIANNUAL':
                    due_date = current_date + timedelta(days=180 * (i + 1))
                else:  # ANNUAL
                    due_date = current_date + timedelta(days=365 * (i + 1))
                
                InvoiceInstallment.objects.create(
                    invoice=invoice,
                    installment_number=i + 1,
                    due_date=due_date,
                    amount=installment_amount
                )
        
        return invoice.installments.all()
    
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
                    'season_end_date': current_season.season_end_date.replace(year=next_year),
                    'vat_rate': current_season.vat_rate,
                    'payment_due_days': current_season.payment_due_days,
                    'is_renewal_season': True,
                    'created_by': current_season.created_by
                }
            )
        
        renewal_count = 0
        
        with transaction.atomic():
            # Generate for all active associations
            for association in Association.objects.all():
                try:
                    invoice = cls.create_organization_invoice(association, 'ASSOCIATION', season_config)
                    renewal_count += 1
                except Exception as e:
                    print(f"Failed to create invoice for association {association}: {e}")
            
            # Generate for all provinces
            for province in Province.objects.all():
                try:
                    invoice = cls.create_organization_invoice(province, 'PROVINCE', season_config)
                    renewal_count += 1
                except Exception as e:
                    print(f"Failed to create invoice for province {province}: {e}")
            
            # Generate for all regions
            for region in Region.objects.all():
                try:
                    invoice = cls.create_organization_invoice(region, 'REGION', season_config)
                    renewal_count += 1
                except Exception as e:
                    print(f"Failed to create invoice for region {region}: {e}")
            
            # Generate for all LFAs
            for lfa in LocalFootballAssociation.objects.all():
                try:
                    invoice = cls.create_organization_invoice(lfa, 'LFA', season_config)
                    renewal_count += 1
                except Exception as e:
                    print(f"Failed to create invoice for LFA {lfa}: {e}")
            
            # Generate for all active clubs
            for club in Club.objects.filter(status='ACTIVE'):
                try:
                    invoice = cls.create_organization_invoice(club, 'CLUB', season_config)
                    renewal_count += 1
                except Exception as e:
                    print(f"Failed to create invoice for club {club}: {e}")
            
            # Generate for all active players
            for player in Player.objects.filter(status='ACTIVE'):
                try:
                    invoice = cls.create_member_invoice(player, season_config=season_config)
                    renewal_count += 1
                except Exception as e:
                    print(f"Failed to create invoice for player {player}: {e}")
            
            # Generate for all active officials
            for official in Official.objects.filter(status='ACTIVE'):
                try:
                    invoice = cls.create_member_invoice(official, season_config=season_config)
                    renewal_count += 1
                except Exception as e:
                    print(f"Failed to create invoice for official {official}: {e}")
        
        return renewal_count, season_config
