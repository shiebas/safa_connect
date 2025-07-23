import os
import datetime
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django.forms import ValidationError
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Field, HTML, ButtonHolder, Submit
from .models import CustomUser, EMPLOYMENT_STATUS, Position, OrganizationType
from geography.models import Province, Region, LocalFootballAssociation, Club, NationalFederation
from membership.models import Player, Official, OfficialCertification
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
            ('ADMIN_NATIONAL', 'SAFA System Administrator'),
            ('ADMIN_NATIONAL_ACCOUNTS', 'National Accounts Administrator'), # Added this line
            ('ASSOCIATION_ADMIN', 'Referee Association Administrator'),
            ('CLUB_ADMIN', 'Club Administrator'),
            ('ADMIN_LOCAL_FED', 'Local Football Association Administrator'),
            ('ADMIN_REGION', 'Region Administrator'),
            ('ADMIN_PROVINCE', 'Province Administrator')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Identity fields
    id_document_type = forms.ChoiceField(
        choices=[('ID', 'SA ID'), ('PP', 'Passport'), ('OT', 'Other')],
        initial='ID',
        widget=forms.Select(attrs={'class': 'form-select'})
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
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')], required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    
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
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select your primary organization type"
    )
    
    safa_id = forms.CharField(
        max_length=5, 
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Auto-generated if left blank'
        }),
        help_text="SAFA ID (auto-generated if left blank)"
    )

    positions = forms.ModelMultipleChoiceField(
        queryset=Position.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select all positions held within SAFA structure"
    )

    class Meta:
        model = CustomUser
        fields = [
            'email', 'first_name', 'last_name', 'role', 
            'organization_type', 
            'province', 'region', 'local_federation', 'club', 'association',
            'id_document_type', 'id_number', 'passport_number', 'id_number_other',
            'date_of_birth', 'gender', 'id_document', 'profile_photo', 
            'popi_act_consent', 'national_federation', 'mother_body', 'age', 'safa_id', 'fifa_id'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, registration_type=None, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'age'):
            self.fields['age'].initial = self.instance.age
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        
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

        # Set default role based on registration type
        if registration_type == 'national':
            self.initial['role'] = 'ADMIN_NATIONAL'
            self.fields['role'].widget = forms.HiddenInput()
            
            # Set default SAFA Referee Association for National admins
            try:
                from geography.models import Association
                safa_referee_association, _ = Association.objects.get_or_create(
                    name="SAFA Referees Association",
                    defaults={
                        'acronym': "SRA",
                        'national_federation': safa_federation
                    }
                )
                self.initial['association'] = safa_referee_association.id
            except Exception:
                pass
        
        # Add association field to all forms - Simple implementation with debug
        from geography.models import Association
        associations = Association.objects.all()
        print(f"[DEBUG - REFEREE REG] Available associations: {[a.name for a in associations]}")
        
        self.fields['association'] = forms.ModelChoiceField(
            queryset=Association.objects.all(),
            required=False,
            widget=forms.Select(attrs={'class': 'form-select'}),
            help_text="Select the referee association for this official"
        )
        
        # Set association required for referee-related roles
        if self.data.get('role') == 'ASSOCIATION_ADMIN' or self.initial.get('role') == 'ASSOCIATION_ADMIN':
            self.fields['association'].required = True
            print("[DEBUG - REFEREE REG] Association field set to required for ASSOCIATION_ADMIN")
            
            # For referee association admins, we shouldn't require club data
            self.fields['club'].required = False
            self.fields['organization_type'].required = False
            
        print("[DEBUG - REFEREE REG] Association field added to form")

        # Add region and local_federation fields dynamically
        self.fields['safa_id'].help_text = "SAFA ID (auto-generated if left blank)"
        self.fields['safa_id'].widget.attrs.update({
            'pattern': '[A-Z0-9]{5}',
            'title': '5-character alphanumeric code (all caps)',
            'placeholder': 'e.g. A12B3'
        })

        self.fields['fifa_id'].required = False
        self.fields['fifa_id'].help_text = "If the player has a FIFA ID, enter it here. Otherwise, leave blank."
        self.fields['fifa_id'].widget.attrs.update({
            'pattern': '[0-9]{7}',
            'title': '7-digit FIFA identification number',
            'placeholder': 'e.g. 1234567'
        })

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

        # Filter local_federation queryset by selected region
        region_id = self.data.get('region') or self.initial.get('region')
        if region_id:
            try:
                self.fields['local_federation'].queryset = LocalFootballAssociation.objects.filter(region_id=region_id)
            except (ValueError, TypeError):
                self.fields['local_federation'].queryset = LocalFootballAssociation.objects.none()
        else:
            self.fields['local_federation'].queryset = LocalFootballAssociation.objects.none()
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
        
        

    def clean_id_number(self):
        """Validate that the ID number is unique"""
        id_number = self.cleaned_data.get('id_number')
        id_document_type = self.cleaned_data.get('id_document_type')
        
        # Only validate if ID is the selected document type and a number is provided
        if id_document_type == 'ID' and id_number:
            # Check if ID is valid (13 digits for South African ID)
            if not id_number.isdigit() or len(id_number) != 13:
                raise forms.ValidationError("South African ID number must be 13 digits.")
                
            # Check if ID already exists
            if CustomUser.objects.filter(id_number=id_number).exists():
                raise forms.ValidationError("This ID number is already registered in the system.")
        
        return id_number

    def clean_passport_number(self):
        """Validate that the passport number is unique"""
        passport_number = self.cleaned_data.get('passport_number')
        id_document_type = self.cleaned_data.get('id_document_type')
        
        # Only validate if Passport is the selected document type and a number is provided
        if id_document_type == 'PP' and passport_number:
            # Check if passport number already exists
            if CustomUser.objects.filter(passport_number=passport_number).exists():
                raise forms.ValidationError("This passport number is already registered in the system.")
        
        return passport_number

    def clean(self):
        print("[DEBUG - REFEREE REG] Starting form validation (clean method)")
        cleaned_data = super().clean()
        
        # Print all form data for debugging
        print(f"[DEBUG - REFEREE REG] Form data before validation: {self.data}")
        print(f"[DEBUG - REFEREE REG] Role value in POST data: {self.data.get('role')}")
        print(f"[DEBUG - REFEREE REG] All form fields: {list(self.fields.keys())}")
        print(f"[DEBUG - REFEREE REG] Required fields: {[field for field, field_obj in self.fields.items() if field_obj.required]}")
        
        # If role is ASSOCIATION_ADMIN, make association required and make organization_type not required
        role = cleaned_data.get('role') or self.data.get('role')
        if role == 'ASSOCIATION_ADMIN':
            print("[DEBUG - REFEREE REG] Role is ASSOCIATION_ADMIN, adjusting requirements")
            
            # For referee association admins
            self.fields['association'].required = True
            self.fields['organization_type'].required = False
            
            # Remove any errors for organization_type since it's not required for this role
            if 'organization_type' in self._errors:
                del self._errors['organization_type']
                
            # Make sure the association field is validated
            if not cleaned_data.get('association'):
                self.add_error('association', 'Association is required for Referee Association Administrators')
                
            print(f"[DEBUG - REFEREE REG] After adjustment - Required fields: {[field for field, field_obj in self.fields.items() if field_obj.required]}")
        
        # Document type validation
        id_document_type = cleaned_data.get('id_document_type')
        id_number = cleaned_data.get('id_number')
        passport_number = cleaned_data.get('passport_number')
        
        if id_document_type == 'ID' and not id_number:
            self.add_error('id_number', 'SA ID Number is required when ID is selected as document type.')
        elif id_document_type == 'PP' and not passport_number:
            self.add_error('passport_number', 'Passport Number is required when Passport is selected as document type.')
        
        # Password confirmation validation
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')
        
        # Debug validation errors
        if self._errors:
            print(f"[DEBUG - REFEREE REG] Form validation errors: {self._errors}")
        else:
            print("[DEBUG - REFEREE REG] Form validation passed, no errors")
            
        # Debug association field
        if 'association' in cleaned_data:
            print(f"[DEBUG - REFEREE REG] Association in cleaned_data: {cleaned_data.get('association')}")
        else:
            print("[DEBUG - REFEREE REG] Association NOT in cleaned_data")
        
        return cleaned_data

    def save(self, commit=True):
        cleaned_data = self.cleaned_data
        print("[DEBUG - REFEREE REG] Starting form save method")
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if not self.cleaned_data.get("password1"):
            raise ValidationError(_("Password cannot be empty."))
        role = self.cleaned_data['role']
        user.role = role
        print(f"[DEBUG - REFEREE REG] User role set to: {role}")

        # Clear all org fields first
        user.national_federation = None
        user.province = None
        user.region = None
        user.local_federation = None
        user.club = None
        
        # Special handling for referee association admins
        if role == 'ASSOCIATION_ADMIN':
            # For referee association admins, we prioritize the association field
            # and don't populate club-related fields
            print("[DEBUG - REFEREE REG] Special handling for ASSOCIATION_ADMIN role")
            
            # Make sure organization type is properly set to ASSOCIATION level
            from .models import OrganizationType
            try:
                # Try to get an organization type with ASSOCIATION level
                association_type = OrganizationType.objects.filter(
                    level='ASSOCIATION'
                ).first()
                
                # If not found, create one
                if not association_type:
                    association_type = OrganizationType.objects.create(
                        name="Referee Association",
                        level="ASSOCIATION",
                        requires_approval=True,
                        is_active=True
                    )
                    print(f"[DEBUG - REFEREE REG] Created new organization type: {association_type}")
                
                user.organization_type = association_type
                print(f"[DEBUG - REFEREE REG] Set organization type to: {association_type}")
                
                # Try to set the association to SAFRA if no specific association is selected
                if not self.cleaned_data.get('association'):
                    try:
                        from geography.models import Association
                        # Try to get SAFRA with ID 11
                        safra = Association.objects.filter(id=11).first()
                        if safra:
                            print(f"[DEBUG - REFEREE REG] Found SAFRA: {safra.name} (ID: {safra.id})")
                            self.cleaned_data['association'] = safra
                            print(f"[DEBUG - REFEREE REG] Set association to SAFRA")
                    except Exception as e:
                        print(f"[DEBUG - REFEREE REG] Error setting SAFRA as association: {e}")
            except Exception as e:
                print(f"[DEBUG - REFEREE REG] Error setting organization type: {e}")
                
            # We can still set province and region if available, but they're secondary
            if self.cleaned_data.get('province'):
                user.province = self.cleaned_data.get('province')
                print(f"[DEBUG - REFEREE REG] Setting province: {user.province}")
                
            if self.cleaned_data.get('region'):
                user.region = self.cleaned_data.get('region')
                print(f"[DEBUG - REFEREE REG] Setting region: {user.region}")
                
            # Always set SAFA as national federation for referee association admins
            try:
                from geography.models import NationalFederation
                # Try to get SAFA by name (case insensitive)
                safa = NationalFederation.objects.filter(name__icontains='South African Football').first()
                if not safa:
                    # Fallback to getting the first national federation if available
                    safa = NationalFederation.objects.first()
                
                if safa:
                    user.national_federation = safa
                    print(f"[DEBUG - REFEREE REG] Setting national federation to: {safa}")
                else:
                    # Create SAFA if it doesn't exist
                    safa = NationalFederation.objects.create(
                        name="South African Football Association",
                        acronym="SAFA",
                        country_id=1  # Assuming South Africa has ID 1
                    )
                    user.national_federation = safa
                    print(f"[DEBUG - REFEREE REG] Created and set national federation to: {safa}")
            except Exception as e:
                print(f"[DEBUG - REFEREE REG] Error setting SAFA national federation: {e}")
        elif role == 'ADMIN_NATIONAL_ACCOUNTS':
            print("[DEBUG - NATIONAL ACCOUNTS REG] Special handling for ADMIN_NATIONAL_ACCOUNTS role")
            from .models import OrganizationType
            from geography.models import NationalFederation
            try:
                # Get or create NATIONAL organization type
                national_org_type, _ = OrganizationType.objects.get_or_create(
                    level='NATIONAL',
                    defaults={'name': 'National Federation', 'requires_approval': False, 'is_active': True}
                )
                user.organization_type = national_org_type
                print(f"[DEBUG - NATIONAL ACCOUNTS REG] Set organization type to: {national_org_type}")

                # Get or create SAFA National Federation
                safa_federation, _ = NationalFederation.objects.get_or_create(
                    name="South African Football Association",
                    defaults={'acronym': "SAFA", 'country_id': 1}
                )
                user.national_federation = safa_federation
                print(f"[DEBUG - NATIONAL ACCOUNTS REG] Set national federation to: {safa_federation}")

            except Exception as e:
                print(f"[DEBUG - NATIONAL ACCOUNTS REG] Error setting organization type or national federation: {e}")
        else:
            # Standard organization type handling for non-referee roles
            org_type = self.cleaned_data.get('organization_type')
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

            # Only set region if present in cleaned_data for non-referee roles
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
        
        # Debug association data
        print(f"[DEBUG - REFEREE REG] Association in form data: {self.cleaned_data.get('association')}")
        print(f"[DEBUG - REFEREE REG] All form cleaned data keys: {list(self.cleaned_data.keys())}")
        
        # Save the association from the form data, ensure it's always checked
        # For ADMIN_NATIONAL_ACCOUNTS, the association field should be None
        if role == 'ADMIN_NATIONAL_ACCOUNTS':
            user.association = None
            print("[DEBUG - NATIONAL ACCOUNTS REG] Association explicitly set to None for ADMIN_NATIONAL_ACCOUNTS role.")
        else:
            association_id = self.cleaned_data.get('association') or self.data.get('association')
            if association_id:
                from geography.models import Association, NationalFederation
                try:
                    # Get the association
                    if isinstance(association_id, Association):
                        user.association = association_id
                    else:
                        user.association = Association.objects.get(pk=association_id)
                    
                    print(f"[DEBUG - REFEREE REG] Association set to: {user.association}")
                    
                    # If the association doesn't have a national federation, set it to SAFA
                    if not user.association.national_federation:
                        # Get or create SAFA
                        safa = NationalFederation.objects.filter(
                            name__icontains="South African Football").first()
                        
                        if not safa:
                            safa = NationalFederation.objects.create(
                                name="South African Football Association",
                                acronym="SAFA",
                                country_id=1  # Assuming South Africa has ID 1
                            )
                        
                        # Set the association's national federation to SAFA and save it
                        user.association.national_federation = safa
                        user.association.save()
                        print(f"[DEBUG - REFEREE REG] Updated association's national federation to: {safa}")
                    
                    # Make sure the user's national federation matches the association's
                    user.national_federation = user.association.national_federation
                    print(f"[DEBUG - REFEREE REG] Set user's national federation to match association: {user.national_federation}")
                    
                except Exception as e:
                    print(f"[DEBUG - REFEREE REG] Error setting association: {e}")
            else:
                print("[DEBUG - REFEREE REG] No association selected in form, trying to set to SAFRA (ID: 11)")
                # If no association is selected and the role is ASSOCIATION_ADMIN, try to set SAFRA as default
                if role == 'ASSOCIATION_ADMIN':
                    try:
                        from geography.models import Association, NationalFederation
                        # Try to get SAFRA with ID 11
                        safra_assoc = Association.objects.filter(id=11).first()
                        if safra_assoc:
                            print(f"[DEBUG - REFEREE REG] Found SAFRA: {safra_assoc.name} (ID: {safra_assoc.id})")
                            user.association = safra_assoc
                            
                            # Make sure the user's national federation matches the association's
                            if safra_assoc.national_federation:
                                user.national_federation = safra_assoc.national_federation
                            print(f"[DEBUG - REFEREE REG] Set default SAFRA as association: {user.association}")
                        else:
                            print("[DEBUG - REFEREE REG] SAFRA association with ID 11 not found")
                    except Exception as e:
                        print(f"[DEBUG - REFEREE REG] Error setting SAFRA as default association: {e}")

        if role in ['ADMIN_NATIONAL', 'ADMIN_PROVINCE', 'ADMIN_REGION', 'ADMIN_LOCAL_FED', 'CLUB_ADMIN']:
            user.is_staff = True
        user.country_code = 'ZAF'
        user.nationality = 'South African'
        user.popi_act_consent = self.cleaned_data.get('popi_act_consent')
        # Generate SAFA ID if not provided
        if not user.safa_id:
            from .utils import generate_unique_safa_id
            user.safa_id = generate_unique_safa_id()

        # Set default status and approval status
        user.status = 'PENDING'
        user.is_approved = False

        if commit:
            user.save()
            # Save the many-to-many relationship for positions
            if self.cleaned_data.get('positions'):
                user.positions.set(self.cleaned_data['positions'])
            print(f"[DEBUG] User saved with region: {user.region} (pk={getattr(user.region, 'pk', None)})")
            print(f"[DEBUG - REFEREE REG] User successfully saved: {user.email}, association: {user.association}")
        return user

