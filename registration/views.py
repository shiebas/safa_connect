# registration/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import json
import csv

from .models import Player, Official, PlayerClubRegistration
from .forms import UniversalRegistrationForm, PlayerRegistrationForm, OfficialRegistrationForm
from membership.models import Member, Invoice, InvoiceItem
from accounts.models import CustomUser
from accounts.decorators import role_required


class RegistrationManager:
    """Centralized registration management to reduce code duplication"""
    
    @staticmethod
    def create_member_invoice(member, amount, description, invoice_type='MEMBERSHIP'):
        """Create standardized invoices for members"""
        invoice = Invoice.objects.create(
            player=member,
            amount=amount,
            status='PENDING',
            invoice_type=invoice_type,
            due_date=timezone.now() + timezone.timedelta(days=30)
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description=description,
            quantity=1,
            unit_price=amount
        )
        return invoice
    
    @staticmethod
    def generate_unique_email(first_name, last_name, domain_suffix='safa.system'):
        """Generate unique email addresses"""
        from django.utils.crypto import get_random_string
        
        base_email = f"{first_name.lower()}.{last_name.lower()}@{domain_suffix}"
        if not Member.objects.filter(email=base_email).exists():
            return base_email
        
        # Add random suffix if base email exists
        counter = 1
        while counter < 100:  # Prevent infinite loop
            email = f"{first_name.lower()}.{last_name.lower()}{counter}@{domain_suffix}"
            if not Member.objects.filter(email=email).exists():
                return email
            counter += 1
        
        # Fallback to completely random
        return f"member_{get_random_string(8)}@{domain_suffix}"
    
    @staticmethod
    def validate_member_documents(member):
        """Validate required documents for approval"""
        missing_docs = []
        
        if not member.profile_picture:
            missing_docs.append("Profile picture")
        
        if member.id_document_type == 'ID' and not member.id_document:
            missing_docs.append("ID document")
        elif member.id_document_type == 'PP' and not member.id_document:
            missing_docs.append("Passport document")
        
        return missing_docs


@login_required
def universal_registration(request):
    """Universal registration form for all member types"""
    # Import models for form context
    from geography.models import Province, Association
    from accounts.models import Position
    
    if request.method == 'POST':
        form = UniversalRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    registration_type = form.cleaned_data.get('registration_type')
                    
                    # Create appropriate member instance
                    if registration_type == 'PLAYER':
                        member = Player()
                    elif registration_type == 'OFFICIAL':
                        member = Official()
                    else:
                        member = Member()
                    
                    # Copy form data to member
                    for field_name, value in form.cleaned_data.items():
                        if hasattr(member, field_name) and field_name != 'registration_type':
                            setattr(member, field_name, value)
                    
                    # Set defaults
                    member.status = 'PENDING'
                    if not member.email:
                        member.email = RegistrationManager.generate_unique_email(
                            member.first_name, member.last_name
                        )
                    
                    # Set geography relationships from club/organization
                    if member.club:
                        if not member.lfa and member.club.localfootballassociation:
                            member.lfa = member.club.localfootballassociation
                        if not member.region and member.club.region:
                            member.region = member.club.region
                        if not member.province and member.club.province:
                            member.province = member.club.province
                    
                    # Force role for specific types
                    if isinstance(member, Player):
                        member.role = 'PLAYER'
                    elif isinstance(member, Official):
                        member.role = 'OFFICIAL'
                    
                    member.save()
                    
                    # Create invoices based on member type
                    invoices_created = []
                    
                    # National membership fee (everyone pays this)
                    national_invoice = RegistrationManager.create_member_invoice(
                        member, 100.00, 'National Federation Membership Fee', 'MEMBERSHIP'
                    )
                    invoices_created.append(national_invoice)
                    
                    # Additional fees based on type and club registration
                    if isinstance(member, Player) and member.club:
                        club_invoice = RegistrationManager.create_member_invoice(
                            member, 200.00, f'Club Registration Fee - {member.club.name}', 'REGISTRATION'
                        )
                        invoices_created.append(club_invoice)
                        
                        # Create club registration record
                        PlayerClubRegistration.objects.create(
                            player=member,
                            club=member.club,
                            status='PENDING'
                        )
                    
                    elif isinstance(member, Official):
                        # Different fees for different official types
                        position_type = member.position.title.lower() if member.position else ""
                        if "referee" in position_type:
                            fee, description = 250.00, "Referee Registration Fee"
                        elif "coach" in position_type:
                            fee, description = 200.00, "Coach Registration Fee"
                        else:
                            fee, description = 150.00, "Official Registration Fee"
                        
                        official_invoice = RegistrationManager.create_member_invoice(
                            member, fee, description, 'REGISTRATION'
                        )
                        invoices_created.append(official_invoice)
                    
                    # Success message
                    total_amount = sum(inv.amount for inv in invoices_created)
                    invoice_numbers = ", ".join([f"#{inv.invoice_number}" for inv in invoices_created])
                    
                    messages.success(request, 
                        f'{registration_type.title()} registration successful! '
                        f'Invoices created: {invoice_numbers}. '
                        f'Total fees: R{total_amount:.2f}. '
                        f'Member will be eligible for approval once invoices are paid.'
                    )
                    
                    return redirect('registration:registration_success')
                    
            except Exception as e:
                messages.error(request, f"Registration failed: {str(e)}")
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    field_label = form.fields.get(field, {}).get('label', field)
                    messages.error(request, f"{field_label}: {error}")
    else:
        form = UniversalRegistrationForm()
    
    # Provide context for form
    context = {
        'form': form,
        'title': 'SAFA Universal Registration',
        'provinces': Province.objects.all(),
        'associations': Association.objects.all(),
        'positions': Position.objects.filter(is_active=True),
    }
    
    return render(request, 'registration/universal_registration.html', context)


