import datetime
from django.forms import ValidationError
import os
import re
import logging
from django.conf import settings
# Import utilities for invoice creation
from django.utils import timezone
from django.db import transaction
import random
import string

# Setup logging
logger = logging.getLogger(__name__)

# Optional imports - will be used if available, otherwise fallback to basic validation
# Setup flags for available libraries
PILLOW_AVAILABLE = False
TESSERACT_AVAILABLE = False
PYMUPDF_AVAILABLE = False

# Setup for checking module availability without importing
import importlib.util

# Check for PIL/Pillow
try:
    pillow_spec = importlib.util.find_spec("PIL")
    PILLOW_AVAILABLE = pillow_spec is not None
    if PILLOW_AVAILABLE:
        logger.info("PIL/Pillow is available for document processing")
    else:
        logger.warning("PIL/Pillow module not found")
except Exception as e:
    logger.warning(f"Error checking PIL/Pillow availability: {e}")
    PILLOW_AVAILABLE = False

# Check for pytesseract
try:
    tesseract_spec = importlib.util.find_spec("pytesseract")
    TESSERACT_AVAILABLE = tesseract_spec is not None
    if TESSERACT_AVAILABLE:
        logger.info("pytesseract module is available for OCR")
        
        # We still need to check if the actual Tesseract binary is available
        # But we'll do this at runtime when needed, not during import
    else:
        logger.warning("pytesseract module not found")
except Exception as e:
    logger.warning(f"Error checking pytesseract availability: {e}")
    TESSERACT_AVAILABLE = False

# Try to import PyMuPDF, but don't actually do the import at the module level
# Instead, just check if it's available and set the flag
try:
    # Just check if the module is available without actually importing it
    import importlib.util
    pymupdf_spec = importlib.util.find_spec("fitz")
    PYMUPDF_AVAILABLE = pymupdf_spec is not None
    if PYMUPDF_AVAILABLE:
        logger.info("PyMuPDF is available for PDF processing")
    else:
        logger.warning("PyMuPDF module not found")
except (ImportError, AttributeError, NameError) as e:
    logger.warning(f"Error checking PyMuPDF availability: {e}")
    PYMUPDF_AVAILABLE = False

def extract_sa_id_dob_gender(id_number):
    """
    Extracts date of birth and gender from a South African ID number.
    Args:
        id_number (str): 13-digit South African ID number.
    Returns:
        tuple: (date_of_birth (datetime.date or None), gender (str or None))
    """
    if not id_number or len(id_number) != 13 or not id_number.isdigit():
        return (None, None)
    
    try:
        year = int(id_number[:2])
        month = int(id_number[2:4])
        day = int(id_number[4:6])

        current_year = datetime.date.today().year % 100
        full_year = 1900 + year if year > current_year else 2000 + year

        # This will raise ValueError if the date is invalid
        dob = datetime.date(full_year, month, day)

        gender_digits = int(id_number[6:10])
        gender = "Male" if gender_digits >= 5000 else "Female"

        return (dob, gender)
    except (ValueError, TypeError):
        return (None, None)

