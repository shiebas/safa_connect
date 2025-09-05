from django import forms
from django.core.exceptions import ValidationError
from .models import TournamentRegistration, TournamentCompetition, TournamentPlayer
from .tournament_models import TournamentCompetition as NewTournamentCompetition
import re

class TournamentRegistrationForm(forms.ModelForm):
    """Form for tournament player registration with camera verification"""
    
    # Additional fields for walk-in registration
    
    terms_accepted = forms.BooleanField(
        label="I accept the tournament terms and conditions",
        required=True,
        help_text="You must accept the terms to register"
    )
    
    class Meta:
        model = TournamentRegistration
        fields = [
            'tournament', 'first_name', 'last_name', 'email', 'phone_number', 
            'id_number', 'live_photo'
        ]
        widgets = {
            'tournament': forms.HiddenInput(),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number'
            }),
            'id_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your ID number or passport'
            }),
            'live_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'capture': 'environment'
            })
        }
    
    def __init__(self, *args, **kwargs):
        tournament_id = kwargs.pop('tournament_id', None)
        super().__init__(*args, **kwargs)
        
        if tournament_id:
            try:
                tournament = NewTournamentCompetition.objects.get(id=tournament_id)
                self.fields['tournament'].initial = tournament
            except NewTournamentCompetition.DoesNotExist:
                pass
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
        return email
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove all non-digit characters
            phone = re.sub(r'\D', '', phone)
            if len(phone) < 10:
                raise ValidationError("Phone number must be at least 10 digits")
        return phone
    
    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number')
        if id_number:
            id_number = id_number.upper().strip()
            # Basic validation for South African ID numbers
            if len(id_number) == 13 and id_number.isdigit():
                # Basic SA ID validation
                pass
            elif len(id_number) >= 6:  # Passport or other ID
                pass
            else:
                raise ValidationError("Please enter a valid ID number or passport number")
        return id_number
    
    def clean(self):
        cleaned_data = super().clean()
        id_number = cleaned_data.get('id_number')
        
        # Check for duplicate registration
        tournament = cleaned_data.get('tournament')
        if tournament and id_number:
            existing = TournamentRegistration.objects.filter(
                tournament=tournament,
                id_number=id_number
            ).exists()
            if existing:
                raise ValidationError("A registration with this ID number already exists for this tournament")
        
        return cleaned_data

class TournamentPlayerForm(forms.ModelForm):
    """Form for creating tournament players (separate from SAFA system)"""
    
    class Meta:
        model = TournamentPlayer
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'date_of_birth',
            'gender', 'id_number', 'id_document_type', 'nationality',
            'emergency_contact_name', 'emergency_contact_phone', 'medical_conditions',
            'profile_photo'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'id_number': forms.TextInput(attrs={'class': 'form-control'}),
            'id_document_type': forms.Select(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'medical_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any medical conditions or allergies (optional)'
            }),
            'profile_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
        return email
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            phone = re.sub(r'\D', '', phone)
            if len(phone) < 10:
                raise ValidationError("Phone number must be at least 10 digits")
        return phone
    
    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number')
        if id_number:
            id_number = id_number.upper().strip()
        return id_number

class CameraVerificationForm(forms.Form):
    """Form for camera-based verification"""
    
    verification_photo = forms.ImageField(
        label="Verification Photo",
        help_text="Take a clear photo of your face for verification",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'capture': 'environment'
        })
    )
    
    verification_notes = forms.CharField(
        label="Verification Notes",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any additional notes for verification (optional)'
        })
    )