# Create alias for backward compatibility 
NationalUserRegistrationForm = UniversalRegistrationForm

from django import forms
from membership.models import Player, PlayerClubRegistration
from django.core.exceptions import ValidationError
from django.utils import timezone
import re

class ClubAdminPlayerRegistrationForm(forms.ModelForm):
    # Optional email field for player (already in model)
    popi_consent = forms.BooleanField(required=False, label="POPI Consent", help_text="Required for juniors")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # We'll handle the <form> tag and CSRF token in the template
        self.helper.layout = Layout(
            Div(
                Div(
                    Field('first_name'),
                    Field('last_name'),
                    Field('id_document_type'),
                    Div(
                        Field('id_number'),
                        css_class='id-number-field'
                    ),
                    Div(
                        Field('has_sa_passport'),
                        Div(
                            Field('sa_passport_number'),
                            css_class='sa-passport-number-field', style='display:none;'
                        ),
                        css_class='sa-passport-section id-number-only', style='display:none;'
                    ),
                    Div(
                        Field('passport_number'),
                        css_class='passport-field', style='display:none;'
                    ),
                    Field('safa_id'),
                    Field('fifa_id'),
                    css_class='col-md-6'
                ),
                Div(
                    Div(
                        HTML("""
                            <div id="div_id_date_of_birth" class="form-group">
                                <label for="id_date_of_birth">Date of birth</label>
                                <input type="date" name="date_of_birth" class="form-control" id="id_date_of_birth" disabled>
                                <small class="form-text text-muted">Auto-populated from ID number or enter manually for passport</small>
                            </div>
                        """),
                        css_class='mb-3'
                    ),
                    Div(
                        HTML("""
                            <div id="div_id_gender" class="form-group">
                                <label for="id_gender">Gender</label>
                                <select name="gender" class="form-control" id="id_gender" disabled>
                                    <option value="">---------</option>
                                    <option value="M">Male</option>
                                    <option value="F">Female</option>
                                </select>
                                <small class="form-text text-muted">Auto-populated from ID number or select for passport</small>
                            </div>
                        """),
                        css_class='mb-3'
                    ),
                    Div(
                        Field('sa_passport_document'),
                        css_class='mb-3 sa-passport-document-field', style='display:none;'
                    ),
                    Div(
                        Field('sa_passport_expiry_date'),
                        css_class='mb-3 sa-passport-expiry-field', style='display:none;'
                    ),
                    css_class='col-md-6'
                ),
                css_class='row'
            ),
            HTML('<hr>'),
            Fieldset(
                'Documents & Player Information',
                HTML('<p class="text-muted small">These documents are required for initial registration only</p>'),
                Div(
                    Div(
                        Field('profile_picture'),
                        css_class='col-md-6'
                    ),
                    Div(
                        Field('id_document'),
                        css_class='col-md-6'
                    ),
                    css_class='row'
                )
            ),
            HTML('<hr>'),
            Field('popi_consent')
        )
        # Make gender and email hidden fields
        self.fields['gender'].widget = forms.HiddenInput()
        self.fields['email'].widget = forms.HiddenInput()
        self.fields['email'].required = False  # Will be auto-generated
        self.fields['date_of_birth'].required = False  # Make DOB not required, will be calculated from ID
        
        # Configure SAFA ID and FIFA ID fields
        self.fields['safa_id'].required = False  # Will be auto-generated if not provided
        self.fields['safa_id'].help_text = "If the player already has a SAFA ID, enter it here. Otherwise, leave blank and it will be auto-generated."
        self.fields['safa_id'].widget.attrs.update({
            'pattern': '[A-Z0-9]{5}',
            'title': '5-character alphanumeric code (all caps)',
            'placeholder': 'e.g. A12B3'
        })
        
        self.fields['fifa_id'].required = False
        self.fields['fifa_id'].help_text = "If the player has a FIFA ID, enter it here. Otherwise, leave blank."
        self.fields['fifa_id'].widget.attrs.update({
            'pattern': '[0-9]{7}',
            'title': '7-digit FIFA identification number',
            'placeholder': 'e.g. 1234567'
        })
        
        # Name validation
        self.fields['first_name'].widget.attrs.update({
            'pattern': '[A-Za-z]{3,}', 
            'minlength': '3', 
            'title': 'Only letters, at least 3 characters'
        })
        self.fields['last_name'].widget.attrs.update({
            'pattern': '[A-Za-z]{3,}', 
            'minlength': '3', 
            'title': 'Only letters, at least 3 characters'
        })
        
        # Make ID number accept only digits
        self.fields['id_number'].widget.attrs.update({
            'pattern': '[0-9]{13}', 
            'inputmode': 'numeric',
            'title': 'ID number must be exactly 13 digits'
        })
        
        # Set has_sa_passport to False by default
        self.fields['has_sa_passport'].initial = False
        self.fields['has_sa_passport'].help_text = "Optional: Check this if the player has a South African passport in addition to SA ID (for record purposes only)"
        
        # Configure SA passport related fields
        self.fields['sa_passport_number'].required = False
        self.fields['sa_passport_number'].help_text = "Optional: Enter the South African passport number for record-keeping purposes"
        
        self.fields['sa_passport_document'].required = False
        self.fields['sa_passport_document'].help_text = "Optional: Upload a copy of the SA passport (PDF or image)"
        
        # Configure the expiry date field as a date widget
        self.fields['sa_passport_expiry_date'].required = False
        self.fields['sa_passport_expiry_date'].help_text = "Optional: Enter the expiry date of the SA passport"
        self.fields['sa_passport_expiry_date'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control', 'min': datetime.date.today().isoformat()}
        )

        if self.instance and self.instance.pk:
            # If an instance is provided (i.e., editing an existing player)
            # Disable fields that should not be changed after initial registration
            self.fields['first_name'].widget.attrs['readonly'] = True
            self.fields['last_name'].widget.attrs['readonly'] = True
            self.fields['id_document_type'].widget.attrs['disabled'] = True
            self.fields['id_number'].widget.attrs['readonly'] = True
            self.fields['passport_number'].widget.attrs['readonly'] = True
            self.fields['gender'].widget.attrs['disabled'] = True
            self.fields['date_of_birth'].widget.attrs['readonly'] = True
            self.fields['email'].widget.attrs['readonly'] = True # Email is auto-generated, should not be changed
            self.fields['safa_id'].widget.attrs['readonly'] = True
            self.fields['fifa_id'].widget.attrs['readonly'] = True
            self.fields['popi_consent'].widget.attrs['disabled'] = True # Consent is given once

            # If SA ID is selected, hide passport fields and vice versa
            if self.instance.id_document_type == 'ID':
                self.fields['passport_number'].widget = forms.HiddenInput()
                self.fields['passport_number'].required = False
            elif self.instance.id_document_type == 'PP':
                self.fields['id_number'].widget = forms.HiddenInput()
                self.fields['id_number'].required = False
                self.fields['has_sa_passport'].widget = forms.HiddenInput()
                self.fields['has_sa_passport'].required = False
                self.fields['sa_passport_number'].widget = forms.HiddenInput()
                self.fields['sa_passport_number'].required = False
                self.fields['sa_passport_document'].widget = forms.HiddenInput()
                self.fields['sa_passport_document'].required = False
                self.fields['sa_passport_expiry_date'].widget = forms.HiddenInput()
                self.fields['sa_passport_expiry_date'].required = False

            # Ensure hidden fields are not required
            for field_name in ['gender', 'email', 'date_of_birth']:
                self.fields[field_name].required = False

    class Meta:
        model = Player
        fields = [
            'first_name', 'last_name',
            'id_document_type', 'id_number', 'passport_number',
            'has_sa_passport', 'sa_passport_number', 'sa_passport_document', 'sa_passport_expiry_date',
            'safa_id', 'fifa_id',
            'gender', 'date_of_birth', 'email',
            'profile_picture', 'id_document',
            'popi_consent',
        ]
        # No widgets override: let JS handle field visibility

    # Keep server-side validation for names, ID/passport uniqueness, etc.
    def clean_first_name(self):
        value = self.cleaned_data.get('first_name', '')
        if not value.isalpha() or len(value) < 3:
            raise ValidationError('First name must be at least 3 alphabetic characters.')
        return value

    def clean_last_name(self):
        value = self.cleaned_data.get('last_name', '')
        if not value.isalpha() or len(value) < 3:
            raise ValidationError('Last name must be at least 3 alphabetic characters.')
        return value

    def clean(self):
        cleaned_data = super().clean()
        id_number = cleaned_data.get('id_number')
        passport_number = cleaned_data.get('passport_number')
        has_sa_passport = cleaned_data.get('has_sa_passport')
        sa_passport_number = cleaned_data.get('sa_passport_number')
        sa_passport_document = cleaned_data.get('sa_passport_document')
        sa_passport_expiry_date = cleaned_data.get('sa_passport_expiry_date')
        popi_consent = cleaned_data.get('popi_consent')
        id_document_type = cleaned_data.get('id_document_type')
        dob = cleaned_data.get('date_of_birth')
        id_document = cleaned_data.get('id_document')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        
        errors = {}
        
        # Validate ID number format if provided
        if id_number:
            if not re.match(r'^\d{13}$', id_number):
                errors['id_number'] = 'ID number must be exactly 13 digits'
        
        # Only require one of ID or passport, let JS/UI handle toggling
        if not id_number and not passport_number:
            errors['id_number'] = 'Either ID number or passport number is required'
            errors['passport_number'] = 'Either ID number or passport number is required'
        
        # Validate passport document if using passport
        from django.conf import settings
        validate_documents = getattr(settings, 'VALIDATE_PASSPORT_DOCUMENTS', True)
        
        if validate_documents and id_document_type == 'PP' and id_document and passport_number:
            from .utils import validate_passport_document
            
            # Validate the uploaded passport document
            is_valid, messages = validate_passport_document(
                id_document, passport_number, first_name, last_name, dob
            )
            
            # If validation failed, add error
            if not is_valid:
                if any(msg.startswith("Document must be") for msg in messages):
                    errors['id_document'] = f"Passport document validation failed: {', '.join(messages)}"
                else:
                    # For OCR validation failures, show warning but allow submission
                    # Store warning in session for display after redirect
                    request = getattr(self, 'request', None)
                    if request and hasattr(request, 'session'):
                        if 'document_warnings' not in request.session:
                            request.session['document_warnings'] = []
                        request.session['document_warnings'].append(
                            f"Passport document accepted but requires validation: {', '.join(messages)}"
                        )
        
        # If SA passport info is provided (optional), validate what's there
        if has_sa_passport:
            # Only validate passport expiry date if it's provided
            today = timezone.now().date()
            if sa_passport_expiry_date and sa_passport_expiry_date < today:
                errors['sa_passport_expiry_date'] = 'The SA passport has expired. Please provide a valid passport with a future expiry date'
                
            # Validate document format (if provided)
            if sa_passport_document:
                ext = os.path.splitext(sa_passport_document.name)[1].lower()
                if ext not in ['.pdf', '.jpg', '.jpeg', '.png']:
                    errors['sa_passport_document'] = 'SA passport document must be a PDF or image file (jpg, jpeg, png)'
                
                # If SA passport document is provided with a number, validate it
                if sa_passport_number and validate_documents:
                    from .utils import validate_passport_document
                    
                    # Validate the uploaded SA passport document
                    is_valid, messages = validate_passport_document(
                        sa_passport_document, sa_passport_number, first_name, last_name, dob
                    )
                    
                    # If validation failed, add error
                    if not is_valid:
                        if any(msg.startswith("Document must be") for msg in messages):
                            errors['sa_passport_document'] = f"SA passport document validation failed: {', '.join(messages)}"
                        else:
                            # For OCR validation failures, show warning but allow submission
                            request = getattr(self, 'request', None)
                            if request and hasattr(request, 'session'):
                                if 'document_warnings' not in request.session:
                                    request.session['document_warnings'] = []
                                request.session['document_warnings'].append(
                                    f"SA passport document accepted but requires validation: {', '.join(messages)}"
                                )
        
        # POPI consent required for juniors (under 18)
        if dob:
            age = (timezone.now().date() - dob).days // 365
            if age < 18 and not popi_consent:
                errors['popi_consent'] = 'POPI consent is required for players under 18'
                
        # Ensure id_number is unique
        if id_number and Player.objects.filter(id_number=id_number).exists():
            errors['id_number'] = 'A player with this ID number already exists'
            
        # Ensure passport_number is unique
        if passport_number and Player.objects.filter(passport_number=passport_number).exists():
            errors['passport_number'] = 'A player with this passport number already exists'
            
        # Check if SA passport number is unique
        if sa_passport_number and Player.objects.filter(sa_passport_number=sa_passport_number).exists():
            errors['sa_passport_number'] = 'A player with this South African passport number already exists'
        
        if errors:
            raise ValidationError(errors)
            
        return cleaned_data
        
        # POPI consent required for juniors (under 18)
        if dob:
            age = (timezone.now().date() - dob).days // 365
            if age < 18 and not popi_consent:
                raise ValidationError('POPI consent is required for players under 18.')
                
        # Ensure id_number/passport is unique
        if id_number and Player.objects.filter(id_number=id_number).exists():
            raise ValidationError('A player with this ID number already exists.')
            
        if passport_number and Player.objects.filter(passport_number=passport_number).exists():
            raise ValidationError('A player with this passport number already exists.')
            
        # Check if SA passport number is unique
        if sa_passport_number and Player.objects.filter(sa_passport_number=sa_passport_number).exists():
            raise ValidationError('A player with this South African passport number already exists.')
            
        return cleaned_data

