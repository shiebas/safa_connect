from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.db import models, transaction
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
            return member.role in ['ADMIN', 'CLUB_ADMIN']
        except:
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
        if member.role == 'ADMIN':
            return Transfer.objects.all()
            
        # Club admins see transfers related to their club
        club = member.club
        return Transfer.objects.filter(
            models.Q(from_club=club) | models.Q(to_club=club)
        )


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
        with transaction.atomic():
            transfer = form.save(commit=False)
            transfer.from_club = form.cleaned_data['player'].club
            transfer.save()
            
            messages.success(self.request, 
                _("Transfer request created successfully."))
            return redirect(self.success_url)


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
