from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils import timezone
from django.db import transaction
import datetime
from .forms import SeniorMemberRegistrationForm, ClubAdminPlayerRegistrationForm
from .models import Player, PlayerClubRegistration
from membership.models import Member, Invoice, InvoiceItem

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

def create_membership_invoice(member, amount=100.00, description='National Federation Membership Fee'):
    """Create a national membership invoice"""
    invoice = Invoice.objects.create(
        player=member,  # Using the member as player since Player inherits from Member
        amount=amount,
        status='PENDING',
        invoice_type='MEMBERSHIP',
        due_date=timezone.now() + timezone.timedelta(days=30)
    )
    InvoiceItem.objects.create(
        invoice=invoice,
        description=description,
        quantity=1,
        unit_price=amount
    )
    return invoice

def create_club_registration_invoice(player, club, amount=200.00):
    """Create a club registration invoice"""
    invoice = Invoice.objects.create(
        player=player,
        club=club,
        amount=amount,
        status='PENDING',
        invoice_type='REGISTRATION',  # Changed to REGISTRATION type
        due_date=timezone.now() + timezone.timedelta(days=30)
    )
    InvoiceItem.objects.create(
        invoice=invoice,
        description=f'Club Registration Fee - {club.name}',
        quantity=1,
        unit_price=amount
    )
    return invoice

def senior_registration(request):
    """Senior membership registration - creates both Member and Player if needed"""
    if request.method == 'POST':
        form = SeniorMemberRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Get the registration type
                    registration_as = form.cleaned_data.get('registration_as')
                    
                    if registration_as == 'PLAYER':
                        # Create a Player (which inherits from Member)
                        player = Player()
                        
                        # Copy form data to player
                        for field_name in form.cleaned_data:
                            if hasattr(player, field_name) and field_name != 'registration_as':
                                setattr(player, field_name, form.cleaned_data[field_name])
                        
                        player.status = 'PENDING'
                        player.member_type = 'SENIOR'
                        
                        if not player.email:
                            player.email = generate_unique_player_email(player.first_name, player.last_name)
                        
                        player.save()
                        
                        # Create membership invoice (everyone pays this)
                        membership_invoice = create_membership_invoice(
                            member=player,
                            amount=100.00,
                            description='National Federation Membership Fee'
                        )
                        
                        club_invoice = None
                        # If they selected a club, create club registration
                        if player.club:
                            club_registration = PlayerClubRegistration.objects.create(
                                player=player,
                                club=player.club,
                                status='PENDING'
                            )
                            
                            # Create club registration invoice
                            club_invoice = create_club_registration_invoice(
                                player=player,
                                club=player.club,
                                amount=200.00
                            )
                        
                        if club_invoice:
                            messages.success(request, _(
                                f'Player registration submitted successfully. '
                                f'Membership invoice (#{membership_invoice.invoice_number}) and '
                                f'club registration invoice (#{club_invoice.invoice_number}) have been generated.'
                            ))
                        else:
                            messages.success(request, _(
                                f'Player registration submitted successfully. '
                                f'Membership invoice (#{membership_invoice.invoice_number}) has been generated.'
                            ))
                    
                    else:  # General Member
                        # Create a regular Member
                        member = Member()
                        
                        # Copy form data to member
                        for field_name in form.cleaned_data:
                            if hasattr(member, field_name) and field_name != 'registration_as':
                                setattr(member, field_name, form.cleaned_data[field_name])
                        
                        member.status = 'PENDING'
                        member.member_type = 'SENIOR'
                        
                        if not member.email:
                            member.email = generate_unique_player_email(member.first_name, member.last_name)
                        
                        member.save()
                        
                        # Create general membership invoice
                        membership_invoice = create_membership_invoice(
                            member=member,
                            amount=100.00,
                            description='National Federation Membership Fee'
                        )
                        
                        messages.success(request, _(
                            f'General membership application submitted successfully. '
                            f'Membership invoice (#{membership_invoice.invoice_number}) has been generated.'
                        ))

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
    """Club admin adds a player - always creates Player with club registration"""
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
                with transaction.atomic():
                    # Create the player
                    player = Player()
                    
                    # Copy form data to player
                    for field_name in player_form.cleaned_data:
                        if hasattr(player, field_name):
                            setattr(player, field_name, player_form.cleaned_data[field_name])
                    
                    player.status = 'PENDING'
                    player.member_type = 'SENIOR'  # Assume senior for club admin registration
                    player.club = request.user.club  # Set the club
                    
                    # Set geography from club if not provided
                    if player.club and player.club.localfootballassociation:
                        if not player.lfa:
                            player.lfa = player.club.localfootballassociation
                        if not player.region and player.club.localfootballassociation.region:
                            player.region = player.club.localfootballassociation.region
                        if not player.province and player.club.localfootballassociation.region and player.club.localfootballassociation.region.province:
                            player.province = player.club.localfootballassociation.region.province
                    
                    if not player.email:
                        player.email = generate_unique_player_email(player.first_name, player.last_name)
                    
                    # Generate SAFA ID if not exists (handled in model save)
                    player.save()

                    # Create membership invoice (national federation fee)
                    membership_invoice = create_membership_invoice(
                        member=player,
                        amount=100.00,
                        description='National Federation Membership Fee'
                    )

                    # Create club registration
                    club_registration = PlayerClubRegistration.objects.create(
                        player=player,
                        club=request.user.club,
                        status='PENDING'
                    )

                    # Create club registration invoice
                    club_invoice = create_club_registration_invoice(
                        player=player,
                        club=request.user.club,
                        amount=200.00
                    )

                    success_message = (
                        f'Player \'{player.first_name} {player.last_name}\' registered successfully with email {player.email}! '
                        f'Membership invoice (#{membership_invoice.invoice_number}) and '
                        f'club registration invoice (#{club_invoice.invoice_number}) have been created. '
                        f'Total fees: R{membership_invoice.amount + club_invoice.amount:.2f}. '
                        f'The player will be eligible for approval once both invoices are paid.'
                    )

                    messages.success(request, success_message)
                    return redirect('accounts:dashboard')

            except Exception as e:
                messages.error(request, f"An unexpected error occurred: {e}")

        else:
            # Form is invalid, display errors
            for field, errors in player_form.errors.items():
                for error in errors:
                    field_label = player_form.fields[field].label if field in player_form.fields else 'Form'
                    messages.error(request, f"{field_label}: {error}")
            messages.warning(request, 'Please correct the errors below.')

    else:
        player_form = ClubAdminPlayerRegistrationForm(request=request)

    return render(request, 'registration/club_admin_add_player.html', {
        'player_form': player_form
    })