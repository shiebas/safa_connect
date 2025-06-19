from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
import datetime
from .forms import EmailAuthenticationForm, NationalUserRegistrationForm, UniversalRegistrationForm, ClubAdminPlayerRegistrationForm, PlayerClubRegistrationOnlyForm, PlayerUpdateForm, PlayerClubRegistrationUpdateForm, PlayerUpdateForm
from .models import CustomUser
from membership.models import Membership, Player, PlayerClubRegistration
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
from rest_framework import viewsets
from .serializers import CustomUserSerializer


def generate_unique_player_email(first_name, last_name, existing_id=None):
    """
    Generate a unique player email in the format firstname.lastname+number@safaglobaladmin.co.za
    
    Args:
        first_name (str): Player's first name
        last_name (str): Player's last name
        existing_id (int): Optional ID of existing player to exclude from uniqueness check
        
    Returns:
        str: Unique email address
    """
    # Clean and normalize names
    first_name = ''.join(e for e in first_name.strip().lower() if e.isalnum())
    last_name = ''.join(e for e in last_name.strip().lower() if e.isalnum())
    
    # Create email base
    email_base = f"{first_name}.{last_name}"
    email_domain = "safaglobaladmin.co.za"
    
    # Find a unique email
    counter = 1
    email = f"{email_base}@{email_domain}"
    
    # Check if email exists, if so add a number and increment until unique
    query = Player.objects.filter(email=email)
    if existing_id:
        query = query.exclude(id=existing_id)
    
    while query.exists():
        email = f"{email_base}{counter}@{email_domain}"
        counter += 1
        query = Player.objects.filter(email=email)
        if existing_id:
            query = query.exclude(id=existing_id)
    
    return email


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
    user = request.user
    lfa = getattr(user, 'local_federation', None)
    if request.method == 'POST':
        form = UniversalRegistrationForm(request.POST, request.FILES)
        # Restrict club choices to clubs in this LFA
        if lfa:
            form.fields['club'].queryset = Club.objects.filter(localfootballassociation=lfa)
        if form.is_valid():
            club_admin = form.save()
            messages.success(request, 'Club administrator account created successfully!')
            return redirect('accounts:login')
    else:
        form = UniversalRegistrationForm()
        if lfa:
            form.fields['club'].queryset = Club.objects.filter(localfootballassociation=lfa)
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

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

from django.contrib.auth.decorators import user_passes_test

@login_required
def lfa_admin_approvals(request):
    user = request.user
    # Only LFA admins can access
    if user.role != 'ADMIN_LOCAL_FED' or not user.local_federation:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('accounts:profile')

    # Get pending club admins in this LFA, prefetch club for compliance checks
    pending_admins = CustomUser.objects.filter(
        role='CLUB_ADMIN',
        local_federation=user.local_federation,
        is_active=False
    ).select_related('club')

    # Get clubs in this LFA that are fully compliant (all compliance fields complete)
    compliant_clubs = []
    for club in Club.objects.filter(localfootballassociation=user.local_federation):
        if club.club_type and club.club_owner_type and club.club_documents:
            compliant_clubs.append(club)

    # Get clubs in this LFA that are not fully compliant (missing any compliance fields)
    non_compliant_clubs = []
    for club in Club.objects.filter(localfootballassociation=user.local_federation):
        if not (club.club_type and club.club_owner_type and club.club_documents):
            non_compliant_clubs.append(club)

    if request.method == 'POST':
        admin_id = request.POST.get('user_id')
        action = request.POST.get('action')
        club_id = request.POST.get('club_id')
        if admin_id:
            admin_user = CustomUser.objects.filter(id=admin_id, local_federation=user.local_federation, role='CLUB_ADMIN').first()
            if admin_user:
                if action == 'approve':
                    admin_user.is_active = True
                    admin_user.save()
                    messages.success(request, f"Approved {admin_user.get_full_name()} as club administrator.")
                elif action == 'reject':
                    admin_user.delete()
                    messages.success(request, "Club administrator registration rejected and deleted.")
            return redirect('accounts:lfa_admin_approvals')
        elif club_id and action == 'mark_paid':
            club = Club.objects.filter(id=club_id, localfootballassociation=user.local_federation).first()
            if club:
                club.affiliation_fees_paid = True
                club.save()
                messages.success(request, f"Affiliation fees marked as paid for {club.name}.")
            return redirect('accounts:lfa_admin_approvals')

    return render(request, 'accounts/lfa_admin_approvals.html', {
        'pending_admins': pending_admins,
        'compliant_clubs': compliant_clubs,
        'non_compliant_clubs': non_compliant_clubs,
    })

