# membership/views.py - CORRECTED for New SAFA System

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext as _
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.utils.decorators import method_decorator
from django.db import transaction
from django.core.mail import send_mail
from rest_framework import viewsets
from decimal import Decimal
import json
from .serializers import MemberSerializer
from django.db.models import Q, Count, Sum
import csv
from datetime import timedelta
# Import corrected models
from .models import (
    Member, Invoice, InvoiceItem, MemberDocument, RegistrationWorkflow,
    MemberSeasonHistory, SAFASeasonConfig, SAFAFeeStructure, 
    OrganizationSeasonRegistration, Transfer, ClubMemberQuota
)
from geography.models import Club, Province, Region, LocalFootballAssociation, Association
from .forms import (
    MemberForm, ClubForm, MemberRegistrationForm, 
    SeniorMemberRegistrationForm, MemberDocumentForm
)

# Import your models
from .models import (
    Member, Invoice, InvoiceItem, MemberDocument, RegistrationWorkflow,
    Transfer, SAFASeasonConfig, ClubMemberQuota
)
from geography.models import Club, Province, Region, LocalFootballAssociation, Association
from .forms import MemberRegistrationForm, TransferRequestForm, MemberDocumentForm
from .serializers import MemberSerializer


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


# ============================================================================
# MEMBER VIEWS (CORRECTED)
# ============================================================================
class RegistrationSelectorView(TemplateView):
    """View to select registration type"""
    template_name = 'membership/registration_selector.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_season = SAFASeasonConfig.get_active_season()
        context.update({
            'current_season': current_season,
            'member_registration_open': current_season.member_registration_open if current_season else False,
        })
        return context

class MemberRegistrationView(CreateView):
    """Member self-registration view"""
    model = Member
    form_class = MemberRegistrationForm
    template_name = 'membership/member_registration.html'
    success_url = reverse_lazy('membership:registration_success')
    
    def form_valid(self, form):
        current_season = SAFASeasonConfig.get_active_season()
        
        if not current_season:
            messages.error(self.request, _('Registration is currently closed.'))
            return self.form_invalid(form)
        
        if not current_season.member_registration_open:
            messages.error(self.request, _('Member registration period is closed.'))
            return self.form_invalid(form)
        
        try:
            with transaction.atomic():
                member = form.save(commit=False)
                member.current_season = current_season
                member.registration_method = 'SELF'
                member.status = 'PENDING'
                member.save()
                
                # Handle associations for officials
                if member.role == 'OFFICIAL' and 'associations' in form.cleaned_data:
                    member.associations.set(form.cleaned_data['associations'])
                
                # Create invoice
                invoice = Invoice.create_member_invoice(member, current_season)
                
                messages.success(
                    self.request, 
                    _('Registration submitted successfully. Please complete payment to activate your membership.')
                )
                
                return super().form_valid(form)
                
        except ValidationError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f"Registration error: {str(e)}")
            return self.form_invalid(form)


class RegistrationSuccessView(TemplateView):
    """Registration success page"""
    template_name = 'membership/registration_success.html'

class RegistrationStatusView(TemplateView):
    """Check registration status"""
    template_name = 'membership/registration_status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get member by SAFA ID or email if provided
        safa_id = self.request.GET.get('safa_id')
        email = self.request.GET.get('email')
        
        member = None
        if safa_id:
            try:
                member = Member.objects.get(safa_id=safa_id)
            except Member.DoesNotExist:
                pass
        elif email:
            try:
                member = Member.objects.get(email=email)
            except Member.DoesNotExist:
                pass
        
        if member:
            context.update({
                'member': member,
                'workflow': getattr(member, 'workflow', None),
                'outstanding_invoices': member.invoices.filter(
                    status__in=['PENDING', 'OVERDUE', 'PARTIALLY_PAID']
                )
            })
        
        return context

