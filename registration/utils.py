# registration/utils.py
"""
Registration utilities for SAFA membership system
Provides centralized functions for registration management and validation
"""

from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.crypto import get_random_string
from decimal import Decimal
import logging

from .models import Player, Official, PlayerClubRegistration
from membership.models import Member, Invoice, InvoiceItem
from accounts.models import CustomUser

logger = logging.getLogger(__name__)


class RegistrationError(Exception):
    """Custom exception for registration-related errors"""
    pass


class MembershipManager:
    """Centralized manager for all membership operations"""
    
    # Fee structure
    FEES = {
        'NATIONAL_MEMBERSHIP': Decimal('100.00'),
        'CLUB_REGISTRATION': Decimal('200.00'),
        'REFEREE_REGISTRATION': Decimal('250.00'),
        'COACH_REGISTRATION': Decimal('200.00'),
        'OFFICIAL_REGISTRATION': Decimal('150.00'),
    }
    
    @staticmethod
    def generate_unique_email(first_name, last_name, domain='safa.system', member_type='member'):
        """Generate unique email addresses for members"""
        base_name = f"{first_name.lower().strip()}.{last_name.lower().strip()}"
        base_name = ''.join(c for c in base_name if c.isalnum() or c in '.-')
        
        # Add member type prefix for better organization
        type_prefix = {
            'PLAYER': 'player',
            'OFFICIAL': 'official',
            'MEMBER': 'member'
        }.get(member_type, 'member')
        
        base_email = f"{type_prefix}.{base_name}@{domain}"
        
        # Check if base email is available
        if not Member.objects.filter(email=base_email).exists():
            return base_email
        
        # Add incrementing number if base email exists
        counter = 1
        while counter < 1000:  # Prevent infinite loop
            email = f"{type_prefix}.{base_name}{counter}@{domain}"
            if not Member.objects.filter(email=email).exists():
                return email
            counter += 1
        
        # Fallback to random string
        random_suffix = get_random_string(6, allowed_chars='0123456789')
        return f"{type_prefix}.{base_name}.{random_suffix}@{domain}"
    
    @staticmethod
    def create_invoice(member, amount, description, invoice_type='MEMBERSHIP', 
                      club=None, association=None, due_days=30):
        """Create standardized invoices for members"""
        try:
            with transaction.atomic():
                invoice = Invoice.objects.create(
                    player=member,
                    club=club,
                    association=association,
                    amount=amount,
                    status='PENDING',
                    invoice_type=invoice_type,
                    due_date=timezone.now() + timezone.timedelta(days=due_days),
                    issued_by=getattr(member, 'registering_admin', None)
                )
                
                InvoiceItem.objects.create(
                    invoice=invoice,
                    description=description,
                    quantity=1,
                    unit_price=amount
                )
                
                logger.info(f"Created invoice #{invoice.invoice_number} for {member.get_full_name()}")
                return invoice
                
        except Exception as e:
            logger.error(f"Failed to create invoice for {member.get_full_name()}: {str(e)}")
            raise RegistrationError(f"Failed to create invoice: {str(e)}")
    
    @staticmethod
    def calculate_registration_fees(registration_type, position=None, club=None):
        """Calculate total fees for a registration type"""
        fees = []
        
        # Everyone pays national membership
        fees.append({
            'type': 'NATIONAL_MEMBERSHIP',
            'description': 'National Federation Membership Fee',
            'amount': MembershipManager.FEES['NATIONAL_MEMBERSHIP']
        })
        
        # Additional fees based on registration type
        if registration_type == 'PLAYER' and club:
            fees.append({
                'type': 'CLUB_REGISTRATION',
                'description': f'Club Registration Fee - {club.name}',
                'amount': MembershipManager.FEES['CLUB_REGISTRATION']
            })
        
        elif registration_type == 'OFFICIAL' and position:
            position_title = position.title.lower()
            if 'referee' in position_title:
                fee_type = 'REFEREE_REGISTRATION'
                description = 'Referee Registration Fee'
            elif 'coach' in position_title:
                fee_type = 'COACH_REGISTRATION'
                description = 'Coach Registration Fee'
            else:
                fee_type = 'OFFICIAL_REGISTRATION'
                description = 'Official Registration Fee'
            
            fees.append({
                'type': fee_type,
                'description': description,
                'amount': MembershipManager.FEES[fee_type]
            })
        
        return fees
    
    @classmethod
    def register_member(cls, form_data, registering_admin=None):
        """
        Main registration method that handles all member types
        Returns: (member_instance, invoices_created)
        """
        registration_type = form_data.get('registration_type', 'MEMBER')
        
        try:
            with transaction.atomic():
                # Create appropriate member instance
                if registration_type == 'PLAYER':
                    member = Player()
                elif registration_type == 'OFFICIAL':
                    member = Official()
                else:
                    member = Member()
                
                # Set basic member data
                cls._populate_member_data(member, form_data, registering_admin)
                
                # Set geography relationships
                cls._set_geography_relationships(member, form_data)
                
                # Handle role-specific data
                if registration_type == 'PLAYER':
                    member.role = 'PLAYER'
                elif registration_type == 'OFFICIAL':
                    member.role = 'OFFICIAL'
                    member.position = form_data.get('position')
                    # Set certification data if provided
                    if form_data.get('certification_number'):
                        member.certification_number = form_data['certification_number']
                    if form_data.get('certification_document'):
                        member.certification_document = form_data['certification_document']
                    if form_data.get('referee_level'):
                        member.referee_level = form_data['referee_level']
                
                # Generate email if not provided
                if not member.email:
                    member.email = cls.generate_unique_email(
                        member.first_name, 
                        member.last_name,
                        member_type=registration_type
                    )
                
                member.save()
                
                # Create club registration for players
                if registration_type == 'PLAYER' and member.club:
                    PlayerClubRegistration.objects.create(
                        player=member,
                        club=member.club,
                        status='PENDING',
                        position=form_data.get('playing_position'),
                        jersey_number=form_data.get('jersey_number')
                    )
                
                # Create invoices
                invoices = cls._create_member_invoices(member, registration_type)
                
                logger.info(f"Successfully registered {registration_type} member: {member.get_full_name()}")
                return member, invoices
                
        except Exception as e:
            logger.error(f"Registration failed for {form_data.get('first_name', 'Unknown')}: {str(e)}")
            raise RegistrationError(f"Registration failed: {str(e)}")
    
    @staticmethod
    def _populate_member_data(member, form_data, registering_admin=None):
        """Populate member instance with form data"""
        # Basic personal information
        member.first_name = form_data.get('first_name', '').strip().title()
        member.last_name = form_data.get('last_name', '').strip().title()
        member.email = form_data.get('email', '').strip().lower()
        member.phone_number = form_data.get('phone_number', '').strip()
        member.date_of_birth = form_data.get('date_of_birth')
        member.gender = form_data.get('gender')
        member.id_number = form_data.get('id_number', '').strip()
        member.passport_number = form_data.get('passport_number', '').strip()
        
        # Address information
        member.street_address = form_data.get('street_address', '').strip()
        member.suburb = form_data.get('suburb', '').strip()
        member.city = form_data.get('city', '').strip()
        member.state = form_data.get('state', '').strip()
        member.postal_code = form_data.get('postal_code', '').strip()
        member.country = form_data.get('country', 'South Africa').strip()
        
        # Emergency contact
        member.emergency_contact = form_data.get('emergency_contact', '').strip()
        member.emergency_phone = form_data.get('emergency_phone', '').strip()
        member.medical_notes = form_data.get('medical_notes', '').strip()
        
        # Files
        if form_data.get('profile_picture'):
            member.profile_picture = form_data['profile_picture']
        if form_data.get('id_document'):
            member.id_document = form_data['id_document']
        
        # Registration metadata
        member.status = 'PENDING'
        member.registered_by_admin = bool(registering_admin)
        member.registering_admin = registering_admin
        
        # Auto-determine member type from age if not set
        if not getattr(member, 'member_type', None) and member.date_of_birth:
            age = (timezone.now().date() - member.date_of_birth).days // 365
            member.member_type = 'JUNIOR' if age < 18 else 'SENIOR'
    
    @staticmethod
    def _set_geography_relationships(member, form_data):
        """Set geographic relationships with automatic hierarchy population"""
        member.province = form_data.get('province')
        member.region = form_data.get('region')
        member.lfa = form_data.get('lfa')
        member.club = form_data.get('club')
        member.association = form_data.get('association')
        
        # Auto-populate hierarchy from club if provided
        if member.club:
            if not member.lfa and hasattr(member.club, 'localfootballassociation'):
                member.lfa = member.club.localfootballassociation
            if not member.region and member.lfa and hasattr(member.lfa, 'region'):
                member.region = member.lfa.region
            if not member.province and member.region and hasattr(member.region, 'province'):
                member.province = member.region.province
        
        # Set national federation (default to SAFA)
        if not getattr(member, 'national_federation', None):
            try:
                from geography.models import NationalFederation
                safa = NationalFederation.objects.first()  # Assuming SAFA is the first/default
                member.national_federation = safa
            except Exception:
                pass  # Skip if NationalFederation doesn't exist yet
    
    @classmethod
    def _create_member_invoices(cls, member, registration_type):
        """Create all required invoices for a member"""
        invoices = []
        fee_structure = cls.calculate_registration_fees(
            registration_type, 
            getattr(member, 'position', None),
            member.club
        )
        
        for fee_info in fee_structure:
            try:
                invoice = cls.create_invoice(
                    member=member,
                    amount=fee_info['amount'],
                    description=fee_info['description'],
                    invoice_type='MEMBERSHIP' if fee_info['type'] == 'NATIONAL_MEMBERSHIP' else 'REGISTRATION',
                    club=member.club if fee_info['type'] == 'CLUB_REGISTRATION' else None,
                    association=member.association if hasattr(member, 'association') else None
                )
                invoices.append(invoice)
            except Exception as e:
                logger.error(f"Failed to create {fee_info['type']} invoice for {member.get_full_name()}: {str(e)}")
                # Continue creating other invoices even if one fails
        
        return invoices


