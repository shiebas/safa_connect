import os
import datetime
import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django.forms import ValidationError
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Field, HTML, ButtonHolder, Submit, Row, Column
from .models import CustomUser, EMPLOYMENT_STATUS, Position, OrganizationType, ROLES, REGISTRATION_ROLES
from geography.models import Province, Region, LocalFootballAssociation, Club, NationalFederation, Association, Country
from django.db.models import Q
from membership.models import Member, Invoice
from geography.models import Country, Province, Region, LocalFootballAssociation, Club
from .utils import extract_sa_id_dob_gender
from membership.safa_config_models import SAFASeasonConfig


class SAFASeasonConfigForm(forms.ModelForm):
    class Meta:
        model = SAFASeasonConfig
        fields = '__all__'


class NationalAdminRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    organization_type = forms.ModelChoiceField(
        queryset=OrganizationType.objects.all(),
        required=True,
        label="Administrator Type",
        help_text="Select the type of organization you will be administering."
    )
    position = forms.ModelChoiceField(
        queryset=Position.objects.all(),
        required=False,
        label="Position",
        help_text="Select your position within the organization."
    )
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        required=False,
    )
    region = forms.ModelChoiceField(
        queryset=Region.objects.none(),
        required=False,
    )
    local_federation = forms.ModelChoiceField(
        queryset=LocalFootballAssociation.objects.none(),
        required=False,
        label="Local Football Association"
    )
    club = forms.ModelChoiceField(
        queryset=Club.objects.none(),
        required=False,
    )
    id_document_type = forms.ChoiceField(
        choices=[('ID', 'ID Number'), ('PP', 'Passport')],
        required=True,
        label="ID Document Type"
    )

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'id_document_type', 'id_number', 'passport_number',
            'date_of_birth', 'gender', 'profile_picture', 'id_document',
            'organization_type', 'position', 'province',
            'region', 'local_federation', 'club', 'popi_act_consent', 'password', 'password2'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update({'class': 'form-control', 'type': 'date'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Personal Information',
                Row(
                    Column('first_name', css_class='form-group col-md-6 mb-0'),
                    Column('last_name', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('email', css_class='form-group col-md-6 mb-0'),
                    Column('phone_number', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Div(id='email-validation-message', css_class='mt-1 small'),
                'profile_picture',
            ),
            Fieldset(
                'Organization Information',
                'organization_type',
                'position',
                Div(
                    'province',
                    id='province-field',
                    style='display:none;'
                ),
                Div(
                    'region',
                    id='region-field',
                    style='display:none;'
                ),
                Div(
                    'local_federation',
                    id='lfa-field',
                    style='display:none;'
                ),
                Div(
                    'club',
                    id='club-field',
                    style='display:none;'
                ),
            ),
            Fieldset(
                'Document Information',
                'id_document_type',
                Div(
                    'id_number',
                    id='sa-id-container'
                ),
                Div(id='id-validation-message', css_class='mt-1 small'),
                Div(
                    'passport_number',
                    id='passport-container',
                    style='display:none;'
                ),
                Row(
                    Column('date_of_birth', css_class='form-group col-md-6 mb-0'),
                    Column('gender', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row',
                    id='dob-gender-manual-row',
                    style='display:none;'
                ),
                'id_document'
            ),
            Fieldset(
                'Security & Compliance',
                'popi_act_consent',
                Row(
                    Column('password', css_class='form-group col-md-6 mb-0'),
                    Column('password2', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                )
            )
        )

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if len(first_name) < 3:
            raise forms.ValidationError("First name must be at least 3 characters long.")
        if not first_name.isalpha():
            raise forms.ValidationError("First name must only contain letters.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if len(last_name) < 3:
            raise forms.ValidationError("Last name must be at least 3 characters long.")
        if not last_name.isalpha():
            raise forms.ValidationError("Last name must only contain letters.")
        return last_name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            # Remove leading '+' for validation, but allow it
            cleaned_number = phone_number[1:] if phone_number.startswith('+') else phone_number
            if not cleaned_number.isdigit():
                raise forms.ValidationError("Phone number must be numeric (with an optional leading '+').")
        return phone_number

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")

        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords don't match.")

        if password:
            if len(password) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")
            if not re.search(r'[A-Z]', password):
                raise forms.ValidationError("Password must contain at least one uppercase letter.")
            if not re.search(r'[a-z]', password):
                raise forms.ValidationError("Password must contain at least one lowercase letter.")
            if not re.search(r'[0-9]', password):
                raise forms.ValidationError("Password must contain at least one number.")
            if not re.search(r'[\W_]', password):
                raise forms.ValidationError("Password must contain at least one special character.")

        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()

        id_document_type = cleaned_data.get('id_document_type')
        id_number = cleaned_data.get('id_number')
        passport_number = cleaned_data.get('passport_number')
        date_of_birth = cleaned_data.get('date_of_birth')
        gender = cleaned_data.get('gender')

        if id_document_type == 'ID':
            if not id_number:
                self.add_error('id_number', 'ID number is required when document type is ID.')
            # The extract_sa_id_dob_gender and setting of dob/gender is now handled in clean_id_number
            # So no need to repeat here.
        elif id_document_type == 'PP':
            if not passport_number:
                self.add_error('passport_number', 'Passport number is required when document type is Passport.')
            if not date_of_birth:
                self.add_error('date_of_birth', 'Date of birth is required when document type is Passport.')
            if not gender:
                self.add_error('gender', 'Gender is required when document type is Passport.')
        else: # Should not happen with required ChoiceField, but for robustness
            self.add_error('id_document_type', 'Please select a document type.')


        # Existing file size and type validations
        profile_picture = cleaned_data.get('profile_picture')
        if profile_picture:
            if profile_picture.size > 5 * 1024 * 1024:
                self.add_error('profile_picture', 'File size must not exceed 5MB.')
            if profile_picture.content_type not in ['image/jpeg', 'image/png', 'application/pdf']:
                self.add_error('profile_picture', 'Invalid file type. Only JPG, PNG, and PDF are allowed.')

        id_document = cleaned_data.get('id_document')
        if id_document:
            if id_document.size > 5 * 1024 * 1024:
                self.add_error('id_document', 'File size must not exceed 5MB.')
            if id_document.content_type not in ['image/jpeg', 'image/png', 'application/pdf']:
                self.add_error('id_document', 'Invalid file type. Only JPG, PNG, and PDF are allowed.')

        # Geographic validations (if applicable, based on your model)
        province = cleaned_data.get('province')
        region = cleaned_data.get('region')
        local_federation = cleaned_data.get('lfa') # Note: 'lfa' in RegistrationForm, not 'local_federation'
        club = cleaned_data.get('club')

        if province and region and region.province != province:
            self.add_error('region', 'Region does not belong to the selected province.')

        if region and local_federation and local_federation.region != region:
            self.add_error('lfa', 'LFA does not belong to the selected region.')

        if local_federation and club and club.localfootballassociation != local_federation:
            self.add_error('club', 'Club does not belong to the selected LFA.')

        return cleaned_data


class RegistrationForm(forms.ModelForm):

    has_email = forms.BooleanField(
        required=False,
        initial=True,
        label="Does the person have an email address?",
        help_text="For juniors or members without email, uncheck this and we'll generate one."
    )
    role = forms.ChoiceField(
        choices=ROLES,
        required=True,
        label="I am a.../Ek is n"
    )
    is_existing_member = forms.BooleanField(
        required=False,
        label="I already have a SAFA ID"
    )
    previous_safa_id = forms.CharField(
        max_length=5,
        required=False,
        label="My existing SAFA ID",
        help_text="Enter your existing 5-character SAFA ID."
    )
    id_document_type = forms.ChoiceField(
        choices=[('ID', 'ID Number'), ('PP', 'Passport')],
        required=True,
        label="ID Document Type",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_id_document_type'})
    )
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=False,
        label="Country",
    )
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        required=False,
        empty_label="Select Province",
    )
    region = forms.ModelChoiceField(
        queryset=Region.objects.none(),
        required=False,
    )
    lfa = forms.ModelChoiceField(
        queryset=LocalFootballAssociation.objects.none(),
        required=False,
        label="Local Football Association"
    )
    club = forms.ModelChoiceField(
        queryset=Club.objects.none(),
        required=False,
    )
    association = forms.ModelChoiceField(
        queryset=Association.objects.all(),
        required=False,
        label="Association (for Officials)"
    )

    popi_act_consent = forms.BooleanField(required=True, label="POPI Act Consent")
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)
    extracted_dob = forms.DateField(required=False, widget=forms.HiddenInput())
    extracted_gender = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = CustomUser
        fields = ['role', 'first_name', 'last_name', 'email', 'id_document_type', 'id_number', 'passport_number',
                  'date_of_birth', 'gender', 'profile_picture', 'id_document',
                   'street_address', 'suburb', 'city', 'state', 'postal_code',
                   'is_existing_member', 'previous_safa_id', 'association', 'extracted_dob', 'extracted_gender']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        limit_role_choices = kwargs.pop('limit_role_choices', False)
        super().__init__(*args, **kwargs)

        # Make email not required initially - it will be validated in clean_email based on has_email
        self.fields['email'].required = False

        if limit_role_choices:
            self.fields['role'].choices = REGISTRATION_ROLES # Use the limited choices

        try:
            south_africa = Country.objects.get(name='South Africa')
            self.fields['country'].initial = south_africa
        except Country.DoesNotExist:
            pass

        if 'province' in self.data:
            try:
                province_id = int(self.data.get('province'))
                self.fields['region'].queryset = Region.objects.filter(province_id=province_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty queryset
        elif self.instance.pk and self.instance.province:
            self.fields['region'].queryset = self.instance.province.region_set.order_by('name')

        if 'region' in self.data:
            try:
                region_id = int(self.data.get('region'))
                self.fields['lfa'].queryset = LocalFootballAssociation.objects.filter(region_id=region_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.region:
            self.fields['lfa'].queryset = self.instance.region.localfootballassociation_set.order_by('name')

        if 'lfa' in self.data:
            try:
                lfa_id = int(self.data.get('lfa'))
                self.fields['club'].queryset = Club.objects.filter(localfootballassociation_id=lfa_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.lfa:
            self.fields['club'].queryset = self.instance.lfa.club_set.order_by('name')

        # Add autocomplete attributes
        self.fields['first_name'].widget.attrs.update({'autocomplete': 'given-name'})
        self.fields['last_name'].widget.attrs.update({'autocomplete': 'family-name'})
        self.fields['email'].widget.attrs.update({'autocomplete': 'email'})
        # Check if phone_number field exists before trying to update its attrs
        if 'phone_number' in self.fields:
            self.fields['phone_number'].widget.attrs.update({'autocomplete': 'tel'})
        self.fields['id_number'].widget.attrs.update({'autocomplete': 'off'})
        self.fields['passport_number'].widget.attrs.update({'autocomplete': 'off'})
        self.fields['date_of_birth'].widget.attrs.update({'autocomplete': 'bday'})
        self.fields['gender'].widget.attrs.update({'autocomplete': 'sex'})
        self.fields['password'].widget.attrs.update({'autocomplete': 'new-password'})
        self.fields['password2'].widget.attrs.update({'autocomplete': 'new-password'})

        role = self.data.get('role') or self.initial.get('role')
        if role:
            if role == 'PLAYER':
                self.fields['club'].required = True
                self.fields['association'].required = False
            elif role == 'OFFICIAL':
                self.fields['club'].required = False
                # Association is only required if it's not a club admin doing the registration
                if not user or user.role != 'CLUB_ADMIN':
                    self.fields['association'].required = True
                else:
                    self.fields['association'].required = False
            elif role == 'SUPPORTER':
                self.fields['province'].widget = forms.HiddenInput()
                self.fields['region'].widget = forms.HiddenInput()
                self.fields['lfa'].widget = forms.HiddenInput()
                self.fields['club'].widget = forms.HiddenInput()
                self.fields['association'].widget = forms.HiddenInput()
            else: # For ADMIN roles
                self.fields['club'].required = False
                self.fields['association'].required = False
        
        # Handle club admin context - pre-populate and disable geographic fields
        if user and user.role == 'CLUB_ADMIN':
            # Pre-populate with admin's geographic data
            if user.club:
                self.fields['club'].queryset = Club.objects.filter(id=user.club.id)
                self.fields['club'].initial = user.club
                
                if user.club.localfootballassociation:
                    self.fields['lfa'].queryset = LocalFootballAssociation.objects.filter(id=user.club.localfootballassociation.id)
                    self.fields['lfa'].initial = user.club.localfootballassociation
                    
                    if user.club.localfootballassociation.region:
                        self.fields['region'].queryset = Region.objects.filter(id=user.club.localfootballassociation.region.id)
                        self.fields['region'].initial = user.club.localfootballassociation.region
                        
                        if user.club.localfootballassociation.region.province:
                            self.fields['province'].queryset = Province.objects.filter(id=user.club.localfootballassociation.region.province.id)
                            self.fields['province'].initial = user.club.localfootballassociation.region.province
            
            # Disable geographic fields so they cannot be changed
            self.fields['province'].disabled = True
            self.fields['region'].disabled = True
            self.fields['lfa'].disabled = True
            self.fields['club'].disabled = True
            
            # Add styling to show these are read-only
            self.fields['province'].widget.attrs.update({'class': 'form-control', 'readonly': True, 'style': 'background-color: #f8f9fa; cursor: not-allowed;'})
            self.fields['region'].widget.attrs.update({'class': 'form-control', 'readonly': True, 'style': 'background-color: #f8f9fa; cursor: not-allowed;'})
            self.fields['lfa'].widget.attrs.update({'class': 'form-control', 'readonly': True, 'style': 'background-color: #f8f9fa; cursor: not-allowed;'})
            self.fields['club'].widget.attrs.update({'class': 'form-control', 'readonly': True, 'style': 'background-color: #f8f9fa; cursor: not-allowed;'})

        self.helper = FormHelper()
        self.helper.layout = Layout(
            'role',
            'is_existing_member',
            'previous_safa_id',
            'first_name',
            'last_name',
            'has_email',
            'email',
            'id_document_type',
            Div(
                'id_number',
                css_id='id_number_box',
                css_class='sa-id-field', # Changed css_class to sa-id-field
                style='display:block;' # Changed to display:block
            ),
            Div(
                'passport_number',
                css_id='passport_box',
                css_class='passport-field',
                style='display:none;' # Hidden by default, shown by JS
            ),
            Div( # New Div for dob and gender
                'date_of_birth',
                'gender',
                css_id='dob-gender-manual-row',
                style='display:none;' # Hidden by default, shown by JS when passport is selected
            ),
            'profile_picture',
            'id_document',
            'popi_act_consent',
            'password',
            'password2',
            'country',
            'province',
            'region',
            'lfa',
            'club',
            'association',
        )

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            if len(first_name) < 3:
                raise forms.ValidationError("First name must be at least 3 characters long.")
            if not re.match(r"^[A-Za-z\s'-]+$", first_name):
                raise forms.ValidationError("First name can only contain letters, spaces, hyphens, and apostrophes.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            if len(last_name) < 3:
                raise forms.ValidationError("Last name must be at least 3 characters long.")
            if not re.match(r"^[A-Za-z\s'-]+$", last_name):
                raise forms.ValidationError("Last name can only contain letters, spaces, hyphens, and apostrophes.")
        return last_name

    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number')
        if not id_number:
            return id_number # Allow empty if not required, or handle required elsewhere

        # Check for uniqueness first
        if CustomUser.objects.filter(id_number=id_number).exists():
            raise forms.ValidationError("A user with this ID number already exists.")

        # Validate SA ID number format and extract DOB/Gender
        dob, gen = extract_sa_id_dob_gender(id_number)
        if not dob or not gen:
            raise forms.ValidationError("Invalid South African ID number format or checksum.")

        # Set date_of_birth and gender in cleaned_data
        self.cleaned_data['date_of_birth'] = dob
        self.cleaned_data['gender'] = gen

        return id_number

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Don't validate email here - we'll handle it in clean() method
        # Just check for duplicate if email is provided
        if email and CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email address already exists. Please use a different email or log in.")
        
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        has_email = cleaned_data.get('has_email', True)
        email = cleaned_data.get('email')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        role = cleaned_data.get('role')
        
        # Validate email requirement
        if has_email and not email:
            self.add_error('email', "Email address is required when 'has email' is checked.")
        
        # Generate email if user doesn't have one
        if not has_email and first_name and last_name:
            # Import the email generation function
            from .utils import generate_unique_member_email
            
            # Generate email based on role
            if role == 'PLAYER':
                email_type = 'player'
            elif role == 'OFFICIAL':
                email_type = 'official'
            else:
                email_type = 'member'
            
            # Generate the unique email
            generated_email = generate_unique_member_email(first_name, last_name, email_type)
            cleaned_data['email'] = generated_email
        
        return cleaned_data

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords don't match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class ClubAdminAddPlayerForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'id_number', 'passport_number',
            'date_of_birth', 'gender', 'profile_picture', 'id_document',
            'popi_act_consent'
        ]

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class AssociationOfficialRegistrationForm(forms.ModelForm):
    id_document_type = forms.ChoiceField(
        choices=[('ID', 'ID Number'), ('PP', 'Passport')],
        required=True,
        label="ID Document Type"
    )
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'id_number', 'passport_number',
            'date_of_birth', 'gender', 'profile_picture', 'id_document',
            'popi_act_consent'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'first_name',
            'last_name',
            'email',
            'id_document_type',
            'id_number',
            'passport_number',
            'date_of_birth',
            'gender',
            'profile_picture',
            'id_document',
            'popi_act_consent',
            'password',
            'password2',
        )

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name and not first_name.isalpha():
            raise forms.ValidationError("First name should only contain letters.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name and not last_name.isalpha():
            raise forms.ValidationError("Last name should only contain letters.")
        return last_name

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class RejectMemberForm(forms.Form):
    rejection_reason = forms.CharField(widget=forms.Textarea, required=True)


class MemberApprovalForm(forms.Form):
    member = forms.ModelChoiceField(queryset=Member.objects.all(), widget=forms.HiddenInput())
    is_approved = forms.BooleanField(required=False, initial=True)




class PlayerForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'id_number']


class ProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    # email is kept as a field, but will be made read-only in __init__
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = [
            'email', # Keep email, but make it read-only
            'profile_picture',
            'phone_number',
            'id_document', # Keep id_document for upload
            'street_address', 'suburb', 'city', 'state', 'postal_code',
        ]
        widgets = {
            # 'date_of_birth': forms.DateInput(attrs={'type': 'date'}) # Removed as date_of_birth is removed from fields
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email read-only
        self.fields['email'].widget.attrs['readonly'] = True


class SettingsForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']


class UpdateProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['profile_picture']


class AdvancedMemberSearchForm(forms.Form):
    """Advanced search form for members with multiple criteria"""
    
    # Basic search fields
    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, email, or SAFA ID...', 
            'autocomplete': 'off'
        }),
        label='Search'
    )
    
    # Role filter
    role = forms.ChoiceField(
        choices=[('', 'All Roles')] + list(ROLES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Role'
    )
    
    # Status filter
    membership_status = forms.ChoiceField(
        choices=[
            ('', 'All Statuses'),
            ('PENDING', 'Pending Payment'),
            ('PAID', 'Payment Received'),
            ('ACTIVE', 'Active Member'),
            ('EXPIRED', 'Membership Expired'),
            ('SUSPENDED', 'Membership Suspended')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Membership Status'
    )
    
    # Geographic filters
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        required=False,
        empty_label="All Provinces",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Province'
    )
    
    region = forms.ModelChoiceField(
        queryset=Region.objects.none(),
        required=False,
        empty_label="All Regions",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Region'
    )
    
    local_federation = forms.ModelChoiceField(
        queryset=LocalFootballAssociation.objects.none(),
        required=False,
        empty_label="All LFAs",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Local Football Association'
    )
    
    club = forms.ModelChoiceField(
        queryset=Club.objects.none(),
        required=False,
        empty_label="All Clubs",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Club'
    )
    
    association = forms.ModelChoiceField(
        queryset=Association.objects.all(),
        required=False,
        empty_label="All Associations",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Association'
    )
    
    # Date range filters
    registration_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Registered From'
    )
    
    registration_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Registered To'
    )
    
    # Age range filters
    age_from = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min age'
        }),
        label='Age From'
    )
    
    age_to = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max age'
        }),
        label='Age To'
    )
    
    # Additional filters
    gender = forms.ChoiceField(
        choices=[('', 'All Genders'), ('M', 'Male'), ('F', 'Female')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Gender'
    )
    
    has_safa_id = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Has SAFA ID'
    )
    
    popi_consent = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='POPI Consent Given'
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter geographic fields based on user\'s role and permissions
        if self.user:
            if self.user.role == 'ADMIN_PROVINCE' and self.user.province:
                self.fields['province'].queryset = Province.objects.filter(id=self.user.province.id)
                self.fields['province'].initial = self.user.province
                self.fields['region'].queryset = Region.objects.filter(province=self.user.province)
            elif self.user.role == 'ADMIN_REGION' and self.user.region:
                self.fields['region'].queryset = Region.objects.filter(id=self.user.region.id)
                self.fields['region'].initial = self.user.region
                self.fields['province'].queryset = Province.objects.filter(id=self.user.region.province.id)
                self.fields['province'].initial = self.user.region.province
            elif self.user.role == 'ADMIN_LOCAL_FED' and self.user.local_federation:
                self.fields['local_federation'].queryset = LocalFootballAssociation.objects.filter(id=self.user.local_federation.id)
                self.fields['local_federation'].initial = self.user.local_federation
            elif self.user.role == 'CLUB_ADMIN' and self.user.club:
                self.fields['club'].queryset = Club.objects.filter(id=self.user.club.id)
                self.fields['club'].initial = self.user.club
    
    def filter_queryset(self, queryset):
        """Apply filters to the queryset"""
        cleaned_data = self.cleaned_data
        
        # Text search
        search_query = cleaned_data.get('search_query')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(safa_id__icontains=search_query) |
                Q(id_number__icontains=search_query)
            )
        
        # Role filter
        role = cleaned_data.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Status filter
        membership_status = cleaned_data.get('membership_status')
        if membership_status:
            queryset = queryset.filter(membership_status=membership_status)
        
        # Geographic filters
        province = cleaned_data.get('province')
        if province:
            queryset = queryset.filter(province=province)
        
        region = cleaned_data.get('region')
        if region:
            queryset = queryset.filter(region=region)
        
        local_federation = cleaned_data.get('local_federation')
        if local_federation:
            queryset = queryset.filter(local_federation=local_federation)
        
        club = cleaned_data.get('club')
        if club:
            queryset = queryset.filter(club=club)
        
        association = cleaned_data.get('association')
        if association:
            queryset = queryset.filter(association=association)
        
        # Date range filters
        reg_from = cleaned_data.get('registration_date_from')
        if reg_from:
            queryset = queryset.filter(date_joined__gte=reg_from)
        
        reg_to = cleaned_data.get('registration_date_to')
        if reg_to:
            queryset = queryset.filter(date_joined__lte=reg_to)
        
        # Age filters
        age_from = cleaned_data.get('age_from')
        age_to = cleaned_data.get('age_to')
        if age_from or age_to:
            from datetime import date
            today = date.today()
            
            if age_from:
                birth_year_max = today.year - age_from
                queryset = queryset.filter(date_of_birth__year__lte=birth_year_max)
            
            if age_to:
                birth_year_min = today.year - age_to
                queryset = queryset.filter(date_of_birth__year__gte=birth_year_min)
        
        # Gender filter
        gender = cleaned_data.get('gender')
        if gender:
            queryset = queryset.filter(gender=gender)
        
        # SAFA ID filter
        has_safa_id = cleaned_data.get('has_safa_id')
        if has_safa_id:
            queryset = queryset.filter(safa_id__isnull=False).exclude(safa_id='')
        
        # POPI consent filter
        popi_consent = cleaned_data.get('popi_consent')
        if popi_consent:
            queryset = queryset.filter(popi_act_consent=True)
        
        return queryset

