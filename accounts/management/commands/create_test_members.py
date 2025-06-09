from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from geography.models import Province, Region, LocalFootballAssociation, Club
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test members across different regions'
    
    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10, help='Number of test members')
    
    def handle(self, *args, **options):
        count = options['count']
        
        # Get geography data
        provinces = list(Province.objects.filter(is_active=True))
        lfas = list(LocalFootballAssociation.objects.filter(is_active=True))
        clubs = list(Club.objects.filter(is_active=True))
        
        if not provinces or not lfas:
            self.stdout.write(
                self.style.ERROR('❌ No geography data found. Run: python manage.py load_complete_geography')
            )
            return
        
        roles = ['player', 'coach', 'official', 'administrator']
        
        created_count = 0
        for i in range(count):
            try:
                # Random geography selection
                lfa = random.choice(lfas)
                region = lfa.region
                province = region.province
                club = random.choice(clubs) if clubs else None
                
                # Create test user
                email = f'test.member.{i+1}@safa.co.za'
                if User.objects.filter(email=email).exists():
                    continue
                
                user = User.objects.create_user(
                    email=email,
                    password='TestPass123!',
                    name=f'Test{i+1}',
                    surname=f'Member{i+1}',
                    role=random.choice(roles),
                    province=province,
                    region=region,
                    lfa=lfa,
                    club=club,
                    membership_status='ACTIVE',
                    phone_number=f'+27{random.randint(700000000, 799999999)}',
                    id_number=f'{random.randint(8000000000000, 9999999999999)}'
                )
                
                # Generate SAFA ID
                user.generate_safa_id()
                user.save()
                
                created_count += 1
                self.stdout.write(f'✅ Created: {user.get_full_name()} ({user.safa_id})')
                
            except Exception as e:
                self.stdout.write(f'❌ Error creating member {i+1}: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(f'🎉 Created {created_count} test members')
        )
