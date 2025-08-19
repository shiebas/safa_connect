from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        if request.user.is_superuser:
            return reverse('superuser_dashboard')
        else:
            return reverse('accounts:profile')
