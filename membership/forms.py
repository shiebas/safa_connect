from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Member, Membership, Player, Transfer, TransferAppeal, MembershipApplication
from geography.models import Club, LocalFootballAssociation
from phonenumber_field.formfields import PhoneNumberField
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
            'date_of_birth',
            # Address Information
            'street_address', 'suburb', 'city', 'state', 
            'postal_code', 'country',
            # Membership Information
            'status', 'membership_number', 'club',
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
        if user and not user.is_superuser:
            # If user is not superuser and has a club, limit club choices
            self.fields['club'].queryset = Club.objects.filter(pk=user.club.pk)
            self.fields['club'].initial = user.club
            self.fields['club'].widget.attrs['readonly'] = True

class PlayerForm(AddressFormMixin, forms.ModelForm):
    class Meta:
        model = Player
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'date_of_birth',
            'gender', 'id_number',
            'street_address', 'suburb', 'city', 'state', 'postal_code', 'country',
            'status', 'membership_number', 'club',
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
        if user and not user.is_superuser:
            member = getattr(user, 'member_profile', None)
            if member and member.role == 'CLUB_ADMIN':
                self.fields['club'].queryset = Club.objects.filter(pk=member.club.pk)
                self.fields['club'].initial = member.club
                self.fields['club'].widget.attrs['readonly'] = True

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
    popi_consent = forms.BooleanField(required=False, label="POPI Consent", help_text="Required for juniors")
    signature_data = forms.CharField(widget=forms.HiddenInput())
    phone_number = forms.CharField(required=False, label="Phone Number")
    street_address = forms.CharField(required=False, label="Street Address")
    suburb = forms.CharField(required=False, label="Suburb")
    city = forms.CharField(required=False, label="City")
    state = forms.CharField(required=False, label="State/Province")
    postal_code = forms.CharField(required=False, label="Postal/ZIP Code")
    country = forms.CharField(required=False, label="Country")
    emergency_contact = forms.CharField(required=False, label="Emergency Contact")
    emergency_phone = forms.CharField(required=False, label="Emergency Contact Phone")
    medical_notes = forms.CharField(required=False, label="Medical Notes", widget=forms.Textarea)
    club = forms.ModelChoiceField(queryset=Club.objects.all(), required=False, label="Club")
    id_number = forms.CharField(required=False, label="ID Number")
    passport_number = forms.CharField(required=False, label="Passport Number")
    gender = forms.CharField(required=False, widget=forms.HiddenInput())
    email = forms.EmailField(required=False, widget=forms.HiddenInput())
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    first_name = forms.CharField(label="First Name")
    last_name = forms.CharField(label="Last Name")
    profile_picture = forms.ImageField(required=False)
    id_document = forms.FileField(required=False)

    class Meta:
        model = Player
        fields = [
            'first_name', 'last_name', 'phone_number',
            'street_address', 'suburb', 'city', 'state', 'postal_code', 'country',
            'emergency_contact', 'emergency_phone', 'medical_notes', 'club',
            'id_document_type', 'id_number', 'passport_number',
            'has_sa_passport', 'sa_passport_number', 'sa_passport_document', 'sa_passport_expiry_date',
            'safa_id', 'fifa_id', 'gender', 'date_of_birth', 'email',
            'profile_picture', 'id_document', 'popi_consent',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide gender and email, match ClubAdminPlayerRegistrationForm
        self.fields['gender'].widget = forms.HiddenInput()
        self.fields['email'].widget = forms.HiddenInput()
        self.fields['email'].required = False
        self.fields['date_of_birth'].required = False
        self.fields['safa_id'].required = False
        self.fields['safa_id'].help_text = "If the player already has a SAFA ID, enter it here. Otherwise, leave blank and it will be auto-generated."
        self.fields['safa_id'].widget.attrs.update({'pattern': '[A-Z0-9]{5}', 'title': '5-character alphanumeric code (all caps)', 'placeholder': 'e.g. A12B3'})
        self.fields['fifa_id'].required = False
        self.fields['fifa_id'].help_text = "If the player has a FIFA ID, enter it here. Otherwise, leave blank."
        self.fields['fifa_id'].widget.attrs.update({'pattern': '[0-9]{7}', 'title': '7-digit FIFA identification number', 'placeholder': 'e.g. 1234567'})
        self.fields['first_name'].widget.attrs.update({'pattern': '[A-Za-z]{3,}', 'minlength': '3', 'title': 'Only letters, at least 3 characters'})
        self.fields['last_name'].widget.attrs.update({'pattern': '[A-Za-z]{3,}', 'minlength': '3', 'title': 'Only letters, at least 3 characters'})
        self.fields['id_number'].widget.attrs.update({'pattern': '[0-9]{13}', 'inputmode': 'numeric', 'title': 'ID number must be exactly 13 digits'})
        self.fields['has_sa_passport'].initial = False
        self.fields['has_sa_passport'].help_text = "Optional: Check this if the player has a South African passport in addition to SA ID (for record purposes only)"
        self.fields['sa_passport_number'].required = False
        self.fields['sa_passport_number'].help_text = "Optional: Enter the South African passport number for record-keeping purposes"
        self.fields['sa_passport_document'].required = False
        self.fields['sa_passport_document'].help_text = "Optional: Upload a copy of the SA passport (PDF or image)"
        self.fields['sa_passport_expiry_date'].required = False
        self.fields['sa_passport_expiry_date'].help_text = "Optional: Enter the expiry date of the SA passport"
        self.fields['sa_passport_expiry_date'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'min': datetime.date.today().isoformat()})

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
        if id_number:
            if not re.match(r'^\d{13}$', id_number):
                errors['id_number'] = 'ID number must be exactly 13 digits'
        if not id_number and not passport_number:
            errors['id_number'] = 'Either ID number or passport number is required'
            errors['passport_number'] = 'Either ID number or passport number is required'
        # Add further validation as in ClubAdminPlayerRegistrationForm...
        if dob:
            age = (timezone.now().date() - dob).days // 365
            if age < 18 and not popi_consent:
                errors['popi_consent'] = 'POPI consent is required for players under 18'
        if id_number and Player.objects.filter(id_number=id_number).exists():
            errors['id_number'] = 'A player with this ID number already exists'
        if passport_number and Player.objects.filter(passport_number=passport_number).exists():
            errors['passport_number'] = 'A player with this passport number already exists'
        if sa_passport_number and Player.objects.filter(sa_passport_number=sa_passport_number).exists():
            errors['sa_passport_number'] = 'A player with this South African passport number already exists'
        if errors:
            raise ValidationError(errors)
        return cleaned_data