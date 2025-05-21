from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.http import HttpResponse 

class WorkingLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = False  # Simpler setup
    success_url = reverse_lazy('admin:index') 

def working_home(request):
    return HttpResponse("CONFIRMED WORKING - LOGIN SUCCESS")