def registration_success(request):
    """Success page after registration"""
    return render(request, 'registration/registration_success.html', {
        'title': 'Registration Successful'
    })


@login_required
@role_required(allowed_roles=['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_NATIONAL', 'ADMIN_NATIONAL_ACCOUNTS'])
def member_approval_dashboard(request):
    """Centralized approval dashboard for all member types"""
    user = request.user
    
    # Get members based on user's role and hierarchy
    base_queryset = Member.objects.all()
    
    # Role-based filtering
    if user.role == 'ADMIN_LOCAL_FED' and hasattr(user, 'local_federation') and user.local_federation:
        base_queryset = base_queryset.filter(lfa=user.local_federation)
    elif user.role == 'ADMIN_REGION' and hasattr(user, 'region') and user.region:
        base_queryset = base_queryset.filter(region=user.region)
    elif user.role == 'ADMIN_PROVINCE' and hasattr(user, 'province') and user.province:
        base_queryset = base_queryset.filter(province=user.province)
    elif user.role == 'ADMIN_NATIONAL_ACCOUNTS':
        # National accounts admin sees all but has limited actions (mainly payment-related)
        pass  # See all members
    # ADMIN_NATIONAL sees all (no filtering)
    
    # Filter by approval status
    status_filter = request.GET.get('status', 'pending')
    if status_filter == 'pending':
        members = base_queryset.filter(status='PENDING')
    elif status_filter == 'approved':
        members = base_queryset.filter(status='ACTIVE')
    else:
        members = base_queryset
    
    # Additional filters
    member_type_filter = request.GET.get('member_type')
    if member_type_filter == 'PLAYER':
        members = members.filter(role='PLAYER')
    elif member_type_filter == 'OFFICIAL':
        members = members.filter(role='OFFICIAL')
    elif member_type_filter == 'MEMBER':
        members = members.filter(role__isnull=True)
    
    payment_status_filter = request.GET.get('payment_status')
    if payment_status_filter == 'paid':
        # Get members with no unpaid invoices
        unpaid_member_ids = Invoice.objects.filter(
            player__in=members,
            status__in=['PENDING', 'OVERDUE']
        ).values_list('player_id', flat=True)
        members = members.exclude(id__in=unpaid_member_ids)
    elif payment_status_filter == 'unpaid':
        # Get members with unpaid invoices
        unpaid_member_ids = Invoice.objects.filter(
            player__in=members,
            status__in=['PENDING', 'OVERDUE']
        ).values_list('player_id', flat=True)
        members = members.filter(id__in=unpaid_member_ids)
    
    # Separate by type for statistics
    all_members = base_queryset
    players = all_members.filter(role='PLAYER')
    officials = all_members.filter(role='OFFICIAL')
    general_members = all_members.filter(role__isnull=True)
    
    # Check payment status for each member
    members_data = []
    for member in members[:50]:  # Limit to 50 for performance
        unpaid_invoices = Invoice.objects.filter(
            player=member, 
            status__in=['PENDING', 'OVERDUE']
        )
        members_data.append({
            'member': member,
            'member_type': type(member).__name__,
            'unpaid_invoices': unpaid_invoices,
            'has_unpaid': unpaid_invoices.exists(),
            'missing_documents': RegistrationManager.validate_member_documents(member)
        })
    
    context = {
        'members_data': members_data,
        'players_count': players.count(),
        'officials_count': officials.count(),
        'general_members_count': general_members.count(),
        'status_filter': status_filter,
        'member_type_filter': member_type_filter or '',
        'payment_status_filter': payment_status_filter or '',
        'user_role': user.role,
        'can_approve': user.role in ['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_NATIONAL'],
        'can_view_payments': user.role in ['ADMIN_NATIONAL_ACCOUNTS', 'ADMIN_NATIONAL'],
    }
    
    return render(request, 'registration/approval_dashboard.html', context)


