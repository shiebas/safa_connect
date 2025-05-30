from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Transfer, Player, Club, PlayerClubRegistration
from .forms import TransferRequestForm


class TransferRequiredMixin(PermissionRequiredMixin):
    def has_permission(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
            
        try:
            member = user.member_profile
            
            # System & Country Admin (SuperUser) - Full access
            if member.role in ['ADMIN_SYSTEM', 'ADMIN_COUNTRY']:
                return True
                
            # Federation Admin - Full access to transfers within their federation
            if member.role == 'ADMIN_FEDERATION':
                if isinstance(self, TransferRequestView):
                    return True
                transfer = getattr(self, 'get_object', lambda: None)()
                if transfer:
                    # TODO: Add federation check once federation field is added
                    return True
                return True  # List view
                
            # Province & Region Admins - View and approve transfers in their area
            if member.role in ['ADMIN_PROVINCE', 'ADMIN_REGION']:
                if isinstance(self, TransferRequestView):
                    return False  # Cannot initiate transfers
                transfer = getattr(self, 'get_object', lambda: None)()
                if transfer:
                    # TODO: Add province/region check once those fields are added
                    return True
                return True  # List view
                
            # Local Federation Admin - Manage transfers between clubs in their local federation
            if member.role == 'ADMIN_LOCAL_FED':
                if isinstance(self, TransferRequestView):
                    return True
                transfer = getattr(self, 'get_object', lambda: None)()
                if transfer:
                    # TODO: Add local federation check once that field is added
                    return True
                return True  # List view
                
            # Club Admin - Can only initiate transfers and view their club's transfers
            if member.role == 'CLUB_ADMIN':
                if isinstance(self, TransferRequestView):
                    return True  # Can initiate transfers
                    
                # For other views, only allow if the transfer involves their club
                transfer = getattr(self, 'get_object', lambda: None)()
                if transfer:
                    return member.club in [transfer.from_club, transfer.to_club]
                return True  # Allow list view
                
        except Exception:
            return False
            
        return False


class TransferListView(TransferRequiredMixin, ListView):
    """List transfers relevant to the user's club"""
    model = Transfer
    template_name = 'membership/transfer/transfer_list.html'
    context_object_name = 'transfers'
    permission_required = 'membership.view_transfer'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Transfer.objects.all()
            
        member = user.member_profile
        
        # System & Country Admin - Full access
        if member.role in ['ADMIN_SYSTEM', 'ADMIN_COUNTRY']:
            return Transfer.objects.all()
            
        # Federation Admin - Access to all transfers in their federation
        if member.role == 'ADMIN_FEDERATION' and member.club and member.club.federation:
            return Transfer.objects.filter(
                from_club__federation=member.club.federation
            )
            
        # Province & Region Admin - Access to transfers in their area
        if member.role == 'ADMIN_PROVINCE' and member.club and member.club.province:
            return Transfer.objects.filter(
                from_club__province=member.club.province
            )
        if member.role == 'ADMIN_REGION' and member.club and member.club.region:
            return Transfer.objects.filter(
                from_club__region=member.club.region
            )
            
        # Local Federation Admin - Access to transfers between their clubs
        if member.role == 'ADMIN_LOCAL_FED' and member.club and member.club.federation:
            return Transfer.objects.filter(
                from_club__federation=member.club.federation
            )
            
        # Club Admin - Only see transfers related to their club
        if member.role == 'CLUB_ADMIN' and member.club:
            return Transfer.objects.filter(
                models.Q(from_club=member.club) | models.Q(to_club=member.club)
            )
            
        # Default - return empty queryset
        return Transfer.objects.none()


class TransferRequestView(TransferRequiredMixin, CreateView):
    """Create a new transfer request"""
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
        member = self.request.user.member_profile
        # Check appropriate roles for initiating transfers
        if member.role in ['ADMIN_SYSTEM', 'ADMIN_COUNTRY', 'ADMIN_FEDERATION',
                          'ADMIN_LOCAL_FED', 'CLUB_ADMIN']:
            with transaction.atomic():
                transfer = form.save(commit=False)
                transfer.from_club = form.cleaned_data['player'].club
                
                # Club admins can only initiate transfers for their own club
                if member.role == 'CLUB_ADMIN' and transfer.from_club != member.club:
                    messages.error(self.request, 
                        _("You can only initiate transfers for players in your club."))
                    return self.form_invalid(form)
                
                transfer.save()
                messages.success(self.request, 
                    _("Transfer request created successfully."))
                return redirect(self.success_url)
        else:
            messages.error(self.request, 
                _("You don't have permission to initiate transfers."))
            return self.form_invalid(form)


class TransferDetailView(TransferRequiredMixin, DetailView):
    """View transfer details and handle approval/rejection"""
    model = Transfer
    template_name = 'membership/transfer/transfer_detail.html'
    context_object_name = 'transfer'
    permission_required = 'membership.view_transfer'

    def post(self, request, *args, **kwargs):
        transfer = self.get_object()
        action = request.POST.get('action')
        
        if action == 'approve' and request.user.has_perm('membership.approve_transfer'):
            try:
                transfer.approve(request.user.member_profile)
                messages.success(request, _("Transfer approved successfully."))
            except Exception as e:
                messages.error(request, str(e))
                
        elif action == 'reject' and request.user.has_perm('membership.reject_transfer'):
            reason = request.POST.get('rejection_reason')
            if not reason:
                messages.error(request, _("Please provide a rejection reason."))
            else:
                try:
                    transfer.reject(request.user.member_profile, reason)
                    messages.success(request, _("Transfer rejected."))
                except Exception as e:
                    messages.error(request, str(e))
        
        return redirect('membership:transfer_detail', pk=transfer.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        transfer = self.get_object()
        
        # Add permissions to context
        context['can_approve'] = user.has_perm('membership.approve_transfer')
        context['can_reject'] = user.has_perm('membership.reject_transfer')
        
        # Add registration history
        context['registration_history'] = PlayerClubRegistration.objects.filter(
            player=transfer.player
        ).order_by('-registration_date')
        
        return context


class TransferApproveView(TransferRequiredMixin, UpdateView):
    """Handle transfer approval"""
    model = Transfer
    template_name = 'membership/transfer/transfer_approve.html'
    fields = []  # No fields needed, just the confirmation
    permission_required = 'membership.approve_transfer'
    
    def get_success_url(self):
        return reverse_lazy('membership:transfer_detail', 
                          kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        try:
            member = self.request.user.member_profile
            # Only allow approval by appropriate roles
            if member.role in ['ADMIN_SYSTEM', 'ADMIN_COUNTRY', 'ADMIN_FEDERATION',
                             'ADMIN_PROVINCE', 'ADMIN_REGION', 'ADMIN_LOCAL_FED']:
                with transaction.atomic():
                    self.object.approve(member)
                    messages.success(self.request, _("Transfer approved successfully."))
                    return redirect(self.get_success_url())
            else:
                messages.error(self.request, _("You don't have permission to approve transfers."))
                return self.form_invalid(form)
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transfer'] = self.object
        return context


class TransferRejectView(TransferRequiredMixin, UpdateView):
    """Handle transfer rejection"""
    model = Transfer
    template_name = 'membership/transfer/transfer_reject.html'
    fields = ['rejection_reason']
    permission_required = 'membership.reject_transfer'
    
    def get_success_url(self):
        return reverse_lazy('membership:transfer_detail', 
                          kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        try:
            member = self.request.user.member_profile
            # Only allow rejection by appropriate roles
            if member.role in ['ADMIN_SYSTEM', 'ADMIN_COUNTRY', 'ADMIN_FEDERATION',
                             'ADMIN_PROVINCE', 'ADMIN_REGION', 'ADMIN_LOCAL_FED']:
                with transaction.atomic():
                    transfer = form.save(commit=False)
                    reason = form.cleaned_data['rejection_reason']
                    transfer.reject(member, reason)
                    messages.success(self.request, _("Transfer rejected successfully."))
                    return redirect(self.get_success_url())
            else:
                messages.error(self.request, _("You don't have permission to reject transfers."))
                return self.form_invalid(form)
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transfer'] = self.object
        return context
