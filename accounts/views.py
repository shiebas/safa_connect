from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
import datetime
from .forms import EmailAuthenticationForm, NationalUserRegistrationForm, UniversalRegistrationForm, PlayerClubRegistrationOnlyForm, PlayerUpdateForm, PlayerClubRegistrationUpdateForm, ClubAdminOfficialRegistrationForm, AssociationOfficialRegistrationForm, OfficialCertificationForm
from .models import CustomUser
from registration.models import Player, Official, PlayerClubRegistration
from membership.models import Invoice
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Sum
from django.shortcuts import get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_GET
from geography.models import Province, Region, Club, Association, LocalFootballAssociation
from rest_framework import viewsets
from .serializers import CustomUserSerializer
from django import forms


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

def admin_registration_view(request, role_type):
    title_map = {
        'national': 'National Federation Administrator Registration',
        'province': 'Province Administrator Registration',
        'region': 'Region Administrator Registration',
        'lfa': 'Local Football Association Administrator Registration',
        'club': 'Club Administrator Registration',
        'association': 'Association Administrator Registration',
    }
    title = title_map.get(role_type, 'Administrator Registration')

    if request.method == 'POST':
        form = UniversalRegistrationForm(request.POST, request.FILES, registration_type=role_type)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'{user.get_role_display()} account created successfully!')
            return redirect('accounts:login')
        else:
            print("Form errors:", form.errors)
            # You might want more sophisticated error display here
            messages.error(request, 'Please correct the errors in the form below.')
    else:
        form = UniversalRegistrationForm(registration_type=role_type)

    return render(request, 'accounts/universal_admin_registration.html', {
        'form': form,
        'title': title,
        'role_type': role_type, # Pass role_type to template for JS logic
    })

def register(request):
    return admin_registration_view(request, role_type='universal') # Or a specific default if needed

def club_registration(request):
    return admin_registration_view(request, role_type='club')

def province_registration(request):
    return admin_registration_view(request, role_type='province')

def national_registration(request):
    return admin_registration_view(request, role_type='national')

def lfa_registration(request):
    return admin_registration_view(request, role_type='lfa')

def association_registration(request):
    return admin_registration_view(request, role_type='association')


def registration_portal(request):

    return render(request, 'accounts/registration_portal.html', {
        'title': 'SAFA Registration Portal'
    })

def check_username(request):

    email = request.GET.get('email', '')  # Changed from username to email
    if not email:
        return JsonResponse({'available': False})

    # Check if the email exists
    exists = CustomUser.objects.filter(email=email).exists()  # Changed from username to email

    return JsonResponse({'available': not exists})

@require_GET
def check_email_availability(request):

    email = request.GET.get('email', '').strip()

    if not email:
        return JsonResponse({'exists': False})

    exists = CustomUser.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})

@require_GET
def check_id_number_availability(request):

    id_number = request.GET.get('id_number', '').strip()

    if not id_number:
        return JsonResponse({'exists': False})

    exists = CustomUser.objects.filter(id_number=id_number).exists()
    return JsonResponse({'exists': exists})

def user_qr_code(request, user_id=None):

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
    #Handle profile photo updates
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

def api_associations_by_lfa(request):
    lfa_id = request.GET.get('lfa')
    print(f"DEBUG: api_associations_by_lfa called with lfa_id: {lfa_id}")

    if lfa_id:
        from geography.models import Association
        associations = Association.objects.filter(local_football_association=lfa_id).values('id', 'name')
        associations_list = list(associations)
        print(f"DEBUG: Found {len(associations_list)} associations: {associations_list}")
        return JsonResponse(associations_list, safe=False)

    print("DEBUG: No lfa_id provided")
    return JsonResponse([], safe=False)

