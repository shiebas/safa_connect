# safa_constants.py
# Create this file in your project root or in a common app

"""
SAFA System Constants
All fees and configuration values that can change annually
"""

# MEMBERSHIP FEES (in ZAR) - Update annually
class MembershipFees:
    # Base membership fees
    NATIONAL_FEDERATION_MEMBERSHIP = 100.00
    
    # Player fees
    PLAYER_REGISTRATION = 200.00
    JUNIOR_PLAYER_REGISTRATION = 150.00  # Under 18
    SENIOR_PLAYER_REGISTRATION = 200.00   # 18 and above
    
    # Official fees  
    REFEREE_REGISTRATION = 250.00
    COACH_REGISTRATION = 200.00
    GENERAL_OFFICIAL_REGISTRATION = 150.00
    
    # Club fees (if applicable)
    CLUB_AFFILIATION = 500.00
    
    # Special fees
    TRANSFER_FEE = 100.00
    CARD_REPLACEMENT = 50.00
    
    # Payment terms
    PAYMENT_DUE_DAYS = 30

# INVOICE CONFIGURATION
class InvoiceConfig:
    # Invoice types
    MEMBERSHIP = 'MEMBERSHIP'
    PLAYER_REGISTRATION = 'PLAYER_REGISTRATION'
    OFFICIAL_REGISTRATION = 'OFFICIAL_REGISTRATION'
    TRANSFER = 'TRANSFER'
    REPLACEMENT = 'REPLACEMENT'
    
    # Payment methods
    PAYMENT_METHODS = [
        ('EFT', 'Electronic Funds Transfer'),
        ('CARD', 'Credit/Debit Card'),
        ('CASH', 'Cash Payment'),
        ('CHEQUE', 'Cheque'),
    ]
    
    # Invoice statuses
    PENDING = 'PENDING'
    PAID = 'PAID'
    OVERDUE = 'OVERDUE'
    CANCELLED = 'CANCELLED'

# ORGANIZATION DETAILS
class SAFADetails:
    ORGANIZATION_NAME = "South African Football Association"
    ABBREVIATION = "SAFA"
    
    # Banking details for payments
    BANK_NAME = "Standard Bank"
    ACCOUNT_NAME = "South African Football Association"
    ACCOUNT_NUMBER = "123456789"  # Replace with actual
    BRANCH_CODE = "051001"        # Replace with actual
    
    # Contact details
    HEAD_OFFICE_ADDRESS = "SAFA House, Nasrec, Johannesburg"
    PHONE = "+27 11 494 3522"
    EMAIL = "info@safa.net"
    WEBSITE = "www.safa.net"

# DOCUMENT TYPES
class DocumentTypes:
    SA_ID = 'ID'
    PASSPORT = 'PP'
    
    CHOICES = [
        (SA_ID, 'South African ID'),
        (PASSPORT, 'Passport'),
    ]

# MEMBER TYPES AND AGES
class MemberTypes:
    JUNIOR = 'JUNIOR'    # Under 18
    SENIOR = 'SENIOR'    # 18 and above
    OFFICIAL = 'OFFICIAL'
    
    # Age thresholds
    JUNIOR_AGE_LIMIT = 18

# POSITION TYPES (for fee calculation)
class PositionTypes:
    REFEREE_KEYWORDS = ['referee', 'ref', 'official referee']
    COACH_KEYWORDS = ['coach', 'trainer', 'coaching']
    
    @classmethod
    def get_official_fee(cls, position_title):
        """
        Determine fee based on position
        """
        if not position_title:
            return MembershipFees.GENERAL_OFFICIAL_REGISTRATION
        
        title_lower = position_title.lower()
        
        if any(keyword in title_lower for keyword in cls.REFEREE_KEYWORDS):
            return MembershipFees.REFEREE_REGISTRATION
        elif any(keyword in title_lower for keyword in cls.COACH_KEYWORDS):
            return MembershipFees.COACH_REGISTRATION
        else:
            return MembershipFees.GENERAL_OFFICIAL_REGISTRATION