@login_required
@role_required(allowed_roles=['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_NATIONAL'])
@require_http_methods(["POST"])
def approve_member(request, member_id):
    """Unified member approval endpoint"""
    member = get_object_or_404(Member, id=member_id)
    
    # Check permissions (similar logic as approval dashboard)
    user = request.user
    if not _user_can_approve_member(user, member):
        return JsonResponse({'success': False, 'message': 'You do not have permission to approve this member.'})
    
    # Validate documents
    missing_docs = RegistrationManager.validate_member_documents(member)
    if missing_docs:
        return JsonResponse({'success': False, 'message': f"Cannot approve member. Missing: {', '.join(missing_docs)}"})
    
    # Check for unpaid invoices
    unpaid_invoices = Invoice.objects.filter(
        player=member, 
        status__in=['PENDING', 'OVERDUE']
    )
    if unpaid_invoices.exists():
        invoice_numbers = ", ".join([f"#{inv.invoice_number}" for inv in unpaid_invoices])
        return JsonResponse({'success': False, 'message': f"Cannot approve member. Unpaid invoices: {invoice_numbers}"})
    
    # Approve the member
    member.status = 'ACTIVE'
    member.approved_by = user
    member.approved_date = timezone.now()
    
    # Set specific status for subtypes
    if isinstance(member, Player):
        member.is_approved = True
    elif isinstance(member, Official):
        member.is_approved = True
    
    member.save()
    
    return JsonResponse({'success': True, 'message': f'{type(member).__name__} {member.get_full_name()} has been approved.'})


@login_required
@role_required(allowed_roles=['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_NATIONAL'])
@require_http_methods(["POST"])
def reject_member(request, member_id):
    """Reject a member with reason"""
    member = get_object_or_404(Member, id=member_id)
    
    # Check permissions
    user = request.user
    if not _user_can_approve_member(user, member):
        return JsonResponse({'success': False, 'message': 'You do not have permission to reject this member.'})
    
    try:
        data = json.loads(request.body)
        reason = data.get('reason', '').strip()
        
        if not reason:
            return JsonResponse({'success': False, 'message': 'Rejection reason is required.'})
        
        # Reject the member
        member.status = 'REJECTED'
        member.approved_by = user
        member.approved_date = timezone.now()
        member.rejection_reason = reason
        
        # Set specific status for subtypes
        if isinstance(member, Player):
            member.is_approved = False
        elif isinstance(member, Official):
            member.is_approved = False
        
        member.save()
        
        return JsonResponse({'success': True, 'message': f'{type(member).__name__} {member.get_full_name()} has been rejected.'})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error rejecting member: {str(e)}'})


