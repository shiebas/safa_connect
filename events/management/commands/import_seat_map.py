import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from events.models import Stadium, SeatMap


class Command(BaseCommand):
    help = 'Bulk upload seat map from CSV file'
    
    def add_arguments(self, parser):
        parser.add_argument('stadium_id', type=str, help='Stadium UUID')
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument('--clear', action='store_true', help='Clear existing seats first')
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
        
    def handle(self, *args, **options):
        stadium_id = options['stadium_id']
        csv_file = options['csv_file']
        clear_existing = options['clear']
        dry_run = options['dry_run']
        
        try:
            stadium = Stadium.objects.get(id=stadium_id)
        except Stadium.DoesNotExist:
            raise CommandError(f'Stadium with ID {stadium_id} does not exist')
        
        self.stdout.write(f'🏟️  Processing seats for: {stadium.name}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be saved'))
        
        # Read and validate CSV
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Expected columns
                required_columns = ['section', 'row', 'seat_number', 'price_tier', 'base_price']
                optional_columns = ['is_wheelchair_accessible', 'has_restricted_view', 'notes']
                
                # Validate headers
                headers = reader.fieldnames
                missing_columns = set(required_columns) - set(headers)
                if missing_columns:
                    raise CommandError(f'Missing required columns: {", ".join(missing_columns)}')
                
                self.stdout.write('📋 CSV Headers validated successfully')
                self.stdout.write(f'   Required: {", ".join(required_columns)}')
                self.stdout.write(f'   Optional: {", ".join([col for col in optional_columns if col in headers])}')
                
                # Process rows
                seats_to_create = []
                errors = []
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 because header is row 1
                    try:
                        # Validate required fields
                        for col in required_columns:
                            if not row[col].strip():
                                errors.append(f'Row {row_num}: {col} is required')
                                continue
                        
                        # Validate price_tier
                        valid_tiers = ['PREMIUM', 'VIP', 'STANDARD', 'ECONOMY', 'STUDENT', 'CORPORATE']
                        if row['price_tier'].upper() not in valid_tiers:
                            errors.append(f'Row {row_num}: Invalid price_tier "{row["price_tier"]}". Must be one of: {", ".join(valid_tiers)}')
                            continue
                        
                        # Validate base_price
                        try:
                            base_price = float(row['base_price'])
                            if base_price < 0:
                                errors.append(f'Row {row_num}: base_price must be positive')
                                continue
                        except ValueError:
                            errors.append(f'Row {row_num}: base_price must be a valid number')
                            continue
                        
                        # Create seat object
                        seat_data = {
                            'stadium': stadium,
                            'section': row['section'].strip().upper(),
                            'row': row['row'].strip().upper(),
                            'seat_number': row['seat_number'].strip(),
                            'price_tier': row['price_tier'].strip().upper(),
                            'base_price': base_price,
                        }
                        
                        # Optional fields
                        if 'is_wheelchair_accessible' in headers:
                            seat_data['is_wheelchair_accessible'] = row['is_wheelchair_accessible'].lower() in ['true', '1', 'yes', 'y']
                        
                        if 'has_restricted_view' in headers:
                            seat_data['has_restricted_view'] = row['has_restricted_view'].lower() in ['true', '1', 'yes', 'y']
                        
                        if 'notes' in headers:
                            seat_data['notes'] = row['notes'].strip()
                        
                        seats_to_create.append(seat_data)
                        
                    except Exception as e:
                        errors.append(f'Row {row_num}: {str(e)}')
                
                # Report validation errors
                if errors:
                    self.stdout.write(self.style.ERROR(f'❌ Found {len(errors)} validation errors:'))
                    for error in errors[:10]:  # Show first 10 errors
                        self.stdout.write(f'   {error}')
                    if len(errors) > 10:
                        self.stdout.write(f'   ... and {len(errors) - 10} more errors')
                    return
                
                self.stdout.write(f'✅ Validation complete: {len(seats_to_create)} seats ready to import')
                
                if dry_run:
                    # Show preview
                    self.stdout.write('\n📋 Preview of seats to be created:')
                    for i, seat in enumerate(seats_to_create[:5]):  # Show first 5
                        self.stdout.write(f'   {seat["section"]}{seat["row"]}-{seat["seat_number"]} ({seat["price_tier"]}) - R{seat["base_price"]}')
                    if len(seats_to_create) > 5:
                        self.stdout.write(f'   ... and {len(seats_to_create) - 5} more seats')
                    return
                
                # Import seats
                with transaction.atomic():
                    if clear_existing:
                        existing_count = stadium.seats.count()
                        if existing_count > 0:
                            stadium.seats.all().delete()
                            self.stdout.write(f'🗑️  Deleted {existing_count} existing seats')
                    
                    # Create seats in batches
                    batch_size = 1000
                    created_count = 0
                    
                    for i in range(0, len(seats_to_create), batch_size):
                        batch = seats_to_create[i:i + batch_size]
                        seat_objects = [SeatMap(**seat_data) for seat_data in batch]
                        
                        try:
                            SeatMap.objects.bulk_create(seat_objects, ignore_conflicts=False)
                            created_count += len(seat_objects)
                            self.stdout.write(f'📥 Created batch {i//batch_size + 1}: {len(seat_objects)} seats')
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Error creating batch: {str(e)}'))
                            raise
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'\n🎉 Import complete!\n'
                            f'   Stadium: {stadium.name}\n'
                            f'   Seats created: {created_count:,}\n'
                            f'   Total seats: {stadium.seats.count():,}'
                        )
                    )
                    
                    # Summary by price tier
                    self.stdout.write('\n📊 Summary by price tier:')
                    from django.db.models import Count
                    tier_summary = stadium.seats.values('price_tier').annotate(
                        count=Count('id')
                    ).order_by('price_tier')
                    
                    for tier in tier_summary:
                        self.stdout.write(f'   {tier["price_tier"]}: {tier["count"]:,} seats')
        
        except FileNotFoundError:
            raise CommandError(f'CSV file not found: {csv_file}')
        except Exception as e:
            raise CommandError(f'Error processing file: {str(e)}')
