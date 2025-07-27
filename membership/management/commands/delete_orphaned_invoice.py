from django.core.management.base import BaseCommand, CommandError
from membership.models import Invoice
from django.db import transaction

class Command(BaseCommand):
    help = 'Deletes one or more orphaned invoice records by their primary keys.'

    def add_arguments(self, parser):
        parser.add_argument(
            'invoice_ids', 
            nargs='+', 
            type=int, 
            help='One or more primary keys of the invoices to delete.'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        invoice_ids = options['invoice_ids']
        
        for invoice_id in invoice_ids:
            self.stdout.write(f"Attempting to delete invoice with ID: {invoice_id}")
            try:
                # We use _base_manager to bypass any custom manager logic that might
                # prevent finding the record.
                invoice = Invoice._base_manager.get(pk=invoice_id)
                
                self.stdout.write(f"Found invoice: {invoice}")
                
                if invoice.player_id:
                    self.stdout.write(f"  - Associated Player ID: {invoice.player_id}")
                
                invoice.delete()
                
                self.stdout.write(self.style.SUCCESS(f"Successfully deleted invoice with ID {invoice_id}."))

                # Verification
                if not Invoice._base_manager.filter(pk=invoice_id).exists():
                    self.stdout.write(self.style.SUCCESS(f"  - Verification successful: Invoice {invoice_id} no longer exists."))
                else:
                    self.stderr.write(self.style.ERROR(f"  - Verification failed: Invoice {invoice_id} still exists."))

            except Invoice.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Invoice with ID '{invoice_id}' does not exist. Skipping."))
            except Exception as e:
                raise CommandError(f"An error occurred while deleting invoice {invoice_id}: {e}")