@login_required
@role_required(allowed_roles=['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_NATIONAL'])
def member_details(request, member_id):
    """Get detailed member information"""
    member = get_object_or_404(Member, id=member_id)
    
    # Check permissions
    user = request.user
    if not _user_can_approve_member(user, member):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get member's invoices
    invoices = Invoice.objects.filter(player=member)
    
    context = {
        'member': member,
        'invoices': invoices,
        'missing_documents': RegistrationManager.validate_member_documents(member)
    }
    
    return render(request, 'registration/member_details_modal.html', context)


@login_required
@role_required(allowed_roles=['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_NATIONAL'])
@require_http_methods(["POST"])
def bulk_member_action(request):
    """Handle bulk actions on members"""
    try:
        data = json.loads(request.body)
        action = data.get('action')
        member_ids = data.get('member_ids', [])
        
        if not action or not member_ids:
            return JsonResponse({'success': False, 'message': 'Invalid action or member selection.'})
        
        members = Member.objects.filter(id__in=member_ids)
        user = request.user
        processed_count = 0
        
        for member in members:
            if not _user_can_approve_member(user, member):
                continue
            
            if action == 'approve':
                # Check if member can be approved
                missing_docs = RegistrationManager.validate_member_documents(member)
                unpaid_invoices = Invoice.objects.filter(player=member, status__in=['PENDING', 'OVERDUE'])
                
                if not missing_docs and not unpaid_invoices.exists():
                    member.status = 'ACTIVE'
                    member.approved_by = user
                    member.approved_date = timezone.now()
                    if isinstance(member, (Player, Official)):
                        member.is_approved = True
                    member.save()
                    processed_count += 1
            
            elif action == 'send_reminder':
                # Send payment reminder
                unpaid_invoices = Invoice.objects.filter(player=member, status__in=['PENDING', 'OVERDUE'])
                if unpaid_invoices.exists() and member.email:
                    _send_payment_reminder(member)
                    processed_count += 1
        
        return JsonResponse({
            'success': True, 
            'message': f'Successfully processed {processed_count} member(s).'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error processing bulk action: {str(e)}'})


@login_required
@role_required(allowed_roles=['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_NATIONAL'])
@require_http_methods(["POST"])
def send_payment_reminder(request, member_id):
    """Send payment reminder to a specific member"""
    member = get_object_or_404(Member, id=member_id)
    
    user = request.user
    if not _user_can_approve_member(user, member):
        return JsonResponse({'success': False, 'message': 'Permission denied.'})
    
    try:
        success = _send_payment_reminder(member)
        if success:
            return JsonResponse({'success': True, 'message': 'Payment reminder sent successfully.'})
        else:
            return JsonResponse({'success': False, 'message': 'No unpaid invoices or no email address.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error sending reminder: {str(e)}'})


def _user_can_approve_member(user, member):
    """Check if user has permission to approve specific member"""
    if user.role == 'ADMIN_NATIONAL':
        return True
    elif user.role == 'ADMIN_PROVINCE' and user.province:
        return member.province == user.province
    elif user.role == 'ADMIN_REGION' and user.region:
        return member.region == user.region
    elif user.role == 'ADMIN_LOCAL_FED' and user.local_federation:
        return member.lfa == user.local_federation
    return False


def _send_payment_reminder(member):
    """Helper function to send payment reminder"""
    try:
        unpaid_invoices = Invoice.objects.filter(
            player=member,
            status__in=['PENDING', 'OVERDUE']
        )
        
        if not unpaid_invoices.exists() or not member.email:
            return False
        
        total_amount = sum(inv.amount for inv in unpaid_invoices)
        
        subject = "SAFA Registration - Payment Reminder"
        context = {
            'member': member,
            'invoices': unpaid_invoices,
            'total_amount': total_amount,
        }
        
        message = render_to_string('registration/emails/payment_reminder.txt', context)
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member.email],
            fail_silently=False
        )
        
        return True
        
    except Exception as e:
        print(f"Failed to send payment reminder: {str(e)}")
        return False


