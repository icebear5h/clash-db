import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session

from db import (
    get_db, Card, Deck, DeckCard, MetaSnapshot, DeckSnapshotStats, CardSnapshotStats,
    Location, Player, Leaderboard, LeaderboardSnapshot, LeaderboardSnapshotPlayer, PlayerDeck,
    Tournament, TournamentMember,
    Battle, BattlePlayer
)
from api import ClashAPI

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_deck_hash(card_ids: List[int]) -> str:
    """Generate unique hash for a deck (order-independent)."""
    sorted_ids = sorted(card_ids)
    return hashlib.sha256(','.join(map(str, sorted_ids)).encode()).hexdigest()


def get_card_type(card_id: int) -> str:
    """Derive card type from card ID prefix."""
    prefix = card_id // 1000000
    if prefix == 26:
        return 'troop'
    elif prefix == 27:
        return 'building'
    elif prefix == 28:
        return 'spell'
    return 'unknown'


class MetaCollector:
    """Collects and aggregates Clash Royale meta data."""
    
    def __init__(self):
        self.api = ClashAPI()
        self.db: Session = next(get_db())
        self._card_cache: Dict[int, Card] = {}
    
    def close(self):
        self.db.close()
    
    # ========== Cards ==========
    
    def sync_cards(self) -> int:
        """Fetch and sync all cards from API to database."""
        logger.info("Syncing cards from API...")
        cards_data = self.api.get_cards()
        
        count = 0
        for c in cards_data:
            card_id = c.get('id')
            if not card_id:
                continue
            
            existing = self.db.query(Card).filter_by(card_id=card_id).first()
            if existing:
                # Update existing
                existing.name = c.get('name', existing.name)
                existing.rarity = c.get('rarity', existing.rarity)
                existing.elixir_cost = c.get('elixirCost', existing.elixir_cost)
                existing.card_type = get_card_type(card_id)
                existing.icon_url = c.get('iconUrls', {}).get('medium')
            else:
                # Insert new
                card = Card(
                    card_id=card_id,
                    name=c.get('name', f'Card_{card_id}'),
                    rarity=c.get('rarity'),
                    elixir_cost=c.get('elixirCost'),
                    card_type=get_card_type(card_id),
                    icon_url=c.get('iconUrls', {}).get('medium')
                )
                self.db.add(card)
                count += 1
        
        self.db.commit()
        self._refresh_card_cache()
        logger.info(f"Synced {len(cards_data)} cards ({count} new)")
        return count
    
    def _refresh_card_cache(self):
        """Refresh in-memory card cache."""
        self._card_cache = {c.card_id: c for c in self.db.query(Card).all()}
    
    # ========== Locations ==========
    
    def sync_locations(self) -> int:
        """Fetch and sync all locations from API."""
        logger.info("Syncing locations from API...")
        locations_data = self.api.get_locations()
        
        count = 0
        for loc in locations_data:
            loc_id = loc.get('id')
            if not loc_id:
                continue
            
            existing = self.db.query(Location).filter_by(location_id=loc_id).first()
            if existing:
                existing.name = loc.get('name', existing.name)
                existing.is_country = loc.get('isCountry', existing.is_country)
                existing.country_code = loc.get('countryCode')
            else:
                location = Location(
                    location_id=loc_id,
                    name=loc.get('name', f'Location_{loc_id}'),
                    is_country=loc.get('isCountry', False),
                    country_code=loc.get('countryCode')
                )
                self.db.add(location)
                count += 1
        
        self.db.commit()
        logger.info(f"Synced {len(locations_data)} locations ({count} new)")
        return count
    
    # ========== Players ==========
    
    def upsert_player(self, player_data: Dict) -> Player:
        """Create or update a player record (just tag)."""
        tag = player_data.get('tag')
        if not tag:
            return None
        
        existing = self.db.query(Player).filter_by(player_tag=tag).first()
        if existing:
            return existing
        else:
            player = Player(player_tag=tag)
            self.db.add(player)
            return player
    
    def fetch_player_with_deck(self, player_tag: str) -> Tuple[Player, Deck]:
        """Fetch player profile from API and save their current deck."""
        try:
            player_data = self.api.get_player(player_tag)
        except Exception as e:
            logger.debug(f"Failed to fetch player {player_tag}: {e}")
            return None, None
        
        # Upsert player
        player = self.upsert_player(player_data)
        if not player:
            return None, None
        
        self.db.flush()
        
        # Get current deck
        current_deck = player_data.get('currentDeck', [])
        card_ids = [c.get('id') for c in current_deck if c.get('id')]
        
        deck = None
        if len(card_ids) == 8:
            try:
                deck = self.get_or_create_deck(card_ids)
                self.db.flush()
                
                # Save player-deck relationship
                existing_pd = self.db.query(PlayerDeck).filter_by(
                    player_tag=player.player_tag,
                    deck_id=deck.deck_id
                ).first()
                
                if not existing_pd:
                    pd = PlayerDeck(
                        player_tag=player.player_tag,
                        deck_id=deck.deck_id,
                        is_current=True
                    )
                    self.db.add(pd)
                else:
                    existing_pd.is_current = True
                    existing_pd.recorded_at = datetime.now()
                    
            except Exception as e:
                logger.debug(f"Failed to save deck for {player_tag}: {e}")
        
        return player, deck
    
    # ========== Leaderboards ==========
    
    def sync_leaderboard(self, location_id: str = 'global', leaderboard_type: str = 'global', fetch_decks: bool = True) -> LeaderboardSnapshot:
        """Fetch and save a leaderboard snapshot with player decks."""
        logger.info(f"Syncing leaderboard: {location_id} ({leaderboard_type})")
        
        # Get or create leaderboard definition
        lb_id = str(location_id)
        leaderboard = self.db.query(Leaderboard).filter_by(leaderboard_id=lb_id).first()
        if not leaderboard:
            # Try to get location name
            loc = self.db.query(Location).filter_by(location_id=int(location_id) if location_id != 'global' else None).first()
            name = loc.name if loc else ('Global' if location_id == 'global' else f'Location {location_id}')
            leaderboard = Leaderboard(
                leaderboard_id=lb_id,
                name=name,
                leaderboard_type=leaderboard_type,
                location_id=int(location_id) if location_id != 'global' else None
            )
            self.db.add(leaderboard)
            self.db.flush()
        
        # Fetch rankings
        if location_id == 'global':
            rankings = self.api.get_global_player_rankings(limit=200)
        else:
            rankings = self.api.get_location_player_rankings(int(location_id), limit=200)
        
        if not rankings:
            logger.warning(f"No rankings returned for {location_id}")
            return None
        
        # Create snapshot
        snapshot = LeaderboardSnapshot(
            leaderboard_id=lb_id,
            player_count=len(rankings)
        )
        self.db.add(snapshot)
        self.db.flush()
        
        # Add players with their decks
        decks_fetched = 0
        for i, rank_data in enumerate(rankings):
            player_tag = rank_data.get('tag')
            if not player_tag:
                continue
            
            deck_id = None
            
            if fetch_decks:
                # Fetch full player profile with deck
                player, deck = self.fetch_player_with_deck(player_tag)
                if deck:
                    deck_id = deck.deck_id
                    decks_fetched += 1
            else:
                # Just upsert basic player info
                player = self.upsert_player(rank_data)
            
            if player:
                self.db.flush()
                
                # Add to snapshot
                entry = LeaderboardSnapshotPlayer(
                    snapshot_id=snapshot.snapshot_id,
                    rank_position=rank_data.get('rank', 0),
                    player_tag=player.player_tag,
                    trophies=rank_data.get('trophies'),
                    deck_id=deck_id
                )
                self.db.add(entry)
            
            # Progress log
            if (i + 1) % 50 == 0:
                logger.info(f"  Processed {i + 1}/{len(rankings)} players, {decks_fetched} decks")
        
        self.db.commit()
        logger.info(f"Saved leaderboard snapshot {snapshot.snapshot_id} with {len(rankings)} players, {decks_fetched} decks")
        return snapshot
    
    # ========== Tournaments ==========
    
    def sync_tournaments(self, search_name: str = 'a', limit: int = 50) -> List[Tournament]:
        """Search and sync tournaments. Name is required by API."""
        logger.info(f"Searching tournaments (name={search_name}, limit={limit})")
        
        try:
            tournaments_data = self.api.search_tournaments(name=search_name, limit=limit)
        except Exception as e:
            logger.error(f"Failed to search tournaments: {e}")
            return []
        
        logger.info(f"Found {len(tournaments_data)} tournaments")
        
        synced = []
        for t in tournaments_data:
            tag = t.get('tag')
            if not tag:
                continue
            
            # Get full tournament details
            try:
                details = self.api.get_tournament(tag)
            except Exception as e:
                logger.error(f"Failed to get tournament {tag}: {e}")
                continue
            
            tournament = self._upsert_tournament(details)
            if tournament:
                synced.append(tournament)
        
        self.db.commit()
        logger.info(f"Synced {len(synced)} tournaments")
        return synced
    
    def _upsert_tournament(self, data: Dict) -> Tournament:
        """Create or update a tournament."""
        tag = data.get('tag')
        if not tag:
            return None
        
        existing = self.db.query(Tournament).filter_by(tournament_tag=tag).first()
        
        # Parse timestamps
        created_time = None
        started_time = None
        if data.get('createdTime'):
            try:
                created_time = datetime.strptime(data['createdTime'], '%Y%m%dT%H%M%S.%fZ')
            except:
                pass
        if data.get('startedTime'):
            try:
                started_time = datetime.strptime(data['startedTime'], '%Y%m%dT%H%M%S.%fZ')
            except:
                pass
        
        if existing:
            existing.status = data.get('status', existing.status)
            existing.capacity = data.get('capacity', existing.capacity)
            tournament = existing
        else:
            tournament = Tournament(
                tournament_tag=tag,
                status=data.get('status'),
                tournament_type=data.get('type'),
                capacity=data.get('capacity'),
                max_capacity=data.get('maxCapacity'),
                level_cap=data.get('levelCap'),
                game_mode_name=data.get('gameMode', {}).get('name'),
                created_time=created_time,
                started_time=started_time,
                first_place_prize=data.get('firstPlaceCardPrize')
            )
            self.db.add(tournament)
        
        self.db.flush()
        
        # Sync members
        members_list = data.get('membersList', [])
        for m in members_list:
            player = self.upsert_player(m)
            if player:
                self.db.flush()
                
                # Check if member exists
                existing_member = self.db.query(TournamentMember).filter_by(
                    tournament_tag=tag,
                    player_tag=player.player_tag
                ).first()
                
                if existing_member:
                    existing_member.rank_position = m.get('rank')
                    existing_member.score = m.get('score')
                else:
                    member = TournamentMember(
                        tournament_tag=tag,
                        player_tag=player.player_tag,
                        rank_position=m.get('rank'),
                        score=m.get('score')
                    )
                    self.db.add(member)
        
        return tournament
    
    # ========== Decks ==========
    
    def get_or_create_deck(self, card_ids: List[int]) -> Deck:
        """Get existing deck or create new one."""
        if len(card_ids) != 8:
            raise ValueError(f"Deck must have 8 cards, got {len(card_ids)}")
        
        deck_hash = get_deck_hash(card_ids)
        
        existing = self.db.query(Deck).filter_by(deck_hash=deck_hash).first()
        if existing:
            return existing
        
        # Calculate avg elixir
        total_elixir = sum(
            self._card_cache.get(cid, Card(elixir_cost=0)).elixir_cost or 0
            for cid in card_ids
        )
        avg_elixir = total_elixir / 8
        
        # Create new deck
        deck = Deck(deck_hash=deck_hash, avg_elixir=avg_elixir)
        self.db.add(deck)
        self.db.flush()  # Get deck_id
        
        # Add deck cards
        for card_id in card_ids:
            if card_id in self._card_cache:
                dc = DeckCard(deck_id=deck.deck_id, card_id=card_id)
                self.db.add(dc)
        
        return deck
    
    # ========== Battle Processing ==========
    
    def _extract_deck_from_battle_player(self, player_data: Dict) -> Tuple[List[int], bool]:
        """Extract card IDs and win status from battle player data."""
        cards = player_data.get('cards', [])
        card_ids = [c.get('id') for c in cards if c.get('id')]
        return card_ids, False  # Win status determined by caller
    
    def _is_ladder_battle(self, battle: Dict) -> bool:
        """Check if battle is a ranked ladder match."""
        battle_type = battle.get('type', '')
        game_mode = battle.get('gameMode', {}).get('name', '')
        
        # Include ladder and path of legend
        if battle_type == 'PvP':
            if 'Ladder' in game_mode or 'PathOfLegend' in game_mode or 'Ranked' in game_mode:
                return True
        return False
    
    def _generate_battle_id(self, battle: Dict) -> str:
        """Generate unique ID for a battle."""
        battle_time = battle.get('battleTime', '')
        team = battle.get('team', [{}])[0]
        opponent = battle.get('opponent', [{}])[0]
        team_tag = team.get('tag', '')
        opp_tag = opponent.get('tag', '')
        
        # Sort tags for consistency (same battle from either player's perspective)
        tags = sorted([team_tag, opp_tag])
        unique_str = f"{battle_time}_{tags[0]}_{tags[1]}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:32]
    
    def save_battle(self, battle: Dict) -> Battle:
        """Save an individual battle to the database."""
        battle_id = self._generate_battle_id(battle)
        
        # Check if already exists
        existing = self.db.query(Battle).filter_by(battle_id=battle_id).first()
        if existing:
            return existing
        
        battle_type = battle.get('type', '')
        game_mode = battle.get('gameMode', {}).get('name', '')
        arena_name = battle.get('arena', {}).get('name', '')
        is_ladder = self._is_ladder_battle(battle)
        
        # Create battle record
        battle_record = Battle(
            battle_id=battle_id,
            battle_type=battle_type,
            game_mode=game_mode,
            arena_name=arena_name,
            is_ladder=is_ladder
        )
        self.db.add(battle_record)
        self.db.flush()
        
        # Process both sides
        team = battle.get('team', [])
        opponent = battle.get('opponent', [])
        
        if team and opponent:
            team_player = team[0]
            opp_player = opponent[0]
            
            team_crowns = team_player.get('crowns', 0)
            opp_crowns = opp_player.get('crowns', 0)
            
            # Save team player
            self._save_battle_player(battle_id, 0, team_player, team_crowns > opp_crowns)
            
            # Save opponent player
            self._save_battle_player(battle_id, 1, opp_player, opp_crowns > team_crowns)
        
        return battle_record
    
    def _save_battle_player(self, battle_id: str, team_side: int, player_data: Dict, is_winner: bool):
        """Save a player's participation in a battle."""
        player_tag = player_data.get('tag')
        if not player_tag:
            return
        
        # Upsert player
        player = self.upsert_player(player_data)
        if not player:
            return
        self.db.flush()
        
        # Get deck
        cards = player_data.get('cards', [])
        card_ids = [c.get('id') for c in cards if c.get('id')]
        
        deck_id = None
        if len(card_ids) == 8:
            try:
                deck = self.get_or_create_deck(card_ids)
                deck_id = deck.deck_id
            except:
                pass
        
        # Create battle player record
        bp = BattlePlayer(
            battle_id=battle_id,
            team_side=team_side,
            player_tag=player_tag,
            deck_id=deck_id,
            starting_trophies=player_data.get('startingTrophies'),
            trophy_change=player_data.get('trophyChange'),
            crowns=player_data.get('crowns'),
            is_winner=is_winner
        )
        self.db.add(bp)
    
    def collect_battles(self, player_tag: str) -> int:
        """Collect all battles from a player's battlelog."""
        try:
            battles = self.api.get_battlelog(player_tag)
        except Exception as e:
            logger.debug(f"Failed to get battlelog for {player_tag}: {e}")
            return 0
        
        saved = 0
        for battle in battles:
            try:
                self.save_battle(battle)
                saved += 1
            except Exception as e:
                logger.debug(f"Failed to save battle: {e}")
        
        return saved
    
    def process_battlelog(self, player_tag: str) -> List[Dict]:
        """
        Process a player's battlelog and extract deck usage data.
        Returns list of deck results: [{'card_ids': [...], 'won': bool}, ...]
        """
        try:
            battles = self.api.get_battlelog(player_tag)
        except Exception as e:
            logger.error(f"Failed to get battlelog for {player_tag}: {e}")
            return []
        
        results = []
        
        for battle in battles:
            if not self._is_ladder_battle(battle):
                continue
            
            team = battle.get('team', [])
            opponent = battle.get('opponent', [])
            
            if not team or not opponent:
                continue
            
            team_player = team[0]
            opponent_player = opponent[0]
            
            team_crowns = team_player.get('crowns', 0)
            opponent_crowns = opponent_player.get('crowns', 0)
            
            # Extract team deck
            team_cards = [c.get('id') for c in team_player.get('cards', []) if c.get('id')]
            if len(team_cards) == 8:
                results.append({
                    'card_ids': team_cards,
                    'won': team_crowns > opponent_crowns
                })
            
            # Extract opponent deck
            opp_cards = [c.get('id') for c in opponent_player.get('cards', []) if c.get('id')]
            if len(opp_cards) == 8:
                results.append({
                    'card_ids': opp_cards,
                    'won': opponent_crowns > team_crowns
                })
        
        return results
    
    # ========== Meta Snapshot Collection ==========
    
    def collect_meta_snapshot(
        self,
        snapshot_type: str = 'top_1000',
        num_players: int = 200,
        description: str = None
    ) -> MetaSnapshot:
        """
        Collect a meta snapshot by gathering battlelogs from top players.
        
        Args:
            snapshot_type: Type label for the snapshot
            num_players: Number of top players to sample
            description: Optional description
        
        Returns:
            The created MetaSnapshot
        """
        logger.info(f"Starting meta collection: {snapshot_type} ({num_players} players)")
        
        # Get top players
        top_players = self.api.get_top_players(limit=num_players)
        logger.info(f"Fetched {len(top_players)} top players")
        
        # Aggregate deck stats
        deck_stats: Dict[str, Dict] = defaultdict(lambda: {'card_ids': [], 'wins': 0, 'games': 0})
        card_stats: Dict[int, Dict] = defaultdict(lambda: {'wins': 0, 'games': 0})
        
        total_battles = 0
        players_processed = 0
        
        # Get trophy range from top players
        trophies = [p.get('trophies', 0) for p in top_players if p.get('trophies')]
        trophy_min = min(trophies) if trophies else None
        trophy_max = max(trophies) if trophies else None
        
        for player in top_players:
            player_tag = player.get('tag')
            if not player_tag:
                continue
            
            try:
                battle_results = self.process_battlelog(player_tag)
                
                for result in battle_results:
                    card_ids = result['card_ids']
                    won = result['won']
                    deck_hash = get_deck_hash(card_ids)
                    
                    # Deck stats
                    if not deck_stats[deck_hash]['card_ids']:
                        deck_stats[deck_hash]['card_ids'] = card_ids
                    deck_stats[deck_hash]['games'] += 1
                    if won:
                        deck_stats[deck_hash]['wins'] += 1
                    
                    # Card stats
                    for card_id in card_ids:
                        card_stats[card_id]['games'] += 1
                        if won:
                            card_stats[card_id]['wins'] += 1
                    
                    total_battles += 1
                
                players_processed += 1
                if players_processed % 20 == 0:
                    logger.info(f"Processed {players_processed}/{len(top_players)} players, {total_battles} battles")
                    
            except Exception as e:
                logger.error(f"Error processing player {player_tag}: {e}")
                continue
        
        logger.info(f"Collection complete: {total_battles} battles, {len(deck_stats)} unique decks")
        
        # Create snapshot
        snapshot = MetaSnapshot(
            snapshot_type=snapshot_type,
            trophy_min=trophy_min,
            trophy_max=trophy_max,
            sample_size=total_battles,
            total_decks=len(deck_stats),
            description=description or f"Top {num_players} players meta"
        )
        self.db.add(snapshot)
        self.db.flush()
        
        # Save deck stats
        for deck_hash, stats in deck_stats.items():
            if stats['games'] == 0:
                continue
            
            try:
                deck = self.get_or_create_deck(stats['card_ids'])
                
                deck_stat = DeckSnapshotStats(
                    snapshot_id=snapshot.snapshot_id,
                    deck_id=deck.deck_id,
                    games_played=stats['games'],
                    games_won=stats['wins'],
                    win_rate=round(stats['wins'] / stats['games'] * 100, 2) if stats['games'] > 0 else 0,
                    pick_rate=round(stats['games'] / total_battles * 100, 2) if total_battles > 0 else 0
                )
                self.db.add(deck_stat)
            except Exception as e:
                logger.error(f"Error saving deck stats: {e}")
                continue
        
        # Save card stats
        for card_id, stats in card_stats.items():
            if stats['games'] == 0 or card_id not in self._card_cache:
                continue
            
            card_stat = CardSnapshotStats(
                snapshot_id=snapshot.snapshot_id,
                card_id=card_id,
                games_played=stats['games'],
                games_won=stats['wins'],
                win_rate=round(stats['wins'] / stats['games'] * 100, 2) if stats['games'] > 0 else 0,
                pick_rate=round(stats['games'] / total_battles * 100, 2) if total_battles > 0 else 0
            )
            self.db.add(card_stat)
        
        self.db.commit()
        logger.info(f"Saved snapshot {snapshot.snapshot_id}")
        
        return snapshot


