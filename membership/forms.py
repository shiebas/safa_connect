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
