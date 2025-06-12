# SAFA Invoice System: Administrator Troubleshooting Guide

This guide is intended for system administrators and provides technical solutions for common issues with the invoice system.

## Database-Related Issues

### Invoice Records Not Appearing

**Problem**: Invoices created during registration don't appear in the system.

**Solution**:
1. Check the database transaction logs:
   ```bash
   python manage.py shell
   >>> from django.db import connection
   >>> with connection.cursor() as cursor:
   >>>     cursor.execute("SELECT * FROM django_transaction_log ORDER BY timestamp DESC LIMIT 10")
   >>>     print(cursor.fetchall())
   ```

2. Verify content type relationships:
   ```bash
   python manage.py shell
   >>> from django.contrib.contenttypes.models import ContentType
   >>> from membership.models import PlayerClubRegistration, Invoice
   >>> ct = ContentType.objects.get_for_model(PlayerClubRegistration)
   >>> Invoice.objects.filter(content_type=ct).count()
   ```

3. Recreate invoice if necessary:
   ```python
   # Example for creating missing invoice
   from membership.models import Player, Invoice, InvoiceItem
   from django.utils import timezone
   
   player = Player.objects.get(id=player_id)
   club = player.club
   
   invoice = Invoice.objects.create(
       reference=f"MANUAL-{player.id}",
       invoice_type='REGISTRATION',
       amount=500.00,  # Update with correct amount
       player=player,
       club=club,
       issued_by=request.user.member,
       payment_method='EFT',
       status='PENDING',
       notes=f"Manually created registration invoice"
   )
   
   # Add invoice item
   InvoiceItem.objects.create(
       invoice=invoice,
       description="Player Registration Fee",
       quantity=1,
       unit_price=500.00,  # Update with correct amount
       sub_total=500.00  # Update with correct amount
   )
   ```

### Invoice Status Not Updating

**Problem**: Invoice status doesn't change when marked as paid.

**Solution**:
1. Check permission issues:
   ```bash
   python manage.py shell
   >>> from django.contrib.auth.models import Permission
   >>> permission = Permission.objects.get(codename='change_invoice')
   >>> user_group = request.user.groups.all()[0]
   >>> user_group.permissions.filter(id=permission.id).exists()
   ```

2. Manually update invoice status:
   ```bash
   python manage.py shell
   >>> from membership.models.invoice import Invoice
   >>> invoice = Invoice.objects.get(invoice_number='INV-2025-000123')
   >>> invoice.status = 'PAID'
   >>> invoice.payment_date = timezone.now().date()
   >>> invoice.save()
   ```

3. Check for cascading update failures:
   ```bash
   python manage.py shell
   >>> from membership.models import Player, PlayerClubRegistration
   >>> player = Player.objects.get(id=player_id)
   >>> reg = PlayerClubRegistration.objects.get(player=player)
   >>> reg.status = 'ACTIVE'
   >>> reg.save()
   >>> player.status = 'ACTIVE'
   >>> player.save()
   ```

## Report Generation Issues

### PDF Generation Fails

**Problem**: PDF exports fail with errors.

**Solution**:
1. Verify WeasyPrint installation:
   ```bash
   pip install WeasyPrint==52.5
   ```

2. Check system dependencies:
   ```bash
   # For Ubuntu/Debian
   sudo apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
   ```

3. Implement fallback to CSV:
   ```python
   try:
       # PDF generation code
       pdf_file = HTML(string=html_string).write_pdf()
   except Exception as e:
       # Fallback to CSV
       response = HttpResponse(content_type='text/csv')
       response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
       # CSV generation code
   ```

### Large Reports Timeout

**Problem**: Generating large reports results in timeout errors.

**Solution**:
1. Implement pagination:
   ```python
   # In your view
   paginator = Paginator(queryset, 100)
   page_number = request.GET.get('page')
   page_obj = paginator.get_page(page_number)
   context['page_obj'] = page_obj
   ```

2. Use asynchronous report generation:
   ```python
   from celery import shared_task
   
   @shared_task
   def generate_large_report(filters, format_type):
       # Report generation logic
       return report_path
   
   # In view:
   task = generate_large_report.delay(filters, format_type)
   request.session['report_task_id'] = task.id
   return redirect('report_status')
   ```

