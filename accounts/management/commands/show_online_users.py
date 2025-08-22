from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Displays users who are currently online.'

    def handle(self, *args, **options):
        # Get all non-expired sessions
        sessions = Session.objects.filter(expire_date__gte=timezone.now())

        # Get user IDs from sessions
        user_ids = []
        for session in sessions:
            session_data = session.get_decoded()
            user_id = session_data.get('_auth_user_id')
            if user_id:
                user_ids.append(user_id)

        if not user_ids:
            self.stdout.write(self.style.SUCCESS('No users are currently online.'))
            return

        # Get user objects
        online_users = CustomUser.objects.filter(id__in=user_ids).select_related('province', 'region')

        self.stdout.write(self.style.SUCCESS(f'Found {len(online_users)} online user(s):'))
        for user in online_users:
            province = user.province.name if user.province else 'N/A'
            region = user.region.name if user.region else 'N/A'
            self.stdout.write(f'- {user.get_full_name()} ({user.email}) - Province: {province}, Region: {region}')
