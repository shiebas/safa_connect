from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from .models import Member, Player, Club, Membership, Province, Region, LocalFootballAssociation
from .forms import MemberForm, PlayerForm, ClubForm
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse

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
    model = Club
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
    model = Club
    template_name = 'membership/club/club_detail.html'
    context_object_name = 'club'

    def get(self, request, *args, **kwargs):
        club = self.get_object()
        member = getattr(request.user, 'member_profile', None)
        if not (request.user.is_staff or (member and member.can_access_club(club))):
            raise PermissionDenied("You do not have permission to view this club.")
        return super().get(request, *args, **kwargs)

class ClubCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Club
    form_class = ClubForm
    template_name = 'membership/club/club_form.html'
    success_url = reverse_lazy('membership:club_list')

    def form_valid(self, form):
        messages.success(self.request, _('Club created successfully.'))
        return super().form_valid(form)

class ClubUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Club
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
    template_name = 'membership_list.html'
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
    template_name = 'membership_form.html'
    fields = '__all__'
    success_url = reverse_lazy('membership-list')

@method_decorator(login_required, name='dispatch')
class MembershipUpdateView(UpdateView):
    model = Membership
    template_name = 'membership_form.html'
    fields = '__all__'
    success_url = reverse_lazy('membership-list')

@method_decorator(login_required, name='dispatch')
class MembershipDeleteView(DeleteView):
    model = Membership
    template_name = 'membership_confirm_delete.html'
    success_url = reverse_lazy('membership-list')

# API Views
def regions_by_province(request, province_id):
    """API endpoint to get regions for a given province"""
    province = get_object_or_404(Province, pk=province_id)
    regions = Region.objects.filter(province=province).values('id', 'name')
    return JsonResponse(list(regions), safe=False)

def lfas_by_region(request, region_id):
    lfas = LocalFootballAssociation.objects.filter(region_id=region_id).values('id', 'name')
    return JsonResponse(list(lfas), safe=False)
