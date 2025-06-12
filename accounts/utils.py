import datetime
from django.forms import ValidationError

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