@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def club_admin_add_player(request):
    if not request.user.is_authenticated or request.user.role != 'CLUB_ADMIN':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('accounts:dashboard')

    if not request.user.club:
        messages.error(request, 'Your user profile is not linked to a club. Please contact support.')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        player_form = ClubAdminPlayerRegistrationForm(request.POST, request.FILES)
        # Store request in form to allow showing document validation warnings
        player_form.request = request
        # Process ID number before validation if provided
        if 'id_number' in request.POST and request.POST['id_number'].strip():
            id_number = request.POST['id_number'].strip()
            try:
                # Extract DOB from ID number (format: YYMMDD...)
                year = int(id_number[:2])
                month = int(id_number[2:4])
                day = int(id_number[4:6])
                
                # Determine century (00-99)
                current_year = timezone.now().year % 100
                century = 2000 if year <= current_year else 1900
                full_year = century + year
                
                # Check if date is valid
                try:
                    dob = datetime.date(full_year, month, day)
                    # Set the date_of_birth field in the form data
                    player_form.data = player_form.data.copy()
                    player_form.data['date_of_birth'] = dob.isoformat()
                    
                    # Also set gender based on ID number
                    gender_digit = int(id_number[6])
                    player_form.data['gender'] = 'M' if gender_digit >= 5 else 'F'
                except ValueError:
                    # Invalid date in ID number, will be caught in form validation
                    pass
            except (ValueError, IndexError):
                # Invalid ID number, will be caught in form validation
                pass
        
        # Generate a unique email for the player before checking form validity
        if 'first_name' in request.POST and 'last_name' in request.POST:
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            
            # Generate unique email using the utility function
            unique_email = generate_unique_player_email(first_name, last_name)
            
            # Set the email in the form data
            player_form.data = player_form.data.copy()
            player_form.data['email'] = unique_email
        
        if player_form.is_valid():
            # Save player with all fields including the generated unique email
            player = player_form.save()
            
            # Create minimal club registration (just linking player to club)
            registration = PlayerClubRegistration(
                player=player,
                club=request.user.club
            )
            registration.save()
            
            # Determine if player is junior (under 18) based on date of birth
            today = timezone.now().date()
            is_junior = False
            if player.date_of_birth:
                player_age = today.year - player.date_of_birth.year
                # Adjust age if birthday hasn't happened yet this year
                if (today.month, today.day) < (player.date_of_birth.month, player.date_of_birth.day):
                    player_age -= 1
                is_junior = player_age < 18
            
            # Create invoice for the player
            from .utils import create_player_invoice
            invoice = create_player_invoice(
                player=player,
                club=request.user.club,
                issued_by=player,  # Using player as issued_by as they don't have a separate Member instance
                is_junior=is_junior
            )
            
            success_message = f'Player registered successfully with email {player.email}!'
            if invoice:
                success_message += f' An invoice (#{invoice.invoice_number}) has been created.'
                success_message += f' Registration fee: R{"100" if is_junior else "200"}.'
                success_message += ' Player will be eligible for approval once the invoice is paid.'
            
            messages.success(request, success_message)
            return redirect('accounts:dashboard')
        else:
            # Add a summary error message at the top without showing specific fields
            messages.error(request, 'Please correct the errors in the form below.')
    else:
        player_form = ClubAdminPlayerRegistrationForm()
    
    return render(request, 'accounts/club_admin_add_player.html', {
        'player_form': player_form
    })

from django.http import JsonResponse
from membership.models import Player

def ajax_check_id_number(request):
    id_number = request.GET.get('id_number')
    exists = False
    if id_number:
        exists = Player.objects.filter(id_number=id_number).exists()
    return JsonResponse({'exists': exists})

def ajax_check_passport_number(request):
    passport_number = request.GET.get('passport_number')
    exists = False
    if passport_number:
        exists = Player.objects.filter(passport_number=passport_number).exists()
    return JsonResponse({'exists': exists})

@require_GET
def ajax_check_id_number(request):
    """AJAX endpoint to check if an ID number already exists"""
    id_number = request.GET.get('id_number', '')
    exists = Player.objects.filter(id_number=id_number).exists()
    return JsonResponse({'exists': exists})

@require_GET
def ajax_check_passport_number(request):
    """AJAX endpoint to check if a passport number already exists"""
    passport_number = request.GET.get('passport_number', '')
    exists = Player.objects.filter(passport_number=passport_number).exists()
    return JsonResponse({'exists': exists})

