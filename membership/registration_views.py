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

from .constants import JUNIOR_FEE_ZAR, SENIOR_FEE_ZAR, BANK_DETAILS

from .forms import PaymentSelectionForm, PlayerRegistrationForm
from registration.models import (
    Player,
    PlayerClubRegistration
)
from .models import (
    Member,
)
from .models import Invoice, InvoiceItem
from geography.models import Club


class ClubAdminRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user is a club admin"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user has CLUB_ADMIN role or is admin
        if request.user.role not in ['CLUB_ADMIN', 'ADMIN', 'ADMIN_COUNTRY']:
            raise PermissionDenied("You must be a club administrator to register players.")
        
        # Get the user's club membership
        try:
            self.club_member = Member.objects.get(
                user=request.user,
                role='CLUB_ADMIN',
                status='ACTIVE',
                club__isnull=False
            )
            self.user_club = self.club_member.club
        except Member.DoesNotExist:
            raise PermissionDenied("You must be associated with a club to register players.")
        
        return super().dispatch(request, *args, **kwargs)


class PlayerRegistrationView(ClubAdminRequiredMixin, CreateView):
    """Step 1: Player personal details registration"""
    model = Player
    form_class = PlayerRegistrationForm
    template_name = 'registration/player_registration.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['club'] = self.user_club
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['club'] = self.user_club
        context['step'] = 1
        return context
    
    def form_valid(self, form):
        # Don't save yet, store in session for next step
        player_data = form.cleaned_data
        
        # Store player data in session
        self.request.session['player_data'] = {
            'first_name': player_data['first_name'],
            'last_name': player_data['last_name'],
            'email': player_data['email'],
            'date_of_birth': player_data['date_of_birth'].isoformat(),
            'gender': player_data['gender'],
            'id_number': player_data.get('id_number', ''),
            'phone_number': player_data.get('phone_number', ''),
            'street_address': player_data.get('street_address', ''),
            'suburb': player_data.get('suburb', ''),
            'city': player_data.get('city', ''),
            'state': player_data.get('state', ''),
            'postal_code': player_data.get('postal_code', ''),
            'country': player_data.get('country', ''),
            'emergency_contact': player_data.get('emergency_contact', ''),
            'emergency_phone': player_data.get('emergency_phone', ''),
            'medical_notes': player_data.get('medical_notes', ''),
            'jersey_number': player_data.get('jersey_number'),
            'position': player_data.get('position', ''),
        }
        
        return redirect('membership:payment_selection')


class PaymentSelectionView(ClubAdminRequiredMixin, TemplateView):
    """Step 2: Select membership type and payment method"""
    template_name = 'registration/payment_selection.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check if player data exists in session
        if 'player_data' not in request.session:
            messages.error(request, "Please complete player registration first.")
            return redirect('membership:player_registration')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from membership.constants import JUNIOR_FEE_ZAR, SENIOR_FEE_ZAR
        context['club'] = self.user_club
        context['step'] = 2
        context['junior_fee'] = float(JUNIOR_FEE_ZAR)  # ZAR 100
        context['senior_fee'] = float(SENIOR_FEE_ZAR)  # ZAR 200
        return context
    
    def post(self, request, *args, **kwargs):
        membership_type = request.POST.get('membership_type')
        payment_method = request.POST.get('payment_method')
        
        if not membership_type or not payment_method:
            messages.error(request, "Please select both membership type and payment method.")
            return self.get(request, *args, **kwargs)
        
        if membership_type not in ['JR', 'SR']:
            messages.error(request, "Invalid membership type selected.")
            return self.get(request, *args, **kwargs)
        
        if payment_method not in ['EFT', 'CARD']:
            messages.error(request, "Invalid payment method selected.")
            return self.get(request, *args, **kwargs)
        
        # Store payment selection in session
        from membership.constants import JUNIOR_FEE_ZAR, SENIOR_FEE_ZAR
        request.session['payment_data'] = {
            'membership_type': membership_type,
            'payment_method': payment_method,
            'fee_amount': float(JUNIOR_FEE_ZAR) if membership_type == 'JR' else float(SENIOR_FEE_ZAR)
        }
        
        return redirect('membership:payment_confirmation')