class QuickMemberLookupForm(forms.Form):
    """Quick lookup form for finding members"""
    
    lookup_type = forms.ChoiceField(
        choices=[
            ('safa_id', 'SAFA ID'),
            ('id_number', 'SA ID Number'),
            ('email', 'Email Address'),
            ('name', 'Full Name')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Search By'
    )
    
    search_value = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter search value...',
            'autocomplete': 'off'
        }),
        label='Search Value'
    )
    
    def clean_search_value(self):
        """Validate search value based on lookup type"""
        lookup_type = self.cleaned_data.get('lookup_type')
        search_value = self.cleaned_data.get('search_value', '').strip()
        
        if not search_value:
            raise forms.ValidationError('Search value is required.')
        
        if lookup_type == 'safa_id':
            if len(search_value) != 5:
                raise forms.ValidationError('SAFA ID must be exactly 5 characters.')
        elif lookup_type == 'id_number':
            if not search_value.isdigit() or len(search_value) != 13:
                raise forms.ValidationError('SA ID Number must be exactly 13 digits.')
        elif lookup_type == 'email':
            if '@' not in search_value:
                raise forms.ValidationError('Please enter a valid email address.')
        
        return search_value
    
    def find_members(self):
        """Find members based on search criteria"""
        if not self.is_valid():
            return CustomUser.objects.none()
        
        lookup_type = self.cleaned_data['lookup_type']
        search_value = self.cleaned_data['search_value']
        
        if lookup_type == 'safa_id':
            return CustomUser.objects.filter(safa_id__iexact=search_value)
        elif lookup_type == 'id_number':
            return CustomUser.objects.filter(id_number=search_value)
        elif lookup_type == 'email':
            return CustomUser.objects.filter(email__iexact=search_value)
        elif lookup_type == 'name':
            return CustomUser.objects.filter(
                Q(first_name__icontains=search_value) |
                Q(last_name__icontains=search_value) |
                Q(first_name__icontains=search_value.split()[0] if ' ' in search_value else search_value) |
                Q(last_name__icontains=search_value.split()[-1] if ' ' in search_value else search_value)
            )
        
        return CustomUser.objects.none()


