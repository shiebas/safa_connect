from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.contrib import messages
from django.utils import timezone

from .models import Transfer, TransferAppeal
from .forms import TransferAppealForm


class AppealRequiredMixin(PermissionRequiredMixin):
    def has_permission(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
            
        try:
            member = user.member_profile
            # Admin and Club Admins can handle appeals
            return member.role in ['ADMIN', 'CLUB_ADMIN']
        except:
            return False


class AppealListView(LoginRequiredMixin, ListView):
    """List appeals that the user can access"""
    model = TransferAppeal
    template_name = 'membership/appeal/appeal_list.html'
    context_object_name = 'appeals'

    def get_queryset(self):
        if self.request.user.has_perm('membership.can_review_appeals'):
            return TransferAppeal.objects.all()
        return TransferAppeal.objects.filter(
            submitted_by=self.request.user.member
        )


class ReviewAppealListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List appeals that need to be reviewed"""
    model = TransferAppeal
    template_name = 'membership/appeal/review_appeal_list.html'
    context_object_name = 'appeals'
    permission_required = 'membership.can_review_appeals'

    def get_queryset(self):
        # Show only pending appeals that need review
        return TransferAppeal.objects.filter(status='PENDING').order_by('-appeal_submission_date')


class AppealCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create a new appeal for a rejected transfer"""
    model = TransferAppeal
    form_class = TransferAppealForm
    template_name = 'membership/appeal/appeal_form.html'
    permission_required = 'membership.can_submit_appeals'

    def get_transfer(self):
        transfer_id = self.kwargs.get('transfer_id')
        return get_object_or_404(Transfer, pk=transfer_id, status='REJECTED')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['transfer'] = self.get_transfer()
        kwargs['submitted_by'] = self.request.user.member
        return kwargs

    def get_success_url(self):
        return reverse_lazy('membership:appeal_detail', 
                          kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)


class AppealDetailView(LoginRequiredMixin, DetailView):
    """View appeal details and handle decisions"""
    model = TransferAppeal
    template_name = 'membership/appeal/appeal_detail.html'
    context_object_name = 'appeal'

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.has_perm('membership.can_review_appeals'):
            qs = qs.filter(submitted_by=self.request.user.member)
        return qs


class AppealReviewView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Review and decide on an appeal"""
    model = TransferAppeal
    template_name = 'membership/appeal/appeal_review.html'
    fields = ['review_notes', 'requires_federation_approval']
    permission_required = 'membership.can_review_appeals'

    def get_success_url(self):
        return reverse_lazy('membership:appeal_detail', 
                          kwargs={'pk': self.object.pk})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        if self.object.status not in ['PENDING', 'ESCALATED']:
            messages.error(request, _("This appeal cannot be reviewed."))
            return redirect(self.get_success_url())

        action = request.POST.get('action')
        notes = request.POST.get('review_notes', '')
        requires_federation = request.POST.get('requires_federation_approval') == 'on'

        try:
            if self.object.status == 'PENDING':
                if action == 'uphold':
                    self.object.requires_federation_approval = requires_federation
                    self.object.uphold(request.user.member, notes)
                    if requires_federation:
                        messages.success(request, _("Appeal escalated to federation for review."))
                    else:
                        messages.success(request, _("Appeal upheld successfully."))
                elif action == 'dismiss':
                    self.object.dismiss(request.user.member, notes)
                    messages.success(request, _("Appeal dismissed successfully."))
                else:
                    messages.error(request, _("Invalid action."))
            elif self.object.status == 'ESCALATED':
                if not request.user.has_perm('membership.can_review_federation_appeals'):
                    messages.error(request, _("You don't have permission to review federation appeals."))
                    return redirect(self.get_success_url())
                
                if action == 'federation_approve':
                    self.object.federation_review(request.user.member, True, notes)
                    messages.success(request, _("Appeal approved by federation."))
                elif action == 'federation_reject':
                    self.object.federation_review(request.user.member, False, notes)
                    messages.success(request, _("Appeal rejected by federation."))
                else:
                    messages.error(request, _("Invalid federation action."))
        except ValidationError as e:
            messages.error(request, str(e))

        return redirect(self.get_success_url())


class FederationAppealListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List appeals that require federation review"""
    model = TransferAppeal
    template_name = 'membership/appeal/federation_appeal_list.html'
    context_object_name = 'appeals'
    permission_required = 'membership.can_review_federation_appeals'

    def get_queryset(self):
        return TransferAppeal.objects.filter(status='ESCALATED').order_by('-appeal_submission_date')


class FederationAppealHistoryView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List appeals that have been reviewed at federation level"""
    model = TransferAppeal
    template_name = 'membership/appeal/federation_appeal_history.html'
    context_object_name = 'appeals'
    permission_required = 'membership.can_review_federation_appeals'

    def get_queryset(self):
        return TransferAppeal.objects.filter(
            status__in=['FEDERATION_APPROVED', 'FEDERATION_REJECTED']
        ).order_by('-federation_review_date')