@require_GET
def ajax_check_sa_passport_number(request):
    """AJAX endpoint to check if a South African passport number already exists"""
    sa_passport_number = request.GET.get('sa_passport_number', '')
    player_id = request.GET.get('player_id', None)
    
    query = Player.objects.filter(sa_passport_number=sa_passport_number)
    if player_id:
        query = query.exclude(pk=player_id)
    
    exists = query.exists()
    return JsonResponse({'is_unique': not exists, 'exists': exists})

@login_required
def player_approval_list(request):
    """View for club admins and higher-level admins to view and approve players"""
    if not hasattr(request.user, 'role') or request.user.role not in ['CLUB_ADMIN', 'LFA_ADMIN', 'REGION_ADMIN', 'PROVINCE_ADMIN', 'NATIONAL_ADMIN']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('accounts:dashboard')
    
    # Get players related to the admin's scope
    player_registrations = []
    
    # For club admins, show only their club's players
    if request.user.role == 'CLUB_ADMIN' and hasattr(request.user, 'club') and request.user.club:
        player_registrations = PlayerClubRegistration.objects.filter(club=request.user.club).select_related('player', 'club')
    
    # For LFA admins, show players in clubs under their LFA
    elif request.user.role == 'LFA_ADMIN' and hasattr(request.user, 'lfa') and request.user.lfa:
        clubs = Club.objects.filter(local_football_association=request.user.lfa)
        player_registrations = PlayerClubRegistration.objects.filter(club__in=clubs).select_related('player', 'club')
    
    # For higher level admins, show players based on their jurisdiction
    elif request.user.role in ['REGION_ADMIN', 'PROVINCE_ADMIN', 'NATIONAL_ADMIN']:
        # Get all players or filter by region/province as appropriate
        if request.user.role == 'REGION_ADMIN' and hasattr(request.user, 'region') and request.user.region:
            lfas = LocalFootballAssociation.objects.filter(region=request.user.region)
            clubs = Club.objects.filter(local_football_association__in=lfas)
            player_registrations = PlayerClubRegistration.objects.filter(club__in=clubs).select_related('player', 'club')
        elif request.user.role == 'PROVINCE_ADMIN' and hasattr(request.user, 'province') and request.user.province:
            regions = Region.objects.filter(province=request.user.province)
            lfas = LocalFootballAssociation.objects.filter(region__in=regions)
            clubs = Club.objects.filter(local_football_association__in=lfas)
            player_registrations = PlayerClubRegistration.objects.filter(club__in=clubs).select_related('player', 'club')
        else:
            # National admin sees all players with their club registrations
            player_registrations = PlayerClubRegistration.objects.all().select_related('player', 'club')
    
    # Create a list of (player, club) tuples
    player_club_pairs = [(reg.player, reg.club) for reg in player_registrations]
    
    # Filter by approval status and make sure each player only appears once
    approval_status = request.GET.get('status', 'pending')
    
    # Import here to avoid circular imports
    from membership.models.invoice import Invoice
    
    # Use a dictionary to ensure each player only appears once
    unique_players = {}
    for player, club in player_club_pairs:
        if player.id not in unique_players:
            if (approval_status == 'pending' and not player.is_approved) or \
               (approval_status == 'approved' and player.is_approved) or \
               (approval_status not in ['pending', 'approved']):
                # Check invoice payment status
                has_unpaid_invoice = Invoice.objects.filter(
                    player=player,
                    status__in=['PENDING', 'OVERDUE'],
                    invoice_type='REGISTRATION'
                ).exists()
                
                # Add invoice payment status to the tuple
                unique_players[player.id] = (player, club, has_unpaid_invoice)
    
    # Convert back to a list of tuples
    player_club_pairs = list(unique_players.values())
    
    return render(request, 'accounts/player_approval_list.html', {
        'player_club_pairs': player_club_pairs,
        'approval_status': approval_status
    })

