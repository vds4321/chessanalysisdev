"""
Platform registry for managing platform connectors.

Implements factory pattern for easy platform instantiation.
Connectors are lazily imported to avoid loading unnecessary dependencies.
"""

import logging
from typing import Dict, Type, Optional, List, Any, Callable

from src.core.constants import Platform
from src.core.protocols import PlatformConnector
from src.core.exceptions import PlatformNotSupportedError

logger = logging.getLogger(__name__)

# Registry mapping platform IDs to connector factory functions
# Using factory functions allows lazy imports
_CONNECTOR_REGISTRY: Dict[str, Callable[..., PlatformConnector]] = {}

# Cache of instantiated connectors (optional singleton pattern)
_CONNECTOR_CACHE: Dict[str, PlatformConnector] = {}


def _register_default_connectors() -> None:
    """Register built-in platform connectors."""

    def create_chesscom_connector(**kwargs) -> PlatformConnector:
        from src.platforms.chesscom.connector import ChessComConnector
        return ChessComConnector(**kwargs)

    def create_lichess_connector(**kwargs) -> PlatformConnector:
        from src.platforms.lichess.connector import LichessConnector
        return LichessConnector(**kwargs)

    _CONNECTOR_REGISTRY["chesscom"] = create_chesscom_connector
    _CONNECTOR_REGISTRY["lichess"] = create_lichess_connector


# Initialize default connectors
_register_default_connectors()


def get_connector(
    platform: Platform,
    use_cache: bool = False,
    **kwargs: Any,
) -> PlatformConnector:
    """
    Get a platform connector instance.

    Args:
        platform: Platform enum value
        use_cache: If True, return cached connector if available
        **kwargs: Platform-specific configuration options

    Returns:
        Configured PlatformConnector instance

    Raises:
        PlatformNotSupportedError: If platform is not supported

    Examples:
        >>> connector = get_connector(Platform.CHESS_COM)
        >>> games = list(connector.get_games("hikaru", max_games=5))

        >>> connector = get_connector(Platform.LICHESS, api_token="lip_xxx")
        >>> profile = connector.get_player_profile("DrNykterstein")
    """
    platform_id = platform.value

    # Check cache if requested
    if use_cache and platform_id in _CONNECTOR_CACHE:
        logger.debug(f"Using cached connector for {platform_id}")
        return _CONNECTOR_CACHE[platform_id]

    # Get factory function
    factory = _CONNECTOR_REGISTRY.get(platform_id)
    if factory is None:
        supported = list(_CONNECTOR_REGISTRY.keys())
        raise PlatformNotSupportedError(
            platform=platform_id,
            supported_platforms=supported,
        )

    try:
        connector = factory(**kwargs)
        logger.info(f"Created connector for {platform_id}")

        # Cache if requested
        if use_cache:
            _CONNECTOR_CACHE[platform_id] = connector

        return connector

    except ImportError as e:
        logger.error(f"Failed to import connector for {platform_id}: {e}")
        raise PlatformNotSupportedError(
            platform=platform_id,
            supported_platforms=list(_CONNECTOR_REGISTRY.keys()),
            details={"import_error": str(e)},
        )


def register_connector(
    platform_id: str,
    factory: Callable[..., PlatformConnector],
) -> None:
    """
    Register a new platform connector.

    Use this to add custom platform implementations.

    Args:
        platform_id: Unique platform identifier
        factory: Factory function that creates connector instances

    Examples:
        >>> def create_my_connector(**kwargs):
        ...     return MyCustomConnector(**kwargs)
        >>> register_connector("myplatform", create_my_connector)
    """
    if platform_id in _CONNECTOR_REGISTRY:
        logger.warning(f"Overwriting existing connector for {platform_id}")

    _CONNECTOR_REGISTRY[platform_id] = factory
    logger.info(f"Registered connector for {platform_id}")


def list_platforms() -> List[str]:
    """
    List all registered platform IDs.

    Returns:
        List of platform identifier strings
    """
    return list(_CONNECTOR_REGISTRY.keys())


def get_all_connectors(**kwargs: Any) -> Dict[str, PlatformConnector]:
    """
    Get connectors for all registered platforms.

    Useful for cross-platform operations. Platforms that fail to
    initialize are logged and skipped.

    Args:
        **kwargs: Configuration passed to all connectors

    Returns:
        Dict mapping platform_id to connector instance
    """
    connectors = {}

    for platform_id in _CONNECTOR_REGISTRY:
        try:
            platform = Platform(platform_id)
            connectors[platform_id] = get_connector(platform, **kwargs)
        except Exception as e:
            logger.warning(f"Failed to create connector for {platform_id}: {e}")
            continue

    return connectors


def clear_cache() -> None:
    """Clear the connector cache."""
    _CONNECTOR_CACHE.clear()
    logger.debug("Cleared connector cache")