class ApprovalManager:
    """Manager for member approval workflows"""
    
    @staticmethod
    def validate_member_for_approval(member):
        """
        Validate that a member meets all requirements for approval
        Returns: (is_valid: bool, errors: list)
        """
        errors = []
        
        # Check required documents
        if not member.profile_picture:
            errors.append("Profile picture is missing")
        
        if member.id_document_type == 'ID' and not member.id_document:
            errors.append("ID document is missing")
        elif member.id_document_type == 'PP' and not member.id_document:
            errors.append("Passport document is missing")
        
        # Check payment status
        unpaid_invoices = Invoice.objects.filter(
            player=member,
            status__in=['PENDING', 'OVERDUE']
        )
        if unpaid_invoices.exists():
            invoice_numbers = ", ".join([f"#{inv.invoice_number}" for inv in unpaid_invoices])
            errors.append(f"Unpaid invoices: {invoice_numbers}")
        
        # Check if member is already approved
        if member.status == 'ACTIVE':
            errors.append("Member is already approved")
        
        # Role-specific validations
        if isinstance(member, Official) and not member.position:
            errors.append("Position is required for officials")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def approve_member(member, approved_by):
        """
        Approve a member after validation
        Returns: (success: bool, message: str)
        """
        try:
            with transaction.atomic():
                # Validate before approval
                is_valid, errors = ApprovalManager.validate_member_for_approval(member)
                if not is_valid:
                    return False, f"Cannot approve member: {'; '.join(errors)}"
                
                # Update member status
                member.status = 'ACTIVE'
                member.approved_by = approved_by
                member.approved_date = timezone.now()
                
                # Set type-specific approval flags
                if isinstance(member, Player):
                    member.is_approved = True
                elif isinstance(member, Official):
                    member.is_approved = True
                
                member.save()
                
                # Send approval notification
                ApprovalManager._send_approval_notification(member)
                
                logger.info(f"Member {member.get_full_name()} approved by {approved_by.get_full_name()}")
                return True, f"Member {member.get_full_name()} has been approved successfully"
                
        except Exception as e:
            logger.error(f"Failed to approve member {member.get_full_name()}: {str(e)}")
            return False, f"Approval failed: {str(e)}"
    
    @staticmethod
    def reject_member(member, rejected_by, reason):
        """
        Reject a member with reason
        Returns: (success: bool, message: str)
        """
        try:
            with transaction.atomic():
                member.status = 'REJECTED'
                member.approved_by = rejected_by
                member.approved_date = timezone.now()
                member.rejection_reason = reason
                
                # Set type-specific rejection flags
                if isinstance(member, Player):
                    member.is_approved = False
                elif isinstance(member, Official):
                    member.is_approved = False
                
                member.save()
                
                # Send rejection notification
                ApprovalManager._send_rejection_notification(member, reason)
                
                logger.info(f"Member {member.get_full_name()} rejected by {rejected_by.get_full_name()}")
                return True, f"Member {member.get_full_name()} has been rejected"
                
        except Exception as e:
            logger.error(f"Failed to reject member {member.get_full_name()}: {str(e)}")
            return False, f"Rejection failed: {str(e)}"
    
    @staticmethod
    def _send_approval_notification(member):
        """Send email notification for member approval"""
        try:
            if not member.email:
                return
            
            subject = "SAFA Membership Application Approved"
            context = {
                'member': member,
                'safa_id': member.safa_id,
                'login_url': f"{settings.SITE_URL}/accounts/login/"
            }
            
            html_message = render_to_string('registration/emails/approval_notification.html', context)
            plain_message = render_to_string('registration/emails/approval_notification.txt', context)
            
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[member.email],
                fail_silently=True
            )
            
        except Exception as e:
            logger.error(f"Failed to send approval notification to {member.email}: {str(e)}")
    
    @staticmethod
    def _send_rejection_notification(member, reason):
        """Send email notification for member rejection"""
        try:
            if not member.email:
                return
            
            subject = "SAFA Membership Application Update"
            context = {
                'member': member,
                'rejection_reason': reason,
                'contact_email': settings.ADMIN_EMAIL
            }
            
            html_message = render_to_string('registration/emails/rejection_notification.html', context)
            plain_message = render_to_string('registration/emails/rejection_notification.txt', context)
            
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[member.email],
                fail_silently=True
            )
            
        except Exception as e:
            logger.error(f"Failed to send rejection notification to {member.email}: {str(e)}")