@login_required
def player_detail(request, player_id):
    """View player details"""
    if not hasattr(request.user, 'role') or request.user.role not in ['CLUB_ADMIN', 'LFA_ADMIN', 'REGION_ADMIN', 'PROVINCE_ADMIN', 'NATIONAL_ADMIN']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('accounts:dashboard')
    
    # Get player with prefetched invoices
    player = get_object_or_404(Player.objects.prefetch_related('invoices'), id=player_id)
    
    # Check if the admin has permission to view this player
    has_permission = False
    
    if request.user.role == 'CLUB_ADMIN' and hasattr(request.user, 'club') and request.user.club:
        # Club admins can only see players in their club
        club_registrations = player.club_registrations.filter(club=request.user.club)
        has_permission = club_registrations.exists()
    elif request.user.role == 'LFA_ADMIN' and hasattr(request.user, 'lfa') and request.user.lfa:
        # LFA admins can see players in clubs under their LFA
        clubs = Club.objects.filter(local_football_association=request.user.lfa)
        club_registrations = player.club_registrations.filter(club__in=clubs)
        has_permission = club_registrations.exists()
    elif request.user.role == 'REGION_ADMIN' and hasattr(request.user, 'region') and request.user.region:
        # Region admins can see players in clubs under LFAs in their region
        lfas = LocalFootballAssociation.objects.filter(region=request.user.region)
        clubs = Club.objects.filter(local_football_association__in=lfas)
        club_registrations = player.club_registrations.filter(club__in=clubs)
        has_permission = club_registrations.exists()
    elif request.user.role == 'PROVINCE_ADMIN' and hasattr(request.user, 'province') and request.user.province:
        # Province admins can see players in clubs under LFAs in regions in their province
        regions = Region.objects.filter(province=request.user.province)
        lfas = LocalFootballAssociation.objects.filter(region__in=regions)
        clubs = Club.objects.filter(local_football_association__in=lfas)
        club_registrations = player.club_registrations.filter(club__in=clubs)
        has_permission = club_registrations.exists()
    elif request.user.role == 'NATIONAL_ADMIN':
        # National admins can see all players
        has_permission = True
    
    if not has_permission:
        messages.error(request, 'You do not have permission to view this player.')
        return redirect('accounts:player_approval_list')
    
    return render(request, 'accounts/player_detail.html', {
        'player': player,
        'registrations': player.club_registrations.all()
    })

@login_required
def approve_player(request, player_id):
    """Approve a player"""
    if request.method != 'POST':
        return redirect('accounts:player_approval_list')
    
    if not hasattr(request.user, 'role') or request.user.role not in ['CLUB_ADMIN', 'LFA_ADMIN', 'REGION_ADMIN', 'PROVINCE_ADMIN', 'NATIONAL_ADMIN']:
        messages.error(request, 'You do not have permission to approve players.')
        return redirect('accounts:dashboard')
    
    player = get_object_or_404(Player, id=player_id)
    
    # Similar permission check as in player_detail
    has_permission = False
    
    # Logic to check if the admin has permission to approve this player
    # (Same permission logic as player_detail)
    if request.user.role == 'CLUB_ADMIN' and hasattr(request.user, 'club') and request.user.club:
        club_registrations = player.club_registrations.filter(club=request.user.club)
        has_permission = club_registrations.exists()
    elif request.user.role == 'LFA_ADMIN' and hasattr(request.user, 'lfa') and request.user.lfa:
        clubs = Club.objects.filter(local_football_association=request.user.lfa)
        club_registrations = player.club_registrations.filter(club__in=clubs)
        has_permission = club_registrations.exists()
    elif request.user.role == 'REGION_ADMIN' and hasattr(request.user, 'region') and request.user.region:
        lfas = LocalFootballAssociation.objects.filter(region=request.user.region)
        clubs = Club.objects.filter(local_football_association__in=lfas)
        club_registrations = player.club_registrations.filter(club__in=clubs)
        has_permission = club_registrations.exists()
    elif request.user.role == 'PROVINCE_ADMIN' and hasattr(request.user, 'province') and request.user.province:
        regions = Region.objects.filter(province=request.user.province)
        lfas = LocalFootballAssociation.objects.filter(region__in=regions)
        clubs = Club.objects.filter(local_football_association__in=lfas)
        club_registrations = player.club_registrations.filter(club__in=clubs)
        has_permission = club_registrations.exists()
    elif request.user.role == 'NATIONAL_ADMIN':
        has_permission = True
    
    if not has_permission:
        messages.error(request, 'You do not have permission to approve this player.')
        return redirect('accounts:player_approval_list')
    
    # Check for required documents before approval
    missing_requirements = []
    
    # Check for profile picture - required for all players
    if not player.profile_picture:
        missing_requirements.append("Profile picture")
    
    # Check for ID document or passport document based on document type
    if player.id_document_type == 'ID' and not player.id_document:
        missing_requirements.append("South African ID document")
    elif player.id_document_type == 'PP' and not player.id_document:
        missing_requirements.append("Passport document")
    
    # Check if the player has any unpaid invoices
    from membership.models.invoice import Invoice
    pending_invoices = Invoice.objects.filter(
        player=player,
        status__in=['PENDING', 'OVERDUE'],
        invoice_type='REGISTRATION'
    )
    
    if pending_invoices.exists():
        invoice_numbers = ", ".join([f"#{inv.invoice_number}" for inv in pending_invoices])
        messages.error(request, 
            f"Cannot approve player. Player has unpaid registration invoice(s): {invoice_numbers}. "
            f"Please ensure all registration fees are paid before approving the player."
        )
        return redirect('accounts:player_detail', player_id=player.id)
    
    # If there are missing requirements, don't approve and show message
    if missing_requirements:
        message = f"Cannot approve player. The following documents are missing: {', '.join(missing_requirements)}."
        messages.error(request, message)
        return redirect('accounts:player_detail', player_id=player.id)
    
    # All checks passed, approve the player
    player.is_approved = True
    player.status = 'ACTIVE'  # Update the status from PENDING to ACTIVE
    player.save()
    
    messages.success(request, f'Player {player.get_full_name()} has been approved.')
    return redirect('accounts:player_approval_list')

