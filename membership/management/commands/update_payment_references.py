from django.core.management.base import BaseCommand
from django.db.models import Q
from membership.models import Invoice

class Command(BaseCommand):
    help = 'Updates the payment reference for all existing invoices that don\'t have one.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Updating payment references for existing invoices...'))
        invoices = Invoice.objects.filter(Q(payment_reference__isnull=True) | Q(payment_reference=''))
        updated_count = 0
        for invoice in invoices:
            invoice.payment_reference = invoice.generate_payment_reference()
            invoice.save()
            updated_count += 1
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} invoices.'))
