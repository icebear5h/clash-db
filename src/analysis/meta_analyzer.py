"""
Meta Analyzer for Clash Royale

This module provides functionality to analyze the current meta, track trends,
and generate insights from the collected battle data.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
import logging
import math
import pandas as pd
from sqlalchemy import func, and_, or_, case, desc
from sqlalchemy.orm import Session

from ..database import models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Trophy range definitions
TROPHY_RANGES = [
    ('0-5000', 0, 5000),
    ('5000-6000', 5000, 6000),
    ('6000-7000', 6000, 7000),
    ('7000-8000', 7000, 8000),
    ('8000+', 8000, 99999)
]

# Game mode categories for analysis
GAME_MODE_CATEGORIES = {
    'ladder': ['PvP', 'pathOfLegend', 'ranked1v1'],
    'challenge': ['challenge', 'grandChallenge', 'classicChallenge'],
    'tournament': ['tournament'],
    'war': ['riverRacePvP', 'riverRaceDuel', 'clanWarWarDay', 'boatBattle']
}

class MetaAnalyzer:
    """Analyzes the Clash Royale meta based on collected battle data."""
    
    def __init__(self, db_session: Session):
        """Initialize with a database session."""
        self.db = db_session
    
    def get_card_usage_stats(self, days: int = 7, min_trophies: int = 4000) -> pd.DataFrame:
        """Get card usage statistics for the specified time period and trophy range.
        
        Args:
            days: Number of days to look back
            min_trophies: Minimum trophy count to include in the analysis
            
        Returns:
            DataFrame with card usage statistics
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query to get card usage in decks
        usage_query = self.db.query(
            models.Card.id,
            models.Card.name,
            models.Card.elixir,
            models.Card.rarity,
            func.count(models.Deck.id).label('usage_count')
        ).join(
            models.deck_cards,
            models.deck_cards.c.card_id == models.Card.id
        ).join(
            models.Deck,
            models.deck_cards.c.deck_id == models.Deck.id
        ).join(
            models.Battle,
            or_(
                models.Battle.deck_id == models.Deck.id,
                models.Battle.opponent_deck_id == models.Deck.id
            )
        ).join(
            models.Player,
            models.Battle.player_tag == models.Player.tag
        ).filter(
            models.Battle.battle_time >= start_date,
            models.Battle.battle_time <= end_date,
            models.Player.trophies >= min_trophies
        ).group_by(
            models.Card.id, models.Card.name, models.Card.elixir, models.Card.rarity
        )
        
        # Get total number of battles for normalization
        total_battles = self.db.query(func.count(models.Battle.id)).filter(
            models.Battle.battle_time >= start_date,
            models.Battle.battle_time <= end_date,
            models.Player.trophies >= min_trophies
        ).scalar() or 1  # Avoid division by zero
        
        # Get win rates for cards
        win_query = self.db.query(
            models.Card.id,
            func.avg(
                case(
                    [
                        (and_(
                            models.Battle.deck_id == models.Deck.id,
                            models.Battle.is_win == True
                        ), 1),
                        (and_(
                            models.Battle.opponent_deck_id == models.Deck.id,
                            models.Battle.is_win == False
                        ), 1)
                    ],
                    else_=0
                )
            ).label('win_rate')
        ).join(
            models.deck_cards,
            models.deck_cards.c.card_id == models.Card.id
        ).join(
            models.Deck,
            models.deck_cards.c.deck_id == models.Deck.id
        ).join(
            models.Battle,
            or_(
                models.Battle.deck_id == models.Deck.id,
                models.Battle.opponent_deck_id == models.Deck.id
            )
        ).join(
            models.Player,
            models.Battle.player_tag == models.Player.tag
        ).filter(
            models.Battle.battle_time >= start_date,
            models.Battle.battle_time <= end_date,
            models.Player.trophies >= min_trophies
        ).group_by(
            models.Card.id
        ).subquery()
        
        # Combine usage and win rate data
        result = pd.read_sql(
            usage_query.outerjoin(
                win_query,
                models.Card.id == win_query.c.id
            ).statement,
            self.db.bind
        )
        
        # Calculate usage rate and clean up
        if not result.empty:
            result['usage_rate'] = (result['usage_count'] / (total_battles * 2)) * 100  # 2 decks per battle
            result['win_rate'] = result['win_rate'] * 100  # Convert to percentage
            result = result.sort_values('usage_rate', ascending=False)
        
        return result
    
    def get_archetype_stats(self, days: int = 7, min_trophies: int = 4000) -> pd.DataFrame:
        """Analyze deck archetypes and their performance.
        
        Args:
            days: Number of days to look back
            min_trophies: Minimum trophy count to include in the analysis
            
        Returns:
            DataFrame with archetype statistics
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query to get deck archetypes and their performance
        query = """
        WITH deck_archetypes AS (
            SELECT 
                d.id,
                GROUP_CONCAT(c.id ORDER BY c.id SEPARATOR ',') AS card_list,
                COUNT(DISTINCT b.id) AS battle_count,
                AVG(CASE WHEN (b.deck_id = d.id AND b.is_win = 1) OR 
                          (b.opponent_deck_id = d.id AND b.is_win = 0) 
                    THEN 1.0 ELSE 0.0 END) * 100 AS win_rate
            FROM decks d
            JOIN deck_cards dc ON d.id = dc.deck_id
            JOIN cards c ON dc.card_id = c.id
            JOIN battles b ON b.deck_id = d.id OR b.opponent_deck_id = d.id
            JOIN players p ON b.player_tag = p.tag
            WHERE b.battle_time >= :start_date
              AND b.battle_time <= :end_date
              AND p.trophies >= :min_trophies
            GROUP BY d.id
            HAVING battle_count >= 5  -- Only consider decks with enough battles
        )
        SELECT 
            card_list,
            COUNT(*) AS deck_count,
            SUM(battle_count) AS total_battles,
            AVG(win_rate) AS avg_win_rate,
            GROUP_CONCAT(id) AS deck_ids
        FROM deck_archetypes
        GROUP BY card_list
        HAVING deck_count >= 5  -- Only consider archetypes with enough occurrences
        ORDER BY total_battles DESC
        """
        
        # Execute the query with parameters
        result = pd.read_sql_query(
            query,
            self.db.bind,
            params={
                'start_date': start_date,
                'end_date': end_date,
                'min_trophies': min_trophies
            }
        )
        
        # Add card names for better readability
        if not result.empty:
            # Get card mapping
            cards = pd.read_sql_table('cards', self.db.bind)
            card_map = dict(zip(cards['id'], cards['name']))
            
            # Replace card IDs with names
            result['archetype'] = result['card_list'].apply(
                lambda x: ', '.join(card_map.get(int(cid), cid) for cid in x.split(','))
            )
            
            # Calculate usage rate
            total_battles = result['total_battles'].sum()
            result['usage_rate'] = (result['total_battles'] / total_battles) * 100
            
            # Reorder columns
            result = result[['archetype', 'usage_rate', 'avg_win_rate', 'deck_count', 
                           'total_battles', 'card_list', 'deck_ids']]
        
        return result
    
    def get_meta_balance_score(self, days: int = 7, min_trophies: int = 4000) -> float:
        """Calculate a balance score for the current meta.
        
        A higher score (closer to 100) indicates a more balanced meta where many
        different cards and archetypes are viable.
        
        Args:
            days: Number of days to look back
            min_trophies: Minimum trophy count to include in the analysis
            
        Returns:
            Balance score between 0 and 100
        """
        # Get card usage stats
        card_stats = self.get_card_usage_stats(days, min_trophies)
        
        if card_stats.empty:
            return 0.0
        
        # Calculate Gini coefficient as a measure of balance
        # Lower Gini = more balanced
        usage_rates = card_stats['usage_rate'].sort_values()
        n = len(usage_rates)
        if n == 0:
            return 0.0
            
        # Calculate Gini coefficient
        gini = (n + 1 - 2 * (usage_rates * (n + 1 - usage_rates.rank())).sum() / usage_rates.sum()) / n
        
        # Convert to balance score (0-100)
        balance_score = (1 - gini) * 100
        
        return max(0, min(100, balance_score))
    
    def get_meta_trends(self, days: int = 30, interval_days: int = 7, 
                        min_trophies: int = 4000) -> pd.DataFrame:
        """Track how the meta has evolved over time.
        
        Args:
            days: Total number of days to look back
            interval_days: Size of each time window in days
            min_trophies: Minimum trophy count to include in the analysis
            
        Returns:
            DataFrame with meta metrics over time
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Generate time windows
        time_windows = []
        current_date = start_date
        
        while current_date < end_date:
            window_end = min(current_date + timedelta(days=interval_days), end_date)
            time_windows.append((current_date, window_end))
            current_date = window_end
        
        # Collect metrics for each time window
        metrics = []
        
        for window_start, window_end in time_windows:
            try:
                # Get card stats for this window
                card_stats = self.get_card_usage_stats(
                    days=interval_days,
                    min_trophies=min_trophies
                )
                
                if card_stats.empty:
                    continue
                
                # Calculate metrics
                total_cards = len(card_stats)
                high_usage = len(card_stats[card_stats['usage_rate'] > 20])
                low_usage = len(card_stats[card_stats['usage_rate'] < 5])
                
                # Get archetype stats
                archetype_stats = self.get_archetype_stats(
                    days=interval_days,
                    min_trophies=min_trophies
                )
                
                num_archetypes = len(archetype_stats) if not archetype_stats.empty else 0
                
                # Calculate balance score
                balance_score = self.get_meta_balance_score(
                    days=interval_days,
                    min_trophies=min_trophies
                )
                
                metrics.append({
                    'period_start': window_start,
                    'period_end': window_end,
                    'total_cards': total_cards,
                    'high_usage_cards': high_usage,
                    'low_usage_cards': low_usage,
                    'num_archetypes': num_archetypes,
                    'balance_score': balance_score,
                    'avg_win_rate': card_stats['win_rate'].mean() if 'win_rate' in card_stats.columns else 0
                })
                
            except Exception as e:
                logger.error(f"Error analyzing time window {window_start} to {window_end}: {e}")
                continue
        
        return pd.DataFrame(metrics)
    
    # ==================== NEW DECK META ANALYSIS METHODS ====================
    
    def get_top_decks(self, days: int = 7, trophy_range: str = None, 
                      game_mode: str = None, min_battles: int = 50,
                      limit: int = 20) -> pd.DataFrame:
        """Get top performing decks using the DeckHash model.
        
        Args:
            days: Number of days to look back
            trophy_range: Filter by trophy range (e.g., '6000-7000')
            game_mode: Filter by game mode category ('ladder', 'challenge', etc.)
            min_battles: Minimum battles required for a deck to be included
            limit: Maximum number of decks to return
            
        Returns:
            DataFrame with top deck statistics
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Base query for deck hashes with battle counts
        query = self.db.query(
            models.DeckHash.id,
            models.DeckHash.card_ids,
            models.DeckHash.card_hash,
            models.DeckHash.avg_elixir,
            func.count(models.Battle.id).label('battles'),
            func.sum(case((models.Battle.is_win == True, 1), else_=0)).label('wins')
        ).join(
            models.Battle,
            models.Battle.deck_hash_id == models.DeckHash.id
        ).filter(
            models.Battle.battle_time >= start_date,
            models.Battle.battle_time <= end_date
        )
        
        # Apply trophy range filter
        if trophy_range:
            for name, min_t, max_t in TROPHY_RANGES:
                if name == trophy_range:
                    query = query.filter(
                        models.Battle.player_trophies >= min_t,
                        models.Battle.player_trophies < max_t
                    )
                    break
        
        # Apply game mode filter
        if game_mode and game_mode in GAME_MODE_CATEGORIES:
            battle_types = GAME_MODE_CATEGORIES[game_mode]
            query = query.filter(models.Battle.battle_type.in_(battle_types))
        
        # Group and filter by minimum battles
        query = query.group_by(
            models.DeckHash.id,
            models.DeckHash.card_ids,
            models.DeckHash.card_hash,
            models.DeckHash.avg_elixir
        ).having(
            func.count(models.Battle.id) >= min_battles
        ).order_by(
            desc('wins' * 1.0 / func.count(models.Battle.id))  # Order by win rate
        ).limit(limit)
        
        results = query.all()
        
        if not results:
            return pd.DataFrame()
        
        # Get card names for display
        card_map = self._get_card_name_map()
        
        # Build result DataFrame
        data = []
        for row in results:
            win_rate = (row.wins / row.battles * 100) if row.battles > 0 else 0
            card_names = [card_map.get(cid, f'Card {cid}') for cid in row.card_ids]
            
            data.append({
                'deck_hash_id': row.id,
                'cards': card_names,
                'card_ids': row.card_ids,
                'avg_elixir': row.avg_elixir,
                'battles': row.battles,
                'wins': row.wins,
                'win_rate': round(win_rate, 2),
                'use_rate': 0  # Will be calculated below
            })
        
        df = pd.DataFrame(data)
        
        # Calculate use rate
        total_battles = df['battles'].sum()
        if total_battles > 0:
            df['use_rate'] = round((df['battles'] / total_battles) * 100, 2)
        
        return df
    
    def get_deck_matchups(self, deck_hash_id: int, days: int = 7, 
                          min_battles: int = 10) -> pd.DataFrame:
        """Get matchup statistics for a specific deck against other decks.
        
        Args:
            deck_hash_id: The DeckHash ID to analyze
            days: Number of days to look back
            min_battles: Minimum battles required for a matchup to be included
            
        Returns:
            DataFrame with matchup statistics (counters and favorable matchups)
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query matchups where this deck was used
        query = self.db.query(
            models.DeckHash.id.label('opponent_deck_id'),
            models.DeckHash.card_ids.label('opponent_cards'),
            models.DeckHash.avg_elixir.label('opponent_elixir'),
            func.count(models.Battle.id).label('battles'),
            func.sum(case((models.Battle.is_win == True, 1), else_=0)).label('wins')
        ).join(
            models.Battle,
            models.Battle.opponent_deck_hash_id == models.DeckHash.id
        ).filter(
            models.Battle.deck_hash_id == deck_hash_id,
            models.Battle.battle_time >= start_date,
            models.Battle.battle_time <= end_date
        ).group_by(
            models.DeckHash.id,
            models.DeckHash.card_ids,
            models.DeckHash.avg_elixir
        ).having(
            func.count(models.Battle.id) >= min_battles
        )
        
        results = query.all()
        
        if not results:
            return pd.DataFrame()
        
        card_map = self._get_card_name_map()
        
        data = []
        for row in results:
            win_rate = (row.wins / row.battles * 100) if row.battles > 0 else 0
            card_names = [card_map.get(cid, f'Card {cid}') for cid in row.opponent_cards]
            
            # Determine matchup type
            if win_rate >= 55:
                matchup_type = 'favorable'
            elif win_rate <= 45:
                matchup_type = 'counter'
            else:
                matchup_type = 'even'
            
            data.append({
                'opponent_deck_id': row.opponent_deck_id,
                'opponent_cards': card_names,
                'opponent_elixir': row.opponent_elixir,
                'battles': row.battles,
                'wins': row.wins,
                'win_rate': round(win_rate, 2),
                'matchup_type': matchup_type
            })
        
        df = pd.DataFrame(data)
        return df.sort_values('win_rate', ascending=True)  # Show counters first
    
    def get_card_synergies(self, days: int = 7, min_battles: int = 100,
                           min_win_rate: float = 52.0) -> pd.DataFrame:
        """Find card pairs that perform well together.
        
        Args:
            days: Number of days to look back
            min_battles: Minimum battles for a card pair
            min_win_rate: Minimum win rate to be considered a synergy
            
        Returns:
            DataFrame with card synergy statistics
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all deck hashes with their stats from recent battles
        deck_stats = self.db.query(
            models.DeckHash.card_ids,
            func.count(models.Battle.id).label('battles'),
            func.sum(case((models.Battle.is_win == True, 1), else_=0)).label('wins')
        ).join(
            models.Battle,
            models.Battle.deck_hash_id == models.DeckHash.id
        ).filter(
            models.Battle.battle_time >= start_date,
            models.Battle.battle_time <= end_date
        ).group_by(
            models.DeckHash.card_ids
        ).having(
            func.count(models.Battle.id) >= 10  # Minimum battles per deck
        ).all()
        
        # Count card pair occurrences and wins
        pair_stats: Dict[Tuple[int, int], Dict[str, int]] = {}
        
        for deck in deck_stats:
            card_ids = deck.card_ids
            battles = deck.battles
            wins = deck.wins
            
            # Generate all pairs from this deck
            for i, card1 in enumerate(card_ids):
                for card2 in card_ids[i+1:]:
                    pair = (min(card1, card2), max(card1, card2))
                    if pair not in pair_stats:
                        pair_stats[pair] = {'battles': 0, 'wins': 0}
                    pair_stats[pair]['battles'] += battles
                    pair_stats[pair]['wins'] += wins
        
        # Filter and format results
        card_map = self._get_card_name_map()
        
        data = []
        for (card1_id, card2_id), stats in pair_stats.items():
            if stats['battles'] >= min_battles:
                win_rate = (stats['wins'] / stats['battles'] * 100)
                if win_rate >= min_win_rate:
                    data.append({
                        'card1_id': card1_id,
                        'card1_name': card_map.get(card1_id, f'Card {card1_id}'),
                        'card2_id': card2_id,
                        'card2_name': card_map.get(card2_id, f'Card {card2_id}'),
                        'battles': stats['battles'],
                        'wins': stats['wins'],
                        'win_rate': round(win_rate, 2)
                    })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values('win_rate', ascending=False)
        return df
    
    def find_counter_decks(self, target_deck_hash_id: int, days: int = 7,
                           min_battles: int = 20, min_win_rate: float = 55.0) -> pd.DataFrame:
        """Find decks that counter a specific deck.
        
        Args:
            target_deck_hash_id: The deck to find counters for
            days: Number of days to look back
            min_battles: Minimum battles in the matchup
            min_win_rate: Minimum win rate to be considered a counter
            
        Returns:
            DataFrame with counter deck statistics
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Find decks that beat the target deck
        query = self.db.query(
            models.DeckHash.id,
            models.DeckHash.card_ids,
            models.DeckHash.avg_elixir,
            func.count(models.Battle.id).label('battles'),
            func.sum(case((models.Battle.is_win == False, 1), else_=0)).label('wins')  # Opponent wins
        ).join(
            models.Battle,
            models.Battle.deck_hash_id == models.DeckHash.id
        ).filter(
            models.Battle.opponent_deck_hash_id == target_deck_hash_id,
            models.Battle.battle_time >= start_date,
            models.Battle.battle_time <= end_date
        ).group_by(
            models.DeckHash.id,
            models.DeckHash.card_ids,
            models.DeckHash.avg_elixir
        ).having(
            func.count(models.Battle.id) >= min_battles
        )
        
        results = query.all()
        
        if not results:
            return pd.DataFrame()
        
        card_map = self._get_card_name_map()
        
        data = []
        for row in results:
            win_rate = (row.wins / row.battles * 100) if row.battles > 0 else 0
            if win_rate >= min_win_rate:
                card_names = [card_map.get(cid, f'Card {cid}') for cid in row.card_ids]
                data.append({
                    'counter_deck_id': row.id,
                    'cards': card_names,
                    'avg_elixir': row.avg_elixir,
                    'battles': row.battles,
                    'wins_vs_target': row.wins,
                    'win_rate_vs_target': round(win_rate, 2)
                })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values('win_rate_vs_target', ascending=False)
        return df
    
    def create_meta_snapshot(self, trophy_range: str = None, 
                             game_mode: str = None) -> models.MetaSnapshot:
        """Create and save a meta snapshot for the current state.
        
        Args:
            trophy_range: Trophy range to analyze
            game_mode: Game mode category to analyze
            
        Returns:
            The created MetaSnapshot object
        """
        # Get top decks
        top_decks_df = self.get_top_decks(
            days=7, 
            trophy_range=trophy_range, 
            game_mode=game_mode,
            min_battles=20,
            limit=50
        )
        
        top_decks_data = top_decks_df.to_dict('records') if not top_decks_df.empty else []
        
        # Get card usage stats
        card_stats = self.get_card_usage_stats(days=7, min_trophies=5000)
        card_usage_data = {}
        if not card_stats.empty:
            for _, row in card_stats.iterrows():
                card_usage_data[str(row['id'])] = {
                    'use_rate': row.get('usage_rate', 0),
                    'win_rate': row.get('win_rate', 0)
                }
        
        # Get card synergies
        synergies_df = self.get_card_synergies(days=7, min_battles=50, min_win_rate=53.0)
        synergies_data = synergies_df.head(50).to_dict('records') if not synergies_df.empty else []
        
        # Calculate meta health metrics
        balance_score = self.get_meta_balance_score(days=7, min_trophies=5000)
        diversity_index = self._calculate_diversity_index(top_decks_df)
        top_deck_dominance = top_decks_df.head(10)['use_rate'].sum() if not top_decks_df.empty else 0
        
        # Count total battles
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        total_battles = self.db.query(func.count(models.Battle.id)).filter(
            models.Battle.battle_time >= start_date,
            models.Battle.battle_time <= end_date
        ).scalar() or 0
        
        # Create snapshot
        snapshot = models.MetaSnapshot(
            timestamp=datetime.utcnow(),
            trophy_range=trophy_range or 'all',
            game_mode=game_mode or 'all',
            total_battles=total_battles,
            top_decks=top_decks_data,
            card_usage=card_usage_data,
            card_synergies=synergies_data,
            archetype_stats={},  # Could be populated with archetype analysis
            balance_score=balance_score,
            diversity_index=diversity_index,
            top_deck_dominance=top_deck_dominance
        )
        
        self.db.add(snapshot)
        self.db.commit()
        
        logger.info(f"Created meta snapshot: {snapshot}")
        return snapshot
    
    def _get_card_name_map(self) -> Dict[int, str]:
        """Get a mapping of card IDs to names."""
        cards = self.db.query(models.Card.id, models.Card.name).all()
        return {card.id: card.name for card in cards}
    
    def _calculate_diversity_index(self, deck_stats: pd.DataFrame) -> float:
        """Calculate Shannon diversity index for deck variety."""
        if deck_stats.empty or 'use_rate' not in deck_stats.columns:
            return 0.0
        
        # Normalize use rates to proportions
        proportions = deck_stats['use_rate'] / 100
        proportions = proportions[proportions > 0]  # Remove zeros
        
        if len(proportions) == 0:
            return 0.0
        
        # Calculate Shannon entropy: H = -sum(p * ln(p))
        entropy = -sum(p * math.log(p) for p in proportions if p > 0)
        
        # Normalize to 0-100 scale (max entropy for n items is ln(n))
        max_entropy = math.log(len(proportions)) if len(proportions) > 1 else 1
        diversity_index = (entropy / max_entropy) * 100 if max_entropy > 0 else 0
        
        return round(diversity_index, 2)
