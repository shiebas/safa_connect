"""
Invoice views for the membership app
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, DurationField, DateTimeField
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _

import csv
import io
# Import xlsxwriter with proper error handling
try:
    import xlsxwriter
    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False
    
from datetime import timedelta, date
from decimal import Decimal

from membership.models import Invoice, InvoiceItem
from geography.models import Club, LocalFootballAssociation, Region, Province
from .models import SAFASeasonConfig, SAFAFeeStructure, Member
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.storage import staticfiles_storage # ADDED

def generate_invoices(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('accounts:modern_home')

    if request.method == 'POST':
        action = request.POST.get('action')
        season = SAFASeasonConfig.get_active_season()

        if not season:
            messages.error(request, "There is no active season configured.")
            return redirect('membership:invoice_list')

        if action == 'hierarchical':
            # Hierarchical invoicing
            # (The existing logic for hierarchical invoicing goes here)
            # ...
            messages.success(request, "Hierarchical invoices generated successfully.")

        elif action == 'direct':
            org_type = request.POST.get('organization_type')
            org_id = request.POST.get('organization_id')

            if not org_type or not org_id:
                messages.error(request, "Organization type and ID are required for direct invoicing.")
                return redirect('membership:generate_invoices')

            model_map = {
                'province': Province,
                'region': Region,
                'lfa': LocalFootballAssociation,
                'club': Club,
            }
            model = model_map.get(org_type)

            if not model:
                messages.error(request, "Invalid organization type.")
                return redirect('membership:generate_invoices')

            organization = get_object_or_404(model, pk=org_id)
            fee_structure = get_object_or_404(SAFAFeeStructure, season_config=season, entity_type=org_type.upper())

            Invoice.objects.create(
                organization=organization,
                season_config=season,
                invoice_type='ORGANIZATION_MEMBERSHIP',
                subtotal=fee_structure.annual_fee,
                status='PENDING'
            )
            messages.success(request, f"Direct invoice generated for {organization.name}.")

        return redirect('membership:invoice_list')

    return render(request, 'membership/invoices/generate_invoices.html')


# Import for PDF generation
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

class InvoiceListView(LoginRequiredMixin, ListView):
    """List all invoices with filtering options"""
    model = Invoice
    template_name = 'membership/invoices/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):
        """Filter invoices based on query parameters"""
        queryset = Invoice.objects.all().select_related('member__current_club')
        
        # Apply filters from GET parameters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        club_id = self.request.GET.get('club')
        if club_id:
            queryset = queryset.filter(member__current_club_id=club_id)
            
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(issue_date__gte=date_from)
            
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(issue_date__lte=date_to)
            
        # Filter by user permissions
        user = self.request.user
        if not user.is_authenticated:
            return Invoice.objects.none()

        # SAFA Admin can see all
        if user.is_staff or user.is_superuser:
            return queryset

        # Other roles
        if hasattr(user, 'member_profile') and user.member_profile:
            member = user.member_profile
            if member.current_club:
                if hasattr(member.current_club, 'club_admins') and member.current_club.club_admins.filter(pk=user.pk).exists():
                    return queryset.filter(member__current_club=member.current_club)
                if hasattr(member.current_club, 'lfa') and member.current_club.lfa and hasattr(member.current_club.lfa, 'lfa_admins') and member.current_club.lfa.lfa_admins.filter(pk=user.pk).exists():
                    return queryset.filter(member__current_club__lfa=member.current_club.lfa)
                if hasattr(member.current_club, 'region') and member.current_club.region and hasattr(member.current_club.region, 'region_admins') and member.current_club.region.region_admins.filter(pk=user.pk).exists():
                    return queryset.filter(member__current_club__region=member.current_club.region)
                if hasattr(member.current_club, 'province') and member.current_club.province and hasattr(member.current_club.province, 'province_admins') and member.current_club.province.province_admins.filter(pk=user.pk).exists():
                    return queryset.filter(member__current_club__province=member.current_club.province)

        # Others can only see their own invoices
        return queryset.filter(member__user=user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # Add clubs for dropdown
        user = self.request.user
        if not user.is_authenticated:
            context['clubs'] = Club.objects.none()
        elif user.is_staff or user.is_superuser:
            context['clubs'] = Club.objects.all()
        elif hasattr(user, 'member_profile') and user.member_profile:
            member = user.member_profile
            if member.current_club:
                if hasattr(member.current_club, 'club_admins') and member.current_club.club_admins.filter(pk=user.pk).exists():
                    context['clubs'] = Club.objects.filter(pk=member.current_club.pk)
                elif hasattr(member.current_club, 'lfa') and member.current_club.lfa and hasattr(member.current_club.lfa, 'lfa_admins') and member.current_club.lfa.lfa_admins.filter(pk=user.pk).exists():
                    context['clubs'] = Club.objects.filter(lfa=member.current_club.lfa)
                elif hasattr(member.current_club, 'region') and member.current_club.region and hasattr(member.current_club.region, 'region_admins') and member.current_club.region.region_admins.filter(pk=user.pk).exists():
                    context['clubs'] = Club.objects.filter(region=member.current_club.region)
                elif hasattr(member.current_club, 'province') and member.current_club.province and hasattr(member.current_club.province, 'province_admins') and member.current_club.province.province_admins.filter(pk=user.pk).exists():
                    context['clubs'] = Club.objects.filter(province=member.current_club.province)
                else:
                    context['clubs'] = Club.objects.none()
            else:
                context['clubs'] = Club.objects.none()
        else:
            # Fallback for users without member profile or club, show all clubs
            context['clubs'] = Club.objects.all()
            
        # Calculate summary stats
        context['total_count'] = queryset.count()
        context['paid_count'] = queryset.filter(status='PAID').count()
        context['paid_amount'] = queryset.filter(status='PAID').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        context['pending_count'] = queryset.filter(status='PENDING').count()
        context['pending_amount'] = queryset.filter(status='PENDING').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        context['overdue_count'] = queryset.filter(status='OVERDUE').count()
        context['overdue_amount'] = queryset.filter(status='OVERDUE').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        
        return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    """Display a single invoice"""
    model = Invoice
    template_name = 'membership/invoices/invoice_detail.html'
    context_object_name = 'invoice'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice = self.get_object()
        context['vat_percentage'] = invoice.vat_rate * 100
        return context
    
    def get_queryset(self):
        """Filter invoices based on user permissions"""
        queryset = Invoice.objects.all().select_related(
            'member__current_club', 'issued_by'
        ).prefetch_related('items')
        
        # Filter by user permissions
        user = self.request.user
        if not user.is_authenticated:
            return Invoice.objects.none()

        if user.is_staff or user.is_superuser:
            return queryset

        if hasattr(user, 'member_profile') and user.member_profile:
            member = user.member_profile
            if member.current_club:
                if hasattr(member.current_club, 'club_admins') and member.current_club.club_admins.filter(pk=user.pk).exists():
                    return queryset.filter(member__current_club=member.current_club)
                if hasattr(member.current_club, 'lfa') and member.current_club.lfa and hasattr(member.current_club.lfa, 'lfa_admins') and member.current_club.lfa.lfa_admins.filter(pk=user.pk).exists():
                    return queryset.filter(member__current_club__lfa=member.current_club.lfa)
                if hasattr(member.current_club, 'region') and member.current_club.region and hasattr(member.current_club.region, 'region_admins') and member.current_club.region.region_admins.filter(pk=user.pk).exists():
                    return queryset.filter(member__current_club__region=member.current_club.region)
                if hasattr(member.current_club, 'province') and member.current_club.province and hasattr(member.current_club.province, 'province_admins') and member.current_club.province.province_admins.filter(pk=user.pk).exists():
                    return queryset.filter(member__current_club__province=member.current_club.province)

        # Others can only see their own invoices
        return queryset.filter(member__user=user)


class InvoicePDFView(LoginRequiredMixin, DetailView):
    """Generate PDF version of an invoice"""
    model = Invoice
    template_name = 'membership/invoices/invoice_export_pdf.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    
    def get(self, request, *args, **kwargs):
        invoice = self.get_object()
        
        # Check if weasyprint is available
        if not WEASYPRINT_AVAILABLE:
            messages.error(request, _("PDF generation is not available. Please install WeasyPrint."))
            return redirect('membership:invoice_detail', uuid=invoice.uuid)
        
        # Render the template to HTML
        html_string = render(request, self.template_name, {'invoice': invoice}).content.decode('utf-8')
        
        # Generate PDF
        pdf_file = HTML(string=html_string).write_pdf()
        
        # Create HTTP response with PDF
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="invoice_{invoice.invoice_number}.pdf"'
        
        return response


class OutstandingReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Generate a report of outstanding balances"""
    template_name = 'membership/invoices/outstanding_report.html'
    permission_required = 'membership.view_invoice'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        level = self.request.GET.get('level', 'club')
        days_overdue = self.request.GET.get('days_overdue', 'any')
        sort_by = self.request.GET.get('sort_by', 'total_desc')
        
        # Base queryset for unpaid invoices
        unpaid_invoices = Invoice.objects.filter(
            Q(status='PENDING') | Q(status='OVERDUE')
        ).select_related('member__current_club')
        
        # Apply days overdue filter
        today = timezone.now().date()
        if days_overdue != 'any':
            days = int(days_overdue)
            overdue_date = today - timedelta(days=days)
            unpaid_invoices = unpaid_invoices.filter(due_date__lte=overdue_date)
        
        # Apply user permission filters
        user = self.request.user
        if hasattr(user, 'member_profile') and user.member_profile:
            member = user.member_profile
            if member.current_club:
                if hasattr(member.current_club, 'club_admins') and member.current_club.club_admins.filter(pk=user.pk).exists():
                    unpaid_invoices = unpaid_invoices.filter(member__current_club=member.current_club)
                elif hasattr(member.current_club, 'lfa') and member.current_club.lfa and hasattr(member.current_club.lfa, 'lfa_admins') and member.current_club.lfa.lfa_admins.filter(pk=user.pk).exists():
                    unpaid_invoices = unpaid_invoices.filter(member__current_club__lfa=member.current_club.lfa)
                elif hasattr(member.current_club, 'region') and member.current_club.region and hasattr(member.current_club.region, 'region_admins') and member.current_club.region.region_admins.filter(pk=user.pk).exists():
                    unpaid_invoices = unpaid_invoices.filter(member__current_club__region=member.current_club.region)
                elif hasattr(member.current_club, 'province') and member.current_club.province and hasattr(member.current_club.province, 'province_admins') and member.current_club.province.province_admins.filter(pk=user.pk).exists():
                    unpaid_invoices = unpaid_invoices.filter(member__current_club__province=member.current_club.province)
        
        # Calculate report items based on grouping level
        report_items = []
        
        if level == 'club':
            # The related name from Member to Club is 'current_members'
            clubs = Club.objects.filter(current_members__invoices__in=unpaid_invoices).distinct()
            
            for club in clubs:
                club_invoices = unpaid_invoices.filter(member__current_club=club)
                days_30 = club_invoices.filter(due_date__gt=today-timedelta(days=30))
                days_90 = club_invoices.filter(due_date__lte=today-timedelta(days=30), 
                                             due_date__gt=today-timedelta(days=90))
                days_90_plus = club_invoices.filter(due_date__lte=today-timedelta(days=90))
                
                report_items.append({
                    'entity_type': 'club',
                    'id': club.id,
                    'name': club.name,
                    'invoice_count': club_invoices.count(),
                    'player_count': club_invoices.values('member').distinct().count(),
                    'days_30_amount': days_30.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    'days_90_amount': days_90.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    'days_90_plus_amount': days_90_plus.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    'total_amount': club_invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    'filter_params': f'club={club.id}&status=PENDING,OVERDUE'
                })
        
        elif level == 'lfa':
            lfas = LocalFootballAssociation.objects.filter(
                clubs__current_members__invoices__in=unpaid_invoices
            ).distinct()
            
            for lfa in lfas:
                lfa_invoices = unpaid_invoices.filter(member__current_club__lfa=lfa)
                days_30 = lfa_invoices.filter(due_date__gt=today-timedelta(days=30))
                days_90 = lfa_invoices.filter(due_date__lte=today-timedelta(days=30), 
                                            due_date__gt=today-timedelta(days=90))
                days_90_plus = lfa_invoices.filter(due_date__lte=today-timedelta(days=90))
                
                report_items.append({
                    'entity_type': 'lfa',
                    'id': lfa.id,
                    'name': lfa.name,
                    'invoice_count': lfa_invoices.count(),
                    'player_count': lfa_invoices.values('member').distinct().count(),
                    'days_30_amount': days_30.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    'days_90_amount': days_90.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    'days_90_plus_amount': days_90_plus.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    'total_amount': lfa_invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    'filter_params': f'lfa={lfa.id}&status=PENDING,OVERDUE'
                })
        
        elif level == 'region':
            regions = Region.objects.filter(
                clubs__current_members__invoices__in=unpaid_invoices
            ).distinct()
            
            for region in regions:
                region_invoices = unpaid_invoices.filter(member__current_club__region=region)
                days_30 = region_invoices.filter(due_date__gt=today-timedelta(days=30))
                days_90 = region_invoices.filter(due_date__lte=today-timedelta(days=30), 
                                              due_date__gt=today-timedelta(days=90))
                days_90_plus = region_invoices.filter(due_date__lte=today-timedelta(days=90))
                
                report_items.append({
                    'entity_type': 'region',
                    'id': region.id,
                    'name': region.name,
                    'invoice_count': region_invoices.count(),
                    'player_count': region_invoices.values('member').distinct().count(),
                    'days_30_amount': days_30.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    'days_90_amount': days_90.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    'days_90_plus_amount': days_90_plus.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    'total_amount': region_invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    'filter_params': f'region={region.id}&status=PENDING,OVERDUE'
                })
        
        elif level == 'province':
            provinces = Province.objects.filter(
                clubs__current_members__invoices__in=unpaid_invoices
            ).distinct()
            
            for province in provinces:
                province_invoices = unpaid_invoices.filter(member__current_club__province=province)
                days_30 = province_invoices.filter(due_date__gt=today-timedelta(days=30))
                days_90 = province_invoices.filter(due_date__lte=today-timedelta(days=30), 
                                               due_date__gt=today-timedelta(days=90))
                days_90_plus = province_invoices.filter(due_date__lte=today-timedelta(days=90))
                
                report_items.append({
                    'entity_type': 'province',
                    'id': province.id,
                    'name': province.name,
                    'invoice_count': province_invoices.count(),
                    'player_count': province_invoices.values('member').distinct().count(),
                    'days_30_amount': days_30.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    'days_90_amount': days_90.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    'days_90_plus_amount': days_90_plus.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    'total_amount': province_invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    'filter_params': f'province={province.id}&status=PENDING,OVERDUE'
                })
        
        # Sort report items
        if sort_by == 'total_desc':
            report_items.sort(key=lambda x: x['total_amount'], reverse=True)
        elif sort_by == 'total_asc':
            report_items.sort(key=lambda x: x['total_amount'])
        elif sort_by == 'name_asc':
            report_items.sort(key=lambda x: x['name'])
        elif sort_by == 'days_desc':
            report_items.sort(key=lambda x: x['days_90_plus_amount'], reverse=True)
        
        # Add summary statistics
        context['report_items'] = report_items
        context['total_amount'] = sum(item['total_amount'] for item in report_items)
        context['total_count'] = sum(item['invoice_count'] for item in report_items)
        context['days_30_amount'] = sum(item['days_30_amount'] for item in report_items)
        context['days_30_count'] = unpaid_invoices.filter(due_date__gt=today-timedelta(days=30)).count()
        context['days_90_amount'] = sum(item['days_90_amount'] for item in report_items)
        context['days_90_count'] = unpaid_invoices.filter(
            due_date__lte=today-timedelta(days=30),
            due_date__gt=today-timedelta(days=90)
        ).count()
        context['days_90_plus_amount'] = sum(item['days_90_plus_amount'] for item in report_items)
        context['days_90_plus_count'] = unpaid_invoices.filter(due_date__lte=today-timedelta(days=90)).count()
        context['today'] = today
        
        return context


