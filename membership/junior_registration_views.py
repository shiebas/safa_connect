from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, TemplateView, ListView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test

from .models import Member, JuniorMember
from .forms import MembershipApplicationForm
from geography.models import Club


class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user is an admin (Superuser, National Admin, or Club Admin)"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Check if user has admin privileges
        if not self.has_admin_access(request.user):
            raise PermissionDenied("You must be an administrator to access this page.")

        return super().dispatch(request, *args, **kwargs)

    def has_admin_access(self, user):
        """Check if user has admin access"""
        return (
                user.is_superuser or
                user.role in ['CLUB_ADMIN', 'ADMIN', 'ADMIN_COUNTRY', 'NATIONAL_ADMIN'] or
                user.is_staff or
                user.groups.filter(name__in=['Club Admin', 'National Admin', 'Superuser']).exists()
        )

    def get_admin_level(self, user):
        """Get the admin level of the user"""
        if user.is_superuser:
            return 'SUPERUSER'
        elif user.role == 'ADMIN_COUNTRY' or user.role == 'NATIONAL_ADMIN':
            return 'NATIONAL_ADMIN'
        elif user.role == 'CLUB_ADMIN':
            return 'CLUB_ADMIN'
        elif user.is_staff:
            return 'STAFF'
        else:
            return 'USER'


class ClubAdminRequiredMixin(AdminRequiredMixin):
    """Mixin to ensure user is a club admin or higher"""

    def has_admin_access(self, user):
        """Check if user has admin access"""
        return (
                user.is_superuser or
                user.role in ['CLUB_ADMIN', 'ADMIN', 'ADMIN_COUNTRY', 'NATIONAL_ADMIN'] or
                user.is_staff or
                user.groups.filter(name__in=['Club Admin', 'National Admin', 'Superuser']).exists()
        )


class NationalAdminRequiredMixin(AdminRequiredMixin):
    """Mixin for national admin and above"""

    def has_admin_access(self, user):
        """National admin and superuser access"""
        return (
                user.is_superuser or
                user.role in ['ADMIN', 'ADMIN_COUNTRY', 'NATIONAL_ADMIN'] or
                user.groups.filter(name__in=['National Admin', 'Superuser']).exists()
        )


class SuperuserRequiredMixin(AdminRequiredMixin):
    """Mixin for superuser only"""

    def has_admin_access(self, user):
        """Superuser only access"""
        return user.is_superuser


class JuniorMemberListView(AdminRequiredMixin, ListView):
    """View to list junior members for admins"""
    model = JuniorMember
    template_name = 'membership/junior_member_list.html'
    context_object_name = 'junior_members'
    paginate_by = 20

    def get_queryset(self):
        """Filter based on admin level"""
        user = self.request.user
        admin_level = self.get_admin_level(user)

        if admin_level == 'SUPERUSER':
            # Superuser can see all junior members
            return JuniorMember.objects.all().order_by('-application_date')
        elif admin_level == 'NATIONAL_ADMIN':
            # National admin can see all junior members
            return JuniorMember.objects.all().order_by('-application_date')
        elif admin_level == 'CLUB_ADMIN':
            # Club admin can only see their club's junior members
            club = self.get_user_club()
            if club:
                return JuniorMember.objects.filter(club=club).order_by('-application_date')
            return JuniorMember.objects.none()
        else:
            return JuniorMember.objects.none()

    def get_user_club(self):
        """Get the club associated with the current user"""
        try:
            return Club.objects.get(admin=self.request.user)
        except Club.DoesNotExist:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Junior Members"
        context['admin_level'] = self.get_admin_level(self.request.user)
        context['club'] = self.get_user_club()
        return context


