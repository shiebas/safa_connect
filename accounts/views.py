from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import EmailAuthenticationForm, NationalUserRegistrationForm, UniversalRegistrationForm
from .models import CustomUser
from membership.models import Membership
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import models
from django.shortcuts import get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_GET
from geography.models import Province, Region, Club
from django.http import JsonResponse
from geography.models import LocalFootballAssociation

class WorkingLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = EmailAuthenticationForm
    redirect_authenticated_user = False
    success_url = reverse_lazy('admin:index')
    
    def form_invalid(self, form):
        # Fix the username field error
        email = form.cleaned_data.get('username') if form.cleaned_data else None
        if email:
            try:
                user = CustomUser.objects.get(email=email)
                if not user.is_active:
                    messages.error(self.request, 'Your account is not yet activated. Please contact an administrator.')
            except CustomUser.DoesNotExist:
                messages.error(self.request, 'Invalid email or password.')
        return super().form_invalid(form)

def working_home(request):
    return HttpResponse("CONFIRMED WORKING - LOGIN SUCCESS")

def register(request):
    """
    View for handling user registration including players, administrators, etc.
    """
    if request.method == 'POST':
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)
        form = UniversalRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # This is probably calling the form's save method which checks 'province'
            user = form.save(commit=False)

            # Handle empty ID number for passport users
            if not user.id_number or user.id_number.strip() == '':
                user.id_number = None  # Store as NULL, not empty string

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
        form = UniversalRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})

def club_registration(request):
    """Registration view for club-level users"""
    if request.method == 'POST':
        form = UniversalRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Club administrator account created successfully!')
            return redirect('accounts:login')
    else:
        form = UniversalRegistrationForm()
    
    return render(request, 'accounts/club_registration.html', {
        'form': form,
        'title': 'Club Administrator Registration'
    })

def province_registration(request):
    """Registration view for province-level users"""
    if request.method == 'POST':
        form = UniversalRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Province administrator account created successfully!')
            return redirect('accounts:login')
    else:
        form = UniversalRegistrationForm()
    
    return render(request, 'accounts/province_registration.html', {
        'form': form,
        'title': 'Province Administrator Registration'
    })

def national_registration(request):
    """Registration view for national federation users"""
    if request.method == 'POST':
        print("=== FORM SUBMISSION DEBUG ===")
        print(f"Document type: {request.POST.get('id_document_type')}")
        print(f"ID number: {request.POST.get('id_number')}")
        print(f"Email: {request.POST.get('email')}")
        print(f"All POST keys: {list(request.POST.keys())}")
        
        form = NationalUserRegistrationForm(request.POST, request.FILES)
        print(f"Form is_valid: {form.is_valid()}")
        
        if form.is_valid():
            user = form.save()
            messages.success(request, 'National administrator account created successfully!')
            return redirect('accounts:login')
        else:
            print("=== FORM ERRORS ===")
            for field, errors in form.errors.items():
                print(f"Field '{field}': {errors}")
            print(f"Non-field errors: {form.non_field_errors()}")
    else:
        form = NationalUserRegistrationForm()
    
    return render(request, 'accounts/national_registration.html', {
        'form': form,
        'title': 'National Federation Administrator Registration'
    })

def lfa_registration(request):
    """Registration view for LFA users"""
    if request.method == 'POST':
        form = UniversalRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'LFA administrator account created successfully!')
            return redirect('accounts:login')
    else:
        form = UniversalRegistrationForm()
    
    return render(request, 'accounts/lfa_registration.html', {
        'form': form,
        'title': 'LFA Administrator Registration'
    })


def registration_portal(request):
    """Portal to choose registration type"""
    return render(request, 'accounts/registration_portal.html', {
        'title': 'SAFA Registration Portal'
    })

def check_username(request):
    """
    AJAX view to check if an email is available.
    Returns JSON response with available: true/false.
    """
    email = request.GET.get('email', '')  # Changed from username to email
    if not email:
        return JsonResponse({'available': False})

    # Check if the email exists
    exists = CustomUser.objects.filter(email=email).exists()  # Changed from username to email

    return JsonResponse({'available': not exists})

@require_GET
def check_email_availability(request):
    """AJAX endpoint to check if email is already registered"""
    email = request.GET.get('email', '').strip()
    
    if not email:
        return JsonResponse({'exists': False})
    
    exists = CustomUser.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})

@require_GET  
def check_id_number_availability(request):
    """AJAX endpoint to check if ID number is already registered"""
    id_number = request.GET.get('id_number', '').strip()
    
    if not id_number:
        return JsonResponse({'exists': False})
    
    exists = CustomUser.objects.filter(id_number=id_number).exists()
    return JsonResponse({'exists': exists})