def universal_registration(request):

    if request.method == 'POST':
        form = UniversalRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'{user.get_role_display()} account created successfully!')
            return redirect('accounts:login')
        else:
            print("Form errors:", form.errors)
            print("Province field value:", request.POST.get('province'))
            if hasattr(form.fields['province'], 'queryset'):
                print("Province field choices:", [(p.id, str(p)) for p in form.fields['province'].queryset])
            else:
                print("Province field doesn't have a queryset - it's type:", type(form.fields['province']))
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
            print("=== FORM ERRORS ===")
            for field, errors in form.errors.items():
                print(f"Field '{field}': {errors}")
            print(f"Non-field errors: {form.non_field_errors()}")
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
@role_required(allowed_roles=['ADMIN_LOCAL_FED'])
def lfa_admin_approvals(request):
    user = request.user
    # Only LFA admins can access
    if not user.local_federation: # Keep this check as it's specific to the LFA admin's data scope
        messages.error(request, 'Your profile is not linked to an LFA.')
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
    """Main dashboard view that routes users based on their role"""
    
    context = {'user': request.user}
    today = timezone.now().date()

    # Calculate age stats for players
    all_players = Player.objects.all()
    junior_players = 0
    senior_players = 0
    for player in all_players:
        if player.date_of_birth:
            age = today.year - player.date_of_birth.year - ((today.month, today.day) < (player.date_of_birth.month, player.date_of_birth.day))
            if age < 18:
                junior_players += 1
            else:
                senior_players += 1

    player_stats = {
        'total': all_players.count(),
        'approved': all_players.filter(is_approved=True).count(),
        'pending': all_players.filter(is_approved=False).count(),
        'junior': junior_players,
        'senior': senior_players,
    }
    
    if request.user.role == 'NATIONAL_ADMIN':
        context.update({
            'player_stats': player_stats,
            'pending_officials': Official.objects.filter(is_approved=False, status='PENDING').count(),
        })
        return render(request, 'accounts/dashboard_national_admin.html', context)
        
    elif request.user.role == 'NATIONAL_ACCOUNTS':
        invoices = Invoice.objects.select_related('player', 'official', 'club').all()
        
        summary = {
            'total_invoices': invoices.count(),
            'total_amount': invoices.aggregate(total=Sum('amount'))['total'] or 0,
            'paid_invoices': invoices.filter(status='PAID').count(),
            'paid_amount': invoices.filter(status='PAID').aggregate(total=Sum('amount'))['total'] or 0,
            'pending_invoices': invoices.filter(status='PENDING').count(),
            'pending_amount': invoices.filter(status='PENDING').aggregate(total=Sum('amount'))['total'] or 0,
            'overdue_invoices': invoices.filter(status='PENDING', due_date__lt=today).count(),
            'overdue_amount': invoices.filter(status='PENDING', due_date__lt=today).aggregate(total=Sum('amount'))['total'] or 0,
        }
        
        context.update({
            'summary': summary,
            'invoices': invoices.order_by('-created')[:50],
            'player_stats': player_stats, # Add player stats for context
        })
        return render(request, 'accounts/dashboard_national_accounts.html', context)
        
    elif request.user.role == 'CLUB_ADMIN':
        return render(request, 'accounts/dashboard_club_admin.html', context)
        
    elif request.user.role == 'ASSOCIATION_ADMIN':
        return render(request, 'accounts/dashboard_association_admin.html', context)
        
    else:
        # Default dashboard for other roles (including superuser)
        if request.user.is_superuser:
            context.update({
                'player_stats': player_stats,
                'total_users': CustomUser.objects.count(),
                'total_officials': Official.objects.count(),
                'total_clubs': Club.objects.count(),
            })
        return render(request, 'accounts/dashboard_default.html', context)


@login_required
@role_required(allowed_roles=['NATIONAL_ACCOUNTS', 'NATIONAL_ADMIN'], allow_superuser=True)
def invoice_detail_view(request, invoice_id):
    """A view for non-superusers to see invoice details."""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    context = {
        'invoice': invoice,
    }
    return render(request, 'accounts/invoice_detail.html', context)



from django.http import JsonResponse
from registration.models import Player

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

    id_number = request.GET.get('id_number', '').strip()

    if not id_number:
        return JsonResponse({'exists': False})

    exists = Player.objects.filter(id_number=id_number).exists()
    return JsonResponse({'exists': exists})

@require_GET
def ajax_check_passport_number(request):

    passport_number = request.GET.get('passport_number', '').strip()

    if not passport_number:
        return JsonResponse({'exists': False})

    exists = Player.objects.filter(passport_number=passport_number).exists()
    return JsonResponse({'exists': exists})

@require_GET
def ajax_check_sa_passport_number(request):

    sa_passport_number = request.GET.get('sa_passport_number', '').strip()
    player_id = request.GET.get('player_id', None)

    query = Player.objects.filter(sa_passport_number=sa_passport_number)
    if player_id:
        query = query.exclude(pk=player_id)

    exists = query.exists()
    return JsonResponse({'exists': exists})

@require_GET
def ajax_check_safa_id(request):

    safa_id = request.GET.get('safa_id', '').strip()
    player_id = request.GET.get('player_id', None)

    # Use Member model since SAFA ID is in the parent class
    from membership.models import Member
    query = Member.objects.filter(safa_id=safa_id)
    if player_id:
        query = query.exclude(pk=player_id)

    exists = query.exists()
    return JsonResponse({'exists': exists})

@require_GET
def ajax_check_fifa_id(request):

    fifa_id = request.GET.get('fifa_id', '').strip()
    player_id = request.GET.get('player_id', None)

    # Use Member model since FIFA ID is in the parent class
    from membership.models import Member
    query = Member.objects.filter(fifa_id=fifa_id)
    if player_id:
        query = query.exclude(pk=player_id)

    exists = query.exists()
    return JsonResponse({'exists': exists})

