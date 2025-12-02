import os
import time
import logging
import requests
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class ClashAPI:
    """Clash Royale API client with rate limiting and error handling."""
    
    BASE_URL = "https://api.clashroyale.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('CLASH_ROYALE_API_KEY')
        if not self.api_key:
            raise ValueError("API key required. Set CLASH_ROYALE_API_KEY env var.")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        })
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a rate-limited request to the API."""
        self._rate_limit()
        url = f"{self.BASE_URL}{endpoint}"
        
        for attempt in range(3):
            try:
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 429:
                    # Rate limited - back off exponentially
                    wait_time = (2 ** attempt) * 5
                    logger.warning(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        
        return {}
    
    def _encode_tag(self, tag: str) -> str:
        """URL encode a player/clan tag."""
        return tag.replace('#', '%23')
    
    # ========== Cards ==========
    
    def get_cards(self) -> List[Dict]:
        """Fetch all cards from the API."""
        result = self._request("/cards")
        return result.get('items', [])
    
    # ========== Players ==========
    
    def get_player(self, player_tag: str) -> Dict:
        """Get player profile."""
        return self._request(f"/players/{self._encode_tag(player_tag)}")
    
    def get_battlelog(self, player_tag: str) -> List[Dict]:
        """Get player's recent battles (up to 25)."""
        return self._request(f"/players/{self._encode_tag(player_tag)}/battlelog")
    
    # ========== Rankings ==========
    
    def get_top_players(self, location_id: str = "global", limit: int = 200) -> List[Dict]:
        """Get top players from leaderboard."""
        result = self._request(
            f"/locations/{location_id}/rankings/players",
            params={'limit': min(limit, 200)}
        )
        return result.get('items', [])
    
    def get_locations(self) -> List[Dict]:
        """Get all available locations."""
        result = self._request("/locations")
        return result.get('items', [])
    
    # ========== Tournaments ==========
    
    def search_tournaments(self, name: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Search tournaments by name."""
        params = {'limit': limit}
        if name:
            params['name'] = name
        result = self._request("/tournaments", params=params)
        return result.get('items', [])
    
    def get_tournament(self, tournament_tag: str) -> Dict:
        """Get tournament details including membersList."""
        return self._request(f"/tournaments/{self._encode_tag(tournament_tag)}")
    
    # ========== Location Rankings ==========
    
    def get_location(self, location_id: int) -> Dict:
        """Get specific location details."""
        return self._request(f"/locations/{location_id}")
    
    def get_location_player_rankings(self, location_id: int, limit: int = 200) -> List[Dict]:
        """Get player rankings for a specific location."""
        result = self._request(
            f"/locations/{location_id}/rankings/players",
            params={'limit': min(limit, 200)}
        )
        return result.get('items', [])
    
    def get_global_player_rankings(self, limit: int = 200) -> List[Dict]:
        """Get global player rankings."""
        result = self._request(
            "/locations/global/rankings/players",
            params={'limit': min(limit, 200)}
        )
        return result.get('items', [])
