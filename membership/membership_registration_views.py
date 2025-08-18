from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils import timezone
from django.core.mail import send_mail
from django.urls import reverse
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.conf import settings

from accounts.utils import send_welcome_email, send_rejection_email
from .models import Member, JuniorMember, ClubRegistration
from .forms import MembershipApplicationForm, ClubRegistrationForm
from geography.models import Club


def membership_application(request):
    """
    Step 1: Apply for SAFA membership (required before club registration)
    Everyone must register as a member first, regardless of role

    Note: Junior members (under 18) must be registered by a club administrator
    """
    if request.method == 'POST':
        form = MembershipApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            # Check if this is a junior application
            is_junior = form.cleaned_data.get('is_junior', False)
            date_of_birth = form.cleaned_data.get('date_of_birth')

            # Calculate age if date of birth is provided
            is_under_18 = False
            if date_of_birth:
                age = (timezone.now().date() - date_of_birth).days // 365
                is_under_18 = age < 18

            # If this is a junior application and not from a club admin, reject it
            if (is_junior or is_under_18) and not request.user.is_authenticated:
                messages.error(request, _("Junior members (under 18) must be registered by a club administrator."))
                return render(request, 'membership/membership_application.html', {'form': form})

            # If this is a junior application and the user is authenticated but not a club admin, reject it
            if (is_junior or is_under_18) and request.user.is_authenticated:
                if not hasattr(request.user, 'role') or request.user.role not in ['CLUB_ADMIN', 'ADMIN', 'ADMIN_COUNTRY']:
                    messages.error(request, _("Junior members (under 18) must be registered by a club administrator."))
                    return render(request, 'membership/membership_application.html', {'form': form})

            # Create Member FIRST
            member_data = form.cleaned_data.copy()
            is_junior = member_data.pop('is_junior', False) or is_under_18

            # Handle junior-specific data
            if is_junior:
                junior_data = {
                    k: member_data.pop(k)
                    for k in ['guardian_name', 'guardian_email', 'guardian_phone', 'school']
                    if k in member_data
                }

            # Remove fields that aren't part of the Member model
            member_fields = [field.name for field in Member._meta.fields]
            filtered_data = {k: v for k, v in member_data.items() if k in member_fields}

            # Create and save base Member
            member = Member(**filtered_data)

            # If registered by a club admin, mark it
            if request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role in ['CLUB_ADMIN', 'ADMIN', 'ADMIN_COUNTRY']:
                member.registered_by_admin = True
                member.registering_admin = request.user

            member.save()

            # Create Junior profile if needed
            if is_junior:
                junior = JuniorMember.objects.create(
                    member_ptr=member,
                    **junior_data
                )
                junior.save()

            # Send for approval
            send_approval_request(member)

            messages.success(request, _("Your SAFA membership application has been submitted for review."))
            return redirect('membership:application_submitted')
    else:
        form = MembershipApplicationForm()

    return render(request, 'membership/membership_application.html', {'form': form})


@staff_member_required
def approve_member(request, member_id):
    """Approve a member's SAFA registration"""
    member = get_object_or_404(Member, pk=member_id)

    if request.method == 'POST':
        member.approve_membership(request.user)
        send_welcome_email(member)
        messages.success(request, f"Membership for {member.get_full_name()} approved successfully")
        return redirect('membership:membership_dashboard')

    return render(request, 'membership/admin/approve_member.html', {'member': member})


@staff_member_required
def reject_member(request, member_id):
    """Reject a member's SAFA registration"""
    member = get_object_or_404(Member, pk=member_id)

    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        member.reject_membership(request.user, reason)
        send_rejection_email(member, reason)
        messages.success(request, f"Membership for {member.get_full_name()} rejected")
        return redirect('membership:membership_dashboard')

    return render(request, 'membership/admin/reject_member.html', {'member': member})


@login_required
def register_with_club(request, member_id=None):
    """
    Step 2: Register with a club (only after SAFA approval)
    """
    if member_id:
        member = get_object_or_404(Member, pk=member_id)
    else:
        # Try to find member by email or other identifier
        # This would need to be implemented based on your authentication system
        member = None

    if not member:
        messages.error(request, "Member not found. Please complete SAFA registration first.")
        return redirect('membership:membership_application')

    if member.status != 'ACTIVE':
        messages.error(request, "Only approved SAFA members can register with clubs")
        return redirect('membership:member_profile')

    # Check if already registered with a club
    if hasattr(member, 'club_registration'):
        messages.warning(request, "You're already registered with a club")
        return redirect('membership:member_profile')

    if request.method == 'POST':
        form = ClubRegistrationForm(request.POST)
        if form.is_valid():
            # Create club registration
            registration = form.save(commit=False)
            registration.member = member
            registration.save()

            messages.success(request, f"Successfully registered with {registration.club.name}")
            return redirect('membership:member_profile')
    else:
        form = ClubRegistrationForm()

    return render(request, 'membership/club_registration.html', {
        'member': member,
        'form': form
    })


@staff_member_required
def membership_dashboard(request):
    """Dashboard for staff to manage membership applications"""
    pending_members = Member.objects.filter(status='PENDING').order_by('-created')
    recent_approvals = Member.objects.filter(status='ACTIVE').order_by('-approved_date')[:10]
    recent_rejections = Member.objects.filter(status='REJECTED').order_by('-modified')[:10]

    context = {
        'pending_members': pending_members,
        'recent_approvals': recent_approvals,
        'recent_rejections': recent_rejections,
        'total_pending': pending_members.count(),
        'total_active': Member.objects.filter(status='ACTIVE').count(),
    }

    return render(request, 'membership/admin/membership_dashboard.html', context)


class ApplicationSubmittedView(TemplateView):
    """Confirmation page after submitting membership application"""
    template_name = 'membership/application_submitted.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Application Submitted")
        return context


def send_approval_request(member):
    """Send notification to admins for new membership application"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_emails = [
            user.email for user in
            User.objects.filter(is_staff=True, email__isnull=False)
            if user.email
        ]

        if admin_emails:
            subject = f"New SAFA Membership Application: {member.get_full_name()}"
            message = f"""
            A new SAFA membership application has been submitted.

            Name: {member.get_full_name()}
            Email: {member.email}
            Member Type: {member.get_member_type_display()}
            Date of Birth: {member.date_of_birth}
            SAFA ID: {member.safa_id}

            Please review and approve/reject this application in the admin dashboard.
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                fail_silently=True,
            )
    except Exception:
        pass  # Fail silently if email can't be sent


# API endpoints for AJAX functionality
def check_member_status(request):
    """Check if member is approved and can register with clubs"""
    email = request.GET.get('email')
    if not email:
        return JsonResponse({'error': 'Email required'}, status=400)

    try:
        member = Member.objects.get(email=email)
        return JsonResponse({
            'exists': True,
            'status': member.status,
            'approved': member.status == 'ACTIVE',
            'safa_id': member.safa_id,
            'member_type': member.member_type,
        })
    except Member.DoesNotExist:
        return JsonResponse({
            'exists': False,
            'message': 'No SAFA membership found with this email'
        })
# End of file