def validate_passport_document(passport_document, passport_number, first_name, last_name, dob=None):
    """
    Validates a passport document by extracting and verifying contents.
    Checks if passport number, name, and DOB match the provided info.
    
    Args:
        passport_document: The uploaded passport document file
        passport_number (str): The passport number to verify against
        first_name (str): First name to verify
        last_name (str): Last name to verify
        dob (datetime.date, optional): Date of birth to verify
    
    Returns:
        tuple: (is_valid (bool), messages (list))
    """
    if not passport_document:
        return False, ["No passport document provided"]
    
    # Check if file extension is supported
    ext = os.path.splitext(passport_document.name)[1].lower()
    if ext not in ['.pdf', '.jpg', '.jpeg', '.png']:
        return False, ["Document must be a PDF or image file (jpg, jpeg, png)"]
    
    # If we don't have the OCR libraries available, fall back to basic validation
    if not (PILLOW_AVAILABLE and TESSERACT_AVAILABLE and PYMUPDF_AVAILABLE):
        logger.warning("OCR libraries not available. Falling back to basic document validation.")
        # Do basic file validation - at minimum check file size and type
        if passport_document.size > 10 * 1024 * 1024:  # Max 10MB
            return False, ["Document file is too large (max 10MB)"]
        
        # Basic check passed - in production you might want to flag this for manual review
        return True, ["Document accepted. OCR validation not available - document will require manual verification."]
    
    try:
        # Extract text from the document based on file type
        extracted_text = ""
        
        if ext == '.pdf' and PYMUPDF_AVAILABLE:
            try:
                # Dynamically import PyMuPDF when needed
                fitz = importlib.import_module("fitz")
                
                with fitz.open(stream=passport_document.read(), filetype="pdf") as doc:
                    for page in doc:
                        extracted_text += page.get_text()
                passport_document.seek(0)  # Reset file pointer after reading
            except Exception as e:
                logger.error(f"PyMuPDF error processing PDF: {e}")
                return True, ["Document accepted. PDF processing error - document will require manual verification."]
        elif PILLOW_AVAILABLE and TESSERACT_AVAILABLE:
            try:
                # Dynamically import PIL and pytesseract when needed
                PIL = importlib.import_module("PIL")
                Image = PIL.Image
                pytesseract = importlib.import_module("pytesseract")
                
                img = Image.open(passport_document)
                extracted_text = pytesseract.image_to_string(img)
            except Exception as e:
                logger.error(f"OCR error processing image: {e}")
                return True, ["Document accepted. Image processing error - document will require manual verification."]
        else:
            # If we got here, it means the imports were available but something went wrong
            return True, ["Document accepted. OCR processing unavailable - document will require manual verification."]
        
        # Normalize text for case-insensitive comparison
        extracted_text = extracted_text.lower()
        first_name_lower = first_name.lower()
        last_name_lower = last_name.lower()
        passport_number_clean = re.sub(r'\s+', '', passport_number).lower()
        
        # Initialize validation results
        validation_results = {
            'passport_number': False,
            'first_name': False,
            'last_name': False,
            'dob': True if dob is None else False  # Skip DOB check if not provided
        }
        
        # Check passport number
        if passport_number_clean in re.sub(r'\s+', '', extracted_text):
            validation_results['passport_number'] = True
        
        # Check names (more flexible check for names)
        if first_name_lower in extracted_text:
            validation_results['first_name'] = True
        
        if last_name_lower in extracted_text:
            validation_results['last_name'] = True
        
        # Check DOB if provided
        if dob:
            # Try different date formats
            date_formats = [
                dob.strftime('%d.%m.%Y'),
                dob.strftime('%d/%m/%Y'),
                dob.strftime('%d-%m-%Y'),
                dob.strftime('%d %b %Y'),
                dob.strftime('%d %B %Y')
            ]
            
            for date_format in date_formats:
                if date_format.lower() in extracted_text:
                    validation_results['dob'] = True
                    break
        
        # Prepare validation messages
        messages = []
        is_valid = True
        
        if not validation_results['passport_number']:
            messages.append(f"Passport number '{passport_number}' not found in document")
            is_valid = False
        
        if not validation_results['first_name']:
            messages.append(f"First name '{first_name}' not found in document")
            is_valid = False
        
        if not validation_results['last_name']:
            messages.append(f"Last name '{last_name}' not found in document")
            is_valid = False
        
        if dob and not validation_results['dob']:
            messages.append(f"Date of birth not found in document or doesn't match")
            is_valid = False
        
        if is_valid:
            messages.append("Document validation successful")
        
        return is_valid, messages
    
    except Exception as e:
        logger.error(f"Error validating passport document: {str(e)}")
        # In case of errors, allow the document but flag for manual verification
        return True, [f"Document accepted but requires manual verification. Automatic validation error: {str(e)}"]