class ClubAdminDashboardView(AdminRequiredMixin, TemplateView):
    """Dashboard for club administrators"""
    template_name = 'membership/club_admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        admin_level = self.get_admin_level(user)

        if admin_level == 'CLUB_ADMIN':
            club = self.get_user_club()
            if club:
                context.update({
                    'club': club,
                    'total_juniors': JuniorMember.objects.filter(club=club).count(),
                    'pending_juniors': JuniorMember.objects.filter(
                        application_status='PENDING'
                    ).count(),
                    'approved_juniors': JuniorMember.objects.filter(
                        application_status='APPROVED'
                    ).count(),
                    'recent_registrations': JuniorMember.objects.filter(
                        club=club
                    ).order_by('-application_date')[:5],
                })
        elif admin_level in ['SUPERUSER', 'NATIONAL_ADMIN']:
            # For higher level admins, show system-wide stats
            context.update({
                'total_juniors': JuniorMember.objects.count(),
                'pending_juniors': JuniorMember.objects.filter(
                    application_status='PENDING'
                ).count(),
                'approved_juniors': JuniorMember.objects.filter(
                    application_status='APPROVED'
                ).count(),
                'recent_registrations': JuniorMember.objects.order_by('-application_date')[:10],
                'total_clubs': Club.objects.count(),
                'clubs_with_juniors': Club.objects.filter(
                    juniormember__isnull=False
                ).distinct().count(),
            })

        context['admin_level'] = admin_level
        return context

    def get_user_club(self):
        """Get the club associated with the current user"""
        try:
            return Club.objects.get(admin=self.request.user)
        except Club.DoesNotExist:
            return None


class JuniorRegistrationForm(MembershipApplicationForm):
    """Form specifically for registering junior members by club administrators"""

    class Meta(MembershipApplicationForm.Meta):
        model = JuniorMember
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'date_of_birth',
            'gender', 'id_document_type', 'id_number', 'passport_number',
            'street_address', 'suburb', 'city', 'state', 'postal_code', 'country',
            'emergency_contact', 'emergency_phone', 'medical_notes',
            'profile_picture', 'id_document',
            'guardian_name', 'guardian_email', 'guardian_phone', 'school',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make guardian fields required
        self.fields['guardian_name'].required = True
        self.fields['guardian_email'].required = True
        self.fields['guardian_phone'].required = True

        # Hide the is_junior field since this form is specifically for juniors
        if 'is_junior' in self.fields:
            self.fields.pop('is_junior')

        # Add a note about POPIA compliance
        self.fields['guardian_email'].help_text = "Required for POPIA compliance for members under 18"

    def clean(self):
        cleaned_data = super().clean()
        # Force member type to be JUNIOR
        cleaned_data['member_type'] = 'JUNIOR'
        return cleaned_data


class JuniorRegistrationView(AdminRequiredMixin, CreateView):
    """View for administrators to register junior members"""
    model = JuniorMember
    form_class = JuniorRegistrationForm
    template_name = 'membership/junior_registration.html'
    success_url = reverse_lazy('membership:junior_registration_success')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Register Junior Member"
        context['subtitle'] = "For members under 18 years old"
        return context

    def form_valid(self, form):
        with transaction.atomic():
            # Create the junior member
            junior = form.save(commit=False)

            # Set the member type to JUNIOR
            junior.member_type = 'JUNIOR'

            # Mark as registered by admin
            junior.registered_by_admin = True
            junior.registering_admin = self.request.user

            # Save the junior member
            junior.save()

            # Send notification
            self.send_registration_notification(junior)

            messages.success(self.request, f"Junior member {junior.get_full_name()} registered successfully!")

            return super().form_valid(form)

    def send_registration_notification(self, junior):
        """Send notification to guardian about the registration"""
        try:
            subject = "SAFA Junior Membership Registration"
            message = f"""
            Dear {junior.guardian_name},

            A junior membership application has been submitted for {junior.get_full_name()} by a club administrator.

            The application is pending approval by SAFA. You will be notified once it has been reviewed.

            If you have any questions, please contact the club administrator or SAFA directly.

            Best regards,
            SAFA Administration
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [junior.guardian_email],
                fail_silently=True,
            )
        except Exception:
            pass  # Fail silently if email can't be sent


class JuniorRegistrationSuccessView(AdminRequiredMixin, TemplateView):
    """Success page after registering a junior member"""
    template_name = 'membership/junior_registration_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Junior Registration Submitted"
        context['subtitle'] = "The application is pending approval"
        return context


def is_club_admin(user):
    """Check if user is a club admin"""
    return (user.is_authenticated and
            (user.is_staff or
             user.role in ['CLUB_ADMIN', 'ADMIN', 'ADMIN_COUNTRY'] or
             user.groups.filter(name='Club Admin').exists()))


@user_passes_test(is_club_admin)
def junior_registration(request):
    """Function-based view wrapper for junior registration"""
    view = JuniorRegistrationView.as_view()
    return view(request)
