import logging
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_GET, require_POST

from geography.models import Club, LocalFootballAssociation, Region, Province
from membership.models import Member, Invoice
from .utils import send_welcome_email, send_rejection_email, send_approval_email, send_support_request_email, get_dashboard_stats

from .forms import (
    PlayerForm, NationalAdminRegistrationForm, RejectMemberForm,
    ClubAdminAddPlayerForm, MemberApprovalForm, AdvancedMemberSearchForm, ModernContactForm,
    ProfileForm, SettingsForm, UpdateProfilePhotoForm
)
from .models import CustomUser, OrganizationType, Position, UserRole, Notification
from .utils import generate_unique_safa_id

logger = logging.getLogger(__name__)





def modern_home(request):
    if request.user.is_authenticated:
        # Redirect based on user role or show a generic dashboard
        return redirect('accounts:profile')
    return render(request, 'accounts/modern_home.html')


def national_registration(request):
    if request.method == 'POST':
        form = NationalAdminRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create CustomUser object but don't save yet
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])

            # Set the legacy role based on organization type
            org_type = form.cleaned_data['organization_type']
            if org_type.name == 'National Federation':
                user.role = 'ADMIN_NATIONAL'
            elif org_type.name == 'Province':
                user.role = 'ADMIN_PROVINCE'
                user.province = form.cleaned_data.get('province')
            elif org_type.name == 'Region':
                user.role = 'ADMIN_REGION'
                user.region = form.cleaned_data.get('region')
            elif org_type.name == 'Local Football Association':
                user.role = 'ADMIN_LOCAL_FED'
                user.local_federation = form.cleaned_data.get('local_federation')
            elif org_type.name == 'Club':
                user.role = 'CLUB_ADMIN'
                user.club = form.cleaned_data.get('club')

            # Set user status to pending approval
            user.membership_status = 'PENDING'
            user.is_active = True # User can login but will be restricted by status
            user.save()

            # Create the corresponding Member profile
            Member.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                role='ADMIN', # All admins are of role 'ADMIN' in the Member model
                status='PENDING',
                # Add other relevant fields from the form
                date_of_birth=user.date_of_birth,
                gender=user.gender,
                id_number=user.id_number,
                passport_number=user.passport_number,
                current_club=form.cleaned_data.get('club'),
                province=form.cleaned_data.get('province'),
                region=form.cleaned_data.get('region'),
                lfa=form.cleaned_data.get('local_federation'),
            )

            # Create the UserRole
            UserRole.objects.create(
                user=user,
                organization=org_type,
                position=form.cleaned_data['position']
            )

            messages.success(request, 'Registration successful. Your application is pending approval.')
            return redirect('accounts:home')
    else:
        form = NationalAdminRegistrationForm()
    return render(request, 'accounts/national_registration.html', {'form': form})


# Placeholder functions for missing utilities
def get_admin_jurisdiction_queryset(user):
    if user.is_superuser or user.role == 'ADMIN_NATIONAL':
        return CustomUser.objects.all()

    if user.role == 'ADMIN_PROVINCE':
        return CustomUser.objects.filter(province=user.province)

    if user.role == 'ADMIN_REGION':
        return CustomUser.objects.filter(region=user.region)

    if user.role == 'ADMIN_LOCAL_FED':
        return CustomUser.objects.filter(local_federation=user.local_federation)

    if user.role == 'CLUB_ADMIN':
        return CustomUser.objects.filter(club=user.club)

    return CustomUser.objects.none()


def can_approve_member(user, member):
    if user.is_superuser or user.role == 'ADMIN_NATIONAL':
        return True

    if user.role == 'ADMIN_PROVINCE' and member.province == user.province:
        return True

    if user.role == 'ADMIN_REGION' and member.region == user.region:
        return True

    if user.role == 'ADMIN_LOCAL_FED' and member.local_federation == user.local_federation:
        return True

    if user.role == 'CLUB_ADMIN' and member.club == user.club:
        return True

    return False


