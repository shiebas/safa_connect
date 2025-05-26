# geography/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import (
    CustomUser,
    Continent,
    Membership,
    Country,
    Province,
    Region,
    Club,
    Association,
    NationalFederation,
    WorldSportsBody,
    ContinentFederation,
    ContinentRegion,
    SPORT_CODES
)
import re
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from crispy_forms.bootstrap import FormActions

class RegistrationForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField(required=True)

    # Personal information
    name = forms.CharField(max_length=50, required=True)
    surname = forms.CharField(max_length=100, required=True)
    middle_name = forms.CharField(max_length=100, required=False)
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    gender = forms.ChoiceField(choices=[('', 'Select gender')] + list(CustomUser._meta.get_field('gender').choices), required=True)

    # Identification
    id_document_type = forms.ChoiceField(
        choices=CustomUser._meta.get_field('id_document_type').choices,
        required=True
    )
    id_number = forms.CharField(max_length=20, required=False)
    passport_number = forms.CharField(max_length=25, required=False)

    # Location
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=True,
        empty_label="Select country"
    )

    # Profile photo
    profile_photo = forms.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'name', 'middle_name', 'surname', 
                  'date_of_birth', 'gender', 'country', 
                  'id_document_type', 'id_number', 'passport_number',
                  'profile_photo', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        id_document_type = cleaned_data.get('id_document_type')
        id_number = cleaned_data.get('id_number')
        passport_number = cleaned_data.get('passport_number')

        # Validate identification based on document type
        if id_document_type == 'PP' and not passport_number:
            self.add_error('passport_number', 'Passport number is required when document type is Passport')
        elif id_document_type in ['ID', 'BC', 'DL'] and not id_number:
            self.add_error('id_number', 'ID number is required for this document type')

        return cleaned_data

