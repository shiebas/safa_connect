class SAFASeasonConfigForm(forms.ModelForm):
    class Meta:
        model = SAFASeasonConfig
        fields = [
            'season_year', 'season_start_date', 'season_end_date',
            'organization_registration_start', 'organization_registration_end',
            'member_registration_start', 'member_registration_end',
            'vat_rate', 'payment_due_days', 'is_active', 'is_renewal_season'
        ]
        widgets = {
            'season_start_date': forms.DateInput(attrs={'type': 'date'}),
            'season_end_date': forms.DateInput(attrs={'type': 'date'}),
            'organization_registration_start': forms.DateInput(attrs={'type': 'date'}),
            'organization_registration_end': forms.DateInput(attrs={'type': 'date'}),
            'member_registration_start': forms.DateInput(attrs={'type': 'date'}),
            'member_registration_end': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-check-input'})


class SAFAFeeStructureForm(forms.ModelForm):
    class Meta:
        model = SAFAFeeStructure
        fields = [
            'season_config', 'entity_type', 'annual_fee', 'minimum_fee',
            'is_pro_rata', 'description'
        ]
        widgets = {
            'annual_fee': forms.NumberInput(attrs={'step': '0.01'}),
            'minimum_fee': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-check-input'})