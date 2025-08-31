import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_GET, require_POST
from datetime import date

from geography.models import (Association, Club, ClubStatus, Country,
                              LocalFootballAssociation, NationalFederation,
                              Province, Region)
from membership.models import Invoice, Member, RegistrationWorkflow, InvoiceItem
from supporters.models import SupporterProfile

from .decorators import role_required
from .forms import (
    AdvancedMemberSearchForm, ClubAdminAddPlayerForm,
    ClubAdminRegistrationForm, ModernContactForm, ProfileForm,
    RejectMemberForm, RegistrationForm, SettingsForm,
    UpdateProfilePhotoForm, EditPlayerForm, ConfirmPaymentForm)
from geography.forms import (
    ProvinceComplianceForm,
    RegionComplianceForm,
    LFAComplianceForm,
    AssociationComplianceForm,
    ClubComplianceForm,
)
from .models import (
    CustomUser, Notification, OrganizationType, Position,
                   UserRole)
import qrcode
import base64
from io import BytesIO
from .utils import (
    generate_unique_safa_id,
    get_dashboard_stats,
    send_approval_email,
    send_rejection_email,
    send_support_request_email
)

logger = logging.getLogger(__name__)


def modern_home(request):
    if request.user.is_authenticated:
        try:
            role = request.user.role
            if role == 'ADMIN_NATIONAL':
                return redirect('accounts:national_admin_dashboard')
            elif role == 'ADMIN_PROVINCE':
                return redirect('accounts:provincial_admin_dashboard')
            elif role == 'ADMIN_REGION':
                return redirect('accounts:regional_admin_dashboard')
            elif role == 'ADMIN_LOCAL_FED':
                return redirect('accounts:lfa_admin_dashboard')
            elif role == 'CLUB_ADMIN':
                return redirect('accounts:club_admin_dashboard')
            elif role == 'ASSOCIATION_ADMIN':
                return redirect('accounts:association_admin_dashboard')
            else:
                # Default redirect for other authenticated users
                return redirect('accounts:profile')
        except AttributeError:
            messages.warning(request, "Your user profile is not fully configured. Please contact support.")
            return redirect('accounts:profile')

    # For anonymous users
    return render(request, 'accounts/modern_home.html')


