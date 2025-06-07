from django.core.management.base import BaseCommand
from django.db.models import Q
from geography.models import NationalFederation, Association, Region, LocalFootballAssociation, Club
from accounts.models import CustomUser
from membership.models import Member, Player
import os

class Command(BaseCommand):
    help = 'Check SAFA ID coverage across all relevant models in the system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== SAFA ID Coverage Report ==="))
        
        models_to_check = {
            'Users': CustomUser,
            'Members': Member,
            'Players': Player,
            'Clubs': Club,
            'Local Football Associations': LocalFootballAssociation,
            'Regions': Region,
            'Associations': Association,
            'National Federations': NationalFederation,
        }
        
        total_objects = 0
        total_missing = 0
        
        # Output format
        fmt = "{:<30} {:<10} {:<10} {:<10} {:<10}"
        
        # Print header
        self.stdout.write(fmt.format("Model", "Total", "With IDs", "Missing", "Coverage"))
        self.stdout.write("-" * 70)
        
        # Check each model
        for model_name, model_class in models_to_check.items():
            # Skip if model doesn't have safa_id field
            if not hasattr(model_class, 'safa_id'):
                self.stdout.write(fmt.format(model_name, "N/A", "N/A", "N/A", "N/A"))
                continue
                
            try:
                total = model_class.objects.count()
                with_ids = model_class.objects.exclude(Q(safa_id=None) | Q(safa_id='')).count()
                missing = total - with_ids
                coverage = (with_ids / total * 100) if total > 0 else 100.0
                
                # Colorize output based on coverage
                if coverage == 100:
                    coverage_str = self.style.SUCCESS(f"{coverage:.1f}%")
                elif coverage >= 90:
                    coverage_str = self.style.WARNING(f"{coverage:.1f}%")
                else:
                    coverage_str = self.style.ERROR(f"{coverage:.1f}%")
                
                self.stdout.write(fmt.format(model_name, total, with_ids, missing, coverage_str))
                
                total_objects += total
                total_missing += missing
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error checking {model_name}: {str(e)}"))
        
        # Print summary
        self.stdout.write("-" * 70)
        total_coverage = ((total_objects - total_missing) / total_objects * 100) if total_objects > 0 else 100.0
        
        if total_coverage == 100:
            coverage_str = self.style.SUCCESS(f"{total_coverage:.1f}%")
            status = self.style.SUCCESS("✓ COMPLETE")
        elif total_coverage >= 90:
            coverage_str = self.style.WARNING(f"{total_coverage:.1f}%")
            status = self.style.WARNING("⚠ ALMOST COMPLETE")
        else:
            coverage_str = self.style.ERROR(f"{total_coverage:.1f}%")
            status = self.style.ERROR("✗ INCOMPLETE")
            
        self.stdout.write(fmt.format("TOTAL", total_objects, total_objects - total_missing, 
                                   total_missing, coverage_str))
        self.stdout.write("\nOverall status: " + status)
        
        # Provide recommendation if missing IDs
        if total_missing > 0:
            self.stdout.write("\nRecommendation:")
            self.stdout.write(self.style.WARNING("  Run the following command to generate all missing SAFA IDs:"))
            self.stdout.write("  python manage.py generate_safa_ids --model all")