class LoginForm(forms.Form):
    """Form for user login"""
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class ProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'middle_name', 'surname', 'alias',
                  'date_of_birth', 'gender', 'country',
                  'id_document_type', 'id_number', 'passport_number',
                  'profile_photo']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class MembershipForm(forms.ModelForm):
    """Form for creating/updating memberships"""
    membership_type = forms.ChoiceField(
        choices=[
            ('club', _('Club')),
            ('association', _('Association')),
            ('national_federation', _('National Federation'))
        ],
        required=True
    )

    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=False,
        empty_label="Select country"
    )

    province = forms.ModelChoiceField(
        queryset=Province.objects.none(),
        required=False,
        empty_label="Select province"
    )

    region = forms.ModelChoiceField(
        queryset=Region.objects.none(),
        required=False,
        empty_label="Select region"
    )

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )

    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )

    class Meta:
        model = Membership
        fields = ['membership_type', 'club', 'association', 'national_federation',
                  'start_date', 'end_date', 'is_active',
                  'player_category', 'jersey_number', 'position']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'position': forms.TextInput(attrs={'placeholder': 'e.g., Striker, Goalkeeper'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initially make these fields not required as they'll be conditionally required
        self.fields['club'].required = False
        self.fields['association'].required = False
        self.fields['national_federation'].required = False

        # If editing an existing membership, initialize the hierarchical fields
        if 'instance' in kwargs and kwargs['instance']:
            instance = kwargs['instance']

            if instance.club:
                self.fields['membership_type'].initial = 'club'
                # Set up the hierarchy
                region = instance.club.region
                province = region.province
                country = province.country

                # Update querysets
                self.fields['country'].initial = country
                self.fields['province'].queryset = Province.objects.filter(country=country)
                self.fields['province'].initial = province
                self.fields['region'].queryset = Region.objects.filter(province=province)
                self.fields['region'].initial = region
                self.fields['club'].queryset = Club.objects.filter(region=region)

            elif instance.association:
                self.fields['membership_type'].initial = 'association'
                country = instance.association.national_federation.country
                self.fields['country'].initial = country
                self.fields['national_federation'].queryset = NationalFederation.objects.filter(country=country)
                self.fields['association'].queryset = Association.objects.filter(
                    national_federation=instance.association.national_federation
                )

            elif instance.national_federation:
                self.fields['membership_type'].initial = 'national_federation'
                self.fields['country'].initial = instance.national_federation.country
                self.fields['national_federation'].queryset = NationalFederation.objects.filter(
                    country=instance.national_federation.country
                )

    def clean(self):
        cleaned_data = super().clean()
        membership_type = cleaned_data.get('membership_type')
        club = cleaned_data.get('club')
        association = cleaned_data.get('association')
        national_federation = cleaned_data.get('national_federation')

        # Validate the selected organization matches the membership type
        if membership_type == 'club' and not club:
            self.add_error('club', 'Please select a club for club membership')
        elif membership_type == 'association' and not association:
            self.add_error('association', 'Please select an association for association membership')
        elif membership_type == 'national_federation' and not national_federation:
            self.add_error('national_federation', 'Please select a national federation for federation membership')

        # Make sure only one organization is selected
        selections = [bool(club), bool(association), bool(national_federation)]
        if sum(selections) > 1:
            self.add_error('membership_type', 'Please select only one organization type')

        return cleaned_data

class WorldSportsBodyForm(forms.ModelForm):
    class Meta:
        model = WorldSportsBody
        fields = ['name', 'acronym', 'sport_code', 'description', 'website', 'logo', 'continents']
        widgets = {
            'continents': forms.CheckboxSelectMultiple,
        }
def clean_logo(self):
        logo = self.cleaned_data.get('logo', False)
        if logo:
            # Check file size (e.g., max 2MB)
            if logo.size > 2 * 1024 * 1024: # 2MB
                raise ValidationError(_("Image file is too large (max 2MB). Please upload a smaller file."))

            # Check content type
            allowed_content_types = ['image/jpeg', 'image/png', 'image/gif']
            if logo.content_type not in allowed_content_types:
                raise ValidationError(_("Invalid file type. Only JPEG, PNG, and GIF images are allowed."))

            # Optional: For more advanced image validation like dimensions, you can use the Pillow library.
            # from PIL import Image
            # try:
            #     img = Image.open(logo)
            #     img.verify() # Verifies that it is, in fact an image
            #     # Example: Check dimensions
            #     # if img.width > 800 or img.height > 600:
            #     #     raise ValidationError(_("Image dimensions are too large (max 800x600px)."))
            # except Exception as e: # Catch more specific exceptions if possible
            #     raise ValidationError(_("Invalid image file: %(error)s", params={'error': str(e)}))
        return logo

class ContinentFederationForm(forms.ModelForm):
    class Meta:
        model = ContinentFederation
        fields = [
            "name",
            "acronym",
            "continent",
            "sport_code",
            "description",
            "website",
            "logo",
        ]

    def clean(self):
        cleaned_data = super().clean()
        continent = cleaned_data.get('continent')
        sport_code = cleaned_data.get('sport_code')
        if continent and sport_code:
            qs = ContinentFederation.objects.filter(continent=continent, sport_code=sport_code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "A federation for this continent and sport code already exists."
                )
        return cleaned_data

class ContinentRegionForm(forms.ModelForm):
    class Meta:
        model = ContinentRegion
        fields = [
            "name",
            "acronym",
            "continent_federation",
            "description",
            "website",
            "logo",
        ]

    def clean(self):
        cleaned_data = super().clean()
        acronym = cleaned_data.get("acronym")
        continent_federation = cleaned_data.get("continent_federation")
        qs = ContinentRegion.objects.filter(acronym=acronym, continent_federation=continent_federation)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This acronym is already used for this federation.")
        return cleaned_data

class CountryForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = [
            "name",
            "fifa_code",
            "association_acronym",
            "continent_region",
            "is_default",
            "logo",
        ]

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        fifa_code = cleaned_data.get("fifa_code")
        # Ensure FIFA code is unique (database already enforces, but for user-friendly error)
        qs = Country.objects.filter(fifa_code=fifa_code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            self.add_error("fifa_code", "This FIFA code is already used by another country.")

        # You could also enforce only one default country, but your model's save() already does this
        # If you want to warn in the form:
        is_default = cleaned_data.get("is_default")
        if is_default:
            qs_default = Country.objects.filter(is_default=True)
            if self.instance.pk:
                qs_default = qs_default.exclude(pk=self.instance.pk)
            if qs_default.exists():
                raise forms.ValidationError(
                    "There is already a default country. Saving this will replace the previous default."
                )

        return cleaned_data

class NationalFederationForm(forms.ModelForm):
    class Meta:
        model = NationalFederation
        fields = [
            "name",
            "acronym",
            "country",
            "world_body",
            "description",
            "website",
            "logo",
        ]

    def clean(self):
        cleaned_data = super().clean()
        country = cleaned_data.get("country")
        world_body = cleaned_data.get("world_body")

        # Check for unique constraint on country and world_body
        if country and world_body:
            qs = NationalFederation.objects.filter(country=country, world_body=world_body)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "A federation for this country and world sports body already exists."
                )

        return cleaned_data

class AssociationForm(forms.ModelForm):
    class Meta:
        model = Association
        fields = [
            "name",
            "acronym",
            "national_federation",
            "association_type",
            "description",
            "logo",
        ]

    def clean(self):
        cleaned_data = super().clean()
        acronym = cleaned_data.get("acronym")
        national_federation = cleaned_data.get("national_federation")

        # Check for unique constraint on acronym and national_federation
        if acronym and national_federation:
            qs = Association.objects.filter(acronym=acronym, national_federation=national_federation)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "An association with this acronym already exists for this national federation."
                )

        return cleaned_data

class ProvinceForm(forms.ModelForm):
    class Meta:
        model = Province
        fields = [
            "name",
            "code",
            "country",
            "logo",
        ]

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get("code")
        country = cleaned_data.get("country")

        # Check for unique constraint on code and country
        if code and country:
            qs = Province.objects.filter(code=code, country=country)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "A province with this code already exists for this country."
                )

        return cleaned_data

class RegionForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = [
            "name",
            "code",
            "province",
            "national_federation",
            "logo",
        ]

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get("code")
        province = cleaned_data.get("province")
        national_federation = cleaned_data.get("national_federation")

        # Check for unique constraint on code, province, and national_federation
        if code and province and national_federation:
            qs = Region.objects.filter(code=code, province=province, national_federation=national_federation)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "A region with this code already exists for this province and national federation."
                )

        return cleaned_data

class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = [
            "name",
            "short_name",
            "region",
            "founded_year",
            "home_ground",
            "club_colors",
            "logo",
        ]

    def clean(self):
        cleaned_data = super().clean()
        short_name = cleaned_data.get("short_name")
        region = cleaned_data.get("region")

        # Check for unique constraint on short_name and region
        if short_name and region:
            qs = Club.objects.filter(short_name=short_name, region=region)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "A club with this short name already exists for this region."
                )

        return cleaned_data