def collect_meta_by_trophy_range(
    collector: MetaCollector,
    trophy_min: int = None,
    trophy_max: int = None,
    snapshot_type: str = 'ladder'
) -> MetaSnapshot:
    """
    Create a meta snapshot from existing battle data filtered by trophy range.
    
    Args:
        collector: MetaCollector instance
        trophy_min: Minimum trophy count (inclusive), None for no lower bound
        trophy_max: Maximum trophy count (exclusive), None for no upper bound
        snapshot_type: Type label for the snapshot
    
    Returns:
        The created MetaSnapshot
    """
    logger.info(f"Creating meta snapshot for trophy range: {trophy_min or 0} - {trophy_max or '∞'}")
    
    # Build query for battles in trophy range
    query = collector.db.query(BattlePlayer).join(Battle).filter(Battle.is_ladder == True)
    
    if trophy_min is not None:
        query = query.filter(BattlePlayer.starting_trophies >= trophy_min)
    if trophy_max is not None:
        query = query.filter(BattlePlayer.starting_trophies < trophy_max)
    
    battle_players = query.all()
    logger.info(f"Found {len(battle_players)} battle records in trophy range")
    
    if not battle_players:
        logger.warning("No battles found in trophy range")
        return None
    
    # Aggregate stats
    deck_stats: Dict[str, Dict] = defaultdict(lambda: {'card_ids': [], 'wins': 0, 'games': 0})
    card_stats: Dict[int, Dict] = defaultdict(lambda: {'wins': 0, 'games': 0})
    total_battles = 0
    
    for bp in battle_players:
        if not bp.deck_id:
            continue
        
        # Get deck cards
        deck_cards = collector.db.query(DeckCard).filter_by(deck_id=bp.deck_id).all()
        card_ids = [dc.card_id for dc in deck_cards]
        
        if len(card_ids) != 8:
            continue
        
        deck_hash = get_deck_hash(card_ids)
        won = bp.is_winner or False
        
        # Deck stats
        if not deck_stats[deck_hash]['card_ids']:
            deck_stats[deck_hash]['card_ids'] = card_ids
        deck_stats[deck_hash]['games'] += 1
        if won:
            deck_stats[deck_hash]['wins'] += 1
        
        # Card stats
        for card_id in card_ids:
            card_stats[card_id]['games'] += 1
            if won:
                card_stats[card_id]['wins'] += 1
        
        total_battles += 1
    
    logger.info(f"Aggregated: {total_battles} battles, {len(deck_stats)} unique decks")
    
    # Build description
    if trophy_min is not None and trophy_max is not None:
        desc = f"Trophy range {trophy_min:,} - {trophy_max:,}"
    elif trophy_min is not None:
        desc = f"Trophy range {trophy_min:,}+"
    elif trophy_max is not None:
        desc = f"Trophy range below {trophy_max:,}"
    else:
        desc = "All trophy ranges"
    
    # Create snapshot
    snapshot = MetaSnapshot(
        snapshot_type=snapshot_type,
        trophy_min=trophy_min,
        trophy_max=trophy_max,
        sample_size=total_battles,
        total_decks=len(deck_stats),
        description=desc
    )
    collector.db.add(snapshot)
    collector.db.flush()
    
    # Save deck stats
    for deck_hash, stats in deck_stats.items():
        if stats['games'] == 0:
            continue
        try:
            deck = collector.get_or_create_deck(stats['card_ids'])
            deck_stat = DeckSnapshotStats(
                snapshot_id=snapshot.snapshot_id,
                deck_id=deck.deck_id,
                games_played=stats['games'],
                games_won=stats['wins'],
                win_rate=round(stats['wins'] / stats['games'] * 100, 2) if stats['games'] > 0 else 0,
                pick_rate=round(stats['games'] / total_battles * 100, 2) if total_battles > 0 else 0
            )
            collector.db.add(deck_stat)
        except Exception as e:
            logger.error(f"Error saving deck stats: {e}")
    
    # Save card stats
    for card_id, stats in card_stats.items():
        if stats['games'] == 0 or card_id not in collector._card_cache:
            continue
        card_stat = CardSnapshotStats(
            snapshot_id=snapshot.snapshot_id,
            card_id=card_id,
            games_played=stats['games'],
            games_won=stats['wins'],
            win_rate=round(stats['wins'] / stats['games'] * 100, 2) if stats['games'] > 0 else 0,
            pick_rate=round(stats['games'] / total_battles * 100, 2) if total_battles > 0 else 0
        )
        collector.db.add(card_stat)
    
    collector.db.commit()
    logger.info(f"Saved snapshot {snapshot.snapshot_id}: {desc}")
    
    return snapshot


