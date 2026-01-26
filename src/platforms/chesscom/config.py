"""
Chess.com platform-specific configuration.

Isolates all Chess.com-specific settings so changes don't affect other platforms.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChessComConfig:
    """
    Configuration for Chess.com API connector.

    All settings have sensible defaults but can be overridden via
    environment variables or constructor arguments.
    """

    # API Settings
    base_url: str = "https://api.chess.com/pub"
    user_agent: str = "ChessAnalysis/1.0 (github.com/chess-analysis)"

    # Request Settings
    timeout: int = 30  # seconds
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds (base delay, exponential backoff applied)
    min_request_interval: float = 0.1  # seconds between requests

    # Cache Settings
    cache_enabled: bool = True
    cache_ttl: int = 3600  # seconds (1 hour)
    cache_dir: Optional[str] = None  # None = use default

    # Default Query Settings
    default_months_back: int = 6  # Default time range for game fetching

    def __post_init__(self):
        """Load settings from environment variables if not set."""
        # Allow environment variable overrides
        if env_base_url := os.getenv("CHESS_COM_API_URL"):
            self.base_url = env_base_url

        if env_user_agent := os.getenv("CHESS_COM_USER_AGENT"):
            self.user_agent = env_user_agent

        if env_timeout := os.getenv("CHESS_COM_TIMEOUT"):
            self.timeout = int(env_timeout)

        if env_cache_dir := os.getenv("CHESS_COM_CACHE_DIR"):
            self.cache_dir = env_cache_dir

    @classmethod
    def from_env(cls) -> "ChessComConfig":
        """Create configuration from environment variables."""
        return cls()


# Default configuration instance
DEFAULT_CONFIG = ChessComConfig()
