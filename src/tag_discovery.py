import os
import time
import logging
from typing import Set, List, Dict
from collections import deque
from dotenv import load_dotenv

from api.client import ClashRoyaleAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tag_discovery.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TagDiscovery:
    """Discovers player tags by crawling through battle opponents."""

    def __init__(self, api_key: str = None):
        self.api = ClashRoyaleAPI(api_key)
        self.discovered_tags: Set[str] = set()
        self.tags_by_range: Dict[str, List[str]] = {
            '0-4000': [],
            '4000-8000': [],
            '8000-10000': [],
            '10000-15000': []
        }
        self.failed_tags: Set[str] = set()

    def get_trophy_range(self, trophies: int) -> str:
        """Determine trophy range for a player."""
        if trophies < 4000:
            return '0-4000'
        elif trophies < 8000:
            return '4000-8000'
        elif trophies < 10000:
            return '8000-10000'
        else:
            return '10000-15000'

    def discover_tags_from_player(self, player_tag: str) -> List[str]:
        """Get opponent tags from a player's battle history."""
        try:
            logger.info(f"Fetching battles for {player_tag}")
            battles = self.api.get_player_battles(player_tag, limit=25)

            opponent_tags = []
            for battle in battles:
                try:
                    # Get opponent from battle data
                    opponent = battle.get('opponent', [{}])[0]
                    opponent_tag = opponent.get('tag', '')

                    if opponent_tag and opponent_tag not in self.discovered_tags:
                        opponent_tags.append(opponent_tag)
                except Exception as e:
                    logger.debug(f"Error extracting opponent from battle: {e}")
                    continue

            # Small delay to respect rate limits
            time.sleep(0.1)
            return opponent_tags

        except Exception as e:
            logger.error(f"Error fetching battles for {player_tag}: {e}")
            self.failed_tags.add(player_tag)
            return []

    def get_player_trophies(self, player_tag: str) -> int:
        """Get a player's trophy count."""
        try:
            player_data = self.api.get_player(player_tag)
            return player_data.get('trophies', 0)
        except Exception as e:
            logger.error(f"Error fetching player {player_tag}: {e}")
            return 0

    def crawl_tags(
        self,
        seed_tags: List[str],
        target_total: int = 1000,
        targets_per_range: Dict[str, int] = None
    ) -> Dict[str, List[str]]:
        """
        Crawl player network to discover tags across trophy ranges.

        Args:
            seed_tags: Initial player tags to start crawling from
            target_total: Total number of unique tags to discover
            targets_per_range: Target distribution by trophy range
        """
        if targets_per_range is None:
            # Default: aim for even distribution
            targets_per_range = {
                '0-4000': 250,
                '4000-8000': 250,
                '8000-10000': 250,
                '10000-15000': 250
            }

        logger.info(f"Starting tag discovery with targets: {targets_per_range}")
        logger.info(f"Total target: {target_total} tags")

        # Initialize queue with seed tags
        queue = deque(seed_tags)

        # Track which tags we've already queued
        queued_tags = set(seed_tags)

        while len(self.discovered_tags) < target_total and queue:
            current_tag = queue.popleft()

            # Skip if already processed or failed
            if current_tag in self.discovered_tags or current_tag in self.failed_tags:
                continue

            # Get player's trophy count
            trophies = self.get_player_trophies(current_tag)
            if trophies == 0:
                self.failed_tags.add(current_tag)
                continue

            # Determine trophy range
            trophy_range = self.get_trophy_range(trophies)

            # Check if we still need players in this range
            if len(self.tags_by_range[trophy_range]) < targets_per_range[trophy_range]:
                self.discovered_tags.add(current_tag)
                self.tags_by_range[trophy_range].append(current_tag)
                logger.info(
                    f"Added {current_tag} ({trophies} trophies) to {trophy_range} "
                    f"[{len(self.tags_by_range[trophy_range])}/{targets_per_range[trophy_range]}]"
                )
            else:
                # Range is full, but still add to discovered set
                self.discovered_tags.add(current_tag)

            # Get opponent tags from this player's battles
            opponent_tags = self.discover_tags_from_player(current_tag)

            # Add new opponents to queue
            for opponent_tag in opponent_tags:
                if opponent_tag not in queued_tags and opponent_tag not in self.failed_tags:
                    queue.append(opponent_tag)
                    queued_tags.add(opponent_tag)

            # Log progress every 50 tags
            if len(self.discovered_tags) % 50 == 0:
                total = len(self.discovered_tags)
                logger.info(f"Progress: {total}/{target_total} tags discovered")
                for range_name, tags in self.tags_by_range.items():
                    logger.info(f"  {range_name}: {len(tags)}/{targets_per_range[range_name]}")

            # Check if all ranges are satisfied
            all_satisfied = all(
                len(self.tags_by_range[range_name]) >= targets_per_range[range_name]
                for range_name in targets_per_range
            )
            if all_satisfied:
                logger.info("All trophy ranges have reached their targets!")
                break

        # Log final summary
        logger.info(f"\n=== Discovery Complete ===")
        logger.info(f"Total tags discovered: {len(self.discovered_tags)}")
        logger.info(f"Failed tags: {len(self.failed_tags)}")
        for range_name, tags in self.tags_by_range.items():
            logger.info(f"{range_name}: {len(tags)} tags")

        return self.tags_by_range

    def save_tags_to_file(self, filename: str = 'player_tags.txt'):
        """Save discovered tags to file, organized by trophy range."""
        try:
            with open(filename, 'w') as f:
                f.write("# Player tags discovered by crawler\n")
                f.write("# Organized by trophy range\n")
                f.write(f"# Total: {len(self.discovered_tags)} tags\n")
                f.write("#\n")

                for range_name in sorted(self.tags_by_range.keys()):
                    tags = self.tags_by_range[range_name]
                    f.write(f"\n# {range_name} trophies ({len(tags)} players)\n")
                    for tag in tags:
                        # Remove # prefix if present for storage
                        clean_tag = tag.replace('#', '')
                        f.write(f"{clean_tag}\n")

            logger.info(f"Saved {len(self.discovered_tags)} tags to {filename}")

        except Exception as e:
            logger.error(f"Error saving tags to file: {e}")

if __name__ == "__main__":
    load_dotenv()

    # Read seed tags from player_tags.txt
    seed_tags = []
    try:
        with open('player_tags.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Add # prefix if not present
                    if not line.startswith('#'):
                        line = '#' + line
                    seed_tags.append(line)
    except FileNotFoundError:
        logger.warning("player_tags.txt not found, using default seed tag")
        seed_tags = [os.getenv('SAMPLE_PLAYER_TAG', '#2RPPVLR8J')]

    logger.info(f"Starting with {len(seed_tags)} seed tag(s): {seed_tags}")

    # Initialize discovery
    discovery = TagDiscovery()

    # Crawl for tags
    discovery.crawl_tags(
        seed_tags=seed_tags,
        target_total=1000,
        targets_per_range={
            '0-4000': 250,
            '4000-8000': 250,
            '8000-10000': 250,
            '10000-15000': 250
        }
    )

    # Save results
    discovery.save_tags_to_file('player_tags.txt')
