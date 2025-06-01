from django.core.management.base import BaseCommand
from geography.models import LocalFootballAssociation, Region
from django.db import transaction
from django.db.models import Count
from collections import defaultdict

class Command(BaseCommand):
    help = 'Update acronyms for all Local Football Associations with longer acronym generation'

    def add_arguments(self, parser):
        parser.add_argument('--region', type=str, help='Optional: Only update LFAs in a specific region')
        parser.add_argument('--dry-run', action='store_true', help='Show changes without applying them')
        parser.add_argument('--force', action='store_true', help='Update even if acronym already exists')
        parser.add_argument('--interactive', action='store_true', help='Confirm each update')
        parser.add_argument('--max-length', type=int, default=10, help='Maximum acronym length (default: 10)')
        parser.add_argument('--chars-per-word', type=int, default=3, help='Characters to take from each word (default: 3)')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== LFA Extended Acronym Generator ==="))
        
        region_filter = options.get('region')
        dry_run = options.get('dry_run', False)
        force_update = options.get('force', False)
        interactive = options.get('interactive', False)
        max_length = options.get('max_length', 10)
        chars_per_word = options.get('chars_per_word', 3)
        
        # Get LFAs to update
        lfas_query = LocalFootballAssociation.objects.all().order_by('region__name', 'name')
        
        if region_filter:
            try:
                region = Region.objects.get(name__iexact=region_filter)
                lfas_query = lfas_query.filter(region=region)
                self.stdout.write(f"Filtering by region: {region.name}")
            except Region.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Region '{region_filter}' not found."))
                return
        
        lfas = list(lfas_query)
        total_lfas = len(lfas)
        
        if total_lfas == 0:
            self.stderr.write(self.style.WARNING("No LFAs found to update."))
            return
        
        self.stdout.write(f"Found {total_lfas} LFAs to process")
        self.stdout.write(f"Using {chars_per_word} characters per word, max length {max_length}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: No changes will be saved to the database"))
        
        # Helper function to generate better acronyms
        def generate_acronym(name, chars_per_word, max_length):
            words = [w for w in name.split() if w]
            
            # Skip common words like "LFA" or "FOOTBALL"
            skip_words = ["LFA", "FOOTBALL", "ASSOCIATION", "LOCAL", "AND", "THE", "OF", "&"]
            filtered_words = [w for w in words if w.upper() not in skip_words]
            
            # If all words were filtered, use original words
            if not filtered_words:
                filtered_words = words
                
            # Get first N chars from each significant word
            parts = []
            for word in filtered_words:
                if word.isupper():  # Acronym or initialism
                    parts.append(word[:min(len(word), chars_per_word)])
                else:
                    parts.append(word[:min(len(word), chars_per_word)].upper())
            
            # Join and trim to max length
            acronym = ''.join(parts)[:max_length]
            
            return acronym
        
        # First pass: Generate acronyms and check for uniqueness
        acronym_map = {}  # Maps LFA id to its proposed acronym
        duplicate_groups = defaultdict(list)  # Groups LFAs by duplicate acronym
        
        for lfa in lfas:
            new_acronym = generate_acronym(lfa.name, chars_per_word, max_length)
            acronym_map[lfa.id] = new_acronym
            duplicate_groups[new_acronym].append(lfa)
        
        # Identify duplicate acronyms
        duplicates = {acr: lfas for acr, lfas in duplicate_groups.items() if len(lfas) > 1}
        
        if duplicates:
            self.stdout.write(self.style.WARNING(f"Found {len(duplicates)} duplicate acronyms:"))
            for acronym, dup_lfas in duplicates.items():
                self.stdout.write(f"  • {acronym}: {', '.join([lfa.name for lfa in dup_lfas])}")
                
            # Try to resolve duplicates by increasing characters per word
            if chars_per_word < 4:
                self.stdout.write(self.style.WARNING(f"Attempting to resolve by using more characters..."))
                
                # Regenerate acronyms with more characters per word for duplicates only
                for acronym, dup_lfas in duplicates.items():
                    for i, lfa in enumerate(dup_lfas):
                        if i == 0:  # Keep first one as is
                            continue
                        # Try with more chars per word for duplicates
                        new_chars = chars_per_word + 1
                        extended_acronym = generate_acronym(lfa.name, new_chars, max_length)
                        
                        # If still a duplicate, add a number
                        if extended_acronym in acronym_map.values():
                            extended_acronym = f"{extended_acronym[:max_length-1]}{i+1}"
                        
                        acronym_map[lfa.id] = extended_acronym
                
                # Update duplicate groups
                duplicate_groups = defaultdict(list)
                for lfa in lfas:
                    duplicate_groups[acronym_map[lfa.id]].append(lfa)
                
                duplicates = {acr: lfas for acr, lfas in duplicate_groups.items() if len(lfas) > 1}
                
                if not duplicates:
                    self.stdout.write(self.style.SUCCESS("All duplicates resolved by using more characters!"))
                else:
                    self.stdout.write(self.style.WARNING(f"Still have {len(duplicates)} duplicate acronyms after adjusting character count."))
        
        # Track statistics
        updated_count = 0
        skipped_count = 0
        unchanged_count = 0
        
        with transaction.atomic():
            # Only create a savepoint if not in dry run mode
            if not dry_run:
                sid = transaction.savepoint()
                
            try:
                # Process LFAs
                for lfa in lfas:
                    new_acronym = acronym_map[lfa.id]
                    
                    # Skip if acronym is unchanged and force is not enabled
                    if lfa.acronym == new_acronym:
                        unchanged_count += 1
                        if interactive:
                            self.stdout.write(f"LFA '{lfa.name}' acronym already correct: {lfa.acronym}")
                        continue
                    
                    if not force_update and lfa.acronym and lfa.acronym.strip():
                        skipped_count += 1
                        self.stdout.write(f"SKIPPED: '{lfa.name}' already has acronym: {lfa.acronym} (new would be: {new_acronym})")
                        continue
                    
                    # In interactive mode, ask for confirmation
                    if interactive:
                        confirm = input(f"Update '{lfa.name}' acronym from '{lfa.acronym or 'empty'}' to '{new_acronym}'? [y/N]: ")
                        if confirm.lower() != 'y':
                            skipped_count += 1
                            self.stdout.write("Skipped.")
                            continue
                    
                    old_acronym = lfa.acronym or 'empty'
                    self.stdout.write(f"Updating '{lfa.name}': {old_acronym} → {new_acronym}")
                    
                    # Only update if not in dry run mode
                    if not dry_run:
                        lfa.acronym = new_acronym
                        lfa.save(update_fields=['acronym'])
                    
                    updated_count += 1
                
                # Only commit if not in dry run mode
                if not dry_run:
                    transaction.savepoint_commit(sid)
            except Exception as e:
                if not dry_run:
                    transaction.savepoint_rollback(sid)
                self.stderr.write(self.style.ERROR(f"Error updating acronyms: {str(e)}"))
                return
        
        # Show summary
        self.stdout.write("\n=== Update Summary ===")
        self.stdout.write(f"Total LFAs processed: {total_lfas}")
        self.stdout.write(f"LFAs updated: {updated_count}")
        self.stdout.write(f"LFAs skipped (had existing acronym): {skipped_count}")
        self.stdout.write(f"LFAs unchanged (acronym already correct): {unchanged_count}")
        
        if duplicates:
            self.stdout.write(self.style.WARNING("\nSome duplicate acronyms could not be automatically resolved."))
            self.stdout.write("Consider running with --chars-per-word=4 or manually editing these acronyms.")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nThis was a dry run. No changes were saved."))
            self.stdout.write("Run without --dry-run to apply the changes.")
        else:
            self.stdout.write(self.style.SUCCESS("\nAcronym updates completed successfully."))