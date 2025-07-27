# registration/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
import re
from .models import Player, Official, PlayerClubRegistration
from membership.models import Member
from accounts.models import CustomUser, Position
from geography.models import Province, Region, LocalFootballAssociation, Club, Association
import sys
import os 
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from safa_constants import DocumentTypes, ValidationRules

class BaseRegistrationForm(forms.ModelForm):
    """Base form with common validation and fields"""
    
    # Document type selector (REQUIRED)
    id_document_type = forms.ChoiceField(
        choices=DocumentTypes.CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Document Type",
        help_text="Select your identification document type"
    )
    
    # Add common fields that all registration forms need
    popi_act_consent = forms.BooleanField(
        required=True,
        label="POPI Act Consent",
        help_text="I consent to the processing of my personal information in accordance with the Protection of Personal Information Act (POPIA)"
    )
    
    class Meta:
        abstract = True
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_form_fields()
        self.setup_cascading_fields()
    
    def setup_form_fields(self):
        """Setup common form field attributes and validation"""
        
        # Name fields - letters only (minimum 3 characters)
        name_attrs = {
            'pattern': r"[A-Za-z\s'-]{3,}",
            'title': 'Only letters, spaces, hyphens, and apostrophes allowed (minimum 3 characters)',
            'class': 'form-control',
            'minlength': '3',
            'oninput': "this.value = this.value.replace(/[^A-Za-z\\s'-]/g, '')"
        }
        
        if 'first_name' in self.fields:
            self.fields['first_name'].widget.attrs.update(name_attrs)
        if 'last_name' in self.fields:
            self.fields['last_name'].widget.attrs.update(name_attrs)
        
        # Email field
        if 'email' in self.fields:
            self.fields['email'].widget.attrs.update({
                'type': 'email',
                'class': 'form-control',
                'data-validation': 'email-check'
            })
            self.fields['email'].required = False  # Will be auto-generated if empty
        
        # Phone number
        if 'phone_number' in self.fields:
            self.fields['phone_number'].widget.attrs.update({
                'pattern': r'^[\+]?[0-9]{10,15}$',
                'title': 'Enter a valid phone number (10-15 digits, optional + prefix)',
                'class': 'form-control',
                'inputmode': 'tel'
            })
        
        # ID number validation - CONDITIONAL based on document type
        if 'id_number' in self.fields:
            self.fields['id_number'].widget.attrs.update({
                'pattern': r'[0-9]{13}',
                'title': 'South African ID number must be exactly 13 digits',
                'class': 'form-control',
                'maxlength': '13',
                'inputmode': 'numeric',
                'data-validation': 'id-check',
                'data-document-field': 'sa-id'
            })
            self.fields['id_number'].required = False  # Made conditional
        
        # Passport number - CONDITIONAL
        if 'passport_number' in self.fields:
            self.fields['passport_number'].widget.attrs.update({
                'class': 'form-control',
                'data-document-field': 'passport'
            })
            self.fields['passport_number'].required = False  # Made conditional
        
        # Date fields - CONDITIONAL for passport users
        if 'date_of_birth' in self.fields:
            self.fields['date_of_birth'].widget = forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'data-document-field': 'dob'
            })
            self.fields['date_of_birth'].required = False  # Will be required for passport
            self.fields['date_of_birth'].help_text = "Auto-filled from SA ID, or manually enter for passport"
        
        # Gender field - CONDITIONAL for passport users
        if 'gender' in self.fields:
            self.fields['gender'].widget.attrs.update({
                'class': 'form-control',
                'data-document-field': 'gender'
            })
            self.fields['gender'].required = False  # Will be required for passport
            self.fields['gender'].help_text = "Auto-filled from SA ID, or manually select for passport"
        
        # File fields
        file_fields = ['profile_picture', 'id_document', 'certification_document']
        for field_name in file_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                    'accept': 'image/*,.pdf' if 'document' in field_name else 'image/*'
                })
    
    def setup_cascading_fields(self):
        """Setup cascading geography fields"""
        geography_fields = ['province', 'region', 'lfa', 'club', 'association']
        
        for field_name in geography_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control geography-select',
                    'data-field': field_name
                })
                self.fields[field_name].required = False
    
    def clean_first_name(self):
        name = self.cleaned_data.get('first_name', '').strip()
        if len(name) < 3:
            raise ValidationError('First name must be at least 3 characters long.')
        if not name.replace(' ', '').replace('-', '').replace("'", '').isalpha():
            raise ValidationError('First name can only contain letters, spaces, hyphens, and apostrophes.')
        return name.title()
    
    def clean_last_name(self):
        name = self.cleaned_data.get('last_name', '').strip()
        if len(name) < 3:
            raise ValidationError('Last name must be at least 3 characters long.')
        if not name.replace(' ', '').replace('-', '').replace("'", '').isalpha():
            raise ValidationError('Last name can only contain letters, spaces, hyphens, and apostrophes.')
        return name.title()
    
    def clean_phone_number(self):
        """Validate phone number to only allow + and digits"""
        phone_number = self.cleaned_data.get('phone_number', '').strip()
        if phone_number:
            if not re.match(r'^[\+]?[0-9]{10,15}$', phone_number):
                raise ValidationError("Phone number must contain only digits and an optional + sign, with 10-15 digits total.")
        return phone_number

    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number', '').strip()
        document_type = self.cleaned_data.get('id_document_type')
        
        # Only validate if SA ID is selected
        if document_type == DocumentTypes.SA_ID:
            if not id_number:
                raise ValidationError('SA ID number is required when SA ID document type is selected.')
            
            # Check format
            if not id_number.isdigit() or len(id_number) != 13:
                raise ValidationError('ID number must be exactly 13 digits.')
            
            # Check if already exists (exclude current instance for updates)
            query = Member.objects.filter(id_number=id_number)
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                raise ValidationError('A member with this ID number already exists.')
            
            # Validate ID number and extract info
            try:
                id_info = CustomUser.extract_id_info(id_number)
                if not id_info['is_valid']:
                    raise ValidationError(id_info.get('error', 'Invalid ID number.'))
                
                # Auto-fill date of birth and gender from ID
                self.cleaned_data['date_of_birth'] = id_info['date_of_birth']
                self.cleaned_data['gender'] = id_info['gender']
                
            except Exception as e:
                raise ValidationError(f'ID validation failed: {str(e)}')
        
        return id_number
    
    def clean_passport_number(self):
        passport_number = self.cleaned_data.get('passport_number')
        document_type = self.cleaned_data.get('id_document_type')

        if passport_number:
            passport_number = passport_number.strip()
        else:
            passport_number = ''
        
        # Only validate if Passport is selected
        if document_type == DocumentTypes.PASSPORT:
            if not passport_number:
                raise ValidationError('Passport number is required when passport document type is selected.')
            
            # Check if already exists
            query = Member.objects.filter(passport_number=passport_number)
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                raise ValidationError('A member with this passport number already exists.')
        
        return passport_number
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            return email  # Will be auto-generated
        
        # Check if already exists
        query = Member.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        
        if query.exists():
            raise ValidationError('A member with this email already exists.')
        
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        document_type = cleaned_data.get('id_document_type')
        id_number = cleaned_data.get('id_number')
        passport_number = cleaned_data.get('passport_number')
        date_of_birth = cleaned_data.get('date_of_birth')
        gender = cleaned_data.get('gender')
        
        # Validate based on document type
        if document_type == DocumentTypes.SA_ID:
            # SA ID selected - clear passport fields
            cleaned_data['passport_number'] = ''
            
        elif document_type == DocumentTypes.PASSPORT:
            # Passport selected - clear SA ID and require DOB/gender
            cleaned_data['id_number'] = ''
            
            if not date_of_birth:
                self.add_error('date_of_birth', 'Date of birth is required when using passport.')
            
            if not gender:
                self.add_error('gender', 'Gender is required when using passport.')
        
        else:
            # No document type selected
            self.add_error('id_document_type', 'Please select a document type.')
        
        return cleaned_data