class PlayerLookupForm(forms.Form):
    safa_id = forms.CharField(
        max_length=5, 
        required=False, 
        label="SAFA ID",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter existing SAFA ID'
        }),
        help_text="Enter the player's existing SAFA ID."
    )
    id_number = forms.CharField(
        max_length=13, 
        required=False, 
        label="SA ID Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 13-digit SA ID number'
        }),
        help_text="Alternatively, enter the player's SA ID number."
    )

    def clean(self):
        cleaned_data = super().clean()
        safa_id = cleaned_data.get('safa_id')
        id_number = cleaned_data.get('id_number')

        if not safa_id and not id_number:
            raise forms.ValidationError("Either SAFA ID or SA ID Number is required.")
        
        return cleaned_data


class OfficialLookupForm(forms.Form):
    safa_id = forms.CharField(
        max_length=5, 
        required=False, 
        label="SAFA ID",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter existing SAFA ID'
        }),
        help_text="Enter the official's existing SAFA ID."
    )
    id_number = forms.CharField(
        max_length=13, 
        required=False, 
        label="SA ID Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 13-digit SA ID number'
        }),
        help_text="Alternatively, enter the official's SA ID number."
    )

    def clean(self):
        cleaned_data = super().clean()
        safa_id = cleaned_data.get('safa_id')
        id_number = cleaned_data.get('id_number')

        if not safa_id and not id_number:
            raise forms.ValidationError("Either SAFA ID or SA ID Number is required.")
        
        return cleaned_data