# SYSTEM CONFIGURATION
class SystemConfig:
    # Auto-generated email domain
    DEFAULT_EMAIL_DOMAIN = 'safa.system'
    
    # SAFA ID generation
    SAFA_ID_LENGTH = 5
    SAFA_ID_PREFIX = ''  # Can add prefix if needed
    
    # File upload limits
    MAX_DOCUMENT_SIZE_MB = 5
    MAX_PHOTO_SIZE_MB = 2
    
    # Allowed file types
    ALLOWED_DOCUMENT_TYPES = ['.pdf', '.jpg', '.jpeg', '.png']
    ALLOWED_PHOTO_TYPES = ['.jpg', '.jpeg', '.png']

# VALIDATION RULES
class ValidationRules:
    # SA ID validation
    SA_ID_LENGTH = 13
    
    # Phone number validation
    PHONE_MIN_LENGTH = 10
    PHONE_MAX_LENGTH = 15
    
    # Name validation
    NAME_MIN_LENGTH = 2
    NAME_MAX_LENGTH = 50
    
    # Required fields by registration type
    PLAYER_REQUIRED_FIELDS = [
        'first_name', 'last_name', 'date_of_birth', 'gender', 
        'club'  # Players must have a club
    ]
    
    OFFICIAL_REQUIRED_FIELDS = [
        'first_name', 'last_name', 'date_of_birth', 'gender', 
        'position'  # Officials must have a position
    ]
    
    MEMBER_REQUIRED_FIELDS = [
        'first_name', 'last_name', 'date_of_birth', 'gender'
    ]

# BUSINESS RULES
class BusinessRules:
    # All registrations create National Federation membership first
    CREATE_NATIONAL_MEMBERSHIP = True
    
    # All invoices are from SAFA National
    INVOICE_ISSUER = "SAFA National Federation"
    
    # Document requirements
    DOCUMENT_REQUIRED_FOR_APPROVAL = True
    PHOTO_REQUIRED_FOR_APPROVAL = True
    
    # Payment requirements
    PAYMENT_REQUIRED_FOR_APPROVAL = True
    
    # Auto-approval rules (if applicable)
    AUTO_APPROVE_PAID_MEMBERS = False  # Set to True if you want automatic approval after payment

# CURRENT YEAR SETTINGS (update annually)
class CurrentSettings:
    REGISTRATION_YEAR = 2025
    FEE_STRUCTURE_VERSION = "2025.1"
    LAST_UPDATED = "2025-01-01"
    
    # Any special rules for current year
    SPECIAL_DISCOUNTS = {
        # 'EARLY_BIRD': 0.10,  # 10% discount for early registration
    }

# Helper functions
def get_age_category(date_of_birth):
    """
    Determine if member is junior or senior based on date of birth
    """
    from datetime import date
    if not date_of_birth:
        return MemberTypes.SENIOR  # Default to senior if no DOB
    
    today = date.today()
    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    
    return MemberTypes.JUNIOR if age < MemberTypes.JUNIOR_AGE_LIMIT else MemberTypes.SENIOR

def calculate_total_fees(registration_type, position=None, age_category=None):
    """
    Calculate total fees for a registration
    """
    total = MembershipFees.NATIONAL_FEDERATION_MEMBERSHIP
    
    if registration_type == 'PLAYER':
        if age_category == MemberTypes.JUNIOR:
            total += MembershipFees.JUNIOR_PLAYER_REGISTRATION
        else:
            total += MembershipFees.SENIOR_PLAYER_REGISTRATION
    elif registration_type == 'OFFICIAL':
        total += PositionTypes.get_official_fee(position.title if position else None)
    
    return total

def get_invoice_description(registration_type, club_name=None, position=None):
    """
    Generate invoice descriptions
    """
    descriptions = []
    
    # National membership (everyone gets this)
    descriptions.append(f"SAFA National Federation Membership - {CurrentSettings.REGISTRATION_YEAR}")
    
    # Additional fees
    if registration_type == 'PLAYER':
        if club_name:
            descriptions.append(f"Player Registration Fee - {club_name}")
        else:
            descriptions.append("Player Registration Fee")
    elif registration_type == 'OFFICIAL':
        if position:
            descriptions.append(f"{position.title} Registration Fee")
        else:
            descriptions.append("Official Registration Fee")
    
    return descriptions