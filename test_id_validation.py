import datetime

def extract_id_info(id_number, country_code='ZAF'):
    """
    Extract and validate information from an ID number based on country.
    Supports South Africa (ZAF/RSA), Namibia (NAM), and Lesotho (LSO).
    Returns a dictionary with date_of_birth, gender, citizenship, and is_valid.
    """
    result = {
        'date_of_birth': None,
        'gender': None,
        'citizenship': None,
        'is_valid': False,
        'error': None
    }

    # Remove any spaces or hyphens
    id_number = id_number.replace(' ', '').replace('-', '')

    # Normalize country code - handle both ZAF and RSA for South Africa
    if country_code == 'RSA':
        country_code = 'ZAF'

    # Validate based on country
    if country_code == 'ZAF':
        # South African ID validation
        # Check if ID number is 13 digits
        if not id_number.isdigit() or len(id_number) != 13:
            result['error'] = "South African ID number must be 13 digits."
            return result

        # Extract date components
        year = id_number[0:2]
        month = id_number[2:4]
        day = id_number[4:6]

        # Validate date
        try:
            # Determine century (19xx or 20xx)
            current_year = datetime.datetime.now().year % 100
            century = '19' if int(year) > current_year else '20'
            full_year = int(century + year)

            # Check if date is valid
            result['date_of_birth'] = datetime.date(full_year, int(month), int(day))
            print(f"Date of birth: {result['date_of_birth']}")
        except ValueError as e:
            result['error'] = f"ID number contains an invalid date of birth: {e}"
            return result

        # Extract gender
        gender_digits = int(id_number[6:10])
        result['gender'] = 'M' if gender_digits >= 5000 else 'F'

        # Extract citizenship
        result['citizenship'] = int(id_number[10])
        if result['citizenship'] not in [0, 1]:
            result['error'] = "ID number citizenship digit (11) must be 0 or 1."
            return result

        # Validate checksum (Luhn algorithm for South African ID)
        # For South African IDs, the algorithm is:
        # 1. Add all digits in odd positions (1st, 3rd, 5th, etc.)
        # 2. Concatenate all digits in even positions (2nd, 4th, 6th, etc.)
        # 3. Multiply the result of step 2 by 2
        # 4. Add the digits of the result from step 3
        # 5. Add the result from step 4 to the result from step 1
        # 6. The check digit is (10 - (result % 10)) % 10

        odd_sum = 0
        even_digits = ""

        # Remember that positions are 0-indexed in code but 1-indexed in the algorithm description
        for i in range(len(id_number) - 1):  # Exclude the check digit
            digit = int(id_number[i])
            if i % 2 == 0:  # Even position in 0-indexed (odd in 1-indexed)
                odd_sum += digit
            else:  # Odd position in 0-indexed (even in 1-indexed)
                even_digits += str(digit)

        # Double the even digits as a single number and sum its digits
        doubled_even = int(even_digits) * 2 if even_digits else 0
        even_sum = sum(int(digit) for digit in str(doubled_even))

        # Calculate the total and check digit
        total = odd_sum + even_sum
        check_digit = (10 - (total % 10)) % 10

        print(f"Calculated check digit: {check_digit}, Actual check digit: {id_number[-1]}")

        if check_digit != int(id_number[-1]):
            result['error'] = f"ID number has an invalid checksum digit. Expected {check_digit}, got {id_number[-1]}."
            return result

    # If we got here, the ID number is valid
    result['is_valid'] = True
    return result

def validate_id_number_membership(id_number):
    """Validate South African ID number format and content using membership implementation"""
    if not id_number.isdigit() or len(id_number) != 13:
        return {"is_valid": False, "error": "ID number must be 13 digits."}

    try:
        # Extract and validate date of birth
        year = id_number[0:2]
        month = id_number[2:4]
        day = id_number[4:6]

        # Determine century (19xx or 20xx)
        current_year = datetime.datetime.now().year % 100
        century = '19' if int(year) > current_year else '20'
        full_year = int(century + year)

        # Validate date
        birth_date = datetime.date(full_year, int(month), int(day))
        print(f"Membership implementation - Date of birth: {birth_date}")

        # Extract and validate gender
        gender_digit = int(id_number[6:10])
        id_gender = 'M' if gender_digit >= 5000 else 'F'

        # Validate citizenship digit (should be 0 or 1)
        citizenship = int(id_number[10])
        if citizenship not in [0, 1]:
            return {"is_valid": False, "error": "ID number citizenship digit must be 0 or 1."}

        # Validate checksum using Luhn algorithm
        digits = [int(d) for d in id_number]
        checksum = 0
        for i in range(len(digits)):
            if i % 2 == 0:
                checksum += digits[i]
            else:
                doubled = digits[i] * 2
                checksum += doubled if doubled < 10 else (doubled - 9)

        print(f"Membership implementation - Checksum: {checksum}, Valid: {checksum % 10 == 0}")

        if checksum % 10 != 0:
            return {"is_valid": False, "error": "ID number checksum is invalid."}

        return {"is_valid": True, "date_of_birth": birth_date, "gender": id_gender, "citizenship": citizenship}
    except Exception as e:
        return {"is_valid": False, "error": f"Invalid ID number: {e}"}

# Test with the provided ID numbers
id_numbers = ['6805315146080', '6805315146081']

print("Testing with accounts implementation (extract_id_info):")
for id_number in id_numbers:
    print(f"\nTesting ID number: {id_number}")
    result = extract_id_info(id_number)
    print(f"Valid: {result['is_valid']}")
    if not result['is_valid']:
        print(f"Error: {result['error']}")
    else:
        print(f"Date of birth: {result['date_of_birth']}")
        print(f"Gender: {result['gender']}")
        print(f"Citizenship: {result['citizenship']}")

print("\n\nTesting with membership implementation:")
for id_number in id_numbers:
    print(f"\nTesting ID number: {id_number}")
    result = validate_id_number_membership(id_number)
    print(f"Valid: {result['is_valid']}")
    if not result['is_valid']:
        print(f"Error: {result['error']}")
    else:
        print(f"Date of birth: {result['date_of_birth']}")
        print(f"Gender: {result['gender']}")
        print(f"Citizenship: {result['citizenship']}")
