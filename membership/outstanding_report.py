"""
Functions related to the outstanding reports in the invoice system
"""
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Sum
from django.http import HttpResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

import csv
import io
# Import xlsxwriter with proper error handling
try:
    import xlsxwriter
    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False

# Import for PDF generation
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

def export_outstanding_report(request, format='csv'):
    """Export outstanding balance report to CSV, Excel or PDF"""
    # Use the same filters as in OutstandingReportView
    # This would be determined by the query parameters
    from membership.invoice_views import OutstandingReportView
    view = OutstandingReportView()
    view.request = request
    
    # Get data from get_context_data to ensure we use the same filtering logic
    context = view.get_context_data()
    queryset = context.get('clubs_with_balances', [])
    
    filename = f"outstanding_balance_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
    
    if format == 'csv':
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Club', 'Region', 'LFA', 'Total Outstanding'])
        
        for club_data in queryset:
            writer.writerow([
                club_data['club_name'],
                club_data['region_name'],
                club_data['lfa_name'],
                club_data['total_outstanding']
            ])
        
        return response
        
    elif format == 'excel':
        # Check if xlsxwriter is available
        if not XLSXWRITER_AVAILABLE:
            messages.error(request, _("Excel export is not available. Please install xlsxwriter."))
            return redirect('membership:outstanding_report')
            
        # Create Excel response
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Outstanding Balances')
        
        # Add headers
        headers = ['Club', 'Region', 'LFA', 'Total Outstanding']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)
        
        # Add data
        for row_num, club_data in enumerate(queryset, 1):
            worksheet.write(row_num, 0, club_data['club_name'])
            worksheet.write(row_num, 1, club_data['region_name'])
            worksheet.write(row_num, 2, club_data['lfa_name'])
            worksheet.write(row_num, 3, float(club_data['total_outstanding']))
        
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
            return redirect('membership:outstanding_report')
        
        # Render the template to HTML
        context = {
            'clubs_with_balances': queryset,
            'title': 'Outstanding Balance Report',
            'date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        html_string = render(request, 'membership/invoices/outstanding_report_pdf.html', context).content.decode('utf-8')
        
        # Generate PDF
        pdf_file = HTML(string=html_string).write_pdf()
        
        # Create HTTP response with PDF
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
        
        return response
    
    # Default fallback
    messages.error(request, _("Unsupported export format"))
    return redirect('membership:outstanding_report')
