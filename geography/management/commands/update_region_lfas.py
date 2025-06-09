from django.core.management.base import BaseCommand
from django.db import transaction
from geography.models import Region, LocalFootballAssociation
import sys

class Command(BaseCommand):
    help = 'Update LFAs for any region by pasting LFA list'
    
    def add_arguments(self, parser):
        parser.add_argument('region_id', type=int, help='Region ID to update')
    
    def handle(self, *args, **options):
        region_id = options['region_id']
        
        try:
            region = Region.objects.get(id=region_id)
            self.stdout.write(f'🎯 Updating LFAs for Region ID {region_id}: {region.name}')
            self.stdout.write(f'   Province: {region.province.name}')
            
            # Show current LFAs
            current_lfas = region.localfootballassociation_set.all().order_by('name')
            self.stdout.write(f'\n📋 Current LFAs ({current_lfas.count()}):')
            for i, lfa in enumerate(current_lfas, 1):
                self.stdout.write(f'  {i:2d}. {lfa.name}')
            
            # Get LFA names from user
            self.stdout.write(f'\n📝 Paste ALL LFA names for {region.name} (one per line):')
            self.stdout.write('   Then press Enter on empty line to finish')
            
            new_lfa_names = []
            while True:
                try:
                    line = input().strip()
                    if not line:  # Empty line = finished
                        break
                    
                    # Clean and format the name
                    lfa_name = line.strip()
                    
                    # Remove any existing prefixes/suffixes
                    for prefix in ['SAFA ', 'safa ', 'Safa ']:
                        if lfa_name.startswith(prefix):
                            lfa_name = lfa_name[len(prefix):].strip()
                    
                    for suffix in [' LFA', ' lfa', ' Lfa']:
                        if lfa_name.endswith(suffix):
                            lfa_name = lfa_name[:-4].strip()
                    
                    # Format as SAFA [Name] LFA
                    formatted_name = f'SAFA {lfa_name} LFA'
                    new_lfa_names.append(formatted_name)
                    
                except KeyboardInterrupt:
                    self.stdout.write('\n❌ Cancelled by user.')
                    return
            
            if not new_lfa_names:
                self.stdout.write('❌ No LFAs provided. Exiting.')
                return
            
            # Show what will be created
            self.stdout.write(f'\n📋 Will create {len(new_lfa_names)} LFAs:')
            for i, name in enumerate(new_lfa_names, 1):
                self.stdout.write(f'  {i:2d}. {name}')
            
            # Confirm
            confirm = input(f'\n❓ Replace ALL LFAs in {region.name} with these {len(new_lfa_names)} LFAs? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('❌ Cancelled.')
                return
            
            # Update LFAs
            with transaction.atomic():
                # Delete ALL existing LFAs for this region
                deleted_count = region.localfootballassociation_set.count()
                region.localfootballassociation_set.all().delete()
                self.stdout.write(f'🗑️  Deleted {deleted_count} existing LFAs')
                
                # Create ALL new LFAs
                for lfa_name in new_lfa_names:
                    LocalFootballAssociation.objects.create(
                        name=lfa_name,
                        region=region
                    )
                
                # Verify final count
                final_count = region.localfootballassociation_set.count()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n🎉 Success!\n'
                        f'   Region: {region.name}\n'
                        f'   Deleted: {deleted_count} old LFAs\n'
                        f'   Created: {len(new_lfa_names)} new LFAs\n'
                        f'   Final count: {final_count}'
                    )
                )
        
        except Region.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Region ID {region_id} not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