# AJAX endpoints for form validation
@require_http_methods(["GET"])
def ajax_validate_id(request):
    """AJAX endpoint to validate ID numbers"""
    id_number = request.GET.get('id_number', '').strip()
    member_id = request.GET.get('member_id')  # For edit forms
    
    response = {'valid': False, 'exists': False, 'errors': []}
    
    if not id_number:
        return JsonResponse(response)
    
    # Check if ID already exists
    query = Member.objects.filter(id_number=id_number)
    if member_id:
        query = query.exclude(id=member_id)
    
    if query.exists():
        response['exists'] = True
        response['errors'].append('A member with this ID number already exists.')
        return JsonResponse(response)
    
    # Validate ID format and extract info
    try:
        id_info = CustomUser.extract_id_info(id_number)
        if id_info['is_valid']:
            response['valid'] = True
            response['date_of_birth'] = id_info['date_of_birth'].isoformat() if id_info['date_of_birth'] else None
            response['gender'] = id_info['gender']
        else:
            response['errors'].append(id_info.get('error', 'Invalid ID number'))
    except Exception as e:
        response['errors'].append(f'ID validation error: {str(e)}')
    
    return JsonResponse(response)


@require_http_methods(["GET"])
def ajax_validate_email(request):
    """AJAX endpoint to validate email addresses"""
    email = request.GET.get('email', '').strip()
    member_id = request.GET.get('member_id')
    
    query = Member.objects.filter(email__iexact=email)
    if member_id:
        query = query.exclude(id=member_id)
    
    return JsonResponse({
        'exists': query.exists()
    })


@require_http_methods(["GET"])
def ajax_validate_safa_id(request):
    """AJAX endpoint to validate SAFA IDs"""
    safa_id = request.GET.get('safa_id', '').strip()
    member_id = request.GET.get('member_id')
    
    query = Member.objects.filter(safa_id=safa_id)
    if member_id:
        query = query.exclude(id=member_id)
    
    return JsonResponse({
        'exists': query.exists()
    })


# Geography cascade endpoints (existing but streamlined)
@require_http_methods(["GET"])
def api_regions(request):
    """Get regions for a province"""
    province_id = request.GET.get('province_id')
    if not province_id:
        return JsonResponse([])
    
    from geography.models import Region
    regions = Region.objects.filter(province_id=province_id).values('id', 'name')
    return JsonResponse(list(regions), safe=False)


@require_http_methods(["GET"]) 
def api_lfas(request):
    """Get LFAs for a region"""
    region_id = request.GET.get('region_id')
    if not region_id:
        return JsonResponse([])
    
    from geography.models import LocalFootballAssociation
    lfas = LocalFootballAssociation.objects.filter(region_id=region_id).values('id', 'name')
    return JsonResponse(list(lfas), safe=False)


@require_http_methods(["GET"])
def api_clubs(request):
    """Get clubs for an LFA"""
    lfa_id = request.GET.get('lfa_id')
    if not lfa_id:
        return JsonResponse([])
    
    from geography.models import Club
    clubs = Club.objects.filter(
        localfootballassociation_id=lfa_id,
        status='ACTIVE'
    ).values('id', 'name')
    return JsonResponse(list(clubs), safe=False)


