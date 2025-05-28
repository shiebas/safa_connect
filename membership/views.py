from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from .models import Member, Player
from .forms import MemberForm, PlayerForm

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class MemberListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Member
    template_name = 'membership/member_list.html'
    context_object_name = 'members'
    paginate_by = 10

class MemberCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Member
    form_class = MemberForm
    template_name = 'membership/member_form.html'
    success_url = reverse_lazy('membership:member-list')

    def form_valid(self, form):
        messages.success(self.request, _('Member created successfully.'))
        return super().form_valid(form)

class MemberUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Member
    form_class = MemberForm
    template_name = 'membership/member_form.html'
    success_url = reverse_lazy('membership:member-list')

    def form_valid(self, form):
        messages.success(self.request, _('Member updated successfully.'))
        return super().form_valid(form)

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
