from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from db import models
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    """Processes raw API data and converts it to database models."""
    
    @staticmethod
    def process_player_data(player_data: Dict) -> models.Player:
        """Convert raw player data from API to Player model."""
        return models.Player(
            tag=player_data.get('tag'),
            name=player_data.get('name', ''),
            exp_level=player_data.get('expLevel'),
            trophies=player_data.get('trophies'),
            best_trophies=player_data.get('bestTrophies'),
            wins=player_data.get('wins', 0),
            losses=player_data.get('losses', 0),
            battle_count=player_data.get('battleCount', 0),
            three_crown_wins=player_data.get('threeCrownWins', 0),
            challenge_cards_won=player_data.get('challengeCardsWon', 0),
            tournament_cards_won=player_data.get('tournamentCardsWon', 0),
            role=player_data.get('role'),
            donations=player_data.get('donations', 0),
            donations_received=player_data.get('donationsReceived', 0),
            total_donations=player_data.get('totalDonations', 0),
            war_day_wins=player_data.get('warDayWins', 0),
            clan_cards_collected=player_data.get('clanCardsCollected', 0)
        )
    
    @staticmethod
    def process_card_data(card_data: Dict) -> models.Card:
        """Convert raw card data from API to Card model."""
        return models.Card(
            id=card_data.get('id'),
            name=card_data.get('name', ''),
            rarity=card_data.get('rarity', '').lower(),
            type=card_data.get('type', '').lower(),
            elixir=card_data.get('elixir', 0),
            arena=card_data.get('arena', 0),
            description=card_data.get('description', '')
        )
    
    @staticmethod
    def process_battle_data(battle_data: Dict, db: Session) -> Optional[models.Battle]:
        """Convert raw battle data from API to Battle model."""
        try:
            # Extract battle time and convert to datetime
            battle_time_str = battle_data.get('battleTime', '')
            battle_time = datetime.strptime(battle_time_str, '%Y%m%dT%H%M%S.%fZ')
            
            # Extract game mode information
            game_mode = battle_data.get('gameMode', {})
            
            # Extract team and opponent data
            team = battle_data.get('team', [{}])[0]
            opponent = battle_data.get('opponent', [{}])[0]
            
            # Create battle object
            battle = models.Battle(
                battle_time=battle_time,
                battle_type=battle_data.get('type', ''),
                game_mode=game_mode.get('name', ''),
                arena_name=battle_data.get('arena', {}).get('name', ''),
                deck_type='ladder',  # Default to ladder, can be updated based on battle type
                trophy_change=team.get('startingTrophies', 0) - team.get('trophyChange', 0),
                crown_difference=team.get('crowns', 0) - opponent.get('crowns', 0),
                player_tag=team.get('tag', ''),
                opponent_tag=opponent.get('tag', ''),
                is_winner=team.get('crowns', 0) > opponent.get('crowns', 0),
                player_crowns=team.get('crowns', 0),
                opponent_crowns=opponent.get('crowns', 0),
                player_cards=DataProcessor._extract_cards_info(team.get('cards', [])),
                opponent_cards=DataProcessor._extract_cards_info(opponent.get('cards', []))
            )
            
            return battle
            
        except Exception as e:
            logger.error(f"Error processing battle data: {e}")
            return None
    
    @staticmethod
    def _extract_cards_info(cards_data: List[Dict]) -> List[Dict]:
        """Extract relevant card information from battle data."""
        return [
            {
                'id': card.get('id'),
                'name': card.get('name', ''),
                'level': card.get('level', 0),
                'max_level': card.get('maxLevel', 0),
                'elixir': card.get('elixir', 0)
            }
            for card in cards_data
        ]
    
    @staticmethod
    def process_deck_data(deck_data: Dict, player_tag: str = '') -> models.Deck:
        """Convert raw deck data to Deck model."""
        # Calculate average elixir cost
        cards = deck_data.get('cards', [])
        avg_elixir = sum(card.get('elixir', 3) for card in cards) / len(cards) if cards else 0
        
        return models.Deck(
            name=f"Deck_{player_tag}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            avg_elixir=round(avg_elixir, 1),
            win_rate=0,  # Will be updated after battle analysis
            use_rate=0,  # Will be updated after battle analysis
            cards_count=len(cards)
        )
    
    @staticmethod
    def update_meta_snapshot(db: Session, trophy_range: str, game_mode: str) -> models.MetaSnapshot:
        """Create a new meta snapshot for the specified trophy range and game mode."""
        from sqlalchemy import and_
        from datetime import timedelta

        # Get current timestamp
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)

        # Get top 10 most used decks in the last week
        recent_battles = db.query(models.Battle).filter(
            models.Battle.battle_time >= seven_days_ago
        )
        
        if trophy_range:
            min_trophies, max_trophies = map(int, trophy_range.split('-'))
            recent_battles = recent_battles.join(
                models.Player,
                models.Battle.player_tag == models.Player.tag
            ).filter(
                and_(
                    models.Player.trophies >= min_trophies,
                    models.Player.trophies <= max_trophies
                )
            )
        
        if game_mode:
            recent_battles = recent_battles.filter(
                models.Battle.game_mode == game_mode
            )
        
        # For simplicity, we're just counting deck occurrences
        # In a real implementation, you'd want to group by card combinations
        deck_stats = {}
        for battle in recent_battles.all():
            deck_key = str(sorted(battle.player_cards or []))
            if deck_key not in deck_stats:
                deck_stats[deck_key] = {
                    'wins': 0,
                    'total': 0,
                    'cards': battle.player_cards or []
                }
            deck_stats[deck_key]['total'] += 1
            if battle.is_winner:
                deck_stats[deck_key]['wins'] += 1
        
        # Calculate win rates
        meta_data = []
        for deck_key, stats in deck_stats.items():
            if stats['total'] > 0:  # Only include decks with battles
                win_rate = (stats['wins'] / stats['total']) * 100
                meta_data.append({
                    'cards': stats['cards'],
                    'battles': stats['total'],
                    'wins': stats['wins'],
                    'win_rate': round(win_rate, 2),
                    'use_rate': 0  # Would be calculated based on total battles
                })
        
        # Sort by number of battles (most used first)
        meta_data.sort(key=lambda x: x['battles'], reverse=True)
        
        # Create and return the meta snapshot
        snapshot = models.MetaSnapshot(
            snapshot_date=now,
            trophy_range=trophy_range,
            game_mode=game_mode,
            meta_data={
                'total_battles': recent_battles.count(),
                'top_decks': meta_data[:20],  # Top 20 decks
                'last_updated': now.isoformat()
            }
        )
        
        return snapshot
