#!/usr/bin/env python
"""
Script to create sample competitions for the SAFA Digital Coins system
Run this with: python manage.py shell < create_sample_competitions.py
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_connect.settings')
django.setup()

from digital_coins.models import SAFACoinCompetition
from django.utils import timezone
from datetime import timedelta

def create_sample_competitions():
    """Create sample competitions for testing"""
    
    # Check if competitions already exist
    if SAFACoinCompetition.objects.exists():
        print("Sample competitions already exist. Skipping creation.")
        return
    
    # Sample competition data
    competitions_data = [
        {
            'title': 'Weekend Fantasy League',
            'subtitle': 'Predict match outcomes and earn coins',
            'description': 'Join our weekend fantasy football league! Pick your dream team, predict match outcomes, and compete against other SAFA members. The more accurate your predictions, the more coins you can win.',
            'competition_type': 'FANTASY_FOOTBALL',
            'entry_fee': Decimal('10.0'),
            'prize_pool': Decimal('500.0'),
            'max_participants': 100,
            'start_date': timezone.now() + timedelta(days=1),
            'end_date': timezone.now() + timedelta(days=8),
            'status': 'UPCOMING',
            'rules': [
                'Pick 11 players for your fantasy team',
                'Predict match outcomes (win/draw/loss)',
                'Earn points for correct predictions',
                'Bonus points for goal scorers and assists',
                'Top 10 players win prizes'
            ]
        },
        {
            'title': 'Championship Predictor',
            'subtitle': 'Predict league champions and earn big rewards',
            'description': 'Think you know who will win the league? Place your predictions and compete for the biggest prize pool! Predict final standings, top scorers, and more.',
            'competition_type': 'LEAGUE_PREDICTION',
            'entry_fee': Decimal('25.0'),
            'prize_pool': Decimal('1000.0'),
            'max_participants': 50,
            'start_date': timezone.now() + timedelta(days=3),
            'end_date': timezone.now() + timedelta(days=90),
            'status': 'UPCOMING',
            'rules': [
                'Predict final league standings',
                'Predict top 3 goal scorers',
                'Predict number of goals in season',
                'Predict relegation teams',
                'Grand prize for most accurate predictions'
            ]
        },
        {
            'title': 'Daily Match Predictor',
            'subtitle': 'Quick daily predictions for instant rewards',
            'description': 'Make quick predictions on today\'s matches and earn coins instantly! Perfect for daily engagement and building your coin balance.',
            'competition_type': 'MATCH_PREDICTION',
            'entry_fee': Decimal('0.0'),  # Free entry
            'prize_pool': Decimal('100.0'),
            'max_participants': 200,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=1),
            'status': 'ACTIVE',
            'rules': [
                'Predict today\'s match outcomes',
                'Free to enter',
                'Instant rewards for correct predictions',
                'Maximum 3 predictions per day',
                'Perfect for beginners'
            ]
        },
        {
            'title': 'World Cup Fantasy',
            'subtitle': 'International tournament fantasy league',
            'description': 'The biggest international tournament is here! Create your dream international team and compete for glory and massive coin rewards.',
            'competition_type': 'INTERNATIONAL_FANTASY',
            'entry_fee': Decimal('50.0'),
            'prize_pool': Decimal('2000.0'),
            'max_participants': 75,
            'start_date': timezone.now() + timedelta(days=7),
            'end_date': timezone.now() + timedelta(days=45),
            'status': 'UPCOMING',
            'rules': [
                'Pick players from any national team',
                'Transfer window opens every round',
                'Captain and vice-captain selections',
                'Bonus chips for special events',
                'Massive prize pool for winners'
            ]
        }
    ]
    
    created_competitions = []
    
    for comp_data in competitions_data:
        # Create competition
        competition = SAFACoinCompetition.objects.create(
            title=comp_data['title'],
            subtitle=comp_data['subtitle'],
            description=comp_data['description'],
            competition_type=comp_data['competition_type'],
            entry_fee=comp_data['entry_fee'],
            prize_pool=comp_data['prize_pool'],
            max_participants=comp_data['max_participants'],
            start_date=comp_data['start_date'],
            end_date=comp_data['end_date'],
            status=comp_data['status'],
            rules='\n'.join(comp_data['rules'])
        )
        
        created_competitions.append(competition)
        print(f"✅ Created competition: {competition.title}")
    
    print(f"\n🎉 Successfully created {len(created_competitions)} sample competitions!")
    print("You can now test the SAFA Digital Coins system with these competitions.")

if __name__ == '__main__':
    try:
        create_sample_competitions()
    except Exception as e:
        print(f"❌ Error creating competitions: {str(e)}")
        import traceback
        traceback.print_exc()
