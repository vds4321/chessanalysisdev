"""
Normalized data schemas for multi-platform chess analysis.

These dataclasses define the common data structures that all platforms
normalize their data into. Analyzers work exclusively with these schemas,
enabling platform-agnostic analysis.

Design principles:
- All fields have sensible defaults where possible
- Platform-specific data goes in platform_metadata dict
- Immutable after creation (frozen=False for performance, but treat as immutable)
- JSON serializable for caching and API responses
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any

from .constants import (
    Platform,
    GameResult,
    TerminationReason,
    TimeClass,
    GameVariant,
    PlayerColor,
    MoveClassification,
)


@dataclass
class TimeControl:
    """
    Normalized time control representation.

    Stores both the raw values and the classified time class.
    """
    initial_seconds: int
    increment_seconds: int
    time_class: TimeClass
    raw_string: str = ""  # Original platform-specific string (e.g., "300+3")

    @property
    def display_name(self) -> str:
        """Human-readable time control string."""
        minutes = self.initial_seconds // 60
        seconds = self.initial_seconds % 60

        if self.time_class == TimeClass.CORRESPONDENCE:
            days = self.initial_seconds // 86400
            return f"{days} day{'s' if days != 1 else ''}/move"

        if seconds > 0:
            time_str = f"{minutes}:{seconds:02d}"
        else:
            time_str = str(minutes)

        if self.increment_seconds > 0:
            return f"{time_str}+{self.increment_seconds}"
        return f"{time_str} min"

    @property
    def estimated_game_duration(self) -> int:
        """Estimated total game time in seconds (40 moves assumed)."""
        return self.initial_seconds + (self.increment_seconds * 40)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "initial_seconds": self.initial_seconds,
            "increment_seconds": self.increment_seconds,
            "time_class": self.time_class.value,
            "raw_string": self.raw_string,
            "display_name": self.display_name,
        }


@dataclass
class Opening:
    """
    Normalized opening information.

    ECO codes and opening names may vary slightly between platforms,
    but we normalize them where possible.
    """
    name: str
    eco_code: Optional[str] = None
    url: Optional[str] = None  # Link to opening explorer
    moves_in_theory: int = 0  # Number of moves following known theory
    ply_count: int = 0  # Total opening ply count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "eco_code": self.eco_code,
            "url": self.url,
            "moves_in_theory": self.moves_in_theory,
            "ply_count": self.ply_count,
        }


@dataclass
class MoveAnalysis:
    """
    Analysis of a single move.

    Populated by engine analysis (e.g., Stockfish).
    """
    move_number: int
    move_san: str  # Standard Algebraic Notation (e.g., "e4", "Nf3")
    move_uci: str  # UCI format (e.g., "e2e4", "g1f3")
    is_player_move: bool
    fen_before: str  # Position before move
    fen_after: str  # Position after move

    # Engine evaluation (optional - requires engine analysis)
    evaluation_before: Optional[int] = None  # Centipawns from white's perspective
    evaluation_after: Optional[int] = None
    eval_change: Optional[int] = None  # Change in evaluation

    # Best move comparison
    best_move_san: Optional[str] = None
    best_move_uci: Optional[str] = None
    is_best_move: bool = False

    # Classification
    classification: MoveClassification = MoveClassification.UNKNOWN

    # Time information (if available)
    time_spent_ms: Optional[int] = None  # Time spent on this move
    time_remaining_ms: Optional[int] = None  # Clock time after move

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "move_number": self.move_number,
            "move_san": self.move_san,
            "move_uci": self.move_uci,
            "is_player_move": self.is_player_move,
            "fen_before": self.fen_before,
            "fen_after": self.fen_after,
            "evaluation_before": self.evaluation_before,
            "evaluation_after": self.evaluation_after,
            "eval_change": self.eval_change,
            "best_move_san": self.best_move_san,
            "classification": self.classification.value,
            "time_spent_ms": self.time_spent_ms,
            "time_remaining_ms": self.time_remaining_ms,
        }


@dataclass
class PlayerInfo:
    """
    Information about a player in a game.
    """
    username: str
    rating: int
    rating_diff: Optional[int] = None  # Rating change after game (+/- points)
    title: Optional[str] = None  # GM, IM, FM, NM, CM, WGM, etc.
    provisional: bool = False  # Whether rating is provisional

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "username": self.username,
            "rating": self.rating,
            "rating_diff": self.rating_diff,
            "title": self.title,
            "provisional": self.provisional,
        }


@dataclass
class NormalizedGame:
    """
    Normalized game representation that works across all platforms.

    This is the core data structure that all analyzers work with.
    Platform-specific normalizers convert raw API data to this format.
    """
    # Identifiers
    game_id: str
    platform: Platform
    url: str

    # Timing
    played_at: datetime
    time_control: TimeControl

    # Players
    white: PlayerInfo
    black: PlayerInfo
    player_username: str  # The user we're analyzing

    # Result
    result: GameResult
    termination: TerminationReason
    winner: Optional[PlayerColor] = None  # None for draws

    # Opening
    opening: Optional[Opening] = None

    # Game data
    pgn: str = ""
    moves_san: List[str] = field(default_factory=list)  # List of moves in SAN
    variant: GameVariant = GameVariant.STANDARD
    is_rated: bool = True

    # Analysis (populated by analyzers)
    move_analysis: List[MoveAnalysis] = field(default_factory=list)
    accuracy: Optional[float] = None  # 0-100 accuracy score

    # Platform-specific metadata (for features unique to a platform)
    platform_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def player_color(self) -> PlayerColor:
        """Determine which color the analyzed player played."""
        if self.white.username.lower() == self.player_username.lower():
            return PlayerColor.WHITE
        return PlayerColor.BLACK

    @property
    def opponent(self) -> PlayerInfo:
        """Get the opponent's player info."""
        if self.player_color == PlayerColor.WHITE:
            return self.black
        return self.white

    @property
    def player(self) -> PlayerInfo:
        """Get the analyzed player's info."""
        if self.player_color == PlayerColor.WHITE:
            return self.white
        return self.black

    @property
    def opponent_rating(self) -> int:
        """Get opponent's rating."""
        return self.opponent.rating

    @property
    def player_rating(self) -> int:
        """Get player's rating in this game."""
        return self.player.rating

    @property
    def total_moves(self) -> int:
        """Total number of half-moves (ply) in the game."""
        return len(self.moves_san)

    @property
    def full_moves(self) -> int:
        """Number of full moves (White + Black = 1 full move)."""
        return (self.total_moves + 1) // 2

    @property
    def player_moves(self) -> List[MoveAnalysis]:
        """Get only the player's moves from move analysis."""
        return [m for m in self.move_analysis if m.is_player_move]

    @property
    def blunders(self) -> List[MoveAnalysis]:
        """Get all blunders by the player."""
        return [
            m for m in self.player_moves
            if m.classification == MoveClassification.BLUNDER
        ]

    @property
    def mistakes(self) -> List[MoveAnalysis]:
        """Get all mistakes by the player."""
        return [
            m for m in self.player_moves
            if m.classification == MoveClassification.MISTAKE
        ]

    @property
    def inaccuracies(self) -> List[MoveAnalysis]:
        """Get all inaccuracies by the player."""
        return [
            m for m in self.player_moves
            if m.classification == MoveClassification.INACCURACY
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "game_id": self.game_id,
            "platform": self.platform.value,
            "url": self.url,
            "played_at": self.played_at.isoformat(),
            "time_control": self.time_control.to_dict(),
            "white": self.white.to_dict(),
            "black": self.black.to_dict(),
            "player_username": self.player_username,
            "player_color": self.player_color.value,
            "result": self.result.value,
            "termination": self.termination.value,
            "winner": self.winner.value if self.winner else None,
            "opening": self.opening.to_dict() if self.opening else None,
            "variant": self.variant.value,
            "is_rated": self.is_rated,
            "total_moves": self.total_moves,
            "accuracy": self.accuracy,
            "platform_metadata": self.platform_metadata,
        }


