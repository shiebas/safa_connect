import datetime
from django.test import TestCase
from .utils import extract_sa_id_dob_gender

class SAIDValidatorTests(TestCase):

    def test_valid_id(self):
        """Test a known valid SA ID number."""
        # This ID is valid according to the standard Luhn algorithm
        id_number = "8001015009087"
        dob, gender = extract_sa_id_dob_gender(id_number)
        self.assertIsNotNone(dob, "DOB should not be None for a valid ID.")
        self.assertEqual(dob, datetime.date(1980, 1, 1))
        self.assertEqual(gender, "M")

        # Test case 2: A real-world valid ID for a female born in the 90s
        id_number_2 = "9202204700085"
        dob_2, gender_2 = extract_sa_id_dob_gender(id_number_2)
        self.assertIsNotNone(dob_2)
        self.assertEqual(dob_2, datetime.date(1992, 2, 20))
        self.assertEqual(gender_2, "F")

        # Test case 3: 21st century ID
        id_number_3 = "0102030111086"
        dob_3, gender_3 = extract_sa_id_dob_gender(id_number_3)
        self.assertIsNotNone(dob_3)
        self.assertEqual(dob_3, datetime.date(2001, 2, 3))
        self.assertEqual(gender_3, "F")

    def test_invalid_checksum(self):
        """Test an ID number with an invalid checksum."""
        id_number = "8001015009088" # Changed last digit to make it invalid
        dob, gender = extract_sa_id_dob_gender(id_number)
        self.assertIsNone(dob, "DOB should be None for an invalid checksum.")
        self.assertIsNone(gender, "Gender should be None for an invalid checksum.")

    def test_invalid_date(self):
        """Test an ID with an impossible date."""
        # 80th month is not valid
        id_number = "8080015009087"
        dob, gender = extract_sa_id_dob_gender(id_number)
        self.assertIsNone(dob, "DOB should be None for an invalid date.")

    def test_invalid_length(self):
        """Test IDs with incorrect length."""
        self.assertIsNone(extract_sa_id_dob_gender("12345")[0])
        self.assertIsNone(extract_sa_id_dob_gender("12345678901234")[0])

    def test_invalid_characters(self):
        """Test IDs with non-digit characters."""
        self.assertIsNone(extract_sa_id_dob_gender("800101500908a")[0])
