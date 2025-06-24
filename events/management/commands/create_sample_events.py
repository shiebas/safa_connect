from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
from geography.models import Province
from events.models import Stadium, SeatMap, InternationalMatch


class Command(BaseCommand):
    help = 'Create sample stadium and international match data for testing'
    
    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data first')
        
    def handle(self, *args, **options):
        clear_existing = options['clear']
        
        if clear_existing:
            self.stdout.write('🗑️  Clearing existing data...')
            InternationalMatch.objects.all().delete()
            SeatMap.objects.all().delete()
            Stadium.objects.all().delete()
        
        with transaction.atomic():
            # Get provinces
            gauteng = Province.objects.filter(name__icontains='Gauteng').first()
            western_cape = Province.objects.filter(name__icontains='Western Cape').first()
            kwazulu_natal = Province.objects.filter(name__icontains='KwaZulu').first()
            
            if not gauteng:
                self.stdout.write(self.style.ERROR('❌ Gauteng province not found'))
                return
            
            self.stdout.write('🏟️  Creating stadiums...')
            
            # Create FNB Stadium
            fnb_stadium = Stadium.objects.create(
                name='FNB Stadium',
                short_name='FNB',
                capacity=94736,
                city='Johannesburg',
                province=gauteng,
                address='Nasrec Road, Nasrec, Johannesburg, 2147',
                surface_type='GRASS',
                has_roof=False,
                has_lighting=True,
                parking_spaces=20000,
                contact_person='Stadium Manager',
                contact_phone='011-247-5000',
                contact_email='info@fnbstadium.co.za',
                is_active=True
            )
            
            # Create Cape Town Stadium
            if western_cape:
                ct_stadium = Stadium.objects.create(
                    name='DHL Stadium',
                    short_name='DHL',
                    capacity=55000,
                    city='Cape Town',
                    province=western_cape,
                    address='Fritz Sonnenberg Road, Green Point, Cape Town, 8051',
                    surface_type='GRASS',
                    has_roof=False,
                    has_lighting=True,
                    parking_spaces=5000,
                    contact_person='Stadium Operations',
                    contact_phone='021-417-0000',
                    contact_email='info@dhlstadium.co.za',
                    is_active=True
                )
            
            # Create Moses Mabhida Stadium  
            if kwazulu_natal:
                moses_stadium = Stadium.objects.create(
                    name='Moses Mabhida Stadium',
                    short_name='MMStadium',
                    capacity=56000,
                    city='Durban',
                    province=kwazulu_natal,
                    address='44 Isaiah Ntshangase Road, Stamford Hill, Durban, 4001',
                    surface_type='GRASS',
                    has_roof=False,
                    has_lighting=True,
                    parking_spaces=3500,
                    contact_person='Venue Manager',
                    contact_phone='031-582-8222',
                    contact_email='info@mmstadium.com',
                    is_active=True
                )
            
            self.stdout.write('🎫 Creating sample seating for FNB Stadium...')
            
            # Create sample seating for FNB Stadium
            seat_configs = [
                # VIP Section
                {'section': 'VIP', 'rows': 5, 'seats_per_row': 20, 'price_tier': 'VIP', 'base_price': 800.00},
                # Premium sections
                {'section': 'PREM', 'rows': 10, 'seats_per_row': 30, 'price_tier': 'PREMIUM', 'base_price': 500.00},
                # Standard sections
                {'section': 'A', 'rows': 20, 'seats_per_row': 40, 'price_tier': 'STANDARD', 'base_price': 300.00},
                {'section': 'B', 'rows': 20, 'seats_per_row': 40, 'price_tier': 'STANDARD', 'base_price': 300.00},
                {'section': 'C', 'rows': 20, 'seats_per_row': 35, 'price_tier': 'STANDARD', 'base_price': 280.00},
                # Economy sections  
                {'section': 'D', 'rows': 25, 'seats_per_row': 45, 'price_tier': 'ECONOMY', 'base_price': 200.00},
                {'section': 'E', 'rows': 25, 'seats_per_row': 45, 'price_tier': 'ECONOMY', 'base_price': 200.00},
                # Student section
                {'section': 'STU', 'rows': 15, 'seats_per_row': 50, 'price_tier': 'STUDENT', 'base_price': 100.00},
            ]
            
            total_seats = 0
            for config in seat_configs:
                section_seats = []
                for row in range(1, config['rows'] + 1):
                    for seat in range(1, config['seats_per_row'] + 1):
                        # Add some wheelchair accessible seats
                        is_wheelchair = (row == 1 and seat % 10 == 1)
                        # Add some restricted view seats in cheaper sections
                        has_restricted = (config['price_tier'] in ['ECONOMY', 'STUDENT'] and row > 20)
                        
                        section_seats.append(SeatMap(
                            stadium=fnb_stadium,
                            section=config['section'],
                            row=str(row),
                            seat_number=str(seat),
                            price_tier=config['price_tier'],
                            base_price=config['base_price'],
                            is_wheelchair_accessible=is_wheelchair,
                            has_restricted_view=has_restricted,
                            is_active=True
                        ))
                
                SeatMap.objects.bulk_create(section_seats)
                seats_created = len(section_seats)
                total_seats += seats_created
                self.stdout.write(f'   Section {config["section"]}: {seats_created} seats')
            
            self.stdout.write(f'✅ Created {total_seats:,} seats for FNB Stadium')
            
            self.stdout.write('⚽ Creating international matches...')
            
            # Create upcoming international matches
            now = timezone.now()
            
            matches = [
                {
                    'name': 'Bafana Bafana vs Nigeria',
                    'home_team': 'South Africa',
                    'away_team': 'Nigeria',
                    'match_type': 'FRIENDLY',
                    'stadium': fnb_stadium,
                    'match_date': now + timedelta(days=45),
                    'tickets_available': 20000,
                    'sales_open_date': now + timedelta(days=1),
                    'sales_close_date': now + timedelta(days=44),
                    'early_bird_end_date': now + timedelta(days=30),
                    'description': 'International friendly match between South Africa and Nigeria at the iconic FNB Stadium.'
                },
                {
                    'name': 'Bafana Bafana vs Ghana',
                    'home_team': 'South Africa',
                    'away_team': 'Ghana',
                    'match_type': 'AFCON',
                    'stadium': fnb_stadium,
                    'match_date': now + timedelta(days=75),
                    'tickets_available': 25000,
                    'sales_open_date': now + timedelta(days=10),
                    'sales_close_date': now + timedelta(days=74),
                    'early_bird_end_date': now + timedelta(days=50),
                    'description': 'AFCON qualifier match - a crucial game for World Cup qualification.'
                },
                {
                    'name': 'Bafana Bafana vs Egypt',
                    'home_team': 'South Africa',
                    'away_team': 'Egypt',
                    'match_type': 'QUALIFIER',
                    'stadium': fnb_stadium,
                    'match_date': now + timedelta(days=120),
                    'tickets_available': 30000,
                    'sales_open_date': now + timedelta(days=30),
                    'sales_close_date': now + timedelta(days=119),
                    'early_bird_end_date': now + timedelta(days=90),
                    'description': 'World Cup qualifier against Egypt - the Pharaohs come to Johannesburg!'
                },
            ]
            
            for match_data in matches:
                match = InternationalMatch.objects.create(**match_data)
                self.stdout.write(f'   ⚽ {match.name} - {match.match_date.strftime("%Y-%m-%d")}')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Sample data creation complete!\n'
                    f'   Stadiums: {Stadium.objects.count()}\n'
                    f'   Total seats: {SeatMap.objects.count():,}\n'
                    f'   International matches: {InternationalMatch.objects.count()}\n'
                    f'\n📋 Next steps:\n'
                    f'   1. Visit /admin/ to manage events\n'
                    f'   2. Visit /events/dashboard/ for events dashboard\n'
                    f'   3. Use import_seat_map command for more stadiums\n'
                    f'   4. Test ticket purchasing with supporters'
                )
            )
