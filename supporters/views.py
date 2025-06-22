from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
from .forms import SupporterRegistrationForm
from .models import SupporterProfile
from accounts.models import CustomUser
from membership.models.invoice import Invoice
from membership.models import Member
from geography.models import Club
from rest_framework import viewsets
from .serializers import SupporterProfileSerializer
from .permissions import IsSupporterSelfOrReadOnly

# Membership pricing (in ZAR)
MEMBERSHIP_PRICING = {
    'PREMIUM': 150.00,
    'VIP': 300.00,
    'FAMILY_BASIC': 450.00,  # Premium for 4 people
    'FAMILY_PREMIUM': 900.00,  # VIP for 4 people
    'FAMILY_VIP': 1500.00,  # Premium VIP package
}

def create_supporter_invoice(supporter_profile):
    """Create an invoice for a supporter registration"""
    try:
        # Get pricing for membership type
        amount = MEMBERSHIP_PRICING.get(supporter_profile.membership_type, 0)
        
        if amount == 0:
            return None  # No invoice needed for free memberships
        
        # Calculate tax (15% VAT)
        tax_amount = amount * 0.15
        total_amount = amount + tax_amount
        
        # Generate invoice number
        invoice_number = f"SUP-{timezone.now().strftime('%Y%m%d')}-{supporter_profile.id:06d}"
        
        # Get a default club (first available club)
        default_club = Club.objects.first()
        club_to_use = supporter_profile.favorite_club or default_club
        
        if not club_to_use:
            print("No club available for invoice creation")
            return None
        
        # Get or create a system member for issuing invoices
        system_user, created = CustomUser.objects.get_or_create(
            email='system@safa.net',
            defaults={
                'username': 'system',
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_active': True
            }
        )
        
        # Get or create system member
        system_member, created = Member.objects.get_or_create(
            user=system_user,
            defaults={
                'membership_status': 'ACTIVE',
                'role': 'ADMIN_SYSTEM'
            }
        )
        
        # Create invoice
        invoice = Invoice.objects.create(
            invoice_number=invoice_number,
            invoice_type='REGISTRATION',
            amount=total_amount,
            tax_amount=tax_amount,
            status='PENDING',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            club=club_to_use,
            issued_by=system_member,
            notes=f"Supporter registration - {supporter_profile.get_membership_type_display()}"
        )
        
        return invoice
        
    except Exception as e:
        print(f"Error creating invoice: {e}")
        return None

@login_required
def register_supporter(request):
    user = request.user
    try:
        profile = user.supporterprofile
        return redirect('supporters:profile')
    except SupporterProfile.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = SupporterRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            supporter = form.save(commit=False)
            supporter.user = user
            
            # Set location timestamp if coordinates were provided
            if supporter.latitude and supporter.longitude:
                supporter.location_timestamp = timezone.now()
            
            supporter.save()
            
            # Create invoice for paid memberships
            invoice = create_supporter_invoice(supporter)
            if invoice:
                supporter.invoice = invoice
                supporter.save()
                messages.success(
                    request, 
                    f'Registration successful! Invoice #{invoice.invoice_number} has been created for R{invoice.amount:.2f}. '
                    f'Please complete payment within 30 days.'
                )
            else:
                messages.success(request, 'Registration successful!')
            
            return redirect('supporters:profile')
    else:
        form = SupporterRegistrationForm()
    
    return render(request, 'supporters/register.html', {
        'form': form,
        'membership_pricing': MEMBERSHIP_PRICING
    })

@login_required
def supporter_profile(request):
    profile = request.user.supporterprofile
    return render(request, 'supporters/profile.html', {'profile': profile})

class SupporterProfileViewSet(viewsets.ModelViewSet):
    queryset = SupporterProfile.objects.all()
    serializer_class = SupporterProfileSerializer
    permission_classes = [IsSupporterSelfOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'supporterprofile'):
            return SupporterProfile.objects.filter(user=user)
        return super().get_queryset()