# Export and reporting views
@login_required
@role_required(allowed_roles=['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_NATIONAL'])
def export_members(request):
    """Export members to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="safa_members.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'SAFA ID', 'Status', 'Registration Date', 'Club', 'Type'])
    
    # Get members based on user permissions
    user = request.user
    members = Member.objects.all()
    
    if user.role == 'ADMIN_LOCAL_FED' and user.local_federation:
        members = members.filter(lfa=user.local_federation)
    elif user.role == 'ADMIN_REGION' and user.region:
        members = members.filter(region=user.region)
    elif user.role == 'ADMIN_PROVINCE' and user.province:
        members = members.filter(province=user.province)
    
    for member in members:
        writer.writerow([
            member.get_full_name(),
            member.email,
            member.safa_id or '',
            member.get_status_display(),
            member.created.strftime('%Y-%m-%d'),
            member.club.name if member.club else '',
            type(member).__name__
        ])
    
    return response


@login_required
@role_required(allowed_roles=['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_NATIONAL'])
def generate_report(request):
    """Generate registration report"""
    # This would generate a more detailed report
    # For now, redirect to export
    return export_members(request)


# Legacy views for backwards compatibility
def senior_registration(request):
    """Legacy senior registration - redirect to universal"""
    return redirect('registration:universal_registration')


def club_admin_add_player(request):
    """Legacy club admin add player - redirect to universal"""
    return redirect('registration:universal_registration')


class RegistrationManager:
    """Centralized registration management to reduce code duplication"""
    
    @staticmethod
    def create_member_invoice(member, amount, description, invoice_type='MEMBERSHIP'):
        """Create standardized invoices for members"""
        invoice = Invoice.objects.create(
            player=member,
            amount=amount,
            status='PENDING',
            invoice_type=invoice_type,
            due_date=timezone.now() + timezone.timedelta(days=30)
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description=description,
            quantity=1,
            unit_price=amount
        )
        return invoice
    
    @staticmethod
    def generate_unique_email(first_name, last_name, domain_suffix='safa.system'):
        """Generate unique email addresses"""
        from django.utils.crypto import get_random_string
        
        base_email = f"{first_name.lower()}.{last_name.lower()}@{domain_suffix}"
        if not Member.objects.filter(email=base_email).exists():
            return base_email
        
        # Add random suffix if base email exists
        counter = 1
        while counter < 100:  # Prevent infinite loop
            email = f"{first_name.lower()}.{last_name.lower()}{counter}@{domain_suffix}"
            if not Member.objects.filter(email=email).exists():
                return email
            counter += 1
        
        # Fallback to completely random
        return f"member_{get_random_string(8)}@{domain_suffix}"
    
    @staticmethod
    def validate_member_documents(member):
        """Validate required documents for approval"""
        missing_docs = []
        
        if not member.profile_picture:
            missing_docs.append("Profile picture")
        
        if member.id_document_type == 'ID' and not member.id_document:
            missing_docs.append("ID document")
        elif member.id_document_type == 'PP' and not member.id_document:
            missing_docs.append("Passport document")
        
        return missing_docs


@login_required
def universal_registration(request):
    """Universal registration form for all member types"""
    if request.method == 'POST':
        form = UniversalRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    registration_type = form.cleaned_data.get('registration_type')
                    
                    # Create appropriate member instance
                    if registration_type == 'PLAYER':
                        member = Player()
                    elif registration_type == 'OFFICIAL':
                        member = Official()
                    else:
                        member = Member()
                    
                    # Copy form data to member
                    for field_name, value in form.cleaned_data.items():
                        if hasattr(member, field_name) and field_name != 'registration_type':
                            setattr(member, field_name, value)
                    
                    # Set defaults
                    member.status = 'PENDING'
                    if not member.email:
                        member.email = RegistrationManager.generate_unique_email(
                            member.first_name, member.last_name
                        )
                    
                    # Set geography relationships from club/organization
                    if member.club:
                        if not member.lfa and member.club.localfootballassociation:
                            member.lfa = member.club.localfootballassociation
                        if not member.region and member.club.region:
                            member.region = member.club.region
                        if not member.province and member.club.province:
                            member.province = member.club.province
                    
                    # Force role for specific types
                    if isinstance(member, Player):
                        member.role = 'PLAYER'
                    elif isinstance(member, Official):
                        member.role = 'OFFICIAL'
                    
                    member.save()
                    
                    # Create invoices based on member type
                    invoices_created = []
                    
                    # National membership fee (everyone pays this)
                    national_invoice = RegistrationManager.create_member_invoice(
                        member, 100.00, 'National Federation Membership Fee', 'MEMBERSHIP'
                    )
                    invoices_created.append(national_invoice)
                    
                    # Additional fees based on type and club registration
                    if isinstance(member, Player) and member.club:
                        club_invoice = RegistrationManager.create_member_invoice(
                            member, 200.00, f'Club Registration Fee - {member.club.name}', 'REGISTRATION'
                        )
                        invoices_created.append(club_invoice)
                        
                        # Create club registration record
                        PlayerClubRegistration.objects.create(
                            player=member,
                            club=member.club,
                            status='PENDING'
                        )
                    
                    elif isinstance(member, Official):
                        # Different fees for different official types
                        position_type = member.position.title.lower() if member.position else ""
                        if "referee" in position_type:
                            fee, description = 250.00, "Referee Registration Fee"
                        elif "coach" in position_type:
                            fee, description = 200.00, "Coach Registration Fee"
                        else:
                            fee, description = 150.00, "Official Registration Fee"
                        
                        official_invoice = RegistrationManager.create_member_invoice(
                            member, fee, description, 'REGISTRATION'
                        )
                        invoices_created.append(official_invoice)
                    
                    # Success message
                    total_amount = sum(inv.amount for inv in invoices_created)
                    invoice_numbers = ", ".join([f"#{inv.invoice_number}" for inv in invoices_created])
                    
                    messages.success(request, 
                        f'{registration_type.title()} registration successful! '
                        f'Invoices created: {invoice_numbers}. '
                        f'Total fees: R{total_amount:.2f}. '
                        f'Member will be eligible for approval once invoices are paid.'
                    )
                    
                    return redirect('membership:registration_success')
                    
            except Exception as e:
                messages.error(request, f"Registration failed: {str(e)}")
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    field_label = form.fields.get(field, {}).get('label', field)
                    messages.error(request, f"{field_label}: {error}")
    else:
        form = UniversalRegistrationForm()
    
    return render(request, 'registration/universal_registration.html', {
        'form': form,
        'title': 'SAFA Universal Registration'
    })


@login_required
@role_required(allowed_roles=['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_NATIONAL'])
def member_approval_dashboard(request):
    """Centralized approval dashboard for all member types"""
    user = request.user
    
    # Get members based on user's role and hierarchy
    base_queryset = Member.objects.all()
    
    if user.role == 'ADMIN_LOCAL_FED' and user.local_federation:
        base_queryset = base_queryset.filter(lfa=user.local_federation)
    elif user.role == 'ADMIN_REGION' and user.region:
        base_queryset = base_queryset.filter(region=user.region)
    elif user.role == 'ADMIN_PROVINCE' and user.province:
        base_queryset = base_queryset.filter(province=user.province)
    # ADMIN_NATIONAL sees all
    
    # Filter by approval status
    status_filter = request.GET.get('status', 'pending')
    if status_filter == 'pending':
        members = base_queryset.filter(status='PENDING')
    elif status_filter == 'approved':
        members = base_queryset.filter(status='ACTIVE')
    else:
        members = base_queryset
    
    # Separate by type
    players = members.filter(role='PLAYER')
    officials = members.filter(role='OFFICIAL')
    general_members = members.filter(role__isnull=True)
    
    # Check payment status for each member
    members_data = []
    for member in members:
        unpaid_invoices = Invoice.objects.filter(
            player=member, 
            status__in=['PENDING', 'OVERDUE']
        )
        members_data.append({
            'member': member,
            'member_type': type(member).__name__,
            'unpaid_invoices': unpaid_invoices,
            'has_unpaid': unpaid_invoices.exists(),
            'missing_documents': RegistrationManager.validate_member_documents(member)
        })
    
    return render(request, 'registration/approval_dashboard.html', {
        'members_data': members_data,
        'players_count': players.count(),
        'officials_count': officials.count(),
        'general_members_count': general_members.count(),
        'status_filter': status_filter,
    })


@login_required
@role_required(allowed_roles=['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_NATIONAL'])
@require_http_methods(["POST"])
def approve_member(request, member_id):
    """Unified member approval endpoint"""
    member = get_object_or_404(Member, id=member_id)
    
    # Check permissions (similar logic as approval dashboard)
    user = request.user
    if not _user_can_approve_member(user, member):
        messages.error(request, 'You do not have permission to approve this member.')
        return redirect('registration:approval_dashboard')
    
    # Validate documents
    missing_docs = RegistrationManager.validate_member_documents(member)
    if missing_docs:
        messages.error(request, f"Cannot approve member. Missing: {', '.join(missing_docs)}")
        return redirect('registration:member_detail', member_id=member.id)
    
    # Check for unpaid invoices
    unpaid_invoices = Invoice.objects.filter(
        player=member, 
        status__in=['PENDING', 'OVERDUE']
    )
    if unpaid_invoices.exists():
        invoice_numbers = ", ".join([f"#{inv.invoice_number}" for inv in unpaid_invoices])
        messages.error(request, f"Cannot approve member. Unpaid invoices: {invoice_numbers}")
        return redirect('registration:member_detail', member_id=member.id)
    
    # Approve the member
    member.status = 'ACTIVE'
    member.approved_by = user
    member.approved_date = timezone.now()
    
    # Set specific status for subtypes
    if isinstance(member, Player):
        member.is_approved = True
    elif isinstance(member, Official):
        member.is_approved = True
    
    member.save()
    
    messages.success(request, f'{type(member).__name__} {member.get_full_name()} has been approved.')
    return redirect('registration:approval_dashboard')


def _user_can_approve_member(user, member):
    """Check if user has permission to approve specific member"""
    if user.role == 'ADMIN_NATIONAL':
        return True
    elif user.role == 'ADMIN_PROVINCE' and user.province:
        return member.province == user.province
    elif user.role == 'ADMIN_REGION' and user.region:
        return member.region == user.region
    elif user.role == 'ADMIN_LOCAL_FED' and user.local_federation:
        return member.lfa == user.local_federation
    return False


# AJAX endpoints for form validation
@require_http_methods(["GET"])
def ajax_validate_id(request):
    """AJAX endpoint to validate ID numbers"""
    id_number = request.GET.get('id_number', '').strip()
    member_id = request.GET.get('member_id')  # For edit forms
    
    response = {'valid': False, 'exists': False, 'errors': []}
    
    if not id_number:
        return JsonResponse(response)
    
    # Check if ID already exists
    query = Member.objects.filter(id_number=id_number)
    if member_id:
        query = query.exclude(id=member_id)
    
    if query.exists():
        response['exists'] = True
        response['errors'].append('A member with this ID number already exists.')
        return JsonResponse(response)
    
    # Validate ID format and extract info
    try:
        id_info = CustomUser.extract_id_info(id_number)
        if id_info['is_valid']:
            response['valid'] = True
            response['date_of_birth'] = id_info['date_of_birth'].isoformat() if id_info['date_of_birth'] else None
            response['gender'] = id_info['gender']
        else:
            response['errors'].append(id_info.get('error', 'Invalid ID number'))
    except Exception as e:
        response['errors'].append(f'ID validation error: {str(e)}')
    
    return JsonResponse(response)


@require_http_methods(["GET"])
def ajax_validate_email(request):
    """AJAX endpoint to validate email addresses"""
    email = request.GET.get('email', '').strip()
    member_id = request.GET.get('member_id')
    
    query = Member.objects.filter(email__iexact=email)
    if member_id:
        query = query.exclude(id=member_id)
    
    return JsonResponse({
        'exists': query.exists()
    })


@require_http_methods(["GET"])
def ajax_validate_safa_id(request):
    """AJAX endpoint to validate SAFA IDs"""
    safa_id = request.GET.get('safa_id', '').strip()
    member_id = request.GET.get('member_id')
    
    query = Member.objects.filter(safa_id=safa_id)
    if member_id:
        query = query.exclude(id=member_id)
    
    return JsonResponse({
        'exists': query.exists()
    })


# Geography cascade endpoints (existing but streamlined)
@require_http_methods(["GET"])
def api_regions(request):
    """Get regions for a province"""
    province_id = request.GET.get('province_id')
    if not province_id:
        return JsonResponse([])
    
    from geography.models import Region
    regions = Region.objects.filter(province_id=province_id).values('id', 'name')
    return JsonResponse(list(regions), safe=False)


@require_http_methods(["GET"]) 
def api_lfas(request):
    """Get LFAs for a region"""
    region_id = request.GET.get('region_id')
    if not region_id:
        return JsonResponse([])
    
    from geography.models import LocalFootballAssociation
    lfas = LocalFootballAssociation.objects.filter(region_id=region_id).values('id', 'name')
    return JsonResponse(list(lfas), safe=False)


@require_http_methods(["GET"])
def api_clubs(request):
    """Get clubs for an LFA"""
    lfa_id = request.GET.get('lfa_id')
    if not lfa_id:
        return JsonResponse([])
    
    from geography.models import Club
    clubs = Club.objects.filter(
        localfootballassociation_id=lfa_id,
        status='ACTIVE'
    ).values('id', 'name')
    return JsonResponse(list(clubs), safe=False)
