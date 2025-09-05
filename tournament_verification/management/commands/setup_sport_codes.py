from django.core.management.base import BaseCommand
from tournament_verification.tournament_models import SportCode

class Command(BaseCommand):
    help = 'Set up default sport codes for tournaments'

    def handle(self, *args, **options):
        sport_codes = [
            {
                'code': 'SOCCER',
                'name': 'Soccer/Football',
                'description': 'Association football with 11 players per team',
                'players_per_team': 11,
                'match_duration_minutes': 90,
                'has_extra_time': True,
                'has_penalties': True,
                'points_for_win': 3,
                'points_for_draw': 1,
                'points_for_loss': 0,
                'field_length_min': 90,
                'field_length_max': 120,
                'field_width_min': 45,
                'field_width_max': 90,
            },
            {
                'code': 'RUGBY',
                'name': 'Rugby Union',
                'description': 'Rugby union with 15 players per team',
                'players_per_team': 15,
                'match_duration_minutes': 80,
                'has_extra_time': True,
                'has_penalties': False,
                'points_for_win': 4,
                'points_for_draw': 2,
                'points_for_loss': 0,
                'field_length_min': 100,
                'field_length_max': 144,
                'field_width_min': 68,
                'field_width_max': 70,
            },
            {
                'code': 'BASKETBALL',
                'name': 'Basketball',
                'description': 'Basketball with 5 players per team',
                'players_per_team': 5,
                'match_duration_minutes': 48,
                'has_extra_time': True,
                'has_penalties': False,
                'points_for_win': 2,
                'points_for_draw': 1,
                'points_for_loss': 0,
                'field_length_min': 28,
                'field_length_max': 28,
                'field_width_min': 15,
                'field_width_max': 15,
            },
            {
                'code': 'TENNIS',
                'name': 'Tennis',
                'description': 'Tennis singles and doubles',
                'players_per_team': 1,
                'match_duration_minutes': 120,
                'has_extra_time': False,
                'has_penalties': False,
                'points_for_win': 1,
                'points_for_draw': 0,
                'points_for_loss': 0,
                'field_length_min': 23.77,
                'field_length_max': 23.77,
                'field_width_min': 8.23,
                'field_width_max': 10.97,
            },
            {
                'code': 'CRICKET',
                'name': 'Cricket',
                'description': 'Cricket with 11 players per team',
                'players_per_team': 11,
                'match_duration_minutes': 180,
                'has_extra_time': False,
                'has_penalties': False,
                'points_for_win': 2,
                'points_for_draw': 1,
                'points_for_loss': 0,
                'field_length_min': 137,
                'field_length_max': 150,
                'field_width_min': 137,
                'field_width_max': 150,
            },
            {
                'code': 'ATHLETICS',
                'name': 'Athletics',
                'description': 'Track and field athletics',
                'players_per_team': 1,
                'match_duration_minutes': 60,
                'has_extra_time': False,
                'has_penalties': False,
                'points_for_win': 1,
                'points_for_draw': 0,
                'points_for_loss': 0,
                'field_length_min': 400,
                'field_length_max': 400,
                'field_width_min': 200,
                'field_width_max': 200,
            },
            {
                'code': 'SWIMMING',
                'name': 'Swimming',
                'description': 'Competitive swimming',
                'players_per_team': 1,
                'match_duration_minutes': 30,
                'has_extra_time': False,
                'has_penalties': False,
                'points_for_win': 1,
                'points_for_draw': 0,
                'points_for_loss': 0,
                'field_length_min': 50,
                'field_length_max': 50,
                'field_width_min': 25,
                'field_width_max': 25,
            },
        ]

        created_count = 0
        updated_count = 0

        for sport_data in sport_codes:
            sport_code, created = SportCode.objects.get_or_create(
                code=sport_data['code'],
                defaults=sport_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created sport code: {sport_code.name}')
                )
            else:
                # Update existing sport code
                for key, value in sport_data.items():
                    if key != 'code':
                        setattr(sport_code, key, value)
                sport_code.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated sport code: {sport_code.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(sport_codes)} sport codes. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )


