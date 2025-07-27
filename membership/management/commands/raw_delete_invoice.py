from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

class Command(BaseCommand):
    help = 'Deletes an invoice and its related items using raw SQL to bypass ORM issues.'

    def add_arguments(self, parser):
        parser.add_argument('invoice_id', type=int, help='The primary key of the invoice to delete.')

    @transaction.atomic
    def handle(self, *args, **options):
        invoice_id = options['invoice_id']
        
        self.stdout.write(self.style.WARNING(f"Attempting to delete invoice {invoice_id} and related items using raw SQL."))

        try:
            with connection.cursor() as cursor:
                # Check if the parent invoice exists
                cursor.execute("SELECT id FROM membership_invoice WHERE id = %s", [invoice_id])
                if not cursor.fetchone():
                    self.stdout.write(self.style.WARNING(f"Invoice with ID {invoice_id} does not exist."))
                    return

                # 1. Delete from membership_invoiceitem
                # Check if table exists before trying to delete from it
                if 'membership_invoiceitem' in connection.introspection.table_names():
                    cursor.execute("SELECT id FROM membership_invoiceitem WHERE invoice_id = %s", [invoice_id])
                    item_rows = cursor.fetchall()
                    if item_rows:
                        self.stdout.write(f"Deleting {len(item_rows)} related invoice item(s)...")
                        cursor.execute("DELETE FROM membership_invoiceitem WHERE invoice_id = %s", [invoice_id])
                else:
                    self.stdout.write(self.style.WARNING("Table 'membership_invoiceitem' not found, skipping."))


                # 2. Delete from membership_invoicepayment
                if 'membership_invoicepayment' in connection.introspection.table_names():
                    cursor.execute("SELECT id FROM membership_invoicepayment WHERE invoice_id = %s", [invoice_id])
                    payment_rows = cursor.fetchall()
                    if payment_rows:
                        self.stdout.write(f"Deleting {len(payment_rows)} related invoice payment(s)...")
                        cursor.execute("DELETE FROM membership_invoicepayment WHERE invoice_id = %s", [invoice_id])
                else:
                    self.stdout.write(self.style.WARNING("Table 'membership_invoicepayment' not found, skipping."))

                
                # 3. Delete the main invoice
                self.stdout.write(f"Deleting main invoice with ID {invoice_id}...")
                cursor.execute("DELETE FROM membership_invoice WHERE id = %s", [invoice_id])

                # Verification
                cursor.execute("SELECT id FROM membership_invoice WHERE id = %s", [invoice_id])
                if not cursor.fetchone():
                    self.stdout.write(self.style.SUCCESS(f"Successfully deleted invoice {invoice_id} and all related items."))
                else:
                    raise CommandError(f"Failed to delete the main invoice with ID {invoice_id}.")

        except Exception as e:
            raise CommandError(f"An error occurred: {e}")