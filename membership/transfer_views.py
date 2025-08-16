from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Transfer, Member, MemberSeasonHistory
from .forms import TransferRequestForm
from geography.models import Club


class TransferPermissionMixin(PermissionRequiredMixin):
    """
    Mixin to check transfer-related permissions based on user's role and club association.
    """
    def has_permission(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True

        member_profile = getattr(user, 'member_profile', None)
        if not member_profile or not member_profile.current_club:
            return False

        # Allow club admins to manage transfers for their club
        if member_profile.current_club.club_admins.filter(pk=user.pk).exists():
            return True

        # Allow LFA admins to manage transfers within their LFA
        if member_profile.current_club.lfa and member_profile.current_club.lfa.lfa_admins.filter(pk=user.pk).exists():
            return True

        return False


class TransferListView(TransferPermissionMixin, ListView):
    """List transfers relevant to the user's club or administrative area."""
    model = Transfer
    template_name = 'membership/transfer/transfer_list.html'
    context_object_name = 'transfers'
    permission_required = 'membership.view_transfer'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return Transfer.objects.all()

        member_profile = getattr(user, 'member_profile', None)
        if not member_profile or not member_profile.current_club:
            return Transfer.objects.none()

        # Club admins see transfers involving their club
        if member_profile.current_club.club_admins.filter(pk=user.pk).exists():
            return Transfer.objects.filter(
                models.Q(from_club=member_profile.current_club) | models.Q(to_club=member_profile.current_club)
            )

        # LFA admins see transfers within their LFA
        if member_profile.current_club.lfa and member_profile.current_club.lfa.lfa_admins.filter(pk=user.pk).exists():
            return Transfer.objects.filter(from_club__lfa=member_profile.current_club.lfa)

        return Transfer.objects.none()


class TransferRequestView(TransferPermissionMixin, CreateView):
    """Create a new transfer request."""
    model = Transfer
    form_class = TransferRequestForm
    template_name = 'membership/transfer/transfer_request.html'
    permission_required = 'membership.add_transfer'
    success_url = reverse_lazy('membership:transfer_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            transfer = form.save(commit=False)
            transfer.from_club = transfer.member.current_club

            # Additional check to ensure the user has permission for the from_club
            user_can_initiate = False
            member_profile = getattr(self.request.user, 'member_profile', None)
            if self.request.user.is_superuser or self.request.user.is_staff:
                user_can_initiate = True
            elif member_profile and member_profile.current_club:
                if member_profile.current_club == transfer.from_club:
                    user_can_initiate = True
                if member_profile.current_club.lfa == transfer.from_club.lfa:
                    user_can_initiate = True

            if not user_can_initiate:
                messages.error(self.request, _("You do not have permission to initiate a transfer for this club."))
                return self.form_invalid(form)

            transfer.save()
            messages.success(self.request, _("Transfer request created successfully."))
            return redirect(self.success_url)


class TransferDetailView(TransferPermissionMixin, DetailView):
    """View transfer details and handle approval/rejection."""
    model = Transfer
    template_name = 'membership/transfer/transfer_detail.html'
    context_object_name = 'transfer'
    permission_required = 'membership.view_transfer'

    def post(self, request, *args, **kwargs):
        transfer = self.get_object()
        action = request.POST.get('action')
        
        if action == 'approve' and request.user.has_perm('membership.change_transfer'):
            try:
                transfer.approve(approved_by=request.user)
                messages.success(request, _("Transfer approved successfully."))
            except ValidationError as e:
                messages.error(request, str(e))
                
        elif action == 'reject' and request.user.has_perm('membership.change_transfer'):
            reason = request.POST.get('rejection_reason')
            if not reason:
                messages.error(request, _("Please provide a rejection reason."))
            else:
                try:
                    transfer.reject(rejected_by=request.user, reason=reason)
                    messages.success(request, _("Transfer rejected."))
                except ValidationError as e:
                    messages.error(request, str(e))
        
        return redirect('membership:transfer_detail', pk=transfer.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transfer = self.get_object()
        
        context['can_approve'] = self.request.user.has_perm('membership.change_transfer')
        context['can_reject'] = self.request.user.has_perm('membership.change_transfer')
        
        # Show member's season history
        context['registration_history'] = MemberSeasonHistory.objects.filter(
            member=transfer.member
        ).order_by('-season_config__season_year')
        
        return context


class TransferApproveView(TransferPermissionMixin, UpdateView):
    """Handle transfer approval confirmation."""
    model = Transfer
    template_name = 'membership/transfer/transfer_approve.html'
    fields = []
    permission_required = 'membership.change_transfer'
    
    def get_success_url(self):
        return reverse_lazy('membership:transfer_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object.approve(approved_by=self.request.user)
                messages.success(self.request, _("Transfer approved successfully."))
                return redirect(self.get_success_url())
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class TransferRejectView(TransferPermissionMixin, UpdateView):
    """Handle transfer rejection confirmation."""
    model = Transfer
    template_name = 'membership/transfer/transfer_reject.html'
    fields = ['rejection_reason']
    permission_required = 'membership.change_transfer'
    
    def get_success_url(self):
        return reverse_lazy('membership:transfer_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        try:
            with transaction.atomic():
                reason = form.cleaned_data['rejection_reason']
                self.object.reject(rejected_by=self.request.user, reason=reason)
                messages.success(self.request, _("Transfer rejected successfully."))
                return redirect(self.get_success_url())
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
