"""
Core module containing shared abstractions for multi-platform chess analysis.

This module provides:
- Normalized data schemas (NormalizedGame, PlayerProfile, etc.)
- Protocol definitions for platform connectors, analyzers, and LLM providers
- Common enums and constants (TimeClass, GameVariant, Platform, etc.)
- Custom exceptions

All platform-specific code normalizes data to these schemas before analysis.
"""

from .constants import (
    Platform,
    GameResult,
    TerminationReason,
    TimeClass,
    GameVariant,
    PlayerColor,
)
from .schemas import (
    TimeControl,
    Opening,
    MoveAnalysis,
    PlayerInfo,
    NormalizedGame,
    PlayerProfile,
    GameFilter,
    AnalysisResult,
    ReportConfig,
)
from .exceptions import (
    ChessAnalysisError,
    PlatformError,
    APIError,
    RateLimitError,
    AuthenticationError,
    NormalizationError,
    AnalysisError,
    LLMError,
)

__all__ = [
    # Constants/Enums
    "Platform",
    "GameResult",
    "TerminationReason",
    "TimeClass",
    "GameVariant",
    "PlayerColor",
    # Schemas
    "TimeControl",
    "Opening",
    "MoveAnalysis",
    "PlayerInfo",
    "NormalizedGame",
    "PlayerProfile",
    "GameFilter",
    "AnalysisResult",
    "ReportConfig",
    # Exceptions
    "ChessAnalysisError",
    "PlatformError",
    "APIError",
    "RateLimitError",
    "AuthenticationError",
    "NormalizationError",
    "AnalysisError",
    "LLMError",
]