class UniversalRegistrationForm(BaseRegistrationForm):
    """Universal form for all registration types"""
    
    REGISTRATION_TYPES = [
        ('MEMBER', 'General Member'),
        ('PLAYER', 'Player'),
        ('OFFICIAL', 'Official'),
    ]
    
    registration_type = forms.ChoiceField(
        choices=REGISTRATION_TYPES,
        widget=forms.RadioSelect,
        initial='MEMBER',
        label="Registration Type"
    )
    
    # Optional position for officials
    position = forms.ModelChoiceField(
        queryset=Position.objects.filter(is_active=True),
        required=False,
        empty_label="Select Position",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Member
        fields = [
            'registration_type',
            'first_name', 'last_name', 'email', 'phone_number',
            'id_document_type', 'id_number', 'passport_number',  # Added document type
            'date_of_birth', 'gender',
            'street_address', 'suburb', 'city', 'state', 'postal_code', 'country',
            'province', 'region', 'lfa', 'club', 'association',
            'profile_picture', 'id_document',
            'emergency_contact', 'emergency_phone', 'medical_notes',
            'position',  # For officials
            'popi_act_consent'
        ]
        widgets = {
            'gender': forms.RadioSelect,
            'medical_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'street_address': forms.TextInput(attrs={'class': 'form-control'}),
            'suburb': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'value': 'South Africa'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Setup cascading querysets
        self.fields['province'].queryset = Province.objects.all()
        self.fields['region'].queryset = Region.objects.none()
        self.fields['lfa'].queryset = LocalFootballAssociation.objects.none()
        self.fields['club'].queryset = Club.objects.none()
        self.fields['association'].queryset = Association.objects.all()
        
        # Load data for edit forms
        if self.is_bound:
            try:
                province_id = self.data.get('province')
                if province_id:
                    self.fields['region'].queryset = Region.objects.filter(province_id=province_id)
                
                region_id = self.data.get('region')
                if region_id:
                    self.fields['lfa'].queryset = LocalFootballAssociation.objects.filter(region_id=region_id)
                
                lfa_id = self.data.get('lfa')
                if lfa_id:
                    self.fields['club'].queryset = Club.objects.filter(localfootballassociation_id=lfa_id)
            except (ValueError, TypeError):
                pass
    
    def clean(self):
        cleaned_data = super().clean()
        registration_type = cleaned_data.get('registration_type')
        position = cleaned_data.get('position')
        club = cleaned_data.get('club')
        
        # Validation based on registration type
        if registration_type == 'PLAYER':
            if not club:
                self.add_error('club', 'Club selection is required for player registration.')
        
        elif registration_type == 'OFFICIAL':
            if not position:
                self.add_error('position', 'Position is required for official registration.')
            # Club or association should be selected for officials
            if not club and not cleaned_data.get('association'):
                self.add_error('club', 'Either club or association must be selected for officials.')
                self.add_error('association', 'Either club or association must be selected for officials.')
        
        return cleaned_data


class PlayerRegistrationForm(BaseRegistrationForm):
    """Specific form for player registration"""
    
    POSITION_CHOICES = [
        ('GK', 'Goalkeeper'),
        ('DF', 'Defender'), 
        ('MF', 'Midfielder'),
        ('FW', 'Forward'),
    ]
    
    # Playing position
    playing_position = forms.ChoiceField(
        choices=POSITION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    jersey_number = forms.IntegerField(
        min_value=1,
        max_value=99,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '99'})
    )
    
    class Meta:
        model = Player
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'date_of_birth', 'gender', 'id_number', 'passport_number',
            'street_address', 'suburb', 'city', 'state', 'postal_code', 'country',
            'province', 'region', 'lfa', 'club',
            'profile_picture', 'id_document',
            'emergency_contact', 'emergency_phone', 'medical_notes',
            'playing_position', 'jersey_number',
            'popi_act_consent'
        ]
        widgets = {
            'gender': forms.RadioSelect,
            'medical_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'street_address': forms.TextInput(attrs={'class': 'form-control'}),
            'suburb': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'value': 'South Africa'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        club = cleaned_data.get('club')
        
        if not club:
            self.add_error('club', 'Club selection is required for player registration.')
        
        return cleaned_data


class OfficialRegistrationForm(BaseRegistrationForm):
    """Specific form for official registration"""
    
    # Required position field
    position = forms.ModelChoiceField(
        queryset=Position.objects.filter(is_active=True),
        required=True,
        empty_label="Select Position",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Certification fields
    certification_number = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    certification_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,image/*'})
    )
    
    certification_expiry_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    # Referee level (if applicable)
    referee_level = forms.ChoiceField(
        choices=[
            ('', 'Not a Referee'),
            ('LOCAL', 'Local'),
            ('REGIONAL', 'Regional'),
            ('PROVINCIAL', 'Provincial'),
            ('NATIONAL', 'National'),
            ('INTERNATIONAL', 'International'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Official
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'date_of_birth', 'gender', 'id_number', 'passport_number',
            'street_address', 'suburb', 'city', 'state', 'postal_code', 'country',
            'province', 'region', 'lfa', 'club', 'association',
            'profile_picture', 'id_document',
            'emergency_contact', 'emergency_phone', 'medical_notes',
            'position', 'certification_number', 'certification_document',
            'certification_expiry_date', 'referee_level',
            'popi_act_consent'
        ]
        widgets = {
            'gender': forms.RadioSelect,
            'medical_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'street_address': forms.TextInput(attrs={'class': 'form-control'}),
            'suburb': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'value': 'South Africa'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        position = cleaned_data.get('position')
        club = cleaned_data.get('club')
        association = cleaned_data.get('association')
        
        if not position:
            self.add_error('position', 'Position is required for official registration.')
        
        # Either club or association should be selected
        if not club and not association:
            error_msg = 'Either club or association must be selected for officials.'
            self.add_error('club', error_msg)
            self.add_error('association', error_msg)
        
        return cleaned_data


class QuickEditForm(forms.ModelForm):
    """Quick edit form for common member updates"""
    
    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'street_address', 'suburb', 'city', 'postal_code',
            'emergency_contact', 'emergency_phone'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'street_address': forms.TextInput(attrs={'class': 'form-control'}),
            'suburb': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class BulkApprovalForm(forms.Form):
    """Form for bulk operations on members"""
    
    ACTION_CHOICES = [
        ('approve', 'Approve Selected'),
        ('reject', 'Reject Selected'),
        ('send_reminder', 'Send Payment Reminder'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    member_ids = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Required for rejection action'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        rejection_reason = cleaned_data.get('rejection_reason')
        
        if action == 'reject' and not rejection_reason:
            self.add_error('rejection_reason', 'Rejection reason is required when rejecting members.')
        
        return cleaned_data


class PaymentConfirmationForm(forms.Form):
    """Form to confirm payment receipt"""
    
    invoice_id = forms.IntegerField(widget=forms.HiddenInput())
    
    payment_method = forms.ChoiceField(
        choices=[
            ('EFT', 'EFT/Bank Transfer'),
            ('CARD', 'Credit/Debit Card'),
            ('CASH', 'Cash'),
            ('OTHER', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    payment_reference = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Transaction reference number'
        })
    )
    
    payment_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    
    payment_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Additional notes about the payment'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default payment date to today
        from django.utils import timezone
        self.fields['payment_date'].initial = timezone.now().date()