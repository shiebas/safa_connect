# membership/forms.py - CORRECTED VERSION
# Fully aligned with the new SAFA Member model system

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import date
from decimal import Decimal
import re

# Import the corrected models
from .models import (
    Member, Transfer, SAFASeasonConfig, MemberDocument, 
    ClubMemberQuota, OrganizationSeasonRegistration
)
from geography.models import Club, LocalFootballAssociation, Province, Region, Association

# Try to import existing models if they exist (for backward compatibility)
try:
    from accounts.models import CustomUser
    CUSTOM_USER_AVAILABLE = True
except ImportError:
    CUSTOM_USER_AVAILABLE = False


class AddressFormMixin:
    """Mixin to add address field grouping to forms"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_address_fieldset()

    def add_address_fieldset(self):
        """Group address fields and add custom widgets"""
        address_fields = ['street_address', 'suburb', 'city', 'state', 'postal_code', 'country']
        for field in address_fields:
            if field in self.fields:
                self.fields[field].widget.attrs.update({
                    'class': 'address-field form-control',
                    'placeholder': self.fields[field].label
                })


class MemberRegistrationForm(AddressFormMixin, forms.ModelForm):
    """Main form for SAFA member registration (corrected)"""
    
    # Additional fields for enhanced registration
    confirm_email = forms.EmailField(
        label=_("Confirm Email Address"),
        help_text=_("Please confirm your email address")
    )
    
    # Club selection with geographic filtering
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        required=False,
        label=_("Province"),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_province'})
    )
    
    region = forms.ModelChoiceField(
        queryset=Region.objects.none(),
        required=False,
        label=_("Region"),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_region'})
    )
    
    lfa = forms.ModelChoiceField(
        queryset=LocalFootballAssociation.objects.none(),
        required=False,
        label=_("Local Football Association"),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_lfa'})
    )
    
    current_club = forms.ModelChoiceField(
        queryset=Club.objects.none(),
        required=True,  # MANDATORY club selection
        label=_("Select Club *"),
        help_text=_("Choose your club (required)"),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_current_club'})
    )
    
    # CORRECTED: Multiple associations for officials only
    associations = forms.ModelMultipleChoiceField(
        queryset=Association.objects.all(),
        required=False,
        label=_("Associations (Officials Only)"),
        help_text=_("Select associations if you are an official"),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'association-checkbox'})
    )
    
    # Document uploads
    id_document_upload = forms.FileField(
        required=False,
        label=_("ID Document"),
        help_text=_("Upload a clear copy of your ID document"),
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'})
    )
    
    profile_photo = forms.ImageField(
        required=False,
        label=_("Profile Photo"),
        help_text=_("Upload a recent passport-style photo"),
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.jpg,.jpeg,.png'})
    )
    
    # Terms and conditions
    terms_and_conditions = forms.BooleanField(
        required=True,
        label=_("I accept the SAFA Terms and Conditions"),
        help_text=_("You must accept the terms to proceed")
    )
    
    privacy_policy = forms.BooleanField(
        required=True,
        label=_("I accept the Privacy Policy"),
        help_text=_("You must accept the privacy policy to proceed")
    )
    
    marketing_emails = forms.BooleanField(
        required=False,
        label=_("I want to receive marketing emails"),
        help_text=_("Optional: Receive news and updates from SAFA")
    )

    class Meta:
        model = Member
        fields = [
            # Personal Information
            'first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'gender',
            # Identification
            'id_number', 'passport_number', 'nationality',
            # SAFA Details
            'role', 'is_existing_member', 'previous_safa_id',
            # Address Information
            'street_address', 'suburb', 'city', 'state', 'postal_code', 'country',
            # Emergency Contact
            'emergency_contact', 'emergency_phone', 'medical_notes',
            # Registration address for auto-detection
            'registration_address',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+27123456789'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'id_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '13-digit ID number',
                'maxlength': '13',
                'pattern': '[0-9]{13}'
            }),
            'passport_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Passport number'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'value': 'South African'}),
            'role': forms.Select(attrs={'class': 'form-control', 'id': 'id_role'}),
            'medical_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Address for geographic detection'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Set up role choices
        self.fields['role'].choices = Member.MEMBER_ROLES
        
        # Set up previous SAFA ID field
        self.fields['previous_safa_id'].widget = forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter previous SAFA ID if you have one'
        })
        
        # Add JavaScript hooks for dynamic behavior
        self.fields['is_existing_member'].widget.attrs.update({
            'class': 'form-check-input',
            'onchange': 'togglePreviousSafaId(this)'
        })
        
        # Set field requirements
        self.fields['phone_number'].required = False
        self.fields['emergency_contact'].required = False
        self.fields['emergency_phone'].required = False
        self.fields['medical_notes'].required = False
        self.fields['registration_address'].required = False
        
        # Set up cascading geographic dropdowns
        if 'province' in self.data:
            try:
                province_id = int(self.data.get('province'))
                self.fields['region'].queryset = Region.objects.filter(
                    province_id=province_id, is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        
        if 'region' in self.data:
            try:
                region_id = int(self.data.get('region'))
                self.fields['lfa'].queryset = LocalFootballAssociation.objects.filter(
                    region_id=region_id, is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        
        # Set club queryset based on geographic selection
        if 'lfa' in self.data:
            try:
                lfa_id = int(self.data.get('lfa'))
                self.fields['current_club'].queryset = Club.objects.filter(
                    lfa_id=lfa_id, is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif 'region' in self.data:
            try:
                region_id = int(self.data.get('region'))
                self.fields['current_club'].queryset = Club.objects.filter(
                    region_id=region_id, is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif 'province' in self.data:
            try:
                province_id = int(self.data.get('province'))
                self.fields['current_club'].queryset = Club.objects.filter(
                    province_id=province_id, is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        else:
            # Default to all active clubs
            self.fields['current_club'].queryset = Club.objects.filter(is_active=True).order_by('name')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        confirm_email = self.data.get('confirm_email')
        
        if email and confirm_email and email != confirm_email:
            raise ValidationError(_("Email addresses do not match"))
        
        # Check for existing member with same email
        if Member.objects.filter(email=email).exists():
            raise ValidationError(_("A member with this email address already exists"))
        
        return email

    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number', '').strip()
        
        if id_number:
            # Validate format
            if not re.match(r'^\d{13}$', id_number):
                raise ValidationError(_("ID number must be exactly 13 digits"))
            
            # Check for existing member
            if Member.objects.filter(id_number=id_number).exists():
                raise ValidationError(_("A member with this ID number already exists"))
            
            # Validate SA ID number format and extract info
            try:
                year = int(id_number[:2])
                month = int(id_number[2:4])
                day = int(id_number[4:6])
                
                # Determine century
                if year < 25:
                    year += 2000
                else:
                    year += 1900
                
                # Validate date
                id_birth_date = date(year, month, day)
                
                # Set birth date if not provided
                if not self.cleaned_data.get('date_of_birth'):
                    self.cleaned_data['date_of_birth'] = id_birth_date
                
                # Extract gender
                gender_digit = int(id_number[6])
                id_gender = 'M' if gender_digit >= 5 else 'F'
                
                if not self.cleaned_data.get('gender'):
                    self.cleaned_data['gender'] = id_gender
                    
            except (ValueError, IndexError):
                raise ValidationError(_("Invalid South African ID number"))
        
        return id_number

    def clean_previous_safa_id(self):
        previous_safa_id = self.cleaned_data.get('previous_safa_id', '').strip()
        is_existing = self.cleaned_data.get('is_existing_member', False)
        
        if is_existing and not previous_safa_id:
            raise ValidationError(_("Previous SAFA ID is required for existing members"))
        
        if previous_safa_id and len(previous_safa_id) != 5:
            raise ValidationError(_("SAFA ID must be exactly 5 characters"))
        
        return previous_safa_id

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        
        if dob:
            # Check if date is not in the future
            if dob > timezone.now().date():
                raise ValidationError(_("Date of birth cannot be in the future"))
            
            # Check reasonable age limits
            age = (timezone.now().date() - dob).days // 365
            if age > 100:
                raise ValidationError(_("Please check the date of birth - age seems too high"))
            if age < 5:
                raise ValidationError(_("Member must be at least 5 years old"))
        
        return dob

    def clean_current_club(self):
        """Validate club selection and check quotas"""
        current_club = self.cleaned_data.get('current_club')
        
        if not current_club:
            raise ValidationError(_("Club selection is mandatory"))
        
        # Check club quotas
        current_season = SAFASeasonConfig.get_active_season()
        if current_season:
            try:
                quota = ClubMemberQuota.objects.get(
                    club=current_club,
                    season_config=current_season
                )
                
                role = self.cleaned_data.get('role')
                dob = self.cleaned_data.get('date_of_birth')
                
                if role == 'PLAYER' and dob:
                    age = (timezone.now().date() - dob).days // 365
                    if age < 18:  # Junior
                        if not quota.can_register_member('junior_player'):
                            raise ValidationError(_(
                                f"Club has reached its junior player quota ({quota.current_junior_players}/{quota.max_junior_players})"
                            ))
                    else:  # Senior
                        if not quota.can_register_member('senior_player'):
                            raise ValidationError(_(
                                f"Club has reached its senior player quota ({quota.current_senior_players}/{quota.max_senior_players})"
                            ))
                elif role == 'OFFICIAL':
                    if not quota.can_register_member('official'):
                        raise ValidationError(_(
                            f"Club has reached its officials quota ({quota.current_officials}/{quota.max_officials})"
                        ))
                        
            except ClubMemberQuota.DoesNotExist:
                # Create default quota if it doesn't exist
                ClubMemberQuota.objects.create(
                    club=current_club,
                    season_config=current_season
                )
        
        return current_club

    def clean(self):
        cleaned_data = super().clean()
        id_number = cleaned_data.get('id_number')
        passport_number = cleaned_data.get('passport_number')
        role = cleaned_data.get('role')
        associations = cleaned_data.get('associations', [])
        
        # Either ID number or passport required
        if not id_number and not passport_number:
            raise ValidationError(_("Either ID number or passport number is required"))
        
        # Validate club selection
        current_club = cleaned_data.get('current_club')
        if not current_club:
            raise ValidationError(_("Club selection is required"))
        
        # CORRECTED: Associations are only for officials
        if role == 'OFFICIAL' and not associations:
            self.add_error('associations', _("Officials must select at least one association"))
        elif role != 'OFFICIAL' and associations:
            self.add_error('associations', _("Only officials can select associations"))
        
        # Set terms acceptance
        cleaned_data['terms_accepted'] = cleaned_data.get('terms_and_conditions', False)
        cleaned_data['privacy_accepted'] = cleaned_data.get('privacy_policy', False)
        cleaned_data['marketing_consent'] = cleaned_data.get('marketing_emails', False)
        
        # Set geographic fields from form data
        if 'province' in self.data:
            try:
                cleaned_data['province'] = Province.objects.get(pk=int(self.data['province']))
            except (Province.DoesNotExist, ValueError):
                pass
        
        if 'region' in self.data:
            try:
                cleaned_data['region'] = Region.objects.get(pk=int(self.data['region']))
            except (Region.DoesNotExist, ValueError):
                pass
        
        if 'lfa' in self.data:
            try:
                cleaned_data['lfa'] = LocalFootballAssociation.objects.get(pk=int(self.data['lfa']))
            except (LocalFootballAssociation.DoesNotExist, ValueError):
                pass
        
        return cleaned_data

    def save(self, commit=True):
        member = super().save(commit=False)
        
        # Set additional fields
        member.registration_method = 'SELF'
        member.current_season = SAFASeasonConfig.get_active_season()
        
        # Set geographic fields
        if 'province' in self.cleaned_data:
            member.province = self.cleaned_data['province']
        if 'region' in self.cleaned_data:
            member.region = self.cleaned_data['region']
        if 'lfa' in self.cleaned_data:
            member.lfa = self.cleaned_data['lfa']
        
        if commit:
            member.save()
            
            # Handle associations for officials
            if member.role == 'OFFICIAL' and 'associations' in self.cleaned_data:
                member.associations.set(self.cleaned_data['associations'])
            
            # Handle file uploads
            if self.cleaned_data.get('id_document_upload'):
                member.id_document = self.cleaned_data['id_document_upload']
            
            if self.cleaned_data.get('profile_photo'):
                member.profile_picture = self.cleaned_data['profile_photo']
            
            member.save()
        
        return member


class MemberForm(forms.ModelForm):
    """Simplified form for staff member creation/editing"""
    
    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'gender',
            'id_number', 'passport_number', 'nationality', 'role', 'status',
            'current_club', 'province', 'region', 'lfa',
            'street_address', 'suburb', 'city', 'state', 'postal_code', 'country',
            'emergency_contact', 'emergency_phone', 'medical_notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'id_number': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '13'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'current_club': forms.Select(attrs={'class': 'form-control'}),
            'province': forms.Select(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-control'}),
            'lfa': forms.Select(attrs={'class': 'form-control'}),
            'medical_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up querysets
        self.fields['current_club'].queryset = Club.objects.filter(is_active=True).order_by('name')
        self.fields['province'].queryset = Province.objects.all().order_by('name')
        self.fields['region'].queryset = Region.objects.filter(is_active=True).order_by('name')
        self.fields['lfa'].queryset = LocalFootballAssociation.objects.filter(is_active=True).order_by('name')


class MemberUpdateForm(AddressFormMixin, forms.ModelForm):
    """Form for updating existing member information"""
    
    # CORRECTED: Handle associations for officials
    associations = forms.ModelMultipleChoiceField(
        queryset=Association.objects.all(),
        required=False,
        label=_("Associations (Officials Only)"),
        widget=forms.CheckboxSelectMultiple()
    )
    
    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 
            'street_address', 'suburb', 'city', 'state', 'postal_code', 'country',
            'emergency_contact', 'emergency_phone', 'medical_notes', 'profile_picture'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'medical_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make SAFA ID and other critical fields read-only
        if self.instance and self.instance.pk:
            self.fields['email'].widget.attrs['readonly'] = True
            self.fields['email'].help_text = _("Contact support to change your email address")
            
            # Pre-populate associations for officials
            if self.instance.role == 'OFFICIAL':
                self.fields['associations'].initial = self.instance.associations.all()
            else:
                # Hide associations field for non-officials
                self.fields['associations'].widget = forms.HiddenInput()

    def save(self, commit=True):
        member = super().save(commit=commit)
        
        if commit and member.role == 'OFFICIAL':
            # Update associations for officials
            associations = self.cleaned_data.get('associations', [])
            member.associations.set(associations)
        
        return member


class TransferRequestForm(forms.ModelForm):
    """Form for requesting a transfer between clubs"""
    
    class Meta:
        model = Transfer
        fields = ['to_club', 'reason']
        widgets = {
            'to_club': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.member = kwargs.pop('member', None)
        super().__init__(*args, **kwargs)
        
        if self.member:
            # Exclude current club from choices
            self.fields['to_club'].queryset = Club.objects.filter(
                is_active=True
            ).exclude(pk=self.member.current_club.pk).order_by('name')
            
            # Set from_club automatically
            self.from_club = self.member.current_club

    def clean_to_club(self):
        to_club = self.cleaned_data.get('to_club')
        
        if self.member and to_club == self.member.current_club:
            raise ValidationError(_("Cannot transfer to the same club"))
        
        return to_club

    def clean(self):
        cleaned_data = super().clean()
        
        if self.member:
            # Check for existing pending transfers
            existing_transfer = Transfer.objects.filter(
                member=self.member,
                status='PENDING'
            ).first()
            
            if existing_transfer:
                raise ValidationError(_("You already have a pending transfer request"))
        
        return cleaned_data

    def save(self, commit=True):
        transfer = super().save(commit=False)
        
        if self.member:
            transfer.member = self.member
            transfer.from_club = self.member.current_club
        
        if commit:
            transfer.save()
        
        return transfer


class MemberDocumentForm(forms.ModelForm):
    """Form for uploading member documents"""
    
    class Meta:
        model = MemberDocument
        fields = ['document_type', 'document_file', 'is_required', 'expiry_date']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'document_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean_document_file(self):
        document_file = self.cleaned_data.get('document_file')
        
        if document_file:
            # Check file size (5MB limit)
            if document_file.size > 5 * 1024 * 1024:
                raise ValidationError(_("File size must be less than 5MB"))
            
            # Check file type
            allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
            if document_file.content_type not in allowed_types:
                raise ValidationError(_("Only PDF, JPG, and PNG files are allowed"))
        
        return document_file


class ClubForm(forms.ModelForm):
    """Form for creating/editing clubs"""
    
    class Meta:
        model = Club
        fields = ['name', 'province', 'region']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_name': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.Select(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-control'}),
            'lfa': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up querysets
        self.fields['province'].queryset = Province.objects.all().order_by('name')
        self.fields['region'].queryset = Region.objects.filter(is_active=True).order_by('name')
        self.fields['lfa'].queryset = LocalFootballAssociation.objects.filter(is_active=True).order_by('name')


class MemberSearchForm(forms.Form):
    """Form for searching members"""
    
    search_query = forms.CharField(
        max_length=100,
        required=False,
        label=_("Search"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, SAFA ID, or email...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Member.MEMBERSHIP_STATUS,
        required=False,
        label=_("Status"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    role = forms.ChoiceField(
        choices=[('', 'All Roles')] + Member.MEMBER_ROLES,
        required=False,
        label=_("Role"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    club = forms.ModelChoiceField(
        queryset=Club.objects.filter(status='ACTIVE'),
        required=False,
        label=_("Club"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    season = forms.ModelChoiceField(
        queryset=SAFASeasonConfig.objects.all().order_by('-season_year'),
        required=False,
        label=_("Season"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default season to active season
        active_season = SAFASeasonConfig.get_active_season()
        if active_season:
            self.fields['season'].initial = active_season


class PaymentPlanForm(forms.Form):
    """Form for setting up payment plans"""
    
    INSTALLMENT_CHOICES = [
        (2, _('2 installments')),
        (3, _('3 installments')),
        (4, _('4 installments')),
        (6, _('6 installments (monthly)')),
    ]
    
    number_of_installments = forms.ChoiceField(
        choices=INSTALLMENT_CHOICES,
        label=_("Number of Installments"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    payment_method = forms.ChoiceField(
        choices=[
            ('EFT', _('Electronic Funds Transfer')),
            ('DEBIT_ORDER', _('Debit Order')),
            ('CREDIT_CARD', _('Credit Card')),
        ],
        label=_("Payment Method"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    agree_to_terms = forms.BooleanField(
        required=True,
        label=_("I agree to the payment plan terms and conditions")
    )

    def clean_number_of_installments(self):
        installments = int(self.cleaned_data.get('number_of_installments'))
        
        if installments < 2 or installments > 12:
            raise ValidationError(_("Number of installments must be between 2 and 12"))
        
        return installments


class SeasonConfigForm(forms.ModelForm):
    """Form for creating/editing season configurations"""
    
    class Meta:
        model = SAFASeasonConfig
        fields = [
            'season_year', 'season_start_date', 'season_end_date',
            'organization_registration_start', 'organization_registration_end',
            'member_registration_start', 'member_registration_end',
            'vat_rate', 'payment_due_days', 'is_renewal_season'
        ]
        widgets = {
            'season_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'season_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'season_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'organization_registration_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'organization_registration_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'member_registration_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'member_registration_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vat_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'payment_due_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_renewal_season': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        season_start = cleaned_data.get('season_start_date')
        season_end = cleaned_data.get('season_end_date')
        org_start = cleaned_data.get('organization_registration_start')
        org_end = cleaned_data.get('organization_registration_end')
        member_start = cleaned_data.get('member_registration_start')
        member_end = cleaned_data.get('member_registration_end')
        
        # Validate date ranges
        if season_start and season_end and season_start >= season_end:
            raise ValidationError(_("Season end date must be after start date"))
        
        if org_start and org_end and org_start >= org_end:
            raise ValidationError(_("Organization registration end must be after start"))
        
        if member_start and member_end and member_start >= member_end:
            raise ValidationError(_("Member registration end must be after start"))
        
        # Organization registration should come before member registration
        if org_end and member_start and org_end > member_start:
            raise ValidationError(_("Organization registration should end before member registration starts"))
        
        return cleaned_data


class BulkActionForm(forms.Form):
    """Form for bulk actions on members"""
    
    ACTION_CHOICES = [
        ('approve', _('Approve Selected Members')),
        ('reject', _('Reject Selected Members')),
        ('activate', _('Activate Selected Members')),
        ('deactivate', _('Deactivate Selected Members')),
        ('generate_invoices', _('Generate Invoices')),
        ('send_reminders', _('Send Payment Reminders')),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        label=_("Action"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    member_ids = forms.CharField(
        widget=forms.HiddenInput(),
        label=_("Selected Members")
    )
    
    reason = forms.CharField(
        max_length=500,
        required=False,
        label=_("Reason (for rejections)"),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    send_notification = forms.BooleanField(
        initial=True,
        required=False,
        label=_("Send email notifications")
    )

    def clean_member_ids(self):
        member_ids_str = self.cleaned_data.get('member_ids', '')
        
        try:
            member_ids = [int(id.strip()) for id in member_ids_str.split(',') if id.strip()]
        except ValueError:
            raise ValidationError(_("Invalid member IDs"))
        
        if not member_ids:
            raise ValidationError(_("No members selected"))
        
        # Validate that all member IDs exist
        existing_count = Member.objects.filter(id__in=member_ids).count()
        if existing_count != len(member_ids):
            raise ValidationError(_("Some selected members do not exist"))
        
        return member_ids

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        reason = cleaned_data.get('reason')
        
        # Reason is required for rejection
        if action == 'reject' and not reason:
            raise ValidationError(_("Reason is required for rejecting members"))
        
        return cleaned_data


class InvoiceFilterForm(forms.Form):
    """Form for filtering invoices"""
    
    STATUS_CHOICES = [('', 'All Statuses')] + [
        ('PENDING', _('Pending')),
        ('PAID', _('Paid')),
        ('OVERDUE', _('Overdue')),
        ('CANCELLED', _('Cancelled')),
        ('PARTIALLY_PAID', _('Partially Paid')),
    ]
    
    TYPE_CHOICES = [('', 'All Types')] + [
        ('ORGANIZATION_MEMBERSHIP', _('Organization Membership')),
        ('MEMBER_REGISTRATION', _('Member Registration')),
        ('ANNUAL_FEE', _('Annual Fee')),
        ('RENEWAL', _('Season Renewal')),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    invoice_type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    season = forms.ModelChoiceField(
        queryset=SAFASeasonConfig.objects.all().order_by('-season_year'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    amount_min = forms.DecimalField(
        required=False,
        min_value=Decimal('0'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    amount_max = forms.DecimalField(
        required=False,
        min_value=Decimal('0'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        amount_min = cleaned_data.get('amount_min')
        amount_max = cleaned_data.get('amount_max')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError(_("Date from must be before date to"))
        
        if amount_min and amount_max and amount_min > amount_max:
            raise ValidationError(_("Minimum amount must be less than maximum amount"))
        
        return cleaned_data


class DocumentApprovalForm(forms.Form):
    """Form for approving/rejecting documents"""
    
    ACTION_CHOICES = [
        ('approve', _('Approve')),
        ('reject', _('Reject')),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect()
    )
    
    notes = forms.CharField(
        max_length=500,
        required=False,
        label=_("Notes"),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        notes = cleaned_data.get('notes')
        
        # Notes are required for rejection
        if action == 'reject' and not notes:
            raise ValidationError(_("Notes are required when rejecting a document"))
        
        return cleaned_data


class MemberApprovalForm(forms.Form):
    """Form for approving/rejecting members"""
    
    ACTION_CHOICES = [
        ('approve', _('Approve SAFA Membership')),
        ('reject', _('Reject SAFA Membership')),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect()
    )
    
    rejection_reason = forms.CharField(
        max_length=500,
        required=False,
        label=_("Rejection Reason"),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    send_notification = forms.BooleanField(
        initial=True,
        required=False,
        label=_("Send email notification to member")
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        rejection_reason = cleaned_data.get('rejection_reason')
        
        # Rejection reason is required for rejection
        if action == 'reject' and not rejection_reason:
            raise ValidationError(_("Rejection reason is required when rejecting a member"))
        
        return cleaned_data


class TransferApprovalForm(forms.Form):
    """Form for approving/rejecting transfers"""
    
    ACTION_CHOICES = [
        ('approve', _('Approve Transfer')),
        ('reject', _('Reject Transfer')),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect()
    )
    
    rejection_reason = forms.CharField(
        max_length=500,
        required=False,
        label=_("Rejection Reason"),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    effective_date = forms.DateField(
        required=False,
        label=_("Effective Date"),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text=_("Leave blank to use today's date")
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        rejection_reason = cleaned_data.get('rejection_reason')
        effective_date = cleaned_data.get('effective_date')
        
        # Rejection reason is required for rejection
        if action == 'reject' and not rejection_reason:
            raise ValidationError(_("Rejection reason is required when rejecting a transfer"))
        
        # Effective date cannot be in the past for approvals
        if action == 'approve' and effective_date and effective_date < timezone.now().date():
            raise ValidationError(_("Effective date cannot be in the past"))
        
        return cleaned_data


class WorkflowUpdateForm(forms.Form):
    """Form for updating workflow steps"""
    
    STEP_STATUS_CHOICES = [
        ('NOT_STARTED', _('Not Started')),
        ('IN_PROGRESS', _('In Progress')),
        ('COMPLETED', _('Completed')),
        ('BLOCKED', _('Blocked')),
    ]
    
    personal_info_status = forms.ChoiceField(
        choices=STEP_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    club_selection_status = forms.ChoiceField(
        choices=STEP_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    document_upload_status = forms.ChoiceField(
        choices=STEP_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    payment_status = forms.ChoiceField(
        choices=STEP_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    club_approval_status = forms.ChoiceField(
        choices=STEP_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    safa_approval_status = forms.ChoiceField(
        choices=STEP_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


class ClubMemberQuotaForm(forms.ModelForm):
    """Form for managing club member quotas"""
    
    class Meta:
        model = ClubMemberQuota
        fields = ['max_senior_players', 'max_junior_players', 'max_officials']
        widgets = {
            'max_senior_players': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100'
            }),
            'max_junior_players': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '200'
            }),
            'max_officials': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '50'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        max_senior = cleaned_data.get('max_senior_players', 0)
        max_junior = cleaned_data.get('max_junior_players', 0)
        max_officials = cleaned_data.get('max_officials', 0)
        
        # Validate reasonable limits
        if max_senior < 10:
            self.add_error('max_senior_players', _("Minimum 10 senior players required"))
        
        if max_junior < 0:
            self.add_error('max_junior_players', _("Junior player quota cannot be negative"))
        
        if max_officials < 5:
            self.add_error('max_officials', _("Minimum 5 officials required"))
        
        return cleaned_data


# ============================================================================
# LEGACY FORMS (Keep for backward compatibility during migration)
# ============================================================================

class LegacyMembershipApplicationForm(forms.Form):
    """Legacy form - redirects to new system"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This form is just a placeholder that redirects to the new system
        pass