def get_user_notifications(user):
    # This should return a list of notifications for the user
    return []


def get_national_admin_stats():
    # This should return a dictionary of stats for the national admin
    return {}


def get_financial_stats():
    # This should return a dictionary of financial stats
    return {}


def get_regional_admin_stats(user):
    # This should return a dictionary of stats for the regional admin
    return {}


def get_club_stats(club):
    # This should return a dictionary of stats for the club admin
    return {}


def get_association_stats(association):
    # This should return a dictionary of stats for the association admin
    return {}





@login_required
def club_admin_add_player(request):
    if request.user.role != 'CLUB_ADMIN':
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('accounts:modern_home')

    if request.method == 'POST':
        form = ClubAdminAddPlayerForm(request.POST, request.FILES)
        if form.is_valid():
            player = form.save(commit=False)
            player.role = 'PLAYER'
            player.club = request.user.club
            # Set a random password for the new player
            password = get_random_string(12)
            player.set_password(password)
            player.save()
            messages.success(request, f"Player {player.get_full_name()} added successfully.")
            return redirect('accounts:modern_home')
    else:
        form = ClubAdminAddPlayerForm()

    context = {
        'form': form,
        'title': 'Add New Player'
    }
    return render(request, 'accounts/club_admin_add_player.html', context)


@login_required
def get_regions_for_province(request):
    province_id = request.GET.get('province_id')
    regions = Region.objects.filter(province_id=province_id).order_by('name')
    return JsonResponse(list(regions.values('id', 'name')), safe=False)


@login_required
def get_lfas_for_region(request):
    region_id = request.GET.get('region_id')
    lfas = LocalFootballAssociation.objects.filter(region_id=region_id).order_by('name')
    return JsonResponse(list(lfas.values('id', 'name')), safe=False)


@login_required
def get_clubs_for_lfa(request):
    lfa_id = request.GET.get('lfa_id')
    clubs = Club.objects.filter(lfa_id=lfa_id).order_by('name')
    return JsonResponse(list(clubs.values('id', 'name')), safe=False)


@login_required
def profile(request):
    user_roles = UserRole.objects.filter(user=request.user)
    organizations = [role.organization for role in user_roles]

    if user_roles:
        current_role = user_roles.first()
        organization = current_role.organization
        position = current_role.position

        stats = get_dashboard_stats(organization)

        context = {
            'user': request.user,
            'organization': organization,
            'position': position,
            'stats': stats,
            'user_roles': user_roles,
            'current_role': current_role,
        }
        return render(request, 'accounts/profile.html', context)

    return render(request, 'accounts/profile.html', {'user': request.user, 'organization': None})


@login_required
def switch_organization(request):
    if request.method == 'POST':
        role_id = request.POST.get('role_id')
        try:
            role = UserRole.objects.get(id=role_id, user=request.user)
            request.session['current_role_id'] = role.id
            messages.success(request, f"Switched to role: {role.position.name} at {role.organization.name}")
        except UserRole.DoesNotExist:
            messages.error(request, "Invalid role selected.")
    return redirect('accounts:profile')


@login_required
def notification_center(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'accounts/notification_center.html', {'notifications': notifications})


@require_POST
@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})


def health_check(request):
    return HttpResponse("OK")


