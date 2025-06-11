import datetime
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset, Div, HTML, ButtonHolder, Submit
from django.db.models.query import EmptyQuerySet as DjangoEmptyQuerySet
from django.utils.translation import gettext_lazy as _

# Import models with proper error handling
from .models import CustomUser, EMPLOYMENT_STATUS, Position
from geography.models import Province, Region, LocalFootballAssociation, Club  # Add missing imports

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
    
    # Add POPI Act consent field
    popi_act_consent = forms.BooleanField(
        required=True,
        label="I agree to the POPI Act terms and conditions",
        help_text="You must agree to the Protection of Personal Information Act terms to register."
    )

    # Nationality field
    nationality = forms.CharField(
        max_length=50,
        initial='South African',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # Fix the LocalFederation reference
    if LocalFootballAssociation is not None:  # Changed from LocalFederation to LocalFootballAssociation
        local_federation = forms.ModelChoiceField(
            queryset=LocalFootballAssociation.objects.all(),
            required=False,
            label=_("Local Football Association"),
            widget=forms.Select(attrs={'class': 'form-select'}),
        )
    else:
        local_federation = forms.ChoiceField(
            choices=[],
            required=False,
            label=_("Local Football Association"),
            widget=forms.Select(attrs={'class': 'form-select'}),
        )

    # Also fix other geography-related model fields
    if Province is not None:
        province = forms.ModelChoiceField(
            queryset=Province.objects.all(),
            required=False,
            label=_("Province"),
            widget=forms.Select(attrs={'class': 'form-select'}),
        )
    else:
        province = forms.ChoiceField(
            choices=[],
            required=False,
            label=_("Province"),
            widget=forms.Select(attrs={'class': 'form-select'}),
        )
        
    region = forms.ModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        label=_("Region"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = (
            'email', 'name', 'middle_name', 'surname', 'alias', 'date_of_birth', 'gender', 'role',
            'id_number', 'id_number_other', 'passport_number', 'id_document_type',
            'phone_number', 'address', 'city', 'postal_code', 'country', 'profile_photo', 
            'id_document', 'password1', 'password2', 'province', 'region', 'local_federation',
            'popi_act_consent', 'nationality'  # Add the new field
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
                    Div(
                        HTML('<div id="registration_error" class="alert alert-danger" style="display:none;"></div>'),
                        css_class='col-md-6'
                    ),
                    css_class='row mb-3'
                ),
            ),
            
            Fieldset(
                'Identification',
                Div(
                    Div(Field('id_document_type', css_id='id_id_document_type'), css_class='col-md-4'),
                    
                    # ID Number field and related fields
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
                    
                    # Other ID field (initially hidden)
                    Div(
                        Field('id_number_other', css_id='id_id_number_other'),
                        css_class='col-md-4',
                        css_id='id_number_other_box',
                        style='display:none;'
                    ),
                    
                    # Passport field (initially hidden)
                    Div(
                        Field('passport_number', css_id='id_passport_number'),
                        css_class='col-md-4',
                        css_id='passport_box',
                        style='display:none;'  # Start hidden by default
                    ),
                    
                    # Document upload field
                    Div(
                        Field('id_document', css_id='id_id_document'),
                        css_class='col-md-4',
                        css_id='document_box'
                    ),
                    
                    # Add JavaScript to control field visibility
                    HTML('''
                    <script>
                        document.addEventListener('DOMContentLoaded', function() {
                            const idTypeSelect = document.getElementById('id_id_document_type');
                            const idNumberBox = document.getElementById('id_number_box');
                            const idNumberOtherBox = document.getElementById('id_number_other_box');
                            const passportBox = document.getElementById('passport_box');
                            
                            function updateFields() {
                                const selectedValue = idTypeSelect.value;
                                
                                // Hide all fields first
                                idNumberBox.style.display = 'none';
                                idNumberOtherBox.style.display = 'none';
                                passportBox.style.display = 'none';
                                
                                // Show the appropriate field based on selection
                                if (selectedValue === 'ID') {
                                    idNumberBox.style.display = 'block';
                                } else if (selectedValue === 'PASSPORT') {
                                    passportBox.style.display = 'block';
                                } else if (selectedValue === 'OTHER') {
                                    idNumberOtherBox.style.display = 'block';
                                }
                            }
                            
                            // Set initial state
                            updateFields();
                            
                            // Add change listener
                            idTypeSelect.addEventListener('change', updateFields);
                            
                            // Show registration error if present
                            const urlParams = new URLSearchParams(window.location.search);
                            const error = urlParams.get('error');
                            if (error) {
                                const errorDiv = document.getElementById('registration_error');
                                errorDiv.textContent = decodeURIComponent(error);
                                errorDiv.style.display = 'block';
                            }
                        });
                    </script>
                    '''),
                    
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
            
            # Add POPI Act consent field before the register button
            Fieldset(
                'Legal Compliance',
                Div(
                    Field('popi_act_consent', css_class='form-check-input'),
                    HTML('<div class="mt-2"><small class="text-muted">By checking this box, you consent to the collection, processing, and storage of your personal information in accordance with the Protection of Personal Information Act (POPI Act). <a href="#" data-bs-toggle="modal" data-bs-target="#popiModal">Read full terms</a></small></div>'),
                    css_class='form-check'
                ),
            ),
            
            # Register button
            Div(
                ButtonHolder(
                    Submit('submit', 'Register', css_class='btn btn-dark')
                ),
                css_class='d-grid gap-2 mt-4'
            ),
            
            # Add POPI Modal
            HTML('''
            <div class="modal fade" id="popiModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">POPI Act Terms and Conditions</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>Your personal information will be processed in accordance with the Protection of Personal Information Act (POPI Act) of South Africa.</p>
                            <p>We collect and process your information for the following purposes:</p>
                            <ul>
                                <li>User registration and account management</li>
                                <li>Communication regarding football administration</li>
                                <li>Compliance with sports federation requirements</li>
                            </ul>
                            <p>Your information will be kept secure and will not be shared with third parties without your consent, except as required by law.</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
            '''),
            
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
        
        # Validate POPI Act consent
        if not cleaned_data.get('popi_act_consent'):
            self.add_error('popi_act_consent', 'You must agree to the POPI Act terms to register.')
        
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

class ProvinceUserRegistrationForm(forms.ModelForm):
    """Standardized Province form based on National form"""
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    employment_status = forms.ChoiceField(
        choices=EMPLOYMENT_STATUS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your status within SAFA structure"
    )
    position = forms.ModelChoiceField(
        queryset=Position.objects.filter(level='PROVINCE', is_active=True).order_by('title'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your position within Province structure",
        empty_label="Select Position (Optional)"
    )
    province = forms.ModelChoiceField(
        queryset=Province.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the province you will administer"
    )
    id_document_type = forms.ChoiceField(
        choices=[
            ('ID', 'South African ID'),
            ('BC', 'Birth Certificate'),
            ('PP', 'Passport'),
            ('DL', 'Driver License'),
            ('OT', 'Other')
        ],
        initial='ID',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your document type"
    )
    id_number = forms.CharField(
        max_length=13,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 13-digit ID number',
            'id': 'id_province_id_number'
        }),
        help_text="13-digit South African ID number"
    )
    passport_number = forms.CharField(
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter passport number'
        }),
        help_text="Passport number"
    )
    driver_license_number = forms.CharField(
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter driver license number'
        }),
        help_text="Driver license number"
    )
    id_number_other = forms.CharField(
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter other document number'
        }),
        help_text="Other document number"
    )
    popi_act_consent = forms.BooleanField(
        required=True,
        label="I consent to POPI Act terms",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    profile_photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text="Upload profile photo (optional)"
    )
    
    id_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        help_text="Upload ID document (PDF, JPG, PNG)"
    )
    
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'employment_status', 'position', 'province', 'profile_photo', 'id_document_type', 'id_number', 'passport_number', 'driver_license_number', 'id_number_other', 'id_document', 'popi_act_consent', 'password1', 'password2']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.role = 'ADMIN_PROVINCE'
        user.employment_status = self.cleaned_data['employment_status']
        user.position = self.cleaned_data.get('position')
        user.popi_act_consent = self.cleaned_data['popi_act_consent']
        user.is_staff = True
        
        # CRITICAL FIX: Save the province_id
        if self.cleaned_data.get('province'):
            user.province_id = self.cleaned_data['province'].id
        
        # Save all document numbers
        if self.cleaned_data.get('passport_number'):
            user.passport_number = self.cleaned_data['passport_number']
        if self.cleaned_data.get('driver_license_number'):
            user.driver_license_number = self.cleaned_data['driver_license_number']
        if self.cleaned_data.get('id_number_other'):
            user.id_number_other = self.cleaned_data['id_number_other']
        
        if commit:
            user.save()
        return user

