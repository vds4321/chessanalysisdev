"""
Protocol definitions for multi-platform chess analysis.

Protocols define the interfaces that all implementations must follow.
Using Protocol (PEP 544) enables structural subtyping - classes don't
need to explicitly inherit, they just need to implement the methods.

This module defines protocols for:
- Platform connectors (Chess.com, Lichess, etc.)
- Game normalizers
- Analyzers
- Report generators
- LLM providers
- Image generators
"""

from abc import abstractmethod
from typing import (
    Protocol,
    List,
    Dict,
    Optional,
    Iterator,
    Any,
    runtime_checkable,
)
from datetime import datetime

from .schemas import (
    NormalizedGame,
    PlayerProfile,
    GameFilter,
    AnalysisResult,
    ReportConfig,
)
from .constants import Platform


@runtime_checkable
class PlatformConnector(Protocol):
    """
    Protocol for platform API connectors.

    Each chess platform (Chess.com, Lichess, etc.) implements this protocol
    to provide a consistent interface for fetching game data.

    Implementations should handle:
    - Rate limiting
    - Caching
    - Error handling / retries
    - Data normalization (via GameNormalizer)
    """

    @property
    def platform_id(self) -> str:
        """Unique identifier for the platform (e.g., 'chesscom', 'lichess')."""
        ...

    @property
    def platform_name(self) -> str:
        """Human-readable platform name (e.g., 'Chess.com', 'Lichess')."""
        ...

    @property
    def platform(self) -> Platform:
        """Platform enum value."""
        ...

    def validate_username(self, username: str) -> bool:
        """
        Check if a username exists on this platform.

        Args:
            username: The username to validate

        Returns:
            True if username exists, False otherwise
        """
        ...

    def get_player_profile(self, username: str) -> Optional[PlayerProfile]:
        """
        Fetch player profile information.

        Args:
            username: The player's username

        Returns:
            PlayerProfile if found, None otherwise
        """
        ...

    def get_games(
        self,
        username: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        game_filter: Optional[GameFilter] = None,
    ) -> Iterator[NormalizedGame]:
        """
        Fetch games as normalized data.

        Yields NormalizedGame objects for memory efficiency with large
        game histories. Games are typically yielded newest-first.

        Args:
            username: The player's username
            start_date: Optional start of date range
            end_date: Optional end of date range
            game_filter: Optional additional filters

        Yields:
            NormalizedGame objects
        """
        ...

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
        ...

    def get_current_games(self, username: str) -> List[Dict[str, Any]]:
        """
        Get currently active games (for anti-scouting features).

        Returns raw game data as some platforms have different
        formats for ongoing vs completed games.

        Args:
            username: The player's username

        Returns:
            List of active game data dicts
        """
        ...

    def get_player_stats(self, username: str) -> Dict[str, Any]:
        """
        Get player statistics from the platform.

        Returns platform-specific stats that may not be normalized.

        Args:
            username: The player's username

        Returns:
            Dict of platform-specific statistics
        """
        ...


@runtime_checkable
class GameNormalizer(Protocol):
    """
    Protocol for converting platform-specific data to normalized format.

    Each platform has its own normalizer that handles the specific
    data formats and field mappings for that platform.
    """

    @property
    def platform(self) -> Platform:
        """Platform this normalizer handles."""
        ...

    def normalize_game(
        self,
        raw_game: Dict[str, Any],
        player_username: str,
    ) -> NormalizedGame:
        """
        Convert platform-specific game data to normalized format.

        Args:
            raw_game: Raw game data from the platform API
            player_username: The username of the player we're analyzing

        Returns:
            NormalizedGame instance

        Raises:
            NormalizationError: If game data cannot be normalized
        """
        ...

    def normalize_profile(
        self,
        raw_profile: Dict[str, Any],
        raw_stats: Optional[Dict[str, Any]] = None,
    ) -> PlayerProfile:
        """
        Convert platform-specific profile to normalized format.

        Args:
            raw_profile: Raw profile data from the platform API
            raw_stats: Optional additional stats data

        Returns:
            PlayerProfile instance
        """
        ...


