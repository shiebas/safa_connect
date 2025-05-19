# geography/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import (
    CustomUser,
    Membership,
    Country,
    Province,
    Region,
    Club,
    Association,
    NationalFederation
)

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
