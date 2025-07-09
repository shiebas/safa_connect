from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .models import Member, Player, Membership, MembershipApplication
from geography.models import Club, Province, Region, LocalFootballAssociation  # Import Club from geography
from .forms import MemberForm, PlayerForm, ClubForm, MembershipApplicationForm
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponseRedirect
from rest_framework import viewsets
from .serializers import MemberSerializer

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

# Member views
class MemberListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Member
    template_name = 'membership/member_list.html'
    context_object_name = 'members'
    paginate_by = 10

class MemberCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Member
    form_class = MemberForm
    template_name = 'membership/member_form.html'
    success_url = reverse_lazy('membership:member_list')

    def form_valid(self, form):
        messages.success(self.request, _('Member created successfully.'))
        return super().form_valid(form)

class MemberUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Member
    form_class = MemberForm
    template_name = 'membership/member_form.html'
    success_url = reverse_lazy('membership:member_list')

    def form_valid(self, form):
        messages.success(self.request, _('Member updated successfully.'))
        return super().form_valid(form)

# Player views
class PlayerListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Player
    template_name = 'membership/player_list.html'
    context_object_name = 'players'
    paginate_by = 10

class PlayerCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Player
    form_class = PlayerForm
    template_name = 'membership/player_form.html'
    success_url = reverse_lazy('membership:player-list')

    def form_valid(self, form):
        messages.success(self.request, _('Player created successfully.'))
        return super().form_valid(form)

class PlayerUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Player
    form_class = PlayerForm
    template_name = 'membership/player_form.html'
    success_url = reverse_lazy('membership:player-list')

    def form_valid(self, form):
        messages.success(self.request, _('Player updated successfully.'))
        return super().form_valid(form)

# Club views
class ClubListView(LoginRequiredMixin, ListView):
    model = Club  # Now uses Club from geography
    template_name = 'membership/club/club_list.html'
    context_object_name = 'clubs'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Club.objects.all().order_by('name')
        # Only show clubs the user can access
        member = getattr(user, 'member_profile', None)
        if member:
            return Club.objects.all().filter(
                id__in=[club.id for club in Club.objects.all() if member.can_access_club(club)]
            ).order_by('name')
        return Club.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_create_club'] = self.request.user.is_staff or (
            hasattr(self.request.user, 'member_profile') and self.request.user.member_profile.role == 'ADMIN_LOCAL_FED'
        )
        return context

class ClubDetailView(LoginRequiredMixin, DetailView):
    model = Club  # Now uses Club from geography
    template_name = 'membership/club/club_detail.html'
    context_object_name = 'club'

    def get(self, request, *args, **kwargs):
        club = self.get_object()
        member = getattr(request.user, 'member_profile', None)
        if not (request.user.is_staff or (member and member.can_access_club(club))):
            raise PermissionDenied("You do not have permission to view this club.")
        return super().get(request, *args, **kwargs)

class ClubCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Club  # Now uses Club from geography
    form_class = ClubForm
    template_name = 'membership/club/club_form.html'
    success_url = reverse_lazy('membership:club_list')

    def form_valid(self, form):
        messages.success(self.request, _('Club created successfully.'))
        return super().form_valid(form)

class ClubUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Club  # Now uses Club from geography
    form_class = ClubForm
    template_name = 'membership/club/club_form.html'
    success_url = reverse_lazy('membership:club_list')

    def test_func(self):
        # Allow staff and club admins of this club
        if self.request.user.is_staff:
            return True
        return self.get_object().member_set.filter(user=self.request.user, role='CLUB_ADMIN').exists()

    def form_valid(self, form):
        messages.success(self.request, _('Club updated successfully.'))
        return super().form_valid(form)

# Membership views
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# Membership
@method_decorator(login_required, name='dispatch')
class MembershipListView(ListView):
    model = Membership
    template_name = 'membership/membership_list.html'
    context_object_name = 'memberships'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            # Filter memberships based on user's role and permissions
            member = getattr(self.request.user, 'member_profile', None)
            if member and getattr(member, 'role', None) == 'CLUB_ADMIN':
                queryset = queryset.filter(club=member.club)
        return queryset

