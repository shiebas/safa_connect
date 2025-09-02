import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_GET, require_POST
from datetime import date

from geography.models import (Association, Club, ClubStatus, Country,
                              LocalFootballAssociation, NationalFederation,
                              Province, Region)
from membership.models import Invoice, Member, RegistrationWorkflow, InvoiceItem
from membership.safa_config_models import SAFASeasonConfig, SAFAFeeStructure
from supporters.models import SupporterProfile, SupporterPreferences

from .decorators import role_required
from .forms import (
    AdvancedMemberSearchForm, ClubAdminAddPlayerForm,
    ClubAdminRegistrationForm, ModernContactForm, ProfileForm,
    RejectMemberForm, RegistrationForm, SettingsForm,
    UpdateProfilePhotoForm, EditPlayerForm, ConfirmPaymentForm, ProofOfPaymentForm)
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
            
            # Set SAFA ID if provided for existing member
            if is_existing and previous_safa_id:
                user.safa_id = previous_safa_id

            # This is a new member registration
            user.save() # Ensure user is saved before creating member
            national_federation = NationalFederation.objects.first()
            if not national_federation:
                country = Country.objects.get(name='South Africa')
                national_federation = NationalFederation.objects.create(name='SAFA', country=country)

            # Get active season configuration
            active_season = SAFASeasonConfig.get_active_season()
            if not active_season:
                messages.error(request, 'No active season configuration found. Please contact support.')
                return redirect('accounts:user_registration')

            # Handle SAFA ID - use previous_safa_id if provided, otherwise use generated one
            safa_id_to_use = previous_safa_id if previous_safa_id and is_existing else user.safa_id
            
            # Ensure province is selected for traceable location
            if user.role != 'SUPPORTER' and not form.cleaned_data.get('province'):
                messages.error(request, 'Province selection is required for traceable location.')
                return redirect('accounts:user_registration')

            member_data = {
                'user': user,
                'safa_id': safa_id_to_use,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'role': user.role,
                'status': 'PENDING',
                'date_of_birth': form.cleaned_data['date_of_birth'], # Use cleaned_data directly
                'gender': form.cleaned_data['gender'],               # Use cleaned_data directly
                'id_number': user.id_number,
                'passport_number': user.passport_number,
                'street_address': user.street_address,
                'suburb': user.suburb,
                'city': user.city,
                'state': user.state,
                'postal_code': user.postal_code,
                'national_federation': national_federation,
                'current_season': active_season,  # Set the current season
                'registration_method': 'SELF'    # Mark as self-registration
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

            # Create SupporterProfile for ALL user types (Player, Official, Supporter)
            # This enables future features like marketing preferences, location tracking, digital services
            try:
                # Try to create a very basic SupporterProfile first
                print(f"🔍 DEBUG: Attempting to create SupporterProfile for user {user.email}")
                
                # Check if SupporterProfile already exists
                existing_profile = SupporterProfile.objects.filter(user=user).first()
                if existing_profile:
                    print(f"✅ SupporterProfile already exists for user {user.email}")
                    supporter_profile = existing_profile
                    created = False
                else:
                    # Create with absolute minimum fields including safa_id
                    supporter_profile = SupporterProfile.objects.create(
                        user=user,
                        safa_id=user.safa_id,  # Add the safa_id field
                        membership_type='PREMIUM' if user.role == 'SUPPORTER' else 'FAMILY_BASIC'
                    )
                    created = True
                    print(f"✅ SupporterProfile created successfully for user {user.email}")
                    print(f"✅ SupporterProfile safa_id: {supporter_profile.safa_id}")
                
                if created:
                    print(f"✅ SupporterProfile created successfully for user {user.email}")
                    # Now update with additional fields if creation was successful
                    try:
                        if user.club or form.cleaned_data.get('club'):
                            supporter_profile.favorite_club = user.club if user.club else form.cleaned_data.get('club')
                        
                        if user.id_number:
                            supporter_profile.id_number = user.id_number
                            
                        if form.cleaned_data.get('date_of_birth'):
                            supporter_profile.date_of_birth = form.cleaned_data.get('date_of_birth')
                        
                        # Build address string safely
                        address_parts = []
                        if user.street_address:
                            address_parts.append(user.street_address)
                        if user.suburb:
                            address_parts.append(user.suburb)
                        if user.city:
                            address_parts.append(user.city)
                        if user.state:
                            address_parts.append(user.state)
                        
                        if address_parts:
                            supporter_profile.address = ', '.join(address_parts)
                        
                        supporter_profile.save()
                        print(f"✅ SupporterProfile updated with additional fields for user {user.email}")
                        
                    except Exception as update_error:
                        print(f"⚠️ Warning: SupporterProfile update failed for user {user.email}: {str(update_error)}")
                        # Profile exists, just not fully populated - that's okay
                        
                else:
                    print(f"✅ SupporterProfile already exists for user {user.email}")
                    
            except Exception as e:
                print(f"⚠️ Warning: SupporterProfile creation failed for user {user.email}: {str(e)}")
                print(f"⚠️ Error details: {type(e).__name__}: {str(e)}")
                print(f"⚠️ Note: SupporterProfile can be created manually later via admin panel")
                # Continue with registration - don't let SupporterProfile failure stop the process
                # The SupporterProfile can be created later if needed

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

            # Create invoice using the simple calculation method for self-registrations
            print(f"🔍 DEBUG: About to create invoice for member {member.safa_id}")
            print(f"🔍 DEBUG: Member role: {member.role}")
            print(f"🔍 DEBUG: Member current_season: {member.current_season}")
            
            try:
                invoice = Invoice.create_simple_member_invoice(member)
                if invoice:
                    print(f"✅ Invoice created successfully: {invoice.invoice_number}")
                    messages.success(request, 'Registration successful! Please complete payment to proceed.')
                    return redirect('membership:invoice_detail', uuid=invoice.uuid)
                else:
                    print(f"❌ Invoice creation returned None for member {member.safa_id}")
                    messages.error(request, 'Registration successful but invoice creation failed. Please contact support.')
                    return redirect('accounts:modern_home')
            except Exception as e:
                print(f"❌ Exception during invoice creation for member {member.safa_id}: {str(e)}")
                messages.error(request, f'Registration successful but invoice creation failed: {str(e)}. Please contact support.')
                return redirect('accounts:modern_home')

    else:
        form = RegistrationForm()
    
    context = {
        'form': form,
        'is_club_admin_registration': False  # This is public registration
    }
    return render(request, 'accounts/user_registration.html', context)


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

    # Generate QR code for the profile
    try:
        # Information to be encoded in the QR code
        profile_url = request.build_absolute_uri(reverse('accounts:profile'))
        qr_data = f"SAFA Member: {request.user.get_full_name()}\nSAFA ID: {request.user.safa_id}\nProfile: {profile_url}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=6,
            border=2,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code to a BytesIO buffer and encode it in base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        qr_code_generated = True
    except Exception as e:
        print(f"⚠️ Warning: QR code generation failed: {str(e)}")
        qr_code_base64 = None
        qr_code_generated = False

    context = {
        'user': request.user,
        'member': member,
        'qr_code': qr_code_base64,
        'qr_code_generated': qr_code_generated,
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
    club = request.user.club # Assuming club admin has a 'club' attribute
    invoices = []
    if club:
        # Get invoices for members belonging to this club
        invoices = Invoice.objects.filter(
            Q(member__current_club=club) | Q(organization=club), # Invoices for members or the club itself
            status__in=['PENDING', 'PARTIALLY_PAID', 'OVERDUE', 'PENDING_REVIEW'] # Only show relevant statuses
        ).order_by('-issue_date')

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

    # Financial Summary
    total_paid = Invoice.objects.filter(
        status='PAID').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Calculate outstanding amount - include PENDING, OVERDUE, and PARTIALLY_PAID invoices
    outstanding_invoices = Invoice.objects.filter(
        status__in=['PENDING', 'OVERDUE', 'PARTIALLY_PAID']
    )
    total_outstanding = outstanding_invoices.aggregate(Sum('outstanding_amount'))['outstanding_amount__sum'] or 0

    # Get all provinces for display
    all_provinces = Province.objects.all().order_by('name')
    
    # Get provinces that can be approved (INACTIVE and COMPLIANT)
    pending_provinces = all_provinces.filter(
        status='INACTIVE',
        is_compliant=True
    )
    
    # Show other organizations for information only (not for approval)
    pending_regions = Region.objects.filter(status='INACTIVE').order_by('name')
    pending_lfas = LocalFootballAssociation.objects.filter(status='INACTIVE').order_by('name')
    pending_associations = Association.objects.filter(status='INACTIVE').order_by('name')
    pending_clubs = Club.objects.filter(status='INACTIVE').order_by('name')
    
    # Paginate all provinces (10 per page)
    pending_paginator = Paginator(all_provinces, 10)
    pending_page = request.GET.get('pending_page', 1)
    pending_organizations = pending_paginator.get_page(pending_page)

    # Correctly fetch members awaiting approval from the workflow
    workflows = RegistrationWorkflow.objects.filter(completion_percentage=100).select_related('member__user', 'member__current_club')
    pending_members = [wf.member for wf in workflows]

    # All Members list
    all_members_list = Member.objects.all().order_by('user__first_name', 'user__last_name')


    context = {
        'dashboard_title': 'National Admin Dashboard',
        'dashboard_subtitle': 'Manage all provinces, regions, LFAs, and clubs',
        'total_paid': total_paid,
        'total_outstanding': total_outstanding,
        'pending_organizations': pending_organizations,
        'all_provinces': all_provinces,
        'pending_provinces': pending_provinces,
        'pending_regions': pending_regions,
        'pending_lfas': pending_lfas,
        'pending_associations': pending_associations,
        'pending_clubs': pending_clubs,
        'members': all_members_list,
        'pending_members': pending_members,
    }
    return render(request, 'accounts/national_admin_dashboard.html', context)


@require_POST
@role_required(allowed_roles=['ADMIN_NATIONAL'])
def update_organization_status(request):
    """
    National Admin can only approve Provinces.
    When a province is approved, an invoice is generated.
    """
    org_type = request.POST.get('org_type')
    org_id = request.POST.get('org_id')
    new_status = request.POST.get('new_status')

    # National Admin can only approve provinces
    if org_type != 'province':
        messages.error(request, "National Admin can only approve provinces.")
        return redirect('accounts:national_admin_dashboard')

    if new_status != 'ACTIVE':
        messages.error(request, "National Admin can only activate provinces.")
        return redirect('accounts:national_admin_dashboard')

    try:
        province = get_object_or_404(Province, id=org_id)
        
        # Check if province is compliant
        if not province.is_compliant:
            messages.error(request, f"Cannot approve {province.name}. Province must be compliant first.")
            return redirect('accounts:national_admin_dashboard')

        # Update status
        province.status = new_status
        province.save()

        # Generate invoice for the province using the same formula as user registration
        try:
            # Get active season
            active_season = SAFASeasonConfig.get_active_season()
            if active_season:
                # Create invoice using the same method as user registration
                invoice = Invoice.create_simple_organization_invoice(province, active_season)
                if invoice:
                    messages.success(
                        request,
                        f"Province {province.name} approved and invoice #{invoice.invoice_number} generated."
                    )
                else:
                    messages.warning(
                        request,
                        f"Province {province.name} approved but invoice generation failed."
                    )
            else:
                messages.warning(
                    request,
                    f"Province {province.name} approved but no active season found."
                )
        except Exception as e:
            messages.warning(
                request,
                f"Province {province.name} approved but invoice generation failed: {str(e)}"
            )

        return redirect('accounts:national_admin_dashboard')

    except Exception as e:
        messages.error(request, f"Error approving province: {str(e)}")
        return redirect('accounts:national_admin_dashboard')


@role_required(allowed_roles=['ADMIN_PROVINCE'])
def approve_region(request):
    """
    Province Admin can only approve Regions within their province.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('accounts:provincial_admin_dashboard')

    region_id = request.POST.get('region_id')
    new_status = request.POST.get('new_status')

    if new_status != 'ACTIVE':
        messages.error(request, "Province Admin can only activate regions.")
        return redirect('accounts:provincial_admin_dashboard')

    try:
        region = get_object_or_404(Region, id=region_id)
        
        # Check if region belongs to the user's province
        if region.province != request.user.province:
            messages.error(request, "You can only approve regions within your province.")
            return redirect('accounts:provincial_admin_dashboard')

        # Check if region is compliant
        if not region.is_compliant:
            messages.error(request, f"Cannot approve {region.name}. Region must be compliant first.")
            return redirect('accounts:provincial_admin_dashboard')

        # Update status
        region.status = new_status
        region.save()

        # Generate invoice for the region using the same formula as user registration
        try:
            # Get active season
            active_season = SAFASeasonConfig.get_active_season()
            if active_season:
                # Create invoice using the same method as user registration
                invoice = Invoice.create_simple_organization_invoice(region, active_season)
                if invoice:
                    messages.success(
                        request,
                        f"Region {region.name} approved and invoice #{invoice.invoice_number} generated."
                    )
                else:
                    messages.warning(
                        request,
                        f"Region {region.name} approved but invoice generation failed."
                    )
            else:
                messages.warning(
                    request,
                    f"Region {region.name} approved but no active season found."
                )
        except Exception as e:
            messages.warning(
                request,
                f"Region {region.name} approved but invoice generation failed: {str(e)}"
            )

        messages.success(request, f"Region {region.name} approved successfully.")
        return redirect('accounts:provincial_admin_dashboard')

    except Exception as e:
        messages.error(request, f"Error approving region: {str(e)}")
        return redirect('accounts:provincial_admin_dashboard')


@role_required(allowed_roles=['ADMIN_REGION'])
def approve_lfa(request):
    """
    Region Admin can only approve LFAs within their region.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('accounts:regional_admin_dashboard')

    lfa_id = request.POST.get('lfa_id')
    new_status = request.POST.get('new_status')

    if new_status != 'ACTIVE':
        messages.error(request, "Region Admin can only activate LFAs.")
        return redirect('accounts:regional_admin_dashboard')

    try:
        lfa = get_object_or_404(LocalFootballAssociation, id=lfa_id)
        
        # Check if LFA belongs to the user's region
        if lfa.region != request.user.region:
            messages.error(request, "You can only approve LFAs within your region.")
            return redirect('accounts:regional_admin_dashboard')

        # Check if LFA is compliant
        if not lfa.is_compliant:
            messages.error(request, f"Cannot approve {lfa.name}. LFA must be compliant first.")
            return redirect('accounts:regional_admin_dashboard')

        # Update status
        lfa.status = new_status
        lfa.save()

        # Generate invoice for the LFA using the same formula as user registration
        try:
            # Get active season
            active_season = SAFASeasonConfig.get_active_season()
            if active_season:
                # Create invoice using the same method as user registration
                invoice = Invoice.create_simple_organization_invoice(lfa, active_season)
                if invoice:
                    messages.success(
                        request,
                        f"LFA {lfa.name} approved and invoice #{invoice.invoice_number} generated."
                    )
                else:
                    messages.warning(
                        request,
                        f"LFA {lfa.name} approved but invoice generation failed."
                    )
            else:
                messages.warning(
                    request,
                    f"LFA {lfa.name} approved but no active season found."
                )
        except Exception as e:
            messages.warning(
                request,
                f"LFA {lfa.name} approved but invoice generation failed: {str(e)}"
            )

        messages.success(request, f"LFA {lfa.name} approved successfully.")
        return redirect('accounts:regional_admin_dashboard')

    except Exception as e:
        messages.error(request, f"Error approving LFA: {str(e)}")
        return redirect('accounts:regional_admin_dashboard')


@role_required(allowed_roles=['ADMIN_LOCAL_FED'])
def approve_club(request):
    """
    LFA Admin can only approve Clubs within their LFA.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('accounts:lfa_admin_dashboard')

    club_id = request.POST.get('club_id')
    new_status = request.POST.get('new_status')

    if new_status != 'ACTIVE':
        messages.error(request, "LFA Admin can only activate clubs.")
        return redirect('accounts:lfa_admin_dashboard')

    try:
        club = get_object_or_404(Club, id=club_id)
        
        # Check if club belongs to the user's LFA
        if club.localfootballassociation != request.user.local_federation:
            messages.error(request, "You can only approve clubs within your LFA.")
            return redirect('accounts:lfa_admin_dashboard')

        # Check if club is compliant
        if not club.is_compliant:
            messages.error(request, f"Cannot approve {club.name}. Club must be compliant first.")
            return redirect('accounts:lfa_admin_dashboard')

        # Update status
        club.status = new_status
        club.save()

        # Generate invoice for the club using the same formula as user registration
        try:
            # Get active season
            active_season = SAFASeasonConfig.get_active_season()
            if active_season:
                # Create invoice using the same method as user registration
                invoice = Invoice.create_simple_organization_invoice(club, active_season)
                if invoice:
                    messages.success(
                        request,
                        f"Club {club.name} approved and invoice #{invoice.invoice_number} generated."
                    )
                else:
                    messages.warning(
                        request,
                        f"Club {club.name} approved but invoice generation failed."
                    )
            else:
                messages.warning(
                    request,
                    f"Club {club.name} approved but no active season found."
                )
        except Exception as e:
            messages.warning(
                request,
                f"Club {club.name} approved but invoice generation failed: {str(e)}"
            )

        messages.success(request, f"Club {club.name} approved successfully.")
        return redirect('accounts:lfa_admin_dashboard')

    except Exception as e:
        messages.error(request, f"Error approving club: {str(e)}")
        return redirect('accounts:lfa_admin_dashboard')


@login_required
@role_required(allowed_roles=['ADMIN_NATIONAL', 'ADMIN_NATIONAL_ACCOUNTS', 'SUPERUSER'])
def national_finance_dashboard(request):
    return render(request, 'accounts/national_finance_dashboard.html')


@role_required(allowed_roles=['ADMIN_PROVINCE'])
def provincial_admin_dashboard(request):
    user_province = request.user.province
    
    # Get regions that can be approved (INACTIVE and COMPLIANT)
    pending_regions = []
    if user_province:
        pending_regions = user_province.region_set.filter(
            status='INACTIVE',
            is_compliant=True
        ).order_by('name')
    
    # Get all regions for display
    all_regions = []
    if user_province:
        all_regions = user_province.region_set.all().order_by('name')
    
    # Get members in this province (simplified query with error handling)
    members = []
    if user_province:
        try:
            # Get all members and filter by province in Python to avoid complex DB queries
            all_members = Member.objects.select_related('user', 'current_club', 'current_club__localfootballassociation', 'current_club__localfootballassociation__region').all()
            for member in all_members:
                try:
                    if (member.current_club and 
                        member.current_club.lfa and 
                        member.current_club.lfa.region and 
                        member.current_club.lfa.region.province == user_province):
                        members.append(member)
                except Exception as e:
                    # Skip members with broken relationships
                    continue
            # Sort by name
            members.sort(key=lambda x: (x.user.first_name or '', x.user.last_name or ''))
        except Exception as e:
            # If there's an error getting members, just use empty list
            members = []
    
    # Get organization invoices for this province
    from django.contrib.contenttypes.models import ContentType
    from membership.models import Invoice
    
    province_content_type = ContentType.objects.get_for_model(user_province.__class__)
    organization_invoices = Invoice.objects.filter(
        content_type=province_content_type,
        object_id=user_province.id
    ).order_by('-created')
    

    
    context = {
        'dashboard_title': 'Provincial Admin Dashboard',
        'dashboard_subtitle': f'Manage {user_province.name if user_province else "your province"}',
        'user_province': user_province,
        'pending_regions': pending_regions,
        'regions': all_regions,
        'members': members,
        'organization_invoices': organization_invoices,
    }
    return render(request, 'accounts/provincial_admin_dashboard.html', context)


@login_required
def regional_admin_dashboard(request):
    user_region = request.user.region
    
    # Get LFAs that can be approved (INACTIVE and COMPLIANT)
    pending_lfas = []
    if user_region:
        pending_lfas = user_region.localfootballassociation_set.filter(
            status='INACTIVE',
            is_compliant=True
        ).order_by('name')
    
    # Get all LFAs for display
    all_lfas = []
    if user_region:
        all_lfas = user_region.localfootballassociation_set.all().order_by('name')
    
    # Get clubs in this region
    clubs = Club.objects.filter(
        localfootballassociation__region=user_region
    ).order_by('name')
    
    # Get members in this region (simplified query with error handling)
    members = []
    if user_region:
        try:
            # Get all members and filter by region in Python to avoid complex DB queries
            all_members = Member.objects.select_related('user', 'current_club', 'current_club__localfootballassociation').all()
            for member in all_members:
                try:
                    if (member.current_club and 
                        member.current_club.lfa and 
                        member.current_club.lfa.region == user_region):
                        members.append(member)
                except Exception as e:
                    # Skip members with broken relationships
                    continue
            # Sort by name
            members.sort(key=lambda x: (x.user.first_name or '', x.user.last_name or ''))
        except Exception as e:
            # If there's an error getting members, just use empty list
            members = []

    # Get organization invoices for this region
    from django.contrib.contenttypes.models import ContentType
    from membership.models import Invoice
    
    region_content_type = ContentType.objects.get_for_model(user_region.__class__)
    organization_invoices = Invoice.objects.filter(
        content_type=region_content_type,
        object_id=user_region.id
    ).order_by('-created')
    
    context = {
        'dashboard_title': 'Regional Admin Dashboard',
        'dashboard_subtitle': f'Manage {user_region.name if user_region else "your region"}',
        'user_region': user_region,
        'pending_lfas': pending_lfas,
        'lfas': all_lfas,
        'clubs': clubs,
        'members': members,
        'organization_invoices': organization_invoices,
    }
    return render(request, 'accounts/regional_admin_dashboard.html', context)


@login_required
def lfa_admin_dashboard(request):
    lfa = request.user.local_federation
    
    # Get clubs that can be approved (INACTIVE and COMPLIANT)
    pending_clubs = []
    if lfa:
        pending_clubs = lfa.clubs.filter(
            status='INACTIVE',
            is_compliant=True
        ).order_by('name')
    
    # Get all clubs for display
    all_clubs = []
    if lfa:
        all_clubs = lfa.clubs.all().order_by('name')

    # Pending Approvals for this LFA
    pending_members = []
    if lfa:
        workflows = RegistrationWorkflow.objects.filter(
            member__lfa=lfa,
            completion_percentage=100
        ).select_related('member__user', 'member__current_club')
        pending_members = [wf.member for wf in workflows]
    
    # Get members in this LFA (simplified query with error handling)
    members = []
    if lfa:
        try:
            # Get all members and filter by LFA in Python to avoid complex DB queries
            all_members = Member.objects.select_related('user', 'current_club').all()
            for member in all_members:
                try:
                    if member.current_club and member.current_club.lfa == lfa:
                        members.append(member)
                except Exception as e:
                    # Skip members with broken relationships
                    continue
            # Sort by name
            members.sort(key=lambda x: (x.user.first_name or '', x.user.last_name or ''))
        except Exception as e:
            # If there's an error getting members, just use empty list
            members = []

    # Get organization invoices for this LFA
    from django.contrib.contenttypes.models import ContentType
    from membership.models import Invoice
    
    lfa_content_type = ContentType.objects.get_for_model(lfa.__class__)
    organization_invoices = Invoice.objects.filter(
        content_type=lfa_content_type,
        object_id=lfa.id
    ).order_by('-created')
    
    context = {
        'dashboard_title': 'LFA Admin Dashboard',
        'dashboard_subtitle': f'Manage {lfa.name if lfa else "your LFA"}',
        'lfa': lfa,
        'pending_clubs': pending_clubs,
        'clubs': all_clubs,
        'pending_members': pending_members,
        'members': members,
        'organization_invoices': organization_invoices,
    }
    return render(request, 'accounts/lfa_admin_dashboard.html', context)


@login_required
def club_admin_dashboard(request):
    club = request.user.club
    
    # Check if user has a club associated
    if not club:
        messages.error(request, "You are not currently associated with any Club. Please contact your administrator to set up your club association.")
        return redirect('accounts:profile')
    
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
    workflows = RegistrationWorkflow.objects.filter(
        member__current_club=club,
        completion_percentage=100
    ).select_related('member__user', 'member__current_club')
    pending_members = [wf.member for wf in workflows]

    # Get organization invoices for this club
    from django.contrib.contenttypes.models import ContentType
    from membership.models import Invoice
    
    club_content_type = ContentType.objects.get_for_model(club.__class__)
    organization_invoices = Invoice.objects.filter(
        content_type=club_content_type,
        object_id=club.id
    ).order_by('-created')
    
    context = {
        'dashboard_title': 'Club Admin Dashboard',
        'dashboard_subtitle': f'Manage {club.name if club else "Club"}',
        'club': club,
        'user_club': club,  # Add this for template compatibility
        'players': players,
        'members': players,  # Add this for template compatibility
        'recent_members': players[:5],  # Add this for template compatibility
        'juniors': juniors,
        'seniors': seniors,
        'male_players': male_players,
        'female_players': female_players,
        'pending_members': pending_members,
        'active_members': players.filter(membership_status='ACTIVE'),  # Fixed: use membership_status not status
        'organization_invoices': organization_invoices,
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
        'dashboard_title': 'Association Admin Dashboard',
        'dashboard_subtitle': f'Manage {association.name if association else "Association"}',
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
            # Check if we already have a success message for this player
            existing_messages = [msg.message for msg in messages.get_messages(request)]
            success_message = f'Player {player.get_full_name()} updated successfully.'
            
            if success_message not in existing_messages:
                logger.debug(f"Adding success message for player update: {player.get_full_name()}")
                # Add a unique identifier to prevent duplicates
                messages.success(request, f'Player {player.get_full_name()} updated successfully. [ID: {player_id}]')
                
                # Log the message after adding it
                logger.debug(f"Messages count after adding success: {len(messages.get_messages(request))}")
            else:
                logger.debug(f"Success message already exists, not adding duplicate")

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
    Now includes automatic invoice creation for SAFA membership fees.
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

            # Get active season configuration
            active_season = SAFASeasonConfig.get_active_season()
            if not active_season:
                messages.error(request, 'No active season configuration found. Please contact support.')
                return redirect('accounts:club_admin_add_person')

            # Create the corresponding Member record
            member = Member.objects.create(
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
                current_season=active_season,  # Set the current season
                registration_method='CLUB'    # Mark as club registration
            )
            
            # Create invoice immediately using simple calculation for club-admin-created members
            try:
                invoice = Invoice.create_simple_member_invoice(member)
                if not invoice:
                    messages.warning(request, f"{form.cleaned_data.get('role').capitalize()} '{user.get_full_name()}' was added successfully, but invoice creation failed. Please contact support.")
                    return redirect('accounts:club_admin_dashboard')
            except Exception as e:
                messages.warning(request, f"{form.cleaned_data.get('role').capitalize()} '{user.get_full_name()}' was added successfully, but invoice creation failed: {str(e)}. Please contact support.")
                return redirect('accounts:club_admin_dashboard')
            
            # Prepare success message
            success_message = f"{form.cleaned_data.get('role').capitalize()} '{user.get_full_name()}' was added successfully. A temporary password has been set."
            
            if not form.cleaned_data.get('has_email', True):
                success_message += f" An email address ({user.email}) has been automatically generated for this member."
            
            success_message += f" A SAFA membership invoice has been created and must be paid before the member can participate."
            
            messages.success(request, success_message)
            return redirect('accounts:club_admin_dashboard')
    else:
        # Form automatically handles pre-population and disabling of geographic fields for club admins
        form = RegistrationForm(user=request.user, limit_role_choices=True)

    context = {
        'form': form,
        'title': 'Add New Player or Official',
        'is_club_admin_registration': True  # Flag to indicate this is club admin registration
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
            return redirect('accounts:provincial_admin_dashboard')
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
            return redirect('accounts:regional_admin_dashboard')
    else:
        form = RegionComplianceForm(instance=region)

    context = {
        'region': region,
        'form': form,
    }
    return render(request, 'accounts/region_compliance.html', context)


@role_required(allowed_roles=['ADMIN_LOCAL_FED'])
def lfa_compliance_view(request):
    # Use the same pattern as region_compliance_view
    print(f"🔍 DEBUG: Request method: {request.method}")
    print(f"🔍 DEBUG: User authenticated: {request.user.is_authenticated}")
    print(f"🔍 DEBUG: User: {request.user}")
    print(f"🔍 DEBUG: User email: {getattr(request.user, 'email', 'No email')}")
    
    lfa = request.user.local_federation
    
    # Debug logging
    print(f"🔍 DEBUG: User: {request.user.email}")
    print(f"🔍 DEBUG: User role: {request.user.role}")
    print(f"🔍 DEBUG: User local_federation: {lfa}")
    print(f"🔍 DEBUG: User local_federation type: {type(lfa)}")
    
    if not lfa:
        print(f"❌ DEBUG: User {request.user.email} has no local_federation")
        messages.error(request, "You are not associated with an LFA.")
        return redirect('accounts:modern_home')

    print(f"✅ DEBUG: Found LFA: {lfa.name} (ID: {lfa.id})")
    print(f"✅ DEBUG: LFA status: {lfa.status}")
    print(f"✅ DEBUG: LFA compliant: {lfa.is_compliant}")

    if request.method == 'POST':
        form = LFAComplianceForm(request.POST, request.FILES, instance=lfa)
        if form.is_valid():
            form.save()
            messages.success(request, 'LFA compliance updated successfully.')
            return redirect('accounts:lfa_admin_dashboard')
        else:
            print(f"❌ DEBUG: Form errors: {form.errors}")
    else:
        form = LFAComplianceForm(instance=lfa)

    context = {
        'local_federation': lfa,  # Match what the template expects
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
            return redirect('accounts:club_admin_dashboard')
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
    form = ConfirmPaymentForm(request.GET or None)
    invoices = None

    if form.is_valid():
        query = form.cleaned_data.get('invoice_number')
        if query:
            invoices = Invoice.objects.filter(invoice_number__icontains=query)

    if request.method == 'POST':
        invoice_id = request.POST.get('invoice_id')
        if invoice_id:
            try:
                invoice = Invoice.objects.get(id=invoice_id)
                invoice.mark_as_paid(payment_method='Manual Confirmation', payment_reference=f"Manual confirmation by {request.user.get_full_name()}")
                messages.success(request, f"Payment for invoice {invoice.invoice_number} has been confirmed.")
                # Redirect to the same search results
                return redirect(request.get_full_path())
            except Invoice.DoesNotExist:
                messages.error(request, "Invalid invoice selected for payment confirmation.")
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
                logger.error(f"Error in confirm_payment POST: {e}")

    context = {
        'form': form,
        'invoices': invoices,
        'title': 'Confirm Payment'
    }
    return render(request, 'accounts/confirm_payment.html', context)


@login_required
def submit_proof_of_payment(request, invoice_uuid):
    invoice = get_object_or_404(Invoice, uuid=invoice_uuid)

    # Security check: Only the member who owns the invoice or a club admin
    # associated with the member's club can submit proof of payment.
    # National admins will have a separate approval flow.
    if not (request.user == invoice.member.user or \
            (request.user.role == 'CLUB_ADMIN' and request.user.club == invoice.member.current_club)):
        messages.error(request, "You do not have permission to submit proof of payment for this invoice.")
        return redirect('accounts:my_invoices') # Or appropriate redirect

    if request.method == 'POST':
        form = ProofOfPaymentForm(request.POST, request.FILES, initial={'invoice_uuid': invoice.uuid})
        if form.is_valid():
            # Update invoice fields
            invoice.proof_of_payment = form.cleaned_data['proof_of_payment']
            invoice.payment_method = form.cleaned_data['payment_method']
            invoice.payment_reference = form.cleaned_data['payment_reference']
            invoice.payment_submitted_by = request.user
            invoice.payment_submission_date = timezone.now()
            invoice.status = 'PENDING_REVIEW' # Set new status
            invoice.save()

            messages.success(request, f"Proof of payment for Invoice {invoice.invoice_number} submitted successfully. Awaiting National Admin review.")
            return redirect('accounts:invoice_detail', invoice_uuid=invoice.uuid)
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ProofOfPaymentForm(initial={'invoice_uuid': invoice.uuid})

    context = {
        'invoice': invoice,
        'form': form,
        'title': 'Submit Proof of Payment'
    }
    return render(request, 'accounts/submit_proof_of_payment.html', context)


@login_required
@role_required(allowed_roles=['ADMIN_NATIONAL', 'ADMIN_NATIONAL_ACCOUNTS', 'SUPERUSER'])
def national_admin_payment_review(request):
    # Filter invoices that are PENDING_REVIEW
    invoices = Invoice.objects.filter(status='PENDING_REVIEW').order_by('-payment_submission_date')

    context = {
        'invoices': invoices,
        'title': 'Payment Review (National Admin)'
    }
    return render(request, 'accounts/national_admin_payment_review.html', context)


@login_required
@role_required(allowed_roles=['ADMIN_NATIONAL', 'ADMIN_NATIONAL_ACCOUNTS', 'SUPERUSER'])
@require_POST
def approve_invoice_payment(request, invoice_uuid):
    invoice = get_object_or_404(Invoice, uuid=invoice_uuid)

    if invoice.status != 'PENDING_REVIEW':
        messages.error(request, "Invoice is not in 'Pending Review' status.")
        return redirect('accounts:national_admin_payment_review')

    try:
        # Mark as paid using the existing method
        invoice.mark_as_paid(
            payment_method=invoice.payment_method, # Use the method submitted by club admin
            payment_reference=f"Approved by {request.user.get_full_name()} - {invoice.payment_reference}"
        )
        messages.success(request, f"Payment for Invoice {invoice.invoice_number} approved successfully.")
    except Exception as e:
        messages.error(request, f"Error approving payment for Invoice {invoice.invoice_number}: {e}")
        logger.error(f"Error approving invoice {invoice.invoice_number}: {e}")

    return redirect('accounts:national_admin_payment_review')


@login_required
@role_required(allowed_roles=['ADMIN_NATIONAL', 'ADMIN_NATIONAL_ACCOUNTS', 'SUPERUSER'])
@require_POST
def reject_invoice_payment(request, invoice_uuid):
    invoice = get_object_or_404(Invoice, uuid=invoice_uuid)
    rejection_reason = request.POST.get('rejection_reason', 'No reason provided.')

    if invoice.status != 'PENDING_REVIEW':
        messages.error(request, "Invoice is not in 'Pending Review' status.")
        return redirect('accounts:national_admin_payment_review')

    try:
        # Revert status to PENDING and clear proof of payment
        invoice.status = 'PENDING'
        invoice.proof_of_payment = None # Clear the uploaded proof
        invoice.payment_submitted_by = None
        invoice.payment_submission_date = None
        invoice.notes += f"\nPayment rejected by {request.user.get_full_name()} on {timezone.now().date()}: {rejection_reason}"
        invoice.save()

        messages.warning(request, f"Payment for Invoice {invoice.invoice_number} rejected. Reason: {rejection_reason}")
    except Exception as e:
        messages.error(request, f"Error rejecting payment for Invoice {invoice.invoice_number}: {e}")
        logger.error(f"Error rejecting invoice {invoice.invoice_number}: {e}")

    return redirect('accounts:national_admin_payment_review')


def custom_logout(request):
    """
    Custom logout view that ensures users are redirected to the correct login page
    """
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('accounts:login')


@login_required
def national_admin_invoices(request):
    """National admin view of all organization invoices"""
    if request.user.role != 'ADMIN_NATIONAL':
        messages.error(request, "Access denied. National admin privileges required.")
        return redirect('accounts:modern_home')
    
    # Get filter parameters
    season_year = request.GET.get('season_year')
    organization_type = request.GET.get('organization_type')
    status = request.GET.get('status')
    
    # Get all organization invoices
    from membership.models import Invoice
    invoices = Invoice.get_national_admin_invoices(season_year=season_year)
    
    # Apply additional filters
    if organization_type:
        invoices = invoices.filter(
            content_type__model__iexact=organization_type.lower()
        )
    
    if status:
        invoices = invoices.filter(status=status)
    
    # Get available seasons for filter
    from membership.safa_config_models import SAFASeasonConfig
    seasons = SAFASeasonConfig.objects.all().order_by('-season_year')
    
    # Get organization type counts for summary
    organization_counts = {}
    for org_type in ['province', 'region', 'localfootballassociation', 'club']:
        count = invoices.filter(content_type__model=org_type).count()
        organization_counts[org_type.replace('localfootballassociation', 'lfa').title()] = count
    
    context = {
        'invoices': invoices,
        'seasons': seasons,
        'current_season': season_year,
        'current_organization_type': organization_type,
        'current_status': status,
        'organization_counts': organization_counts,
        'title': 'National Admin - Organization Invoices'
    }
    
    return render(request, 'accounts/national_admin_invoices.html', context)


@login_required
def province_admin_invoices(request):
    """Province admin view of their organization invoices"""
    if request.user.role != 'ADMIN_PROVINCE':
        messages.error(request, "Access denied. Province admin privileges required.")
        return redirect('accounts:modern_home')
    
    # Get the province this admin is associated with
    province_info = request.user.get_organization_info()
    if not province_info or province_info.get('type') != 'Province':
        messages.error(request, "Access denied. No province association found.")
        return redirect('accounts:modern_home')
    
    # Get the actual province instance
    province_instance = request.user.province
    if not province_instance:
        messages.error(request, "Access denied. No province instance found.")
        return redirect('accounts:modern_home')
    
    # Get filter parameters
    season_year = request.GET.get('season_year')
    status = request.GET.get('status')
    
    # Get province invoices
    from membership.models import Invoice
    invoices = Invoice.get_province_admin_invoices(
        province=province_instance,
        season_year=season_year
    )
    
    if status:
        invoices = invoices.filter(status=status)
    
    # Get available seasons for filter
    from membership.safa_config_models import SAFASeasonConfig
    seasons = SAFASeasonConfig.objects.all().order_by('-season_year')
    
    context = {
        'invoices': invoices,
        'seasons': seasons,
        'current_season': season_year,
        'current_status': status,
        'province': province_info,
        'title': 'Province Admin - Organization Invoices'
    }
    
    return render(request, 'accounts/province_admin_invoices.html', context)