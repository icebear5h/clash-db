import os
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Add parent directory to path to allow imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.config import get_db
from db import models
from api.client import ClashRoyaleAPI
from api.processor import DataProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_collection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataCollector:
    """Handles data collection from the Clash Royale API and storage in the database."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the data collector with an optional API key."""
        self.api = ClashRoyaleAPI(api_key)
        self.processor = DataProcessor()
        self.db_session = next(get_db())
    
    def collect_player_data(self, player_tag: str) -> Optional[models.Player]:
        """Collect and store data for a single player."""
        try:
            logger.info(f"Fetching data for player: {player_tag}")
            
            # Check if player already exists
            existing_player = self.db_session.query(models.Player).filter_by(tag=player_tag).first()
            
            # Fetch player data from API
            player_data = self.api.get_player(player_tag)
            
            # Process and save player data
            player = self.processor.process_player_data(player_data)
            
            if existing_player:
                # Update existing player
                for key, value in player.__dict__.items():
                    if not key.startswith('_') and key != 'id':
                        setattr(existing_player, key, value)
                player = existing_player
            else:
                # Add new player
                self.db_session.add(player)
            
            self.db_session.commit()
            logger.info(f"Successfully saved data for player: {player_tag}")
            
            return player
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error collecting player data for {player_tag}: {e}")
            return None
    
    def collect_player_battles(self, player_tag: str, limit: int = 25) -> List[models.Battle]:
        """Collect and store battle history for a player."""
        try:
            logger.info(f"Fetching battles for player: {player_tag}")

            # Fetch battle log from API
            battles_data = self.api.get_player_battles(player_tag, limit=limit)

            processed_battles = []
            opponent_tags = set()

            # First, collect all opponent player data
            for battle_data in battles_data:
                try:
                    team = battle_data.get('team', [{}])[0]
                    opponent = battle_data.get('opponent', [{}])[0]
                    opponent_tag = opponent.get('tag', '')

                    if opponent_tag and opponent_tag not in opponent_tags:
                        opponent_tags.add(opponent_tag)
                        # Check if opponent exists in database
                        existing_opponent = self.db_session.query(models.Player).filter_by(tag=opponent_tag).first()
                        if not existing_opponent:
                            # Try to fetch opponent data
                            try:
                                opponent_data = self.api.get_player(opponent_tag)
                                opponent_player = self.processor.process_player_data(opponent_data)
                                self.db_session.add(opponent_player)
                                self.db_session.flush()  # Ensure opponent is saved before battles
                                logger.debug(f"Added opponent player: {opponent_tag}")
                            except Exception as e:
                                logger.warning(f"Could not fetch opponent {opponent_tag}: {e}")
                                continue
                except Exception as e:
                    logger.debug(f"Error checking opponent: {e}")
                    continue

            # Now process battles
            for battle_data in battles_data:
                try:
                    # Check if battle already exists
                    battle_time_str = battle_data.get('battleTime')
                    battle_time = datetime.strptime(battle_time_str, '%Y%m%dT%H%M%S.%fZ')

                    existing_battle = self.db_session.query(models.Battle).filter_by(
                        player_tag=player_tag,
                        battle_time=battle_time
                    ).first()

                    if existing_battle:
                        logger.debug(f"Battle already exists for player {player_tag} at {battle_time}")
                        continue

                    # Process battle data
                    battle = self.processor.process_battle_data(battle_data, self.db_session)
                    if battle:
                        self.db_session.add(battle)
                        processed_battles.append(battle)

                except Exception as e:
                    logger.error(f"Error processing battle data: {e}")
                    continue

            self.db_session.commit()
            logger.info(f"Successfully saved {len(processed_battles)} battles for player: {player_tag}")
            return processed_battles
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error collecting battles for {player_tag}: {e}")
            return []
    
    def collect_all_cards(self) -> int:
        """Collect and store all available cards from the API."""
        try:
            logger.info("Fetching all cards from API")

            cards_data = self.api.get_cards()
            processed_cards = 0

            for card_data in cards_data.get('items', []):
                try:
                    # Check if card already exists
                    existing_card = self.db_session.query(models.Card).filter_by(
                        id=card_data.get('id')
                    ).first()

                    if existing_card:
                        logger.debug(f"Card {card_data.get('name')} already exists")
                        continue

                    # Process and add card
                    card = self.processor.process_card_data(card_data)
                    self.db_session.add(card)
                    processed_cards += 1

                except Exception as e:
                    logger.error(f"Error processing card {card_data.get('name', 'unknown')}: {e}")
                    continue

            self.db_session.commit()
            logger.info(f"Successfully saved {processed_cards} new cards")
            return processed_cards

        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error collecting cards: {e}")
            return 0

    def collect_popular_decks(self, limit: int = 20) -> List[models.Deck]:
        """Collect and store popular decks from top players."""
        try:
            logger.info("Fetching popular decks from top players")
            
            # Fetch popular decks from API
            decks_data = self.api.get_popular_decks(limit=limit)
            
            processed_decks = []
            
            for deck_data in decks_data:
                try:
                    # Process deck data
                    deck = self.processor.process_deck_data(deck_data, deck_data.get('player_tag', ''))
                    
                    # Add cards to the database and create relationships
                    for card_data in deck_data.get('cards', []):
                        card = self.db_session.query(models.Card).filter_by(id=card_data.get('id')).first()
                        if not card:
                            # If card doesn't exist, fetch its details
                            card_info = self.api.get_card_info(card_data.get('id'))
                            if card_info:
                                card = self.processor.process_card_data(card_info)
                                self.db_session.add(card)
                                self.db_session.flush()  # Get the card ID
                        
                        if card:
                            deck.cards.append(card)
                    
                    self.db_session.add(deck)
                    processed_decks.append(deck)
                    
                except Exception as e:
                    logger.error(f"Error processing deck data: {e}")
                    continue
            
            self.db_session.commit()
            logger.info(f"Successfully saved {len(processed_decks)} popular decks")
            return processed_decks
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error collecting popular decks: {e}")
            return []
    
    def collect_players_by_trophy_range(self, player_tags: List[str], players_per_range: int = 100) -> Dict[str, List[str]]:
        """Organize player tags by trophy range after collecting their data."""
        import os

        # Get trophy ranges from env
        trophy_ranges_str = os.getenv('TROPHY_RANGES', '0-4000,4000-8000,8000-10000,10000-15000')
        trophy_ranges = trophy_ranges_str.split(',')

        # Initialize groups
        trophy_groups = {range_str: [] for range_str in trophy_ranges}

        logger.info(f"Collecting {len(player_tags)} players and organizing by trophy ranges: {trophy_ranges}")

        for player_tag in player_tags:
            try:
                # Collect player data
                player = self.collect_player_data(player_tag)

                if player:
                    # Determine trophy range
                    trophies = player.trophies or 0

                    for range_str in trophy_ranges:
                        min_t, max_t = map(int, range_str.split('-'))
                        if min_t <= trophies < max_t:
                            if len(trophy_groups[range_str]) < players_per_range:
                                trophy_groups[range_str].append(player_tag)
                                logger.info(f"Player {player.name} ({trophies} trophies) -> {range_str}")
                            break

                    # Collect battles for this player
                    self.collect_player_battles(player_tag, limit=25)

                    # Rate limiting
                    time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error processing player {player_tag}: {e}")
                continue

        # Log summary
        for range_str, tags in trophy_groups.items():
            logger.info(f"Trophy range {range_str}: {len(tags)} players collected")

        return trophy_groups

    def update_meta_snapshots(self):
        """Update meta snapshots for different trophy ranges and game modes."""
        try:
            logger.info("Updating meta snapshots")

            import os
            trophy_ranges_str = os.getenv('TROPHY_RANGES', '0-4000,4000-8000,8000-10000,10000-15000')
            trophy_ranges = trophy_ranges_str.split(',')

            game_modes_str = os.getenv('GAME_MODES', 'Ladder')
            game_modes = game_modes_str.split(',')

            logger.info(f"Creating meta snapshots for trophy ranges: {trophy_ranges}")
            logger.info(f"Game modes: {game_modes}")
            
            for trophy_range in trophy_ranges:
                for game_mode in game_modes:
                    try:
                        snapshot = self.processor.update_meta_snapshot(
                            self.db_session,
                            trophy_range=trophy_range,
                            game_mode=game_mode
                        )
                        self.db_session.add(snapshot)
                        logger.info(f"Created meta snapshot for {trophy_range} trophies in {game_mode} mode")
                    except Exception as e:
                        logger.error(f"Error creating meta snapshot for {trophy_range} {game_mode}: {e}")
                        continue
            
            self.db_session.commit()
            logger.info("Successfully updated meta snapshots")
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error updating meta snapshots: {e}")
    
    def run_collection_pipeline(self, player_tags: List[str] = None):
        """Run the complete data collection pipeline."""
        start_time = datetime.now()
        logger.info("Starting data collection pipeline")

        try:
            # If no player tags provided, use sample player tag from env
            if not player_tags or len(player_tags) == 0:
                logger.info("No player tags provided, using sample player tag")
                import os
                sample_tag = os.getenv('SAMPLE_PLAYER_TAG', '#8L9L9GL')
                player_tags = [sample_tag]
                logger.info(f"Using sample player: {sample_tag}")

            # Collect all cards first
            self.collect_all_cards()

            # Collect data for each player
            for player_tag in player_tags:
                try:
                    # Collect player data
                    self.collect_player_data(player_tag)
                    
                    # Collect player battles
                    self.collect_player_battles(player_tag, limit=25)
                    
                    # Be nice to the API
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing player {player_tag}: {e}")
                    continue
            
            # Collect popular decks
            self.collect_popular_decks(limit=20)
            
            # Update meta snapshots
            self.update_meta_snapshots()

            logger.info(f"Data collection completed in {datetime.now() - start_time}")
            
        except Exception as e:
            logger.error(f"Error in data collection pipeline: {e}")
            raise
        finally:
            self.db_session.close()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Initialize and run the data collector
    collector = DataCollector()
    
    # You can pass specific player tags or leave empty to use top players
    collector.run_collection_pipeline(player_tags=[])
