from django import forms
from .models import Province, Region, LocalFootballAssociation, Association, Club, Continent, ContinentFederation, ContinentRegion, Country, NationalFederation, WorldSportsBody

class ProvinceComplianceForm(forms.ModelForm):
    class Meta:
        model = Province
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass # Handled by custom widget attrs
            else:
                field.widget.attrs.update({'class': 'form-control'})


class RegionComplianceForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs.update({'class': 'form-control'})


class LFAComplianceForm(forms.ModelForm):
    class Meta:
        model = LocalFootballAssociation
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs.update({'class': 'form-control'})


class AssociationComplianceForm(forms.ModelForm):
    class Meta:
        model = Association
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs.update({'class': 'form-control'})


class ClubComplianceForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs.update({'class': 'form-control'})


class AssociationForm(forms.ModelForm):
    class Meta:
        model = Association
        fields = '__all__'


class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = '__all__'


class ContinentFederationForm(forms.ModelForm):
    class Meta:
        model = ContinentFederation
        fields = '__all__'


class ContinentRegionForm(forms.ModelForm):
    class Meta:
        model = ContinentRegion
        fields = '__all__'


class CountryForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = '__all__'


class LocalFootballAssociationForm(forms.ModelForm):
    class Meta:
        model = LocalFootballAssociation
        fields = '__all__'


class NationalFederationForm(forms.ModelForm):
    class Meta:
        model = NationalFederation
        fields = '__all__'


from django import forms
from .models import Province, Region, LocalFootballAssociation, Association, Club, Continent, ContinentFederation, ContinentRegion, Country, NationalFederation, WorldSportsBody
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

class ProvinceComplianceForm(forms.ModelForm):
    class Meta:
        model = Province
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass # Handled by custom widget attrs
            else:
                field.widget.attrs.update({'class': 'form-control'})


class RegionComplianceForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs.update({'class': 'form-control'})


class LFAComplianceForm(forms.ModelForm):
    class Meta:
        model = LocalFootballAssociation
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs.update({'class': 'form-control'})


class AssociationComplianceForm(forms.ModelForm):
    class Meta:
        model = Association
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs.update({'class': 'form-control'})


class ClubComplianceForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs.update({'class': 'form-control'})


class AssociationForm(forms.ModelForm):
    class Meta:
        model = Association
        fields = '__all__'


class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = '__all__'


class ContinentFederationForm(forms.ModelForm):
    class Meta:
        model = ContinentFederation
        fields = '__all__'


class ContinentRegionForm(forms.ModelForm):
    class Meta:
        model = ContinentRegion
        fields = '__all__'


class CountryForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = '__all__'


class LocalFootballAssociationForm(forms.ModelForm):
    class Meta:
        model = LocalFootballAssociation
        fields = '__all__'


class NationalFederationForm(forms.ModelForm):
    class Meta:
        model = NationalFederation
        fields = '__all__'


class ProvinceForm(forms.ModelForm):
    class Meta:
        model = Province
        fields = [
            'name',
            'code',
            'national_federation',
            'description',
            'status',
            'safa_id',
            'fifa_id',
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
            'compliance_verified_date',
        ]
        widgets = {
            'compliance_verified_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'name',
            'code',
            'national_federation',
            'description',
            'status',
            'safa_id',
            'fifa_id',
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
            'compliance_verified_date',
            Submit('submit', 'Save Changes', css_class='btn-primary')
        )
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class RegionForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = '__all__'


class WorldSportsBodyForm(forms.ModelForm):
    class Meta:
        model = WorldSportsBody
        fields = '__all__'


class ClubRegistrationForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = '__all__'


class ClubLogoForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['logo']


class RegionComplianceForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs.update({'class': 'form-control'})


class LFAComplianceForm(forms.ModelForm):
    class Meta:
        model = LocalFootballAssociation
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs.update({'class': 'form-control'})


class AssociationComplianceForm(forms.ModelForm):
    class Meta:
        model = Association
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs.update({'class': 'form-control'})


class ClubComplianceForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs.update({'class': 'form-control'})


class RegionForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = '__all__'


class WorldSportsBodyForm(forms.ModelForm):
    class Meta:
        model = WorldSportsBody
        fields = '__all__'


class ClubRegistrationForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = '__all__'


class ClubLogoForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['logo']


class RegionComplianceForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs.update({'class': 'form-control'})


class LFAComplianceForm(forms.ModelForm):
    class Meta:
        model = LocalFootballAssociation
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs.update({'class': 'form-control'})


class AssociationComplianceForm(forms.ModelForm):
    class Meta:
        model = Association
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs.update({'class': 'form-control'})


class ClubComplianceForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = [
            'constitution_document',
            'minutes_of_agm_document',
            'financial_statements_document',
            'is_compliant',
        ]
        widgets = {
            'is_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control-file'})
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs.update({'class': 'form-control'})