class PlayerClubRegistrationOnlyForm(forms.ModelForm):
    class Meta:
        model = PlayerClubRegistration
        fields = ['position', 'jersey_number', 'height', 'weight', 'notes']

class PlayerUpdateForm(forms.ModelForm):
    """Form for updating player information after registration (including ID documents)"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set has_sa_passport initial value based on instance or default to False
        if self.instance and self.instance.pk:
            self.fields['has_sa_passport'].initial = self.instance.has_sa_passport
        else:
            self.fields['has_sa_passport'].initial = False
        # Help text for the checkbox
        self.fields['has_sa_passport'].help_text = "Optional: Check if player has a South African passport (for record purposes only)"
        # Make the SA passport number field not required initially
        self.fields['sa_passport_number'].required = False
        self.fields['sa_passport_number'].help_text = "Optional: Enter the South African passport number for record-keeping purposes"
        
        # Make phone_number optional
        self.fields['phone_number'].required = False
        self.fields['phone_number'].help_text = "Optional: Enter player's phone number if available"
        
        # Configure profile picture field
        self.fields['profile_picture'].help_text = "Upload player photo (required for player approval)"
        
        # Configure ID document field
        self.fields['id_document'].required = False
        if self.instance.id_document_type == 'ID':
            self.fields['id_document'].help_text = "Upload a copy of the South African ID document (required for approval)"
            self.fields['id_document'].label = "SA ID Document"
        else:
            self.fields['id_document'].help_text = "Upload a copy of the passport document (required for approval)"
            self.fields['id_document'].label = "Passport Document"
        
        # Configure the SA passport document and expiry fields
        self.fields['sa_passport_document'].required = False
        self.fields['sa_passport_document'].help_text = "Optional: Upload a copy of the SA passport (PDF or image)"
        
        # Configure the expiry date field
        self.fields['sa_passport_expiry_date'].required = False
        self.fields['sa_passport_expiry_date'].help_text = "Optional: Enter the expiry date of the SA passport"
        self.fields['sa_passport_expiry_date'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control', 'min': datetime.date.today().isoformat()}
        )
    
    class Meta:
        model = Player
        fields = [
            'email', 'phone_number', 'profile_picture', 'id_document',
            'has_sa_passport', 'sa_passport_number', 'sa_passport_document', 'sa_passport_expiry_date',
            'street_address', 'suburb', 'city', 'state', 'postal_code',
        ]
        
    def clean(self):
        from django.conf import settings
        cleaned_data = super().clean()
        sa_passport_number = cleaned_data.get('sa_passport_number')
        id_document = cleaned_data.get('id_document')
        
        # Check if SA passport number is unique (excluding the current instance), but only if provided
        if sa_passport_number:
            existingPlayers = Player.objects.filter(sa_passport_number=sa_passport_number).exclude(pk=self.instance.pk)
            if existingPlayers.exists():
                raise ValidationError('A player with this South African passport number already exists.')
        
        # If document validation is enabled in settings (default to True if not specified)
        validate_documents = getattr(settings, 'VALIDATE_PASSPORT_DOCUMENTS', True)
        
        if validate_documents:
            # If a new passport document is uploaded and player is not using SA ID, validate it
            if id_document and self.instance.id_document_type != 'ID' and hasattr(id_document, 'content_type'):
                # Only validate if the file is new or changed (check if it's a UploadedFile object)
                if hasattr(id_document, 'file') or hasattr(id_document, 'read'):
                    from .utils import validate_passport_document
                    
                    passport_number = self.instance.passport_number
                    first_name = self.instance.first_name
                    last_name = self.instance.last_name
                    dob = self.instance.date_of_birth
                    
                    # Validate the uploaded passport document
                    is_valid, messages = validate_passport_document(
                        id_document, passport_number, first_name, last_name, dob
                    )
                    
                    # If validation failed, add error or warning
                    if not is_valid:
                        # If it's a serious problem, block submission
                        if any(msg.startswith("Document must be") for msg in messages):
                            raise ValidationError(f"Passport document validation failed: {', '.join(messages)}")
                        else:
                            # For OCR validation failures, show warning but allow submission
                            # In a production system, you might want to flag these for manual review
                            from django.contrib import messages as django_messages
                            request = getattr(self, 'request', None)
                            if request:
                                django_messages.warning(
                                    request, 
                                    f"Passport document accepted but requires validation: {', '.join(messages)}"
                                )
    
            # Similarly, if a new SA passport document is uploaded, validate it
            sa_passport_document = cleaned_data.get('sa_passport_document')
            has_sa_passport = cleaned_data.get('has_sa_passport')
            
            if sa_passport_document and has_sa_passport and hasattr(sa_passport_document, 'content_type'):
                # Only validate if the file is new or changed
                if hasattr(sa_passport_document, 'file') or hasattr(sa_passport_document, 'read'):
                    from .utils import validate_passport_document
                    
                    sa_passport_number = cleaned_data.get('sa_passport_number')
                    if sa_passport_number:  # Only validate if SA passport number is provided
                        first_name = self.instance.first_name
                        last_name = self.instance.last_name
                        dob = self.instance.date_of_birth
                        
                        # Validate the SA passport document
                        is_valid, messages = validate_passport_document(
                            sa_passport_document, sa_passport_number, first_name, last_name, dob
                        )
                        
                        # If validation failed, add error or warning
                        if not is_valid:
                            # If it's a serious problem, block submission
                            if any(msg.startswith("Document must be") for msg in messages):
                                raise ValidationError(f"SA passport document validation failed: {', '.join(messages)}")
                            else:
                                # For OCR validation failures, show warning but allow submission
                                # In a production system, you might want to flag these for manual review
                                from django.contrib import messages as django_messages
                                request = getattr(self, 'request', None)
                                if request:
                                    django_messages.warning(
                                        request, 
                                        f"SA passport document accepted but requires validation: {', '.join(messages)}"
                                    )
                
        return cleaned_data

class PlayerClubRegistrationUpdateForm(forms.ModelForm):
    """Form for updating player club registration information"""
    class Meta:
        model = PlayerClubRegistration
        fields = ['position', 'jersey_number', 'height', 'weight', 'notes']


class OfficialCertificationForm(forms.ModelForm):
    """Form for adding certifications to officials"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configure date fields as date input
        self.fields['obtained_date'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['expiry_date'].widget = forms.DateInput(attrs={'type': 'date'})
        
        # Add classes and placeholders
        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter certification name'
        })
        
        self.fields['issuing_body'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter organization that issued this certification'
        })
        
        self.fields['certification_number'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter certification number (if applicable)'
        })
        
        self.fields['notes'].widget.attrs.update({
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter any additional notes about this certification'
        })
        
        # Set current date as default for obtained_date
        self.fields['obtained_date'].initial = timezone.now().date()
    
    class Meta:
        model = OfficialCertification
        fields = [
            'certification_type', 'level', 'name', 'issuing_body',
            'certification_number', 'obtained_date', 'expiry_date', 
            'document', 'notes'
        ]
        widgets = {
            'certification_type': forms.Select(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
        }


class ClubAdminOfficialRegistrationForm(forms.ModelForm):
    # Optional email field for official (already in model)
    popi_consent = forms.BooleanField(required=False, label="POPI Consent", help_text="Required for all officials")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    'first_name',
                    'last_name',
                    'id_document_type',
                    Div('id_number', css_class='id-number-field'),
                    Div('passport_number', css_class='passport-field', style='display:none;'),
                    'safa_id',
                    'fifa_id',
                    css_class='col-md-6'
                ),
                Div(
                    HTML("""
                        <div class="mb-3">
                            <div id="div_id_date_of_birth" class="form-group">
                                <label for="id_date_of_birth">Date of birth</label>
                                <input type="date" name="date_of_birth" class="form-control" id="id_date_of_birth" disabled>
                                <small class="form-text text-muted">Auto-populated from ID number or enter manually for passport</small>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div id="div_id_gender" class="form-group">
                                <label for="id_gender">Gender</label>
                                <select name="gender" class="form-control" id="id_gender" disabled>
                                    <option value="">---------</option>
                                    <option value="M">Male</option>
                                    <option value="F">Female</option>
                                </select>
                                <small class="form-text text-muted">Auto-populated from ID number or select for passport</small>
                            </div>
                        </div>
                    """),
                    'position',
                    Div('referee_level', css_class='referee-field', style='display:none;'),
                    css_class='col-md-6'
                ),
                css_class='row'
            ),
            Fieldset(
                'Certification Information',
                Div(
                    Div('certification_number', css_class='col-md-4'),
                    Div('certification_document', css_class='col-md-4'),
                    Div('certification_expiry_date', css_class='col-md-4'),
                    css_class='row'
                ),
                css_id='certification-section'
            ),
            Fieldset(
                'Documents & Official Information',
                Div(
                    Div('profile_picture', css_class='col-md-6'),
                    Div('id_document', css_class='col-md-6'),
                    css_class='row'
                )
            ),
            'popi_consent'
        )

        # Make gender and email hidden fields
        self.fields['gender'].widget = forms.HiddenInput()
        self.fields['email'].widget = forms.HiddenInput()
        self.fields['email'].required = False  # Will be auto-generated
        
        # Name validation
        self.fields['first_name'].widget.attrs.update({
            'pattern': '[A-Za-z]{3,}', 
            'minlength': '3', 
            'title': 'Only letters, at least 3 characters'
        })
        self.fields['last_name'].widget.attrs.update({
            'pattern': '[A-Za-z]{3,}', 
            'minlength': '3', 
            'title': 'Only letters, at least 3 characters'
        })
        
        # Make ID number accept only digits
        self.fields['id_number'].widget.attrs.update({
            'pattern': '[0-9]{13}', 
            'inputmode': 'numeric',
            'title': 'ID number must be exactly 13 digits'
        })
        
        # Configure SAFA ID and FIFA ID fields
        self.fields['safa_id'].required = False  # Will be auto-generated if not provided
        self.fields['safa_id'].help_text = "If the official already has a SAFA ID, enter it here. Otherwise, leave blank and it will be auto-generated."
        self.fields['safa_id'].widget.attrs.update({
            'pattern': '[A-Z0-9]{5}',
            'title': '5-character alphanumeric code (all caps)',
            'placeholder': 'e.g. A12B3'
        })
        
        self.fields['fifa_id'].required = False
        self.fields['fifa_id'].help_text = "If the official has a FIFA ID, enter it here. Otherwise, leave blank."
        self.fields['fifa_id'].widget.attrs.update({
            'pattern': '[0-9]{7}',
            'title': '7-digit FIFA identification number',
            'placeholder': 'e.g. 1234567'
        })
        
        # Filter positions to only show positions available at club level
        self.fields['position'].queryset = self.fields['position'].queryset.filter(
            levels__contains='CLUB', is_active=True)
        self.fields['position'].help_text = "Select the official's role or position in the club"
        self.fields['position'].required = True

    class Meta:
        model = Official
        fields = [
            'first_name', 'last_name',
            'id_document_type', 'id_number', 'passport_number',
            'gender', 'date_of_birth', 'email',
            'position', 'certification_number', 'certification_document',
            'certification_expiry_date', 'referee_level',
            'safa_id', 'fifa_id',
            'profile_picture', 'id_document',
            'popi_consent',
        ]

    # Keep server-side validation for names, ID/passport uniqueness, etc.
    def clean_first_name(self):
        value = self.cleaned_data.get('first_name', '')
        if not value.isalpha() or len(value) < 3:
            raise ValidationError('First name must be at least 3 alphabetic characters.')
        return value

    def clean_last_name(self):
        value = self.cleaned_data.get('last_name', '')
        if not value.isalpha() or len(value) < 3:
            raise ValidationError('Last name must be at least 3 alphabetic characters.')
        return value

    def clean(self):
        cleaned_data = super().clean()
        id_number = cleaned_data.get('id_number')
        passport_number = cleaned_data.get('passport_number')
        popi_consent = cleaned_data.get('popi_consent')
        id_document_type = cleaned_data.get('id_document_type')
        dob = cleaned_data.get('date_of_birth')
        id_document = cleaned_data.get('id_document')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        
        errors = {}
        
        # Validate ID number format if provided
        if id_number:
            if not re.match(r'^\d{13}$', id_number):
                errors['id_number'] = 'ID number must be exactly 13 digits'
        
        # Only require one of ID or passport, let JS/UI handle toggling
        if not id_number and not passport_number:
            errors['id_number'] = 'Either ID number or passport number is required'
            errors['passport_number'] = 'Either ID number or passport number is required'
        
        # Validate passport document if using passport
        from django.conf import settings
        validate_documents = getattr(settings, 'VALIDATE_PASSPORT_DOCUMENTS', True)
        
        if validate_documents and id_document_type == 'PP' and id_document and passport_number:
            from .utils import validate_passport_document
            
            # Validate the uploaded passport document
            is_valid, messages = validate_passport_document(
                id_document, passport_number, first_name, last_name, dob
            )
            
            # If validation failed, add error
            if not is_valid:
                if any(msg.startswith("Document must be") for msg in messages):
                    errors['id_document'] = f"Passport document validation failed: {', '.join(messages)}"
                else:
                    # For OCR validation failures, show warning but allow submission
                    # Store warning in session for display after redirect
                    request = getattr(self, 'request', None)
                    if request and hasattr(request, 'session'):
                        if 'document_warnings' not in request.session:
                            request.session['document_warnings'] = []
                        request.session['document_warnings'].append(
                            f"Passport document accepted but requires validation: {', '.join(messages)}"
                        )
        
        # POPI consent required for everyone
        if not popi_consent:
            errors['popi_consent'] = 'POPI consent is required'
                
        # Ensure id_number is unique across all members
        if id_number:
            from membership.models import Member
            if Member.objects.filter(id_number=id_number).exists():
                errors['id_number'] = 'A member with this ID number already exists'
            
        # Ensure passport_number is unique across all members
        if passport_number:
            from membership.models import Member
            if Member.objects.filter(passport_number=passport_number).exists():
                errors['passport_number'] = 'A member with this passport number already exists'
        
        if errors:
            raise ValidationError(errors)
            
        return cleaned_data

