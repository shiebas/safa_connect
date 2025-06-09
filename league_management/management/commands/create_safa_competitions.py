from django.core.management.base import BaseCommand
from django.db import transaction
from league_management.models import CompetitionCategory
from geography.models import Region

class Command(BaseCommand):
    help = 'Create official SAFA competition categories based on real structure'
    
    def handle(self, *args, **options):
        self.stdout.write('🏆 Creating official SAFA competition categories...')
        
        # Real SAFA competition categories from the links
        categories_data = [
            # ABC Motsepe League (National First Division)
            {
                'name': 'ABC Motsepe League',
                'short_name': 'ABC',
                'description': 'National First Division - Tier 2 of South African football',
                'level': 'national',
                'gender': 'men',
                'age_category': 'senior'
            },
            
            # SAFA Regional Leagues (Tier 3)
            {
                'name': 'SAFA Regional League',
                'short_name': 'SRL',
                'description': 'Regional leagues across all provinces - Tier 3',
                'level': 'regional',
                'gender': 'men',
                'age_category': 'senior'
            },
            
            # Sasol League (Women's National League)
            {
                'name': 'Sasol League',
                'short_name': 'SASOL',
                'description': 'Women\'s National League',
                'level': 'national',
                'gender': 'women',
                'age_category': 'senior'
            },
            
            # SAB League (Provincial Women)
            {
                'name': 'SAB Regional Women\'s League',
                'short_name': 'SAB',
                'description': 'Regional Women\'s League',
                'level': 'regional',
                'gender': 'women',
                'age_category': 'senior'
            },
            
            # Women's Regional League
            {
                'name': 'Women\'s Regional League',
                'short_name': 'WRL',
                'description': 'Provincial Women\'s Regional League',
                'level': 'provincial',
                'gender': 'women',
                'age_category': 'senior'
            },
            
            # Youth Categories
            {
                'name': 'SAFA Youth League U19',
                'short_name': 'U19',
                'description': 'Under-19 Development League',
                'level': 'regional',
                'gender': 'men',
                'age_category': 'u19'
            },
            
            {
                'name': 'SAFA Youth League U17',
                'short_name': 'U17',
                'description': 'Under-17 Development League',
                'level': 'regional',
                'gender': 'men',
                'age_category': 'u17'
            },
            
            # Local LFA Leagues
            {
                'name': 'LFA Local League',
                'short_name': 'LOCAL',
                'description': 'Local Football Association Leagues',
                'level': 'local',
                'gender': 'men',
                'age_category': 'senior'
            },
        ]
        
        try:
            with transaction.atomic():
                created_count = 0
                
                for cat_data in categories_data:
                    category, created = CompetitionCategory.objects.get_or_create(
                        name=cat_data['name'],
                        defaults=cat_data
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f'✅ Created: {category.name}')
                    else:
                        self.stdout.write(f'🔄 Exists: {category.name}')
                
                # Show summary
                total_categories = CompetitionCategory.objects.count()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n🎉 SAFA competition categories setup complete!\n'
                        f'   Created: {created_count} new categories\n'
                        f'   Total: {total_categories} categories\n\n'
                        f'Competition hierarchy:\n'
                        f'   🏆 National: ABC Motsepe, Sasol League\n'
                        f'   🎯 Regional: SAFA Regional, SAB Women\n'
                        f'   📍 Provincial: Women\'s Regional\n'
                        f'   🏠 Local: LFA Leagues\n'
                        f'   👶 Youth: U19, U17 Development'
                    )
                )
                
                # Show regions available for competitions
                regions = Region.objects.count()
                self.stdout.write(f'\n📊 Available for competitions: {regions} regions across 9 provinces')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
