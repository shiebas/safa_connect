from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
from .forms import SupporterRegistrationForm, SupporterPreferencesForm
from .models import SupporterProfile, SupporterPreferences
from accounts.models import CustomUser
from membership.invoice_models import Invoice
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

def register_supporter(request):
    # Allow both authenticated and unauthenticated users
    if request.user.is_authenticated:
        user = request.user
        try:
            profile = user.supporterprofile
            return redirect('supporters:profile')
        except SupporterProfile.DoesNotExist:
            pass
    else:
        user = None
    
    if request.method == 'POST':
        # Only process form if user is authenticated
        if not user:
            messages.error(request, 'Please log in first to complete your supporter registration.')
            return redirect('accounts:login')
            
        form = SupporterRegistrationForm(request.POST, request.FILES)
        preferences_form = SupporterPreferencesForm(request.POST) if request.POST.get('setup_preferences') else None
        
        if form.is_valid() and (preferences_form is None or preferences_form.is_valid()):
            supporter = form.save(commit=False)
            supporter.user = user
            
            # Set location timestamp if coordinates were provided
            if supporter.latitude and supporter.longitude:
                supporter.location_timestamp = timezone.now()
            
            # Create preferences if form was submitted
            if preferences_form:
                preferences = preferences_form.save()
                supporter.preferences = preferences
            
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
        preferences_form = SupporterPreferencesForm()
    
    return render(request, 'supporters/register.html', {
        'form': form,
        'preferences_form': preferences_form,
        'membership_pricing': MEMBERSHIP_PRICING,
        'user_authenticated': request.user.is_authenticated
    })

@login_required
def supporter_profile(request):
    profile = request.user.supporterprofile
    return render(request, 'supporters/profile.html', {'profile': profile})

@login_required
def edit_preferences(request):
    """Allow supporters to update their preferences"""
    try:
        profile = request.user.supporterprofile
        preferences = profile.preferences
        if not preferences:
            preferences = SupporterPreferences.objects.create()
            profile.preferences = preferences
            profile.save()
    except SupporterProfile.DoesNotExist:
        messages.error(request, 'You need to complete your supporter registration first.')
        return redirect('supporters:register')
    
    if request.method == 'POST':
        form = SupporterPreferencesForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your preferences have been updated successfully!')
            return redirect('supporters:profile')
    else:
        form = SupporterPreferencesForm(instance=preferences)
    
    return render(request, 'supporters/edit_preferences.html', {
        'form': form,
        'profile': profile
    })

@login_required
def preferences_setup(request):
    """Standalone preferences setup for existing supporters"""
    try:
        profile = request.user.supporterprofile
        preferences = profile.preferences
        if not preferences:
            preferences = SupporterPreferences.objects.create()
            profile.preferences = preferences
            profile.save()
    except SupporterProfile.DoesNotExist:
        messages.error(request, 'You need to complete your supporter registration first.')
        return redirect('supporters:register')
    
    if request.method == 'POST':
        form = SupporterPreferencesForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your preferences have been set up successfully!')
            return redirect('supporters:profile')
    else:
        form = SupporterPreferencesForm(instance=preferences)
    
    return render(request, 'supporters/preferences_setup.html', {
        'form': form,
        'profile': profile
    })

class SupporterProfileViewSet(viewsets.ModelViewSet):
    queryset = SupporterProfile.objects.all()
    serializer_class = SupporterProfileSerializer
    permission_classes = [IsSupporterSelfOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'supporterprofile'):
            return SupporterProfile.objects.filter(user=user)
        return super().get_queryset()
