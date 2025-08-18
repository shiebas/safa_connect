# membership/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone
from .forms import PlayerRegistrationForm, OfficialRegistrationForm, AdminRegistrationForm
from .models import Member
from accounts.models import CustomUser
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def registration_portal(request):
    """Registration portal with different registration options"""
    if request.user.is_authenticated:
        return redirect('accounts:home')
    context = {
        'title': 'SAFA Registration Portal',
    }
    return render(request, 'membership/registration_portal.html', context)

def registration_success(request):
    """Registration success page"""
    context = {
        'title': 'Registration Successful',
    }
    return render(request, 'membership/registration_success.html', context)

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

class MemberApprovalListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Member
    template_name = 'membership/member_approval_list.html'
    context_object_name = 'members'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role in ['ADMIN_NATIONAL', 'ADMIN_PROVINCE', 'CLUB_ADMIN']
    
    def get_queryset(self):
        return Member.objects.filter(status='PENDING').order_by('-created')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Member Approvals'
        return context

def approve_member(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    if request.method == 'POST':
        member.status = 'ACTIVE'
        member.approved_by = request.user
        member.approved_date = timezone.now()
        member.save()
        messages.success(request, f'Member {member.get_full_name()} has been approved.')
    return redirect('membership:member_approval_list')

def reject_member(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    if request.method == 'POST':
        member.status = 'REJECTED'
        member.rejection_reason = request.POST.get('reason', '')
        member.save()
        messages.success(request, f'Member {member.get_full_name()} has been rejected.')
    return redirect('membership:member_approval_list')

def generate_membership_card(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    template_path = 'membership/membership_card.html'
    context = {'member': member}

    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{member.safa_id}_card.pdf"'

    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response)
    # if error then show some funy view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response