class PositionForm(forms.ModelForm):
    """Form for creating and editing positions with level checkboxes"""
    LEVEL_CHOICES = [
        ('NATIONAL', 'National Level'),
        ('PROVINCE', 'Province Level'),
        ('REGION', 'Region Level'),
        ('LFA', 'LFA Level'),
        ('CLUB', 'Club Level'),
        ('ASSOCIATION', 'Association Level'),
    ]
    
    level_checkboxes = forms.MultipleChoiceField(
        choices=LEVEL_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Available at Levels",
        help_text="Select all levels where this position can be used"
    )
    
    class Meta:
        model = Position
        fields = ['title', 'description', 'employment_type', 'is_active', 'requires_approval']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If instance exists, populate checkboxes from levels string
        if self.instance and self.instance.pk and self.instance.levels:
            selected_levels = [level.strip() for level in self.instance.levels.split(',')]
            self.initial['level_checkboxes'] = selected_levels
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Convert selected checkboxes to comma-separated string
        selected_levels = self.cleaned_data.get('level_checkboxes', [])
        if selected_levels:
            instance.levels = ','.join(selected_levels)
        else:
            # Default to all levels if none selected
            instance.levels = 'NATIONAL,PROVINCE,REGION,LFA,CLUB'
        
        if commit:
            instance.save()
        
        return instance