class ClubUserRegistrationForm(forms.ModelForm):
    """Registration form for club-level users with Province → Region → LFA → Club hierarchy"""
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    employment_status = forms.ChoiceField(
        choices=EMPLOYMENT_STATUS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your status within SAFA structure"
    )
    position = forms.ModelChoiceField(
        queryset=Position.objects.filter(level='CLUB', is_active=True).order_by('title'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your position within Club structure",
        empty_label="Select Position (Optional)"
    )
    province = forms.ModelChoiceField(
        queryset=Province.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the province where club is located"
    )
    region = forms.ModelChoiceField(
        queryset=Region.objects.none(),  # Start empty
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the region (populated based on province)"
    )
    local_federation = forms.ModelChoiceField(
        queryset=LocalFootballAssociation.objects.none(),  # Start empty
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the LFA (populated based on region)"
    )
    club = forms.ModelChoiceField(
        queryset=Club.objects.none(),  # Start empty
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the club you represent"
    )
    id_document_type = forms.ChoiceField(
        choices=[
            ('ID', 'South African ID'),
            ('BC', 'Birth Certificate'),
            ('PP', 'Passport'),
            ('DL', 'Driver License'),
            ('OT', 'Other')
        ],
        initial='ID',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your document type"
    )
    id_number = forms.CharField(
        max_length=13,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 13-digit ID number',
            'id': 'id_club_id_number'
        }),
        help_text="13-digit South African ID number"
    )
    passport_number = forms.CharField(
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter passport number'
        }),
        help_text="Passport number"
    )
    driver_license_number = forms.CharField(
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter driver license number'
        }),
        help_text="Driver license number"
    )
    id_number_other = forms.CharField(
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter other document number'
        }),
        help_text="Other document number"
    )
    popi_act_consent = forms.BooleanField(
        required=True,
        label="I consent to POPI Act terms",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    profile_photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text="Upload profile photo (optional)"
    )
    
    id_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        help_text="Upload ID document (PDF, JPG, PNG)"
    )
    
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'employment_status', 'position', 'province', 'region', 'local_federation', 'club', 'profile_photo', 'id_document_type', 'id_number', 'passport_number', 'driver_license_number', 'id_number_other', 'id_document', 'popi_act_consent', 'password1', 'password2']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Handle dynamic population during form submission
        if self.data:
            try:
                province_id = int(self.data.get('province'))
                self.fields['region'].queryset = Region.objects.filter(province=province_id)
            except (ValueError, TypeError):
                pass
            
            try:
                region_id = int(self.data.get('region'))
                self.fields['local_federation'].queryset = LocalFootballAssociation.objects.filter(region=region_id)
            except (ValueError, TypeError):
                pass
                
            try:
                lfa_id = int(self.data.get('local_federation'))
                self.fields['club'].queryset = Club.objects.filter(localfootballassociation=lfa_id, status='ACTIVE')
            except (ValueError, TypeError):
                pass
    
    def clean_region(self):
        region = self.cleaned_data.get('region')
        province = self.cleaned_data.get('province')
        
        if region and province:
            if region.province != province:
                raise forms.ValidationError("Selected region does not belong to the selected province.")
        return region
    
    def clean_local_federation(self):
        local_federation = self.cleaned_data.get('local_federation')
        region = self.cleaned_data.get('region')
        
        if local_federation and region:
            if local_federation.region != region:
                raise forms.ValidationError("Selected LFA does not belong to the selected region.")
        return local_federation
    
    def clean_club(self):
        club = self.cleaned_data.get('club')
        local_federation = self.cleaned_data.get('local_federation')
        
        if club and local_federation:
            if club.localfootballassociation != local_federation:
                raise forms.ValidationError("Selected club does not belong to the selected LFA.")
        return club
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.role = 'CLUB_ADMIN'
        user.employment_status = self.cleaned_data['employment_status']
        user.position = self.cleaned_data.get('position')
        user.popi_act_consent = self.cleaned_data['popi_act_consent']
        user.is_staff = True
        
        # Save all hierarchy IDs
        if self.cleaned_data.get('province'):
            user.province_id = self.cleaned_data['province'].id
        if self.cleaned_data.get('region'):
            user.region_id = self.cleaned_data['region'].id
        if self.cleaned_data.get('local_federation'):
            user.local_federation_id = self.cleaned_data['local_federation'].id
        if self.cleaned_data.get('club'):
            user.club_id = self.cleaned_data['club'].id
        
        # Save document numbers
        if self.cleaned_data.get('passport_number'):
            user.passport_number = self.cleaned_data['passport_number']
        if self.cleaned_data.get('driver_license_number'):
            user.driver_license_number = self.cleaned_data['driver_license_number']
        if self.cleaned_data.get('id_number_other'):
            user.id_number_other = self.cleaned_data['id_number_other']
        
        if commit:
            user.save()
        return user

