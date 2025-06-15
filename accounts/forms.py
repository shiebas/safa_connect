import datetime
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django.forms import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Field, HTML, ButtonHolder, Submit

from .models import CustomUser, EMPLOYMENT_STATUS, Position, OrganizationType
from geography.models import Province, Region, LocalFootballAssociation, Club, NationalFederation
from .utils import extract_sa_id_dob_gender

class EmailAuthenticationForm(AuthenticationForm):
    """Custom authentication form using email instead of username"""
    username = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Email Address'

class UniversalRegistrationForm(forms.ModelForm):
    age = forms.IntegerField(label='Age', required=False, disabled=True)
    """
    Simplified registration form for South African context.
    Passport option primarily for player registration by clubs.
    """
    # Account fields
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a secure password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    
    # Role selection
    role = forms.ChoiceField(
        choices=[
            ('ADMIN_NATIONAL', 'National Administrator'),
            ('ADMIN_PROVINCE', 'Province Administrator'),
            ('ADMIN_REGION', 'Region Administrator'), 
            ('ADMIN_LOCAL_FED', 'LFA Administrator'),
            ('CLUB_ADMIN', 'Club Administrator')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Identity fields
    id_document_type = forms.ChoiceField(
        choices=[('ID', 'SA ID'), ('PP', 'Passport'), ('OT', 'Other')],
        initial='ID',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    id_number = forms.CharField(
        max_length=13, 
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 13-digit ID number'
        })
    )
    passport_number = forms.CharField(
        max_length=25, 
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter passport number'
        })
    )
    id_number_other = forms.CharField(
        max_length=25, 
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter document number'
        })
    )
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')], required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    
    # Files - ID document moved to identity section, profile photo to compliance
    id_document = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    profile_photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}))
    
    # Geographic fields - for administrators only
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(), 
        required=False, 
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-placeholder': 'Select province'
        })
    )
    
    # Consent
    popi_act_consent = forms.BooleanField(required=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    # Add organization type field
    organization_type = forms.ModelChoiceField(
        queryset=OrganizationType.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your primary organization type"
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'email', 'first_name', 'last_name', 'role', 
            'organization_type', 
            'province', 'region', 'local_federation', 'club',
            'id_document_type', 'id_number', 'passport_number', 'id_number_other',
            'date_of_birth', 'gender', 'id_document', 'profile_photo', 
            'popi_act_consent', 'national_federation', 'age'  # add age
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, registration_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'age'):
            self.fields['age'].initial = self.instance.age
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        
        # Set default role based on registration type
        if registration_type == 'national':
            self.initial['role'] = 'ADMIN_NATIONAL'
            self.fields['role'].widget = forms.HiddenInput()
            
            # For ALL registrations, set SAFA as default national federation
            try:
                safa_federation, _ = NationalFederation.objects.get_or_create(
                    name="South African Football Association",
                    defaults={
                        'acronym': "SAFA",
                        'country_id': 1  # Assuming South Africa has ID 1
                    }
                )
                self.initial['national_federation'] = safa_federation.id
                # Make it read-only for clarity
                if 'national_federation' not in self.fields:
                    self.fields['national_federation'] = forms.ModelChoiceField(
                        queryset=NationalFederation.objects.all(),
                        required=False,
                        widget=forms.Select(attrs={'class': 'form-control', 'readonly': True})
                    )
                self.fields['national_federation'].widget.attrs['readonly'] = True
                self.fields['national_federation'].help_text = "Default: SAFA (All registrations belong to SAFA)"
            except Exception:
                pass
        
        # Add region and local_federation fields dynamically
        self.fields['region'] = forms.ModelChoiceField(
            queryset=Region.objects.none(),
            required=False,  # Will set required dynamically below
            widget=forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Select region'
            })
        )
        self.fields['local_federation'] = forms.ModelChoiceField(
            queryset=LocalFootballAssociation.objects.none(),
            required=False,
            widget=forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Select local football association'
            })
        )
        # Filter region queryset by selected province
        province_id = self.data.get('province') or self.initial.get('province')
        if province_id:
            try:
                self.fields['region'].queryset = Region.objects.filter(province_id=province_id)
            except (ValueError, TypeError):
                self.fields['region'].queryset = Region.objects.none()
        else:
            self.fields['region'].queryset = Region.objects.none()
        # Set region required for Region Admin and below
        org_type = self.initial.get('organization_type') or self.data.get('organization_type')
        if org_type:
            try:
                if hasattr(org_type, 'level'):
                    org_level = org_type.level
                else:
                    org_obj = OrganizationType.objects.get(pk=org_type)
                    org_level = org_obj.level
                if org_level in ['REGION', 'LFA', 'CLUB']:
                    self.fields['region'].required = True
                else:
                    self.fields['region'].required = False
            except Exception as e:
                self.fields['region'].required = False
        # ...existing code...
        
        # Create a layout with organization type selection
        self.helper.layout = Layout(
            # Account Information
            Fieldset(
                'Account Information',
                Div(
                    Div(Field('email', css_id='id_email'), css_class='col-md-4'),
                    Div(Field('password1', css_id='id_password1'), css_class='col-md-4'),
                    Div(Field('password2', css_id='id_password2'), css_class='col-md-4'),
                    css_class='row mb-3'
                ),
            ),
            
            # Personal Information
            Fieldset(
                'Personal Information',
                Div(
                    Div(Field('first_name', css_id='id_first_name'), css_class='col-md-6'),
                    Div(Field('last_name', css_id='id_last_name'), css_class='col-md-6'),
                    css_class='row mb-3'
                ),
                Div(
                    Div(Field('organization_type', css_id='id_organization_type'), css_class='col-md-6'),
                    Div(Field('role', css_id='id_role'), css_class='col-md-6'),
                    css_class='row mb-3'
                ),
            ),

            # Organization Information - dynamically shown based on organization type
            Fieldset(
                'Organization Information',
                Div(
                    Div(Field('province', css_id='id_province'), css_class='col-md-12'),
                    css_class='row mb-3 org-field province-field',
                    css_id='province-container',
                    style='display:none;'
                ),
                Div(
                    Div(Field('region', css_id='id_region'), css_class='col-md-12'),
                    css_class='row mb-3 org-field region-field',
                    css_id='region-container',
                    style='display:none;'
                ),
                Div(
                    Div(Field('local_federation', css_id='id_local_federation'), css_class='col-md-12'),
                    css_class='row mb-3 org-field lfa-field',
                    css_id='lfa-container',
                    style='display:none;'
                ),
                Div(
                    Div(Field('club', css_id='id_club'), css_class='col-md-12'),
                    css_class='row mb-3 org-field club-field',
                    css_id='club-container',
                    style='display:none;'
                ),
                css_id='organization-section'
            ),
            
            # Identity Information
            Fieldset(
                'Identity Information',
                Div(
                    Div(Field('id_document_type', css_id='id_id_document_type'), css_class='col-md-4'),
                    Div(
                        Field('id_number', css_id='id_id_number'),
                        HTML('<div id="id_number_error" class="text-danger" style="display:none;"></div>'),
                        css_class='col-md-4',
                        css_id='id_number_box'
                    ),
                    Div(
                        Field('passport_number', css_id='id_passport_number'),
                        css_class='col-md-4',
                        css_id='passport_box',
                        style='display:none;'
                    ),
                    Div(
                        Field('id_number_other', css_id='id_id_number_other'),
                        css_class='col-md-4',
                        css_id='id_number_other_box',
                        style='display:none;'
                    ),
                    css_class='row mb-3'
                ),
                Div(
                    Div(Field('date_of_birth', css_id='id_date_of_birth'), css_class='col-md-6'),
                    Div(Field('gender', css_id='id_gender'), css_class='col-md-6'),
                    css_class='row mb-3'
                ),
                Div(
                    Div(Field('id_document', css_id='id_id_document'), css_class='col-md-12'),
                    css_class='row mb-3'
                ),
            ),
            
            # Compliance Section (including profile photo)
            Fieldset(
                'Compliance Requirements',
                Div(
                    Div(Field('profile_photo', css_id='id_profile_photo'), css_class='col-md-12'),
                    HTML('<div class="form-text mb-3">Please upload a clear profile photo for identification</div>'),
                    css_class='row mb-3'
                ),
                Div(
                    Field('popi_act_consent', css_class='form-check-input'),
                    HTML('<div class="mt-2"><small class="text-muted">By checking this box, you consent to the POPI Act terms</small></div>'),
                    css_class='form-check'
                ),
            ),
            
            # Submit button
            Div(
                Submit('submit', 'Register', css_class='btn btn-primary'),
                css_class='d-grid gap-2 mt-4'
            ),
            
            # JavaScript for field toggling
            HTML('''
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    // ID Type field toggling
                    const idTypeSelect = document.getElementById('id_id_document_type');
                    const idNumberBox = document.getElementById('id_number_box');
                    const passportBox = document.getElementById('passport_box');
                    const otherIdBox = document.getElementById('id_number_other_box');
                    
                    function updateIdFields() {
                        const selectedValue = idTypeSelect.value;
                        
                        // Hide all ID fields first
                        idNumberBox.style.display = 'none';
                        passportBox.style.display = 'none';
                        otherIdBox.style.display = 'none';
                        
                        // Show the appropriate field
                        if (selectedValue === 'ID') {
                            idNumberBox.style.display = 'block';
                        } else if (selectedValue === 'PP') {
                            passportBox.style.display = 'block';
                        } else if (selectedValue === 'OT') {
                            otherIdBox.style.display = 'block';
                        }
                    }
                    
                    // Initial state
                    updateIdFields();
                    
                    // Add change listener
                    idTypeSelect.addEventListener('change', updateIdFields);
                    
                    // Dynamic geographic fields based on role
                    const roleSelect = document.getElementById('id_role');
                    const geoSection = document.getElementById('geographic-section');
                    
                    function updateGeoFields() {
                        const role = roleSelect.value;
                        
                        if (role === 'ADMIN_NATIONAL') {
                            geoSection.style.display = 'none';
                        } else {
                            geoSection.style.display = 'block';
                        }
                    }
                    
                    // Initial state
                    updateGeoFields();
                    
                    // Add change listener
                    roleSelect.addEventListener('change', updateGeoFields);
                    
                    // Organization type handling - add data attributes to options first
                    const orgTypeSelect = document.getElementById('id_organization_type');
                    // Add data-level attribute to each option
                    Array.from(orgTypeSelect.options).forEach(option => {
                        if (option.value) {
                            const text = option.text;
                            if (text.includes('National')) option.setAttribute('data-level', 'NATIONAL');
                            else if (text.includes('Province')) option.setAttribute('data-level', 'PROVINCE');
                            else if (text.includes('Region')) option.setAttribute('data-level', 'REGION');
                            else if (text.includes('Local') || text.includes('LFA')) option.setAttribute('data-level', 'LFA');
                            else if (text.includes('Club')) option.setAttribute('data-level', 'CLUB');
                        }
                    });
                    
                    // Get all organization field containers
                    const nationalFederationContainer = document.getElementById('national-federation-container');
                    const provinceContainer = document.getElementById('province-container');
                    const regionContainer = document.getElementById('region-container');
                    const lfaContainer = document.getElementById('lfa-container');
                    const clubContainer = document.getElementById('club-container');
                    
                    // Function to update visible organization fields
                    function updateOrgFields() {
                        // Get selected organization type level
                        const selectedOption = orgTypeSelect.options[orgTypeSelect.selectedIndex];
                        const orgLevel = selectedOption.getAttribute('data-level');
                        
                        // Hide all organization fields first
                        document.querySelectorAll('.org-field').forEach(field => {
                            field.style.display = 'none';
                        });
                        
                        // Show relevant fields based on organization type
                        switch(orgLevel) {
                            case 'NATIONAL':
                                nationalFederationContainer.style.display = 'flex';
                                break;
                            case 'PROVINCE':
                                provinceContainer.style.display = 'flex';
                                break;
                            case 'REGION':
                                provinceContainer.style.display = 'flex';
                                regionContainer.style.display = 'flex';
                                break;
                            case 'LFA':
                                provinceContainer.style.display = 'flex';
                                regionContainer.style.display = 'flex';
                                lfaContainer.style.display = 'flex';
                                break;
                            case 'CLUB':
                                provinceContainer.style.display = 'flex';
                                regionContainer.style.display = 'flex';
                                lfaContainer.style.display = 'flex';
                                clubContainer.style.display = 'flex';
                                break;
                        }
                    }
                    
                    // Set initial state
                    updateOrgFields();
                    
                    // Add change listeners
                    orgTypeSelect.addEventListener('change', updateOrgFields);
                });
            </script>
            '''),
        )
    
    def clean(self):
        cleaned_data = super().clean()
        # All custom validation removed as requested
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        role = self.cleaned_data['role']
        user.role = role

        org_type = self.cleaned_data.get('organization_type')
        # Clear all org fields first
        user.national_federation = None
        user.province = None
        user.region = None
        user.local_federation = None
        user.club = None

        if org_type:
            level = org_type.level
            # Assign only the relevant organization field(s) based on org type level
            if level == 'NATIONAL':
                user.national_federation = self.cleaned_data.get('national_federation')
            elif level == 'PROVINCE':
                user.province = self.cleaned_data.get('province')
            elif level == 'REGION':
                user.region = self.cleaned_data.get('region')
                user.province = self.cleaned_data.get('province')
            elif level == 'LFA':
                user.local_federation = self.cleaned_data.get('local_federation')
                user.region = self.cleaned_data.get('region')
                user.province = self.cleaned_data.get('province')
            elif level == 'CLUB':
                user.club = self.cleaned_data.get('club')
                user.local_federation = self.cleaned_data.get('local_federation')
                user.region = self.cleaned_data.get('region')
                user.province = self.cleaned_data.get('province')

        # If a club admin is registering a player, inherit club info
        admin_user = self.initial.get('admin_user')
        if admin_user and role == 'PLAYER':
            user.club = admin_user.club
            user.province = admin_user.province
            user.region = admin_user.region
            user.local_federation = admin_user.local_federation
            user.national_federation = admin_user.national_federation

        # Only set region if present in cleaned_data
        if self.cleaned_data.get('region'):
            user.region = self.cleaned_data.get('region')
            print(f"[DEBUG] Assigned region: {user.region} (pk={getattr(user.region, 'pk', None)})")
        else:
            print("[DEBUG] No region assigned in form data!")
        if self.cleaned_data.get('province'):
            user.province = self.cleaned_data.get('province')
        if self.cleaned_data.get('local_federation'):
            user.local_federation = self.cleaned_data.get('local_federation')
        if self.cleaned_data.get('club'):
            user.club = self.cleaned_data.get('club')

        if role in ['ADMIN_NATIONAL', 'ADMIN_PROVINCE', 'ADMIN_REGION', 'ADMIN_LOCAL_FED', 'CLUB_ADMIN']:
            user.is_staff = True
        user.country_code = 'ZAF'
        user.nationality = 'South African'
        user.popi_act_consent = self.cleaned_data.get('popi_act_consent')
        if commit:
            user.save()
            print(f"[DEBUG] User saved with region: {user.region} (pk={getattr(user.region, 'pk', None)})")
        return user

# Create alias for backward compatibility 
NationalUserRegistrationForm = UniversalRegistrationForm