@runtime_checkable
class Analyzer(Protocol):
    """
    Protocol for game analyzers.

    Analyzers take normalized game data and produce analysis results.
    They are platform-agnostic and work with NormalizedGame objects.
    """

    @property
    def analyzer_id(self) -> str:
        """Unique identifier for this analyzer (e.g., 'tactical', 'opening')."""
        ...

    @property
    def analyzer_name(self) -> str:
        """Human-readable name for this analyzer."""
        ...

    def analyze(
        self,
        games: List[NormalizedGame],
        **kwargs: Any,
    ) -> AnalysisResult:
        """
        Perform analysis on normalized game data.

        Args:
            games: List of normalized games to analyze
            **kwargs: Analyzer-specific options

        Returns:
            AnalysisResult containing analysis data and recommendations
        """
        ...

    def get_recommendations(
        self,
        analysis_result: AnalysisResult,
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on analysis.

        Args:
            analysis_result: Result from analyze()

        Returns:
            List of recommendation dicts with priority, type, title, description
        """
        ...


@runtime_checkable
class ReportGenerator(Protocol):
    """
    Protocol for report generators.

    Report generators take analysis results and produce formatted reports
    (Markdown, HTML, PDF, etc.).
    """

    @property
    def report_type(self) -> str:
        """Type of report this generator produces (e.g., 'personal', 'scouting')."""
        ...

    def generate(
        self,
        analysis_results: Dict[str, AnalysisResult],
        config: ReportConfig,
    ) -> str:
        """
        Generate a report from analysis results.

        Args:
            analysis_results: Dict mapping analyzer_id to AnalysisResult
            config: Report configuration options

        Returns:
            Formatted report content (Markdown by default)
        """
        ...

    def supports_platform(self, platform_id: str) -> bool:
        """
        Check if this report generator supports a given platform.

        Args:
            platform_id: Platform identifier to check

        Returns:
            True if platform is supported
        """
        ...


@runtime_checkable
class LLMProvider(Protocol):
    """
    Protocol for LLM (Large Language Model) providers.

    Enables using multiple LLM backends (Claude, GPT, DeepSeek, etc.)
    with a consistent interface for chess coaching insights.
    """

    @property
    def provider_id(self) -> str:
        """Provider identifier (e.g., 'anthropic', 'openai')."""
        ...

    @property
    def model_id(self) -> str:
        """Current model identifier."""
        ...

    @property
    def supports_vision(self) -> bool:
        """Whether this model supports image input."""
        ...

    @property
    def max_tokens(self) -> int:
        """Maximum tokens this model supports."""
        ...

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """
        Generate a text completion.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            **kwargs: Provider-specific options

        Returns:
            Generated text response
        """
        ...

    def complete_with_images(
        self,
        prompt: str,
        images: List[bytes],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> str:
        """
        Generate completion with image context.

        Args:
            prompt: The user prompt
            images: List of image data as bytes
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response
            **kwargs: Provider-specific options

        Returns:
            Generated text response

        Raises:
            NotImplementedError: If model doesn't support vision
        """
        ...


@runtime_checkable
class ImageGenerator(Protocol):
    """
    Protocol for image generation providers.

    Used for generating chess board diagrams, report illustrations, etc.
    """

    @property
    def provider_id(self) -> str:
        """Provider identifier (e.g., 'dalle', 'flux')."""
        ...

    @property
    def supported_sizes(self) -> List[tuple[int, int]]:
        """List of supported image sizes (width, height)."""
        ...

    def generate(
        self,
        prompt: str,
        size: tuple[int, int] = (1024, 1024),
        **kwargs: Any,
    ) -> bytes:
        """
        Generate an image from a prompt.

        Args:
            prompt: Text description of desired image
            size: Image dimensions (width, height)
            **kwargs: Provider-specific options

        Returns:
            Image data as bytes (PNG format)
        """
        ...


class ChessCoach(Protocol):
    """
    Protocol for unified chess coaching interface.

    Combines LLM capabilities with chess-specific prompting
    for consistent coaching insights across different models.
    """

    @property
    def llm_provider(self) -> LLMProvider:
        """The underlying LLM provider."""
        ...

    def analyze_game(
        self,
        game: NormalizedGame,
        analysis: Optional[AnalysisResult] = None,
    ) -> str:
        """
        Generate coaching insights for a single game.

        Args:
            game: The game to analyze
            analysis: Optional pre-computed analysis

        Returns:
            Coaching insights as text
        """
        ...

    def analyze_opening_performance(
        self,
        opening_stats: Dict[str, Any],
    ) -> str:
        """
        Generate insights about opening performance.

        Args:
            opening_stats: Opening statistics from analyzer

        Returns:
            Opening coaching insights
        """
        ...

    def analyze_tactical_patterns(
        self,
        tactical_data: Dict[str, Any],
    ) -> str:
        """
        Generate insights about tactical patterns.

        Args:
            tactical_data: Tactical analysis data

        Returns:
            Tactical coaching insights
        """
        ...

    def generate_improvement_plan(
        self,
        analysis_results: Dict[str, AnalysisResult],
        config: Optional[ReportConfig] = None,
    ) -> str:
        """
        Generate a comprehensive improvement plan.

        Args:
            analysis_results: Results from multiple analyzers
            config: Optional report configuration

        Returns:
            Improvement plan as text
        """
        ...

    def explain_position(
        self,
        fen: str,
        context: Optional[str] = None,
    ) -> str:
        """
        Explain a chess position.

        Args:
            fen: FEN string of the position
            context: Optional context (e.g., what happened in the game)

        Returns:
            Position explanation
        """
        ...

    def explain_blunder(
        self,
        move_analysis: Dict[str, Any],
        pgn: Optional[str] = None,
    ) -> str:
        """
        Explain why a move was a blunder.

        Args:
            move_analysis: Analysis data for the blunder move
            pgn: Optional full game PGN for context

        Returns:
            Blunder explanation
        """
        ...