class MemberApproveView(LoginRequiredMixin, View):
    """Approve member registration"""
    
    def post(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can approve members")
        
        member = get_object_or_404(Member, pk=pk)
        
        if member.status != 'PENDING':
            messages.error(request, _('Only pending members can be approved'))
            return redirect('membership:member_detail', pk=pk)
        
        try:
            member.approve_safa_membership(request.user)
            messages.success(request, _('Member approved successfully'))
        except ValidationError as e:
            messages.error(request, str(e))
        
        return redirect('membership:member_detail', pk=pk)

class MemberRejectView(LoginRequiredMixin, View):
    """Reject member registration"""
    
    def post(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can reject members")
        
        member = get_object_or_404(Member, pk=pk)
        reason = request.POST.get('reason', '')
        
        if not reason:
            messages.error(request, _('Rejection reason is required'))
            return redirect('membership:member_detail', pk=pk)
        
        if member.status != 'PENDING':
            messages.error(request, _('Only pending members can be rejected'))
            return redirect('membership:member_detail', pk=pk)
        
        try:
            member.reject_safa_membership(request.user, reason)
            messages.success(request, _('Member rejected successfully'))
        except ValidationError as e:
            messages.error(request, str(e))
        
        return redirect('membership:member_detail', pk=pk)

class MemberDocumentListView(LoginRequiredMixin, ListView):
    """List member documents"""
    model = MemberDocument
    template_name = 'membership/member_document_list.html'
    context_object_name = 'documents'
    
    def get_queryset(self):
        self.member = get_object_or_404(Member, pk=self.kwargs['pk'])
        return self.member.documents.all().order_by('-created')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member'] = self.member
        return context

class MemberHistoryView(LoginRequiredMixin, DetailView):
    """View member's season history"""
    model = Member
    template_name = 'membership/member_history.html'
    context_object_name = 'member'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['season_history'] = self.object.season_history.all().order_by('-season_config__season_year')
        return context

class TransferRequestView(LoginRequiredMixin, CreateView):
    """Request a transfer"""
    model = Transfer
    form_class = TransferRequestForm
    template_name = 'membership/transfer_request.html'
    success_url = reverse_lazy('membership:transfer_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        try:
            kwargs['member'] = self.request.user.member_profile
        except AttributeError:
            kwargs['member'] = None
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _('Transfer request submitted successfully'))
        return super().form_valid(form)


class TransferDetailView(LoginRequiredMixin, DetailView):
    """Transfer detail view"""
    model = Transfer
    template_name = 'membership/transfer_detail.html'
    context_object_name = 'transfer'


class TransferApproveView(LoginRequiredMixin, View):
    """Approve transfer"""
    
    def post(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can approve transfers")
        
        transfer = get_object_or_404(Transfer, pk=pk)
        
        try:
            transfer.approve(request.user)
            messages.success(request, _('Transfer approved successfully'))
        except ValidationError as e:
            messages.error(request, str(e))
        
        return redirect('membership:transfer_detail', pk=pk)


class TransferRejectView(LoginRequiredMixin, View):
    """Reject transfer"""
    
    def post(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can reject transfers")
        
        transfer = get_object_or_404(Transfer, pk=pk)
        reason = request.POST.get('reason', '')
        
        if not reason:
            messages.error(request, _('Rejection reason is required'))
            return redirect('membership:transfer_detail', pk=pk)
        
        try:
            transfer.reject(request.user, reason)
            messages.success(request, _('Transfer rejected successfully'))
        except ValidationError as e:
            messages.error(request, str(e))
        
        return redirect('membership:transfer_detail', pk=pk)


class MemberListView(LoginRequiredMixin, ListView):
    model = Member
    template_name = 'membership/member_list.html'
    context_object_name = 'members'
    paginate_by = 20
    
    def get_queryset(self):
        qs = Member.objects.select_related(
            'current_club', 'current_season', 'province', 'region', 'lfa'
        ).prefetch_related('associations')
        
        user = self.request.user
        
        # Filter based on user permissions
        if user.is_superuser or user.is_staff:
            return qs.order_by('-created')
        
        # Get user's member profile to determine access level
        try:
            member_profile = user.member_profile
            
            # Club admins can only see members from their club
            if hasattr(member_profile, 'current_club') and member_profile.current_club:
                return qs.filter(current_club=member_profile.current_club).order_by('-created')
            
            # LFA admins can see members from their LFA
            if hasattr(member_profile, 'lfa') and member_profile.lfa:
                return qs.filter(lfa=member_profile.lfa).order_by('-created')
                
            # Region admins can see members from their region
            if hasattr(member_profile, 'region') and member_profile.region:
                return qs.filter(region=member_profile.region).order_by('-created')
                
            # Province admins can see members from their province
            if hasattr(member_profile, 'province') and member_profile.province:
                return qs.filter(province=member_profile.province).order_by('-created')
                
        except AttributeError:
            pass
        
        return Member.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_season'] = SAFASeasonConfig.get_active_season()
        context['total_members'] = self.get_queryset().count()
        
        # Add status counts
        qs = self.get_queryset()
        context['status_counts'] = {
            'active': qs.filter(status='ACTIVE').count(),
            'pending': qs.filter(status='PENDING').count(),
            'inactive': qs.filter(status='INACTIVE').count(),
        }
        
        return context


class MemberCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Member
    form_class = MemberForm
    template_name = 'membership/member_form.html'
    success_url = reverse_lazy('membership:member_list')

    def form_valid(self, form):
        try:
            with transaction.atomic():
                member = form.save(commit=False)
                
                # Set current season if not set
                if not member.current_season:
                    member.current_season = SAFASeasonConfig.get_active_season()
                
                # Validate club is within geographic area
                member.clean()
                member.save()
                
                # Handle associations for officials
                if 'associations' in form.cleaned_data:
                    member.associations.set(form.cleaned_data['associations'])
                
                messages.success(self.request, _('Member created successfully.'))
                return super().form_valid(form)
                
        except ValidationError as e:
            form.add_error(None, e.message)
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f"Error creating member: {str(e)}")
            return self.form_invalid(form)


class MemberUpdateView(LoginRequiredMixin, UpdateView):
    model = Member
    form_class = MemberForm
    template_name = 'membership/member_form.html'
    success_url = reverse_lazy('membership:member_list')

    def get_queryset(self):
        """Limit access based on user permissions"""
        qs = super().get_queryset()
        user = self.request.user
        
        if user.is_superuser or user.is_staff:
            return qs
        
        try:
            member_profile = user.member_profile
            
            # Club admins can only edit members from their club
            if hasattr(member_profile, 'current_club') and member_profile.current_club:
                return qs.filter(current_club=member_profile.current_club)
                
        except AttributeError:
            pass
        
        return Member.objects.none()

    def form_valid(self, form):
        try:
            with transaction.atomic():
                member = form.save(commit=False)
                member.clean()
                member.save()
                
                # Handle associations for officials
                if 'associations' in form.cleaned_data:
                    member.associations.set(form.cleaned_data['associations'])
                
                messages.success(self.request, _('Member updated successfully.'))
                return super().form_valid(form)
                
        except ValidationError as e:
            form.add_error(None, e.message)
            return self.form_invalid(form)


class MemberDetailView(LoginRequiredMixin, DetailView):
    model = Member
    template_name = 'membership/member_detail.html'
    context_object_name = 'member'

    def get_queryset(self):
        """Apply same access controls as list view"""
        qs = Member.objects.select_related(
            'current_club', 'current_season', 'province', 'region', 'lfa', 'user'
        ).prefetch_related('associations', 'documents', 'season_history')
        
        user = self.request.user
        
        if user.is_superuser or user.is_staff:
            return qs
        
        try:
            member_profile = user.member_profile
            
            if hasattr(member_profile, 'current_club') and member_profile.current_club:
                return qs.filter(current_club=member_profile.current_club)
                
        except AttributeError:
            pass
        
        return Member.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = self.object
        
        # Get member's workflow status
        try:
            context['workflow'] = member.workflow
        except:
            context['workflow'] = None
        
        # Get member's documents
        context['documents'] = member.documents.all().order_by('document_type')
        
        # Get member's season history
        context['season_history'] = member.season_history.all().order_by('-season_config__season_year')
        
        # Get member's invoices
        context['invoices'] = member.invoices.all().order_by('-created')
        
        # Check if member can be transferred
        context['can_transfer'] = member.status == 'ACTIVE' and member.current_club
        
        return context


# ============================================================================
# CLUB VIEWS (UPDATED FOR NEW SYSTEM)
# ============================================================================

class ClubListView(LoginRequiredMixin, ListView):
    model = Club
    template_name = 'membership/club/club_list.html'
    context_object_name = 'clubs'
    paginate_by = 20

    def get_queryset(self):
        qs = Club.objects.select_related('province', 'region', 'lfa').prefetch_related('current_members')
        
        user = self.request.user
        if user.is_staff:
            return qs.filter(is_active=True).order_by('name')
        
        # Filter based on user's geographic access
        try:
            member_profile = user.member_profile
            
            if hasattr(member_profile, 'lfa') and member_profile.lfa:
                return qs.filter(lfa=member_profile.lfa, is_active=True)
            elif hasattr(member_profile, 'region') and member_profile.region:
                return qs.filter(region=member_profile.region, is_active=True)
            elif hasattr(member_profile, 'province') and member_profile.province:
                return qs.filter(province=member_profile.province, is_active=True)
                
        except AttributeError:
            pass
        
        return Club.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_create_club'] = self.request.user.is_staff
        
        # Add member counts for each club
        current_season = SAFASeasonConfig.get_active_season()
        if current_season:
            for club in context['clubs']:
                club.current_member_count = club.current_members.filter(
                    current_season=current_season,
                    status='ACTIVE'
                ).count()
        
        return context


class ClubDetailView(LoginRequiredMixin, DetailView):
    model = Club
    template_name = 'membership/club/club_detail.html'
    context_object_name = 'club'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        club = self.object
        current_season = SAFASeasonConfig.get_active_season()
        
        if current_season:
            # Get current members
            context['current_members'] = club.current_members.filter(
                current_season=current_season,
                status='ACTIVE'
            ).select_related('user').order_by('last_name', 'first_name')
            
            # Get member counts by role
            members_qs = club.current_members.filter(current_season=current_season, status='ACTIVE')
            context['member_counts'] = {
                'players': members_qs.filter(role='PLAYER').count(),
                'officials': members_qs.filter(role='OFFICIAL').count(),
                'admins': members_qs.filter(role='ADMIN').count(),
            }
            
            # Get club quotas
            try:
                context['quota'] = ClubMemberQuota.objects.get(
                    club=club, 
                    season_config=current_season
                )
            except ClubMemberQuota.DoesNotExist:
                context['quota'] = None
            
            # Get organization registration status
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(club)
            try:
                context['org_registration'] = OrganizationSeasonRegistration.objects.get(
                    season_config=current_season,
                    content_type=content_type,
                    object_id=club.pk
                )
            except OrganizationSeasonRegistration.DoesNotExist:
                context['org_registration'] = None
        
        return context


# ============================================================================
# MEMBER TRANSFER VIEWS
# ============================================================================

class TransferCreateView(LoginRequiredMixin, CreateView):
    model = Transfer
    template_name = 'membership/transfer_form.html'
    fields = ['member', 'to_club', 'reason']
    success_url = reverse_lazy('membership:transfer_list')
    
    def form_valid(self, form):
        transfer = form.save(commit=False)
        transfer.from_club = transfer.member.current_club
        
        try:
            transfer.clean()
            transfer.save()
            messages.success(self.request, _('Transfer request submitted successfully.'))
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e.message)
            return self.form_invalid(form)


class TransferListView(LoginRequiredMixin, ListView):
    model = Transfer
    template_name = 'membership/transfer_list.html'
    context_object_name = 'transfers'
    paginate_by = 20
    
    def get_queryset(self):
        qs = Transfer.objects.select_related(
            'member', 'from_club', 'to_club', 'approved_by'
        ).order_by('-request_date')
        
        # Filter based on user permissions
        user = self.request.user
        if not (user.is_superuser or user.is_staff):
            try:
                member_profile = user.member_profile
                if hasattr(member_profile, 'current_club') and member_profile.current_club:
                    # Club admins see transfers involving their club
                    qs = qs.filter(
                        models.Q(from_club=member_profile.current_club) | 
                        models.Q(to_club=member_profile.current_club)
                    )
            except AttributeError:
                return Transfer.objects.none()
        
        return qs


@login_required
@staff_member_required
def approve_transfer(request, transfer_id):
    """Approve a member transfer"""
    transfer = get_object_or_404(Transfer, pk=transfer_id)
    
    if transfer.status != 'PENDING':
        messages.error(request, _('Only pending transfers can be approved.'))
        return redirect('membership:transfer_list')
    
    try:
        transfer.approve(request.user)
        messages.success(request, _('Transfer approved successfully.'))
    except ValidationError as e:
        messages.error(request, str(e))
    
    return redirect('membership:transfer_list')


@login_required
@staff_member_required
def reject_transfer(request, transfer_id):
    """Reject a member transfer"""
    transfer = get_object_or_404(Transfer, pk=transfer_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        if not reason:
            messages.error(request, _('Rejection reason is required.'))
            return redirect('membership:transfer_list')
        
        try:
            transfer.reject(request.user, reason)
            messages.success(request, _('Transfer rejected.'))
        except ValidationError as e:
            messages.error(request, str(e))
    
    return redirect('membership:transfer_list')


# ============================================================================
# INVOICE AND PAYMENT VIEWS
# ============================================================================

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'membership/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):
        qs = Invoice.objects.select_related(
            'member', 'season_config', 'content_type'
        ).order_by('-created')
        
        user = self.request.user
        if not (user.is_superuser or user.is_staff):
            # Members can only see their own invoices
            try:
                member_profile = user.member_profile
                return qs.filter(member=member_profile)
            except AttributeError:
                return Invoice.objects.none()
        
        return qs

class InvoicePDFView(LoginRequiredMixin, View):
    """Generate PDF invoice"""
    
    def get(self, request, uuid):
        invoice = get_object_or_404(Invoice, uuid=uuid)
        
        # Check permissions
        if not (request.user.is_staff or (
            invoice.member and invoice.member.user == request.user
        )):
            raise PermissionDenied("You don't have permission to view this invoice")
        
        # Here you would generate PDF - for now return simple response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
        
        # TODO: Implement PDF generation
        response.write(b'PDF generation not implemented yet')
        return response

class InvoicePaymentView(LoginRequiredMixin, TemplateView):
    """Invoice payment page"""
    template_name = 'membership/invoice_payment.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice = get_object_or_404(Invoice, uuid=kwargs['uuid'])
        
        # Check permissions
        if not (self.request.user.is_staff or (
            invoice.member and invoice.member.user == self.request.user
        )):
            raise PermissionDenied("You don't have permission to view this invoice")
        
        context['invoice'] = invoice
        return context


class MarkInvoicePaidView(LoginRequiredMixin, View):
    """Mark invoice as paid"""
    
    def post(self, request, uuid):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can mark invoices as paid")
        
        invoice = get_object_or_404(Invoice, uuid=uuid)
        payment_method = request.POST.get('payment_method', 'MANUAL')
        payment_reference = request.POST.get('payment_reference', '')
        
        try:
            invoice.mark_as_paid(
                payment_method=payment_method,
                payment_reference=payment_reference
            )
            messages.success(request, _('Invoice marked as paid successfully'))
        except Exception as e:
            messages.error(request, str(e))
        
        return redirect('membership:invoice_detail', uuid=uuid)

class ProcessPaymentView(LoginRequiredMixin, View):
    """Process payment"""
    
    def post(self, request):
        # TODO: Implement payment processing
        messages.info(request, _('Payment processing not implemented yet'))
        return redirect('membership:payment_return')


class PaymentNotifyView(View):
    """Payment notification webhook"""
    
    def post(self, request):
        # TODO: Implement payment notification handling
        return JsonResponse({'status': 'received'})



class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'membership/invoice_detail.html'
    context_object_name = 'invoice'
    
    def get_queryset(self):
        qs = Invoice.objects.select_related(
            'member', 'season_config', 'content_type'
        ).prefetch_related('items')
        
        user = self.request.user
        if not (user.is_superuser or user.is_staff):
            try:
                member_profile = user.member_profile
                return qs.filter(member=member_profile)
            except AttributeError:
                return Invoice.objects.none()
        
        return qs


@login_required
def create_member_invoice(request, member_id):
    """Create invoice for member registration"""
    if not request.user.is_staff:
        raise PermissionDenied("Only staff can create invoices")
    
    member = get_object_or_404(Member, pk=member_id)
    current_season = SAFASeasonConfig.get_active_season()
    
    if not current_season:
        messages.error(request, _('No active season configuration found.'))
        return redirect('membership:member_detail', pk=member_id)
    
    # Check if invoice already exists
    existing_invoice = Invoice.objects.filter(
        member=member,
        season_config=current_season,
        status__in=['PENDING', 'PARTIALLY_PAID']
    ).first()
    
    if existing_invoice:
        messages.warning(request, _('Member already has a pending invoice.'))
        return redirect('membership:invoice_detail', pk=existing_invoice.pk)
    
    try:
        invoice = Invoice.create_member_invoice(member, current_season)
        messages.success(request, _('Invoice created successfully.'))
        return redirect('membership:invoice_detail', pk=invoice.pk)
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect('membership:member_detail', pk=member_id)


# ============================================================================
# MEMBER DOCUMENT VIEWS
# ============================================================================

class DocumentUploadView(LoginRequiredMixin, CreateView):
    model = MemberDocument
    form_class = MemberDocumentForm
    template_name = 'membership/document_upload.html'
    
    def get_success_url(self):
        return reverse('membership:member_detail', kwargs={'pk': self.object.member.pk})
    
    def form_valid(self, form):
        form.instance.member_id = self.kwargs['member_id']
        messages.success(self.request, _('Document uploaded successfully.'))
        return super().form_valid(form)

class DocumentListView(LoginRequiredMixin, ListView):
    """List all documents"""
    model = MemberDocument
    template_name = 'membership/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20
    
    def get_queryset(self):
        if not self.request.user.is_staff:
            return MemberDocument.objects.none()
        
        qs = MemberDocument.objects.select_related('member', 'verified_by').order_by('-created')
        
        # Apply filters
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(verification_status=status)
        
        return qs


class DocumentUploadView(LoginRequiredMixin, CreateView):
    """Upload document"""
    model = MemberDocument
    form_class = MemberDocumentForm
    template_name = 'membership/document_upload.html'
    
    def get_success_url(self):
        member_id = self.request.GET.get('member_id')
        if member_id:
            return reverse('membership:member_detail', kwargs={'pk': member_id})
        return reverse('membership:document_list')
    
    def form_valid(self, form):
        member_id = self.request.GET.get('member_id')
        if not member_id:
            messages.error(self.request, _('Member ID is required'))
            return self.form_invalid(form)
        
        try:
            member = Member.objects.get(pk=member_id)
            form.instance.member = member
            messages.success(self.request, _('Document uploaded successfully'))
            return super().form_valid(form)
        except Member.DoesNotExist:
            messages.error(self.request, _('Member not found'))
            return self.form_invalid(form)


class DocumentDetailView(LoginRequiredMixin, DetailView):
    """Document detail view"""
    model = MemberDocument
    template_name = 'membership/document_detail.html'
    context_object_name = 'document'


class DocumentApproveView(LoginRequiredMixin, View):
    """Approve document"""
    
    def post(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can approve documents")
        
        document = get_object_or_404(MemberDocument, pk=pk)
        document.approve(request.user)
        messages.success(request, _('Document approved successfully'))
        
        return redirect('membership:document_detail', pk=pk)


class DocumentRejectView(LoginRequiredMixin, View):
    """Reject document"""
    
    def post(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can reject documents")
        
        document = get_object_or_404(MemberDocument, pk=pk)
        notes = request.POST.get('notes', '')
        
        if not notes:
            messages.error(request, _('Rejection notes are required'))
            return redirect('membership:document_detail', pk=pk)
        
        document.reject(request.user, notes)
        messages.success(request, _('Document rejected successfully'))
        
        return redirect('membership:document_detail', pk=pk)

@login_required
@staff_member_required
def approve_document(request, document_id):
    """Approve a member document"""
    document = get_object_or_404(MemberDocument, pk=document_id)
    document.approve(request.user)
    messages.success(request, _('Document approved.'))
    return redirect('membership:member_detail', pk=document.member.pk)

@login_required
@staff_member_required
def reject_document(request, document_id):
    """Reject a member document"""
    document = get_object_or_404(MemberDocument, pk=document_id)
    
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        document.reject(request.user, notes)
        messages.success(request, _('Document rejected.'))
    
    return redirect('membership:member_detail', pk=document.member.pk)


# ============================================================================
# REGISTRATION WORKFLOW VIEWS
# ============================================================================

class RegistrationSelectorView(TemplateView):
    template_name = 'membership/registration_selector.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_season = SAFASeasonConfig.get_active_season()
        context['current_season'] = current_season
        context['member_registration_open'] = current_season.member_registration_open if current_season else False
        return context


class MemberRegistrationView(CreateView):
    """Member self-registration view"""
    model = Member
    form_class = SeniorMemberRegistrationForm
    template_name = 'membership/member_registration.html'
    
    def get_success_url(self):
        return reverse('membership:registration_success')
    
    def form_valid(self, form):
        current_season = SAFASeasonConfig.get_active_season()
        
        if not current_season:
            messages.error(self.request, _('Registration is currently closed.'))
            return self.form_invalid(form)
        
        if not current_season.member_registration_open:
            messages.error(self.request, _('Member registration period is closed.'))
            return self.form_invalid(form)
        
        try:
            with transaction.atomic():
                member = form.save(commit=False)
                member.current_season = current_season
                member.registration_method = 'SELF'
                member.status = 'PENDING'
                
                # Validate member can register
                member.clean()
                member.save()
                
                # Handle associations for officials
                if 'associations' in form.cleaned_data:
                    member.associations.set(form.cleaned_data['associations'])
                
                # Create invoice
                invoice = Invoice.create_member_invoice(member, current_season)
                
                messages.success(
                    self.request, 
                    _('Registration submitted successfully. Please complete payment to activate your membership.')
                )
                
                # Send registration confirmation email
                self.send_registration_email(member, invoice)
                
                return super().form_valid(form)
                
        except ValidationError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f"Registration error: {str(e)}")
            return self.form_invalid(form)
    
    def send_registration_email(self, member, invoice):
        """Send registration confirmation email"""
        try:
            send_mail(
                subject=_('SAFA Registration Confirmation'),
                message=_(
                    f'Dear {member.get_full_name()},\n\n'
                    f'Your SAFA registration has been submitted successfully. '
                    f'Your SAFA ID is: {member.safa_id}\n\n'
                    f'Please complete payment of R{invoice.total_amount} to activate your membership.\n\n'
                    f'Invoice Number: {invoice.invoice_number}\n'
                    f'Due Date: {invoice.due_date}\n\n'
                    f'Thank you,\nSAFA Registration Team'
                ),
                from_email='noreply@safa.org.za',
                recipient_list=[member.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send registration email: {e}")


class RegistrationSuccessView(TemplateView):
    template_name = 'membership/registration_success.html'


# ============================================================================
# API ENDPOINTS FOR DYNAMIC FORMS
# ============================================================================

def get_regions_by_province(request, province_id):
    """Get regions for a province"""
    regions = Region.objects.filter(
        province_id=province_id, 
        is_active=True
    ).values('id', 'name').order_by('name')
    return JsonResponse(list(regions), safe=False)


def get_lfas_by_region(request, region_id):
    """Get LFAs for a region"""
    lfas = LocalFootballAssociation.objects.filter(
        region_id=region_id, 
        is_active=True
    ).values('id', 'name').order_by('name')
    return JsonResponse(list(lfas), safe=False)


def get_clubs_by_geography(request):
    """Get clubs filtered by geographic area"""
    province_id = request.GET.get('province_id')
    region_id = request.GET.get('region_id')
    lfa_id = request.GET.get('lfa_id')
    
    clubs_qs = Club.objects.filter(is_active=True)
    
    if lfa_id:
        clubs_qs = clubs_qs.filter(lfa_id=lfa_id)
    elif region_id:
        clubs_qs = clubs_qs.filter(region_id=region_id)
    elif province_id:
        clubs_qs = clubs_qs.filter(province_id=province_id)
    
    clubs = clubs_qs.values('id', 'name').order_by('name')
    return JsonResponse(list(clubs), safe=False)


def get_associations_by_type(request):
    """Get associations by type for officials"""
    association_type = request.GET.get('type', 'REFEREE')
    associations = Association.objects.filter(
        association_type=association_type,
        is_active=True
    ).values('id', 'name').order_by('name')
    return JsonResponse(list(associations), safe=False)


def check_email_availability(request):
    """Check if email is available for registration"""
    email = request.GET.get('email', '').strip().lower()
    if not email:
        return JsonResponse({'is_available': False, 'message': 'Email is required'})
    
    is_taken = Member.objects.filter(email__iexact=email).exists()
    return JsonResponse({
        'is_available': not is_taken,
        'message': 'Email is already registered' if is_taken else 'Email is available'
    })


def check_id_number_availability(request):
    """Check if ID number is available for registration"""
    id_number = request.GET.get('id_number', '').strip()
    if not id_number:
        return JsonResponse({'is_available': False, 'message': 'ID number is required'})
    
    is_taken = Member.objects.filter(id_number=id_number).exists()
    return JsonResponse({
        'is_available': not is_taken,
        'message': 'ID number is already registered' if is_taken else 'ID number is available'
    })


# ============================================================================
# PAYMENT PROCESSING VIEWS
# ============================================================================

class PaymentReturnView(LoginRequiredMixin, View):
    """Handle successful payment returns"""
    
    def get(self, request, *args, **kwargs):
        payment_ref = request.GET.get('reference', '')
        invoice_id = request.GET.get('invoice_id', '')
        
        if invoice_id:
            try:
                invoice = Invoice.objects.get(uuid=invoice_id)
                # Mark invoice as paid (implement actual payment verification)
                invoice.mark_as_paid(
                    payment_method='CARD',
                    payment_reference=payment_ref
                )
                messages.success(request, _('Payment processed successfully.'))
                
                if invoice.member:
                    return redirect('membership:member_detail', pk=invoice.member.pk)
                else:
                    return redirect('membership:invoice_list')
                    
            except Invoice.DoesNotExist:
                messages.error(request, _('Invoice not found.'))
        
        return redirect('membership:invoice_list')


class PaymentCancelView(LoginRequiredMixin, TemplateView):
    """Handle cancelled payments"""
    template_name = 'membership/payment_cancel.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Payment Cancelled")
        context['message'] = _("Your payment was cancelled. Please try again or contact support.")
        return context


# ============================================================================
# REPORTING VIEWS
# ============================================================================

class MembershipReportView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = 'membership/reports/membership_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_season = SAFASeasonConfig.get_active_season()
        
        if current_season:
            members_qs = Member.objects.filter(current_season=current_season)
            
            context.update({
                'current_season': current_season,
                'total_members': members_qs.count(),
                'active_members': members_qs.filter(status='ACTIVE').count(),
                'pending_members': members_qs.filter(status='PENDING').count(),
                'members_by_role': {
                    'players': members_qs.filter(role='PLAYER').count(),
                    'officials': members_qs.filter(role='OFFICIAL').count(),
                    'admins': members_qs.filter(role='ADMIN').count(),
                },
                'members_by_province': members_qs.values(
                    'province__name'
                ).annotate(
                    count=models.Count('id')
                ).order_by('-count')[:10]
            })
        
        return context


# ============================================================================
# API VIEWSETS
# ============================================================================

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    
    def get_queryset(self):
        """Apply same access controls as views"""
        qs = super().get_queryset()
        user = self.request.user
        
        if user.is_superuser or user.is_staff:
            return qs
        
        try:
            member_profile = user.member_profile
            if hasattr(member_profile, 'current_club') and member_profile.current_club:
                return qs.filter(current_club=member_profile.current_club)
        except AttributeError:
            pass
        
        return Member.objects.none()


# ============================================================================
# LEGACY COMPATIBILITY (Remove after migration)
# ============================================================================

# These views are kept for backward compatibility during migration
# TODO: Remove after full migration to new system

@login_required
def legacy_membership_application(request):
    """Legacy membership application - redirect to new system"""
    messages.info(request, _('Please use the new registration system.'))
    return redirect('membership:registration_selector')


def verify_view(request):
    """Legacy verify view"""
    return render(request, 'membership/verify.html')


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def send_payment_reminder(request, invoice_id):
    """Send payment reminder for invoice"""
    if not request.user.is_staff:
        raise PermissionDenied("Only staff can send payment reminders")
    
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    if invoice.status not in ['PENDING', 'OVERDUE', 'PARTIALLY_PAID']:
        messages.error(request, _('Payment reminder can only be sent for unpaid invoices.'))
        return redirect('membership:invoice_detail', pk=invoice_id)
    
    try:
        recipient_email = None
        recipient_name = None
        
        if invoice.member:
            recipient_email = invoice.member.email
            recipient_name = invoice.member.get_full_name()
        elif invoice.organization:
            # Get organization admin email
            org_name = getattr(invoice.organization, 'name', str(invoice.organization))
            recipient_name = org_name
            
            # Try to find admin emails based on organization type
            if hasattr(invoice.organization, 'current_members'):
                admin_emails = invoice.organization.current_members.filter(
                    role='ADMIN',
                    status='ACTIVE'
                ).values_list('email', flat=True)
                if admin_emails:
                    recipient_email = list(admin_emails)[0]  # Use first admin email
        
        if recipient_email and recipient_name:
            subject = _('Payment Reminder - Invoice #{0}').format(invoice.invoice_number)
            message = _(
                'Dear {0},\n\n'
                'This is a reminder that your invoice #{1} for R{2:.2f} is outstanding.\n\n'
                'Invoice Details:\n'
                '- Invoice Number: {1}\n'
                '- Amount Due: R{3:.2f}\n'
                '- Due Date: {4}\n'
                '- Status: {5}\n\n'
                'Please log in to the SAFA system to view and pay this invoice.\n\n'
                'If you have already made payment, please ignore this reminder.\n\n'
                'Thank you,\nSAFA Finance Team'
            ).format(
                recipient_name,
                invoice.invoice_number,
                invoice.total_amount,
                invoice.outstanding_amount,
                invoice.due_date,
                invoice.get_status_display()
            )
            
            success = send_mail(
                subject=subject,
                message=message,
                from_email='finance@safa.org.za',
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            
            if success:
                messages.success(request, _('Payment reminder sent successfully to {0}').format(recipient_name))
            else:
                messages.error(request, _('Failed to send payment reminder.'))
        else:
            messages.error(request, _('No valid email address found for this invoice.'))
            
    except Exception as e:
        messages.error(request, _('Error sending payment reminder: {0}').format(str(e)))
    
    return redirect('membership:invoice_detail', pk=invoice_id)


@login_required
@staff_member_required
def bulk_invoice_generation(request):
    """Generate invoices for all members or organizations for the current season"""
    current_season = SAFASeasonConfig.get_active_season()
    
    if not current_season:
        messages.error(request, _('No active season configuration found.'))
        return redirect('membership:member_list')
    
    if request.method == 'POST':
        invoice_type = request.POST.get('invoice_type')
        
        try:
            with transaction.atomic():
                created_count = 0
                
                if invoice_type == 'member_renewals':
                    # Generate invoices for all active members without current season invoice
                    members = Member.objects.filter(
                        status='ACTIVE'
                    ).exclude(
                        invoices__season_config=current_season,
                        invoices__status__in=['PENDING', 'PAID', 'PARTIALLY_PAID']
                    )
                    
                    for member in members:
                        try:
                            Invoice.create_member_invoice(member, current_season)
                            created_count += 1
                        except ValidationError:
                            continue  # Skip members that can't have invoices created
                
                elif invoice_type == 'organization_renewals':
                    # Generate invoices for all organizations
                    from django.contrib.contenttypes.models import ContentType
                    
                    # Get all club content types that need invoices
                    club_ct = ContentType.objects.get_for_model(Club)
                    clubs_needing_invoices = Club.objects.filter(
                        is_active=True
                    ).exclude(
                        organization_registrations__season_config=current_season
                    )
                    
                    for club in clubs_needing_invoices:
                        # Create organization registration
                        org_reg, created = OrganizationSeasonRegistration.objects.get_or_create(
                            season_config=current_season,
                            content_type=club_ct,
                            object_id=club.pk,
                            defaults={
                                'registered_by': request.user,
                                'status': 'PENDING'
                            }
                        )
                        
                        if created:
                            # Create invoice for organization
                            fee_structure = SAFAFeeStructure.objects.filter(
                                season_config=current_season,
                                entity_type='CLUB'
                            ).first()
                            
                            if fee_structure:
                                invoice = Invoice.objects.create(
                                    season_config=current_season,
                                    content_type=club_ct,
                                    object_id=club.pk,
                                    invoice_type='ORGANIZATION_MEMBERSHIP',
                                    subtotal=fee_structure.annual_fee,
                                    vat_rate=current_season.vat_rate,
                                    issued_by=request.user
                                )
                                
                                InvoiceItem.objects.create(
                                    invoice=invoice,
                                    description=f'Club Membership Fee - {current_season.season_year}',
                                    quantity=1,
                                    unit_price=fee_structure.annual_fee
                                )
                                
                                org_reg.invoice = invoice
                                org_reg.save()
                                created_count += 1
                
                messages.success(request, _('Generated {0} invoices successfully.').format(created_count))
                
        except Exception as e:
            messages.error(request, _('Error generating invoices: {0}').format(str(e)))
    
    context = {
        'current_season': current_season,
        'member_count': Member.objects.filter(status='ACTIVE').count(),
        'club_count': Club.objects.filter(is_active=True).count(),
    }
    
    return render(request, 'membership/bulk_invoice_generation.html', context)


@login_required
def member_search(request):
    """AJAX endpoint for member search"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search members by name, email, or SAFA ID
    members = Member.objects.filter(
        models.Q(first_name__icontains=query) |
        models.Q(last_name__icontains=query) |
        models.Q(email__icontains=query) |
        models.Q(safa_id__icontains=query)
    ).select_related('current_club')[:10]
    
    results = []
    for member in members:
        results.append({
            'id': member.id,
            'text': f"{member.get_full_name()} ({member.safa_id})",
            'email': member.email,
            'club': member.current_club.name if member.current_club else 'No Club',
            'status': member.get_status_display()
        })
    
    return JsonResponse({'results': results})


@login_required
def club_search(request):
    """AJAX endpoint for club search"""
    query = request.GET.get('q', '').strip()
    province_id = request.GET.get('province_id')
    region_id = request.GET.get('region_id')
    lfa_id = request.GET.get('lfa_id')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    clubs_qs = Club.objects.filter(
        name__icontains=query,
        is_active=True
    )
    
    # Apply geographic filters
    if lfa_id:
        clubs_qs = clubs_qs.filter(lfa_id=lfa_id)
    elif region_id:
        clubs_qs = clubs_qs.filter(region_id=region_id)
    elif province_id:
        clubs_qs = clubs_qs.filter(province_id=province_id)
    
    clubs = clubs_qs.select_related('province', 'region', 'lfa')[:10]
    
    results = []
    for club in clubs:
        location_parts = []
        if club.lfa:
            location_parts.append(club.lfa.name)
        if club.region:
            location_parts.append(club.region.name)
        if club.province:
            location_parts.append(club.province.name)
        
        results.append({
            'id': club.id,
            'text': club.name,
            'location': ' - '.join(location_parts) if location_parts else 'Unknown Location'
        })
    
    return JsonResponse({'results': results})


# ============================================================================
# SEASON MANAGEMENT VIEWS
# ============================================================================

class SeasonConfigListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = SAFASeasonConfig
    template_name = 'membership/season/season_list.html'
    context_object_name = 'seasons'
    paginate_by = 10


class SeasonConfigDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = SAFASeasonConfig
    template_name = 'membership/season/season_detail.html'
    context_object_name = 'season'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        season = self.object
        
        # Get season statistics
        context.update({
            'total_members': season.current_season_members.count(),
            'active_members': season.current_season_members.filter(status='ACTIVE').count(),
            'pending_members': season.current_season_members.filter(status='PENDING').count(),
            'total_invoices': season.invoices.count(),
            'paid_invoices': season.invoices.filter(status='PAID').count(),
            'pending_invoices': season.invoices.filter(status='PENDING').count(),
            'overdue_invoices': season.invoices.filter(status='OVERDUE').count(),
            'fee_structures': season.fee_structures.all().order_by('entity_type'),
            'organization_registrations': season.organization_registrations.all().count(),
        })
        
        return context


@login_required
@staff_member_required
def activate_season(request, season_id):
    """Activate a season configuration"""
    season = get_object_or_404(SAFASeasonConfig, pk=season_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Deactivate all other seasons
                SAFASeasonConfig.objects.exclude(pk=season.pk).update(is_active=False)
                
                # Activate this season
                season.is_active = True
                season.save()
                
                messages.success(request, _('Season {0} activated successfully.').format(season.season_year))
                
        except Exception as e:
            messages.error(request, _('Error activating season: {0}').format(str(e)))
    
    return redirect('membership:season_detail', pk=season_id)

class SeasonListView(LoginRequiredMixin, ListView):
    """List seasons"""
    model = SAFASeasonConfig
    template_name = 'membership/season_list.html'
    context_object_name = 'seasons'
    
    def get_queryset(self):
        return SAFASeasonConfig.objects.all().order_by('-season_year')


class SeasonCreateView(LoginRequiredMixin, CreateView):
    """Create season"""
    model = SAFASeasonConfig
    template_name = 'membership/season_form.html'
    fields = [
        'season_year', 'season_start_date', 'season_end_date',
        'organization_registration_start', 'organization_registration_end',
        'member_registration_start', 'member_registration_end',
        'vat_rate', 'payment_due_days', 'is_renewal_season'
    ]
    success_url = reverse_lazy('membership:season_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, _('Season created successfully'))
        return super().form_valid(form)


class SeasonDetailView(LoginRequiredMixin, DetailView):
    """Season detail view"""
    model = SAFASeasonConfig
    template_name = 'membership/season_detail.html'
    context_object_name = 'season'


class SeasonActivateView(LoginRequiredMixin, View):
    """Activate season"""
    
    def post(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can activate seasons")
        
        season = get_object_or_404(SAFASeasonConfig, pk=pk)
        
        try:
            with transaction.atomic():
                # Deactivate all other seasons
                SAFASeasonConfig.objects.exclude(pk=season.pk).update(is_active=False)
                # Activate this season
                season.is_active = True
                season.save()
                
                messages.success(request, f'Season {season.season_year} activated successfully')
        except Exception as e:
            messages.error(request, f'Error activating season: {str(e)}')
        
        return redirect('membership:season_detail', pk=pk)


class SeasonFeeStructureView(LoginRequiredMixin, TemplateView):
    """Season fee structure view"""
    template_name = 'membership/season_fee_structure.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        season = get_object_or_404(SAFASeasonConfig, pk=kwargs['pk'])
        context.update({
            'season': season,
            'fee_structures': season.fee_structures.all().order_by('entity_type')
        })
        return context

# ============================================================================
# ADVANCED FILTERING AND EXPORT VIEWS
# ============================================================================

class MemberFilterView(LoginRequiredMixin, ListView):
    model = Member
    template_name = 'membership/member_filter.html'
    context_object_name = 'members'
    paginate_by = 50
    
    def get_queryset(self):
        qs = Member.objects.select_related(
            'current_club', 'current_season', 'province', 'region', 'lfa'
        ).prefetch_related('associations')
        
        # Apply filters from GET parameters
        status = self.request.GET.get('status')
        role = self.request.GET.get('role')
        province_id = self.request.GET.get('province')
        region_id = self.request.GET.get('region')
        lfa_id = self.request.GET.get('lfa')
        club_id = self.request.GET.get('club')
        season_id = self.request.GET.get('season')
        
        if status:
            qs = qs.filter(status=status)
        if role:
            qs = qs.filter(role=role)
        if province_id:
            qs = qs.filter(province_id=province_id)
        if region_id:
            qs = qs.filter(region_id=region_id)
        if lfa_id:
            qs = qs.filter(lfa_id=lfa_id)
        if club_id:
            qs = qs.filter(current_club_id=club_id)
        if season_id:
            qs = qs.filter(current_season_id=season_id)
        
        return qs.order_by('last_name', 'first_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter options
        context.update({
            'status_choices': Member.MEMBERSHIP_STATUS,
            'role_choices': Member.MEMBER_ROLES,
            'provinces': Province.objects.filter(is_active=True).order_by('name'),
            'seasons': SAFASeasonConfig.objects.all().order_by('-season_year'),
            'current_filters': {
                'status': self.request.GET.get('status', ''),
                'role': self.request.GET.get('role', ''),
                'province': self.request.GET.get('province', ''),
                'region': self.request.GET.get('region', ''),
                'lfa': self.request.GET.get('lfa', ''),
                'club': self.request.GET.get('club', ''),
                'season': self.request.GET.get('season', ''),
            }
        })
        
        return context


@login_required
@staff_member_required
def export_members_csv(request):
    """Export filtered members to CSV"""
    import csv
    from django.http import HttpResponse
    
    # Apply same filtering as MemberFilterView
    qs = Member.objects.select_related(
        'current_club', 'current_season', 'province', 'region', 'lfa'
    )
    
    # Apply filters (same logic as MemberFilterView)
    status = request.GET.get('status')
    role = request.GET.get('role')
    province_id = request.GET.get('province')
    region_id = request.GET.get('region')
    lfa_id = request.GET.get('lfa')
    club_id = request.GET.get('club')
    season_id = request.GET.get('season')
    
    if status:
        qs = qs.filter(status=status)
    if role:
        qs = qs.filter(role=role)
    if province_id:
        qs = qs.filter(province_id=province_id)
    if region_id:
        qs = qs.filter(region_id=region_id)
    if lfa_id:
        qs = qs.filter(lfa_id=lfa_id)
    if club_id:
        qs = qs.filter(current_club_id=club_id)
    if season_id:
        qs = qs.filter(current_season_id=season_id)
    
    # Create HTTP response with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="safa_members_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'SAFA ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Date of Birth',
        'Gender', 'ID Number', 'Role', 'Status', 'Current Club', 'Province',
        'Region', 'LFA', 'Registration Date', 'Season'
    ])
    
    # Write member data
    for member in qs.order_by('last_name', 'first_name'):
        writer.writerow([
            member.safa_id,
            member.first_name,
            member.last_name,
            member.email,
            member.phone_number,
            member.date_of_birth.strftime('%Y-%m-%d') if member.date_of_birth else '',
            member.get_gender_display(),
            member.id_number,
            member.get_role_display(),
            member.get_status_display(),
            member.current_club.name if member.current_club else '',
            member.province.name if member.province else '',
            member.region.name if member.region else '',
            member.lfa.name if member.lfa else '',
            member.created.strftime('%Y-%m-%d %H:%M') if member.created else '',
            f"Season {member.current_season.season_year}" if member.current_season else ''
        ])
    
    return response


# ============================================================================
# DASHBOARD AND ANALYTICS VIEWS
# ============================================================================

class MembershipDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'membership/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_season = SAFASeasonConfig.get_active_season()
        
        if current_season:
            # Basic statistics
            members_qs = Member.objects.filter(current_season=current_season)
            
            context.update({
                'current_season': current_season,
                'total_members': members_qs.count(),
                'active_members': members_qs.filter(status='ACTIVE').count(),
                'pending_members': members_qs.filter(status='PENDING').count(),
                'rejected_members': members_qs.filter(status='REJECTED').count(),
                
                # Role breakdown
                'players_count': members_qs.filter(role='PLAYER').count(),
                'officials_count': members_qs.filter(role='OFFICIAL').count(),
                'admins_count': members_qs.filter(role='ADMIN').count(),
                
                # Recent registrations
                'recent_members': members_qs.order_by('-created')[:10],
                
                # Invoice statistics
                'total_invoices': Invoice.objects.filter(season_config=current_season).count(),
                'paid_invoices': Invoice.objects.filter(season_config=current_season, status='PAID').count(),
                'overdue_invoices': Invoice.objects.filter(season_config=current_season, status='OVERDUE').count(),
                
                # Club statistics
                'total_clubs': Club.objects.filter(is_active=True).count(),
                'clubs_with_members': Club.objects.filter(
                    current_members__current_season=current_season,
                    current_members__status='ACTIVE'
                ).distinct().count(),
            })
            
            # Registration trends (last 30 days)
            from datetime import timedelta
            thirty_days_ago = timezone.now() - timedelta(days=30)
            daily_registrations = members_qs.filter(
                created__gte=thirty_days_ago
            ).extra(
                select={'day': 'date(created)'}
            ).values('day').annotate(
                count=models.Count('id')
            ).order_by('day')
            
            context['daily_registrations'] = list(daily_registrations)
        
        return context


# ============================================================================
# WORKFLOW MANAGEMENT VIEWS
# ============================================================================

class WorkflowListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = RegistrationWorkflow
    template_name = 'membership/workflow_list.html'
    context_object_name = 'workflows'
    paginate_by = 20
    
    def get_queryset(self):
        return RegistrationWorkflow.objects.select_related(
            'member', 'member__current_club'
        ).exclude(
            current_step='COMPLETE'
        ).order_by('completion_percentage', '-created')


@login_required
@staff_member_required
def update_workflow_step(request, workflow_id, step):
    """Update a specific workflow step"""
    workflow = get_object_or_404(RegistrationWorkflow, pk=workflow_id)
    
    if step not in dict(RegistrationWorkflow.WORKFLOW_STEPS):
        messages.error(request, _('Invalid workflow step.'))
        return redirect('membership:workflow_list')
    
    # Update the step status
    step_field = f"{step.lower()}_status"
    if hasattr(workflow, step_field):
        setattr(workflow, step_field, 'COMPLETED')
        workflow.update_progress()
        messages.success(request, _('Workflow step updated successfully.'))
    else:
        messages.error(request, _('Invalid workflow step field.'))
    
    return redirect('membership:member_detail', pk=workflow.member.pk)


class ReportsIndexView(LoginRequiredMixin, TemplateView):
    """Reports index page"""
    template_name = 'membership/reports/index.html'


class MemberReportView(LoginRequiredMixin, TemplateView):
    """Member reports"""
    template_name = 'membership/reports/member_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_season = SAFASeasonConfig.get_active_season()
        
        if current_season:
            members_qs = Member.objects.filter(current_season=current_season)
            context.update({
                'current_season': current_season,
                'total_members': members_qs.count(),
                'active_members': members_qs.filter(status='ACTIVE').count(),
                'pending_members': members_qs.filter(status='PENDING').count(),
                'members_by_role': {
                    'players': members_qs.filter(role='PLAYER').count(),
                    'officials': members_qs.filter(role='OFFICIAL').count(),
                    'admins': members_qs.filter(role='ADMIN').count(),
                }
            })
        
        return context


class InvoiceReportView(LoginRequiredMixin, TemplateView):
    """Invoice reports"""
    template_name = 'membership/reports/invoice_report.html'


class TransferReportView(LoginRequiredMixin, TemplateView):
    """Transfer reports"""
    template_name = 'membership/reports/transfer_report.html'


class OutstandingReportView(LoginRequiredMixin, TemplateView):
    """Outstanding payments report"""
    template_name = 'membership/reports/outstanding_report.html'


class ExportReportView(LoginRequiredMixin, View):
    """Export reports"""
    
    def get(self, request, report_type):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can export reports")
        
        if report_type == 'members':
            return self.export_members()
        elif report_type == 'invoices':
            return self.export_invoices()
        else:
            messages.error(request, _('Invalid report type'))
            return redirect('membership:reports_index')
    
    def export_members(self):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="members_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['SAFA ID', 'Name', 'Email', 'Club', 'Status', 'Role'])
        
        for member in Member.objects.select_related('current_club'):
            writer.writerow([
                member.safa_id,
                member.get_full_name(),
                member.email,
                member.current_club.name if member.current_club else '',
                member.get_status_display(),
                member.get_role_display()
            ])
        
        return response
    
    def export_invoices(self):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="invoices_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Invoice Number', 'Member', 'Amount', 'Status', 'Issue Date'])
        
        for invoice in Invoice.objects.select_related('member'):
            writer.writerow([
                invoice.invoice_number,
                invoice.member.get_full_name() if invoice.member else 'Organization',
                float(invoice.total_amount),
                invoice.get_status_display(),
                invoice.issue_date
            ])
        
        return response


# ============================================================================
# MISSING BULK OPERATION VIEWS
# ============================================================================

class BulkApproveView(LoginRequiredMixin, View):
    """Bulk approve members"""
    
    def post(self, request):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can perform bulk operations")
        
        member_ids = request.POST.getlist('member_ids')
        if not member_ids:
            messages.error(request, _('No members selected'))
            return redirect('membership:member_list')
        
        try:
            with transaction.atomic():
                approved_count = 0
                for member_id in member_ids:
                    try:
                        member = Member.objects.get(pk=member_id, status='PENDING')
                        member.approve_safa_membership(request.user)
                        approved_count += 1
                    except Member.DoesNotExist:
                        continue
                
                messages.success(request, f'Successfully approved {approved_count} members')
        except Exception as e:
            messages.error(request, f'Error during bulk approval: {str(e)}')
        
        return redirect('membership:member_list')


class BulkRejectView(LoginRequiredMixin, View):
    """Bulk reject members"""
    
    def post(self, request):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can perform bulk operations")
        
        member_ids = request.POST.getlist('member_ids')
        reason = request.POST.get('reason', '')
        
        if not member_ids:
            messages.error(request, _('No members selected'))
            return redirect('membership:member_list')
        
        if not reason:
            messages.error(request, _('Rejection reason is required'))
            return redirect('membership:member_list')
        
        try:
            with transaction.atomic():
                rejected_count = 0
                for member_id in member_ids:
                    try:
                        member = Member.objects.get(pk=member_id, status='PENDING')
                        member.reject_safa_membership(request.user, reason)
                        rejected_count += 1
                    except Member.DoesNotExist:
                        continue
                
                messages.success(request, f'Successfully rejected {rejected_count} members')
        except Exception as e:
            messages.error(request, f'Error during bulk rejection: {str(e)}')
        
        return redirect('membership:member_list')


class BulkInvoiceView(LoginRequiredMixin, View):
    """Bulk generate invoices"""
    
    def post(self, request):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can generate invoices")
        
        # TODO: Implement bulk invoice generation
        messages.info(request, _('Bulk invoice generation not implemented yet'))
        return redirect('membership:invoice_list')


class BulkReminderView(LoginRequiredMixin, View):
    """Bulk send reminders"""
    
    def post(self, request):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can send reminders")
        
        # TODO: Implement bulk reminder sending
        messages.info(request, _('Bulk reminder sending not implemented yet'))
        return redirect('membership:invoice_list')


# ============================================================================
# MISSING WORKFLOW VIEWS
# ============================================================================

class WorkflowDetailView(LoginRequiredMixin, DetailView):
    """Workflow detail view"""
    model = RegistrationWorkflow
    template_name = 'membership/workflow_detail.html'
    context_object_name = 'workflow'
    
    def get_object(self):
        member = get_object_or_404(Member, pk=self.kwargs['member_id'])
        workflow, created = RegistrationWorkflow.objects.get_or_create(member=member)
        return workflow


class WorkflowUpdateView(LoginRequiredMixin, View):
    """Update workflow"""
    
    def post(self, request, member_id):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can update workflows")
        
        member = get_object_or_404(Member, pk=member_id)
        workflow, created = RegistrationWorkflow.objects.get_or_create(member=member)
        
        # Update workflow steps based on POST data
        for step in ['personal_info', 'club_selection', 'document_upload', 'payment', 'club_approval', 'safa_approval']:
            status = request.POST.get(f'{step}_status')
            if status:
                setattr(workflow, f'{step}_status', status)
        
        workflow.update_progress()
        messages.success(request, _('Workflow updated successfully'))
        
        return redirect('membership:workflow_detail', member_id=member_id)


class StatusCheckView(LoginRequiredMixin, TemplateView):
    """Check system status"""
    template_name = 'membership/status_check.html'


# ============================================================================
# MISSING NOTIFICATION VIEWS
# ============================================================================

class NotificationListView(LoginRequiredMixin, TemplateView):
    """List notifications"""
    template_name = 'membership/notification_list.html'


class SendNotificationView(LoginRequiredMixin, View):
    """Send notification"""
    
    def post(self, request):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can send notifications")
        
        # TODO: Implement notification sending
        messages.info(request, _('Notification sending not implemented yet'))
        return redirect('membership:notification_list')


class PaymentReminderView(LoginRequiredMixin, View):
    """Send payment reminder"""
    
    def post(self, request):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can send payment reminders")
        
        # TODO: Implement payment reminder
        messages.info(request, _('Payment reminder not implemented yet'))
        return redirect('membership:invoice_list')


# ============================================================================
# MISSING LEGACY AND UTILITY VIEWS
# ============================================================================

class LegacyRedirectView(View):
    """Redirect legacy URLs to new system"""
    
    def get(self, request, target):
        messages.info(request, _('Please use the new registration system'))
        return redirect(f'membership:{target}')


class HealthCheckView(View):
    """Health check endpoint"""
    
    def get(self, request):
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat()
        })


class VersionView(View):
    """Version information"""
    
    def get(self, request):
        return JsonResponse({
            'version': '1.0.0',
            'system': 'SAFA Membership System'
        })


class TestEmailView(LoginRequiredMixin, View):
    """Test email functionality"""
    
    def get(self, request):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can test email")
        
        try:
            send_mail(
                'Test Email',
                'This is a test email from SAFA system',
                'noreply@safa.org.za',
                [request.user.email],
                fail_silently=False
            )
            messages.success(request, _('Test email sent successfully'))
        except Exception as e:
            messages.error(request, f'Email test failed: {str(e)}')
        
        return redirect('membership:member_list')


# ============================================================================
# VIEWSET FOR API
# ============================================================================

class MemberViewSet(viewsets.ModelViewSet):
    """ViewSet for Member CRUD operations via DRF"""
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        if user.is_superuser or user.is_staff:
            return qs
        
        # Filter base
    