def user_registration(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            is_existing = form.cleaned_data.get('is_existing_member')
            previous_safa_id = form.cleaned_data.get('previous_safa_id')

            # Create the CustomUser object first, but don't save if we might link to an existing member
            user = form.save(commit=False)

            # This is a new member registration
            user.save() # Ensure user is saved before creating member
            national_federation = NationalFederation.objects.first()
            if not national_federation:
                country = Country.objects.get(name='South Africa')
                national_federation = NationalFederation.objects.create(name='SAFA', country=country)

            member_data = {
                'user': user,
                'safa_id': user.safa_id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'role': user.role,
                'status': 'PENDING',
                'date_of_birth': user.date_of_birth,
                'gender': user.gender,
                'id_number': user.id_number,
                'passport_number': user.passport_number,
                'street_address': user.street_address,
                'suburb': user.suburb,
                'city': user.city,
                'state': user.state,
                'postal_code': user.postal_code,
                'national_federation': national_federation,
            }

            if user.role != 'SUPPORTER':
                member_data.update({
                    'province': form.cleaned_data.get('province'),
                    'region': form.cleaned_data.get('region'),
                    'lfa': form.cleaned_data.get('lfa'),
                    'current_club': form.cleaned_data.get('club'),
                })

            member = Member.objects.create(**member_data)

            association = form.cleaned_data.get('association')
            if association:
                member.associations.add(association)

            # Common logic for both new and existing members starts here

            # Sync data to CustomUser
            user.national_federation = member.national_federation
            user.province = member.province
            user.region = member.region
            user.local_federation = member.lfa
            user.club = member.current_club
            user.association = member.associations.first()
            user.popi_act_consent = form.cleaned_data.get('popi_act_consent', False)
            user.save()

            # Create SupporterProfile
            if user.role == 'SUPPORTER':
                SupporterProfile.objects.get_or_create(user=user, defaults={'safa_id': user.safa_id})

            # Login the user
            login(request, user)

            # Handle workflow and invoicing
            workflow, _ = RegistrationWorkflow.objects.get_or_create(member=member)
            # Unconditionally set the status after a successful registration form submission
            workflow.personal_info_status = 'COMPLETED'
            workflow.club_selection_status = 'COMPLETED'
            workflow.document_upload_status = 'COMPLETED' # Assume docs are optional for now
            workflow.current_step = 'PAYMENT'
            workflow.save()

            invoice = Invoice.create_member_invoice(member)

            if invoice:
                messages.success(request, 'Registration successful! Please complete payment to proceed.')
                return redirect('membership:invoice_detail', uuid=invoice.uuid)
            else:
                workflow.payment_status = 'COMPLETED'
                workflow.current_step = 'SAFA_APPROVAL'
                workflow.save()
                messages.success(request, 'Registration successful. Your application is pending approval.')
                return redirect('accounts:modern_home')

    else:
        form = RegistrationForm()
    return render(request, 'accounts/user_registration.html', {'form': form})


# ... (the rest of the file remains the same) ...

# Placeholder functions for missing utilities
def get_admin_jurisdiction_queryset(user):
    if user.is_superuser or user.role == 'ADMIN_NATIONAL':
        return CustomUser.objects.all()

    if user.role == 'ADMIN_PROVINCE':
        return CustomUser.objects.filter(province=user.province)

    if user.role == 'ADMIN_REGION':
        return CustomUser.objects.filter(region=user.region)

    if user.role == 'ADMIN_LOCAL_FED':
        return CustomUser.objects.filter(
            local_federation=user.local_federation)

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

    if user.role == 'ADMIN_LOCAL_FED' and \
            member.local_federation == user.local_federation:
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
        messages.error(
            request, "You do not have permission to perform this action.")
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
            messages.success(
                request,
                f"Player {player.get_full_name()} added successfully.")
            return redirect('accounts:modern_home')
    else:
        form = ClubAdminAddPlayerForm()

    context = {
        'form': form,
        'title': 'Add New Player'
    }
    return render(request, 'accounts/club_admin_add_player.html', context)


def get_regions_for_province(request, province_id):
    try:
        regions = Region.objects.filter(province_id=province_id).order_by('name')
        return JsonResponse(list(regions.values('id', 'name')), safe=False)
    except Exception as e:
        logger.error(f"Error in get_regions_for_province for province_id {province_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def get_lfas_for_region(request, region_id):
    try:
        lfas = LocalFootballAssociation.objects.filter(
            region_id=region_id).order_by('name')
        return JsonResponse(list(lfas.values('id', 'name')), safe=False)
    except Exception as e:
        logger.error(f"Error in get_lfas_for_region for region_id {region_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def get_clubs_for_lfa(request, lfa_id):
    try:
        clubs = Club.objects.filter(
            localfootballassociation_id=lfa_id).order_by('name')
        return JsonResponse(list(clubs.values('id', 'name')), safe=False)
    except Exception as e:
        logger.error(f"Error in get_clubs_for_lfa for lfa_id {lfa_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def profile(request):
    try:
        member = request.user.member_profile
    except Member.DoesNotExist:
        member = None

    context = {
        'user': request.user,
        'member': member,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def generate_digital_card(request):
    try:
        member = request.user.member_profile
    except Member.DoesNotExist:
        messages.error(request, "You do not have a member profile to generate a card.")
        return redirect('accounts:profile')

    # Information to be encoded in the QR code
    profile_url = request.build_absolute_uri(reverse('accounts:profile'))
    qr_data = f"SAFA Member: {member.get_full_name()}\nSAFA ID: {member.safa_id}\nProfile: {profile_url}"

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Save QR code to a BytesIO buffer and encode it in base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    context = {
        'member': member,
        'user': request.user,
        'qr_code': qr_code_base64,
    }
    return render(request, 'accounts/digital_card.html', context)


@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save()
            # Also update the related Member profile
            try:
                member = user.member_profile
                member.street_address = user.street_address
                member.suburb = user.suburb
                member.city = user.city
                member.state = user.state
                member.postal_code = user.postal_code
                member.save()
            except Member.DoesNotExist:
                pass # Or handle cases where a user might not have a member profile
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = ProfileForm(instance=user)
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def switch_organization(request):
    if request.method == 'POST':
        role_id = request.POST.get('role_id')
        try:
            role = UserRole.objects.get(id=role_id, user=request.user)
            request.session['current_role_id'] = role.id
            messages.success(
                request,
                f"Switched to role: {role.position.name} at "
                f"{role.organization.name}")
        except UserRole.DoesNotExist:
            messages.error(request, "Invalid role selected.")
    return redirect('accounts:profile')


@login_required
def notification_center(request):
    notifications = Notification.objects.filter(
        user=request.user).order_by('-timestamp')
    return render(
        request,
        'accounts/notification_center.html',
        {'notifications': notifications})


@require_POST
@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(
        Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})


def health_check(request):
    return HttpResponse("OK")


@login_required
def member_approvals_list(request):
    logger.debug(f"member_approvals_list called. GET params: {request.GET}")
    member_id = request.GET.get('member_id')
    
    # Initial queryset before any member_id filtering
    workflows_initial = RegistrationWorkflow.objects.filter(current_step='SAFA_APPROVAL').select_related('member__user')
    logger.debug(f"Workflows in SAFA_APPROVAL (initial count): {workflows_initial.count()}")
    for wf in workflows_initial:
        logger.debug(f"Initial Workflow: Member ID={wf.member.id}, User Email={wf.member.user.email}, Current Step={wf.current_step}")

    workflows = workflows_initial # Start with the initial queryset

    if member_id:
        logger.debug(f"Member ID from GET: {member_id}")
        try:
            member_id = int(member_id)
            workflows = workflows.filter(member__id=member_id)
            logger.debug(f"Workflows after filtering by member_id {member_id} (count): {workflows.count()}")
        except ValueError:
            messages.error(request, "Invalid member ID provided.")
            logger.error(f"Invalid member ID provided: {member_id}")
            return redirect('accounts:member_approvals_list')

    # In a real-world scenario, you would filter this based on the admin's jurisdiction
    # For now, we assume a national admin can see all.
    if not request.user.is_superuser and request.user.role != 'ADMIN_NATIONAL':
        messages.error(request, "You do not have permission to view this page.")
        logger.warning(f"User {request.user.email} attempted to access member_approvals_list without permission.")
        return redirect('accounts:modern_home')

    members_to_approve = [wf.member for wf in workflows]
    logger.debug(f"Members to approve (final count): {len(members_to_approve)}")
    for member in members_to_approve:
        logger.debug(f"Final Member in list: ID={member.id}, Email={member.user.email}, Status={member.status}")

    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        member = get_object_or_404(Member, id=member_id)
        user = member.user

        if 'approve' in request.POST:
            # Check for parental consent for minors
            if user.age and user.age < 18 and not user.parental_consent:
                messages.error(request, "Cannot approve a junior member without parental consent.")
                return redirect('accounts:member_approvals_list')

            # Update user and member status
            user.membership_status = 'ACTIVE'
            user.is_approved = True
            user.save()

            member.status = 'ACTIVE'
            member.approved_by = request.user
            member.approved_date = timezone.now()
            member.save()

            # Update workflow
            try:
                workflow = member.workflow
                workflow.safa_approval_status = 'COMPLETED'
                workflow.current_step = 'COMPLETE'
                workflow.save()
            except RegistrationWorkflow.DoesNotExist:
                pass # Should not happen in this flow

            messages.success(request, f"Member {user.get_full_name()} has been approved.")

        elif 'reject' in request.POST:
            rejection_reason = request.POST.get('rejection_reason', 'No reason provided.')
            user.membership_status = 'REJECTED'
            user.save()

            member.status = 'REJECTED'
            member.rejection_reason = rejection_reason
            member.save()

            # Optionally, you could move the workflow back or to a 'REJECTED' state
            try:
                workflow = member.workflow
                workflow.safa_approval_status = 'BLOCKED' # Or a new 'REJECTED' status
                workflow.save()
            except RegistrationWorkflow.DoesNotExist:
                pass

            messages.warning(request, f"Member {user.get_full_name()} has been rejected.")

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

            messages.success(
                request,
                f"Member {member.user.get_full_name()} has been rejected.")
            return redirect('accounts:member_approvals_list')
    else:
        form = RejectMemberForm()

    return render(
        request,
        'accounts/reject_member.html',
        {'form': form, 'member': member})


@login_required
def advanced_search(request):
    form = AdvancedMemberSearchForm()
    results = None
    if 'query' in request.GET:
        form = AdvancedMemberSearchForm(request.GET)
        if form.is_valid():
            results = form.search()

    return render(
        request,
        'accounts/advanced_search.html',
        {'form': form, 'results': results})


@login_required
def statistics(request):
    stats = {
        'total_users': CustomUser.objects.count(),
        'total_members': Member.objects.count(),
        'members_by_province': (
            Member.objects
            .values('current_club__name') # Simplified to just club name
            .annotate(count=Count('id'))
            .order_by('-count')
        )
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
        return JsonResponse({
            'status': 'success',
            'message': f'Member {member.user.get_full_name()} approved.'
        })
    except Member.DoesNotExist:
        return JsonResponse(
            {'status': 'error', 'message': 'Member not found.'}, status=404)


@login_required
def get_organization_types_api(request):
    types = OrganizationType.objects.all()
    return JsonResponse(list(types.values('id', 'name')), safe=False)


@login_required
def get_positions_for_org_type_api(request):
    org_type_id = request.GET.get('organization_type_id')
    positions = Position.objects.filter(
        organization_type_id=org_type_id)
    return JsonResponse(list(positions.values('id', 'name')), safe=False)


@require_GET
def check_id_number(request):
    id_number = request.GET.get('id_number', None)
    if id_number:
        exists = CustomUser.objects.filter(id_number=id_number).exists()
        return JsonResponse({'exists': exists})
    return JsonResponse({'exists': False})


def contact_support(request):
    if request.method == 'POST':
        form = ModernContactForm(request.POST)
        if form.is_valid():
            support_request = form.save(commit=False)
            if request.user.is_authenticated:
                support_request.user = request.user
            support_request.save()

            send_support_request_email(support_request)

            messages.success(
                request,
                "Your support request has been sent. We will get back to you "
                "shortly.")
            return redirect('accounts:modern_home')
    else:
        form = ModernContactForm()
    return render(request, 'accounts/contact_support.html', {'form': form})


@login_required
def my_invoices(request):
    """Display a list of invoices for the logged-in user."""
    try:
        # Invoices are linked to the Member model, which is linked to the User
        invoices = Invoice.objects.filter(member__user=request.user).order_by('-issue_date')
    except Invoice.DoesNotExist:
        invoices = []
    
    context = {
        'invoices': invoices,
        'title': 'My Invoices'
    }
    return render(request, 'accounts/my_invoices.html', context)


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
    form = UpdateProfilePhotoForm(
        request.POST, request.FILES, instance=request.user)
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


@login_required
@role_required(allowed_roles=['ADMIN_NATIONAL', 'ADMIN_PROVINCE', 'ADMIN_REGION', 'ADMIN_LOCAL_FED', 'CLUB_ADMIN', 'ASSOCIATION_ADMIN'])
def member_cards_admin(request):
    # Placeholder for logic to display/manage member cards for admins
    # This could involve listing members, generating cards, etc.
    context = {
        'title': 'Member Cards Management',
        'members': [], # Replace with actual member query
    }
    return render(request, 'accounts/member_cards_admin.html', context)


def custom_403_view(request, exception=None):
    return render(request, 'errors/403.html', status=403)

def custom_404_view(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def custom_500_view(request):
    return render(request, 'errors/500.html', status=500)

def custom_admin_logout(request):
    logout(request)
    return redirect('/')


@role_required(allowed_roles=['ADMIN_NATIONAL'])
def national_admin_dashboard(request):
    org_lists = {
        'province': Province.objects.all(),
        'region': Region.objects.all(),
        'lfa': LocalFootballAssociation.objects.all(),
        'association': Association.objects.all(),
        'club': Club.objects.all(),
    }

    paginators = {
        org_type: Paginator(queryset, 10)
        for org_type, queryset in org_lists.items()
    }

    page_numbers = {
        org_type: request.GET.get(f'{org_type}_page', 1)
        for org_type in org_lists.keys()
    }

    org_data = {
        org_type: paginator.get_page(page_numbers[org_type])
        for org_type, paginator in paginators.items()
    }

    # Financial Summary
    total_paid = Invoice.objects.filter(
        status='PAID').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_outstanding = Invoice.objects.filter(
        status='PENDING'
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Pending Approvals
    pending_provinces = Province.objects.filter(status='INACTIVE')
    pending_regions = Region.objects.filter(status='INACTIVE')
    pending_lfas = LocalFootballAssociation.objects.filter(
        status='INACTIVE')
    pending_associations = Association.objects.filter(status='INACTIVE')
    pending_clubs = Club.objects.filter(status='INACTIVE')

    # Correctly fetch members awaiting approval from the workflow
    workflows = RegistrationWorkflow.objects.filter(completion_percentage=100).select_related('member__user', 'member__current_club')
    pending_members = [wf.member for wf in workflows]

    # All Members list
    all_members_list = CustomUser.objects.all().order_by('first_name', 'last_name')
    member_paginator = Paginator(all_members_list, 10)
    member_page_number = request.GET.get('member_page', 1)
    members_page = member_paginator.get_page(member_page_number)


    context = {
        'org_data': org_data,
        'ClubStatus': ClubStatus,
        'total_paid': total_paid,
        'total_outstanding': total_outstanding,
        'pending_provinces': pending_provinces,
        'pending_regions': pending_regions,
        'pending_lfas': pending_lfas,
        'pending_associations': pending_associations,
        'pending_clubs': pending_clubs,
        'members_page': members_page,
        'pending_members': pending_members,
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
        return redirect(request.META.get('HTTP_REFERER', 'accounts:modern_home'))

    org = get_object_or_404(model, id=org_id)

    valid_statuses = [choice[0] for choice in ClubStatus.choices]
    if new_status not in valid_statuses:
        messages.error(request, "Invalid status.")
        return redirect(request.META.get('HTTP_REFERER', 'accounts:modern_home'))

    org.status = new_status
    org.save()

    messages.success(
        request,
        f"Status for {org.name} has been updated to {new_status}.")
    return redirect('accounts:national_admin_dashboard')


@login_required
def national_finance_dashboard(request):
    return render(request, 'accounts/national_finance_dashboard.html')


@role_required(allowed_roles=['ADMIN_PROVINCE'])
def provincial_admin_dashboard(request):
    user_province = request.user.province
    regions = []
    if user_province:
        regions = user_province.region_set.all()
    
    context = {
        'user_province': user_province,
        'regions': regions,
    }
    return render(request, 'accounts/provincial_admin_dashboard.html', context)


@login_required
def regional_admin_dashboard(request):
    user_region = request.user.region
    lfas = []
    if user_region:
        lfas = user_region.localfootballassociation_set.all()

    context = {
        'user_region': user_region,
        'lfas': lfas,
    }
    return render(request, 'accounts/regional_admin_dashboard.html', context)


@login_required
def lfa_admin_dashboard(request):
    lfa = request.user.local_federation
    clubs = []
    if lfa:
        clubs = lfa.clubs.all()

    # Pending Approvals for this LFA
    pending_members = []
    if lfa:
        workflows = RegistrationWorkflow.objects.filter(
            member__lfa=lfa,
            completion_percentage=100
        ).select_related('member__user', 'member__current_club')
        pending_members = [wf.member for wf in workflows]

    context = {
        'lfa': lfa,
        'clubs': clubs,
        'pending_members': pending_members,
    }
    return render(request, 'accounts/lfa_admin_dashboard.html', context)


@login_required
def club_admin_dashboard(request):
    club = request.user.club
    players = CustomUser.objects.filter(club=club)

    # Player breakdown
    juniors = 0
    seniors = 0
    for player in players:
        if player.age and player.age < 18:
            juniors += 1
        elif player.age and player.age >= 18:
            seniors += 1

    male_players = players.filter(gender='M').count()
    female_players = players.filter(gender='F').count()

    # Pending Approvals for this Club
    pending_members = []
    if club:
        workflows = RegistrationWorkflow.objects.filter(
            member__current_club=club,
            completion_percentage=100
        ).select_related('member__user', 'member__current_club')
        pending_members = [wf.member for wf in workflows]

    context = {
        'club': club,
        'players': players,
        'juniors': juniors,
        'seniors': seniors,
        'male_players': male_players,
        'female_players': female_players,
        'pending_members': pending_members,
    }
    return render(request, 'accounts/club_admin_dashboard.html', context)


@login_required
def association_admin_dashboard(request):
    association = request.user.association
    # Pending Approvals for this Association
    pending_members = []
    if association:
        workflows = RegistrationWorkflow.objects.filter(
            member__associations=association,
            completion_percentage=100
        ).select_related('member__user', 'member__current_club')
        pending_members = [wf.member for wf in workflows]

    context = {
        'association': association,
        'pending_members': pending_members,
    }
    return render(request, 'accounts/association_admin_dashboard.html', context)


@login_required
def edit_player(request, player_id):
    player = get_object_or_404(CustomUser, id=player_id)
    redirect_url = request.GET.get('next', None)

    if request.method == 'POST':
        form = EditPlayerForm(request.POST, instance=player)
        if form.is_valid():
            form.save()
            logger.debug(f"Adding success message for player update: {player.get_full_name()}")
            messages.success(request, f'Player {player.get_full_name()} updated successfully.')

            # Redirect back to the original page, or a default if 'next' is not provided
            if redirect_url:
                return redirect(redirect_url)
            else:
                # Default redirection logic based on user role
                if request.user.role == 'CLUB_ADMIN':
                    return redirect('accounts:club_admin_dashboard')
                elif request.user.role == 'ADMIN_NATIONAL':
                    return redirect('accounts:national_admin_dashboard')
                else:
                    return redirect('accounts:profile') # Fallback
    else:
        form = EditPlayerForm(instance=player)

    context = {
        'form': form,
        'player': player,
        'next': redirect_url, # Pass 'next' to the template if needed
    }
    return render(request, 'accounts/edit_player.html', context)


@login_required
def approve_player(request, player_id):
    player = get_object_or_404(CustomUser, id=player_id)
    if player.age < 18 and not player.parental_consent:
        messages.error(request, "Cannot approve a junior member without parental consent.")
        return redirect('accounts:club_admin_dashboard')

    player.membership_status = 'ACTIVE'
    player.save()
    messages.success(request, f'Player {player.get_full_name()} approved successfully.')
    return redirect('accounts:club_admin_dashboard')


@login_required
def club_management_dashboard(request):
    return render(request, 'accounts/club_management_dashboard.html')


@login_required
@role_required(allowed_roles=['CLUB_ADMIN'])
def club_admin_add_person(request):
    """
    Allows a Club Admin to register a new Player or Official for their club.
    The form will be pre-populated with the admin's geographic details.
    """
    if request.method == 'POST':
        # Pass the admin's user object to the form to handle disabled fields
        form = RegistrationForm(request.POST, request.FILES, user=request.user, limit_role_choices=True)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Set a random password for the new user
            password = get_random_string(12)
            user.set_password(password)
            
            # Set the club and geographic info from the logged-in admin
            admin_user = request.user
            user.club = admin_user.club
            if admin_user.club:
                lfa = admin_user.club.localfootballassociation
                user.local_federation = lfa
                if lfa:
                    region = lfa.region
                    user.region = region
                    if region:
                        user.province = region.province
            
            user.save()

            # Create the corresponding Member record
            Member.objects.create(
                user=user,
                safa_id=user.safa_id,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                role=form.cleaned_data.get('role'),
                status='ACTIVE', # Players/Officials added by admins are auto-approved at club level
                date_of_birth=user.date_of_birth,
                gender=user.gender,
                id_number=user.id_number,
                passport_number=user.passport_number,
                current_club=user.club,
                province=user.province,
                region=user.region,
                lfa=user.local_federation,
                registration_method='CLUB'
            )
            
            messages.success(request, f"{form.cleaned_data.get('role').capitalize()} '{user.get_full_name()}' was added successfully. A temporary password has been set.")
            return redirect('accounts:club_admin_dashboard')
    else:
        # Pre-fill the form with the admin's club info
        initial_data = {}
        if request.user.club:
            initial_data['club'] = request.user.club
            if request.user.club.localfootballassociation:
                initial_data['lfa'] = request.user.club.localfootballassociation
                if request.user.club.localfootballassociation.region:
                    initial_data['region'] = request.user.club.localfootballassociation.region
                    if request.user.club.localfootballassociation.region.province:
                        initial_data['province'] = request.user.club.localfootballassociation.region.province

        form = RegistrationForm(initial=initial_data, user=request.user, limit_role_choices=True)

    context = {
        'form': form,
        'title': 'Add New Player or Official'
    }
    return render(request, 'accounts/user_registration.html', context)


@login_required
def province_compliance_view(request):
    province = request.user.province
    if not province:
        messages.error(request, "You are not associated with a province.")
        return redirect('accounts:modern_home')

    if request.method == 'POST':
        form = ProvinceComplianceForm(request.POST, request.FILES, instance=province)
        if form.is_valid():
            form.save()
            messages.success(request, 'Province compliance updated successfully.')
            return redirect('accounts:province_compliance_view')
    else:
        form = ProvinceComplianceForm(instance=province)

    context = {
        'province': province,
        'form': form,
    }
    return render(request, 'accounts/province_compliance.html', context)


@login_required
def region_compliance_view(request):
    region = request.user.region
    if not region:
        messages.error(request, "You are not associated with a region.")
        return redirect('accounts:modern_home')

    if request.method == 'POST':
        form = RegionComplianceForm(request.POST, request.FILES, instance=region)
        if form.is_valid():
            form.save()
            messages.success(request, 'Region compliance updated successfully.')
            return redirect('accounts:region_compliance_view')
    else:
        form = RegionComplianceForm(instance=region)

    context = {
        'region': region,
        'form': form,
    }
    return render(request, 'accounts/region_compliance.html', context)


@login_required
def lfa_compliance_view(request):
    lfa = request.user.local_federation
    if not lfa:
        messages.error(request, "You are not associated with an LFA.")
        return redirect('accounts:modern_home')

    if request.method == 'POST':
        form = LFAComplianceForm(request.POST, request.FILES, instance=lfa)
        if form.is_valid():
            form.save()
            messages.success(request, 'LFA compliance updated successfully.')
            return redirect('accounts:lfa_compliance_view')
    else:
        form = LFAComplianceForm(instance=lfa)

    context = {
        'lfa': lfa,
        'form': form,
    }
    return render(request, 'accounts/lfa_compliance.html', context)


@login_required
def association_compliance_view(request):
    association = request.user.association
    if not association:
        messages.error(request, "You are not associated with an Association.")
        return redirect('accounts:modern_home')

    if request.method == 'POST':
        form = AssociationComplianceForm(request.POST, request.FILES, instance=association)
        if form.is_valid():
            form.save()
            messages.success(request, 'Association compliance updated successfully.')
            return redirect('accounts:association_compliance_view')
    else:
        form = AssociationComplianceForm(instance=association)

    context = {
        'association': association,
        'form': form,
    }
    return render(request, 'accounts/association_compliance.html', context)


@login_required
def club_compliance_view(request):
    club = request.user.club
    if not club:
        messages.error(request, "You are not associated with a Club.")
        return redirect('accounts:modern_home')

    if request.method == 'POST':
        form = ClubComplianceForm(request.POST, request.FILES, instance=club)
        if form.is_valid():
            form.save()
            messages.success(request, 'Club compliance updated successfully.')
            return redirect('accounts:club_compliance_view')
    else:
        form = ClubComplianceForm(instance=club)

    context = {
        'club': club,
        'form': form,
    }
    return render(request, 'accounts/club_compliance.html', context)

def get_organization_type_name(request, org_type_id):
    org_type = get_object_or_404(OrganizationType, id=org_type_id)
    return JsonResponse({'name': org_type.name})


@require_GET
def check_email(request):
    email = request.GET.get('email', None)
    if email:
        exists = CustomUser.objects.filter(email=email).exists()
        return JsonResponse({'exists': exists})
    return JsonResponse({'exists': False})







@login_required
def invoice_detail(request, invoice_uuid):
    invoice = get_object_or_404(Invoice, uuid=invoice_uuid)
    # Security check to ensure the user owns the invoice or is staff
    if not request.user.is_staff and invoice.member.user != request.user:
        return HttpResponse('Unauthorized', status=403)

    context = {
        'invoice': invoice,
        'invoice_items': invoice.items.all(),
    }
    return render(request, 'accounts/invoice_detail.html', context)

@require_GET
def ajax_extract_id_data(request):
    id_number = request.GET.get('id_number', None)
    if not id_number or len(id_number) != 13 or not id_number.isdigit():
        return JsonResponse({'error': 'Invalid ID number'}, status=400)

    try:
        year = int(id_number[:2])
        month = int(id_number[2:4])
        day = int(id_number[4:6])

        if year < 25:
            year += 2000
        else:
            year += 1900

        dob = date(year, month, day)

        gender_digit = int(id_number[6])
        gender = 'M' if gender_digit >= 5 else 'F'

        return JsonResponse({
            'date_of_birth': dob.strftime('%Y-%m-%d'),
            'gender': gender,
        })
    except (ValueError, IndexError):
        return JsonResponse({'error': 'Invalid date or gender in ID number'}, status=400)

@login_required
@role_required(allowed_roles=['ADMIN_NATIONAL', 'ADMIN_NATIONAL_ACCOUNTS', 'SUPERUSER'])
def confirm_payment(request):
    form = ConfirmPaymentForm()
    invoice = None

    if request.method == 'POST':
        form = ConfirmPaymentForm(request.POST)
        if form.is_valid():
            payment_reference = form.cleaned_data['payment_reference']
            try:
                invoice = Invoice.objects.get(payment_reference=payment_reference)
                if 'confirm_payment' in request.POST:
                    invoice.mark_as_paid(payment_method='Manual Confirmation', payment_reference=payment_reference)
                    messages.success(request, f"Payment for invoice {invoice.invoice_number} has been confirmed.")
                    return redirect('accounts:confirm_payment')
            except Invoice.DoesNotExist:
                messages.error(request, "No invoice found with that payment reference.")
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
                logger.error(f"Error in confirm_payment: {e}")

    context = {
        'form': form,
        'invoice': invoice,
        'title': 'Confirm Payment'
    }
    return render(request, 'accounts/confirm_payment.html', context)