def create_trophy_range_snapshots(collector: MetaCollector) -> List[MetaSnapshot]:
    """
    Create meta snapshots for predefined trophy ranges.
    
    Trophy ranges:
    - 10000+: Top ladder / Ultimate Champion+
    - 7000-10000: Mid-high ladder / Champion
    - 1000-7000: Mid ladder
    
    Returns:
        List of created MetaSnapshots
    """
    TROPHY_RANGES = [
        (10000, None, 'ladder_10k_plus'),      # 10k+
        (7000, 10000, 'ladder_7k_10k'),         # 7k-10k
        (1000, 7000, 'ladder_1k_7k'),           # 1k-7k
    ]
    
    snapshots = []
    for trophy_min, trophy_max, snapshot_type in TROPHY_RANGES:
        snapshot = collect_meta_by_trophy_range(
            collector,
            trophy_min=trophy_min,
            trophy_max=trophy_max,
            snapshot_type=snapshot_type
        )
        if snapshot:
            snapshots.append(snapshot)
    
    return snapshots


def collect_from_player_tags(collector: MetaCollector, player_tags: List[str], snapshot_type: str = 'custom') -> MetaSnapshot:
    """Collect meta data from a list of player tags."""
    logger.info(f"Starting meta collection from {len(player_tags)} player tags")
    
    deck_stats: Dict[str, Dict] = defaultdict(lambda: {'card_ids': [], 'wins': 0, 'games': 0})
    card_stats: Dict[int, Dict] = defaultdict(lambda: {'wins': 0, 'games': 0})
    
    total_battles = 0
    players_processed = 0
    
    for player_tag in player_tags:
        try:
            battle_results = collector.process_battlelog(player_tag)
            
            for result in battle_results:
                card_ids = result['card_ids']
                won = result['won']
                deck_hash = get_deck_hash(card_ids)
                
                if not deck_stats[deck_hash]['card_ids']:
                    deck_stats[deck_hash]['card_ids'] = card_ids
                deck_stats[deck_hash]['games'] += 1
                if won:
                    deck_stats[deck_hash]['wins'] += 1
                
                for card_id in card_ids:
                    card_stats[card_id]['games'] += 1
                    if won:
                        card_stats[card_id]['wins'] += 1
                
                total_battles += 1
            
            players_processed += 1
            logger.info(f"Processed {players_processed}/{len(player_tags)} players, {total_battles} battles")
                
        except Exception as e:
            logger.error(f"Error processing player {player_tag}: {e}")
            continue
    
    logger.info(f"Collection complete: {total_battles} battles, {len(deck_stats)} unique decks")
    
    # Create snapshot
    snapshot = MetaSnapshot(
        snapshot_type=snapshot_type,
        sample_size=total_battles,
        total_decks=len(deck_stats),
        description=f"Collection from {len(player_tags)} players"
    )
    collector.db.add(snapshot)
    collector.db.flush()
    
    # Save deck stats
    for deck_hash, stats in deck_stats.items():
        if stats['games'] == 0:
            continue
        try:
            deck = collector.get_or_create_deck(stats['card_ids'])
            deck_stat = DeckSnapshotStats(
                snapshot_id=snapshot.snapshot_id,
                deck_id=deck.deck_id,
                games_played=stats['games'],
                games_won=stats['wins'],
                win_rate=round(stats['wins'] / stats['games'] * 100, 2) if stats['games'] > 0 else 0,
                pick_rate=round(stats['games'] / total_battles * 100, 2) if total_battles > 0 else 0
            )
            collector.db.add(deck_stat)
        except Exception as e:
            logger.error(f"Error saving deck stats: {e}")
    
    # Save card stats
    for card_id, stats in card_stats.items():
        if stats['games'] == 0 or card_id not in collector._card_cache:
            continue
        card_stat = CardSnapshotStats(
            snapshot_id=snapshot.snapshot_id,
            card_id=card_id,
            games_played=stats['games'],
            games_won=stats['wins'],
            win_rate=round(stats['wins'] / stats['games'] * 100, 2) if stats['games'] > 0 else 0,
            pick_rate=round(stats['games'] / total_battles * 100, 2) if total_battles > 0 else 0
        )
        collector.db.add(card_stat)
    
    collector.db.commit()
    return snapshot


