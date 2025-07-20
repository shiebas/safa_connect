from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from membership.models import Member, Official, Transfer, MembershipApplication
from membership.models import Invoice

class SeniorMembershipDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'membership/senior_membership_dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser and request.user.role != 'ADMIN_NATIONAL':
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Senior Membership Approval")

        # Get all members
        members = Member.objects.all()

        # Filter by approval status
        approval_status = self.request.GET.get('status', 'pending')
        if approval_status == 'pending':
            members = members.filter(status='PENDING')
        elif approval_status == 'approved':
            members = members.filter(status='ACTIVE')
        elif approval_status == 'rejected':
            members = members.filter(status='REJECTED')

        context['members'] = members
        context['approval_status'] = approval_status
        return context

def approve_membership(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    member.status = 'ACTIVE'
    member.approved_by = request.user # Assign the user who approved
    member.approved_date = timezone.now() # Set the approval date
    member.save()
    messages.success(request, f'Membership for {member.get_full_name()} has been approved.')
    return redirect('membership:senior_membership_dashboard')

def reject_membership(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    member.status = 'REJECTED'
    member.save()
    messages.success(request, f'Membership for {member.get_full_name()} has been rejected.')
    return redirect('membership:senior_membership_dashboard')

class JuniorMembershipDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'membership/junior_membership_dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser and request.user.role != 'ADMIN_NATIONAL':
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Junior Membership Approval")

        # Get all junior members
        members = Member.objects.filter(member_type='JUNIOR')

        # Filter by approval status
        approval_status = self.request.GET.get('status', 'pending')
        if approval_status == 'pending':
            members = members.filter(status='PENDING')
        elif approval_status == 'approved':
            members = members.filter(status='ACTIVE')
        elif approval_status == 'rejected':
            members = members.filter(status='REJECTED')

        context['members'] = members
        context['approval_status'] = approval_status
        return context