from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from .constants import BANK_DETAILS

from .forms import PlayerRegistrationForm

from .models import (
    Member,
    Invoice,
    InvoiceItem,
    SAFASeasonConfig,
    SAFAFeeStructure
)
from geography.models import Club


class ClubAdminRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user is a club admin"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not (request.user.is_staff or request.user.is_superuser):
            try:
                self.club_member = Member.objects.get(
                    user=request.user,
                    status='ACTIVE',
                    current_club__isnull=False
                )
                self.user_club = self.club_member.current_club
                # Check if the user is a club admin for their current club.
                # This assumes a ManyToManyField `club_admins` on the Club model.
                if not self.user_club.club_admins.filter(pk=request.user.pk).exists():
                     raise PermissionDenied("You must be a club administrator to register players.")
            except Member.DoesNotExist:
                raise PermissionDenied("You must be associated with a club to register players.")
        else:
            # For superusers, we need a club context. This part is tricky.
            # For now, let's assume superuser needs to select a club.
            club_id = request.session.get('admin_selected_club_id')
            if not club_id:
                # Redirect to a club selection page if not set
                # This page does not exist, so this is a placeholder for a complete implementation.
                messages.error(request, "Superusers must select a club to manage registrations.")
                return redirect(reverse('admin:index')) # Redirect to admin home as a fallback
            self.user_club = get_object_or_404(Club, pk=club_id)

        return super().dispatch(request, *args, **kwargs)


class PlayerRegistrationView(ClubAdminRequiredMixin, CreateView):
    """Step 1: Player personal details registration"""
    model = Member
    form_class = PlayerRegistrationForm
    template_name = 'membership/templates/membership/senior_registration.html' # Changed to a valid template path
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # The form does not take club as an argument anymore.
        # kwargs['club'] = self.user_club
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['club'] = self.user_club
        context['step'] = 1
        return context
    
    def form_valid(self, form):
        # The form now creates a user and a member.
        # We need to assign the club and role.
        member = form.save(commit=False)
        member.current_club = self.user_club
        member.role = 'PLAYER'
        member.status = 'PENDING' # Start as pending
        member.save()
        
        # Store member ID in session for next step
        self.request.session['new_member_id'] = member.id
        
        return redirect('membership:payment_selection')


class PaymentSelectionView(ClubAdminRequiredMixin, TemplateView):
    """Step 2: Select membership type and payment method"""
    template_name = 'membership/templates/membership/payment_selection.html' # Changed to a valid template path

    def dispatch(self, request, *args, **kwargs):
        if 'new_member_id' not in request.session:
            messages.error(request, "Please complete player registration first.")
            return redirect('membership:player_registration')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = get_object_or_404(Member, pk=self.request.session['new_member_id'])

        active_season = SAFASeasonConfig.get_active_season()
        if not active_season:
            messages.error(self.request, "No active season found.")
            return context

        fee_type = 'PLAYER_JUNIOR' if member.is_junior else 'PLAYER_SENIOR'
        fee_structure = SAFAFeeStructure.objects.filter(season_config=active_season, entity_type=fee_type).first()

        if not fee_structure:
            messages.error(self.request, f"No fee structure found for {fee_type} in the current season.")
            return context

        context['club'] = self.user_club
        context['step'] = 2
        context['fee_amount'] = fee_structure.annual_fee
        context['member'] = member
        context['fee_type'] = fee_type
        return context

    def post(self, request, *args, **kwargs):
        payment_method = request.POST.get('payment_method')
        fee_amount = request.POST.get('fee_amount')
        fee_type = request.POST.get('fee_type')

        if not payment_method or not fee_amount or not fee_type:
            messages.error(request, "Please select a payment method.")
            return self.get(request, *args, **kwargs)

        request.session['payment_data'] = {
            'payment_method': payment_method,
            'fee_amount': fee_amount,
            'fee_type': fee_type
        }
        
        return redirect('membership:payment_confirmation')


class PaymentConfirmationView(ClubAdminRequiredMixin, TemplateView):
    """Step 3: Generate payment reference and show payment details"""
    template_name = 'membership/templates/membership/payment_confirmation.html' # Changed to a valid template path

    def dispatch(self, request, *args, **kwargs):
        if 'new_member_id' not in request.session or 'payment_data' not in request.session:
            messages.error(request, "Registration data missing. Please start again.")
            return redirect('membership:player_registration')
        return super().dispatch(request, *args, **kwargs)

    def generate_payment_reference(self):
        """Generate unique payment reference code"""
        return f"SAFA-{get_random_string(8).upper()}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if 'payment_reference' not in self.request.session:
            self.request.session['payment_reference'] = self.generate_payment_reference()
        
        member = get_object_or_404(Member, pk=self.request.session['new_member_id'])
        payment_data = self.request.session['payment_data']
        
        context.update({
            'club': self.user_club,
            'step': 3,
            'member': member,
            'payment_data': payment_data,
            'payment_reference': self.request.session['payment_reference'],
        })
        
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'confirm_registration':
            return self.process_registration()
        return self.get(request, *args, **kwargs)

    @transaction.atomic
    def process_registration(self):
        """Create the invoice for the registration"""
        try:
            member = get_object_or_404(Member, pk=self.request.session['new_member_id'])
            payment_data = self.request.session['payment_data']
            payment_reference = self.request.session['payment_reference']
            active_season = SAFASeasonConfig.get_active_season()

            # Create invoice for payment
            invoice = Invoice.objects.create(
                member=member,
                season_config=active_season,
                invoice_type='MEMBER_REGISTRATION',
                subtotal=Decimal(payment_data['fee_amount']),
                status='PENDING',
                notes=f"Registration invoice for {member.get_full_name()}",
                invoice_number=payment_reference,
            )
            
            InvoiceItem.objects.create(
                invoice=invoice,
                description=f"{payment_data['fee_type']} Registration Fee",
                quantity=1,
                amount=Decimal(payment_data['fee_amount'])
            )
            
            self.request.session['created_invoice_id'] = invoice.id
            
            messages.success(self.request, f"Invoice for {member.get_full_name()} created successfully!")
            return redirect('membership:registration_success')
            
        except Exception as e:
            messages.error(self.request, f"Registration failed: {str(e)}")
            return self.get(self.request)


class RegistrationSuccessView(ClubAdminRequiredMixin, TemplateView):
    """Final success page showing registration details"""
    template_name = 'membership/templates/membership/registration_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        member_id = self.request.session.get('new_member_id')
        invoice_id = self.request.session.get('created_invoice_id')
        
        if member_id and invoice_id:
            try:
                member = Member.objects.get(id=member_id)
                invoice = Invoice.objects.get(id=invoice_id)
                
                context.update({
                    'member': member,
                    'invoice': invoice,
                    'club': self.user_club,
                    'bank_details': BANK_DETAILS,
                })
            except (Member.DoesNotExist, Invoice.DoesNotExist):
                messages.error(self.request, "Registration details not found.")
        
        # Clear session data
        for key in ['new_member_id', 'payment_data', 'payment_reference', 'created_invoice_id']:
            if key in self.request.session:
                del self.request.session[key]

        return context

# AJAX Views for dynamic form updates
def get_club_info(request):
    """Return club information for form population"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
        
    try:
        # This logic assumes a simple link from user to one club via Member profile.
        member = Member.objects.get(user=request.user, current_club__isnull=False)
        club = member.current_club
        
        data = {
            'club_name': club.name,
            'address': club.address,
            'phone': club.phone,
            'email': club.email,
        }
        return JsonResponse(data)
    except Member.DoesNotExist:
        return JsonResponse({'error': 'User is not associated with a club'}, status=403)
