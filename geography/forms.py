# geography/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError, FieldDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
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


class LoginForm(forms.Form):
    """Form for user login"""
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


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
        # Make sure to only include fields that exist in the model
        fields = ['name', 'code', 'continent_region', 'description', 'logo']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name != 'logo':
                field.widget.attrs.update({'class': 'form-control'})

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
        fields = ['name', 'acronym', 'country', 'website', 'headquarters', 'description', 'logo']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name != 'logo':
                field.widget.attrs.update({'class': 'form-control'})

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
        fields = ['name', 'acronym', 'national_federation', 'logo']
        
        # Try to include additional fields if they exist in the model
        try:
            # Check if these fields exist in the model
            Association._meta.get_field('website')
            Association._meta.get_field('headquarters')
            Association._meta.get_field('description')
            # Add them to the form if they exist
            fields.extend(['website', 'headquarters', 'description'])
        except FieldDoesNotExist:
            pass
        
        # Define widgets for text fields
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name != 'logo':
                field.widget.attrs.update({'class': 'form-control'})

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
        fields = ['name', 'code', 'description']  # Removed 'logo'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name != 'logo':
                field.widget.attrs.update({'class': 'form-control'})

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
        fields = ['name', 'code', 'province', 'description', 'logo'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name != 'logo':
                field.widget.attrs.update({'class': 'form-control'})

class LocalFootballAssociationForm(forms.ModelForm):
    class Meta:
        model = LocalFootballAssociation
        fields = ['name', 'acronym', 'region', 'association', 'website', 'headquarters', 'description', 'logo']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name != 'logo':
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class ClubForm(forms.ModelForm):
    province = forms.ModelChoiceField(
        queryset=Province.objects.all().order_by('name'),
        required=False, 
        help_text=_("Select province first"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    region = forms.ModelChoiceField(
        queryset=Region.objects.none(),  # Initially empty
        required=False, 
        help_text=_("Select region after selecting province"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Club
        fields = [
            'name', 'code', 'status', 'province', 'region', 
            'localfootballassociation', 'founding_date', 'website', 
            'stadium', 'colors', 'description', 'logo'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'province': forms.Select(attrs={'class': 'form-select'}),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'localfootballassociation': forms.Select(attrs={'class': 'form-select'}),
            'founding_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'stadium': forms.TextInput(attrs={'class': 'form-control'}),
            'colors': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and getattr(user, 'role', None) == 'ADMIN_LOCAL_FED' and getattr(user, 'local_federation', None):
            lfa = user.local_federation
            self.fields['localfootballassociation'].queryset = LocalFootballAssociation.objects.filter(pk=lfa.pk)
            self.fields['localfootballassociation'].initial = lfa
            self.fields['region'].queryset = Region.objects.filter(pk=lfa.region.pk)
            self.fields['region'].initial = lfa.region
            self.fields['province'].queryset = Province.objects.filter(pk=lfa.region.province.pk)
            self.fields['province'].initial = lfa.region.province
            # Optionally, make these fields readonly or hidden
            self.fields['province'].widget.attrs['readonly'] = True
            self.fields['region'].widget.attrs['readonly'] = True
            self.fields['localfootballassociation'].widget.attrs['readonly'] = True
        else:
            # Superuser: normal cascading logic
            self.fields['region'].queryset = Region.objects.none()
            self.fields['localfootballassociation'].queryset = LocalFootballAssociation.objects.none()

            # Editing existing club
            if self.instance.pk and self.instance.localfootballassociation:
                lfa = self.instance.localfootballassociation
                self.fields['province'].initial = lfa.region.province
                self.fields['region'].queryset = Region.objects.filter(province=lfa.region.province)
                self.fields['region'].initial = lfa.region
                self.fields['localfootballassociation'].queryset = LocalFootballAssociation.objects.filter(region=lfa.region)
                self.fields['localfootballassociation'].initial = lfa

            # Bound form (POST)
            elif 'data' in kwargs:
                data = kwargs['data']
                province_id = data.get('province')
                region_id = data.get('region')
                if province_id:
                    self.fields['region'].queryset = Region.objects.filter(province_id=province_id)
                if region_id:
                    self.fields['localfootballassociation'].queryset = LocalFootballAssociation.objects.filter(region_id=region_id)

    def clean(self):
        cleaned_data = super().clean()
        province = cleaned_data.get('province')
        region = cleaned_data.get('region')
        lfa = cleaned_data.get('localfootballassociation')

        # Validate region belongs to province
        if province and region and region.province != province:
            self.add_error('region', 'Selected region does not belong to the selected province')
        
        # Validate LFA belongs to region
        if region and lfa and lfa.region != region:
            self.add_error('localfootballassociation', 'Selected LFA does not belong to the selected region')
        
        return cleaned_data

class ClubRegistrationForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['name', 'region', 'description', 'logo']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Restrict region choices to the user's region
        if user and user.role == 'ADMIN_LOCAL_FED':
            self.fields['region'].queryset = user.region_set.all()

        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

class ClubComplianceForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['logo', 'club_type', 'club_owner_type', 'club_documents']
        widgets = {
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'club_type': forms.Select(attrs={'class': 'form-select'}),
            'club_owner_type': forms.Select(attrs={'class': 'form-select'}),
            'club_documents': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'logo': 'Club Logo'
        }
        help_texts = {
            'logo': 'Upload a square image for best results (JPG or PNG format)'
        }

class ClubLogoForm(forms.ModelForm):
    """Form for editing a club's logo"""
    class Meta:
        model = Club
        fields = ['logo']
        labels = {
            'logo': 'Club Logo'
        }
        help_texts = {
            'logo': 'Upload a square image for best results (JPG or PNG format)'
        }

