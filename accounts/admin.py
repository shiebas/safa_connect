import collections
import sys

# Fix for collections.Iterator removed in Python 3.10
if sys.version_info >= (3, 10) and not hasattr(collections, 'Iterator'):
    collections.Iterator = collections.abc.Iterator

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django import forms
from django.contrib.admin.forms import AdminPasswordChangeForm
from .models import CustomUser

# Properly import Province directly
try:
    from geography.models import Province
    PROVINCE_QUERYSET = Province.objects.all()
except (ImportError, RuntimeError):
    from django.db.models.query import EmptyQuerySet
    PROVINCE_QUERYSET = EmptyQuerySet()

# Create a custom ModelForm specifically for admin use
class CustomUserAdminForm(forms.ModelForm):
    # Add a ModelChoiceField for province that maps to province_id - fix the queryset issue
    province = forms.ModelChoiceField(
        queryset=PROVINCE_QUERYSET,
        required=False,
        label="Province"
    )
    
    class Meta:
        model = CustomUser
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If we're editing an existing user, set the province field value
        if self.instance and self.instance.pk and self.instance.province_id:
            try:
                province = Province.objects.get(pk=self.instance.province_id)
                self.initial['province'] = province
            except:
                pass

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Map the province field to province_id when saving
        if 'province' in self.cleaned_data and self.cleaned_data['province']:
            user.province_id = self.cleaned_data['province'].id
            
        if commit:
            user.save()
            
        return user

# Custom admin class
class CustomUserAdmin(UserAdmin):
    form = CustomUserAdminForm
    
    # Update fieldsets to use the province field we added
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'middle_name', 'surname', 'alias', 
                                     'date_of_birth', 'gender', 'role')}),
        ('Identification', {'fields': ('id_document_type', 'id_number', 'id_number_other', 
                                      'passport_number', 'id_document')}),
        ('Status', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        # Change from 'province_id' to 'province' here:
        ('Admin Roles', {'fields': ('province', 'region_id', 'local_federation_id', 'club_id')}),
        ('Media', {'fields': ('profile_photo', 'logo')}),
    )
    
    # Fields for adding new users
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'name', 'surname', 'role'),
        }),
    )
    
    list_display = ('email', 'name', 'surname', 'role', 'is_active')
    list_filter = ('is_active', 'role')
    search_fields = ('email', 'name', 'surname')
    ordering = ('email',)

# Register the model with our custom admin
admin.site.register(CustomUser, CustomUserAdmin)