@method_decorator(login_required, name='dispatch')
class MembershipCreateView(CreateView):
    model = Membership
    template_name = 'membership/membership_form.html'
    fields = ['member', 'club', 'start_date', 'end_date', 'status']
    success_url = reverse_lazy('membership:membership-list')

@method_decorator(login_required, name='dispatch')
class MembershipDetailView(DetailView):
    model = Membership
    template_name = 'membership/membership_detail.html'
    context_object_name = 'membership'

@method_decorator(login_required, name='dispatch')
class MembershipUpdateView(UpdateView):
    model = Membership
    template_name = 'membership/membership_form.html'
    fields = ['member', 'club', 'start_date', 'end_date', 'status']
    success_url = reverse_lazy('membership:membership-list')

@method_decorator(login_required, name='dispatch')
class MembershipDeleteView(DeleteView):
    model = Membership
    template_name = 'membership/membership_confirm_delete.html'
    success_url = reverse_lazy('membership:membership-list')

# API Views
def regions_by_province(request, province_id):
    """API endpoint to get regions for a given province"""
    province = get_object_or_404(Province, pk=province_id)
    regions = Region.objects.filter(province=province).values('id', 'name')
    return JsonResponse(list(regions), safe=False)

def lfas_by_region(request, region_id):
    lfas = LocalFootballAssociation.objects.filter(region_id=region_id).values('id', 'name')
    return JsonResponse(list(lfas), safe=False)

# Payment Processing Views
class PaymentReturnView(LoginRequiredMixin, View):
    """
    Handle successful returns from payment processor.
    This view processes the payment confirmation and updates relevant records.
    """
    def get(self, request, *args, **kwargs):
        # Get payment reference from request
        payment_ref = request.GET.get('reference', '')
        
        # TODO: Process the payment confirmation
        # Implement payment verification logic here
        # Update relevant invoice or payment records
        
        messages.success(request, _("Payment processed successfully."))
        return HttpResponseRedirect(reverse_lazy('membership:registration_success'))
        
    def post(self, request, *args, **kwargs):
        # Handle POST callbacks from payment processor
        # Similar logic as GET but for POST data
        return self.get(request, *args, **kwargs)

class PaymentCancelView(LoginRequiredMixin, TemplateView):
    """
    Handle cancelled payments from payment processor.
    """
    template_name = 'membership/payment_cancel.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Payment Cancelled")
        context['message'] = _("Your payment was cancelled. Please try again or contact support if you need assistance.")
        # Generate a reference for unfinished registrations
        context['registration_reference'] = f"REF-{timezone.now().strftime('%Y%m%d')}-{self.request.user.id}"
        return context

class ProcessCardPaymentView(LoginRequiredMixin, View):
    """
    Process card payments and redirect to payment processor.
    """
    def post(self, request, uuid, *args, **kwargs):
        # Logic for initiating card payment process
        # TODO: Implement integration with payment processor
        
        # Placeholder - redirect to payment gateway
        return HttpResponseRedirect(reverse_lazy('membership:payment_return'))

@login_required
def send_payment_reminder(request, entity_type, entity_id):
    """
    Send payment reminder to a club or player based on entity_type.
    
    Args:
        entity_type: 'club' or 'player'
        entity_id: ID of the club or player to send reminder to
    """
    from django.core.mail import send_mail
    from .models.invoice import Invoice
    
    success = False
    if entity_type == 'club':
        club = get_object_or_404(Club, pk=entity_id)
        invoices = Invoice.objects.filter(club=club, status__in=['PENDING', 'OVERDUE'])
        if invoices.exists():
            # Get club admin email
            admin_emails = list(Member.objects.filter(
                club=club, 
                role='CLUB_ADMIN'
            ).values_list('email', flat=True))
            
            if admin_emails:
                total_due = sum(invoice.amount for invoice in invoices)
                # Send email to club administrators
                success = send_mail(
                    _('Payment Reminder: Outstanding Invoices'),
                    _(f'Your club has {invoices.count()} outstanding invoices totaling R{total_due:.2f} ZAR. '
                      f'Please log in to the system to view and settle these invoices.'),
                    'noreply@safaglobal.org',
                    admin_emails,
                    fail_silently=False,
                )
                
    elif entity_type == 'player':
        player = get_object_or_404(Player, pk=entity_id)
        invoices = Invoice.objects.filter(player=player, status__in=['PENDING', 'OVERDUE'])
        
        if invoices.exists() and player.email:
            total_due = sum(invoice.amount for invoice in invoices)
            # Send email to player
            success = send_mail(
                _('Payment Reminder: Outstanding Invoices'),
                _(f'You have {invoices.count()} outstanding invoices totaling R{total_due:.2f} ZAR. '
                  f'Please log in to the system to view and settle these invoices.'),
                'noreply@safaglobal.org',
                [player.email],
                fail_silently=False,
            )
    
    if success:
        messages.success(
            request, 
            _("Payment reminder sent successfully to {0} {1}").format(
                entity_type, 
                Club.objects.get(pk=entity_id).name if entity_type == 'club' else Player.objects.get(pk=entity_id).get_full_name()
            )
        )
    else:
        messages.error(
            request, 
            _("Could not send payment reminder. Please check if the recipient has a valid email address.")
        )
    
    # Redirect to the referring page if available
    return redirect(request.META.get('HTTP_REFERER', reverse_lazy('membership:outstanding_report')))

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

