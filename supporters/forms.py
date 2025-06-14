from django import forms
from .models import SupporterProfile

class SupporterRegistrationForm(forms.ModelForm):
    class Meta:
        model = SupporterProfile
        fields = [
            'favorite_club', 'membership_type', 'id_number', 'id_document',
            'date_of_birth', 'address'
        ]

    # Optionally, add custom validation or widgets here
