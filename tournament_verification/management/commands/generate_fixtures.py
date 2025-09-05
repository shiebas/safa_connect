from django.core.management.base import BaseCommand, CommandError
from tournament_verification.tournament_models import TournamentCompetition
from tournament_verification.fixture_generator import generate_tournament_fixtures


class Command(BaseCommand):
    help = 'Generate fixtures for tournaments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tournament-id',
            type=str,
            help='Generate fixtures for a specific tournament ID',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Generate fixtures for all tournaments',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerate fixtures even if they already exist',
        )

    def handle(self, *args, **options):
        if options['tournament_id']:
            self.generate_for_tournament(options['tournament_id'], options['force'])
        elif options['all']:
            self.generate_for_all_tournaments(options['force'])
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --tournament-id or --all')
            )

    def generate_for_tournament(self, tournament_id, force=False):
        try:
            tournament = TournamentCompetition.objects.get(id=tournament_id)
            
            # Check if fixtures already exist
            if tournament.fixtures.exists() and not force:
                self.stdout.write(
                    self.style.WARNING(
                        f'Fixtures already exist for tournament "{tournament.name}". '
                        'Use --force to regenerate.'
                    )
                )
                return
            
            # Check if tournament has teams
            if not tournament.teams.exists():
                self.stdout.write(
                    self.style.ERROR(
                        f'No teams found for tournament "{tournament.name}". '
                        'Please add teams before generating fixtures.'
                    )
                )
                return
            
            self.stdout.write(f'Generating fixtures for tournament: {tournament.name}')
            
            # Generate fixtures
            fixtures = generate_tournament_fixtures(tournament_id)
            
            if fixtures:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully generated {len(fixtures)} fixtures for "{tournament.name}"'
                    )
                )
                
                # Display fixture summary
                self.stdout.write('\nFixture Summary:')
                for fixture in fixtures[:5]:  # Show first 5 fixtures
                    self.stdout.write(f'  - {fixture}')
                
                if len(fixtures) > 5:
                    self.stdout.write(f'  ... and {len(fixtures) - 5} more fixtures')
            else:
                self.stdout.write(
                    self.style.ERROR('No fixtures were generated')
                )
                
        except TournamentCompetition.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Tournament with ID {tournament_id} not found')
            )

    def generate_for_all_tournaments(self, force=False):
        tournaments = TournamentCompetition.objects.all()
        
        if not tournaments.exists():
            self.stdout.write(
                self.style.WARNING('No tournaments found')
            )
            return
        
        self.stdout.write(f'Generating fixtures for {tournaments.count()} tournaments...')
        
        success_count = 0
        for tournament in tournaments:
            try:
                # Check if fixtures already exist
                if tournament.fixtures.exists() and not force:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping "{tournament.name}" - fixtures already exist'
                        )
                    )
                    continue
                
                # Check if tournament has teams
                if not tournament.teams.exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping "{tournament.name}" - no teams found'
                        )
                    )
                    continue
                
                # Generate fixtures
                fixtures = generate_tournament_fixtures(str(tournament.id))
                
                if fixtures:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Generated {len(fixtures)} fixtures for "{tournament.name}"'
                        )
                    )
                    success_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Failed to generate fixtures for "{tournament.name}"'
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error generating fixtures for "{tournament.name}": {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Successfully generated fixtures for {success_count} tournaments.'
            )
        )