@login_required
@role_required(allowed_roles=['CLUB_ADMIN', 'LFA_ADMIN', 'REGION_ADMIN', 'PROVINCE_ADMIN', 'NATIONAL_ADMIN'], allow_superuser=True, allow_staff=True)
def player_approval_list(request):

    # Get players related to the admin's scope
    player_registrations = []

    # For superusers and staff, show all players
    if request.user.is_superuser or request.user.is_staff:
        player_registrations = PlayerClubRegistration.objects.all().select_related('player', 'club')
    # For club admins, show only their club's players
    elif hasattr(request.user, 'role') and request.user.role == 'CLUB_ADMIN' and hasattr(request.user, 'club') and request.user.club:
        player_registrations = PlayerClubRegistration.objects.filter(club=request.user.club).select_related('player', 'club')

    # For LFA admins, show players in clubs under their LFA
    elif hasattr(request.user, 'role') and request.user.role == 'LFA_ADMIN' and hasattr(request.user, 'lfa') and request.user.lfa:
        clubs = Club.objects.filter(local_football_association=request.user.lfa)
        player_registrations = PlayerClubRegistration.objects.filter(club__in=clubs).select_related('player', 'club')

    # For higher level admins, show players based on their jurisdiction
    elif hasattr(request.user, 'role') and request.user.role in ['REGION_ADMIN', 'PROVINCE_ADMIN', 'NATIONAL_ADMIN']:
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

    # Filter by approval status and make sure each player only appears once
    approval_status = request.GET.get('status', 'pending')
    invoice_filter_status = request.GET.get('invoice_status', 'all') # New filter for invoices

    # Import here to avoid circular imports
    from membership.models import Invoice

    # Use a dictionary to ensure each player only appears once
    unique_players = {}
    for reg in player_registrations:
        player = reg.player
        club = reg.club

        if player.id not in unique_players:
            # Apply approval status filter
            if (approval_status == 'pending' and not player.is_approved) or \
               (approval_status == 'approved' and player.is_approved) or \
               (approval_status not in ['pending', 'approved']):

                # Get all invoices for the player
                player_invoices = Invoice.objects.filter(player=player, invoice_type='REGISTRATION')
                unpaid_invoices = player_invoices.filter(status__in=['PENDING', 'OVERDUE'])
                paid_invoices = player_invoices.filter(status='PAID')

                # Apply invoice status filter
                if invoice_filter_status == 'unpaid' and not unpaid_invoices.exists():
                    continue # Skip if filtering for unpaid but no unpaid invoices
                if invoice_filter_status == 'paid' and not paid_invoices.exists():
                    continue # Skip if filtering for paid but no paid invoices

                # Add invoice details to the player data
                unique_players[player.id] = {
                    'player': player,
                    'club': club,
                    'unpaid_invoices': unpaid_invoices,
                    'paid_invoices': paid_invoices,
                    'has_unpaid_invoice': unpaid_invoices.exists()
                }

    # Convert back to a list of dictionaries
    players_data = list(unique_players.values())

    return render(request, 'accounts/player_approval_list.html', {
        'players_data': players_data,
        'approval_status': approval_status,
        'invoice_filter_status': invoice_filter_status,
    })

@login_required
@role_required(allowed_roles=['CLUB_ADMIN', 'LFA_ADMIN', 'REGION_ADMIN', 'PROVINCE_ADMIN', 'NATIONAL_ADMIN'])
def player_detail(request, safa_id):

    # Get player with prefetched invoices
    player = get_object_or_404(Player.objects.prefetch_related('invoices'), safa_id=safa_id)

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
@role_required(allowed_roles=['CLUB_ADMIN', 'LFA_ADMIN', 'REGION_ADMIN', 'PROVINCE_ADMIN', 'NATIONAL_ADMIN'])
def approve_player(request, safa_id):

    if request.method != 'POST':
        return redirect('accounts:player_approval_list')

    player = get_object_or_404(Player, safa_id=safa_id)

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
        from membership.models import Invoice
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
            return redirect('accounts:player_detail', safa_id=player.safa_id)

        # If there are missing requirements, don't approve and show message
        if missing_requirements:
            message = f"Cannot approve player. The following documents are missing: {', '.join(missing_requirements)}."
            messages.error(request, message)
            return redirect('accounts:player_detail', safa_id=player.safa_id)

        # All checks passed, approve the player
        player.is_approved = True
        player.status = 'ACTIVE'  # Update the status from PENDING to ACTIVE
        player.save()

        messages.success(request, f'Player {player.get_full_name()} has been approved.')
        return redirect('accounts:player_approval_list')

@login_required
@role_required(allowed_roles=['LFA_ADMIN', 'REGION_ADMIN', 'PROVINCE_ADMIN', 'NATIONAL_ADMIN'])
def unapprove_player(request, safa_id):

        if request.method != 'POST':
            return redirect('accounts:player_approval_list')

        player = get_object_or_404(Player, safa_id=safa_id)

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
@role_required(allowed_roles=['CLUB_ADMIN', 'LFA_ADMIN', 'REGION_ADMIN', 'PROVINCE_ADMIN', 'NATIONAL_ADMIN'])
def edit_player(request, safa_id):

        player = get_object_or_404(Player, safa_id=safa_id)

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
                return redirect('accounts:player_detail', safa_id=player.safa_id)
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

        # Import here to avoid circular imports
        from membership.models import Invoice

        # Check permission based on user role
        is_association = request.GET.get('association') == 'true'

        if is_association:
            # Association admin viewing invoices
            if not (request.user.is_superuser or request.user.is_staff or
                    (getattr(request.user, 'role', None) == 'ASSOCIATION_ADMIN')):
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('accounts:dashboard')

            if not (request.user.is_superuser or request.user.is_staff) and (not hasattr(request.user, 'association') or not request.user.association):
                messages.error(request, 'Your profile is not linked to an association.')
                return redirect('accounts:dashboard')

            # Get all invoices for this association (or all for superusers)
            if request.user.is_superuser or request.user.is_staff:
                # Superusers can see all association invoices
                status = request.GET.get('status')
                if status:
                    invoices = Invoice.objects.filter(
                        association__isnull=False,
                        status=status
                    ).select_related('official', 'association')
                else:
                    invoices = Invoice.objects.filter(
                        association__isnull=False
                    ).select_related('official', 'association')
                entity = None  # No specific entity for superusers
            else:
                association = request.user.association
                # Filter by status if provided
                status = request.GET.get('status')
                if status:
                    invoices = Invoice.objects.filter(
                        association=association,
                        status=status
                    ).select_related('official')
                else:
                    invoices = Invoice.objects.filter(
                        association=association
                    ).select_related('official')
                entity = association
            template = 'accounts/association_invoices.html'
        else:
            # Club admin viewing invoices
            if not (request.user.is_superuser or request.user.is_staff or
                    (getattr(request.user, 'role', None) == 'CLUB_ADMIN')):
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('accounts:dashboard')

            if not (request.user.is_superuser or request.user.is_staff) and (not hasattr(request.user, 'club') or not request.user.club):
                messages.error(request, 'Your profile is not linked to a club.')
                return redirect('accounts:dashboard')

            # Get all invoices for this club (or all for superusers)
            if request.user.is_superuser or request.user.is_staff:
                # Superusers can see all club invoices
                status = request.GET.get('status')
                if status:
                    invoices = Invoice.objects.filter(
                        club__isnull=False,
                        status=status
                    ).select_related('player', 'club')
                else:
                    invoices = Invoice.objects.filter(
                        club__isnull=False
                    ).select_related('player', 'club')
                entity = None  # No specific entity for superusers
            else:
                club = request.user.club
                # Filter by status if provided
                status = request.GET.get('status')
                if status:
                    invoices = Invoice.objects.filter(
                        club=club,
                        status=status
                    ).select_related('player')
                else:
                    invoices = Invoice.objects.filter(
                        club=club
                    ).select_related('player')
                entity = club
            template = 'accounts/club_invoices.html'

        # Calculate summary statistics
        summary = {
            'total_invoices': invoices.count(),
            'total_amount': sum(invoice.amount for invoice in invoices),
            'pending_invoices': invoices.filter(status='PENDING').count(),
            'pending_amount': sum(invoice.amount for invoice in invoices.filter(status='PENDING')),
            'overdue_invoices': invoices.filter(status='OVERDUE').count(),
            'overdue_amount': sum(invoice.amount for invoice in invoices.filter(status='OVERDUE')),
            'paid_invoices': invoices.filter(status='PAID').count(),
            'paid_amount': sum(invoice.amount for invoice in invoices.filter(status='PAID')),
        }

        # If this is an association, use club_invoices.html but pass is_association flag
        if is_association:
            return render(request, 'accounts/club_invoices.html', {
                'club': entity,
                'invoices': invoices,
                'summary': summary,
                'selected_status': status,
                'is_association': True
            })
        else:
            return render(request, 'accounts/club_invoices.html', {
                'club': entity,
                'invoices': invoices,
                'summary': summary,
                'selected_status': status,
                'is_association': False
            })

@login_required
@role_required(allowed_roles=['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_COUNTRY'])
def player_statistics(request):

        # Import models
        from geography.models import Province, Region, LocalFootballAssociation, Club
        from registration.models import Player
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
                approved_count=Count('player_registrations__player', distinct=True,\
                    filter=Q(player_registrations__player__is_approved=True)),\
                pending_count=Count('player_registrations__player', distinct=True,\
                    filter=Q(player_registrations__player__is_approved=False))\
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
                approved_count=Count('clubs__player_registrations__player', distinct=True,\
                    filter=Q(clubs__player_registrations__player__is_approved=True)),\
                pending_count=Count('clubs__player_registrations__player', distinct=True,\
                    filter=Q(clubs__player_registrations__player__is_approved=False))\
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
                approved_count=Count('localfootballassociations__clubs__player_registrations__player', distinct=True,\
                    filter=Q(localfootballassociations__clubs__player_registrations__player__is_approved=True)),\
                pending_count=Count('localfootballassociations__clubs__player_registrations__player', distinct=True,\
                    filter=Q(localfootballassociations__clubs__player_registrations__player__is_approved=False))\
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
                approved_count=Count('regions__localfootballassociations__clubs__player_registrations__player', distinct=True,\
                    filter=Q(regions__localfootballassociations__clubs__player_registrations__player__is_approved=True)),\
                pending_count=Count('regions__localfootballassociations__clubs__player_registrations__player', distinct=True,\
                    filter=Q(regions__localfootballassociations__clubs__player_registrations__player__is_approved=False))\
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