def membership_application(request):
    from django.core.files.base import ContentFile
    import base64
    from .models import Member
    from geography.models import Club, Province, Region, LocalFootballAssociation  # Add other FK models if needed

    if request.method == 'POST':
        form = MembershipApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            # Try to find existing member by ID number or email
            member = None
            if cd.get('id_number'):
                member = Member.objects.filter(id_number=cd['id_number']).first()
            if not member and cd.get('email'):
                member = Member.objects.filter(email=cd['email']).first()
            # Prepare member_data for non-FK fields only
            member_fields = [
                'first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'gender', 'id_number',
                'passport_number', 'street_address', 'suburb', 'city', 'postal_code', 'emergency_contact',
                'emergency_phone', 'medical_notes'
            ]
            member_data = {field: cd.get(field) for field in member_fields}
            # Handle ForeignKey fields separately
            club_obj = None
            club_val = cd.get('club')
            if club_val:
                if isinstance(club_val, Club):
                    club_obj = club_val
                else:
                    try:
                        club_obj = Club.objects.get(pk=club_val)
                    except Exception:
                        club_obj = None
            country_obj = None
            country_val = cd.get('country')
            if country_val and hasattr(Member, 'country'):
                try:
                    # Replace with your actual Country model if needed
                    from geography.models import Country
                    country_obj = Country.objects.get(pk=country_val)
                except Exception:
                    country_obj = None
            state_obj = None
            state_val = cd.get('state')
            if state_val and hasattr(Member, 'state'):
                try:
                    # Replace with your actual State/Province model if needed
                    state_obj = Province.objects.get(pk=state_val)
                except Exception:
                    state_obj = None
            # ...add similar logic for other FK fields if present...
            if member:
                for field, value in member_data.items():
                    setattr(member, field, value)
                if request.FILES.get('profile_picture'):
                    member.profile_picture = request.FILES['profile_picture']
            else:
                member = Member(**member_data)
                if request.FILES.get('profile_picture'):
                    member.profile_picture = request.FILES['profile_picture']
            # Assign FK fields after instance creation
            member.club = club_obj
            if hasattr(member, 'country'):
                member.country = country_obj
            if hasattr(member, 'state'):
                member.state = state_obj
            member.save()  # Save or update member after all fields set
            # Now create the MembershipApplication object manually
            app = MembershipApplication()
            app.member = member  # Only assign after member is saved
            app.club = club_obj
            app.popi_consent = cd.get('popi_consent', False)
            # Handle signature image (base64)
            signature_data = cd.get('signature_data')
            if signature_data:
                format, imgstr = signature_data.split(';base64,')
                ext = format.split('/')[-1]
                app.signature.save(
                    f'signature_{member.id_number}.{ext}',
                    ContentFile(base64.b64decode(imgstr)),
                    save=False
                )
            # Save ID document if uploaded
            if request.FILES.get('id_document'):
                app.id_document = request.FILES['id_document']
            app.save()
            return redirect('success_page')
        else:
            # Show form errors as messages for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = MembershipApplicationForm()
    return render(request, 'membership/membership_application.html', {'form': form})