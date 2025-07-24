from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils import timezone
from django.db import transaction  # Add this import
import datetime  # Add this import
from .forms import SeniorMemberRegistrationForm, ClubAdminPlayerRegistrationForm
from .models import Player, PlayerClubRegistration
from membership.models import Invoice, InvoiceItem

# Also add this utility function to generate unique emails
def generate_unique_player_email(first_name, last_name):
    """Generate a unique email for a player"""
    from django.utils.crypto import get_random_string
    from .models import Player
    
    base_email = f"{first_name.lower()}.{last_name.lower()}".replace(" ", "")
    domain = "@safa.system"
    
    # Try the base email first
    email = f"{base_email}{domain}"
    if not Player.objects.filter(email=email).exists():
        return email
    
    # If it exists, add a random string
    for _ in range(10):  # Try up to 10 times
        random_suffix = get_random_string(4)
        email = f"{base_email}{random_suffix}{domain}"
        if not Player.objects.filter(email=email).exists():
            return email
    
    # Fallback to completely random email
    return f"player_{get_random_string(8)}{domain}"

def senior_registration(request):
    """Senior membership registration"""
    if request.method == 'POST':
        form = SeniorMemberRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    player = form.save(commit=False)
                    player.status = 'PENDING'
                    
                    if not player.email:
                        player.email = generate_unique_player_email(player.first_name, player.last_name)

                    registration_as = form.cleaned_data.get('registration_as')

                    if registration_as == 'PLAYER':
                        player.role = 'PLAYER'
                        player.save()

                        if player.club:
                            PlayerClubRegistration.objects.create(
                                player=player,
                                club=player.club,
                                status='PENDING'
                            )
                        
                        invoice = create_player_invoice(
                            player=player,
                            club=player.club,
                            issued_by=request.user,
                            is_junior=False
                        )
                        messages.success(request, _('Player registration submitted successfully. An invoice has been generated.'))

                    else: # General Member
                        player.role = 'MEMBER'
                        player.save()
                        # Create a general membership invoice (not tied to a club registration)
                        invoice = Invoice.objects.create(
                            player=player,
                            amount=50.00,  # A different fee for general membership
                            status='PENDING',
                            invoice_type='MEMBERSHIP',
                            due_date=timezone.now() + timezone.timedelta(days=30)
                        )
                        InvoiceItem.objects.create(
                            invoice=invoice,
                            description='General Membership Fee',
                            quantity=1,
                            unit_price=50.00
                        )
                        messages.success(request, _('General membership application submitted successfully. An invoice has been generated.'))

                    return redirect('membership:registration_selector')

            except Exception as e:
                messages.error(request, _(f"An unexpected error occurred during registration: {e}"))
        
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields.get(field).label if form.fields.get(field) and field != '__all__' else 'Form Error'}: {error}")
    else:
        form = SeniorMemberRegistrationForm()
    
    return render(request, 'membership/senior_registration.html', {'form': form})

def club_admin_add_player(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'role') or request.user.role != 'CLUB_ADMIN':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('accounts:dashboard')

    if not request.user.club:
        messages.error(request, 'Your user profile is not linked to a club. Please contact support.')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        player_form = ClubAdminPlayerRegistrationForm(request.POST, request.FILES, request=request)
        if player_form.is_valid():
            try:
                # The form's save method now handles everything, including invoice creation
                player = player_form.save()

                invoice = player_form.invoice
                success_message = f'Player \'{player.first_name} {player.last_name}\' registered successfully with email {player.email}!'
                
                if invoice:
                    fee = invoice.amount
                    success_message += f' An invoice (#{invoice.invoice_number}) has been created for R{fee:.2f}.'
                    success_message += ' The player will be eligible for approval once the invoice is paid.'
                else:
                    messages.warning(request, "Player was created, but an invoice could not be generated.")

                messages.success(request, success_message)
                return redirect('accounts:dashboard')
            except Exception as e:
                messages.error(request, f"An unexpected error occurred: {e}")

        else:
            # Form is invalid, display errors
            for field, errors in player_form.errors.items():
                for error in errors:
                    # Use a more user-friendly field name
                    field_label = player_form.fields[field].label if field in player_form.fields else 'Form'
                    messages.error(request, f"{field_label}: {error}")
            messages.warning(request, 'Please correct the errors below.')

    else:
        player_form = ClubAdminPlayerRegistrationForm(request=request)

    return render(request, 'registration/club_admin_add_player.html', {
        'player_form': player_form
    })