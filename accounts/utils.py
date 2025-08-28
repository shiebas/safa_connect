import string
import random
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import date # Moved this import to the top

def generate_unique_safa_id():
    """Generate a unique SAFA ID that is not in CustomUser or Member model"""
    from .models import CustomUser
    from membership.models import Member
    
    chars = string.ascii_uppercase + string.digits
    
    while True:
        safa_id = ''.join(random.choices(chars, k=5))
        
        # Check if ID already exists in either model
        if not CustomUser.objects.filter(safa_id=safa_id).exists() and \
           not Member.objects.filter(safa_id=safa_id).exists():
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
    """
    Extract date of birth and gender from SA ID number and validate it.
    Includes Luhn algorithm check and basic date validation.
    """
    if not id_number or not id_number.isdigit() or len(id_number) != 13:
        return None, None

    # Luhn algorithm check for SA ID
    def luhn_check(id_num):
        """
        Validate a South African ID number using the specified Luhn algorithm.
        """
        if len(id_num) != 13 or not id_num.isdigit():
            return False

        digits = [int(d) for d in id_num]
        odd_sum = sum(digits[i] for i in range(0, 12, 2))
        even_digits_str = "".join(str(digits[i]) for i in range(1, 12, 2))
        even_doubled = int(even_digits_str) * 2
        even_sum = sum(int(d) for d in str(even_doubled))
        total_sum = odd_sum + even_sum
        check_digit = (10 - (total_sum % 10)) % 10
        return check_digit == digits[12]

    if not luhn_check(id_number):
        return None, None

    try:
        year_digits = int(id_number[:2])
        month = int(id_number[2:4])
        day = int(id_number[4:6])

        current_year_full = timezone.now().year
        current_year_short = current_year_full % 100
        
        if year_digits <= current_year_short:
            full_year = 2000 + year_digits
        else:
            full_year = 1900 + year_digits

        # Attempt to create date object, will raise ValueError for invalid dates
        dob = date(full_year, month, day)

        # Basic date validation: ensure date is not in the future
        if dob > timezone.now().date():
            return None, None
        
        # Basic age check (e.g., not older than 120 years)
        # Using timedelta for age calculation
        age_in_days = (timezone.now().date() - dob).days
        if age_in_days < 0 or age_in_days / 365.25 > 120: # Also check for negative age (future date)
            return None, None

        gender_digit = int(id_number[6:10])
        gender = 'M' if gender_digit >= 5000 else 'F'

        return dob, gender

    except ValueError: # Catches invalid date components (e.g., month 13, day 32)
        return None, None
    except IndexError: # Catches if id_number slicing goes out of bounds (should be caught by initial len check, but good for robustness)
        return None, None
    except Exception as e: # Catch any other unexpected errors
        # Log the error for debugging purposes in a real application
        # print(f"Error logging user activity: {e}")
        return None, None

def log_user_activity(user, action, details=""):
    """Log user activity for audit trail"""
    try:
        # You can implement this with a UserActivity model
        # or use Django's built-in logging
        logger.info(f"User Activity - User: {user.email if user else 'Anonymous'}, Action: {action}, Details: {details}")
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")
def get_dashboard_stats(organization=None):
    """Get dashboard statistics, optionally filtered by organization."""
    from .models import CustomUser, Member

    if organization:
        # Stats for a specific organization
        # This is a placeholder - you'll need to define how to get members
        # related to a specific OrganizationType instance.
        # For now, we'll return some placeholder data.
        return {
            'org_total_members': 0, # Replace with actual query
            'org_active_members': 0, # Replace with actual query
            'org_name': organization.name,
        }

    # General, site-wide stats if no organization is provided
    return {
        'total_users': CustomUser.objects.count(),
        'active_users': CustomUser.objects.filter(is_active=True).count(),
        'registrations_today': CustomUser.objects.filter(
            date_joined__date=timezone.now().date()
        ).count()
    }