class EmailAuthenticationForm(AuthenticationForm):
    """Custom authentication form that uses email instead of username"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Change the username field to email
        self.fields['username'].label = 'Email'
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'type': 'email'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Convert email to lowercase for consistency
            return username.lower()
        return username

class NationalUserRegistrationForm(forms.ModelForm):
    """Step 6 - Add position dropdown and separate document fields"""
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    employment_status = forms.ChoiceField(
        choices=EMPLOYMENT_STATUS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your status within SAFA structure"
    )
    id_document_type = forms.ChoiceField(
        choices=[
            ('ID', 'South African ID'),
            ('BC', 'Birth Certificate'),
            ('PP', 'Passport'),
            ('DL', 'Driver License'),
            ('OT', 'Other')
        ],
        initial='ID',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your document type"
    )
    id_number = forms.CharField(
        max_length=13,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 13-digit ID number',
            'id': 'id_national_id_number'
        }),
        help_text="13-digit South African ID number (optional)"
    )
    # Fix hidden fields for passport and other documents - remove inline display:none
    passport_number = forms.CharField(
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter passport number'
        }),
        help_text="Passport number"
    )
    id_number_other = forms.CharField(
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter document number'
        }),
        help_text="Document number for driver license or other documents"
    )
    popi_act_consent = forms.BooleanField(
        required=True,
        label="I consent to POPI Act terms",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    position = forms.ModelChoiceField(
        queryset=Position.objects.filter(level='NATIONAL', is_active=True).order_by('title'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your position within SAFA National structure",
        empty_label="Select Position (Optional)"
    )
    
    profile_photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text="Upload profile photo (optional)"
    )
    
    id_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        help_text="Upload ID document (PDF, JPG, PNG)"
    )
    
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'employment_status', 'position', 'profile_photo', 'id_document_type', 'id_number', 'passport_number', 'driver_license_number', 'id_number_other', 'id_document', 'popi_act_consent', 'password1', 'password2']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.role = 'ADMIN_NATIONAL'
        user.employment_status = self.cleaned_data['employment_status']
        user.id_document_type = self.cleaned_data['id_document_type']
        user.popi_act_consent = self.cleaned_data['popi_act_consent']
        user.position = self.cleaned_data.get('position')
        user.is_staff = True
        
        # Save all document numbers
        if self.cleaned_data.get('passport_number'):
            user.passport_number = self.cleaned_data['passport_number']
        if self.cleaned_data.get('driver_license_number'):
            user.driver_license_number = self.cleaned_data['driver_license_number']
        if self.cleaned_data.get('id_number_other'):
            user.id_number_other = self.cleaned_data['id_number_other']
        
        if commit:
            user.save()
        return user

class SupporterRegistrationForm(forms.ModelForm):
    """Registration form for supporters/public - SAFA Support only"""
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    id_number = forms.CharField(
        max_length=13,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 13-digit ID number',
        }),
        help_text="13-digit South African ID number (optional)"
    )
    popi_act_consent = forms.BooleanField(
        required=True,
        label="I consent to the processing of my personal information in accordance with the Protection of Personal Information Act (POPI Act)",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'id_number', 'popi_act_consent']  # Removed supporting_club
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.role = 'SUPPORTER'
        user.employment_status = 'PUBLIC'
        if commit:
            user.save()
        return user

class LFAUserRegistrationForm(forms.ModelForm):
    """Standardized LFA form with Province → Region → LFA hierarchy"""
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    employment_status = forms.ChoiceField(
        choices=EMPLOYMENT_STATUS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your status within SAFA structure"
    )
    position = forms.ModelChoiceField(
        queryset=Position.objects.filter(level='LFA', is_active=True).order_by('title'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your position within LFA structure",
        empty_label="Select Position (Optional)"
    )
    province = forms.ModelChoiceField(
        queryset=Province.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the province where LFA is located"
    )
    
    region = forms.ModelChoiceField(
        queryset=Region.objects.none(),  # Start empty, will be populated by JavaScript
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the region (populated based on province)"
    )
    
    local_federation = forms.ModelChoiceField(
        queryset=LocalFootballAssociation.objects.none(),  # Start empty
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the LFA you will administer"
    )
    
    id_document_type = forms.ChoiceField(
        choices=[
            ('ID', 'South African ID'),
            ('BC', 'Birth Certificate'),
            ('PP', 'Passport'),
            ('DL', 'Driver License'),
            ('OT', 'Other')
        ],
        initial='ID',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your document type"
    )
    id_number = forms.CharField(
        max_length=13,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 13-digit ID number',
            'id': 'id_lfa_id_number'
        }),
        help_text="13-digit South African ID number"
    )
    passport_number = forms.CharField(
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter passport number'
        }),
        help_text="Passport number"
    )
    driver_license_number = forms.CharField(
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter driver license number'
        }),
        help_text="Driver license number"
    )
    id_number_other = forms.CharField(
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter other document number'
        }),
        help_text="Other document number"
    )
    popi_act_consent = forms.BooleanField(
        required=True,
        label="I consent to POPI Act terms",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    profile_photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text="Upload profile photo (optional)"
    )
    
    id_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        help_text="Upload ID document (PDF, JPG, PNG)"
    )
    
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'employment_status', 'position', 'province', 'region', 'local_federation', 'profile_photo', 'id_document_type', 'id_number', 'passport_number', 'driver_license_number', 'id_number_other', 'id_document', 'popi_act_consent', 'password1', 'password2']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Handle dynamic population during form submission
        if self.data:
            try:
                province_id = int(self.data.get('province'))
                self.fields['region'].queryset = Region.objects.filter(province=province_id)
            except (ValueError, TypeError):
                pass
            
            try:
                region_id = int(self.data.get('region'))
                self.fields['local_federation'].queryset = LocalFootballAssociation.objects.filter(region=region_id)
            except (ValueError, TypeError):
                pass
    
    def clean_region(self):
        region = self.cleaned_data.get('region')
        province = self.cleaned_data.get('province')
        
        if region and province:
            # Verify that the region belongs to the selected province
            if region.province != province:
                raise forms.ValidationError("Selected region does not belong to the selected province.")
        
        return region
    
    def clean_local_federation(self):
        local_federation = self.cleaned_data.get('local_federation')
        region = self.cleaned_data.get('region')
        
        if local_federation and region:
            # Verify that the LFA belongs to the selected region
            if local_federation.region != region:
                raise forms.ValidationError("Selected LFA does not belong to the selected region.")
        
        return local_federation
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.role = 'ADMIN_LOCAL_FED'
        user.employment_status = self.cleaned_data['employment_status']
        user.position = self.cleaned_data.get('position')
        user.popi_act_consent = self.cleaned_data['popi_act_consent']
        user.is_staff = True
        
        # Save province_id, region_id, and local_federation_id
        if self.cleaned_data.get('province'):
            user.province_id = self.cleaned_data['province'].id
        if self.cleaned_data.get('region'):
            user.region_id = self.cleaned_data['region'].id
        if self.cleaned_data.get('local_federation'):
            user.local_federation_id = self.cleaned_data['local_federation'].id
        
        # Save all document numbers
        if self.cleaned_data.get('passport_number'):
            user.passport_number = self.cleaned_data['passport_number']
        if self.cleaned_data.get('driver_license_number'):
            user.driver_license_number = self.cleaned_data['driver_license_number']
        if self.cleaned_data.get('id_number_other'):
            user.id_number_other = self.cleaned_data['id_number_other']
        
        if commit:
            user.save()
        return user

class ClubUserRegistrationForm(forms.ModelForm):
    """Registration form for club-level users with Province → Region → LFA → Club hierarchy"""
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    employment_status = forms.ChoiceField(
        choices=EMPLOYMENT_STATUS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your status within SAFA structure"
    )
    position = forms.ModelChoiceField(
        queryset=Position.objects.filter(level='CLUB', is_active=True).order_by('title'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your position within Club structure",
        empty_label="Select Position (Optional)"
    )
    province = forms.ModelChoiceField(
        queryset=Province.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the province where club is located"
    )
    region = forms.ModelChoiceField(
        queryset=Region.objects.none(),  # Start empty
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the region (populated based on province)"
    )
    local_federation = forms.ModelChoiceField(
        queryset=LocalFootballAssociation.objects.none(),  # Start empty
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the LFA (populated based on region)"
    )
    club = forms.ModelChoiceField(
        queryset=Club.objects.none(),  # Start empty
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the club you represent"
    )
    id_document_type = forms.ChoiceField(
        choices=[
            ('ID', 'South African ID'),
            ('BC', 'Birth Certificate'),
            ('PP', 'Passport'),
            ('DL', 'Driver License'),
            ('OT', 'Other')
        ],
        initial='ID',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your document type"
    )
    id_number = forms.CharField(
        max_length=13,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 13-digit ID number',
            'id': 'id_club_id_number'
        }),
        help_text="13-digit South African ID number"
    )
    passport_number = forms.CharField(
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter passport number'
        }),
        help_text="Passport number"
    )
    driver_license_number = forms.CharField(
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter driver license number'
        }),
        help_text="Driver license number"
    )
    id_number_other = forms.CharField(
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter other document number'
        }),
        help_text="Other document number"
    )
    popi_act_consent = forms.BooleanField(
        required=True,
        label="I consent to POPI Act terms",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    profile_photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text="Upload profile photo (optional)"
    )
    
    id_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        help_text="Upload ID document (PDF, JPG, PNG)"
    )
    
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'employment_status', 'position', 'province', 'region', 'local_federation', 'club', 'profile_photo', 'id_document_type', 'id_number', 'passport_number', 'driver_license_number', 'id_number_other', 'id_document', 'popi_act_consent', 'password1', 'password2']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Handle dynamic population during form submission
        if self.data:
            try:
                province_id = int(self.data.get('province'))
                self.fields['region'].queryset = Region.objects.filter(province=province_id)
            except (ValueError, TypeError):
                pass
            
            try:
                region_id = int(self.data.get('region'))
                self.fields['local_federation'].queryset = LocalFootballAssociation.objects.filter(region=region_id)
            except (ValueError, TypeError):
                pass
                
            try:
                lfa_id = int(self.data.get('local_federation'))
                self.fields['club'].queryset = Club.objects.filter(localfootballassociation=lfa_id, status='ACTIVE')
            except (ValueError, TypeError):
                pass
    
    def clean_region(self):
        region = self.cleaned_data.get('region')
        province = self.cleaned_data.get('province')
        
        if region and province:
            if region.province != province:
                raise forms.ValidationError("Selected region does not belong to the selected province.")
        return region
    
    def clean_local_federation(self):
        local_federation = self.cleaned_data.get('local_federation')
        region = self.cleaned_data.get('region')
        
        if local_federation and region:
            if local_federation.region != region:
                raise forms.ValidationError("Selected LFA does not belong to the selected region.")
        return local_federation
    
    def clean_club(self):
        club = self.cleaned_data.get('club')
        local_federation = self.cleaned_data.get('local_federation')
        
        if club and local_federation:
            if club.localfootballassociation != local_federation:
                raise forms.ValidationError("Selected club does not belong to the selected LFA.")
        return club
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.role = 'CLUB_ADMIN'
        user.employment_status = self.cleaned_data['employment_status']
        user.position = self.cleaned_data.get('position')
        user.popi_act_consent = self.cleaned_data['popi_act_consent']
        user.is_staff = True
        
        # Save all hierarchy IDs
        if self.cleaned_data.get('province'):
            user.province_id = self.cleaned_data['province'].id
        if self.cleaned_data.get('region'):
            user.region_id = self.cleaned_data['region'].id
        if self.cleaned_data.get('local_federation'):
            user.local_federation_id = self.cleaned_data['local_federation'].id
        if self.cleaned_data.get('club'):
            user.club_id = self.cleaned_data['club'].id
        
        # Save document numbers
        if self.cleaned_data.get('passport_number'):
            user.passport_number = self.cleaned_data['passport_number']
        if self.cleaned_data.get('driver_license_number'):
            user.driver_license_number = self.cleaned_data['driver_license_number']
        if self.cleaned_data.get('id_number_other'):
            user.id_number_other = self.cleaned_data['id_number_other']
        
        if commit:
            user.save()
        return user