def create_player_invoice(player, club, issued_by, is_junior=False):
    """
    Create an invoice for player registration
    
    Args:
        player (Player): The player to create an invoice for
        club (Club): The club the player is registering with
        issued_by (Member): The admin who issued the invoice
        is_junior (bool): If True, use junior registration fee (R100), otherwise senior fee (R200)
        
    Returns:
        Invoice: The created invoice
    """
    try:
        # Import at function level to avoid circular imports
        from membership.models.invoice import Invoice, InvoiceItem
        
        # Calculate player age to determine junior/senior status if not specified
        if is_junior is None:
            today = timezone.now().date()
            player_age = today.year - player.date_of_birth.year
            # Adjust age if birthday hasn't happened yet this year
            if (today.month, today.day) < (player.date_of_birth.month, player.date_of_birth.day):
                player_age -= 1
            is_junior = player_age < 18
        
        # Set fee amount based on age group
        fee_amount = 100.00 if is_junior else 200.00
        registration_type = "Junior Registration" if is_junior else "Senior Registration"
        
        # Generate a reference number using player membership number or ID
        reference = f"REG-{player.membership_number or player.id}-{timezone.now().strftime('%Y%m%d')}"

        with transaction.atomic():
            # Create invoice
            invoice = Invoice(
                invoice_type='REGISTRATION',
                amount=fee_amount,
                status='PENDING',
                issue_date=timezone.now().date(),
                player=player,
                club=club,
                issued_by=issued_by,
                reference=reference
            )
            invoice.save()
            
            # Create invoice item
            item = InvoiceItem(
                invoice=invoice,
                description=f"{registration_type} Fee",
                quantity=1,
                unit_price=fee_amount,
                sub_total=fee_amount
            )
            item.save()
            
            return invoice
    except Exception as e:
        logger.error(f"Error creating player invoice: {str(e)}")
        return None

def generate_unique_safa_id():
    """
    Generates a unique 5-character SAFA ID.
    Format: A combination of uppercase letters and numbers (e.g., A12B3)
    
    Returns:
        str: A unique 5-character SAFA ID
    """
    from django.utils.crypto import get_random_string
    from membership.models import Member
    
    # Generate a unique code
    while True:
        code = get_random_string(length=5, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        if not Member.objects.filter(safa_id=code).exists():
            return code

def create_official_invoice(official, club=None, association=None, issued_by=None, position_type=None):
    """
    Create an invoice for official registration
    
    Args:
        official (Official): The official to create an invoice for
        club (Club, optional): The club the official is registering with
        association (Association, optional): The association the official is registering with
        issued_by (Member): The admin who issued the invoice
        position_type (str): Type of position - determines fee amount
        
    Returns:
        Invoice: The created invoice
    """
    try:
        # Import at function level to avoid circular imports
        from membership.models.invoice import Invoice, InvoiceItem
        
        # Set fee amount based on position type
        # Default fee is R150, but can be adjusted based on position
        fee_amount = 150.00
        position_title = "Standard Position"
        
        if official.position:
            position_title = official.position.title
            # Check if referee or coach for higher fee
            if "referee" in position_title.lower():
                fee_amount = 250.00
            elif "coach" in position_title.lower():
                fee_amount = 200.00
        
        # Generate a reference number
        reference = f"REG-OFF-{official.membership_number or official.id}-{timezone.now().strftime('%Y%m%d')}"

        with transaction.atomic():
            # Create invoice
            invoice = Invoice(
                invoice_type='REGISTRATION',
                amount=fee_amount,
                status='PENDING',
                issue_date=timezone.now().date(),
                player=None,  # Not a player registration
                official=official,  # Link to official
                club=club,
                association=association,
                issued_by=issued_by,
                reference=reference
            )
            invoice.save()
            
            # Create invoice item
            item = InvoiceItem(
                invoice=invoice,
                description=f"{position_title} Registration Fee",
                quantity=1,
                unit_price=fee_amount,
                sub_total=fee_amount
            )
            item.save()
            
            return invoice
    except Exception as e:
        logger.error(f"Error creating official invoice: {str(e)}")
        return None