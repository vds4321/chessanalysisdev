"""
Chess.com platform connector.

Implements the PlatformConnector protocol for Chess.com API.
Handles rate limiting, caching, and data normalization.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Iterator

import requests

from src.core.constants import Platform, TimeClass
from src.core.schemas import (
    NormalizedGame,
    PlayerProfile,
    GameFilter,
)
from src.core.exceptions import (
    APIError,
    RateLimitError,
    UserNotFoundError,
    NormalizationError,
)

from .config import ChessComConfig, DEFAULT_CONFIG
from .normalizer import ChessComNormalizer

logger = logging.getLogger(__name__)


class ChessComConnector:
    """
    Chess.com API connector.

    Implements the PlatformConnector protocol for Chess.com.
    Handles all API communication, rate limiting, caching, and
    data normalization.

    Example:
        >>> connector = ChessComConnector()
        >>> games = list(connector.get_games("hikaru", max_games=10))
        >>> print(f"Fetched {len(games)} games")
    """

    def __init__(self, config: Optional[ChessComConfig] = None):
        """
        Initialize Chess.com connector.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or DEFAULT_CONFIG
        self.normalizer = ChessComNormalizer()

        # Set up HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.config.user_agent,
            "Accept": "application/json",
        })

        # Rate limiting
        self._last_request_time: float = 0

        # Cache setup
        self._cache_dir: Optional[Path] = None
        if self.config.cache_enabled:
            self._setup_cache()

    @property
    def platform_id(self) -> str:
        """Unique platform identifier."""
        return "chesscom"

    @property
    def platform_name(self) -> str:
        """Human-readable platform name."""
        return "Chess.com"

    @property
    def platform(self) -> Platform:
        """Platform enum value."""
        return Platform.CHESS_COM

    # =========================================================================
    # Cache Management
    # =========================================================================

    def _setup_cache(self) -> None:
        """Set up cache directory."""
        if self.config.cache_dir:
            self._cache_dir = Path(self.config.cache_dir)
        else:
            # Default to data/cache in project root
            self._cache_dir = Path("data/cache/chesscom")

        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, endpoint: str) -> str:
        """Generate cache key from endpoint."""
        # Remove base URL and clean up for filename
        clean = endpoint.replace("/", "_").replace("?", "_").replace("&", "_")
        return clean[:200]  # Limit length

    def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Load data from cache if valid."""
        if not self._cache_dir:
            return None

        cache_file = self._cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r") as f:
                cached = json.load(f)

            # Check TTL
            cached_at = datetime.fromisoformat(cached.get("cached_at", ""))
            if datetime.now() - cached_at > timedelta(seconds=self.config.cache_ttl):
                logger.debug(f"Cache expired for {cache_key}")
                return None

            logger.debug(f"Cache hit for {cache_key}")
            return cached.get("data")

        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            return None

    def _save_to_cache(self, cache_key: str, data: Dict) -> None:
        """Save data to cache."""
        if not self._cache_dir:
            return

        cache_file = self._cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, "w") as f:
                json.dump({
                    "cached_at": datetime.now().isoformat(),
                    "data": data,
                }, f)
            logger.debug(f"Cached {cache_key}")
        except Exception as e:
            logger.warning(f"Error saving to cache: {e}")

    # =========================================================================
    # Rate Limiting
    # =========================================================================

    def _rate_limit(self) -> None:
        """Ensure minimum interval between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.config.min_request_interval:
            sleep_time = self.config.min_request_interval - elapsed
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    # =========================================================================
    # HTTP Requests
    # =========================================================================

    def _make_request(
        self,
        endpoint: str,
        use_cache: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Make API request with retry logic and caching.

        Args:
            endpoint: API endpoint (appended to base URL)
            use_cache: Whether to use caching

        Returns:
            JSON response as dict, or None if not found

        Raises:
            APIError: If request fails after retries
            RateLimitError: If rate limited and retries exhausted
        """
        url = f"{self.config.base_url}{endpoint}"
        cache_key = self._get_cache_key(endpoint)

        # Try cache first
        if use_cache:
            cached = self._load_from_cache(cache_key)
            if cached is not None:
                return cached

        # Make request with retries
        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):
            self._rate_limit()

            try:
                response = self.session.get(
                    url,
                    timeout=self.config.timeout,
                )

                if response.status_code == 200:
                    data = response.json()
                    if use_cache:
                        self._save_to_cache(cache_key, data)
                    return data

                elif response.status_code == 429:
                    # Rate limited
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Rate limited by Chess.com. Waiting {wait_time:.1f}s "
                        f"(attempt {attempt + 1}/{self.config.max_retries + 1})"
                    )
                    time.sleep(wait_time)
                    continue

                elif response.status_code == 404:
                    logger.debug(f"Resource not found: {endpoint}")
                    return None

                else:
                    logger.warning(
                        f"HTTP {response.status_code} for {endpoint}"
                    )
                    last_error = APIError(
                        f"HTTP {response.status_code}",
                        platform="chesscom",
                        status_code=response.status_code,
                        url=url,
                    )

            except requests.Timeout:
                logger.warning(f"Request timeout for {endpoint}")
                last_error = APIError(
                    "Request timeout",
                    platform="chesscom",
                    url=url,
                )

            except requests.RequestException as e:
                logger.warning(f"Request failed: {e}")
                last_error = APIError(
                    str(e),
                    platform="chesscom",
                    url=url,
                )

            # Wait before retry
            if attempt < self.config.max_retries:
                time.sleep(self.config.retry_delay * (attempt + 1))

        # All retries exhausted
        if last_error:
            raise last_error
        raise APIError("Request failed", platform="chesscom", url=url)

    # =========================================================================
    # Public API Methods
    # =========================================================================

    def validate_username(self, username: str) -> bool:
        """
        Check if username exists on Chess.com.

        Args:
            username: Username to validate

        Returns:
            True if username exists
        """
        try:
            result = self._make_request(f"/player/{username.lower()}")
            return result is not None
        except APIError:
            return False

    def get_player_profile(self, username: str) -> Optional[PlayerProfile]:
        """
        Fetch and normalize player profile.

        Args:
            username: Player's Chess.com username

        Returns:
            PlayerProfile if found, None otherwise
        """
        profile_data = self._make_request(f"/player/{username.lower()}")
        if not profile_data:
            return None

        # Also fetch stats for ratings
        stats_data = self._make_request(f"/player/{username.lower()}/stats")

        return self.normalizer.normalize_profile(profile_data, stats_data)

    def get_player_stats(self, username: str) -> Dict[str, Any]:
        """
        Get raw player statistics.

        Args:
            username: Player's Chess.com username

        Returns:
            Stats dict from Chess.com API
        """
        return self._make_request(f"/player/{username.lower()}/stats") or {}

    def _get_archives(self, username: str) -> List[str]:
        """
        Get list of available game archive URLs.

        Chess.com organizes games by month. This returns URLs to each
        monthly archive.
        """
        result = self._make_request(f"/player/{username.lower()}/games/archives")
        return result.get("archives", []) if result else []

    def _get_games_for_month(
        self,
        username: str,
        year: int,
        month: int,
    ) -> List[Dict]:
        """Fetch raw games for a specific month."""
        result = self._make_request(
            f"/player/{username.lower()}/games/{year}/{month:02d}"
        )
        return result.get("games", []) if result else []

    def get_games(
        self,
        username: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        game_filter: Optional[GameFilter] = None,
    ) -> Iterator[NormalizedGame]:
        """
        Fetch games and yield normalized game objects.

        Uses iterator pattern for memory efficiency with large game histories.
        Games are yielded newest-first by default.

        Args:
            username: Player's Chess.com username
            start_date: Optional start of date range
            end_date: Optional end of date range (defaults to now)
            game_filter: Optional additional filters

        Yields:
            NormalizedGame objects

        Example:
            >>> for game in connector.get_games("hikaru", max_games=100):
            ...     print(f"{game.played_at}: {game.result.value}")
        """
        # Set default date range
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=self.config.default_months_back * 30)

        # Get archives
        archives = self._get_archives(username)
        if not archives:
            logger.warning(f"No game archives found for {username}")
            return

        # Filter archives by date range
        filtered_archives = []
        for archive_url in archives:
            try:
                # URL format: .../games/{year}/{month}
                parts = archive_url.rstrip("/").split("/")
                year, month = int(parts[-2]), int(parts[-1])
                archive_date = datetime(year, month, 1)

                # Check if archive overlaps with date range
                archive_end = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)

                if archive_end >= start_date and archive_date <= end_date:
                    filtered_archives.append((year, month))

            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse archive URL {archive_url}: {e}")
                continue

        # Sort newest first
        filtered_archives.sort(reverse=True)

        # Fetch and normalize games
        games_yielded = 0
        max_games = game_filter.max_games if game_filter else None

        for year, month in filtered_archives:
            if max_games and games_yielded >= max_games:
                return

            logger.debug(f"Fetching games for {year}/{month:02d}")
            raw_games = self._get_games_for_month(username, year, month)

            # Sort by end_time descending (newest first)
            raw_games.sort(key=lambda g: g.get("end_time", 0), reverse=True)

            for raw_game in raw_games:
                if max_games and games_yielded >= max_games:
                    return

                try:
                    normalized = self.normalizer.normalize_game(raw_game, username)

                    # Apply date filter
                    if normalized.played_at < start_date:
                        continue
                    if normalized.played_at > end_date:
                        continue

                    # Apply game filter
                    if game_filter and not game_filter.matches(normalized):
                        continue

                    yield normalized
                    games_yielded += 1

                except NormalizationError as e:
                    logger.warning(f"Skipping game due to normalization error: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Unexpected error processing game: {e}")
                    continue

        logger.info(f"Yielded {games_yielded} games for {username}")

    def get_games_list(
        self,
        username: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        game_filter: Optional[GameFilter] = None,
    ) -> List[NormalizedGame]:
        """
        Fetch games as a list (convenience method).

        Same as get_games() but returns a list instead of iterator.
        Use get_games() for large datasets to avoid memory issues.
        """
        return list(self.get_games(username, start_date, end_date, game_filter))

    def get_current_games(self, username: str) -> List[Dict[str, Any]]:
        """
        Get currently active daily games.

        Useful for anti-scouting features to detect if users are
        currently playing each other.

        Args:
            username: Player's Chess.com username

        Returns:
            List of active game data dicts
        """
        result = self._make_request(
            f"/player/{username.lower()}/games",
            use_cache=False,  # Don't cache current games
        )
        return result.get("games", []) if result else []

    def get_game_count(self, username: str) -> Dict[str, int]:
        """
        Get total game count by time control.

        Useful for checking if player has enough games for analysis.

        Args:
            username: Player's Chess.com username

        Returns:
            Dict mapping time class to game count
        """
        stats = self.get_player_stats(username)
        counts = {}

        stat_mappings = [
            ("chess_bullet", "bullet"),
            ("chess_blitz", "blitz"),
            ("chess_rapid", "rapid"),
            ("chess_daily", "daily"),
        ]

        for stat_key, time_class in stat_mappings:
            stat_data = stats.get(stat_key, {})
            record = stat_data.get("record", {})
            total = record.get("win", 0) + record.get("loss", 0) + record.get("draw", 0)
            if total > 0:
                counts[time_class] = total

        return counts