@dataclass
class PlayerProfile:
    """
    Normalized player profile information.
    """
    username: str
    platform: Platform
    url: str
    joined_at: Optional[datetime] = None
    last_online: Optional[datetime] = None
    country: Optional[str] = None
    title: Optional[str] = None
    is_streamer: bool = False
    verified: bool = False

    # Ratings by time control
    ratings: Dict[TimeClass, int] = field(default_factory=dict)

    # Statistics
    total_games: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0

    # Platform-specific data
    platform_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def win_rate(self) -> float:
        """Calculate overall win rate."""
        if self.total_games == 0:
            return 0.0
        return (self.wins / self.total_games) * 100

    @property
    def draw_rate(self) -> float:
        """Calculate draw rate."""
        if self.total_games == 0:
            return 0.0
        return (self.draws / self.total_games) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "username": self.username,
            "platform": self.platform.value,
            "url": self.url,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "country": self.country,
            "title": self.title,
            "ratings": {k.value: v for k, v in self.ratings.items()},
            "total_games": self.total_games,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "win_rate": self.win_rate,
        }


@dataclass
class GameFilter:
    """
    Filter criteria for fetching and filtering games.
    """
    # Time range
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Time controls
    time_classes: Optional[List[TimeClass]] = None

    # Variants
    variants: Optional[List[GameVariant]] = None

    # Rating
    rated_only: bool = False
    min_opponent_rating: Optional[int] = None
    max_opponent_rating: Optional[int] = None

    # Result
    result_filter: Optional[List[GameResult]] = None

    # Color
    color_filter: Optional[PlayerColor] = None

    # Quantity
    max_games: Optional[int] = None

    # Platform-specific filters
    platform_filters: Dict[str, Any] = field(default_factory=dict)

    def matches(self, game: NormalizedGame) -> bool:
        """Check if a game matches all filter criteria."""
        # Date range
        if self.start_date and game.played_at < self.start_date:
            return False
        if self.end_date and game.played_at > self.end_date:
            return False

        # Time class
        if self.time_classes and game.time_control.time_class not in self.time_classes:
            return False

        # Variant
        if self.variants and game.variant not in self.variants:
            return False

        # Rated
        if self.rated_only and not game.is_rated:
            return False

        # Opponent rating
        if self.min_opponent_rating and game.opponent_rating < self.min_opponent_rating:
            return False
        if self.max_opponent_rating and game.opponent_rating > self.max_opponent_rating:
            return False

        # Result
        if self.result_filter and game.result not in self.result_filter:
            return False

        # Color
        if self.color_filter and game.player_color != self.color_filter:
            return False

        return True


