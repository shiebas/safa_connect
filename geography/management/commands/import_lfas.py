from django.core.management.base import BaseCommand
from geography.models import Region, LocalFootballAssociation
from django.db import transaction

class Command(BaseCommand):
    help = 'Import Local Football Associations interactively'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== LFA Import Tool ==="))

        # 1. List available regions for selection
        regions = Region.objects.all().order_by('name')
        if not regions:
            self.stderr.write(self.style.ERROR("No regions found in the database. Please create regions first."))
            return

        self.stdout.write("Available regions:")
        for i, region in enumerate(regions, 1):
            self.stdout.write(f"  {i}. {region.name}")

        # 2. Ask user to select a region
        region = None
        while not region:
            try:
                region_choice = input("\nEnter region number or name: ")
                # Check if input is a number
                if region_choice.isdigit() and 1 <= int(region_choice) <= len(regions):
                    region = regions[int(region_choice) - 1]
                else:
                    # Try to find by name
                    region = Region.objects.get(name__iexact=region_choice)
            except (ValueError, Region.DoesNotExist):
                self.stderr.write(self.style.ERROR(f"Region '{region_choice}' not found. Please try again."))

        self.stdout.write(self.style.SUCCESS(f"\nSelected region: {region.name}"))

        # 3. Ask for LFA names (bulk paste support)
        self.stdout.write(self.style.SUCCESS("Now enter LFA names, one per line. You can paste multiple lines at once."))
        self.stdout.write("When finished, type 'done' on a new line:")
        
        lfa_names = []
        while True:
            lines = input()
            if lines.lower() == 'done':
                break
                
            # Handle multiple lines (from clipboard paste)
            for line in lines.split('\n'):
                name = line.strip()
                if name and name.lower() != 'done':
                    lfa_names.append(name)
        
        if not lfa_names:
            self.stderr.write(self.style.ERROR("No LFA names provided. Import canceled."))
            return
        
        self.stdout.write(f"\nProcessing {len(lfa_names)} LFA names...")
        
        # 4. Create LFAs
        with transaction.atomic():
            lfas_to_create = []
            existing_count = 0
            
            for name in lfa_names:
                # Check if LFA already exists
                if LocalFootballAssociation.objects.filter(name=name, region=region).exists():
                    existing_count += 1
                    self.stdout.write(f"LFA '{name}' already exists for this region")
                    continue
                
                # Generate acronym from first letters
                acronym = ''.join(word[0] for word in name.split() if word)
                
                # Create LFA object (not saved to DB yet)
                lfa = LocalFootballAssociation(
                    name=name,
                    acronym=acronym,
                    region=region,
                    # No association specified
                )
                lfas_to_create.append(lfa)
            
            # Bulk create all new LFAs
            if lfas_to_create:
                LocalFootballAssociation.objects.bulk_create(lfas_to_create)
                self.stdout.write(self.style.SUCCESS(f"Created {len(lfas_to_create)} new LFAs"))
            
            if existing_count > 0:
                self.stdout.write(f"Skipped {existing_count} existing LFAs")
            
            total = len(lfa_names)
            self.stdout.write(self.style.SUCCESS(
                f"Import complete: {len(lfas_to_create)} created, {existing_count} skipped, {total} total"
            ))
            
            # Show newly created LFAs
            if lfas_to_create:
                self.stdout.write("\nNewly created LFAs:")
                for lfa in lfas_to_create:
                    self.stdout.write(f"  - {lfa.name} ({lfa.acronym})")