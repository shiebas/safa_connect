# geography/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser
from .models import (
    Continent,
    Country,
    Province,
    Region,
    Club,
    Association,
    NationalFederation,
    WorldSportsBody,
    ContinentFederation,
    ContinentRegion,
    LocalFootballAssociation,
    SPORT_CODES
)
import re
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from crispy_forms.bootstrap import FormActions

class RegistrationForm(UserCreationForm):
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
        fields = ['email', 'name', 'middle_name', 'surname',
                  'date_of_birth', 'gender',
                  'id_document_type', 'id_number', 'passport_number',
                  'profile_photo']

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
                  'date_of_birth', 'gender',
                  'id_document_type', 'id_number', 'passport_number',
                  'profile_photo']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class WorldSportsBodyForm(forms.ModelForm):
    continents = forms.ModelMultipleChoiceField(
        queryset=Continent.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=_('Select continents where this body operates')
    )
    
    class Meta:
        model = WorldSportsBody
        fields = ['name', 'acronym', 'logo', 'website', 'headquarters', 'description', 'sport_code']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            if field_name != 'continents' and field_name != 'logo':
                field.widget.attrs.update({'class': 'form-control'})
        
        # If we're editing an existing instance, populate continents
        if self.instance.pk:
            self.fields['continents'].initial = self.instance.continents.all()
    
    def save(self, commit=True):
        world_body = super().save(commit=commit)
        
        if commit:
            # Update continent relationships
            continents = self.cleaned_data.get('continents', [])
            # Update only the continents that are in the form data
            for continent in Continent.objects.filter(world_sports_body=world_body):
                if continent not in continents:
                    continent.world_sports_body = None
                    continent.save()
            
            for continent in continents:
                continent.world_sports_body = world_body
                continent.save()
                
        return world_body
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
        fields = ['name', 'code', 'continent', 'description', 'logo']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name != 'logo':
                field.widget.attrs.update({'class': 'form-control'})

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
            "province_type",
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

class LocalFootballAssociationForm(forms.ModelForm):
    class Meta:
        model = LocalFootballAssociation
        fields = [
            "name",
            "acronym",
            "region",
            "contact_email",
            "contact_phone",
            "website",
            "logo",
        ]

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class ClubForm(forms.ModelForm):
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        required=False,
        empty_label="Select province"
    )

    class Meta:
        model = Club
        fields = [
            "name",
            "province",
            "region",
            "local_football_association",  # <-- add this line!
            "founded_year",
            
            
        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initially set region queryset to empty
        self.fields['region'].queryset = Region.objects.none()

        # If editing an existing club, initialize the province field
        if 'instance' in kwargs and kwargs['instance'] and kwargs['instance'].region:
            instance = kwargs['instance']
            region = instance.region
            province = region.province

            # Set the province field
            self.fields['province'].initial = province

            # Update the region queryset based on the province
            self.fields['region'].queryset = Region.objects.filter(province=province)

        # If province is provided in POST data, filter regions
        if 'data' in kwargs and kwargs['data'].get('province'):
            try:
                province_id = int(kwargs['data'].get('province'))
                self.fields['region'].queryset = Region.objects.filter(province_id=province_id)
            except (ValueError, TypeError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        short_name = cleaned_data.get("short_name")
        region = cleaned_data.get("region")
        province = cleaned_data.get("province")

        # Ensure province is selected
        if not province:
            self.add_error("province", "Please select a province.")

        # Ensure region is selected and belongs to the selected province
        if region and province and region.province != province:
            self.add_error("region", "The selected region does not belong to the selected province.")

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
         

        return cleaned_data