@login_required
def member_approvals_list(request):
    members_to_approve = Member.objects.none()

    if request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'ADMIN_NATIONAL'):
        members_to_approve = Member.objects.filter(status='PENDING')
    else:
        # Placeholder for other admin roles, can be expanded later
        messages.error(request, "You do not have permission to view this page.")
        return redirect('accounts:home')

    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        member = get_object_or_404(Member, id=member_id)

        if 'approve' in request.POST:
            member.status = 'ACTIVE'
            member.approved_by = request.user
            member.approved_date = timezone.now()
            member.save()

            # Also update the CustomUser status
            if member.user:
                member.user.membership_status = 'ACTIVE'
                member.user.save()

            # Generate invoice
            try:
                Invoice.create_member_invoice(member)
                messages.success(request, f"Member {member.get_full_name()} approved and invoice created.")
            except Exception as e:
                messages.error(request, f"Member approved, but failed to create invoice: {e}")

            # send_approval_email(member.user) # This can be re-enabled later

        elif 'reject' in request.POST:
            rejection_reason = request.POST.get('rejection_reason')
            if rejection_reason:
                member.status = 'REJECTED'
                member.rejection_reason = rejection_reason
                member.save()

                if member.user:
                    member.user.membership_status = 'REJECTED'
                    member.user.save()

                # send_rejection_email(member.user, rejection_reason) # Re-enable later
                messages.success(request, f"Member {member.get_full_name()} has been rejected.")
            else:
                messages.error(request, "Rejection reason is required.")

        return redirect('accounts:member_approvals_list')

    context = {
        'members_to_approve': members_to_approve,
    }
    return render(request, 'accounts/member_approvals_list.html', context)