@login_required
@role_required(allowed_roles=['CLUB_ADMIN'])
def club_admin_add_official(request):

        if not request.user.club:
            messages.error(request, 'Your user profile is not linked to a club. Please contact support.')
            return redirect('accounts:dashboard')

        if request.method == 'POST':
            official_form = ClubAdminOfficialRegistrationForm(request.POST, request.FILES)
            # Store request in form to allow showing document validation warnings
            official_form.request = request
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
                        official_form.data = official_form.data.copy()
                        official_form.data['date_of_birth'] = dob.isoformat()

                        # Also set gender based on ID number
                        gender_digit = int(id_number[6])
                        official_form.data['gender'] = 'M' if gender_digit >= 5 else 'F'
                    except ValueError:
                        # Invalid date in ID number, will be caught in form validation
                        pass
                except (ValueError, IndexError):
                    # Invalid ID number, will be caught in form validation
                    pass

            # Generate a unique email for the official before checking form validity
            if 'first_name' in request.POST and 'last_name' in request.POST:
                first_name = request.POST['first_name']
                last_name = request.POST['last_name']

                # Generate unique email using position name as a prefix
                position_id = request.POST.get('position')
                position_prefix = 'official'

                if position_id:
                    try:
                        from .models import Position
                        position = Position.objects.get(pk=position_id)
                        position_prefix = position.title.lower().replace(' ', '')
                    except (Position.DoesNotExist, ValueError):
                        position_prefix = 'official'

                # Generate unique email
                unique_email = f"{position_prefix}.{first_name.lower()}.{last_name.lower()}@{request.user.club.name.lower().replace(' ', '')}.safa.net"

                # Set the email in the form data
                official_form.data = official_form.data.copy()
                official_form.data['email'] = unique_email

            if official_form.is_valid():
                # Generate a unique SAFA ID if one wasn't provided
                if not official_form.cleaned_data.get('safa_id'):
                    from .utils import generate_unique_safa_id
                    try:
                        unique_safa_id = generate_unique_safa_id()
                        official_form.instance.safa_id = unique_safa_id
                    except Exception as e:
                        messages.warning(request, f"Could not generate a unique SAFA ID: {e}")

                # Extract email and password from form
                email = official_form.cleaned_data.get('email')
                password = official_form.cleaned_data.get('password')

                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,  # ✅ Password is hashed here
                    first_name=official_form.cleaned_data['first_name'],
                    last_name=official_form.cleaned_data['last_name']
                )

                user.is_active = True  # Ensure user is active
                user.save()

                # Save official with club reference
                official = official_form.save(commit=False)
                official.user = user
                official.club = request.user.club
                official.province = request.user.province
                official.region = request.user.region
                official.local_federation = request.user.local_federation

                # Set organization_type to CLUB type
                try:
                    from accounts.models import OrganizationType
                    # Try to get an organization type with CLUB level
                    club_type = OrganizationType.objects.filter(
                        level='CLUB'
                    ).first()

                    # If not found, create one
                    if not club_type:
                        club_type = OrganizationType.objects.create(
                            name="Club",
                            level="CLUB",
                            requires_approval=True,
                            is_active=True
                        )
                        print(f"[DEBUG - CLUB OFFICIAL REG] Created new organization type: {club_type}")

                    official.organization_type = club_type
                    print(f"[DEBUG - CLUB OFFICIAL REG] Set organization type to: {club_type}")
                except Exception as e:
                    print(f"[DEBUG - CLUB OFFICIAL REG] Error setting organization type: {e}")

                official.save()

                # Create invoice for the official
                from .utils import create_official_invoice
                position = official_form.cleaned_data.get('position')
                position_type = position.title if position else None

                invoice = create_official_invoice(
                    official=official,
                    club=request.user.club,
                    issued_by=official,  # Using official as issued_by as they don't have a separate Member instance
                    position_type=position_type
                )

                # Associate with appropriate referee/coach associations if needed
                position_title = position.title.lower() if position else ""
                if "referee" in position_title or "coach" in position_title:
                    from geography.models import Association

                    # Find relevant associations by type
                    association_type = "referee" if "referee" in position_title else "coach"
                    associations = Association.objects.filter(
                        type__icontains=association_type,
                        local_football_association=request.user.local_federation
                    )

                    # Link to associations
                    if associations.exists():
                        for association in associations:
                            official.associations.add(association)

                # If this is a referee with a level, create a certification record
                referee_level = official_form.cleaned_data.get('referee_level')
                if referee_level and "referee" in position_title:
                    from membership.models import OfficialCertification

                    # Create certification record
                    certification = OfficialCertification(
                        official=official,
                        certification_type='REFEREE',\
                        level=referee_level,
                        name=f"Referee Level {referee_level}",
                        issuing_body="SAFA",
                        certification_number=official_form.cleaned_data.get('certification_number'),
                        obtained_date=timezone.now().date(),
                        expiry_date=official_form.cleaned_data.get('certification_expiry_date'),
                        document=official_form.cleaned_data.get('certification_document'),
                        notes="Initial certification registered with official",
                        is_verified=False  # Requires verification
                    )
                    certification.save()

                success_message = f'Official registered successfully with email {official.email}!'
                if invoice:
                    success_message += f' An invoice (#{invoice.invoice_number}) has been created.'
                    base_fee = "250" if "referee" in position_title else "200" if "coach" in position_title else "150"
                    success_message += f' Registration fee: R{base_fee}.'
                    success_message += ' Official will be eligible for approval once the invoice is paid.'

                messages.success(request, success_message)
                return redirect('accounts:official_list')
            else:
                # Add a summary error message at the top without showing specific fields
                messages.error(request, 'Please correct the errors in the form below.')
        else:
            official_form = ClubAdminOfficialRegistrationForm()

        return render(request, 'accounts/club_admin_add_official.html', {
            'official_form': official_form
        })

