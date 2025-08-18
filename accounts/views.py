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
from .email_templates import send_welcome_email, send_rejection_email, send_approval_email, send_support_request_email

from .forms import (
    EmailAuthenticationForm, PlayerForm, NationalAdminRegistrationForm, RejectMemberForm,
    ClubAdminAddPlayerForm, MemberApprovalForm, AdvancedSearchForm, ContactSupportForm,
    ProfileForm, SettingsForm, UpdateProfilePhotoForm
)
from .models import CustomUser, Organization, OrganizationType, Position, UserRole, Notification
from .stats_view import get_dashboard_stats
from .utils import generate_unique_safa_id

logger = logging.getLogger(__name__)


class ModernLoginView(LoginView):
    """Modern login view with enhanced security and UX"""
    form_class = EmailAuthenticationForm
    template_name = 'accounts/modern_login.html'
    redirect_authenticated_user = True


def modern_home(request):
    if request.user.is_authenticated:
        # Redirect based on user role or show a generic dashboard
        return redirect('accounts:profile')
    return render(request, 'accounts/modern_home.html')


@login_required
def national_registration(request):
    if request.method == 'POST':
        form = NationalAdminRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.role = 'ADMIN_NATIONAL'
            user.save()
            messages.success(request, 'National Administrator registered successfully.')
            return redirect('accounts:modern_home')
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


class ModernLoginView(LoginView):
    """Modern login view with enhanced security and UX"""
    authentication_form = EmailAuthenticationForm
    template_name = 'accounts/modern_login.html'
    redirect_authenticated_user = True

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['email'].widget.attrs['placeholder'] = 'Email Address'
        return form


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
    try:
        user_role = UserRole.objects.get(user=request.user)
        organization = user_role.organization

        if organization.organization_type.name == 'Local Football Association':
            clubs_in_lfa = Club.objects.filter(lfa=organization)
            members_to_approve = Member.objects.filter(club__in=clubs_in_lfa, status='Pending Approval')
        elif organization.organization_type.name == 'Region':
            members_to_approve = Member.objects.none()  # Placeholder
        else:
            members_to_approve = Member.objects.none()

    except UserRole.DoesNotExist:
        members_to_approve = Member.objects.none()
        messages.error(request, "You are not associated with any organization.")

    if request.method == 'POST':
        form = MemberApprovalForm(request.POST)
        if form.is_valid():
            member = form.cleaned_data['member']
            is_approved = form.cleaned_data['is_approved']
            if is_approved:
                member.status = 'Approved'
                member.save()
                send_approval_email(member.user)
                messages.success(request, f"Member {member.user.get_full_name()} approved.")
    else:
        form = MemberApprovalForm()

    context = {
        'members_to_approve': members_to_approve,
        'form': form
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
    form = AdvancedSearchForm()
    results = None
    if 'query' in request.GET:
        form = AdvancedSearchForm(request.GET)
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
        form = ContactSupportForm(request.POST)
        if form.is_valid():
            support_request = form.save(commit=False)
            if request.user.is_authenticated:
                support_request.user = request.user
            support_request.save()

            send_support_request_email(support_request)

            messages.success(request, "Your support request has been sent. We will get back to you shortly.")
            return redirect('accounts:home')
    else:
        form = ContactSupportForm()
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
