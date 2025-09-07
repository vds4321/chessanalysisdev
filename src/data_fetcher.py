"""
Chess.com API Data Fetcher

This module handles downloading games from Chess.com API with proper
rate limiting, caching, and error handling.
"""

import requests
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from tqdm import tqdm
import logging

from config.settings import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChessComDataFetcher:
    """Fetches chess game data from Chess.com API."""
    
    def __init__(self, username: Optional[str] = None):
        """
        Initialize the data fetcher.
        
        Args:
            username: Chess.com username. If None, uses config setting.
        """
        self.username = username or Config.CHESS_COM_USERNAME
        if not self.username:
            raise ValueError("Chess.com username must be provided")
        
        self.base_url = Config.CHESS_COM_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ChessAnalysisApp/1.0 (Contact: your-email@example.com)'
        })
        
        # Ensure cache directory exists
        os.makedirs(Config.CACHE_DIR, exist_ok=True)
    
    def _make_request(self, url: str, max_retries: Optional[int] = None) -> Optional[Dict]:
        """
        Make a request with retry logic and rate limiting.
        
        Args:
            url: URL to request
            max_retries: Maximum number of retries
            
        Returns:
            JSON response data or None if failed
        """
        max_retries = max_retries or Config.MAX_RETRIES
        
        for attempt in range(max_retries + 1):
            try:
                response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    wait_time = Config.RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 404:
                    logger.error(f"Resource not found: {url}")
                    return None
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                
            if attempt < max_retries:
                time.sleep(Config.RETRY_DELAY * (attempt + 1))
        
        logger.error(f"Failed to fetch {url} after {max_retries + 1} attempts")
        return None
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Get cache file path for a given key."""
        return os.path.join(Config.CACHE_DIR, f"{cache_key}.json")
    
    def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Load data from cache if it exists and is recent."""
        cache_path = self._get_cache_path(cache_key)
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cached_data = json.load(f)
                
                # Check if cache is less than 1 hour old
                cache_time = datetime.fromisoformat(cached_data.get('cached_at', ''))
                if datetime.now() - cache_time < timedelta(hours=1):
                    logger.info(f"Using cached data for {cache_key}")
                    return cached_data['data']
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Invalid cache file {cache_path}: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict) -> None:
        """Save data to cache with timestamp."""
        cache_path = self._get_cache_path(cache_key)
        
        cached_data = {
            'cached_at': datetime.now().isoformat(),
            'data': data
        }
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(cached_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache {cache_path}: {e}")
    
    def get_player_profile(self) -> Optional[Dict]:
        """
        Get player profile information.
        
        Returns:
            Player profile data or None if failed
        """
        cache_key = f"profile_{self.username}"
        
        # Try cache first
        cached_data = self._load_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        url = f"{self.base_url}/player/{self.username}"
        data = self._make_request(url)
        
        if data:
            self._save_to_cache(cache_key, data)
        
        return data
    
    def get_available_archives(self) -> List[str]:
        """
        Get list of available game archives for the player.
        
        Returns:
            List of archive URLs
        """
        cache_key = f"archives_{self.username}"
        
        # Try cache first
        cached_data = self._load_from_cache(cache_key)
        if cached_data:
            return cached_data.get('archives', [])
        
        url = f"{self.base_url}/player/{self.username}/games/archives"
        data = self._make_request(url)
        
        if data:
            self._save_to_cache(cache_key, data)
            return data.get('archives', [])
        
        return []
    
    def get_games_for_month(self, year: int, month: int) -> List[Dict]:
        """
        Get all games for a specific month.
        
        Args:
            year: Year (e.g., 2023)
            month: Month (1-12)
            
        Returns:
            List of game dictionaries
        """
        cache_key = f"games_{self.username}_{year}_{month:02d}"
        
        # Try cache first
        cached_data = self._load_from_cache(cache_key)
        if cached_data:
            return cached_data.get('games', [])
        
        url = f"{self.base_url}/player/{self.username}/games/{year}/{month:02d}"
        data = self._make_request(url)
        
        if data:
            self._save_to_cache(cache_key, data)
            return data.get('games', [])
        
        return []
    
    def get_all_games(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Get all games within a date range.
        
        Args:
            start_date: Start date (inclusive). If None, gets all available games.
            end_date: End date (inclusive). If None, uses current date.
            
        Returns:
            List of all game dictionaries
        """
        logger.info(f"Fetching games for {self.username}")
        
        # Get available archives
        archives = self.get_available_archives()
        if not archives:
            logger.error("No game archives found")
            return []
        
        # Filter archives by date range if specified
        filtered_archives = []
        for archive_url in archives:
            # Extract year/month from URL: .../games/2023/01
            parts = archive_url.split('/')
            if len(parts) >= 2:
                try:
                    year = int(parts[-2])
                    month = int(parts[-1])
                    archive_date = datetime(year, month, 1)
                    
                    # Check if archive is within date range
                    if start_date and archive_date < start_date.replace(day=1):
                        continue
                    if end_date and archive_date > end_date.replace(day=1):
                        continue
                    
                    filtered_archives.append((year, month))
                except (ValueError, IndexError):
                    continue
        
        # Fetch games from filtered archives
        all_games = []
        for year, month in tqdm(filtered_archives, desc="Fetching game archives"):
            games = self.get_games_for_month(year, month)
            
            # Filter games by exact date range if specified
            if start_date or end_date:
                filtered_games = []
                for game in games:
                    game_date = datetime.fromtimestamp(game.get('end_time', 0))
                    
                    if start_date and game_date < start_date:
                        continue
                    if end_date and game_date > end_date:
                        continue
                    
                    filtered_games.append(game)
                
                games = filtered_games
            
            all_games.extend(games)
            
            # Be respectful to the API
            time.sleep(0.1)
        
        logger.info(f"Fetched {len(all_games)} games")
        return all_games
    
    def save_games_to_file(self, games: List[Dict], filename: Optional[str] = None) -> str:
        """
        Save games to a JSON file.
        
        Args:
            games: List of game dictionaries
            filename: Output filename. If None, generates based on username and date.
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.username}_games_{timestamp}.json"
        
        filepath = os.path.join(Config.RAW_DATA_DIR, filename)
        os.makedirs(Config.RAW_DATA_DIR, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(games, f, indent=2)
        
        logger.info(f"Saved {len(games)} games to {filepath}")
        return filepath


def main():
    """Example usage of the data fetcher."""
    # This requires CHESS_COM_USERNAME to be set in environment or config
    try:
        fetcher = ChessComDataFetcher()
        
        # Get player profile
        profile = fetcher.get_player_profile()
        if profile:
            print(f"Player: {profile.get('username')}")
            print(f"Joined: {datetime.fromtimestamp(profile.get('joined', 0))}")
        
        # Get recent games (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        games = fetcher.get_all_games(start_date=start_date, end_date=end_date)
        
        if games:
            filepath = fetcher.save_games_to_file(games)
            print(f"Downloaded {len(games)} games to {filepath}")
        else:
            print("No games found in the specified date range")
            
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set CHESS_COM_USERNAME in your environment or config/.env file")


if __name__ == "__main__":
    main()