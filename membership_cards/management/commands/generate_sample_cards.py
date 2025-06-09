from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from membership_cards.models import DigitalCard, PhysicalCard
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate sample cards for testing'
    
    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=5, help='Number of sample cards to create')
    
    def handle(self, *args, **options):
        users_count = options['users']
        
        # Get active users without cards
        users_without_cards = User.objects.filter(
            membership_status='ACTIVE'
        ).exclude(
            digital_card__isnull=False
        )[:users_count]
        
        if not users_without_cards:
            self.stdout.write(
                self.style.WARNING('No active users without cards found')
            )
            return
        
        created_count = 0
        for user in users_without_cards:
            try:
                # Ensure user has SAFA ID
                if not user.safa_id:
                    user.generate_safa_id()
                    user.save()
                
                # Create digital card
                digital_card = DigitalCard.objects.create(
                    user=user,
                    expires_date=timezone.now().date() + timedelta(days=365),
                    status='ACTIVE'
                )
                
                # Create physical card if requested
                if user.physical_card_requested:
                    PhysicalCard.objects.create(
                        user=user,
                        card_number=digital_card.card_number,
                        shipping_address=user.physical_card_delivery_address or 'Sample Address'
                    )
                
                created_count += 1
                self.stdout.write(f'Created cards for {user.get_full_name()}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to create card for {user.email}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample cards')
        )
