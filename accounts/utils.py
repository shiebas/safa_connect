import string
import random
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import date # Moved this import to the top

def generate_unique_member_email(first_name, last_name, email_type='member'):
    """
    Generate a unique member email in the format membertype.firstname.lastname@safaconnect.co.za
    
    Args:
        first_name (str): Member's first name
        last_name (str): Member's last name
        email_type (str): Type of email (player, official, member)
        
    Returns:
        str: Unique email address
    """
    from .models import CustomUser
    
    # Clean and normalize names
    first_name_clean = ''.join(e for e in first_name.strip().lower() if e.isalnum())
    last_name_clean = ''.join(e for e in last_name.strip().lower() if e.isalnum())
    
    # Create email base
    email_base = f"{email_type}.{first_name_clean}.{last_name_clean}"
    email_domain = "safaconnect.co.za"
    
    # Find a unique email
    counter = 1
    email = f"{email_base}@{email_domain}"
    
    # Check if email exists, if so add a number and increment until unique
    while CustomUser.objects.filter(email__iexact=email).exists():
        email = f"{email_base}{counter}@{email_domain}"
        counter += 1
    
    return email


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
    Includes Luhn algorithm check and comprehensive date validation.
    
    Args:
        id_number (str): 13-digit South African ID number
        
    Returns:
        tuple: (date_of_birth, gender) or (None, None) if invalid
        
    Rules:
    - ID format: YYMMDD G SSSS C A Z
    - YY: Year (00-99)
    - MM: Month (01-12)
    - DD: Day (01-31)
    - G: Gender (0-4 = Female, 5-9 = Male)
    - SSSS: Sequence number (0000-9999)
    - C: Citizenship (0 = SA Citizen, 1 = Permanent Resident)
    - A: Race (0-9, historical)
    - Z: Check digit (Luhn algorithm)
    """
    if not id_number or not isinstance(id_number, str):
        return None, None
    
    # Remove any spaces or hyphens
    id_number = id_number.replace(' ', '').replace('-', '')
    
    # Basic format validation
    if not id_number.isdigit() or len(id_number) != 13:
        return None, None

    # South African ID validation algorithm
    def validate_sa_id(id_num):
        """Validate check digit using South African ID algorithm"""
        if len(id_num) != 13:
            return False
            
        # Weights: 1,2,1,2,1,2,1,2,1,2,1,2
        weights = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2]
        total = 0
        
        for i in range(12):
            digit = int(id_num[i])
            weight = weights[i]
            result = digit * weight
            if result >= 10:
                result = (result // 10) + (result % 10)  # Sum the digits
            total += result
        
        check_digit = (10 - (total % 10)) % 10
        return check_digit == int(id_num[12])

    if not validate_sa_id(id_number):
        return None, None

    try:
        # Extract date components
        year_digits = int(id_number[:2])
        month = int(id_number[2:4])
        day = int(id_number[4:6])

        # Determine century (current year logic)
        current_year = timezone.now().year
        current_year_short = current_year % 100
        
        # If year digits are <= current year's last two digits, assume 2000s
        # Otherwise assume 1900s (for people born in 1900s)
        if year_digits <= current_year_short:
            full_year = 2000 + year_digits
        else:
            full_year = 1900 + year_digits

        # Validate date components
        if month < 1 or month > 12:
            return None, None
            
        if day < 1 or day > 31:
            return None, None

        # Create date object (will raise ValueError for invalid dates like Feb 30)
        dob = date(full_year, month, day)

        # Additional date validations
        today = timezone.now().date()
        
        # Date should not be in the future
        if dob > today:
            return None, None
        
        # Age should be reasonable (not older than 120 years)
        age_in_days = (today - dob).days
        if age_in_days < 0 or age_in_days > 43800:  # ~120 years
            return None, None

        # Extract gender (7th digit: 0-4 = Female, 5-9 = Male)
        gender_digit = int(id_number[6])
        if gender_digit < 0 or gender_digit > 9:
            return None, None
            
        gender = 'F' if gender_digit < 5 else 'M'

        return dob, gender

    except (ValueError, IndexError):
        # ValueError: Invalid date components (e.g., month 13, day 32)
        # IndexError: String slicing issues (shouldn't happen with len check)
        return None, None
    except Exception:
        # Catch any other unexpected errors
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