@login_required
def unapprove_player(request, player_id):
    """Unapprove a player"""
    if request.method != 'POST':
        return redirect('accounts:player_approval_list')
    
    # Only higher-level admins can unapprove players
    if not hasattr(request.user, 'role') or request.user.role not in ['LFA_ADMIN', 'REGION_ADMIN', 'PROVINCE_ADMIN', 'NATIONAL_ADMIN']:
        messages.error(request, 'You do not have permission to unapprove players.')
        return redirect('accounts:dashboard')
    
    player = get_object_or_404(Player, id=player_id)
    
    # Similar permission check as in approve_player
    has_permission = False
    
    # Logic to check if the admin has permission to unapprove this player
    if request.user.role == 'LFA_ADMIN' and hasattr(request.user, 'lfa') and request.user.lfa:
        clubs = Club.objects.filter(local_football_association=request.user.lfa)
        club_registrations = player.club_registrations.filter(club__in=clubs)
        has_permission = club_registrations.exists()
    elif request.user.role == 'REGION_ADMIN' and hasattr(request.user, 'region') and request.user.region:
        lfas = LocalFootballAssociation.objects.filter(region=request.user.region)
        clubs = Club.objects.filter(local_football_association__in=lfas)
        club_registrations = player.club_registrations.filter(club__in=clubs)
        has_permission = club_registrations.exists()
    elif request.user.role == 'PROVINCE_ADMIN' and hasattr(request.user, 'province') and request.user.province:
        regions = Region.objects.filter(province=request.user.province)
        lfas = LocalFootballAssociation.objects.filter(region__in=regions)
        clubs = Club.objects.filter(local_football_association__in=lfas)
        club_registrations = player.club_registrations.filter(club__in=clubs)
        has_permission = club_registrations.exists()
    elif request.user.role == 'NATIONAL_ADMIN':
        has_permission = True
    
    if not has_permission:
        messages.error(request, 'You do not have permission to unapprove this player.')
        return redirect('accounts:player_approval_list')
    
    player.is_approved = False
    player.status = 'PENDING'  # Update the status back to PENDING
    player.save()
    
    messages.success(request, f'Player {player.get_full_name()} approval has been revoked.')
    return redirect('accounts:player_approval_list')

