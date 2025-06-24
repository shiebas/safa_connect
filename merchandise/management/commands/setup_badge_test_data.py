from django.core.management.base import BaseCommand
from merchandise.models import Product
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Set up test data to showcase badge stacking functionality'

    def handle(self, *args, **options):
        products = Product.objects.filter(status='ACTIVE')[:6]
        
        if not products:
            self.stdout.write(self.style.ERROR('No active products found. Run populate_merchandise first.'))
            return
            
        # Create different badge combinations
        scenarios = [
            {'name': 'On Sale Only', 'sale_price': True, 'featured': False},
            {'name': 'Featured Only', 'sale_price': False, 'featured': True},
            {'name': 'On Sale + Featured', 'sale_price': True, 'featured': True},
            {'name': 'All Badges (with New)', 'sale_price': True, 'featured': True},  # We'll make this "new" by backdating it
            {'name': 'New Only', 'sale_price': False, 'featured': False},  # Will be made "new"
            {'name': 'Featured + New', 'sale_price': False, 'featured': True},  # Will be made "new"
        ]
        
        for i, product in enumerate(products):
            if i >= len(scenarios):
                break
                
            scenario = scenarios[i]
            
            # Set sale price
            if scenario['sale_price']:
                original_price = product.price
                discount = Decimal('0.20')  # 20% discount
                product.sale_price = original_price * (Decimal('1') - discount)
            else:
                product.sale_price = None
                
            # Set featured status
            product.is_featured = scenario['featured']
            
            # For "new" products, we'll update created_at to be recent
            # (The template filter checks if created within last 30 days)
            if 'New' in scenario['name']:
                from django.utils import timezone
                from datetime import timedelta
                # Set created_at to 5 days ago to make it "new"
                product.created_at = timezone.now() - timedelta(days=5)
            else:
                # Set created_at to 60 days ago to make it "old"
                from django.utils import timezone
                from datetime import timedelta
                product.created_at = timezone.now() - timedelta(days=60)
            
            product.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated "{product.name}" for scenario: {scenario["name"]}'
                )
            )
            
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set up badge test data for {len(products)} products!'
            )
        )
        
        # Print summary
        self.stdout.write('\n=== BADGE TEST DATA SUMMARY ===')
        for product in products:
            badges = []
            if product.is_on_sale:
                badges.append(f'SALE ({product.discount_percentage}%)')
            if product.is_featured:
                badges.append('FEATURED')
            
            # Check if new (created within last 30 days)
            from django.utils import timezone
            from datetime import timedelta
            if product.created_at >= timezone.now() - timedelta(days=30):
                badges.append('NEW')
                
            badge_str = ', '.join(badges) if badges else 'No badges'
            self.stdout.write(f'{product.name}: {badge_str}')