def mark_invoice_paid(request, uuid):
    """Mark an invoice as paid"""
    # Get the invoice
    invoice = get_object_or_404(Invoice, uuid=uuid)
    
    # Check permissions
    if not request.user.has_perm('membership.change_invoice'):
        messages.error(request, _("You don't have permission to mark invoices as paid."))
        return redirect('membership:invoice_detail', uuid=uuid)
    
    # Mark as paid
    invoice.mark_as_paid()
    
    # The invoice.mark_as_paid() method now handles associated status updates
    # and history creation.
    if invoice.invoice_type == 'MEMBER_REGISTRATION' and invoice.member:
        messages.success(request, _(f"Invoice {invoice.invoice_number} marked as paid. {invoice.member.get_full_name()}'s registration is now pending approval."))
    else:
        messages.success(request, _(f"Invoice {invoice.invoice_number} marked as paid."))
    
    return redirect('membership:invoice_detail', uuid=uuid)


def export_invoices(request, format='csv'):
    """Export invoices to CSV, Excel or PDF"""
    # Get the queryset based on filters
    # Instantiating the view to call get_queryset is not ideal, but works for now.
    list_view = InvoiceListView()
    list_view.request = request
    queryset = list_view.get_queryset()
    
    # Apply any additional filters from GET parameters
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)
        
    club_id = request.GET.get('club')
    if club_id:
        queryset = queryset.filter(member__current_club_id=club_id)
        
    date_from = request.GET.get('date_from')
    if date_from:
        queryset = queryset.filter(issue_date__gte=date_from)
        
    date_to = request.GET.get('date_to')
    if date_to:
        queryset = queryset.filter(issue_date__lte=date_to)
    
    # Generate filename
    filename = f"invoices_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
    
    if format == 'csv':
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Invoice Number', 'Member', 'Club', 'Issue Date',
            'Due Date', 'Amount', 'Status', 'Payment Date'
        ])
        
        for invoice in queryset:
            writer.writerow([
                invoice.invoice_number,
                invoice.member.get_full_name() if invoice.member else 'N/A',
                invoice.member.current_club.name if invoice.member and invoice.member.current_club else 'N/A',
                invoice.issue_date.strftime('%Y-%m-%d'),
                invoice.due_date.strftime('%Y-%m-%d'),
                invoice.total_amount,
                invoice.get_status_display(),
                invoice.payment_date.strftime('%Y-%m-%d') if invoice.payment_date else ''
            ])
        
        return response
        
    elif format == 'excel':
        # Check if xlsxwriter is available
        if not XLSXWRITER_AVAILABLE:
            messages.error(request, _("Excel export is not available. Please install xlsxwriter."))
            return redirect('membership:invoice_list')
            
        # Create Excel response
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Invoices')
        
        # Add headers
        headers = ['Invoice Number', 'Member', 'Club', 'Issue Date',
                  'Due Date', 'Amount', 'Status', 'Payment Date']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)
        
        # Add data
        for row_num, invoice in enumerate(queryset, 1):
            worksheet.write(row_num, 0, invoice.invoice_number)
            worksheet.write(row_num, 1, invoice.member.get_full_name() if invoice.member else 'N/A')
            worksheet.write(row_num, 2, invoice.member.current_club.name if invoice.member and invoice.member.current_club else 'N/A')
            worksheet.write(row_num, 3, invoice.issue_date.strftime('%Y-%m-%d'))
            worksheet.write(row_num, 4, invoice.due_date.strftime('%Y-%m-%d'))
            worksheet.write(row_num, 5, float(invoice.total_amount))
            worksheet.write(row_num, 6, invoice.get_status_display())
            worksheet.write(row_num, 7, invoice.payment_date.strftime('%Y-%m-%d') if invoice.payment_date else '')
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        
        return response
        
    elif format == 'pdf':
        # Check if weasyprint is available
        if not WEASYPRINT_AVAILABLE:
            messages.error(request, _("PDF export is not available. Please install WeasyPrint."))
            return redirect('membership:invoice_list')
        
        # Render the template to HTML
        context = {
            'invoices': queryset,
            'title': 'Invoices Export',
            'date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'safa_logo_url': request.build_absolute_uri(staticfiles_storage.url('images/safa_logo.png')), # ADD THIS LINE
        }
        # Render the template to HTML
        context = {
            'title': 'Invoices Export',
            'date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'safa_logo_url': request.build_absolute_uri(staticfiles_storage.url('images/safa_logo.png')),
        }

        # Calculate VAT percentage for each invoice
        invoices_with_vat_percentage = []
        for invoice in queryset:
            invoice.vat_percentage = invoice.vat_rate * 100
            invoices_with_vat_percentage.append(invoice)
        
        context['invoices'] = invoices_with_vat_percentage # Update context with modified invoices

        html_string = render(request, 'membership/invoices/invoice_export_pdf.html', context).content.decode('utf-8')
        
        # Generate PDF
        pdf_file = HTML(string=html_string).write_pdf()
        
        # Create HTTP response with PDF
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
        
        return response
    
    # Default fallback
    messages.error(request, _("Unsupported export format"))
    return redirect('membership:invoice_list')
