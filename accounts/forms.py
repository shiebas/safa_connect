from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from geography.models import CustomUser, Club, Region, NationalFederation, Country, ROLES, DOCUMENT_TYPES

class UserRegistrationForm(UserCreationForm):
    """
    Form for registering new users including players, administrators, etc.
    """
    role = forms.ChoiceField(choices=ROLES, required=True, 
                            widget=forms.Select(attrs={'class': 'form-control'}))

    name = forms.CharField(max_length=50, required=True, 
                          widget=forms.TextInput(attrs={'class': 'form-control'}))

    middle_name = forms.CharField(max_length=100, required=False, 
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))

    surname = forms.CharField(max_length=100, required=True, 
                             widget=forms.TextInput(attrs={'class': 'form-control'}))

    email = forms.EmailField(required=True, 
                            widget=forms.EmailInput(attrs={'class': 'form-control'}))

    date_of_birth = forms.DateField(required=False, 
                                   widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')], required=False, 
                              widget=forms.Select(attrs={'class': 'form-control'}))

    id_number = forms.CharField(max_length=13, required=False, 
                               widget=forms.TextInput(attrs={'class': 'form-control', 'maxlength': '13'}))

    passport_number = forms.CharField(max_length=25, required=False, 
                                     widget=forms.TextInput(attrs={'class': 'form-control'}))

    id_document_type = forms.ChoiceField(choices=DOCUMENT_TYPES, required=True,
                                       widget=forms.RadioSelect(attrs={'class': 'form-check-input'}))

    document = forms.FileField(required=False,
                             widget=forms.FileInput(attrs={'class': 'form-control'}))

    # For club administrators and players
    club = forms.ModelChoiceField(queryset=Club.objects.all(), required=False, 
                                 widget=forms.Select(attrs={'class': 'form-control'}))

    # For regional administrators
    region = forms.ModelChoiceField(queryset=Region.objects.all(), required=False, 
                                   widget=forms.Select(attrs={'class': 'form-control'}))

    # For national administrators
    national_federation = forms.ModelChoiceField(queryset=NationalFederation.objects.all(), required=False, 
                                               widget=forms.Select(attrs={'class': 'form-control'}))

    # Country selection for ID validation
    country = forms.ModelChoiceField(queryset=Country.objects.all(), required=True,
                                   widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ('username', 'name', 'middle_name', 'surname', 'email', 'date_of_birth', 
                 'gender', 'role', 'country', 'id_document_type', 'id_number', 'passport_number', 
                 'document', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to the default fields
        for field_name in ['username', 'password1', 'password2']:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})

        # Make some fields conditionally required based on role
        self.fields['club'].required = False
        self.fields['region'].required = False
        self.fields['national_federation'].required = False

    def clean_id_number(self):
        """
        Validate ID number format and content based on country.
        Supports South Africa, Namibia, and Lesotho.
        """
        id_number = self.cleaned_data.get('id_number')

        # If ID number is not provided, return it (passport might be used instead)
        if not id_number:
            return id_number

        # Get the selected country
        country = self.cleaned_data.get('country')
        if not country:
            # If no country is selected, we can't validate the ID number
            return id_number

        # Remove any spaces or hyphens
        id_number = id_number.replace(' ', '').replace('-', '')

        # Use the helper method from CustomUser to validate and extract information
        from geography.models import CustomUser
        id_info = CustomUser.extract_id_info(id_number, country.fifa_code)

        if not id_info['is_valid']:
            raise forms.ValidationError(id_info['error'])

        # For South African IDs, we can validate gender and date of birth
        if country.fifa_code == 'ZAF':
            # Validate gender matches the one in the form
            form_gender = self.cleaned_data.get('gender')
            if form_gender and id_info['gender'] and form_gender != id_info['gender']:
                raise forms.ValidationError(
                    f"ID number gender doesn't match the selected gender ({form_gender})."
                )

            # Validate date of birth matches the one in the form
            form_dob = self.cleaned_data.get('date_of_birth')
            if form_dob and id_info['date_of_birth'] and form_dob != id_info['date_of_birth']:
                raise forms.ValidationError(
                    f"Date of birth in ID number ({id_info['date_of_birth'].strftime('%Y-%m-%d')}) "
                    f"doesn't match the provided date of birth ({form_dob.strftime('%Y-%m-%d')})."
                )

        return id_number

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')

        # Validate that appropriate organization is selected based on role
        if role == 'CLUB' and not cleaned_data.get('club'):
            self.add_error('club', 'Club is required for club managers')

        if role == 'ADMIN_COUNTRY' and not cleaned_data.get('national_federation'):
            self.add_error('national_federation', 'National federation is required for country administrators')

        # Validate document type and required fields
        id_document_type = cleaned_data.get('id_document_type')
        id_number = cleaned_data.get('id_number')
        passport_number = cleaned_data.get('passport_number')
        document = cleaned_data.get('document')
        country = cleaned_data.get('country')
        date_of_birth = cleaned_data.get('date_of_birth')
        gender = cleaned_data.get('gender')

        if id_document_type == 'ID':
            # National ID selected, require ID number
            if not id_number:
                self.add_error('id_number', 'ID number is required when National ID is selected')
        elif id_document_type == 'PP':
            # Passport selected, require passport number and document
            if not passport_number:
                self.add_error('passport_number', 'Passport number is required when Passport is selected')
            if not document:
                self.add_error('document', 'Passport copy is required when Passport is selected')

            # When using passport, date of birth and gender are required
            if not date_of_birth:
                self.add_error('date_of_birth', 'Date of birth is required when using passport')
            if not gender:
                self.add_error('gender', 'Gender is required when using passport')
        else:
            # Other document type, at least one of ID or passport should be provided
            if not id_number and not passport_number:
                self.add_error('id_number', 'Either ID number or passport number is required')

            # For other document types, date of birth and gender are required
            if not date_of_birth:
                self.add_error('date_of_birth', 'Date of birth is required')
            if not gender:
                self.add_error('gender', 'Gender is required')

        # Auto-populate date of birth and gender from ID number if country and ID number are provided
        if id_number and country and id_document_type == 'ID':
            # Remove any spaces or hyphens
            id_number = id_number.replace(' ', '').replace('-', '')

            # Get ID info based on country
            from geography.models import CustomUser
            id_info = CustomUser.extract_id_info(id_number, country.fifa_code)

            if id_info['is_valid']:
                # Auto-populate date of birth if available from ID
                if id_info['date_of_birth']:
                    # Set date of birth in cleaned_data
                    cleaned_data['date_of_birth'] = id_info['date_of_birth']

                    # Also update the form field value for display
                    self.data = self.data.copy()  # Make mutable
                    self.data['date_of_birth'] = id_info['date_of_birth'].strftime('%Y-%m-%d')

                # Auto-populate gender if available from ID
                if id_info['gender']:
                    # Set gender in cleaned_data
                    cleaned_data['gender'] = id_info['gender']

                    # Also update the form field value for display
                    self.data = self.data.copy()  # Make mutable
                    self.data['gender'] = id_info['gender']

        return cleaned_data