class SeniorMemberRegistrationForm(MemberRegistrationForm):
    """Alias for backward compatibility"""
    pass


# ============================================================================
# UTILITY FORMS
# ============================================================================

class EmailTestForm(forms.Form):
    """Form for testing email functionality"""
    
    recipient_email = forms.EmailField(
        label=_("Recipient Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    subject = forms.CharField(
        max_length=200,
        label=_("Subject"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    message = forms.CharField(
        label=_("Message"),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5})
    )


class SystemHealthCheckForm(forms.Form):
    """Form for system health checks"""
    
    CHECK_TYPES = [
        ('data_integrity', _('Data Integrity Check')),
        ('member_validation', _('Member Validation')),
        ('invoice_validation', _('Invoice Validation')),
        ('workflow_validation', _('Workflow Validation')),
        ('all', _('All Checks')),
    ]
    
    check_type = forms.ChoiceField(
        choices=CHECK_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    fix_issues = forms.BooleanField(
        required=False,
        label=_("Automatically fix issues where possible"),
        help_text=_("Warning: This will modify data")
    )


class BackupRestoreForm(forms.Form):
    """Form for backup and restore operations"""
    
    OPERATION_CHOICES = [
        ('backup', _('Create Backup')),
        ('restore', _('Restore from Backup')),
    ]
    
    operation = forms.ChoiceField(
        choices=OPERATION_CHOICES,
        widget=forms.RadioSelect()
    )
    
    backup_file = forms.FileField(
        required=False,
        label=_("Backup File"),
        help_text=_("Required for restore operations"),
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    include_documents = forms.BooleanField(
        initial=True,
        required=False,
        label=_("Include uploaded documents")
    )

    def clean(self):
        cleaned_data = super().clean()
        operation = cleaned_data.get('operation')
        backup_file = cleaned_data.get('backup_file')
        
        if operation == 'restore' and not backup_file:
            raise ValidationError(_("Backup file is required for restore operations"))
        
        return cleaned_data