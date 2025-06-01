from django.core.management.base import BaseCommand
from geography.models import NationalFederation, Association, Region, LocalFootballAssociation, Club
from django.db import transaction
from django.db.models import Q
import random
import string
import time

class Command(BaseCommand):
    help = 'Generate SAFA IDs for all geography entities'

    def add_arguments(self, parser):
        parser.add_argument('--model', choices=['nf', 'assoc', 'region', 'lfa', 'club', 'all'], 
                          default='all', help='Model to generate IDs for')
        parser.add_argument('--force', action='store_true', help='Force regenerate all IDs')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    def handle(self, *args, **options):
        model_choice = options['model']
        force = options['force']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS("=== SAFA ID Generator ==="))
        
        # Define models to process
        model_map = {
            'nf': NationalFederation,
            'assoc': Association,
            'region': Region,
            'lfa': LocalFootballAssociation,
            'club': Club,
        }
        
        # Process selected models
        models_to_process = [model_map[model_choice]] if model_choice != 'all' else model_map.values()
        
        # Collect existing IDs across ALL models to ensure uniqueness
        used_ids = set()
        if not force:
            for model in model_map.values():
                existing_ids = model.objects.exclude(Q(safa_id=None) | Q(safa_id='')).values_list('safa_id', flat=True)
                used_ids.update(existing_ids)
                self.stdout.write(f"Found {len(existing_ids)} existing IDs in {model.__name__}")
        
        self.stdout.write(f"Total existing IDs across all models: {len(used_ids)}")
        
        # Generate IDs for each model
        total_updated = 0
        with transaction.atomic():
            for model in models_to_process:
                model_name = model.__name__
                
                # Get objects that need IDs
                if force:
                    objects = model.objects.all()
                else:
                    objects = model.objects.filter(Q(safa_id=None) | Q(safa_id=''))
                    
                count = objects.count()
                self.stdout.write(f"Processing {count} {model_name} objects...")
                
                for obj in objects:
                    safa_id = self.generate_unique_safa_id(used_ids)
                    used_ids.add(safa_id)
                    
                    self.stdout.write(f"  {obj}: {safa_id}")
                    
                    if not dry_run:
                        obj.safa_id = safa_id
                        obj.save(update_fields=['safa_id'])
                        total_updated += 1
                
                self.stdout.write(self.style.SUCCESS(f"Processed {count} {model_name} objects"))
                # Small pause between models to avoid DB contention
                time.sleep(0.5)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: No changes were made"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully updated {total_updated} objects with SAFA IDs"))
    
    def generate_unique_safa_id(self, used_ids):
        """Generate a unique SAFA ID not in used_ids"""
        chars = string.ascii_uppercase + string.digits
        max_attempts = 100
        
        for _ in range(max_attempts):
            # Generate a random 5-character string
            safa_id = ''.join(random.choice(chars) for _ in range(5))
            
            if safa_id not in used_ids:
                return safa_id
        
        raise ValueError("Could not generate a unique SAFA ID after multiple attempts")