## Email Notification Issues

### Payment Reminders Not Sending

**Problem**: Automated payment reminders fail to send.

**Solution**:
1. Check email configuration:
   ```bash
   python manage.py shell
   >>> from django.core.mail import send_mail
   >>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'], fail_silently=False)
   ```

2. Verify email templates:
   ```bash
   # Check if template exists
   ls -la templates/membership/emails/payment_overdue.html
   
   # Test template rendering
   python manage.py shell
   >>> from django.template.loader import render_to_string
   >>> context = {'invoice': invoice, 'days_overdue': 15}
   >>> html = render_to_string('membership/emails/payment_overdue.html', context)
   >>> print(html)
   ```

3. Implement email logging:
   ```python
   # Add to settings.py
   EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
   EMAIL_FILE_PATH = '/tmp/app-emails'
   ```

## Command Line Utilities

### Useful Management Commands

1. **Manually update overdue invoices**:
   ```bash
   python manage.py update_invoice_status
   ```

2. **Send payment reminders**:
   ```bash
   python manage.py update_invoice_status --notify
   ```

3. **List all pending invoices**:
   ```bash
   python manage.py shell -c "from membership.models.invoice import Invoice; print(Invoice.objects.filter(status='PENDING').count())"
   ```

4. **Fix inconsistent player statuses**:
   ```bash
   python manage.py shell -c "
   from membership.models import Player, PlayerClubRegistration, Invoice;
   paid_invoices = Invoice.objects.filter(status='PAID', invoice_type='REGISTRATION');
   for inv in paid_invoices:
     try:
       player = inv.player;
       if player.status != 'ACTIVE':
         player.status = 'ACTIVE';
         player.save();
         print(f'Updated player {player.id}');
     except Exception as e:
       print(f'Error with player {inv.player_id}: {e}')
   "
   ```

## System Monitoring

### Key Metrics to Watch

1. **Invoice Creation Rate**:
   ```bash
   python manage.py shell -c "
   from membership.models.invoice import Invoice;
   from django.utils import timezone;
   today = timezone.now().date();
   print(f'Invoices created today: {Invoice.objects.filter(created__date=today).count()}')
   "
   ```

2. **Payment Success Rate**:
   ```bash
   python manage.py shell -c "
   from membership.models.invoice import Invoice;
   from django.utils import timezone;
   import datetime;
   last_week = timezone.now().date() - datetime.timedelta(days=7);
   total = Invoice.objects.filter(created__date__gte=last_week).count();
   paid = Invoice.objects.filter(created__date__gte=last_week, status='PAID').count();
   print(f'Payment rate: {paid}/{total} ({paid/total*100 if total else 0:.1f}%)')
   "
   ```

3. **Overdue Invoice Count**:
   ```bash
   python manage.py shell -c "
   from membership.models.invoice import Invoice;
   print(f'Overdue invoices: {Invoice.objects.filter(status='OVERDUE').count()}')
   "
   ```

## Database Maintenance

### Regular Maintenance Tasks

1. **Backup invoice data**:
   ```bash
   python manage.py dumpdata membership.invoice membership.invoiceitem > /home/shaun/safa_global/backups/invoices_$(date +%Y%m%d).json
   ```

2. **Check for orphaned invoice items**:
   ```bash
   python manage.py shell -c "
   from membership.models.invoice import InvoiceItem;
   orphans = InvoiceItem.objects.filter(invoice__isnull=True);
   print(f'Orphaned items: {orphans.count()}');
   "
   ```

3. **Clean up test invoices**:
   ```bash
   python manage.py shell -c "
   from membership.models.invoice import Invoice;
   test_invoices = Invoice.objects.filter(reference__startswith='TEST-');
   print(f'Deleting {test_invoices.count()} test invoices');
   test_invoices.delete();
   "
   ```

For persistent issues that cannot be resolved using this guide, please contact the development team at dev@safa.net.

---

*Last Updated: June 12, 2025*
