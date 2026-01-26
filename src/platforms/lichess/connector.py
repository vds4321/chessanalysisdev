"""
Lichess platform connector.

Implements the PlatformConnector protocol for Lichess API.
Handles rate limiting, streaming responses, and data normalization.
"""

import json
import logging
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
    AuthenticationError,
    NormalizationError,
)

from .config import LichessConfig, DEFAULT_CONFIG
from .normalizer import LichessNormalizer

logger = logging.getLogger(__name__)


class LichessConnector:
    """
    Lichess API connector.

    Implements the PlatformConnector protocol for Lichess.
    Supports both authenticated and unauthenticated access.

    Lichess API features:
    - NDJSON streaming for efficient game downloads
    - Higher rate limits with authentication
    - Comprehensive game metadata including openings

    Example:
        >>> # Unauthenticated (lower rate limits)
        >>> connector = LichessConnector()

        >>> # Authenticated (recommended)
        >>> connector = LichessConnector(api_token="lip_xxxx")

        >>> games = list(connector.get_games("DrNykterstein", max_games=10))
    """

    def __init__(
        self,
        config: Optional[LichessConfig] = None,
        api_token: Optional[str] = None,
    ):
        """
        Initialize Lichess connector.

        Args:
            config: Optional configuration. Uses defaults if not provided.
            api_token: Optional API token (overrides config token)
        """
        self.config = config or DEFAULT_CONFIG

        # Allow token override
        if api_token:
            self.config.api_token = api_token

        self.normalizer = LichessNormalizer()

        # Set up HTTP session
        self.session = requests.Session()
        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "application/x-ndjson",
        }

        if self.config.api_token:
            headers["Authorization"] = f"Bearer {self.config.api_token}"
            logger.info("Lichess connector initialized with authentication")
        else:
            logger.info("Lichess connector initialized without authentication (limited rate)")

        self.session.headers.update(headers)

        # Rate limiting
        self._last_request_time: float = 0

        # Cache setup
        self._cache_dir: Optional[Path] = None
        if self.config.cache_enabled:
            self._setup_cache()

    @property
    def platform_id(self) -> str:
        """Unique platform identifier."""
        return "lichess"

    @property
    def platform_name(self) -> str:
        """Human-readable platform name."""
        return "Lichess"

    @property
    def platform(self) -> Platform:
        """Platform enum value."""
        return Platform.LICHESS

    @property
    def is_authenticated(self) -> bool:
        """Check if connector has API token."""
        return self.config.is_authenticated

    # =========================================================================
    # Cache Management
    # =========================================================================

    def _setup_cache(self) -> None:
        """Set up cache directory."""
        if self.config.cache_dir:
            self._cache_dir = Path(self.config.cache_dir)
        else:
            self._cache_dir = Path("data/cache/lichess")

        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, endpoint: str) -> str:
        """Generate cache key from endpoint."""
        clean = endpoint.replace("/", "_").replace("?", "_").replace("&", "_")
        return clean[:200]

    def _load_from_cache(self, cache_key: str) -> Optional[Any]:
        """Load data from cache if valid."""
        if not self._cache_dir:
            return None

        cache_file = self._cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r") as f:
                cached = json.load(f)

            cached_at = datetime.fromisoformat(cached.get("cached_at", ""))
            if datetime.now() - cached_at > timedelta(seconds=self.config.cache_ttl):
                return None

            logger.debug(f"Cache hit for {cache_key}")
            return cached.get("data")

        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            return None

    def _save_to_cache(self, cache_key: str, data: Any) -> None:
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
        except Exception as e:
            logger.warning(f"Error saving to cache: {e}")

    # =========================================================================
    # Rate Limiting
    # =========================================================================

    def _rate_limit(self) -> None:
        """Ensure minimum interval between requests."""
        interval = self.config.effective_rate_limit
        elapsed = time.time() - self._last_request_time
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request_time = time.time()

    # =========================================================================
    # HTTP Requests
    # =========================================================================

    def _make_request(
        self,
        endpoint: str,
        use_cache: bool = True,
        accept: str = "application/json",
    ) -> Optional[Dict[str, Any]]:
        """
        Make API request for JSON response.

        Args:
            endpoint: API endpoint
            use_cache: Whether to use caching
            accept: Accept header value

        Returns:
            JSON response as dict
        """
        url = f"{self.config.base_url}{endpoint}"
        cache_key = self._get_cache_key(endpoint)

        if use_cache:
            cached = self._load_from_cache(cache_key)
            if cached is not None:
                return cached

        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):
            self._rate_limit()

            try:
                response = self.session.get(
                    url,
                    timeout=self.config.timeout,
                    headers={"Accept": accept},
                )

                if response.status_code == 200:
                    data = response.json()
                    if use_cache:
                        self._save_to_cache(cache_key, data)
                    return data

                elif response.status_code == 429:
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limited. Waiting {wait_time:.1f}s")
                    time.sleep(wait_time)
                    continue

                elif response.status_code == 401:
                    raise AuthenticationError(
                        "Invalid or expired API token",
                        platform="lichess",
                    )

                elif response.status_code == 404:
                    return None

                else:
                    last_error = APIError(
                        f"HTTP {response.status_code}",
                        platform="lichess",
                        status_code=response.status_code,
                        url=url,
                    )

            except requests.Timeout:
                last_error = APIError("Request timeout", platform="lichess", url=url)

            except requests.RequestException as e:
                last_error = APIError(str(e), platform="lichess", url=url)

            if attempt < self.config.max_retries:
                time.sleep(self.config.retry_delay * (attempt + 1))

        if last_error:
            raise last_error
        raise APIError("Request failed", platform="lichess", url=url)

    def _stream_ndjson(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Stream NDJSON response from Lichess.

        Lichess supports NDJSON (newline-delimited JSON) for efficient
        streaming of large datasets like game exports.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Yields:
            Parsed JSON objects
        """
        url = f"{self.config.base_url}{endpoint}"
        self._rate_limit()

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.config.timeout,
                headers={"Accept": "application/x-ndjson"},
                stream=True,
            )

            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid or expired API token",
                    platform="lichess",
                )

            if response.status_code == 429:
                raise RateLimitError(platform="lichess")

            if response.status_code == 404:
                return

            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    try:
                        yield json.loads(line.decode("utf-8"))
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse NDJSON line: {e}")
                        continue

        except requests.RequestException as e:
            raise APIError(str(e), platform="lichess", url=url)

    # =========================================================================
    # Public API Methods
    # =========================================================================

    def validate_username(self, username: str) -> bool:
        """
        Check if username exists on Lichess.

        Args:
            username: Username to validate

        Returns:
            True if username exists
        """
        try:
            result = self._make_request(f"/user/{username}")
            return result is not None
        except APIError:
            return False

    def get_player_profile(self, username: str) -> Optional[PlayerProfile]:
        """
        Fetch and normalize player profile.

        Args:
            username: Player's Lichess username

        Returns:
            PlayerProfile if found, None otherwise
        """
        profile_data = self._make_request(f"/user/{username}")
        if not profile_data:
            return None

        return self.normalizer.normalize_profile(profile_data)

    def get_player_stats(self, username: str) -> Dict[str, Any]:
        """
        Get raw player statistics.

        For Lichess, stats are included in the user profile.

        Args:
            username: Player's Lichess username

        Returns:
            Stats dict (perfs section from profile)
        """
        profile = self._make_request(f"/user/{username}")
        if profile:
            return profile.get("perfs", {})
        return {}

    def get_games(
        self,
        username: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        game_filter: Optional[GameFilter] = None,
    ) -> Iterator[NormalizedGame]:
        """
        Fetch games and yield normalized game objects.

        Uses Lichess streaming API for efficient downloads.
        Games are yielded newest-first by default.

        Args:
            username: Player's Lichess username
            start_date: Optional start of date range
            end_date: Optional end of date range
            game_filter: Optional additional filters

        Yields:
            NormalizedGame objects

        Example:
            >>> for game in connector.get_games("DrNykterstein", max_games=50):
            ...     print(f"{game.played_at}: {game.result.value}")
        """
        # Build query parameters
        params: Dict[str, Any] = {
            "opening": "true",  # Include opening info
            "moves": "true",    # Include moves
            "tags": "true",     # Include PGN tags
        }

        # Date range (Lichess uses milliseconds)
        if start_date:
            params["since"] = int(start_date.timestamp() * 1000)
        if end_date:
            params["until"] = int(end_date.timestamp() * 1000)

        # Max games
        max_games = None
        if game_filter and game_filter.max_games:
            max_games = game_filter.max_games
            params["max"] = max_games

        # Time control filter
        if game_filter and game_filter.time_classes:
            # Lichess uses perfType parameter
            perf_types = []
            time_class_map = {
                TimeClass.ULTRA_BULLET: "ultraBullet",
                TimeClass.BULLET: "bullet",
                TimeClass.BLITZ: "blitz",
                TimeClass.RAPID: "rapid",
                TimeClass.CLASSICAL: "classical",
                TimeClass.CORRESPONDENCE: "correspondence",
            }
            for tc in game_filter.time_classes:
                if tc in time_class_map:
                    perf_types.append(time_class_map[tc])
            if perf_types:
                params["perfType"] = ",".join(perf_types)

        # Rated only
        if game_filter and game_filter.rated_only:
            params["rated"] = "true"

        # Color filter
        if game_filter and game_filter.color_filter:
            params["color"] = game_filter.color_filter.value

        # Stream games
        endpoint = f"/games/user/{username}"
        games_yielded = 0

        logger.info(f"Fetching Lichess games for {username}")

        for raw_game in self._stream_ndjson(endpoint, params):
            if max_games and games_yielded >= max_games:
                return

            try:
                normalized = self.normalizer.normalize_game(raw_game, username)

                # Apply additional filters not supported by API
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
        """
        return list(self.get_games(username, start_date, end_date, game_filter))

    def get_current_games(self, username: str) -> List[Dict[str, Any]]:
        """
        Get currently active games.

        Useful for anti-scouting features.

        Args:
            username: Player's Lichess username

        Returns:
            List of active game data dicts
        """
        result = self._make_request(
            f"/user/{username}/current-game",
            use_cache=False,
        )
        if result:
            return [result]
        return []

    def get_ongoing_games(self, username: str) -> List[Dict[str, Any]]:
        """
        Get all ongoing games (TV, playing, etc.).

        Args:
            username: Player's Lichess username

        Returns:
            List of ongoing game data
        """
        games = []
        for game in self._stream_ndjson(f"/user/{username}/games", {"playing": "true"}):
            games.append(game)
        return games

    def get_game_count(self, username: str) -> Dict[str, int]:
        """
        Get total game count by time control.

        Args:
            username: Player's Lichess username

        Returns:
            Dict mapping time class to game count
        """
        profile = self._make_request(f"/user/{username}")
        if not profile:
            return {}

        counts = {}
        perfs = profile.get("perfs", {})

        perf_mappings = [
            ("ultraBullet", "ultraBullet"),
            ("bullet", "bullet"),
            ("blitz", "blitz"),
            ("rapid", "rapid"),
            ("classical", "classical"),
            ("correspondence", "correspondence"),
        ]

        for perf_key, time_class in perf_mappings:
            perf_data = perfs.get(perf_key, {})
            games = perf_data.get("games", 0)
            if games > 0:
                counts[time_class] = games

        return counts

    def get_leaderboard(self, perf_type: str = "blitz", count: int = 10) -> List[Dict]:
        """
        Get top players leaderboard.

        Args:
            perf_type: Time control type (bullet, blitz, rapid, etc.)
            count: Number of players to return

        Returns:
            List of player data dicts
        """
        result = self._make_request(f"/player/top/{count}/{perf_type}")
        return result.get("users", []) if result else []
