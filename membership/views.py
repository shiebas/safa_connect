# membership/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone
from .models import Member, Invoice
from accounts.models import CustomUser
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def registration_portal(request):
    """Redirects to the main user registration page."""
    return redirect('accounts:user_registration')

def registration_success(request):
    """Registration success page"""
    context = {
        'title': 'Registration Successful',
    }
    return render(request, 'membership/registration_success.html', context)


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


def generate_invoice_pdf(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    template_path = 'membership/invoice_template.html'
    context = {'invoice': invoice}

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(
       html, dest=response)
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

from .safa_config_models import SAFASeasonConfig
from .forms import SAFASeasonConfigForm
from django.contrib.auth.decorators import login_required, user_passes_test

def is_national_admin(user):
    return user.is_authenticated and user.role == 'ADMIN_NATIONAL'

@login_required
@user_passes_test(is_national_admin)
def season_list(request):
    seasons = SAFASeasonConfig.objects.all().order_by('-season_year')
    context = {
        'seasons': seasons,
        'title': 'Manage Season Configurations'
    }
    return render(request, 'membership/season_list.html', context)

@login_required
@user_passes_test(is_national_admin)
def add_season_config(request):
    if request.method == 'POST':
        form = SAFASeasonConfigForm(request.POST)
        if form.is_valid():
            season_config = form.save(commit=False)
            season_config.created_by = request.user
            season_config.save()
            messages.success(request, 'Season configuration added successfully.')
            return redirect('membership:season_list')
    else:
        form = SAFASeasonConfigForm()
    context = {
        'form': form,
        'title': 'Add New Season Configuration'
    }
    return render(request, 'membership/add_season_config.html', context)

@login_required
@user_passes_test(is_national_admin)
def edit_season_config(request, pk):
    instance = get_object_or_404(SAFASeasonConfig, pk=pk)
    if request.method == 'POST':
        form = SAFASeasonConfigForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Season configuration updated successfully.')
            return redirect('membership:season_list')
    else:
        form = SAFASeasonConfigForm(instance=instance)
    context = {
        'form': form,
        'title': 'Edit Season Configuration'
    }
    return render(request, 'membership/edit_season_config.html', context)


@login_required
def export_profile_pdf(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    template_path = 'membership/membership_profile_export_pdf.html'
    context = {'user': user}

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{user.safa_id}_profile.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(
       html, dest=response)

    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response