@login_required
def reject_member(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    if request.method == 'POST':
        form = RejectMemberForm(request.POST)
        if form.is_valid():
            rejection_reason = form.cleaned_data['rejection_reason']
            member.status = 'Rejected'
            member.rejection_reason = rejection_reason
            member.save()

            send_rejection_email(member.user, rejection_reason)

            messages.success(request, f"Member {member.user.get_full_name()} has been rejected.")
            return redirect('accounts:member_approvals_list')
    else:
        form = RejectMemberForm()

    return render(request, 'accounts/reject_member.html', {'form': form, 'member': member})


@login_required
def advanced_search(request):
    form = AdvancedMemberSearchForm()
    results = None
    if 'query' in request.GET:
        form = AdvancedMemberSearchForm(request.GET)
        if form.is_valid():
            results = form.search()

    return render(request, 'accounts/advanced_search.html', {'form': form, 'results': results})


@login_required
def statistics(request):
    stats = {
        'total_users': CustomUser.objects.count(),
        'total_members': Member.objects.count(),
        'members_by_province': (Member.objects
                               .values('club__lfa__region__province__name')
                               .annotate(count=Count('id'))
                               .order_by('-count'))
    }
    return render(request, 'accounts/statistics.html', {'stats': stats})


@login_required
def dashboard_stats_api(request):
    user_role = UserRole.objects.filter(user=request.user).first()
    if not user_role:
        return JsonResponse({'error': 'User has no role'}, status=403)

    stats = get_dashboard_stats(user_role.organization)
    return JsonResponse(stats)


@login_required
def search_members_api(request):
    query = request.GET.get('q', '')
    members = Member.objects.filter(
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(safa_id__icontains=query)
    ).select_related('user', 'club')[:10]

    results = [{
        'id': member.id,
        'name': member.user.get_full_name(),
        'safa_id': member.safa_id,
        'club': member.club.name if member.club else 'N/A'
    } for member in members]

    return JsonResponse(results, safe=False)


@require_POST
@login_required
def quick_approve_member(request):
    member_id = request.POST.get('member_id')
    try:
        member = Member.objects.get(id=member_id)
        member.status = 'Approved'
        member.save()
        send_approval_email(member.user)
        return JsonResponse({'status': 'success', 'message': f'Member {member.user.get_full_name()} approved.'})
    except Member.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Member not found.'}, status=404)


@login_required
def get_organization_types_api(request):
    types = OrganizationType.objects.all()
    return JsonResponse(list(types.values('id', 'name')), safe=False)


@login_required
def get_positions_for_org_type_api(request):
    org_type_id = request.GET.get('organization_type_id')
    positions = Position.objects.filter(organization_type_id=org_type_id)
    return JsonResponse(list(positions.values('id', 'name')), safe=False)


def contact_support(request):
    if request.method == 'POST':
        form = ModernContactForm(request.POST)
        if form.is_valid():
            support_request = form.save(commit=False)
            if request.user.is_authenticated:
                support_request.user = request.user
            support_request.save()

            send_support_request_email(support_request)

            messages.success(request, "Your support request has been sent. We will get back to you shortly.")
            return redirect('accounts:home')
    else:
        form = ModernContactForm()
    return render(request, 'accounts/contact_support.html', {'form': form})


@login_required
def my_invoices(request):
    return render(request, 'accounts/my_invoices.html')


@login_required
def settings(request):
    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your settings have been updated.")
            return redirect('accounts:settings')
    else:
        form = SettingsForm(instance=request.user)
    return render(request, 'accounts/settings.html', {'form': form})


@login_required
def registration_portal(request):
    return render(request, 'accounts/registration_portal.html')


@login_required
@require_POST
def update_profile_photo(request):
    form = UpdateProfilePhotoForm(request.POST, request.FILES, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Profile photo updated successfully.")
    else:
        messages.error(request, "Failed to update profile photo.")
    return redirect('accounts:profile')


@login_required
def eligible_clubs_api(request):
    return JsonResponse([], safe=False)


@login_required
def members_api(request):
    return JsonResponse([], safe=False)


@login_required
def self_register_member_api(request):
    return JsonResponse({}, safe=False)


@login_required
def transfers_api(request):
    return JsonResponse([], safe=False)


@login_required
def approve_transfer_api(request, transfer_id):
    return JsonResponse({})


@login_required
def member_season_history_api(request, member_id):
    return JsonResponse([], safe=False)


@login_required
def member_history_by_club_api(request):
    return JsonResponse([], safe=False)


@login_required
def seasonal_analysis_api(request):
    return JsonResponse([], safe=False)


@login_required
def member_associations_api(request, member_id):
    return JsonResponse([], safe=False)


@login_required
def senior_membership_dashboard(request):
    return render(request, 'membership/senior_membership_dashboard.html')


@login_required
def club_invoices(request):
    invoices = []
    context = {
        'title': 'Club Invoices',
        'invoices': invoices,
    }
    return render(request, 'accounts/club_invoices.html', context)


def custom_403_view(request, exception=None):
    return render(request, 'errors/403.html', status=403)


def custom_404_view(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def custom_500_view(request):
    return render(request, 'errors/500.html', status=500)


from django.contrib.auth import logout
from .decorators import role_required
from geography.models import Province, Region, LocalFootballAssociation, Association, Club
from geography.models import ClubStatus

def custom_admin_logout(request):
    logout(request)
    return redirect('/')

@role_required(allowed_roles=['ADMIN_NATIONAL'])
def national_admin_dashboard(request):
    org_data = [
        ('province', Province.objects.all(), 'Provinces'),
        ('region', Region.objects.all(), 'Regions'),
        ('lfa', LocalFootballAssociation.objects.all(), 'Local Football Associations'),
        ('association', Association.objects.all(), 'Associations'),
        ('club', Club.objects.all(), 'Clubs'),
    ]

    context = {
        'org_data': org_data,
        'ClubStatus': ClubStatus
    }
    return render(request, 'accounts/national_admin_dashboard.html', context)

@require_POST
@role_required(allowed_roles=['ADMIN_NATIONAL'])
def update_organization_status(request):
    org_type = request.POST.get('org_type')
    org_id = request.POST.get('org_id')
    new_status = request.POST.get('new_status')

    model_map = {
        'province': Province,
        'region': Region,
        'lfa': LocalFootballAssociation,
        'association': Association,
        'club': Club,
    }

    model = model_map.get(org_type)
    if not model or not org_id or not new_status:
        messages.error(request, "Invalid request.")
        return redirect(request.META.get('HTTP_REFERER', 'accounts:home'))

    org = get_object_or_404(model, id=org_id)

    valid_statuses = [choice[0] for choice in ClubStatus.choices]
    if new_status not in valid_statuses:
        messages.error(request, "Invalid status.")
        return redirect(request.META.get('HTTP_REFERER', 'accounts:home'))

    org.status = new_status
    org.save()

    messages.success(request, f"Status for {org.name} has been updated to {new_status}.")
    return redirect('accounts:national_admin_dashboard')
