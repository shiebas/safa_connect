from django.core.management.base import BaseCommand
from supporters.models import SupporterProfile, SupporterPreferences


class Command(BaseCommand):
    help = 'Migrate existing supporter profiles to have preferences'

    def handle(self, *args, **options):
        """Ensure all supporter profiles have associated preferences"""
        
        profiles_without_preferences = SupporterProfile.objects.filter(preferences__isnull=True)
        count = profiles_without_preferences.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('All supporter profiles already have preferences set up.')
            )
            return
        
        self.stdout.write(f'Found {count} supporter profiles without preferences. Creating them...')
        
        created_count = 0
        for profile in profiles_without_preferences:
            try:
                # Create default preferences
                preferences = SupporterPreferences.objects.create(
                    # Set some sensible defaults
                    email_notifications=True,
                    communication_frequency='WEEKLY',
                    discount_tickets=True,  # Most supporters would want this
                    international_matches=True,  # Popular choice
                    local_matches=True,  # Popular choice
                )
                
                # Link to profile
                profile.preferences = preferences
                profile.save()
                
                created_count += 1
                self.stdout.write(f'Created preferences for {profile.user.get_full_name()}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating preferences for {profile.user.get_full_name()}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created preferences for {created_count} supporter profiles.')
        )
        
        # Show summary statistics
        total_profiles = SupporterProfile.objects.count()
        profiles_with_preferences = SupporterProfile.objects.filter(preferences__isnull=False).count()
        
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'Total supporter profiles: {total_profiles}')
        self.stdout.write(f'Profiles with preferences: {profiles_with_preferences}')
        self.stdout.write(f'Migration complete!')