@login_required
def edit_player(request, player_id):
    """View for editing player information after registration"""
    if not hasattr(request.user, 'role') or request.user.role not in ['CLUB_ADMIN', 'LFA_ADMIN', 'REGION_ADMIN', 'PROVINCE_ADMIN', 'NATIONAL_ADMIN']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('accounts:dashboard')
    
    player = get_object_or_404(Player, id=player_id)
    
    # Check if the admin has permission to edit this player (same logic as player_detail)
    has_permission = False
    
    if request.user.role == 'CLUB_ADMIN' and hasattr(request.user, 'club') and request.user.club:
        # Club admins can only edit players in their club
        club_registrations = player.club_registrations.filter(club=request.user.club)
        has_permission = club_registrations.exists()
        if has_permission:
            registration = club_registrations.first()  # Get the registration for this club
    elif request.user.role == 'LFA_ADMIN' and hasattr(request.user, 'lfa') and request.user.lfa:
        # LFA admins can edit players in clubs under their LFA
        clubs = Club.objects.filter(local_football_association=request.user.lfa)
        club_registrations = player.club_registrations.filter(club__in=clubs)
        has_permission = club_registrations.exists()
        if has_permission:
            registration = club_registrations.first()
    elif request.user.role == 'REGION_ADMIN' and hasattr(request.user, 'region') and request.user.region:
        lfas = LocalFootballAssociation.objects.filter(region=request.user.region)
        clubs = Club.objects.filter(local_football_association__in=lfas)
        club_registrations = player.club_registrations.filter(club__in=clubs)
        has_permission = club_registrations.exists()
        if has_permission:
            registration = club_registrations.first()
    elif request.user.role == 'PROVINCE_ADMIN' and hasattr(request.user, 'province') and request.user.province:
        regions = Region.objects.filter(province=request.user.province)
        lfas = LocalFootballAssociation.objects.filter(region__in=regions)
        clubs = Club.objects.filter(local_football_association__in=lfas)
        club_registrations = player.club_registrations.filter(club__in=clubs)
        has_permission = club_registrations.exists()
        if has_permission:
            registration = club_registrations.first()
    elif request.user.role == 'NATIONAL_ADMIN':
        # National admins can edit all players
        has_permission = True
        if player.club_registrations.exists():
            registration = player.club_registrations.first()
        else:
            registration = None
    
    if not has_permission:
        messages.error(request, 'You do not have permission to edit this player.')
        return redirect('accounts:player_approval_list')
    
    if request.method == 'POST':
        player_form = PlayerUpdateForm(request.POST, request.FILES, instance=player)
        reg_form = PlayerClubRegistrationUpdateForm(request.POST, instance=registration) if registration else None
        
        # Store request in form to allow showing document validation warnings
        player_form.request = request
        
        # If email is empty or invalid, regenerate a unique one
        if not player_form.data.get('email') or '@' not in player_form.data.get('email', ''):
            player_form.data = player_form.data.copy()
            player_form.data['email'] = generate_unique_player_email(
                player.first_name, player.last_name, existing_id=player.id
            )

        forms_valid = player_form.is_valid()
        if reg_form:
            forms_valid = forms_valid and reg_form.is_valid()
        
        if forms_valid:
            player_form.save()
            if reg_form:
                reg_form.save()
            
            messages.success(request, f'Player {player.get_full_name()} updated successfully.')
            return redirect('accounts:player_detail', player_id=player.id)
    else:
        player_form = PlayerUpdateForm(instance=player)
        reg_form = PlayerClubRegistrationUpdateForm(instance=registration) if registration else None
    
    return render(request, 'accounts/edit_player.html', {
        'player': player,
        'player_form': player_form,
        'reg_form': reg_form
    })

@login_required
def club_invoices(request):
    """View to show outstanding and all invoices for a club"""
    if not hasattr(request.user, 'role') or request.user.role != 'CLUB_ADMIN':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('accounts:dashboard')
    
    if not hasattr(request.user, 'club') or not request.user.club:
        messages.error(request, 'Your profile is not linked to any club.')
        return redirect('accounts:dashboard')
    
    # Import here to avoid circular imports
    from membership.models.invoice import Invoice
    
    # Get all invoices for this club
    club = request.user.club
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        club_invoices = Invoice.objects.filter(
            club=club,
            status=status
        ).select_related('player')
    else:
        club_invoices = Invoice.objects.filter(
            club=club
        ).select_related('player')
    
    # Calculate summary statistics
    summary = {
        'total_invoices': club_invoices.count(),
        'total_amount': sum(invoice.amount for invoice in club_invoices),
        'pending_invoices': club_invoices.filter(status='PENDING').count(),
        'pending_amount': sum(invoice.amount for invoice in club_invoices.filter(status='PENDING')),
        'overdue_invoices': club_invoices.filter(status='OVERDUE').count(),
        'overdue_amount': sum(invoice.amount for invoice in club_invoices.filter(status='OVERDUE')),
        'paid_invoices': club_invoices.filter(status='PAID').count(),
        'paid_amount': sum(invoice.amount for invoice in club_invoices.filter(status='PAID')),
    }
    
    return render(request, 'accounts/club_invoices.html', {
        'club': club,
        'invoices': club_invoices,
        'summary': summary,
        'selected_status': status
    })

