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

from .models import Member, JuniorMember, ClubRegistration
from .forms import MembershipApplicationForm, ClubRegistrationForm
from geography.models import Club


def membership_application(request):
    """
    Step 1: Apply for SAFA membership (required before club registration)
    Everyone must register as a member first, regardless of role
    """
    if request.method == 'POST':
        form = MembershipApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create Member FIRST
            member_data = form.cleaned_data.copy()
            is_junior = member_data.pop('is_junior', False)
            
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


def send_welcome_email(member):
    """Send welcome email to approved member"""
    if member.email:
        try:
            subject = "Welcome to SAFA - Your Membership Has Been Approved"
            message = f"""
            Dear {member.first_name},
            
            Congratulations! Your SAFA membership application has been approved.
            
            Your SAFA ID is: {member.safa_id}
            
            Next steps:
            1. Complete your profile information
            2. Register with a club or association
            3. Keep your membership information up to date
            
            Welcome to the South African Football Association!
            
            Best regards,
            SAFA Administration
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [member.email],
                fail_silently=True,
            )
        except Exception:
            pass  # Fail silently


def send_rejection_email(member, reason):
    """Send rejection email to member"""
    if member.email:
        try:
            subject = "SAFA Membership Application Update"
            message = f"""
            Dear {member.first_name},
            
            Thank you for your interest in SAFA membership. 
            
            Unfortunately, your application could not be approved at this time.
            
            Reason: {reason}
            
            If you have any questions or would like to reapply, please contact us.
            
            Best regards,
            SAFA Administration
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [member.email],
                fail_silently=True,
            )
        except Exception:
            pass  # Fail silently


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
