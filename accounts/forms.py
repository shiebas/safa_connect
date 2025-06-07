import datetime
from django import forms
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset, Div, HTML, ButtonHolder, Submit
from django.db.models.query import EmptyQuerySet as DjangoEmptyQuerySet

# Import models based on your project structure
from .models import CustomUser

# Always import Province since we know it exists
from geography.models import Province

# Try to import other models safely
try:
    from geography.models import Region
except ImportError:
    Region = None

try:
    from geography.models import LocalFederation  # Try first in geography app
except ImportError:
    try:
        from membership.models import LocalFederation  # Try next in membership app
    except ImportError:
        LocalFederation = None

try:
    from membership.models import Club
except ImportError:
    Club = None

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
    id_document = forms.FileField(required=False, label="Upload Document")
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        required=False,
        label='Province',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = CustomUser
        fields = (
            'email', 'name', 'middle_name', 'surname', 'alias', 'date_of_birth', 'gender', 'role',
            'id_number', 'id_number_other', 'passport_number', 'id_document_type',
            'phone_number', 'address', 'city', 'postal_code', 'country', 'profile_photo', 
            'id_document',  # Changed from 'document' to match model
            'password1', 'password2', 'province'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # IMPORTANT: Set to False to use our own form tag
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        
        # Maintain all original IDs for JS to work
        self.helper.layout = Layout(
            Fieldset(
                'Account Information',
                Div(
                    Div(Field('email', css_id='id_email'), css_class='col-md-4'),
                    Div(Field('password1', css_id='id_password1'), css_class='col-md-4'),
                    Div(Field('password2', css_id='id_password2'), css_class='col-md-4'),
                    css_class='row mb-3'
                ),
            ),
            
            Fieldset(
                'Personal Information',
                Div(
                    Div(Field('name', css_id='id_name'), css_class='col-md-6'),
                    Div(Field('surname', css_id='id_surname'), css_class='col-md-6'),
                    css_class='row mb-3'
                ),
                Div(
                    Div(Field('role', css_id='id_role'), css_class='col-md-6'),
                    css_class='row mb-3'
                ),
            ),
            
            Fieldset(
                'Identification',
                Div(
                    Div(Field('id_document_type', css_id='id_id_document_type'), css_class='col-md-4'),
                    Div(
                        Field('id_number', css_id='id_id_number'),
                        HTML('<div id="id_number_error" class="text-danger" style="display:none;"></div>'),
                        HTML('<div id="id-extra-fields" style="display:none;">'),
                        Field('date_of_birth', css_id='id_date_of_birth'),
                        Field('gender', css_id='id_gender'),
                        HTML('</div>'),
                        css_class='col-md-4',
                        css_id='id_number_box'
                    ),
                    Div(Field('passport_number', css_id='id_passport_number'), css_class='col-md-4', css_id='passport_box'),
                    Div(Field('id_document', css_id='id_document'), css_class='col-md-4', css_id='document_box'),
                    css_class='row mb-3'
                ),
            ),
            
            # Country & Profile Photo
            Div(
                Div(
                    Field('country', css_id='id_country'),
                    HTML('<span id="country-flag" class="input-group-text" style="display:none;">'
                         '<img src="https://flagcdn.com/za.svg" alt="South Africa" width="24" height="16" style="margin-right:4px;">'
                         '<span id="country-code" style="font-weight:bold;">ZAF</span>'
                         '</span>'),
                    css_class='col-md-6 position-relative'
                ),
                Div(Field('profile_photo', css_id='id_profile_photo'), css_class='col-md-6'),
                css_class='row mb-3'
            ),
            
            # Admin-specific fields section - all in one container for easier showing/hiding
            Fieldset(
                'Admin-Specific Information',
                # Province Admin field
                Div(
                    Div(
                        Field('province', css_class='form-control'),
                        css_class='col-md-6'
                    ),
                    css_class='row mb-3 admin-field-wrapper province-field-wrapper',
                    css_id='province-field-container'
                ),
                # Region Admin field
                Div(
                    Div(
                        Field('region', css_class='form-control'),
                        css_class='col-md-6'
                    ),
                    css_class='row mb-3 admin-field-wrapper region-field-wrapper',
                    css_id='region-field-container'
                ),
                # LFA Admin field
                Div(
                    Div(
                        Field('local_federation', css_class='form-control'),
                        css_class='col-md-6'
                    ),
                    css_class='row mb-3 admin-field-wrapper lfa-field-wrapper',
                    css_id='lfa-field-container'
                ),
                # Club Admin field
                Div(
                    Div(
                        Field('club', css_class='form-control'),
                        css_class='col-md-6'
                    ),
                    css_class='row mb-3 admin-field-wrapper club-field-wrapper',
                    css_id='club-field-container'
                ),
            ),
            
            # Register button
            Div(
                ButtonHolder(
                    Submit('submit', 'Register', css_class='btn btn-dark')
                ),
                css_class='d-grid gap-2 mt-4'
            ),
            
            HTML('<div class="text-center mt-3"><p>Already have an account? <a href="{% url \'accounts:login\' %}" style="color: var(--safa-black);">Login here</a></p></div>'),
        )

    def clean(self):
        cleaned_data = super().clean()
        id_document_type = cleaned_data.get("id_document_type")
        id_number = cleaned_data.get("id_number")
        country = cleaned_data.get("country")
        role = cleaned_data.get('role')
        
        # Validate province is provided for Province Admins
        if role == 'ADMIN_PROVINCE' and not cleaned_data.get('province'):
            self.add_error('province', 'Province is required for Province Admins')
        
        # Validate region is provided for Region Admins
        if role == 'ADMIN_REGION' and not cleaned_data.get('region'):
            self.add_error('region', 'Region is required for Region Admins')
        
        # Validate LFA is provided for LFA Admins
        if role == 'ADMIN_LOCAL_FED' and not cleaned_data.get('local_federation'):
            self.add_error('local_federation', 'Local Federation is required for LFA Admins')
        
        # Validate club is provided for Club Admins
        if role == 'CLUB_ADMIN' and not cleaned_data.get('club'):
            self.add_error('club', 'Club is required for Club Admins')
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Check if field exists before using it
        role = self.cleaned_data.get('role')
        
        # Access province field safely
        if role == 'ADMIN_PROVINCE':
            province = self.cleaned_data.get('province')
            if province and hasattr(user, 'province_id'):
                user.province_id = province.id
        elif role == 'ADMIN_REGION' and self.cleaned_data.get('region'):
            user.region_id = self.cleaned_data.get('region').id
        elif role == 'ADMIN_LOCAL_FED' and self.cleaned_data.get('local_federation'):
            user.local_federation_id = self.cleaned_data.get('local_federation').id
        elif role == 'CLUB_ADMIN' and self.cleaned_data.get('club'):
            user.club_id = self.cleaned_data.get('club').id
        
        if commit:
            user.save()
            
        return user
