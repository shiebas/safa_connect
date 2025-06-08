from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import UserRegistrationForm
from .models import CustomUser
from membership.models import Membership  # Import Membership from the correct location
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import models
from django.shortcuts import get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.crypto import get_random_string

class WorkingLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = False  # Simpler setup
    success_url = reverse_lazy('admin:index') 

def working_home(request):
    return HttpResponse("CONFIRMED WORKING - LOGIN SUCCESS")

def register(request):
    """
    View for handling user registration including players, administrators, etc.
    """
    if request.method == 'POST':
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # This is probably calling the form's save method which checks 'province'
            user = form.save()

            # Set user as inactive until approved by an admin
            user.is_active = False

            # Set document type and handle file upload
            user.id_document_type = form.cleaned_data.get('id_document_type')
            if form.cleaned_data.get('id_document'):  # Change 'document' to 'id_document' 
                user.id_document = form.cleaned_data.get('id_document')

            # Handle administrative relationships based on role
            if user.role == 'ADMIN_PROVINCE':
                user.province = form.cleaned_data.get('province')
            elif user.role == 'ADMIN_REGION':
                user.region = form.cleaned_data.get('region')
            elif user.role == 'ADMIN_LOCAL_FED':
                user.local_federation = form.cleaned_data.get('local_federation')
                
            user.save()

            # Create membership if club is selected
            if form.cleaned_data.get('club'):
                Membership.objects.create(
                    member=user,  # Changed from user to member as per membership model
                    club=form.cleaned_data.get('club'),
                    start_date=user.date_joined.date(),
                    status='INACTIVE'  # Use the status field instead of is_active
                )

            # Display success message
            messages.success(request, 'Registration successful! Your account is pending approval.')
            return redirect('accounts:login')
        else:
            # Debug form errors
            print("Form errors:", form.errors)
            print("Province field value:", request.POST.get('province'))

            # Check if province field has a queryset before trying to access it
            if hasattr(form.fields['province'], 'queryset'):
                print("Province field choices:", [(p.id, str(p)) for p in form.fields['province'].queryset])
            else:
                print("Province field doesn't have a queryset - it's type:", type(form.fields['province']))
            # Make sure these errors are displayed in template
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})

def check_username(request):
    """
    AJAX view to check if a username is available.
    Returns JSON response with available: true/false.
    """
    username = request.GET.get('username', '')
    if not username:
        return JsonResponse({'available': False})

    # Check if the username exists
    exists = CustomUser.objects.filter(username=username).exists()

    return JsonResponse({'available': not exists})

def check_email_exists(request):
    email = request.GET.get('email', '').strip().lower()
    exists = get_user_model().objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})

def user_qr_code(request, user_id=None):
    """
    View to display a QR code for a user.
    If user_id is provided, displays the QR code for that user.
    Otherwise, displays the QR code for the current user.
    """
    

    @login_required
    def view_func(request, user_id=None):
        # If user_id is provided, get that user
        # Otherwise, use the current user
        if user_id:
            # Only staff can view other users' QR codes
            if not request.user.is_staff:
                messages.error(request, "You don't have permission to view this QR code.")
                return redirect('home')
            user = get_object_or_404(CustomUser, id=user_id)
        else:
            user = request.user

        # Generate the QR code
        qr_code = user.generate_qr_code()

        # If QR code generation failed, show an error
        if not qr_code:
            messages.error(request, "Failed to generate QR code. Please make sure the qrcode library is installed.")
            return redirect('home')

        # Render the template with the QR code
        return render(request, 'accounts/qr_code.html', {
            'user': user,
            'qr_code': qr_code,
        })

    return view_func(request, user_id)

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')

# Add this temporarily to your views.py
def model_debug_view(request):
    from django.http import HttpResponse
    from django.apps import apps
    
    models_info = []
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            models_info.append(f"{app_config.name}.{model.__name__}")
    
    return HttpResponse("<br>".join(models_info))

@staff_member_required
def generate_safa_id_ajax(request):
    """Generate a unique SAFA ID and return as JSON"""
    try:
        # Generate a unique SAFA ID
        while True:
            safa_id = get_random_string(length=5, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            if not CustomUser.objects.filter(safa_id=safa_id).exists():
                break
                
        return JsonResponse({
            'success': True,
            'safa_id': safa_id
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


