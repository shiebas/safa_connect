from django.core.management.base import BaseCommand
from geography.models import Province, Region, LocalFootballAssociation

class Command(BaseCommand):
    help = 'Check Eastern Cape LFA count (should be 56, not 60)'
    
    def handle(self, *args, **options):
        try:
            province = Province.objects.get(name='Eastern Cape')
            regions = province.region_set.all().order_by('id')
            
            self.stdout.write('🔍 Eastern Cape LFA Analysis:')
            total_lfas = 0
            
            for region in regions:
                lfas = region.localfootballassociation_set.all().order_by('name')
                total_lfas += lfas.count()
                self.stdout.write(f'\nRegion {region.id}: {region.name} ({lfas.count()} LFAs)')
                
                for lfa in lfas:
                    self.stdout.write(f'  • {lfa.name}')
            
            self.stdout.write(f'\n📊 Total: {total_lfas} LFAs (target: 56)')
            
            if total_lfas > 56:
                self.stdout.write(self.style.WARNING(f'⚠️  {total_lfas - 56} extra LFAs need to be removed'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
