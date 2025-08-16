# membership/forms.py
from django import forms
from .models import Member
from accounts.models import CustomUser, ROLES

class BaseRegistrationForm(forms.ModelForm):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)

    class Meta:
        model = Member
        exclude = ['user']

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = CustomUser.objects.create_user(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            role=self.role
        )
        member = super().save(commit=False)
        member.user = user
        if commit:
            member.save()
        return member

class PlayerRegistrationForm(BaseRegistrationForm):
    role = 'PLAYER'

class OfficialRegistrationForm(BaseRegistrationForm):
    role = 'OFFICIAL'

class AdminRegistrationForm(BaseRegistrationForm):
    role = forms.ChoiceField(choices=ROLES)

from .models import Transfer, Member
from geography.models import Club

class TransferRequestForm(forms.ModelForm):
    member = forms.ModelChoiceField(queryset=Member.objects.filter(status='ACTIVE', role='PLAYER'))
    to_club = forms.ModelChoiceField(queryset=Club.objects.filter(is_active=True))

    class Meta:
        model = Transfer
        fields = ['member', 'to_club', 'reason', 'transfer_fee']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and not self.user.is_superuser:
            # Limit members to the user's club if they are a club admin
            if hasattr(self.user, 'member_profile') and self.user.member_profile.current_club:
                self.fields['member'].queryset = Member.objects.filter(
                    current_club=self.user.member_profile.current_club,
                    status='ACTIVE',
                    role='PLAYER'
                )

    def clean(self):
        cleaned_data = super().clean()
        member = cleaned_data.get('member')
        to_club = cleaned_data.get('to_club')

        if member and to_club:
            if member.current_club == to_club:
                raise forms.ValidationError("A player cannot be transferred to their current club.")
        return cleaned_data