class PaymentConfirmationView(ClubAdminRequiredMixin, TemplateView):
    """Step 3: Generate payment reference and show payment details"""
    template_name = 'registration/payment_confirmation.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check if required data exists in session
        if 'player_data' not in request.session or 'payment_data' not in request.session:
            messages.error(request, "Registration data missing. Please start again.")
            return redirect('membership:player_registration')
        return super().dispatch(request, *args, **kwargs)
    
    def generate_payment_reference(self):
        """Generate unique payment reference code"""
        while True:
            timestamp = str(int(timezone.now().timestamp()))[-6:]
            random_part = get_random_string(6, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            reference = f"PAY-{timestamp}-{random_part}"
            break
        return reference
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Generate payment reference if not exists
        if 'payment_reference' not in self.request.session:
            self.request.session['payment_reference'] = self.generate_payment_reference()
        
        player_data = self.request.session['player_data']
        payment_data = self.request.session['payment_data']
        
        context.update({
            'club': self.user_club,
            'step': 3,
            'player_data': player_data,
            'payment_data': payment_data,
            'payment_reference': self.request.session['payment_reference'],
            'membership_type_display': 'Junior' if payment_data['membership_type'] == 'JR' else 'Senior',
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Process final registration"""
        if request.POST.get('action') == 'confirm_registration':
            return self.process_registration()
        elif request.POST.get('action') == 'proceed_card_payment':
            return self.process_card_payment()
        
        return self.get(request, *args, **kwargs)
    
    @transaction.atomic
    def process_registration(self):
        """Create the player and club registration records with invoice"""
        try:
            player_data = self.request.session['player_data']
            payment_data = self.request.session['payment_data']
            payment_reference = self.request.session['payment_reference']
            
            # Create the player
            player = Player.objects.create(
                first_name=player_data['first_name'],
                last_name=player_data['last_name'],
                email=player_data['email'],
                date_of_birth=player_data['date_of_birth'],
                gender=player_data['gender'],
                id_number=player_data.get('id_number', ''),
                phone_number=player_data['phone_number'],
                street_address=player_data['street_address'],
                suburb=player_data['suburb'],
                city=player_data['city'],
                state=player_data['state'],
                postal_code=player_data['postal_code'],
                country=player_data['country'],
                emergency_contact=player_data['emergency_contact'],
                emergency_phone=player_data['emergency_phone'],
                medical_notes=player_data['medical_notes'],
                role='PLAYER',
                status='INACTIVE',  # Will be activated when payment is confirmed
                club=self.user_club
            )
            
            # Create club registration
            registration = PlayerClubRegistration.objects.create(
                player=player,
                club=self.user_club,
                registration_date=timezone.now().date(),
                status='INACTIVE',
                position=player_data.get('position', ''),
                jersey_number=player_data.get('jersey_number'),
                notes=f"Payment Reference: {payment_reference}\n"
                      f"Membership Type: {'Junior' if payment_data['membership_type'] == 'JR' else 'Senior'}"
            )
            
            # Create invoice for payment
            fee_amount = payment_data['fee_amount']
            membership_type = 'Junior' if payment_data['membership_type'] == 'JR' else 'Senior'
            
            # Get content type for registration
            content_type = ContentType.objects.get_for_model(registration)
            
            # Create invoice
            invoice = Invoice.objects.create(
                reference=payment_reference,
                invoice_type='REGISTRATION',
                amount=fee_amount,
                player=player,
                club=self.user_club,
                issued_by=self.club_member,
                content_type=content_type,
                object_id=registration.id,
                payment_method=payment_data['payment_method'],
                status='PENDING',
                notes=f"Registration invoice for {player.get_full_name()}\n"
                      f"Membership Type: {membership_type}"
            )
            
            # Create invoice item
            InvoiceItem.objects.create(
                invoice=invoice,
                description=f"{membership_type} Player Registration Fee",
                quantity=1,
                unit_price=fee_amount,
                sub_total=fee_amount
            )
            
            # Store IDs for success page
            self.request.session['created_player_id'] = player.id
            self.request.session['created_registration_id'] = registration.id
            self.request.session['created_invoice_id'] = invoice.id
            
            # Clear registration data but keep payment reference for tracking
            del self.request.session['player_data']
            del self.request.session['payment_data']
            
            # If payment method is CARD and we're not immediately processing
            # Store the invoice UUID for the payment page
            if payment_data['payment_method'] == 'CARD':
                self.request.session['pending_invoice_uuid'] = str(invoice.uuid)
            
            messages.success(self.request, f"Player {player.get_full_name()} registered successfully!")
            return redirect('membership:registration_success')
            
        except Exception as e:
            messages.error(self.request, f"Registration failed: {str(e)}")
            return self.get(self.request)
    
    def process_card_payment(self):
        """Handle card payment redirect"""
        payment_reference = self.request.session['payment_reference']
        payment_data = self.request.session['payment_data']
        
        # Create the registration and invoice
        result = self.process_registration()
        
        # Get the invoice UUID
        invoice_uuid = self.request.session.get('pending_invoice_uuid')
        
        if not invoice_uuid:
            messages.error(self.request, "Payment processing failed: Invoice not created")
            return result
        
        # Prepare payment gateway data
        self.request.session['payment_gateway_data'] = {
            'amount': payment_data['fee_amount'],
            'reference': payment_reference,
            'invoice_uuid': invoice_uuid,
            'return_url': self.request.build_absolute_uri(reverse('membership:payment_return')),
            'cancel_url': self.request.build_absolute_uri(reverse('membership:payment_cancel')),
        }
        
        # In a real implementation, redirect to payment gateway
        # For development, simulate a successful payment
        messages.info(self.request, f"Redirecting to payment gateway for R{payment_data['fee_amount']}...")
        
        # For now, just return the registration process result
        return result


class RegistrationSuccessView(ClubAdminRequiredMixin, TemplateView):
    """Final success page showing registration details"""
    template_name = 'registration/registration_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get created player, registration and invoice
        player_id = self.request.session.get('created_player_id')
        registration_id = self.request.session.get('created_registration_id')
        invoice_id = self.request.session.get('created_invoice_id')
        payment_reference = self.request.session.get('payment_reference')
        
        if player_id and registration_id:
            try:
                player = Player.objects.get(id=player_id)
                registration = PlayerClubRegistration.objects.get(id=registration_id)
                invoice = None
                
                if invoice_id:
                    try:
                        invoice = Invoice.objects.get(id=invoice_id)
                    except Invoice.DoesNotExist:
                        pass
                
                context.update({
                    'player': player,
                    'registration': registration,
                    'invoice': invoice,
                    'payment_reference': payment_reference,
                    'club': self.user_club,
                    'bank_details': BANK_DETAILS,
                })
            except (Player.DoesNotExist, PlayerClubRegistration.DoesNotExist):
                messages.error(self.request, "Registration details not found.")
        
        return context


# AJAX Views for dynamic form updates
def get_club_info(request):
    """Return club information for form population"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
        
    try:
        admin_member = Member.objects.get(
            user=request.user,
            role='CLUB_ADMIN',
            status='ACTIVE',
            club__isnull=False
        )
        club = admin_member.club
        
        data = {
            'club_name': club.name,
            'address': club.address,
            'phone': club.phone,
            'email': club.email,
        }
        return JsonResponse(data)
    except Member.DoesNotExist:
        return JsonResponse({'error': 'Not a club administrator'}, status=403)