class ModernContactForm(forms.Form):
    """Modern contact form for support requests"""
    
    INQUIRY_TYPES = [
        ('general', 'General Inquiry'),
        ('registration', 'Registration Issue'),
        ('payment', 'Payment Problem'),
        ('technical', 'Technical Support'),
        ('document', 'Document Issue'),
        ('membership', 'Membership Question'),
        ('club', 'Club Administration'),
        ('official', 'Official Registration'),
        ('other', 'Other')
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low - General question'),
        ('normal', 'Normal - Standard request'),
        ('high', 'High - Urgent issue'),
        ('critical', 'Critical - System blocking')
    ]
    
    # Contact details
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your full name'
        }),
        label='Full Name'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        }),
        label='Email Address'
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+27xx xxx xxxx (optional)'
        }),
        label='Phone Number'
    )
    
    # SAFA details
    safa_id = forms.CharField(
        max_length=5,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your SAFA ID (if applicable)'
        }),
        label='SAFA ID'
    )
    
    # Inquiry details
    inquiry_type = forms.ChoiceField(
        choices=INQUIRY_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Inquiry Type'
    )
    
    priority = forms.ChoiceField(
        choices=PRIORITY_LEVELS,
        initial='normal',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Priority Level'
    )
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Brief description of your issue'
        }),
        label='Subject'
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Please provide detailed information about your inquiry...'
        }),
        label='Message'
    )
    
    # File attachment
    attachment = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
        }),
        label='Attachment',
        help_text='Optional: Attach relevant documents (PDF, images, Word docs)'
    )
    
    # Agreement
    data_processing_consent = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I consent to my data being processed to respond to this inquiry'
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-populate fields for logged-in users
        if self.user and self.user.is_authenticated:
            self.fields['name'].initial = self.user.get_full_name()
            self.fields['email'].initial = self.user.email
            if hasattr(self.user, 'safa_id') and self.user.safa_id:
                self.fields['safa_id'].initial = self.user.safa_id
    
    def clean_attachment(self):
        """Validate file attachment"""
        attachment = self.cleaned_data.get('attachment')
        
        if attachment:
            # Check file size (max 5MB)
            if attachment.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size must not exceed 5MB.')
            
            # Check file type
            allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg',
                           'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            
            if attachment.content_type not in allowed_types:
                raise forms.ValidationError('File type not allowed. Please upload PDF, image, or Word document.')
        
        return attachment


