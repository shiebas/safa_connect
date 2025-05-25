from django.core.management.base import BaseCommand
from geography.models import Continent, WorldSportsBody, ContinentFederation

class Command(BaseCommand):
    help = 'Populate initial data for continents, world sports bodies, and some federations'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data population...'))
        
        # Create Continents
        continents_data = [
            {'name': 'Europe', 'code': 'EUR'},
            {'name': 'Asia', 'code': 'ASI'},
            {'name': 'Africa', 'code': 'AFR'},
            {'name': 'North America', 'code': 'NAM'},
            {'name': 'South America', 'code': 'SAM'},
            {'name': 'Oceania', 'code': 'OCE'},
        ]
        
        continents = {}
        for continent_data in continents_data:
            continent, created = Continent.objects.get_or_create(
                code=continent_data['code'],
                defaults={'name': continent_data['name']}
            )
            continents[continent_data['code']] = continent
            if created:
                self.stdout.write(f'Created continent: {continent.name}')
        
        # Create World Sports Bodies
        world_bodies_data = [
            {
                'name': 'Fédération Internationale de Football Association',
                'acronym': 'FIFA',
                'sport_code': 'FOOT',
                'description': 'The international governing body of association football',
                'website': 'https://www.fifa.com',
                'continents': ['EUR', 'ASI', 'AFR', 'NAM', 'SAM', 'OCE']
            },
            {
                'name': 'World Rugby',
                'acronym': 'WR',
                'sport_code': 'RUGBY',
                'description': 'The world governing body for rugby union',
                'website': 'https://www.world.rugby',
                'continents': ['EUR', 'ASI', 'AFR', 'NAM', 'SAM', 'OCE']
            },
            {
                'name': 'International Cricket Council',
                'acronym': 'ICC',
                'sport_code': 'CRICK',
                'description': 'The global governing body of cricket',
                'website': 'https://www.icc-cricket.com',
                'continents': ['EUR', 'ASI', 'AFR', 'NAM', 'SAM', 'OCE']
            },
            {
                'name': 'International Basketball Federation',
                'acronym': 'FIBA',
                'sport_code': 'BASK',
                'description': 'The international governing body for basketball',
                'website': 'https://www.fiba.basketball',
                'continents': ['EUR', 'ASI', 'AFR', 'NAM', 'SAM', 'OCE']
            },
        ]
        
        world_bodies = {}
        for wb_data in world_bodies_data:
            continents_for_wb = wb_data.pop('continents')
            world_body, created = WorldSportsBody.objects.get_or_create(
                acronym=wb_data['acronym'],
                defaults=wb_data
            )
            
            # Add continents to world body
            for continent_code in continents_for_wb:
                if continent_code in continents:
                    world_body.continents.add(continents[continent_code])
            
            world_bodies[wb_data['acronym']] = world_body
            if created:
                self.stdout.write(f'Created world sports body: {world_body.acronym}')
        
        # Create sample Continent Federations
        federations_data = [
            # FIFA Football Federations
            {
                'name': 'Union of European Football Associations',
                'acronym': 'UEFA',
                'sport_code': 'FOOT',
                'world_body_acronym': 'FIFA',
                'continent_code': 'EUR',
                'website': 'https://www.uefa.com',
                'description': 'The administrative body for football in Europe'
            },
            {
                'name': 'Confederation of African Football',
                'acronym': 'CAF',
                'sport_code': 'FOOT',
                'world_body_acronym': 'FIFA',
                'continent_code': 'AFR',
                'website': 'https://www.cafonline.com',
                'description': 'The administrative body for football in Africa'
            },
            {
                'name': 'Asian Football Confederation',
                'acronym': 'AFC',
                'sport_code': 'FOOT',
                'world_body_acronym': 'FIFA',
                'continent_code': 'ASI',
                'website': 'https://www.the-afc.com',
                'description': 'The governing body of football in Asia'
            },
            # Rugby Federations
            {
                'name': 'Rugby Europe',
                'acronym': 'RE',
                'sport_code': 'RUGBY',
                'world_body_acronym': 'WR',
                'continent_code': 'EUR',
                'website': 'https://www.rugbyeurope.eu',
                'description': 'The governing body for rugby union in Europe'
            }