def user_qr_code(request, user_id=None):
    """
    View to display a QR code for a user.
    """
    @login_required
    def view_func(request, user_id=None):
        if user_id:
            if not request.user.is_staff:
                messages.error(request, "You don't have permission to view this QR code.")
                return redirect('accounts:login')  # Change from 'home' to 'accounts:login'
            user = get_object_or_404(CustomUser, id=user_id)
        else:
            user = request.user

        # Generate the QR code
        qr_code = user.generate_qr_code()

        if not qr_code:
            messages.error(request, "Failed to generate QR code. Please make sure the qrcode library is installed.")
            return redirect('accounts:login')  # Change from 'home' to 'accounts:login'

        return render(request, 'accounts/qr_code.html', {
            'user': user,
            'qr_code': qr_code,
        })

    return view_func(request, user_id)

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')

@login_required
def update_profile_photo(request):
    """Handle profile photo updates"""
    if request.method == 'POST':
        if 'profile_photo' in request.FILES:
            user = request.user
            
            # Delete old photo if exists
            if user.profile_photo:
                user.profile_photo.delete()
            
            # Save new photo
            user.profile_photo = request.FILES['profile_photo']
            user.save()
            
            messages.success(request, 'Profile photo updated successfully!')
        else:
            messages.error(request, 'Please select a photo to upload.')
    
    return redirect('accounts:profile')

# Add this temporarily to your views.py
def model_debug_view(request):
    from django.http import HttpResponse
    from django.apps import apps
    
    models_info = []
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            models_info.append(f"{app_config.name}.{model.__name__}")
    
    return HttpResponse("<br>".join(models_info))

def api_regions(request):
    """API endpoint to get regions by province"""
    province_id = request.GET.get('province')
    print(f"DEBUG: api_regions called with province_id: {province_id}")
    
    if province_id:
        # Region has a ForeignKey to Province, so we use province=province_id
        regions = Region.objects.filter(province=province_id).values('id', 'name')
        regions_list = list(regions)
        print(f"DEBUG: Found {len(regions_list)} regions: {regions_list}")
        return JsonResponse(regions_list, safe=False)
    
    print("DEBUG: No province_id provided")
    return JsonResponse([], safe=False)

def api_clubs(request):
    """API endpoint to get clubs by LFA"""
    lfa_id = request.GET.get('lfa')
    region_id = request.GET.get('region')
    
    print(f"DEBUG: api_clubs called with lfa_id: {lfa_id}, region_id: {region_id}")
    
    if lfa_id:
        # Clubs filtered by LFA
        clubs = Club.objects.filter(localfootballassociation=lfa_id, status='ACTIVE').values('id', 'name')
        clubs_list = list(clubs)
        print(f"DEBUG: Returning {len(clubs_list)} clubs by LFA: {clubs_list}")
        return JsonResponse(clubs_list, safe=False)
    elif region_id:
        # Fallback: Clubs filtered by region
        clubs = Club.objects.filter(localfootballassociation__region=region_id, status='ACTIVE').values('id', 'name')
        clubs_list = list(clubs)
        print(f"DEBUG: Returning {len(clubs_list)} clubs by region: {clubs_list}")
        return JsonResponse(clubs_list, safe=False)
    
    print("DEBUG: No lfa_id or region_id provided")
    return JsonResponse([], safe=False)

def api_lfas(request):
    """API endpoint to get LFAs by region"""
    region_id = request.GET.get('region')
    print(f"DEBUG: api_lfas called with region_id: {region_id}")
    
    if region_id:
        # LFA has a ForeignKey to Region, so we use region=region_id
        lfas = LocalFootballAssociation.objects.filter(region=region_id).values('id', 'name')
        lfas_list = list(lfas)
        print(f"DEBUG: Found {len(lfas_list)} LFAs: {lfas_list}")
        return JsonResponse(lfas_list, safe=False)
    
    print("DEBUG: No region_id provided")
    return JsonResponse([], safe=False)

def universal_registration(request):
    """Single universal registration view for all admin types"""
    if request.method == 'POST':
        form = UniversalRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'{user.get_role_display()} account created successfully!')
            return redirect('accounts:login')
    else:
        form = UniversalRegistrationForm()
    
    return render(request, 'accounts/universal_registration.html', {
        'form': form,
        'title': 'SAFA Registration'
    })

def national_registration_view(request):
    if request.method == 'POST':
        form = UniversalRegistrationForm(request.POST, request.FILES, registration_type='national')
        if form.is_valid():
            user = form.save()
            messages.success(request, 'National administrator account created successfully!')
            return redirect('accounts:login')
    else:
        form = UniversalRegistrationForm(registration_type='national')
    
    return render(request, 'accounts/national_registration.html', {
        'form': form,
        'title': 'National Federation Administrator Registration'
    })