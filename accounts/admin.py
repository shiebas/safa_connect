import collections
import sys

# Fix for collections.Iterator removed in Python 3.10
if sys.version_info >= (3, 10) and not hasattr(collections, 'Iterator'):
    collections.Iterator = collections.abc.Iterator

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    # Custom fields for list view
    list_display = ('email', 'name', 'surname', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'name', 'surname', 'id_number', 'passport_number')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'surname', 'date_of_birth', 'gender')}),
        ('Authentication', {'fields': ('role', 'id_document_type', 'id_number', 
                                      'passport_number', 'document')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'name', 'surname', 'role', 'is_staff', 'is_active'),
        }),
    )
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)
