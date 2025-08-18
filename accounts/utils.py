import string
import random
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def generate_unique_safa_id():
    """Generate a unique SAFA ID"""
    from .models import CustomUser
    
    chars = string.ascii_uppercase + string.digits
    
    while True:
        safa_id = ''.join(random.choices(chars, k=5))
        
        # Check if ID already exists
        if not CustomUser.objects.filter(safa_id=safa_id).exists():
            return safa_id


def create_member_invoice(user, amount=None, invoice_type='REGISTRATION'):
    """Create an invoice for a member"""
    from membership.models import Invoice
    
    if amount is None:
        # Default amounts based on role
        amount_mapping = {
            'PLAYER': 50.00,
            'OFFICIAL': 250.00,
            'COACH': 200.00,
            'CLUB_ADMIN': 500.00,
            'ADMIN_LOCAL_FED': 750.00,
            'ADMIN_REGION': 1000.00,
            'ADMIN_PROVINCE': 1500.00,
            'ASSOCIATION_ADMIN': 300.00,
        }
        amount = amount_mapping.get(user.role, 100.00)
    
    invoice = Invoice.objects.create(
        user=user,
        invoice_type=invoice_type,
        amount=amount,
        description=f'{user.get_role_display()} {invoice_type.title()} Fee',
        status='PENDING',
        due_date=timezone.now().date() + timezone.timedelta(days=30)
    )
    
    return invoice


def send_welcome_email(member):
    """Send welcome email to approved member"""
    if member.email:
        try:
            subject = "Welcome to SAFA - Your Membership Has Been Approved"
            message = f"""
            Dear {member.first_name},

            Congratulations! Your SAFA membership application has been approved.

            Your SAFA ID is: {member.safa_id}

            Next steps:
            1. Complete your profile information
            2. Register with a club or association
            3. Keep your membership information up to date

            Welcome to the South African Football Association!

            Best regards,
            SAFA Administration
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [member.email],
                fail_silently=True,
            )
        except Exception:
            pass  # Fail silently


def send_rejection_email(member, reason):
    """Send rejection email to member"""
    if member.email:
        try:
            subject = "SAFA Membership Application Update"
            message = f"""
            Dear {member.first_name},

            Thank you for your interest in SAFA membership.

            Unfortunately, your application could not be approved at this time.

            Reason: {reason}

            If you have any questions or would like to reapply, please contact us.

            Best regards,
            SAFA Administration
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [member.email],
                fail_silently=True,
            )
        except Exception:
            pass  # Fail silently

def send_approval_email(user):
    """Placeholder function for sending approval email."""
    pass

def send_support_request_email(support_request):
    """Placeholder function for sending support request email."""
    pass


def extract_sa_id_dob_gender(id_number):
    """Extract date of birth and gender from SA ID number"""
    if not id_number or len(id_number) != 13:
        return None, None
    
    try:
        # Extract date components
        year = int(id_number[:2])
        month = int(id_number[2:4])
        day = int(id_number[4:6])
        
        # Determine century
        current_year = timezone.now().year % 100
        century = 2000 if year <= current_year else 1900
        full_year = century + year
        
        # Create date
        from datetime import date
        date_of_birth = date(full_year, month, day)
        
        # Extract gender
        gender_digit = int(id_number[6:10])
        gender = 'M' if gender_digit >= 5000 else 'F'
        
        return date_of_birth, gender
    
    except (ValueError, IndexError):
        return None, None

def log_user_activity(user, action, details=""):
    """Log user activity for audit trail"""
    try:
        # You can implement this with a UserActivity model
        # or use Django's built-in logging
        logger.info(f"User Activity - User: {user.email if user else 'Anonymous'}, Action: {action}, Details: {details}")
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")
def get_dashboard_stats():
    """Get general dashboard statistics"""
    return {
        'total_users': CustomUser.objects.count(),
        'active_users': CustomUser.objects.filter(is_active=True).count(),
        'registrations_today': CustomUser.objects.filter(
            date_joined__date=timezone.now().date()
        ).count()
    }