class AssociationOfficialRegistrationForm(forms.ModelForm):
    """Form for registering officials at Association level"""
    # Optional email field for official (already in model)
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}))
    popi_consent = forms.BooleanField(required=False, label="POPI Consent", help_text="Required for all officials")


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configure gender field with proper display and options
        self.fields['gender'].widget = forms.Select(choices=[('M', 'Male'), ('F', 'Female')], attrs={'class': 'form-select'})
        self.fields['email'].required = False  # Will be auto-generated
        
        # Add email field with improved styling
        self.fields['email'].widget = forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email or leave blank for auto-generation',
            'autocomplete': 'email',
            'data-validation-email': 'true'
        })
        
        # Configure phone number field and validation
        self.fields['phone_number'] = forms.CharField(
            max_length=20, 
            required=False,
            label="Mobile Number",
            help_text="Enter South African mobile number (optional)",
            widget=forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '+27xx xxx xxxx or 0xx xxx xxxx',
                'pattern': '(\\+27|0)\\d{9}',
                'data-validation-phone': 'true'
            })
        )
        
        # Make date of birth a date picker and readonly when ID is selected (will be extracted from ID)
        self.fields['date_of_birth'].widget = forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control',
            'readonly': 'readonly'
        })
        
        # Name validation
        self.fields['first_name'].widget.attrs.update({
            'pattern': '[A-Za-z]{3,}', 
            'minlength': '3', 
            'title': 'Only letters, at least 3 characters'
        })
        self.fields['last_name'].widget.attrs.update({
            'pattern': '[A-Za-z]{3,}', 
            'minlength': '3', 
            'title': 'Only letters, at least 3 characters'
        })
        
        # Make ID number accept only digits
        self.fields['id_number'].widget.attrs.update({
            'pattern': '[0-9]{13}', 
            'inputmode': 'numeric',
            'title': 'ID number must be exactly 13 digits'
        })
        
        # Configure SAFA ID and FIFA ID fields
        self.fields['safa_id'].required = False  # Will be auto-generated if not provided
        self.fields['safa_id'].help_text = "If the official already has a SAFA ID, enter it here. Otherwise, leave blank and it will be auto-generated."
        self.fields['safa_id'].widget.attrs.update({
            'pattern': '[A-Z0-9]{5}',
            'title': '5-character alphanumeric code (all caps)',
            'placeholder': 'e.g. A12B3'
        })
        
        self.fields['fifa_id'].required = False
        self.fields['fifa_id'].help_text = "If the official has a FIFA ID, enter it here. Otherwise, leave blank."
        self.fields['fifa_id'].widget.attrs.update({
            'pattern': '[0-9]{7}',
            'title': '7-digit FIFA identification number',
            'placeholder': 'e.g. 1234567'
        })
        # Filter positions to only show positions available at association level
        self.fields['position'].queryset = self.fields['position'].queryset.filter(
            levels__contains='ASSOCIATION', is_active=True)
        self.fields['position'].help_text = "Select the official's role or position in the association"
        self.fields['position'].required = True
        
        # Add a field to select the official's primary referee association
        from geography.models import Association
        self.fields['primary_association'] = forms.ModelChoiceField(
            queryset=Association.objects.all(),  # Remove is_active filter as it doesn't exist in the model
            required=True,
            widget=forms.Select(attrs={'class': 'form-select'}),
            help_text="Select the referee association for this official"
        )
        # Prepopulate on edit
        if self.instance and self.instance.primary_association_id:
            self.initial['primary_association'] = self.instance.primary_association_id

    class Meta:
        model = Official
        fields = [
            'first_name', 'last_name', 'email',
            'id_document_type', 'id_number', 'passport_number',
            'gender', 'date_of_birth', 'email', 'phone_number',
            'position', 'certification_number', 'certification_document',
            'certification_expiry_date', 'referee_level',
            'safa_id', 'fifa_id',
            'profile_picture', 'id_document',
            'popi_consent',
            'primary_association',  # Primary referee association
         ]

    # Keep server-side validation for names, ID/passport uniqueness, etc.
    def clean_first_name(self):
        value = self.cleaned_data.get('first_name', '')
        if not value.isalpha() or len(value) < 3:
            raise ValidationError('First name must be at least 3 alphabetic characters.')
        return value

    def clean_last_name(self):
        value = self.cleaned_data.get('last_name', '')
        if not value.isalpha() or len(value) < 3:
            raise ValidationError('Last name must be at least 3 alphabetic characters.')
        return value

    def clean(self):
        cleaned_data = super().clean()
        id_number = cleaned_data.get('id_number')
        passport_number = cleaned_data.get('passport_number')
        popi_consent = cleaned_data.get('popi_consent')
        id_document_type = cleaned_data.get('id_document_type')
        dob = cleaned_data.get('date_of_birth')
        id_document = cleaned_data.get('id_document')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password and password2 and password != password2:
            self.add_error('password2', "Passwords do not match")

        
        errors = {}
        
        # Validate ID number format if provided
        if id_number:
            if not re.match(r'^\d{13}$', id_number):
                errors['id_number'] = 'ID number must be exactly 13 digits'
        
        # Only require one of ID or passport, let JS/UI handle toggling
        if not id_number and not passport_number:
            errors['id_number'] = 'Either ID number or passport number is required'
            errors['passport_number'] = 'Either ID number or passport number is required'
        
        # Validate passport document if using passport
        from django.conf import settings
        validate_documents = getattr(settings, 'VALIDATE_PASSPORT_DOCUMENTS', True)
        
        if validate_documents and id_document_type == 'PP' and id_document and passport_number:
            from .utils import validate_passport_document
            
            # Validate the uploaded passport document
            is_valid, messages = validate_passport_document(
                id_document, passport_number, first_name, last_name, dob
            )
            
            # If validation failed, add error
            if not is_valid:
                if any(msg.startswith("Document must be") for msg in messages):
                    errors['id_document'] = f"Passport document validation failed: {', '.join(messages)}"
                else:
                    # For OCR validation failures, show warning but allow submission
                    # Store warning in session for display after redirect
                    request = getattr(self, 'request', None)
                    if request and hasattr(request, 'session'):
                        if 'document_warnings' not in request.session:
                            request.session['document_warnings'] = []
                        request.session['document_warnings'].append(
                            f"Passport document accepted but requires validation: {', '.join(messages)}"
                        )
        
        # POPI consent required for everyone
        if not popi_consent:
            errors['popi_consent'] = 'POPI consent is required'
                
        # Ensure id_number is unique across all members
        if id_number:
            from membership.models import Member
            if Member.objects.filter(id_number=id_number).exists():
                errors['id_number'] = 'A member with this ID number already exists'
            
        # Ensure passport_number is unique across all members
        if passport_number:
            from membership.models import Member
            if Member.objects.filter(passport_number=passport_number).exists():
                errors['passport_number'] = 'A member with this passport number already exists'
        
        if errors:
            raise ValidationError(errors)
            
        return cleaned_data

        
