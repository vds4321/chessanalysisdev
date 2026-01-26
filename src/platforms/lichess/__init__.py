"""
Lichess platform connector.

Provides Lichess API integration with:
- Game fetching with streaming support and rate limiting
- Optional authentication for higher rate limits
- Data normalization to common schemas
- Platform-specific game type definitions

Usage:
    from src.platforms.lichess import LichessConnector

    # Public access (limited rate)
    connector = LichessConnector()

    # With API token (higher rate limits)
    connector = LichessConnector(api_token="lip_xxxx")

    games = list(connector.get_games("DrNykterstein", max_games=100))
"""

from .connector import LichessConnector
from .normalizer import LichessNormalizer
from .config import LichessConfig

__all__ = [
    "LichessConnector",
    "LichessNormalizer",
    "LichessConfig",
]