@login_required
def player_statistics(request):
    """View for LFA, Region, and Province admins to see player registration statistics"""
    if not hasattr(request.user, 'role') or request.user.role not in ['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_COUNTRY']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('accounts:dashboard')
    
    # Import models
    from geography.models import Province, Region, LocalFootballAssociation, Club
    from membership.models import Player
    from django.db.models import Count, Sum
    
    # Initialize statistics based on user role
    stats = {}
    total_players = 0
    approved_players = 0
    pending_players = 0
    junior_players = 0
    senior_players = 0
    female_players = 0
    female_junior_players = 0
    female_senior_players = 0
    
    # Variables to store the list of entities (provinces, regions, LFAs, or clubs)
    entities = []
    entity_type = ""
    
    # Get today's date for age calculation
    today = timezone.now().date()
    
    # For LFA admins
    if request.user.role == 'ADMIN_LOCAL_FED' and hasattr(request.user, 'local_federation') and request.user.local_federation:
        lfa = request.user.local_federation
        entity_type = "clubs"
        
        # Get clubs in this LFA with player counts
        clubs = Club.objects.filter(
            localfootballassociation=lfa
        ).annotate(
            players_count=Count('player_registrations__player', distinct=True),
            approved_count=Count('player_registrations__player', distinct=True, 
                filter=models.Q(player_registrations__player__is_approved=True)),
            pending_count=Count('player_registrations__player', distinct=True,
                filter=models.Q(player_registrations__player__is_approved=False))
        )
        
        # Add approval percentage for each club
        for club in clubs:
            if club.players_count > 0:
                club.approval_percentage = round((club.approved_count / club.players_count) * 100)
            else:
                club.approval_percentage = 0
        
        entities = clubs
        
        # Calculate total players in LFA
        players = Player.objects.filter(
            club_registrations__club__localfootballassociation=lfa
        ).distinct()
        
        total_players = players.count()
        approved_players = players.filter(is_approved=True).count()
        pending_players = players.filter(is_approved=False).count()
        
        # Calculate junior/senior counts and gender distribution
        for player in players:
            player_age = today.year - player.date_of_birth.year
            if (today.month, today.day) < (player.date_of_birth.month, player.date_of_birth.day):
                player_age -= 1
                
            # Count by age group
            if player_age < 18:
                junior_players += 1
            else:
                senior_players += 1
                
            # Count female players
            if player.gender == 'F':
                female_players += 1
                if player_age < 18:
                    female_junior_players += 1
                else:
                    female_senior_players += 1
    
    # For Region admins
    elif request.user.role == 'ADMIN_REGION' and hasattr(request.user, 'region') and request.user.region:
        region = request.user.region
        entity_type = "lfas"
        
        # Get LFAs in this region with player counts
        lfas = LocalFootballAssociation.objects.filter(
            region=region
        ).annotate(
            players_count=Count('clubs__player_registrations__player', distinct=True),
            approved_count=Count('clubs__player_registrations__player', distinct=True, 
                filter=models.Q(clubs__player_registrations__player__is_approved=True)),
            pending_count=Count('clubs__player_registrations__player', distinct=True,
                filter=models.Q(clubs__player_registrations__player__is_approved=False))
        )
        
        # Add approval percentage for each LFA
        for lfa in lfas:
            if lfa.players_count > 0:
                lfa.approval_percentage = round((lfa.approved_count / lfa.players_count) * 100)
            else:
                lfa.approval_percentage = 0
        
        entities = lfas
        
        # Calculate total players in region
        players = Player.objects.filter(
            club_registrations__club__localfootballassociation__region=region
        ).distinct()
        
        total_players = players.count()
        approved_players = players.filter(is_approved=True).count()
        pending_players = players.filter(is_approved=False).count()
        
        # Calculate junior/senior counts and gender distribution
        for player in players:
            player_age = today.year - player.date_of_birth.year
            if (today.month, today.day) < (player.date_of_birth.month, player.date_of_birth.day):
                player_age -= 1
                
            # Count by age group
            if player_age < 18:
                junior_players += 1
            else:
                senior_players += 1
                
            # Count female players
            if player.gender == 'F':
                female_players += 1
                if player_age < 18:
                    female_junior_players += 1
                else:
                    female_senior_players += 1
    
    # For Province admins
    elif request.user.role == 'ADMIN_PROVINCE' and hasattr(request.user, 'province') and request.user.province:
        province = request.user.province
        entity_type = "regions"
        
        # Get regions in this province with player counts
        regions = Region.objects.filter(
            province=province
        ).annotate(
            players_count=Count('localfootballassociations__clubs__player_registrations__player', distinct=True),
            approved_count=Count('localfootballassociations__clubs__player_registrations__player', distinct=True, 
                filter=models.Q(localfootballassociations__clubs__player_registrations__player__is_approved=True)),
            pending_count=Count('localfootballassociations__clubs__player_registrations__player', distinct=True,
                filter=models.Q(localfootballassociations__clubs__player_registrations__player__is_approved=False))
        )
        
        # Add approval percentage for each region
        for region in regions:
            if region.players_count > 0:
                region.approval_percentage = round((region.approved_count / region.players_count) * 100)
            else:
                region.approval_percentage = 0
        
        entities = regions
        
        # Calculate total players in province
        players = Player.objects.filter(
            club_registrations__club__localfootballassociation__region__province=province
        ).distinct()
        
        total_players = players.count()
        approved_players = players.filter(is_approved=True).count()
        pending_players = players.filter(is_approved=False).count()
        
        # Calculate junior/senior counts and gender distribution
        for player in players:
            player_age = today.year - player.date_of_birth.year
            if (today.month, today.day) < (player.date_of_birth.month, player.date_of_birth.day):
                player_age -= 1
                
            # Count by age group
            if player_age < 18:
                junior_players += 1
            else:
                senior_players += 1
                
            # Count female players
            if player.gender == 'F':
                female_players += 1
                if player_age < 18:
                    female_junior_players += 1
                else:
                    female_senior_players += 1
    
    # For Country/National admins
    elif request.user.role == 'ADMIN_COUNTRY':
        entity_type = "provinces"
        
        # Get provinces with player counts
        provinces = Province.objects.annotate(
            players_count=Count('regions__localfootballassociations__clubs__player_registrations__player', distinct=True),
            approved_count=Count('regions__localfootballassociations__clubs__player_registrations__player', distinct=True, 
                filter=models.Q(regions__localfootballassociations__clubs__player_registrations__player__is_approved=True)),
            pending_count=Count('regions__localfootballassociations__clubs__player_registrations__player', distinct=True,
                filter=models.Q(regions__localfootballassociations__clubs__player_registrations__player__is_approved=False))
        )
        
        # Add approval percentage for each province
        for province in provinces:
            if province.players_count > 0:
                province.approval_percentage = round((province.approved_count / province.players_count) * 100)
            else:
                province.approval_percentage = 0
        
        entities = provinces
        
        # Calculate total players nationally
        players = Player.objects.all()
        
        total_players = players.count()
        approved_players = players.filter(is_approved=True).count()
        pending_players = players.filter(is_approved=False).count()
        
        # Calculate junior/senior counts and gender distribution
        for player in players:
            player_age = today.year - player.date_of_birth.year
            if (today.month, today.day) < (player.date_of_birth.month, player.date_of_birth.day):
                player_age -= 1
                
            # Count by age group
            if player_age < 18:
                junior_players += 1
            else:
                senior_players += 1
                
            # Count female players
            if player.gender == 'F':
                female_players += 1
                if player_age < 18:
                    female_junior_players += 1
                else:
                    female_senior_players += 1
    
    # Compile statistics
    stats = {
        'total_players': total_players,
        'approved_players': approved_players,
        'pending_players': pending_players,
        'junior_players': junior_players,
        'senior_players': senior_players,
        'female_players': female_players,
        'female_junior_players': female_junior_players,
        'female_senior_players': female_senior_players,
        'male_players': total_players - female_players,
        'male_junior_players': junior_players - female_junior_players,
        'male_senior_players': senior_players - female_senior_players,
    }
    
    # Calculate percentages here for use in the template
    if total_players > 0:
        approved_percentage = round((approved_players / total_players) * 100)
        pending_percentage = 100 - approved_percentage
        junior_percentage = round((junior_players / total_players) * 100)
        senior_percentage = round((senior_players / total_players) * 100)
        female_percentage = round((female_players / total_players) * 100)
        male_percentage = 100 - female_percentage
    else:
        approved_percentage = 0
        pending_percentage = 0
        junior_percentage = 0
        senior_percentage = 0
        female_percentage = 0
        male_percentage = 0
        
    stats.update({
        'approved_percentage': approved_percentage,
        'pending_percentage': pending_percentage,
        'junior_percentage': junior_percentage,
        'senior_percentage': senior_percentage,
        'female_percentage': female_percentage,
        'male_percentage': male_percentage,
    })
    
    return render(request, 'accounts/player_statistics.html', {
        'stats': stats,
        'entities': entities,
        'entity_type': entity_type,
    })