class PaymentManager:
    """Manager for payment-related operations"""
    
    @staticmethod
    def send_payment_reminder(member):
        """Send payment reminder to member"""
        try:
            unpaid_invoices = Invoice.objects.filter(
                player=member,
                status__in=['PENDING', 'OVERDUE']
            )
            
            if not unpaid_invoices.exists() or not member.email:
                return False, "No unpaid invoices or no email address"
            
            total_amount = sum(inv.amount for inv in unpaid_invoices)
            
            subject = "SAFA Registration - Payment Reminder"
            context = {
                'member': member,
                'invoices': unpaid_invoices,
                'total_amount': total_amount,
                'payment_url': f"{settings.SITE_URL}/payments/"
            }
            
            html_message = render_to_string('registration/emails/payment_reminder.html', context)
            plain_message = render_to_string('registration/emails/payment_reminder.txt', context)
            
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[member.email],
                fail_silently=False
            )
            
            logger.info(f"Payment reminder sent to {member.email}")
            return True, "Payment reminder sent successfully"
            
        except Exception as e:
            logger.error(f"Failed to send payment reminder to {member.email}: {str(e)}")
            return False, f"Failed to send reminder: {str(e)}"
    
    @staticmethod
    def confirm_payment(invoice, payment_method, payment_reference, amount=None):
        """Confirm payment for an invoice"""
        try:
            with transaction.atomic():
                invoice.status = 'PAID'
                invoice.payment_date = timezone.now()
                invoice.payment_method = payment_method
                invoice.payment_reference = payment_reference
                
                if amount and amount != invoice.amount:
                    invoice.paid_amount = amount
                else:
                    invoice.paid_amount = invoice.amount
                
                invoice.save()
                
                # Check if all invoices for the member are now paid
                member = invoice.player
                remaining_unpaid = Invoice.objects.filter(
                    player=member,
                    status__in=['PENDING', 'OVERDUE']
                ).exclude(id=invoice.id)
                
                if not remaining_unpaid.exists():
                    # All invoices paid - member can now be approved if documents are complete
                    PaymentManager._send_payment_confirmation(member, invoice)
                
                logger.info(f"Payment confirmed for invoice #{invoice.invoice_number}")
                return True, "Payment confirmed successfully"
                
        except Exception as e:
            logger.error(f"Failed to confirm payment for invoice #{invoice.invoice_number}: {str(e)}")
            return False, f"Payment confirmation failed: {str(e)}"
    
    @staticmethod
    def _send_payment_confirmation(member, invoice):
        """Send payment confirmation email"""
        try:
            if not member.email:
                return
            
            subject = "SAFA Registration - Payment Received"
            context = {
                'member': member,
                'invoice': invoice,
                'login_url': f"{settings.SITE_URL}/accounts/login/"
            }
            
            html_message = render_to_string('registration/emails/payment_confirmation.html', context)
            plain_message = render_to_string('registration/emails/payment_confirmation.txt', context)
            
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[member.email],
                fail_silently=True
            )
            
        except Exception as e:
            logger.error(f"Failed to send payment confirmation to {member.email}: {str(e)}")