@login_required
def official_list(request):
        """View for listing club officials"""

        # Club admins can see officials in their own club
        if request.user.role == 'CLUB_ADMIN':
            if not request.user.club:
                messages.error(request, 'Your profile is not linked to a club.')
                return redirect('accounts:dashboard')

            officials = Official.objects.filter(club=request.user.club).order_by('-created')

        # LFA admins can see officials across clubs in their LFA
        elif request.user.role == 'ADMIN_LOCAL_FED':
            if not request.user.local_federation:
                messages.error(request, 'Your profile is not linked to an LFA.')
                return redirect('accounts:dashboard')

            officials = Official.objects.filter(
                local_federation=request.user.local_federation
            ).order_by('-created')

        # Region admins can see officials across LFAs in their region
        elif request.user.role == 'ADMIN_REGION':
            if not request.user.region:
                messages.error(request, 'Your profile is not linked to a region.')
                return redirect('accounts:dashboard')

            officials = Official.objects.filter(
                region=request.user.region
            ).order_by('-created')

        # Province admins can see officials across regions in their province
        elif request.user.role == 'ADMIN_PROVINCE':
            if not request.user.province:
                messages.error(request, 'Your profile is not linked to a province.')
                return redirect('accounts:dashboard')

            officials = Official.objects.filter(
                province=request.user.province
            ).order_by('-created')

        # National admins can see all officials
        elif request.user.role == 'ADMIN_NATIONAL' or request.user.is_superuser:
            officials = Official.objects.all().order_by('-created')

        # Association admins can see officials in their association
        elif request.user.role == 'ASSOCIATION_ADMIN':
            if not request.user.association:
                messages.error(request, 'Your profile is not linked to an association.')
                return redirect('accounts:dashboard')

            # Find officials that are part of this association (either through primary_association or the many-to-many relationship)
            officials = Official.objects.filter(
                Q(primary_association=request.user.association) |
                Q(associations=request.user.association)
            ).distinct().order_by('-created')

        # Other users don't have access
        else:
            messages.error(request, 'You do not have permission to view officials.')
            return redirect('accounts:dashboard')

        # Count officials by position
        position_counts = {}
        for official in officials:
            if official.position:
                position_name = official.position.title
                if position_name in position_counts:
                    position_counts[position_name] += 1
                else:
                    position_counts[position_name] = 1

        # Sort by position count (descending)
        sorted_positions = sorted(position_counts.items(), key=lambda x: x[1], reverse=True)

        # Ensure all officials have their primary_association set
        for official in officials:
            if hasattr(official, 'primary_association') and not official.primary_association:
                # Try to find if this official has a SAFRA association
                if official.associations.filter(id=11).exists():
                    try:
                        from geography.models import Association
                        safra = Association.objects.get(id=11)
                        official.primary_association = safra
                        official.save(update_fields=['primary_association'])
                        print(f"[DEBUG - OFFICIALS LIST] Set primary_association for {official.get_full_name()} to SAFRA")
                    except Exception as e:
                        print(f"[DEBUG - OFFICIALS LIST] Error setting SAFRA as primary_association: {e}")

        # Force prefetch of primary_association to avoid N+1 queries
        officials = officials.select_related('primary_association', 'user__association')

        return render(request, 'accounts/official_list.html', {
            'officials': officials,
            'position_counts': sorted_positions,
            'total_count': officials.count()
        })

