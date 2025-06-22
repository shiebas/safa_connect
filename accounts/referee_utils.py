"""
Utility functions for referee management
"""
from membership.models.main import Official

def generate_unique_referee_email(first_name, last_name, existing_id=None):
    """
    Generate a unique referee email in the format referee.firstname.lastname@safaglobaladmin.co.za
    
    Args:
        first_name (str): Referee's first name
        last_name (str): Referee's last name
        existing_id (int): Optional ID of existing referee to exclude from uniqueness check
        
    Returns:
        str: Unique email address
    """
    # Clean and normalize names
    first_name_clean = ''.join(e for e in first_name.strip().lower() if e.isalnum())
    last_name_clean = ''.join(e for e in last_name.strip().lower() if e.isalnum())
    
    # Create email base
    email_base = f"referee.{first_name_clean}.{last_name_clean}"
    email_domain = "safaglobaladmin.co.za"
    
    # Find a unique email
    counter = 1
    email = f"{email_base}@{email_domain}"
    
    # Check if email exists, if so add a number and increment until unique
    query = Official.objects.filter(email=email)
    if existing_id:
        query = query.exclude(id=existing_id)
    
    while query.exists():
        email = f"{email_base}{counter}@{email_domain}"
        counter += 1
        query = Official.objects.filter(email=email)
        if existing_id:
            query = query.exclude(id=existing_id)
    
    return email

def validate_south_african_mobile(mobile_number):
    """
    Validates South African mobile numbers in various formats
    Returns formatted number if valid, False otherwise
    
    Valid formats:
    - 0821234567
    - +27821234567
    - 27821234567
    """
    import re
    
    if not mobile_number:
        return True  # Empty is valid since we made it optional
    
    # Remove spaces, dashes, and parentheses
    mobile_number = re.sub(r'[\s\-\(\)]', '', mobile_number)
    
    # Check for various formats
    vodacom_pattern = r'^(?:\+?27|0)?(6[0-9]|7[1-9]|8[1-4])[0-9]{7}$'  # Vodacom: 060-069, 71-79, 81-84
    mtn_pattern = r'^(?:\+?27|0)?(6[0-9]|7[1-9]|8[1-9])[0-9]{7}$'  # MTN: 060-069, 71-79, 81-89
    telkom_pattern = r'^(?:\+?27|0)?(6[0-9]|8[1-9])[0-9]{7}$'  # Telkom Mobile: 060-069, 81-89
    cell_c_pattern = r'^(?:\+?27|0)?(6[0-9]|8[1-4])[0-9]{7}$'  # Cell C: 060-069, 81-84
    
    # Check if the number matches any of the patterns
    if (re.match(vodacom_pattern, mobile_number) or 
        re.match(mtn_pattern, mobile_number) or 
        re.match(telkom_pattern, mobile_number) or 
        re.match(cell_c_pattern, mobile_number)):
        
        # Format as +27 format
        if mobile_number.startswith('0'):
            return '+27' + mobile_number[1:]
        elif mobile_number.startswith('27'):
            return '+' + mobile_number
        elif mobile_number.startswith('+27'):
            return mobile_number
        else:
            return '+27' + mobile_number
    
    return False
