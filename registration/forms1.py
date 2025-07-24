from django import forms
from django.db import transaction
from django.utils import timezone
from .models import Player, PlayerClubRegistration
from membership.models import Invoice, InvoiceItem
from accounts.utils import generate_unique_safa_id, create_player_invoice, validate_sa_id_number
import datetime
from django.contrib import messages


class SeniorMemberRegistrationForm(forms.ModelForm):
    REGISTRATION_CHOICES = [
        ('MEMBER', 'Register as a General Member'),
        ('PLAYER', 'Register as a Player for a Club'),
    ]
    registration_as = forms.ChoiceField(
        choices=REGISTRATION_CHOICES,
        widget=forms.RadioSelect,
        initial='MEMBER',
        label="How would you like to register?"
    )

    class Meta:
        model = Player
        fields = ['registration_as', 'first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'gender', 'id_number', 'passport_number', 'street_address', 'suburb', 'city', 'state', 'postal_code', 'country', 'province', 'region', 'lfa', 'club', 'association']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['club'].required = False # Not required by default

    def clean(self):
        cleaned_data = super().clean()
        registration_as = cleaned_data.get('registration_as')
        club = cleaned_data.get('club')

        if registration_as == 'PLAYER' and not club:
            self.add_error('club', "You must select a club to register as a player.")
        
        return cleaned_data


class ClubAdminPlayerRegistrationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.invoice = None

        # Set up widgets and field properties
        self.fields['date_of_birth'].widget = forms.DateInput(attrs={'type': 'date'})
        
        # Email is not required, will be auto-generated if empty
        self.fields['email'].required = False
        
        # DOB and Gender are not required initially, they depend on ID/Passport
        self.fields['date_of_birth'].required = False
        self.fields['gender'].required = False

    class Meta:
        model = Player
        # Using the same fields as SeniorMemberRegistrationForm for consistency
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'gender', 'id_number', 'passport_number', 'street_address', 'suburb', 'city', 'state', 'postal_code', 'country', 'province', 'region', 'lfa', 'club', 'association', 'profile_picture', 'id_document']
        widgets = {
            'gender': forms.RadioSelect,
        }

    def clean(self):
        cleaned_data = super().clean()
        id_number = cleaned_data.get('id_number')
        passport_number = cleaned_data.get('passport_number')

        if not id_number and not passport_number:
            raise forms.ValidationError("Either an ID number or a passport number must be provided.")

        # If an ID number is provided, we prioritize it for validation and data extraction.
        if id_number:
            validation_result = validate_sa_id_number(id_number)
            if not validation_result['is_valid']:
                self.add_error('id_number', validation_result['error_message'] or "Invalid South African ID number.")
            else:
                # Overwrite DOB and Gender with data from the valid ID.
                cleaned_data['date_of_birth'] = validation_result.get('date_of_birth')
                cleaned_data['gender'] = validation_result.get('gender')
        
        # If no ID number is provided, passport must be, and we need DOB and Gender.
        elif not id_number:
            date_of_birth = cleaned_data.get('date_of_birth')
            gender = cleaned_data.get('gender')
            if not date_of_birth:
                self.add_error('date_of_birth', "Date of birth is required when using a passport.")
            if not gender:
                self.add_error('gender', "Gender is required when using a passport.")
        
        return cleaned_data

    def save(self, commit=True):
        player = super().save(commit=False)
        
        # Populate player's details from the club admin's user
        if self.request and self.request.user.is_authenticated and hasattr(self.request.user, 'club'):
            club = self.request.user.club
            if club:
                player.club = club
                if club.localfootballassociation:
                    player.lfa = club.localfootballassociation
                    if club.localfootballassociation.region:
                        player.region = club.localfootballassociation.region
                        if club.localfootballassociation.region.province:
                            player.province = club.localfootballassociation.region.province

        # Generate email if it wasn't provided
        if not player.email:
            from accounts.views import generate_unique_player_email
            player.email = generate_unique_player_email(player.first_name, player.last_name)

        if not player.safa_id:
            player.safa_id = generate_unique_safa_id()

        if commit:
            with transaction.atomic():
                player.save()

                club_for_registration = player.club or (self.request.user.club if self.request else None)

                if club_for_registration:
                    PlayerClubRegistration.objects.create(
                        player=player,
                        club=club_for_registration,
                        status='PENDING'
                    )
                    # Calculate age to determine if the player is a junior
                    today = timezone.now().date()
                    age = today.year - player.date_of_birth.year - ((today.month, today.day) < (player.date_of_birth.month, player.date_of_birth.day))
                    
                    self.invoice = create_player_invoice(
                        player=player,
                        club=club_for_registration,
                        issued_by=self.request.user,
                        is_junior=age < 18
                    )
                elif self.request:
                    messages.error(self.request, "Could not create invoice because the player is not associated with a club.")

        return player
