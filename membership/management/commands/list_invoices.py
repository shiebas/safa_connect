from django.core.management.base import BaseCommand
from membership.models import Invoice

class Command(BaseCommand):
    help = 'Lists all invoices with their payment references.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Listing all invoices:'))
        invoices = Invoice.objects.all()
        if invoices:
            for invoice in invoices:
                self.stdout.write(
                    f"Invoice Number: {invoice.invoice_number}, "
                    f"Payment Reference: {invoice.payment_reference}, "
                    f"Member: {invoice.member}, "
                    f"Status: {invoice.status}"
                )
        else:
            self.stdout.write('No invoices found.')
