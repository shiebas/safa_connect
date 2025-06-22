from django import forms
from .models import SupporterProfile

class SupporterRegistrationForm(forms.ModelForm):
    class Meta:
        model = SupporterProfile
        fields = [
            'favorite_club', 'membership_type', 'id_number', 'id_document',
            'date_of_birth', 'address', 'latitude', 'longitude', 
            'location_city', 'location_province', 'location_country',
            'location_accuracy'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
            'id_number': forms.TextInput(
                attrs={
                    'placeholder': 'Enter your South African ID number',
                    'class': 'form-control'
                }
            ),
            'address': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Enter your full address (or use location detection)',
                    'class': 'form-control'
                }
            ),
            'favorite_club': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),
            'membership_type': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),
            'id_document': forms.FileInput(
                attrs={
                    'class': 'form-control',
                    'accept': '.pdf,.jpg,.jpeg,.png'
                }
            ),
            # Hidden fields for geolocation data
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'location_city': forms.HiddenInput(),
            'location_province': forms.HiddenInput(),
            'location_country': forms.HiddenInput(),
            'location_accuracy': forms.HiddenInput(),
        }
        
        labels = {
            'favorite_club': 'Favorite Club',
            'membership_type': 'Membership Type',
            'id_number': 'ID Number',
            'id_document': 'ID Document',
            'date_of_birth': 'Date of Birth',
            'address': 'Address'
        }
        
        help_texts = {
            'favorite_club': 'Select the club you support (optional)',
            'membership_type': 'Choose your membership level',
            'id_number': 'Your South African ID number for verification',
            'id_document': 'Upload a clear photo or scan of your ID document',
            'date_of_birth': 'Your date of birth',
            'address': 'Your full residential address'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make favorite_club optional by adding empty choice
        if 'favorite_club' in self.fields:
            self.fields['favorite_club'].empty_label = "Select a club (optional)"
        
        # Set required fields
        required_fields = ['membership_type']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