@login_required
@role_required(allowed_roles=['CLUB_ADMIN', 'ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ASSOCIATION_ADMIN', 'ADMIN_NATIONAL'], allow_superuser=True)
def official_detail(request, official_id):
        """View details of an official"""
        official = get_object_or_404(Official, id=official_id)

        # Check permissions
        has_permission = False

        # Get certifications
        certifications = official.certifications.all().order_by('-obtained_date')

        # Get associations
        associations = official.associations.all()

        # Debug log to see if primary association is set
        if hasattr(official, 'primary_association') and official.primary_association:
            print(f"[DEBUG - OFFICIAL DETAIL] Official has primary_association: {official.primary_association.name} (ID: {official.primary_association.id})")
        else:
            print("[DEBUG - OFFICIAL DETAIL] Official has no primary_association")

            # Try to find association with ID 11 (SAFRA) and set it as primary
            try:
                from geography.models import Association
                safra = Association.objects.filter(id=11).first()
                if safra:
                    print(f"[DEBUG - OFFICIAL DETAIL] Found SAFRA: {safra.name} (ID: {safra.id})")
                    official.primary_association = safra
                    official.save(update_fields=['primary_association'])
                    print("[DEBUG - OFFICIAL DETAIL] Set primary_association to SAFRA")

                    # Also ensure it's in the M2M relationship
                    if not official.associations.filter(id=11).exists():
                        official.associations.add(safra)
                        print("[DEBUG - OFFICIAL DETAIL] Added SAFRA to associations M2M")
                else:
                    print("[DEBUG - OFFICIAL DETAIL] SAFRA with ID 11 not found")
            except Exception as e:
                print(f"[DEBUG - OFFICIAL DETAIL] Error setting SAFRA as primary_association: {e}")

        # Get invoices
        from membership.models import Invoice
        invoices = Invoice.objects.filter(official=official)

        # Check if user can approve official
        can_approve = request.user.role in ['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'NATIONAL_ADMIN'] or request.user.is_superuser

        # Today's date for checking expiry
        today = timezone.now().date()

        context = {
            'official': official,
            'certifications': certifications,
            'associations': associations,
            'invoices': invoices,
            'can_approve': can_approve,
            'today': today,
            'referee_level': official.referee_level,
        }

        return render(request, 'accounts/official_detail.html', context)


@login_required
@role_required(allowed_roles=['CLUB_ADMIN', 'LFA_ADMIN', 'REGION_ADMIN', 'PROVINCE_ADMIN', 'NATIONAL_ADMIN', 'ASSOCIATION_ADMIN'])
def edit_official(request, official_id):

    official = get_object_or_404(Official, id=official_id)

    # Check if the admin has permission to edit this official
    has_permission = False
    if request.user.role == 'CLUB_ADMIN' and hasattr(request.user, 'club') and request.user.club:
        has_permission = official.club == request.user.club
    elif request.user.role == 'LFA_ADMIN' and hasattr(request.user, 'local_federation') and request.user.local_federation:
        has_permission = official.local_federation == request.user.local_federation
    elif request.user.role == 'REGION_ADMIN' and hasattr(request.user, 'region') and request.user.region:
        has_permission = official.region == request.user.region
    elif request.user.role == 'PROVINCE_ADMIN' and hasattr(request.user, 'province') and request.user.province:
        has_permission = official.province == request.user.province
    elif request.user.role == 'ASSOCIATION_ADMIN' and hasattr(request.user, 'association') and request.user.association:
        has_permission = official.primary_association == request.user.association or official.associations.filter(id=request.user.association.id).exists()
    elif request.user.role == 'NATIONAL_ADMIN' or request.user.is_superuser:
        has_permission = True

    if not has_permission:
        messages.error(request, 'You do not have permission to edit this official.')
        return redirect('accounts:official_list')

    if request.method == 'POST':
        form = ClubAdminOfficialRegistrationForm(request.POST, request.FILES, instance=official)
        if form.is_valid():
            form.save()
            messages.success(request, 'Official updated successfully.')
            return redirect('accounts:official_detail', official_id=official.id)
    else:
        form = ClubAdminOfficialRegistrationForm(instance=official)

    return render(request, 'accounts/edit_official.html', {
        'official': official,
        'form': form
    })

@login_required
@role_required(allowed_roles=['CLUB_ADMIN', 'ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_NATIONAL'], allow_superuser=True)
def add_official_certification(request, official_id):
        """Add a certification to an official"""
        official = get_object_or_404(Official, id=official_id)

        # Check permissions - only club admins for their own club, or higher level admins
        has_permission = False

        if request.method == 'POST':
            form = OfficialCertificationForm(request.POST, request.FILES)
            if form.is_valid():
                certification = form.save(commit=False)
                certification.official = official

                # Only admin levels above club can directly verify certifications
                if request.user.role in ['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_NATIONAL'] or request.user.is_superuser:
                    certification.is_verified = True

                certification.save()

                messages.success(request, 'Certification added successfully.')

                # Check if this is a referee certification and update official's referee_level if needed
                if certification.certification_type == 'REFEREE' and not official.referee_level:
                    official.referee_level = certification.level
                    official.save()
                    messages.info(request, f"Updated official's referee level to {certification.get_level_display()}.")

                return redirect('accounts:official_detail', official_id=official.id)
        else:
            form = OfficialCertificationForm()

        return render(request, 'accounts/add_official_certification.html', {
            'form': form,
            'official': official
        })

@login_required
@role_required(allowed_roles=['CLUB_ADMIN', 'ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_NATIONAL'], allow_superuser=True)
def manage_official_associations(request, official_id):
        """Manage associations linked to an official"""
        official = get_object_or_404(Official, id=official_id)

        # Check permissions - only admins can manage associations
        has_permission = False

        from geography.models import Association

        # Get all available associations
        position_type = ""
        if official.position:
            position_type = official.position.title.lower()

        # Filter associations based on the position
        if "referee" in position_type:
            filter_type = "referee"
        elif "coach" in position_type:
            filter_type = "coach"
        else:
            filter_type = ""

        all_associations = Association.objects.all()
        if filter_type:
            all_associations = all_associations.filter(type__icontains=filter_type)

        # Get current associations
        current_associations = official.associations.all()

        if request.method == 'POST':
            # Process form submission
            selected_associations = request.POST.getlist('associations')

            # Update associations
            official.associations.clear()
            if selected_associations:
                for assoc_id in selected_associations:
                    try:
                        association = Association.objects.get(id=assoc_id)
                        official.associations.add(association)
                    except Association.DoesNotExist:
                        continue

            messages.success(request, f'Associations updated successfully for {official.get_full_name()}.')
            return redirect('accounts:official_detail', official_id=official.id)

        context = {
            'official': official,
            'all_associations': all_associations,
            'current_associations': current_associations,
            'position_type': position_type
        }

        return render(request, 'accounts/manage_official_associations.html', context)

@login_required
@role_required(allowed_roles=['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'NATIONAL_ADMIN'], allow_superuser=True)
def approve_official(request, official_id):
        """Approve an official registration"""
        official = get_object_or_404(Official, id=official_id)

        # Check if the official has any unpaid invoices
        from membership.models import Invoice
        unpaid_invoices = Invoice.objects.filter(official=official, status__in=['PENDING', 'OVERDUE'])

        if unpaid_invoices.exists():
            messages.error(request, 'Official cannot be approved until all registration invoices are paid.')
            return redirect('accounts:official_detail', official_id=official.id)

        # Approve the official
        official.is_approved = True
        official.status = 'ACTIVE'
        official.save()

        messages.success(request, f'Official {official.get_full_name()} has been approved.')
        return redirect('accounts:official_detail', official_id=official.id)

@login_required
@role_required(allowed_roles=['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'NATIONAL_ADMIN'], allow_superuser=True)
def unapprove_official(request, official_id):
        """Unapprove an official registration"""
        official = get_object_or_404(Official, id=official_id)

        # Unapprove the official
        official.is_approved = False
        official.status = 'PENDING'
        official.save()

        messages.success(request, f'Official {official.get_full_name()} has been unapproved and status set to pending.')
        return redirect('accounts:official_detail', official_id=official.id)

@login_required
@role_required(allowed_roles=['ASSOCIATION_ADMIN'])
def association_admin_add_official(request):

    if not request.user.association:
        messages.error(request, 'Your user profile is not linked to an association. Please contact support.')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        official_form = AssociationOfficialRegistrationForm(request.POST, request.FILES)
        # Store request in form to allow showing document validation warnings
        official_form.request = request
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
                    official_form.data = official_form.data.copy()
                    official_form.data['date_of_birth'] = dob.isoformat()

                    # Also set gender based on ID number
                    gender_digit = int(id_number[6])
                    official_form.data['gender'] = 'M' if gender_digit >= 5 else 'F'
                except ValueError:
                    # Invalid date in ID number, will be caught in form validation
                    pass
            except (ValueError, IndexError):
                # Invalid ID number, will be caught in form validation
                pass

        # Generate a unique email for the official before checking form validity
        if 'first_name' in request.POST and 'last_name' in request.POST:
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']

            # Generate unique email using position name as a prefix
            position_id = request.POST.get('position')
            position_prefix = 'official'

            if position_id:
                try:
                    from .models import Position
                    position = Position.objects.get(pk=position_id)
                    position_prefix = position.title.lower().replace(' ', '')
                except (Position.DoesNotExist, ValueError):
                    position_prefix = 'official'

            # Generate unique email
            unique_email = f"{position_prefix}.{first_name.lower()}.{last_name.lower()}@{request.user.association.acronym.lower()}.safa.net"

            # Set the email in the form data
            official_form.data = official_form.data.copy()
            official_form.data['email'] = unique_email

        if official_form.is_valid():
            # Generate a unique SAFA ID if one wasn't provided
            if not official_form.cleaned_data.get('safa_id'):
                from .utils import generate_unique_safa_id
                try:
                    unique_safa_id = generate_unique_safa_id()
                    official_form.instance.safa_id = unique_safa_id
                except Exception as e:
                    messages.warning(request, f"Could not generate a unique SAFA ID: {e}")

            # Extract email and password from form
            email = official_form.cleaned_data.get('email')
            password = official_form.cleaned_data.get('password')

            user = CustomUser.objects.create_user(
                email=email,
                password=password,  # ✅ Password is hashed here
                first_name=official_form.cleaned_data['first_name'],
                last_name=official_form.cleaned_data['last_name']
            )

            user.is_active = True  # Ensure user is active
            user.save()

            # Save official with association reference
            official = official_form.save(commit=False)
            official.user = user
            official.primary_association = request.user.association
            official.province = request.user.province
            official.region = request.user.region
            official.local_federation = request.user.local_federation

            # Set organization_type to ASSOCIATION type
            try:
                from accounts.models import OrganizationType
                # Try to get an organization type with ASSOCIATION level
                association_type_obj = OrganizationType.objects.filter(
                    level='ASSOCIATION'
                ).first()

                # If not found, create one
                if not association_type_obj:
                    association_type_obj = OrganizationType.objects.create(
                        name="Association",
                        level="ASSOCIATION",
                        requires_approval=True,
                        is_active=True
                    )
                    print(f"[DEBUG - ASSOC OFFICIAL REG] Created new organization type: {association_type_obj}")

                official.organization_type = association_type_obj
                print(f"[DEBUG - ASSOC OFFICIAL REG] Set organization type to: {association_type_obj}")
            except Exception as e:
                print(f"[DEBUG - ASSOC OFFICIAL REG] Error setting organization type: {e}")

            official.save()

            # Create invoice for the official
            from .utils import create_official_invoice
            position = official_form.cleaned_data.get('position')
            position_type = position.title if position else None

            invoice = create_official_invoice(
                official=official,
                association=request.user.association,
                issued_by=official,  # Using official as issued_by as they don't have a separate Member instance
                position_type=position_type
            )

            # Associate with appropriate referee/coach associations if needed
            position_title = position.title.lower() if position else ""
            if "referee" in position_title or "coach" in position_title:
                from geography.models import Association

                # Find relevant associations by type
                association_type = "referee" if "referee" in position_title else "coach"
                associations = Association.objects.filter(
                    type__icontains=association_type,
                    local_football_association=request.user.local_federation
                )

                # Link to associations
                if associations.exists():
                    for association_obj in associations:
                        official.associations.add(association_obj)

            # If this is a referee with a level, create a certification record
            referee_level = official_form.cleaned_data.get('referee_level')
            if referee_level and "referee" in position_title:
                from membership.models import OfficialCertification

                # Create certification record
                certification = OfficialCertification(
                    official=official,
                    certification_type='REFEREE',\
                    level=referee_level,
                    name=f"Referee Level {referee_level}",
                    issuing_body="SAFA",
                    certification_number=official_form.cleaned_data.get('certification_number'),
                    obtained_date=timezone.now().date(),
                    expiry_date=official_form.cleaned_data.get('certification_expiry_date'),
                    document=official_form.cleaned_data.get('certification_document'),
                    notes="Initial certification registered with official",
                    is_verified=False  # Requires verification
                )
                certification.save()

            success_message = f"Official registered successfully with email {official.email}!"
            if invoice:
                success_message += f" An invoice (#{invoice.invoice_number}) has been created."
                base_fee = "250" if "referee" in position_title else "200" if "coach" in position_title else "150"
                success_message += f" Registration fee: R{base_fee}."
                success_message += " Official will be eligible for approval once the invoice is paid."

            messages.success(request, success_message)
            return redirect('accounts:official_list')
        else:
            # Add a summary error message at the top without showing specific fields
            messages.error(request, 'Please correct the errors in the form below.')
    else:
        official_form = AssociationOfficialRegistrationForm()

    return render(request, 'accounts/association_admin_add_official.html', {
        'official_form': official_form
    })

def national_member_list(request):

    if not request.user.is_authenticated:
        return redirect('accounts:login')

    # Only national admins and superusers can view this list
    if not (request.user.is_superuser or request.user.role == 'ADMIN_NATIONAL'):
        messages.error(request, 'You do not have permission to view the national member list.')
        return redirect('accounts:dashboard')

    members = Member.objects.all().order_by('last_name', 'first_name')

    context = {
        'members': members,
        'title': 'National Member List'
    }
    return render(request, 'accounts/national_member_list.html', context)
