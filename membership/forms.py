from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Member, Membership, Player, Transfer, TransferAppeal, MembershipApplication, ClubRegistration
from geography.models import Club, LocalFootballAssociation
from phonenumber_field.formfields import PhoneNumberField
from accounts.models import CustomUser
import re
import datetime
from django.utils import timezone

class AddressFormMixin:
    """Mixin to add address field grouping to forms"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_address_fieldset()

    def add_address_fieldset(self):
        """Group address fields and add any custom widgets"""
        address_fields = ['street_address', 'suburb', 'city', 
                         'state', 'postal_code', 'country']
        for field in address_fields:
            if field in self.fields:
                self.fields[field].widget.attrs.update({
                    'class': 'address-field',
                    'placeholder': self.fields[field].label
                })

class MemberForm(AddressFormMixin, forms.ModelForm):
    class Meta:
        model = Member
        fields = [
            # Personal Information
            'first_name', 'last_name', 'email', 'phone_number', 
            'date_of_birth', 'member_type',
            # Identification
            'id_number', 'passport_number', 'gender',
            # Address Information
            'street_address', 'suburb', 'city', 'state', 
            'postal_code', 'country',
            # Membership Information
            'status',
            # Geography
            'province', 'region', 'lfa',
            # Images
            'profile_picture',  
            # Emergency Contact
            'emergency_contact', 'emergency_phone', 'medical_notes'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'registration_date': forms.DateInput(attrs={'type': 'date'}),
            'medical_notes': forms.Textarea(attrs={'rows': 3}),
            'street_address': forms.TextInput(attrs={'placeholder': _('Street address')}),
            'suburb': forms.TextInput(attrs={'placeholder': _('Suburb')}),
            'city': forms.TextInput(attrs={'placeholder': _('City')}),
            'state': forms.TextInput(attrs={'placeholder': _('State/Province')}),
            'postal_code': forms.TextInput(attrs={'placeholder': _('Postal/ZIP code')}),
            'country': forms.TextInput(attrs={'placeholder': _('Country')}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Add any user-specific customizations here if needed
        # Note: club assignment is now handled through ClubRegistration

class PlayerForm(AddressFormMixin, forms.ModelForm):
    class Meta:
        model = Player
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'date_of_birth',
            'gender', 'id_number', 'passport_number',
            'street_address', 'suburb', 'city', 'state', 'postal_code', 'country',
            'status', 'is_approved',
            'profile_picture',
            'emergency_contact', 'emergency_phone', 'medical_notes'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'registration_date': forms.DateInput(attrs={'type': 'date'}),
            'medical_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Add any user-specific customizations here if needed
        # Note: club assignment is now handled through ClubRegistration

    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number', '').strip()
        if id_number:
            try:
                # Use the model's validation logic
                temp_instance = Player(id_number=id_number)
                temp_instance._validate_id_number()
            except ValidationError as e:
                raise forms.ValidationError(e.messages)
        return id_number

    def clean(self):
        cleaned_data = super().clean()
        # No need to call clean_id_number explicitly; Django does this automatically.
        return cleaned_data

class PlayerRegistrationForm(AddressFormMixin, forms.ModelForm):
    """Form for registering a new player"""

    POSITION_CHOICES = [
        ('GK', 'Goalkeeper'),
        ('DF', 'Defender'),
        ('MF', 'Midfielder'),
        ('FW', 'Forward'),
    ]

    # Club fields (read-only)
    club_name = forms.CharField(disabled=True, required=False)

    # Playing details
    position = forms.ChoiceField(
        choices=POSITION_CHOICES,
        required=False,
        help_text=_("Player's primary position")
    )
    jersey_number = forms.IntegerField(
        min_value=1,
        max_value=99,
        required=False,
        help_text=_("Preferred jersey number (1-99)")
    )

    class Meta:
        model = Player
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'date_of_birth',
            'gender', 'id_number',
            'street_address', 'suburb', 'city', 'state', 'postal_code', 'country',
            'emergency_contact', 'emergency_phone', 'medical_notes',
            'position', 'jersey_number',
            # Do NOT include 'club' here; set it in the view!
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'medical_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club
        # Make important fields required
        self.fields['phone_number'].required = True
        self.fields['emergency_contact'].required = True
        self.fields['emergency_phone'].required = True

    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number', '').strip()
        if id_number:
            try:
                temp_instance = Player(id_number=id_number)
                temp_instance._validate_id_number()
            except ValidationError as e:
                raise forms.ValidationError(e.messages)
        return id_number

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.club:
            instance.club = self.club
        if commit:
            instance.save()
        return instance

class PaymentSelectionForm(forms.Form):
    """Form for selecting membership type and payment method"""

    MEMBERSHIP_CHOICES = [
        ('JR', 'Junior (R100 ZAR)'),
        ('SR', 'Senior (R200 ZAR)'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('EFT', 'EFT/Bank Transfer'),
        ('CARD', 'Credit/Debit Card'),
    ]

    membership_type = forms.ChoiceField(
        choices=MEMBERSHIP_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        label=_("Membership Type"),
        help_text=_("Select the appropriate membership category")
    )

    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        label=_("Payment Method"),
        help_text=_("Choose how you would like to pay")
    )

class TransferRequestForm(forms.ModelForm):
    """Form for initiating a player transfer"""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        # Filter players based on user's club if they're a club admin
        if not self.user.is_superuser:
            member = self.user.member_profile
            if member.role == 'CLUB_ADMIN':
                self.fields['player'].queryset = Player.objects.filter(
                    club=member.club,
                    club_registrations__status='ACTIVE'
                )

        # Filter destination clubs to exclude player's current club
        self.fields['to_club'].queryset = Club.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        player = cleaned_data.get('player')
        to_club = cleaned_data.get('to_club')

        if player and to_club:
            # Check if player's current club matches the user's club
            if not self.user.is_superuser:
                member = self.user.member_profile
                if member.role == 'CLUB_ADMIN' and player.club != member.club:
                    raise ValidationError(
                        _("You can only initiate transfers for players in your club.")
                    )

            # Check if player is already registered with destination club
            if player.club == to_club:
                raise ValidationError(
                    _("Player is already registered with this club.")
                )

            # Check for existing pending transfers
            pending_transfer = Transfer.objects.filter(
                player=player,
                status='PENDING'
            ).first()

            if pending_transfer:
                raise ValidationError(
                    _("Player already has a pending transfer request.")
                )

        return cleaned_data

    class Meta:
        model = Transfer
        fields = ['player', 'to_club', 'transfer_fee', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

class TransferAppealForm(forms.ModelForm):
    class Meta:
        model = TransferAppeal
        fields = ['appeal_reason', 'supporting_document']
        widgets = {
            'appeal_reason': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, transfer=None, submitted_by=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.transfer = transfer
        self.submitted_by = submitted_by

    def clean(self):
        cleaned_data = super().clean()
        if self.transfer and self.transfer.status != 'REJECTED':
            raise ValidationError(_("Only rejected transfers can be appealed."))
        return cleaned_data

    def save(self, commit=True):
        appeal = super().save(commit=False)
        appeal.transfer = self.transfer
        appeal.submitted_by = self.submitted_by
        if commit:
            appeal.save()
        return appeal

# Club form
class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = [
            'name', 
            'code', 
            'localfootballassociation',  # Instead of local_football_association
            'founding_date',             # Instead of founded_year
            'website',
            'stadium',
            'description',
            'colors',
            'logo'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'founding_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name != 'logo':
                field.widget.attrs.update({'class': 'form-control'})

class MembershipApplicationForm(forms.ModelForm):
    """Form for applying for SAFA membership (Step 1 of two-tier system)"""

    # Junior-specific fields
    is_junior = forms.BooleanField(required=False, label="Under 18 years old")
    guardian_name = forms.CharField(required=False, label="Guardian/Parent Name")
    guardian_email = forms.EmailField(required=False, label="Guardian/Parent Email") 
    guardian_phone = forms.CharField(required=False, label="Guardian/Parent Phone")
    school = forms.CharField(required=False, label="School Name")

    # Consent
    popi_consent = forms.BooleanField(
        required=False, 
        label="POPI Act Consent",
        help_text="Required for members under 18 years old"
    )

    # Signature data (for digital signature pad)
    signature_data = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        help_text="Digital signature data"
    )

    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'date_of_birth',
            'gender', 'id_document_type', 'id_number', 'passport_number', 'member_type',
            'safa_id', 'fifa_id',  # Add SAFA ID and FIFA ID fields
            'has_sa_passport', 'sa_passport_number', 'sa_passport_document', 'sa_passport_expiry_date',
            'street_address', 'suburb', 'city', 'state', 'postal_code', 'country',
            'emergency_contact', 'emergency_phone', 'medical_notes',
            'profile_picture', 'id_document',
            # Geography fields for administrative purposes
            'province', 'region', 'lfa',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'medical_notes': forms.Textarea(attrs={'rows': 3}),
            'member_type': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make email required for all members
        self.fields['email'].required = True
        self.fields['phone_number'].required = False  # Make phone number optional
        self.fields['date_of_birth'].required = False  # DOB will be extracted from ID

        # Configure document type field
        self.fields['id_document_type'].widget.attrs.update({'class': 'form-control'})

        # Style form fields
        self.fields['first_name'].widget.attrs.update({
            'pattern': '[A-Za-z\s\-\']{3,}', 
            'minlength': '3', 
            'title': 'Only letters, spaces, hyphens, and apostrophes (no numbers), at least 3 characters',
            'class': 'form-control',
            'oninput': 'this.value = this.value.replace(/[^A-Za-z\s\-\']/g, "")',
            'onblur': 'validateNameField(this)'
        })
        self.fields['last_name'].widget.attrs.update({
            'pattern': '[A-Za-z\s\-\']{3,}', 
            'minlength': '3', 
            'title': 'Only letters, spaces, hyphens, and apostrophes (no numbers), at least 3 characters',
            'class': 'form-control',
            'oninput': 'this.value = this.value.replace(/[^A-Za-z\s\-\']/g, "")',
            'onblur': 'validateNameField(this)'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'type': 'email',
            'pattern': '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'title': 'Please enter a valid email address',
            'oninput': 'validateEmailField(this)',
        })
        self.fields['phone_number'].widget.attrs.update({
            'class': 'form-control',
            'pattern': '^[+]?[0-9]{10,15}$',
            'title': 'Enter a valid phone number (numbers and + sign only)',
            'placeholder': 'e.g., +27123456789 (optional)',
            'inputmode': 'tel',
            'oninput': 'this.value = this.value.replace(/[^+0-9]/g, "")'
        })

        # Configure SAFA ID and FIFA ID fields
        self.fields['safa_id'].required = False  # Will be auto-generated if not provided
        self.fields['safa_id'].help_text = "If you already have a SAFA ID, enter it here. Otherwise, leave blank and it will be auto-generated."
        self.fields['safa_id'].widget.attrs.update({
            'pattern': '[A-Z0-9]{5}',
            'title': '5-character alphanumeric code (all caps)',
            'placeholder': 'e.g. A12B3',
            'class': 'form-control'
        })

        self.fields['fifa_id'].required = False
        self.fields['fifa_id'].help_text = "If you have a FIFA ID, enter it here. Otherwise, leave blank."
        self.fields['fifa_id'].widget.attrs.update({
            'pattern': '[0-9]{7}',
            'title': '7-digit FIFA identification number',
            'placeholder': 'e.g. 1234567',
            'class': 'form-control'
        })

        # ID validation
        self.fields['id_number'].widget.attrs.update({
            'pattern': '[0-9]{13}', 
            'inputmode': 'numeric', 
            'title': 'ID number must be exactly 13 digits (numbers only)',
            'class': 'form-control',
            'oninput': 'this.value = this.value.replace(/[^0-9]/g, "")',
            'onblur': 'validateIdField(this)',
            'maxlength': '13',
            'minlength': '13'
        })

        # Geography fields are optional but helpful for admin
        self.fields['province'].required = False
        self.fields['region'].required = False
        self.fields['lfa'].required = False

    def clean_first_name(self):
        value = self.cleaned_data.get('first_name', '')
        # Check if name contains at least 3 characters
        if len(value) < 3:
            raise ValidationError('First name must be at least 3 characters.')

        # Check if name contains only allowed characters (letters, spaces, hyphens, apostrophes)
        import re
        if not re.match(r'^[A-Za-z\s\-\']+$', value):
            raise ValidationError('First name must contain only letters, spaces, hyphens, and apostrophes (no numbers).')

        # Check if name contains any digits
        if any(char.isdigit() for char in value):
            raise ValidationError('First name cannot contain numbers.')

        return value

    def clean_last_name(self):
        value = self.cleaned_data.get('last_name', '')
        # Check if name contains at least 3 characters
        if len(value) < 3:
            raise ValidationError('Last name must be at least 3 characters.')

        # Check if name contains only allowed characters (letters, spaces, hyphens, apostrophes)
        import re
        if not re.match(r'^[A-Za-z\s\-\']+$', value):
            raise ValidationError('Last name must contain only letters, spaces, hyphens, and apostrophes (no numbers).')

        # Check if name contains any digits
        if any(char.isdigit() for char in value):
            raise ValidationError('Last name cannot contain numbers.')

        return value

    def clean_phone_number(self):
        """Validate phone number to only allow numeric characters and + sign"""
        phone_number = self.cleaned_data.get('phone_number', '').strip()
        if phone_number:
            # Remove all non-numeric characters except the + sign
            import re
            if not re.match(r'^[+]?[0-9]{10,15}$', phone_number):
                raise ValidationError('Phone number must contain only digits and optional + sign (10-15 digits)')
        return phone_number

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and Member.objects.filter(email=email).exists():
            raise ValidationError('A member with this email address already exists.')
        return email

    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number', '').strip()
        if id_number:
            if not re.match(r'^\d{13}$', id_number):
                raise ValidationError('ID number must be exactly 13 digits')
            # Check for existing member with same ID
            if Member.objects.filter(id_number=id_number).exists():
                raise ValidationError('A member with this ID number already exists')

            # Extract DOB and gender
            id_info = CustomUser.extract_id_info(id_number)
            if not id_info['is_valid']:
                raise ValidationError(id_info['error'])
            self.cleaned_data['date_of_birth'] = id_info['date_of_birth']
            self.cleaned_data['gender'] = id_info['gender']
        return id_number

    def clean(self):
        cleaned_data = super().clean()
        id_number = cleaned_data.get('id_number')
        passport_number = cleaned_data.get('passport_number')
        dob = cleaned_data.get('date_of_birth')
        is_junior = cleaned_data.get('is_junior')
        popi_consent = cleaned_data.get('popi_consent')

        # SAFA ID auto-generation will be handled in the save method
        guardian_name = cleaned_data.get('guardian_name')
        guardian_email = cleaned_data.get('guardian_email')

        errors = {}

        # Either ID number or passport required
        if not id_number and not passport_number:
            errors['id_number'] = 'Either ID number or passport number is required'
            errors['passport_number'] = 'Either ID number or passport number is required'
        elif id_number and passport_number:
            # If both are provided, clear any previous errors for these fields
            if 'id_number' in errors:
                del errors['id_number']
            if 'passport_number' in errors:
                del errors['passport_number']

        # For passport users, DOB and gender are required
        id_document_type = cleaned_data.get('id_document_type')
        if id_document_type == 'PP' and passport_number:
            if not dob:
                errors['date_of_birth'] = 'Date of birth is required when using passport'
            if not cleaned_data.get('gender'):
                errors['gender'] = 'Gender is required when using passport'

        # Junior validation
        if dob:
            age = (timezone.now().date() - dob).days // 365
            is_actually_junior = age < 18

            if is_actually_junior or is_junior:
                # Require POPI consent for juniors
                if not popi_consent:
                    errors['popi_consent'] = 'POPI consent is required for members under 18'

                # Require guardian information for juniors
                if not guardian_name:
                    errors['guardian_name'] = 'Guardian name is required for members under 18'
                if not guardian_email:
                    errors['guardian_email'] = 'Guardian email is required for members under 18'

                # Auto-set member type
                cleaned_data['member_type'] = 'JUNIOR'
            else:
                cleaned_data['member_type'] = 'SENIOR'

        if errors:
            raise ValidationError(errors)

        return cleaned_data


class ClubRegistrationForm(forms.ModelForm):
    """Form for registering an approved SAFA member with a club"""

    class Meta:
        model = ClubRegistration
        fields = ['club', 'position', 'jersey_number', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['club'].required = True
        self.fields['position'].help_text = "Playing position (for athletes)"
        self.fields['jersey_number'].help_text = "Preferred jersey number (optional)"

        # Add styling
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
