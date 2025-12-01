import os
import requests
import time
from typing import Dict, Optional, List, Any
from datetime import datetime
from dotenv import load_dotenv

class ClashRoyaleAPI:
    BASE_URL = "https://api.clashroyale.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Clash Royale API client.
        
        Args:
            api_key: Your Clash Royale API key. If not provided, will try to get from environment variables.
        """
        load_dotenv()
        self.api_key = api_key or os.getenv('CLASH_ROYALE_API_KEY')
        if not self.api_key:
            raise ValueError("API key not provided and CLASH_ROYALE_API_KEY not found in environment variables")
            
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to the Clash Royale API.
        
        Args:
            endpoint: API endpoint (e.g., '/players/{playerTag}')
            params: Query parameters for the request
            
        Returns:
            JSON response from the API
            
        Raises:
            requests.HTTPError: If the API returns an error status code
        """
        url = f"{self.BASE_URL}{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_player(self, player_tag: str) -> Dict:
        """Get information about a single player by player tag."""
        player_tag = player_tag.replace('#', '%23')  # URL encode the # symbol
        return self._make_request(f"/players/{player_tag}")
    
    def get_player_battles(self, player_tag: str, limit: int = 25) -> List[Dict]:
        """Get list of recent battles for a player."""
        player_tag = player_tag.replace('#', '%23')
        return self._make_request(f"/players/{player_tag}/battlelog")
    
    def get_player_chests(self, player_tag: str) -> Dict:
        """Get information about upcoming chests for a player."""
        player_tag = player_tag.replace('#', '%23')
        return self._make_request(f"/players/{player_tag}/upcomingchests")
    
    def get_cards(self) -> Dict:
        """Get list of all available cards."""
        return self._make_request("/cards")
    
    def get_tournaments(self, name: Optional[str] = None) -> Dict:
        """Search all tournaments by name."""
        params = {}
        if name:
            params['name'] = name
        return self._make_request("/tournaments", params=params)
    
    def get_popular_players(self, limit: int = 100) -> Dict:
        """Get list of top 1000 players."""
        return self._make_request("/locations/global/rankings/players")
    
    def get_popular_decks(self, limit: int = 20) -> List[Dict]:
        """Get popular decks from top players."""
        try:
            top_players = self.get_popular_players(limit=limit)['items']
            all_decks = []
            
            for player in top_players:
                try:
                    battles = self.get_player_battles(player['tag'])
                    for battle in battles:
                        if 'team' in battle and 'deck' in battle['team'][0]:
                            deck = battle['team'][0]['deck']
                            deck_info = {
                                'player_tag': player['tag'],
                                'player_name': player.get('name', ''),
                                'trophies': player.get('trophies', 0),
                                'cards': [{
                                    'id': card['id'],
                                    'level': card.get('level', 0),
                                    'max_level': card.get('maxLevel', 0)
                                } for card in deck],
                                'game_mode': battle.get('gameMode', {}).get('name', '')
                            }
                            all_decks.append(deck_info)
                except Exception as e:
                    print(f"Error getting battles for player {player.get('tag')}: {e}")
                    continue
                
                # Be nice to the API
                time.sleep(0.5)
                
            return all_decks
            
        except Exception as e:
            print(f"Error getting popular decks: {e}")
            return []
    
    def get_card_info(self, card_id: str) -> Dict:
        """Get detailed information about a specific card."""
        cards = self.get_cards()
        for card in cards.get('items', []):
            if str(card.get('id')) == str(card_id):
                return card
        return {}

# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api = ClashRoyaleAPI()
    
    # Example: Get player info
    player_tag = os.getenv('SAMPLE_PLAYER_TAG', '#2Y2JQ2U')
    try:
        player = api.get_player(player_tag)
        print(f"Player: {player.get('name')} ({player.get('tag')})")
        print(f"Trophies: {player.get('trophies')}")
        print(f"Current Deck: {player.get('currentDeck', [])}")
    except Exception as e:
        print(f"Error: {e}")
