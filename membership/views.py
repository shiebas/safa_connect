# membership/views.py
from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import PlayerRegistrationForm, OfficialRegistrationForm, AdminRegistrationForm
from .models import Member
from accounts.models import CustomUser

def registration_portal(request):
    """Registration portal with different registration options"""
    context = {
        'title': 'SAFA Registration Portal',
    }
    return render(request, 'membership/registration_portal.html', context)

class PlayerRegistrationView(CreateView):
    model = Member
    form_class = PlayerRegistrationForm
    template_name = 'membership/player_registration.html'
    success_url = reverse_lazy('membership:registration_success')

    def form_valid(self, form):
        # Create CustomUser and Member objects
        user = CustomUser.objects.create_user(
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            role='PLAYER'
        )
        member = form.save(commit=False)
        member.user = user
        member.save()
        return redirect(self.success_url)

class OfficialRegistrationView(CreateView):
    model = Member
    form_class = OfficialRegistrationForm
    template_name = 'membership/official_registration.html'
    success_url = reverse_lazy('membership:registration_success')

    def form_valid(self, form):
        # Create CustomUser and Member objects
        user = CustomUser.objects.create_user(
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            role='OFFICIAL'
        )
        member = form.save(commit=False)
        member.user = user
        member.save()
        return redirect(self.success_url)

class AdminRegistrationView(CreateView):
    model = Member
    form_class = AdminRegistrationForm
    template_name = 'membership/admin_registration.html'
    success_url = reverse_lazy('membership:registration_success')

    def form_valid(self, form):
        # Create CustomUser and Member objects
        user = CustomUser.objects.create_user(
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            role=form.cleaned_data['role']
        )
        member = form.save(commit=False)
        member.user = user
        member.save()
        return redirect(self.success_url)

def registration_success(request):
    return render(request, 'membership/registration_success.html')