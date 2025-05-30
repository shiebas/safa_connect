from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Member, Membership, Player, Transfer, TransferAppeal
from geography.models import (
    Country, Province, Region, Club,
    NationalFederation, Association, LocalFootballAssociation
)

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
        ('JR', 'Junior (R100)'),
        ('SR', 'Senior (R200)'),
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
            'short_name',
            'code',
            'email',
            'phone',
            'address',
            'founded_year',
            'region',  # Use region instead of province
            'local_football_association',
            'logo'
        ]
        widgets = {
            'founded_year': forms.NumberInput(attrs={'min': 1800, 'max': 9999}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If you need to filter regions or LFAs, do it here
        if 'region' in self.fields:
            self.fields['region'].queryset = Region.objects.all().select_related('province')
        if 'local_football_association' in self.fields:
            self.fields['local_football_association'].queryset = LocalFootballAssociation.objects.all().select_related('region')