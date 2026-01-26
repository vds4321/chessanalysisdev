"""
Lichess platform-specific configuration.

Isolates all Lichess-specific settings so changes don't affect other platforms.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class LichessConfig:
    """
    Configuration for Lichess API connector.

    Lichess has different rate limits for authenticated vs unauthenticated
    requests. Using an API token is recommended for better performance.

    To get a token: https://lichess.org/account/oauth/token
    """

    # API Settings
    base_url: str = "https://lichess.org/api"
    user_agent: str = "ChessAnalysis/1.0 (github.com/chess-analysis)"

    # Authentication (optional but recommended)
    api_token: Optional[str] = None

    # Request Settings
    timeout: int = 30  # seconds
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds

    # Rate limiting
    # Lichess limits: 20 req/sec authenticated, stricter for unauthenticated
    min_request_interval: float = 0.1  # seconds between requests
    min_request_interval_unauth: float = 0.5  # higher for unauthenticated

    # Cache Settings
    cache_enabled: bool = True
    cache_ttl: int = 3600  # seconds (1 hour)
    cache_dir: Optional[str] = None

    # Game export settings
    default_months_back: int = 6
    max_games_per_request: int = 300  # Lichess streams games, this is a soft limit

    # Performance settings
    use_streaming: bool = True  # Lichess supports NDJSON streaming

    def __post_init__(self):
        """Load settings from environment variables if not set."""
        if env_token := os.getenv("LICHESS_API_TOKEN"):
            if self.api_token is None:
                self.api_token = env_token

        if env_base_url := os.getenv("LICHESS_API_URL"):
            self.base_url = env_base_url

        if env_user_agent := os.getenv("LICHESS_USER_AGENT"):
            self.user_agent = env_user_agent

        if env_cache_dir := os.getenv("LICHESS_CACHE_DIR"):
            self.cache_dir = env_cache_dir

    @property
    def is_authenticated(self) -> bool:
        """Check if API token is configured."""
        return bool(self.api_token)

    @property
    def effective_rate_limit(self) -> float:
        """Get effective rate limit based on authentication status."""
        if self.is_authenticated:
            return self.min_request_interval
        return self.min_request_interval_unauth

    @classmethod
    def from_env(cls) -> "LichessConfig":
        """Create configuration from environment variables."""
        return cls()


# Default configuration instance
DEFAULT_CONFIG = LichessConfig()
