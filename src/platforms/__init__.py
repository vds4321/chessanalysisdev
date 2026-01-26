"""
Platform connectors for multi-platform chess analysis.

This module provides connectors for various chess platforms:
- Chess.com
- Lichess
- (Future platforms)

Each platform has its own submodule with:
- connector.py: API client implementing PlatformConnector protocol
- normalizer.py: Converts platform data to normalized schemas
- game_types.py: Platform-specific game type definitions
- config.py: Platform-specific configuration

Use the registry to get connectors:

    from src.platforms import get_connector
    from src.core import Platform

    connector = get_connector(Platform.CHESS_COM)
    games = connector.get_games("hikaru", max_games=100)
"""

from .registry import (
    get_connector,
    register_connector,
    list_platforms,
    get_all_connectors,
)

__all__ = [
    "get_connector",
    "register_connector",
    "list_platforms",
    "get_all_connectors",
]