def main():
    """Run a full meta collection."""
    collector = MetaCollector()
    
    try:
        # ============================================
        # 1. SYNC REFERENCE DATA
        # ============================================
        print("\n📦 Syncing reference data...")
        collector.sync_cards()
        collector.sync_locations()
        
        # ============================================
        # 2. LEADERBOARDS - Try multiple locations
        # ============================================
        print("\n🏆 Syncing leaderboards...")
        
        # Try different location IDs for rankings
        LOCATION_IDS = [
            ('57000249', 'United States'),
            ('57000056', 'Canada'),
            ('57000094', 'Germany'),
            ('57000138', 'United Kingdom'),
            ('57000107', 'France'),
        ]
        
        leaderboard_players = set()
        for loc_id, loc_name in LOCATION_IDS:
            try:
                lb_snapshot = collector.sync_leaderboard(loc_id, 'location')
                if lb_snapshot and lb_snapshot.player_count > 0:
                    print(f"   {loc_name}: {lb_snapshot.player_count} players")
                    # Collect player tags for battlelog
                    for entry in lb_snapshot.players:
                        leaderboard_players.add(entry.player_tag)
            except Exception as e:
                logger.warning(f"Failed to sync {loc_name} leaderboard: {e}")
        
        print(f"   Total leaderboard players: {len(leaderboard_players)}")
        
        # ============================================
        # 3. TOURNAMENTS - Search multiple terms
        # ============================================
        print("\n🎮 Syncing tournaments...")
        
        SEARCH_TERMS = ['a', 'e', 'pro', 'war', 'clash']
        all_tournaments = []
        
        for term in SEARCH_TERMS:
            try:
                tournaments = collector.sync_tournaments(search_name=term, limit=10)
                all_tournaments.extend(tournaments)
                print(f"   Search '{term}': {len(tournaments)} tournaments")
            except Exception as e:
                logger.warning(f"Failed tournament search '{term}': {e}")
        
        # Get player tags from tournament members and fetch their decks
        tournament_players = set()
        tournament_members = collector.db.query(TournamentMember).all()
        
        print(f"   Fetching decks for {len(tournament_members)} tournament players...")
        decks_fetched = 0
        for i, tm in enumerate(tournament_members):
            tournament_players.add(tm.player_tag)
            # Fetch player profile with deck
            player, deck = collector.fetch_player_with_deck(tm.player_tag)
            if deck:
                decks_fetched += 1
            if (i + 1) % 50 == 0:
                print(f"      {i + 1}/{len(tournament_members)} players, {decks_fetched} decks")
        
        collector.db.commit()
        print(f"   Total tournament players: {len(tournament_players)}, decks: {decks_fetched}")
        
        # ============================================
        # 4. COLLECT BATTLES
        # ============================================
        print("\n⚔️ Collecting individual battles...")
        
        # Combine all player sources
        all_player_tags = list(tournament_players | leaderboard_players)
        
        # Limit to reasonable amount (API rate limits)
        MAX_PLAYERS = 100
        sample_players = all_player_tags[:MAX_PLAYERS]
        
        print(f"   Collecting battles from {len(sample_players)} players...")
        
        total_battles_saved = 0
        for i, player_tag in enumerate(sample_players):
            battles_saved = collector.collect_battles(player_tag)
            total_battles_saved += battles_saved
            if (i + 1) % 20 == 0:
                collector.db.commit()
                print(f"      {i + 1}/{len(sample_players)} players, {total_battles_saved} battles")
        
        collector.db.commit()
        print(f"   Total battles saved: {total_battles_saved}")
        
        # ============================================
        # 5. META SNAPSHOT (aggregated stats)
        # ============================================
        print("\n📊 Creating meta snapshot from battles...")
        
        snapshot = collect_from_player_tags(
            collector,
            sample_players,
            snapshot_type='ladder'
        )
        
        # ============================================
        # 6. TROPHY RANGE META SNAPSHOTS
        # ============================================
        print("\n🏅 Creating trophy range meta snapshots...")
        
        trophy_snapshots = create_trophy_range_snapshots(collector)
        for ts in trophy_snapshots:
            print(f"   {ts.snapshot_type}: {ts.sample_size} battles, {ts.total_decks} decks")
        
        # ============================================
        # SUMMARY
        # ============================================
        print(f"\n{'='*50}")
        print(f"✅ COLLECTION COMPLETE")
        print(f"{'='*50}")
        print(f"\n📦 Reference Data:")
        print(f"   Cards: {collector.db.query(Card).count()}")
        print(f"   Locations: {collector.db.query(Location).count()}")
        
        print(f"\n🏆 Leaderboards:")
        print(f"   Leaderboards: {collector.db.query(Leaderboard).count()}")
        print(f"   Snapshots: {collector.db.query(LeaderboardSnapshot).count()}")
        lb_players = collector.db.query(LeaderboardSnapshotPlayer).count()
        print(f"   Ranked players: {lb_players}")
        
        print(f"\n🎮 Tournaments:")
        print(f"   Tournaments: {collector.db.query(Tournament).count()}")
        print(f"   Tournament members: {collector.db.query(TournamentMember).count()}")
        
        print(f"\n👤 Player Decks:")
        print(f"   Player-deck links: {collector.db.query(PlayerDeck).count()}")
        
        print(f"\n⚔️ Battles:")
        print(f"   Total battles: {collector.db.query(Battle).count()}")
        print(f"   Battle players: {collector.db.query(BattlePlayer).count()}")
        
        print(f"\n📊 Meta Snapshot:")
        print(f"   Battles analyzed: {snapshot.sample_size}")
        print(f"   Unique decks: {snapshot.total_decks}")
        print(f"   Players in DB: {collector.db.query(Player).count()}")
        
    finally:
        collector.close()


if __name__ == '__main__':
    main()