class BulkActionForm(forms.Form):
    """Form for performing bulk actions on members"""
    
    BULK_ACTIONS = [
        ('', 'Select Action...'),
        ('approve', 'Approve Selected Members'),
        ('suspend', 'Suspend Selected Members'),
        ('activate', 'Activate Selected Members'),
        ('deactivate', 'Deactivate Selected Members'),
        ('export', 'Export Selected Members'),
        ('send_email', 'Send Email to Selected'),
        ('update_status', 'Update Membership Status'),
        ('generate_cards', 'Generate Digital Cards'),
        ('send_reminders', 'Send Payment Reminders')
    ]
    
    STATUS_UPDATES = [
        ('', 'Select New Status...'),
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Payment Received'),
        ('ACTIVE', 'Active Member'),
        ('EXPIRED', 'Membership Expired'),
        ('SUSPENDED', 'Membership Suspended')
    ]
    
    action = forms.ChoiceField(
        choices=BULK_ACTIONS,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'toggleBulkActionFields(this.value)'
        }),
        label='Bulk Action'
    )
    
    # For status updates
    new_status = forms.ChoiceField(
        choices=STATUS_UPDATES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='New Status'
    )
    
    # For email sending
    email_subject = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email subject line'
        }),
        label='Email Subject'
    )
    
    email_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Email message content'
        }),
        label='Email Message'
    )
    
    # Confirmation
    confirm_action = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I confirm this bulk action'
    )
    
    # Notes for action
    action_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional notes about this action'
        }),
        label='Action Notes'
    )
    
    def clean(self):
        """Validate form based on selected action"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        
        if action == 'update_status':
            new_status = cleaned_data.get('new_status')
            if not new_status:
                raise forms.ValidationError('New status is required for status update action.')
        
        elif action == 'send_email':
            email_subject = cleaned_data.get('email_subject')
            email_message = cleaned_data.get('email_message')
            
            if not email_subject:
                raise forms.ValidationError('Email subject is required for email action.')
            if not email_message:
                raise forms.ValidationError('Email message is required for email action.')
        
        return cleaned_data


class StatisticsForm(forms.Form):
    """Form for generating quick statistics"""
    
    STAT_TYPES = [
        ('overview', 'General Overview'),
        ('registrations', 'Registration Statistics'),
        ('financial', 'Financial Summary'),
        ('geographic', 'Geographic Distribution'),
        ('demographics', 'Demographics Breakdown'),
        ('activity', 'Recent Activity'),
        ('compliance', 'Compliance Status')
    ]
    
    TIME_PERIODS = [
        ('today', 'Today'),
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('quarter', 'This Quarter'),
        ('year', 'This Year'),
        ('all', 'All Time'),
        ('custom', 'Custom Range')
    ]
    
    stat_type = forms.ChoiceField(
        choices=STAT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Statistics Type'
    )
    
    time_period = forms.ChoiceField(
        choices=TIME_PERIODS,
        initial='month',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'toggleCustomDateRange(this.value)'
        }),
        label='Time Period'
    )
    
    # Custom date range
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='From Date'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='To Date'
    )
    
    # Filters
    role_filter = forms.ChoiceField(
        choices=[('', 'All Roles')] + list(ROLES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Filter by Role'
    )
    
    status_filter = forms.ChoiceField(
        choices=[
            ('', 'All Statuses'),
            ('ACTIVE', 'Active'),
            ('PENDING', 'Pending'),
            ('SUSPENDED', 'Suspended'),
            ('EXPIRED', 'Expired')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Filter by Status'
    )
    
    include_charts = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Include Charts'
    )
    
    def clean(self):
        """Validate custom date range"""
        cleaned_data = super().clean()
        time_period = cleaned_data.get('time_period')
        
        if time_period == 'custom':
            date_from = cleaned_data.get('date_from')
            date_to = cleaned_data.get('date_to')
            
            if not date_from or not date_to:
                raise forms.ValidationError('Both start and end dates are required for custom range.')
            
            if date_from > date_to:
                raise forms.ValidationError('Start date must be before end date.')
            
            # Check if date range is reasonable (not more than 5 years)
            from datetime import timedelta
            if date_to - date_from > timedelta(days=1825):  # 5 years
                raise forms.ValidationError('Date range cannot exceed 5 years.')
        
        return cleaned_data
    
    def get_date_range(self):
        """Get the actual date range based on selected period"""
        time_period = self.cleaned_data.get('time_period')
        
        if time_period == 'custom':
            return self.cleaned_data.get('date_from'), self.cleaned_data.get('date_to')
        
        from datetime import date, timedelta
        today = date.today()
        
        if time_period == 'today':
            return today, today
        elif time_period == 'week':
            start = today - timedelta(days=today.weekday())
            return start, today
        elif time_period == 'month':
            start = today.replace(day=1)
            return start, today
        elif time_period == 'quarter':
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            start = today.replace(month=quarter_start_month, day=1)
            return start, today
        elif time_period == 'year':
            start = today.replace(month=1, day=1)
            return start, today
        else:  # all time
            return None, None


class EditPlayerForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'id_number', 'passport_number',
            'date_of_birth', 'gender', 'membership_status',
            'street_address', 'suburb', 'city', 'state', 'postal_code',
            'guardian_name', 'guardian_phone', 'guardian_email', 'parental_consent'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'street_address': forms.TextInput(attrs={'class': 'form-control'}),
            'suburb': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'parental_consent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'membership_status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make most fields read-only
        read_only_fields = [
            'first_name', 'last_name', 'email', 'id_number', 'passport_number',
            'date_of_birth', 'gender',
        ]
        for field in read_only_fields:
            if field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True
                self.fields[field].widget.attrs['class'] = 'form-control-plaintext' # Add a class for styling read-only fields

        # Conditionally make guardian fields required for minors
        if self.instance and self.instance.age and self.instance.age < 18:
            self.fields['guardian_name'].required = True
            self.fields['guardian_phone'].required = True
            self.fields['parental_consent'].required = True


class ConfirmPaymentForm(forms.Form):
    invoice_number = forms.CharField(
        label="Invoice Number",
        max_length=100,
        help_text="Enter the invoice number (e.g., MEMYYYYMMDD/SAFAID-XX) to find the invoice.",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class ProofOfPaymentForm(forms.Form):
    invoice_uuid = forms.UUIDField(widget=forms.HiddenInput())
    proof_of_payment = forms.FileField(
        label="Upload Proof of Payment",
        required=True,
        help_text="Upload a clear image or PDF of the payment receipt/proof."
    )
    payment_method = forms.ChoiceField(
        choices=Invoice.PAYMENT_METHODS,
        label="Payment Method",
        required=True
    )
    payment_reference = forms.CharField(
        label="Payment Reference",
        max_length=100,
        required=False,
        help_text="Enter the bank reference or transaction ID."
    )

    def clean_proof_of_payment(self):
        proof = self.cleaned_data.get('proof_of_payment')
        if proof:
            # Basic file type and size validation
            if not proof.content_type in ['image/jpeg', 'image/png', 'application/pdf']:
                raise forms.ValidationError("Only JPEG, PNG, and PDF files are allowed.")
            if proof.size > 5 * 1024 * 1024: # 5 MB
                raise forms.ValidationError("File size cannot exceed 5 MB.")
        return proof

class ClubAdminRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)
    national_federation = forms.ModelChoiceField(queryset=NationalFederation.objects.all(), required=False, disabled=True)
    province = forms.ModelChoiceField(queryset=Province.objects.all(), required=False, disabled=True)
    region = forms.ModelChoiceField(queryset=Region.objects.all(), required=False, disabled=True)
    lfa = forms.ModelChoiceField(queryset=LocalFootballAssociation.objects.all(), required=False, disabled=True, label="LFA")
    club = forms.ModelChoiceField(queryset=Club.objects.all(), required=False, disabled=True)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'id_document_type', 'id_number', 'passport_number',
            'date_of_birth', 'gender', 'profile_picture', 'id_document',
            'national_federation', 'province', 'region', 'lfa', 'club',
            'popi_act_consent', 'password', 'password2'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
