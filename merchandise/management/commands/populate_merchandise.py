from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from merchandise.models import ProductCategory, Product, ProductVariant
from decimal import Decimal
import requests
import io


class Command(BaseCommand):
    help = 'Populate the merchandise store with sample SAFA products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing products before adding new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing products...')
            Product.objects.all().delete()
            ProductCategory.objects.all().delete()

        self.stdout.write('Creating SAFA merchandise categories...')
        self.create_categories()
        
        self.stdout.write('Creating SAFA products...')
        self.create_products()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated SAFA merchandise store!')
        )

    def create_categories(self):
        """Create product categories"""
        categories_data = [
            {
                'name': 'Official Jerseys',
                'description': 'Official SAFA team jerseys and kits',
                'is_featured': True,
                'display_order': 1
            },
            {
                'name': 'Training Gear',
                'description': 'Professional training equipment and apparel',
                'is_featured': True,
                'display_order': 2
            },
            {
                'name': 'Casual Wear',
                'description': 'Casual SAFA branded clothing and accessories',
                'is_featured': True,
                'display_order': 3
            },
            {
                'name': 'Accessories',
                'description': 'SAFA branded accessories and collectibles',
                'is_featured': True,
                'display_order': 4
            },
            {
                'name': 'Equipment',
                'description': 'Football equipment and gear',
                'is_featured': False,
                'display_order': 5
            },
            {
                'name': 'Souvenirs',
                'description': 'Collectible SAFA memorabilia and souvenirs',
                'is_featured': False,
                'display_order': 6
            }
        ]

        for cat_data in categories_data:
            category = ProductCategory.objects.create(
                name=cat_data['name'],
                slug=slugify(cat_data['name']),
                description=cat_data['description'],
                is_featured=cat_data['is_featured'],
                display_order=cat_data['display_order'],
                is_active=True
            )
            self.stdout.write(f'Created category: {category.name}')

    def create_products(self):
        """Create sample products"""
        # Get categories
        jerseys = ProductCategory.objects.get(slug='official-jerseys')
        training = ProductCategory.objects.get(slug='training-gear')
        casual = ProductCategory.objects.get(slug='casual-wear')
        accessories = ProductCategory.objects.get(slug='accessories')
        equipment = ProductCategory.objects.get(slug='equipment')
        souvenirs = ProductCategory.objects.get(slug='souvenirs')

        products_data = [
            # Official Jerseys
            {
                'name': 'Bafana Bafana Home Jersey 2024',
                'category': jerseys,
                'description': 'Official home jersey of the South African national football team. Features moisture-wicking technology and the iconic gold and green design.',
                'short_description': 'Official Bafana Bafana home jersey with moisture-wicking technology',
                'price': Decimal('899.00'),
                'sale_price': Decimal('799.00'),
                'sku': 'SAFA-HOME-2024',
                'is_featured': True,
                'stock_quantity': 50,
                'tags': 'jersey, bafana bafana, home, official, 2024',
                'variants': [
                    {'name': 'Small', 'size': 'S', 'stock': 10},
                    {'name': 'Medium', 'size': 'M', 'stock': 15},
                    {'name': 'Large', 'size': 'L', 'stock': 15},
                    {'name': 'X-Large', 'size': 'XL', 'stock': 8},
                    {'name': 'XX-Large', 'size': 'XXL', 'stock': 2}
                ]
            },
            {
                'name': 'Bafana Bafana Away Jersey 2024',
                'category': jerseys,
                'description': 'Official away jersey featuring a sleek white design with gold accents. Perfect for supporters following the team abroad.',
                'short_description': 'Official Bafana Bafana away jersey in white with gold accents',
                'price': Decimal('899.00'),
                'sku': 'SAFA-AWAY-2024',
                'is_featured': True,
                'stock_quantity': 45,
                'tags': 'jersey, bafana bafana, away, official, 2024',
                'variants': [
                    {'name': 'Small', 'size': 'S', 'stock': 8},
                    {'name': 'Medium', 'size': 'M', 'stock': 12},
                    {'name': 'Large', 'size': 'L', 'stock': 15},
                    {'name': 'X-Large', 'size': 'XL', 'stock': 7},
                    {'name': 'XX-Large', 'size': 'XXL', 'stock': 3}
                ]
            },
            {
                'name': 'Banyana Banyana Home Jersey 2024',
                'category': jerseys,
                'description': 'Official home jersey of the South African womens national football team. Celebrating the success of our female football stars.',
                'short_description': 'Official Banyana Banyana home jersey',
                'price': Decimal('849.00'),
                'sku': 'SAFA-BANYANA-HOME-2024',
                'is_featured': True,
                'stock_quantity': 35,
                'tags': 'jersey, banyana banyana, womens, home, official, 2024',
                'variants': [
                    {'name': 'Small', 'size': 'S', 'stock': 10},
                    {'name': 'Medium', 'size': 'M', 'stock': 12},
                    {'name': 'Large', 'size': 'L', 'stock': 8},
                    {'name': 'X-Large', 'size': 'XL', 'stock': 5}
                ]
            },

            # Training Gear
            {
                'name': 'SAFA Training Polo Shirt',
                'category': training,
                'description': 'Professional training polo shirt used by SAFA coaching staff. Breathable fabric with SAFA logo embroidery.',
                'short_description': 'Professional training polo with SAFA logo',
                'price': Decimal('399.00'),
                'sku': 'SAFA-TRAIN-POLO',
                'stock_quantity': 60,
                'tags': 'training, polo, coaching, professional',
                'variants': [
                    {'name': 'Small', 'size': 'S', 'stock': 15},
                    {'name': 'Medium', 'size': 'M', 'stock': 20},
                    {'name': 'Large', 'size': 'L', 'stock': 15},
                    {'name': 'X-Large', 'size': 'XL', 'stock': 10}
                ]
            },
            {
                'name': 'SAFA Training Shorts',
                'category': training,
                'description': 'High-performance training shorts with moisture-wicking technology. Perfect for training sessions and workouts.',
                'short_description': 'Performance training shorts with moisture-wicking',
                'price': Decimal('299.00'),
                'sale_price': Decimal('249.00'),
                'sku': 'SAFA-TRAIN-SHORTS',
                'stock_quantity': 40,
                'tags': 'training, shorts, performance, moisture-wicking'
            },
            {
                'name': 'SAFA Football Training Cones Set',
                'category': training,
                'description': 'Professional training cones set of 20. Essential for football training drills and exercises.',
                'short_description': 'Set of 20 professional training cones',
                'price': Decimal('199.00'),
                'sku': 'SAFA-CONES-20',
                'stock_quantity': 25,
                'tags': 'training, cones, equipment, drills'
            },

            # Casual Wear
            {
                'name': 'SAFA Casual T-Shirt',
                'category': casual,
                'description': 'Comfortable cotton t-shirt with stylish SAFA logo. Perfect for everyday wear and showing your support.',
                'short_description': 'Comfortable cotton t-shirt with SAFA logo',
                'price': Decimal('249.00'),
                'sku': 'SAFA-CASUAL-TEE',
                'is_featured': True,
                'stock_quantity': 80,
                'tags': 'casual, t-shirt, cotton, everyday',
                'variants': [
                    {'name': 'Small', 'size': 'S', 'stock': 20},
                    {'name': 'Medium', 'size': 'M', 'stock': 25},
                    {'name': 'Large', 'size': 'L', 'stock': 20},
                    {'name': 'X-Large', 'size': 'XL', 'stock': 15}
                ]
            },
            {
                'name': 'SAFA Hoodie',
                'category': casual,
                'description': 'Warm and comfortable hoodie with embroidered SAFA logo. Perfect for cooler weather or casual outings.',
                'short_description': 'Warm hoodie with embroidered SAFA logo',
                'price': Decimal('599.00'),
                'sku': 'SAFA-HOODIE',
                'stock_quantity': 30,
                'tags': 'casual, hoodie, warm, embroidered'
            },
            {
                'name': 'SAFA Track Suit',
                'category': casual,
                'description': 'Complete track suit set with jacket and pants. Comfortable fit with SAFA branding.',
                'short_description': 'Complete track suit set with SAFA branding',
                'price': Decimal('899.00'),
                'sale_price': Decimal('749.00'),
                'sku': 'SAFA-TRACKSUIT',
                'stock_quantity': 20,
                'tags': 'casual, tracksuit, set, comfortable'
            },

            # Accessories
            {
                'name': 'SAFA Baseball Cap',
                'category': accessories,
                'description': 'Classic baseball cap with embroidered SAFA logo. Adjustable strap for perfect fit.',
                'short_description': 'Classic baseball cap with SAFA logo',
                'price': Decimal('199.00'),
                'sku': 'SAFA-CAP',
                'stock_quantity': 50,
                'tags': 'accessories, cap, hat, embroidered'
            },
            {
                'name': 'SAFA Scarf',
                'category': accessories,
                'description': 'Official SAFA supporters scarf in team colors. Essential for match days and cold weather.',
                'short_description': 'Official supporters scarf in team colors',
                'price': Decimal('149.00'),
                'sku': 'SAFA-SCARF',
                'is_featured': True,
                'stock_quantity': 75,
                'tags': 'accessories, scarf, supporters, match day'
            },
            {
                'name': 'SAFA Water Bottle',
                'category': accessories,
                'description': 'BPA-free sports water bottle with SAFA logo. 750ml capacity, perfect for training and matches.',
                'short_description': 'BPA-free sports water bottle 750ml',
                'price': Decimal('89.00'),
                'sku': 'SAFA-BOTTLE',
                'stock_quantity': 100,
                'tags': 'accessories, bottle, sports, hydration'
            },

            # Equipment
            {
                'name': 'Official SAFA Match Ball',
                'category': equipment,
                'description': 'Official match ball used in SAFA competitions. FIFA Quality Pro certified.',
                'short_description': 'FIFA Quality Pro certified match ball',
                'price': Decimal('599.00'),
                'sku': 'SAFA-BALL-MATCH',
                'stock_quantity': 15,
                'tags': 'equipment, ball, match, official, FIFA'
            },
            {
                'name': 'SAFA Goalkeeper Gloves',
                'category': equipment,
                'description': 'Professional goalkeeper gloves with superior grip and protection. Used by SAFA keepers.',
                'short_description': 'Professional goalkeeper gloves with superior grip',
                'price': Decimal('449.00'),
                'sku': 'SAFA-GK-GLOVES',
                'stock_quantity': 12,
                'tags': 'equipment, gloves, goalkeeper, professional'
            },

            # Souvenirs
            {
                'name': 'SAFA Keychain',
                'category': souvenirs,
                'description': 'Metal keychain with SAFA logo. Perfect souvenir or gift for football fans.',
                'short_description': 'Metal keychain with SAFA logo',
                'price': Decimal('39.00'),
                'sku': 'SAFA-KEYCHAIN',
                'stock_quantity': 200,
                'tags': 'souvenirs, keychain, gift, metal'
            },
            {
                'name': 'SAFA Mug',
                'category': souvenirs,
                'description': 'Ceramic mug with SAFA logo and team colors. Dishwasher safe, 350ml capacity.',
                'short_description': 'Ceramic mug with SAFA logo, 350ml',
                'price': Decimal('99.00'),
                'sku': 'SAFA-MUG',
                'stock_quantity': 60,
                'tags': 'souvenirs, mug, ceramic, dishwasher safe'
            },
            {
                'name': 'SAFA Car Sticker Set',
                'category': souvenirs,
                'description': 'Set of 5 weatherproof car stickers with various SAFA designs. Show your support on the road.',
                'short_description': 'Set of 5 weatherproof car stickers',
                'price': Decimal('69.00'),
                'sku': 'SAFA-STICKERS',
                'stock_quantity': 150,
                'tags': 'souvenirs, stickers, car, weatherproof, set'
            }
        ]

        for product_data in products_data:
            # Create the product
            variants_data = product_data.pop('variants', [])
            
            # Generate unique slug
            product_data['slug'] = slugify(product_data['name'])
            
            product = Product.objects.create(
                **product_data,
                status='ACTIVE',
                manage_stock=True,
                requires_shipping=True
            )

            # Create variants if specified
            for i, variant_data in enumerate(variants_data, 1):
                ProductVariant.objects.create(
                    product=product,
                    name=variant_data['name'],
                    size=variant_data['size'],
                    sku=f"{product.sku}-{variant_data['size']}",
                    stock_quantity=variant_data['stock'],
                    is_active=True
                )

            self.stdout.write(f'Created product: {product.name}')

        self.stdout.write(f'Created {Product.objects.count()} products total')
