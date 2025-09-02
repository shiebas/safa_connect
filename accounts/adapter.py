from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        if request.user.is_superuser:
            return reverse('superuser_dashboard')
        elif request.user.role == 'ADMIN_NATIONAL':
            return reverse('accounts:national_admin_dashboard')
        elif request.user.role == 'ADMIN_PROVINCE':
            return reverse('accounts:provincial_admin_dashboard')
        elif request.user.role == 'ADMIN_REGION':
            return reverse('accounts:regional_admin_dashboard')
        elif request.user.role == 'ADMIN_LOCAL_FED':
            return reverse('accounts:lfa_admin_dashboard')
        elif request.user.role == 'CLUB_ADMIN':
            return reverse('accounts:club_admin_dashboard')
        elif request.user.role == 'ASSOCIATION_ADMIN':
            return reverse('accounts:association_admin_dashboard')
        else:
            return reverse('accounts:profile')