@dataclass
class AnalysisResult:
    """
    Container for analysis results from any analyzer.

    Provides consistent structure for all analysis outputs.
    """
    analyzer_id: str  # e.g., "tactical", "opening", "progression"
    timestamp: datetime = field(default_factory=datetime.now)
    games_analyzed: int = 0
    platform: Optional[Platform] = None  # None for cross-platform analysis

    # Core results (structure depends on analyzer)
    results: Dict[str, Any] = field(default_factory=dict)

    # Summary statistics
    summary: Dict[str, Any] = field(default_factory=dict)

    # Recommendations
    recommendations: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "analyzer_id": self.analyzer_id,
            "timestamp": self.timestamp.isoformat(),
            "games_analyzed": self.games_analyzed,
            "platform": self.platform.value if self.platform else None,
            "results": self.results,
            "summary": self.summary,
            "recommendations": self.recommendations,
            "metadata": self.metadata,
        }


@dataclass
class ReportConfig:
    """
    Configuration for report generation.
    """
    report_type: str  # "personal", "scouting", "comparative"
    username: str
    platforms: List[Platform]

    # Time range
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Filters
    game_filter: Optional[GameFilter] = None

    # LLM options
    include_llm_insights: bool = True
    llm_provider: Optional[str] = None  # "anthropic", "openai", etc.
    llm_model: Optional[str] = None  # "sonnet", "gpt-4o", etc.

    # Scouting-specific
    opponent_username: Optional[str] = None
    opponent_platforms: Optional[List[Platform]] = None

    # Output options
    output_format: str = "markdown"  # "markdown", "pdf", "html"
    include_visualizations: bool = True
    include_pgn_samples: bool = True

    # Report sections to include
    sections: Optional[List[str]] = None  # None = all sections

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "report_type": self.report_type,
            "username": self.username,
            "platforms": [p.value for p in self.platforms],
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "include_llm_insights": self.include_llm_insights,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "opponent_username": self.opponent_username,
            "output_format": self.output_format,
        }
