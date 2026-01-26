"""
Chess.com platform connector.

Provides Chess.com API integration with:
- Game fetching with rate limiting and caching
- Data normalization to common schemas
- Platform-specific game type definitions

Usage:
    from src.platforms.chesscom import ChessComConnector

    connector = ChessComConnector()
    games = list(connector.get_games("hikaru", max_games=100))
"""

from .connector import ChessComConnector
from .normalizer import ChessComNormalizer
from .config import ChessComConfig

__all__ = [
    "ChessComConnector",
    "ChessComNormalizer",
    "ChessComConfig",
]
