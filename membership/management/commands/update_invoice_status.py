from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q, F
from datetime import timedelta
from membership.invoice_models import Invoice

class Command(BaseCommand):
    help = 'Update invoice statuses for overdue payments'
    
    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Find invoices that are past their due date but not marked as overdue
        overdue_invoices = Invoice.objects.filter(
            status='PENDING',
            due_date__lt=today
        )
        
        # Update them to overdue status
        updated_count = overdue_invoices.update(status='OVERDUE')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} invoices to overdue status')
        )
        
        # Optional: Send email notifications for newly overdue invoices
        if options.get('notify', False):
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            from django.conf import settings
            
            for invoice in overdue_invoices:
                days_overdue = (today - invoice.due_date).days
                context = {
                    'invoice': invoice,
                    'days_overdue': days_overdue,
                    'player': invoice.player,
                    'club': invoice.club,
                }
                
                subject = f'Payment Overdue: Invoice #{invoice.invoice_number}'
                html_message = render_to_string('membership/emails/payment_overdue.html', context)
                
                send_mail(
                    subject=subject,
                    message='', # Plain text version - we'll use html only for simplicity
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[invoice.player.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Sent payment reminder for Invoice #{invoice.invoice_number}')
                )