class ValidationUtils:
    """Utility functions for validation"""
    
    @staticmethod
    def validate_sa_id_number(id_number):
        """
        Validate South African ID number
        Returns: dict with validation results and extracted info
        """
        try:
            return CustomUser.extract_id_info(id_number, 'ZAF')
        except Exception as e:
            return {
                'is_valid': False,
                'error': str(e),
                'date_of_birth': None,
                'gender': None
            }
    
    @staticmethod
    def check_duplicate_member(id_number=None, email=None, exclude_id=None):
        """
        Check for duplicate members by ID number or email
        Returns: (exists: bool, member: Member or None)
        """
        query = Member.objects.none()
        
        if id_number:
            query = Member.objects.filter(id_number=id_number)
        elif email:
            query = Member.objects.filter(email__iexact=email)
        
        if exclude_id:
            query = query.exclude(id=exclude_id)
        
        member = query.first()
        return member is not None, member


# Convenience functions for common operations
def register_new_member(form_data, admin_user=None):
    """Convenience function for member registration"""
    return MembershipManager.register_member(form_data, admin_user)

def approve_member_registration(member_id, approved_by):
    """Convenience function for member approval"""
    try:
        member = Member.objects.get(id=member_id)
        return ApprovalManager.approve_member(member, approved_by)
    except Member.DoesNotExist:
        return False, "Member not found"

def validate_id_number(id_number):
    """Convenience function for ID validation"""
    return ValidationUtils.validate_sa_id_number(id_number)