# views.py
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
from .models import CustomUser, Membership, Club
from .forms import PlayerRegistrationForm, PaymentSelectionForm


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
            self.user_club_membership = Membership.objects.get(
                user=request.user,
                membership_type='club',
                is_active=True,
                club__isnull=False
            )
            self.user_club = self.user_club_membership.club
        except Membership.DoesNotExist:
            raise PermissionDenied("You must be associated with a club to register players.")
        
        return super().dispatch(request, *args, **kwargs)


class PlayerRegistrationView(ClubAdminRequiredMixin, CreateView):
    """Step 1: Player personal details registration"""
    model = CustomUser
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
            'name': player_data['name'],
            'surname': player_data['surname'],
            'middle_name': player_data.get('middle_name', ''),
            'email': player_data['email'],
            'date_of_birth': player_data['date_of_birth'].isoformat(),
            'gender': player_data['gender'],
            'id_number': player_data.get('id_number', ''),
            'passport_number': player_data.get('passport_number', ''),
            'id_document_type': player_data['id_document_type'],
            'address': player_data.get('address', ''),
            'postal_address': player_data.get('postal_address', ''),
            'next_of_kin': player_data.get('next_of_kin', ''),
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
        context['club'] = self.user_club
        context['step'] = 2
        context['junior_fee'] = 100  # R100
        context['senior_fee'] = 200  # R200
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
        request.session['payment_data'] = {
            'membership_type': membership_type,
            'payment_method': payment_method,
            'fee_amount': 100 if membership_type == 'JR' else 200
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
            
            # Check if reference already exists (you might want to store these in a PaymentReference model)
            # For now, we'll assume it's unique
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
        """Create the player and membership records"""
        try:
            player_data = self.request.session['player_data']
            payment_data = self.request.session['payment_data']
            payment_reference = self.request.session['payment_reference']
            
            # Create the player user account
            player = CustomUser.objects.create_user(
                username=f"{player_data['name'].lower()}.{player_data['surname'].lower()}.{get_random_string(4).lower()}",
                name=player_data['name'],
                surname=player_data['surname'],
                middle_name=player_data.get('middle_name', ''),
                email=player_data['email'],
                date_of_birth=player_data['date_of_birth'],
                gender=player_data['gender'],
                id_number=player_data.get('id_number', ''),
                passport_number=player_data.get('passport_number', ''),
                id_document_type=player_data['id_document_type'],
                role='PLAYER',
                country=self.user_club.province.country if self.user_club.province else None,
                is_active=False,  # Will be activated when payment is confirmed
                payment_required=True
            )
            
            # Create membership
            membership = Membership.objects.create(
                user=player,
                membership_type='club',
                club=self.user_club,
                region=self.user_club.region,
                local_football_association=self.user_club.local_football_association,
                start_date=timezone.now().date(),
                player_category=payment_data['membership_type'],
                jersey_number=player_data.get('jersey_number'),
                position=player_data.get('position', ''),
                address=player_data.get('address', ''),
                postal_address=player_data.get('postal_address', ''),
                next_of_kin=player_data.get('next_of_kin', ''),
                is_active=False,  # Will be activated when payment is confirmed
                payment_confirmed=False
            )
            
            # Store IDs for success page
            self.request.session['created_player_id'] = player.id
            self.request.session['created_membership_id'] = membership.id
            
            # Clear registration data but keep payment reference for tracking
            del self.request.session['player_data']
            del self.request.session['payment_data']
            
            messages.success(self.request, f"Player {player.name} {player.surname} registered successfully!")
            return redirect('membership:registration_success')
            
        except Exception as e:
            messages.error(self.request, f"Registration failed: {str(e)}")
            return self.get(self.request)
    
    def process_card_payment(self):
        """Handle card payment redirect"""
        payment_reference = self.request.session['payment_reference']
        payment_data = self.request.session['payment_data']
        
        # In a real implementation, you would redirect to your payment gateway
        # For now, we'll simulate the redirect
        
        # Store additional data for payment gateway
        self.request.session['payment_gateway_data'] = {
            'amount': payment_data['fee_amount'],
            'reference': payment_reference,
            'return_url': self.request.build_absolute_uri(reverse('membership:payment_return')),
            'cancel_url': self.request.build_absolute_uri(reverse('membership:payment_cancel')),
        }
        
        # Simulate redirect to payment gateway
        messages.info(self.request, f"Redirecting to payment gateway for R{payment_data['fee_amount']}...")
        
        # In real implementation:
        # return redirect(f"https://payment-gateway.com/pay?amount={amount}&ref={reference}")
        
        # For now, create the registration and redirect to success
        return self.process_registration()


class RegistrationSuccessView(ClubAdminRequiredMixin, TemplateView):
    """Final success page showing registration details"""
    template_name = 'registration/registration_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get created player and membership
        player_id = self.request.session.get('created_player_id')
        membership_id = self.request.session.get('created_membership_id')
        payment_reference = self.request.session.get('payment_reference')
        
        if player_id and membership_id:
            try:
                player = CustomUser.objects.get(id=player_id)
                membership = Membership.objects.get(id=membership_id)
                
                context.update({
                    'player': player,
                    'membership': membership,
                    'payment_reference': payment_reference,
                    'club': self.user_club,
                })
            except (CustomUser.DoesNotExist, Membership.DoesNotExist):
                messages.error(self.request, "Registration details not found.")
        
        return context


# AJAX Views for dynamic form updates
class GetClubInfoView(ClubAdminRequiredMixin, JsonResponse):
    """Return club information for form population"""
    
    def get(self, request, *args, **kwargs):
        data = {
            'club_name': self.user_club.name,
            'region': self.user_club.region.name if self.user_club.region else '',
            'lfa': self.user_club.local_football_association.name if self.user_club.local_football_association else '',
            'province': self.user_club.province.name if self.user_club.province else '',
        }
        return JsonResponse(data)