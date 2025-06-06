import datetime
import datetime
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class UserRegistrationForm(UserCreationForm):
    """
    Form for user registration that uses email as the identifier
    instead of username
    """
    email = forms.EmailField(required=True, label="Email")
    name = forms.CharField(required=True, label="First Name")
    middle_name = forms.CharField(required=False, label="Middle Name")
    surname = forms.CharField(required=True, label="Surname")
    alias = forms.CharField(required=False, label="Alias")
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(choices=CustomUser._meta.get_field('gender').choices, required=False)
    role = forms.ChoiceField(choices=CustomUser._meta.get_field('role').choices, required=True)
    id_number = forms.CharField(required=False, label="ID Number")
    id_number_other = forms.CharField(required=False, label="Other ID Number")
    passport_number = forms.CharField(required=False, label="Passport Number")
    id_document_type = forms.ChoiceField(
        choices=CustomUser._meta.get_field('id_document_type').choices, required=False)
    phone_number = forms.CharField(required=False, label="Phone Number")
    address = forms.CharField(required=False, label="Address")
    city = forms.CharField(required=False, label="City")
    postal_code = forms.CharField(required=False, label="Postal Code")
    country = forms.CharField(required=False, label="Country")
    profile_photo = forms.ImageField(required=False, label="Profile Photo")
    document = forms.FileField(required=False, label="Upload Document")

    class Meta:
        model = CustomUser
        fields = (
            'email', 'name', 'middle_name', 'surname', 'alias', 'date_of_birth', 'gender', 'role',
            'id_number', 'id_number_other', 'passport_number', 'id_document_type',
            'phone_number', 'address', 'city', 'postal_code', 'country', 'profile_photo', 'document',
            'password1', 'password2'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']

    def clean(self):
        cleaned_data = super().clean()
        id_document_type = cleaned_data.get("id_document_type")
        id_number = cleaned_data.get("id_number")
        country = cleaned_data.get("country")

        if id_document_type == 'ID' and country == 'ZAF' and id_number:
            try:
                # Basic validation for 13-digit number
                if not id_number.isdigit() or len(id_number) != 13:
                    raise forms.ValidationError("Invalid ID number format.")

                # Extract and validate date of birth
                year = int(id_number[0:2])
                month = int(id_number[2:4])
                day = int(id_number[4:6])
                current_year = datetime.date.today().year % 100
                century = 1900 if year > current_year else 2000
                dob = datetime.date(century + year, month, day)
                cleaned_data['date_of_birth'] = dob

                # Extract gender
                gender_digit = int(id_number[6])
                cleaned_data['gender'] = 'F' if gender_digit < 5 else 'M'

            except (ValueError, TypeError):
                raise forms.ValidationError("Invalid date of birth in ID number.")
        
        return cleaned_data

    def clean(self):
        cleaned_data = super().clean()
        id_document_type = cleaned_data.get("id_document_type")
        id_number = cleaned_data.get("id_number")
        country = cleaned_data.get("country")

        if id_document_type == 'ID' and country == 'ZAF' and id_number:
            try:
                # Basic validation for 13-digit number
                if not id_number.isdigit() or len(id_number) != 13:
                    raise forms.ValidationError("Invalid ID number format.")

                # Extract and validate date of birth
                year = int(id_number[0:2])
                month = int(id_number[2:4])
                day = int(id_number[4:6])
                current_year = datetime.date.today().year % 100
                century = 1900 if year > current_year else 2000
                dob = datetime.date(century + year, month, day)
                cleaned_data['date_of_birth'] = dob

                # Extract gender
                gender_digit = int(id_number[6])
                cleaned_data['gender'] = 'F' if gender_digit < 5 else 'M'

            except (ValueError, TypeError):
                raise forms.ValidationError("Invalid date of birth in ID number.")
        
        return cleaned_data
