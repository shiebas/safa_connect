from django.core.management.base import BaseCommand
from django.db import transaction
from geography.models import Club
from django.db import models

class Command(BaseCommand):
    help = 'Generate SAFA IDs for clubs (FIFA IDs handled via API)'
    
    def add_arguments(self, parser):
        parser.add_argument('--update-existing', action='store_true', 
                          help='Update clubs that already have SAFA IDs')
    
    def handle(self, *args, **options):
        update_existing = options['update_existing']
        
        self.stdout.write('🏟️  Managing SAFA IDs for clubs...')
        self.stdout.write('ℹ️  SAFA IDs only generated after payment confirmation')
        self.stdout.write('ℹ️  FIFA IDs will be obtained via FIFA API application')
        
        # Get clubs that have paid but no SAFA ID, or need existing ID verification
        if update_existing:
            clubs = Club.objects.all()
        else:
            # Only process clubs that have confirmed payment but no SAFA ID
            clubs = Club.objects.filter(
                models.Q(safa_id__isnull=True) | models.Q(safa_id=''),
                # Add payment confirmation check here when payment model exists
                # payment_confirmed=True
            )
        
        total_clubs = clubs.count()
        self.stdout.write(f'📊 Processing {total_clubs} clubs...')
        
        if total_clubs == 0:
            self.stdout.write(self.style.SUCCESS('✅ No clubs need SAFA ID processing'))
            return
        
        try:
            with transaction.atomic():
                updated_safa = 0
                
                for club in clubs:
                    # Check if club has existing SAFA ID to use
                    existing_safa = input(f'\n🏟️  {club.name} ({club.local_football_association.name})\n'
                                        f'   Current SAFA ID: {club.safa_id or "None"}\n'
                                        f'   Enter existing SAFA ID (or press Enter to generate new): ')
                    
                    if existing_safa.strip():
                        # Use existing SAFA ID
                        club.safa_id = existing_safa.strip()
                        club.save()
                        self.stdout.write(f'  ✅ Used existing SAFA ID: {club.safa_id}')
                        updated_safa += 1
                    elif not club.safa_id:
                        # Generate new SAFA ID only if payment confirmed
                        # TODO: Add payment confirmation check
                        confirm_payment = input(f'   Payment confirmed for {club.name}? (y/N): ')
                        
                        if confirm_payment.lower() == 'y':
                            # Generate new SAFA ID (handled by model save method)
                            old_safa_id = club.safa_id
                            club.save()
                            
                            if club.safa_id != old_safa_id:
                                updated_safa += 1
                                self.stdout.write(f'  ✅ Generated new SAFA ID: {club.safa_id}')
                        else:
                            self.stdout.write(f'  ⏳ Skipped - payment not confirmed')
                    else:
                        self.stdout.write(f'  🔄 {club.name}: SAFA={club.safa_id} (unchanged)')
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n🎉 SAFA ID generation complete!\n'
                        f'   SAFA IDs updated: {updated_safa}\n'
                        f'   Total clubs processed: {total_clubs}\n'
                        f'   FIFA IDs: Apply via FIFA registration API'
                    )
                )
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
