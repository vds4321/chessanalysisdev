"""
Core constants and enumerations for multi-platform chess analysis.

These enums provide a normalized vocabulary that works across all platforms.
Platform-specific values are mapped to these enums in each platform's
game_types.py module.
"""

from enum import Enum, auto


class Platform(str, Enum):
    """
    Supported chess platforms.

    Using str mixin allows direct string comparison and JSON serialization.
    """
    CHESS_COM = "chesscom"
    LICHESS = "lichess"

    @classmethod
    def from_string(cls, value: str) -> "Platform":
        """Convert string to Platform enum, case-insensitive."""
        value_lower = value.lower().replace(".", "").replace("-", "").replace(" ", "")
        mapping = {
            "chesscom": cls.CHESS_COM,
            "chess": cls.CHESS_COM,
            "lichess": cls.LICHESS,
        }
        if value_lower in mapping:
            return mapping[value_lower]
        raise ValueError(f"Unknown platform: {value}")


class GameResult(str, Enum):
    """
    Normalized game results from the player's perspective.
    """
    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"

    @property
    def score(self) -> float:
        """Return numeric score: 1.0 for win, 0.5 for draw, 0.0 for loss."""
        if self == GameResult.WIN:
            return 1.0
        elif self == GameResult.DRAW:
            return 0.5
        return 0.0


class TerminationReason(str, Enum):
    """
    Normalized reasons for game termination.

    Covers all common termination types across platforms.
    """
    # Decisive endings
    CHECKMATE = "checkmate"
    RESIGNATION = "resignation"
    TIMEOUT = "timeout"
    ABANDONMENT = "abandonment"

    # Draws
    STALEMATE = "stalemate"
    INSUFFICIENT_MATERIAL = "insufficient_material"
    THREEFOLD_REPETITION = "repetition"
    FIFTY_MOVES = "fifty_moves"
    AGREEMENT = "agreement"

    # Timeout special cases
    TIMEOUT_VS_INSUFFICIENT = "timeout_vs_insufficient"

    # Other
    UNKNOWN = "unknown"
    OTHER = "other"

    @property
    def is_decisive(self) -> bool:
        """Return True if this termination typically produces a winner."""
        decisive = {
            TerminationReason.CHECKMATE,
            TerminationReason.RESIGNATION,
            TerminationReason.TIMEOUT,
            TerminationReason.ABANDONMENT,
        }
        return self in decisive

    @property
    def is_draw(self) -> bool:
        """Return True if this termination typically produces a draw."""
        draws = {
            TerminationReason.STALEMATE,
            TerminationReason.INSUFFICIENT_MATERIAL,
            TerminationReason.THREEFOLD_REPETITION,
            TerminationReason.FIFTY_MOVES,
            TerminationReason.AGREEMENT,
            TerminationReason.TIMEOUT_VS_INSUFFICIENT,
        }
        return self in draws


class TimeClass(str, Enum):
    """
    Normalized time control categories.

    Classification follows common conventions:
    - UltraBullet: < 30 seconds total
    - Bullet: < 3 minutes total
    - Blitz: 3-10 minutes total
    - Rapid: 10-30 minutes total
    - Classical: > 30 minutes total
    - Correspondence: Days per move
    """
    ULTRA_BULLET = "ultrabullet"
    BULLET = "bullet"
    BLITZ = "blitz"
    RAPID = "rapid"
    CLASSICAL = "classical"
    CORRESPONDENCE = "correspondence"
    UNKNOWN = "unknown"

    @classmethod
    def from_seconds(cls, initial_seconds: int, increment_seconds: int = 0) -> "TimeClass":
        """
        Classify time control based on initial time and increment.

        Uses estimated game time: initial + (increment * 40 moves)
        """
        if initial_seconds == 0 and increment_seconds == 0:
            return cls.UNKNOWN

        # Correspondence games have very long time controls (days)
        if initial_seconds >= 86400:  # 1 day
            return cls.CORRESPONDENCE

        # Estimate total game time (40 move estimate)
        estimated_total = initial_seconds + (increment_seconds * 40)

        if estimated_total < 30:
            return cls.ULTRA_BULLET
        elif estimated_total < 180:  # 3 minutes
            return cls.BULLET
        elif estimated_total < 600:  # 10 minutes
            return cls.BLITZ
        elif estimated_total < 1800:  # 30 minutes
            return cls.RAPID
        else:
            return cls.CLASSICAL

    @property
    def display_name(self) -> str:
        """Return human-readable name."""
        names = {
            TimeClass.ULTRA_BULLET: "UltraBullet",
            TimeClass.BULLET: "Bullet",
            TimeClass.BLITZ: "Blitz",
            TimeClass.RAPID: "Rapid",
            TimeClass.CLASSICAL: "Classical",
            TimeClass.CORRESPONDENCE: "Correspondence",
            TimeClass.UNKNOWN: "Unknown",
        }
        return names.get(self, self.value.title())


class GameVariant(str, Enum):
    """
    Normalized chess variants.

    Covers variants available on both Chess.com and Lichess.
    """
    # Standard chess
    STANDARD = "standard"

    # Fischer Random / Chess960
    CHESS960 = "chess960"

    # Piece placement variants
    CRAZYHOUSE = "crazyhouse"

    # Alternative win conditions
    KING_OF_THE_HILL = "kingofthehill"
    THREE_CHECK = "threecheck"
    RACING_KINGS = "racingkings"

    # Alternative rules
    ANTICHESS = "antichess"
    ATOMIC = "atomic"
    HORDE = "horde"

    # From custom position (but standard rules)
    FROM_POSITION = "fromposition"

    # Other/unknown
    OTHER = "other"

    @property
    def uses_standard_openings(self) -> bool:
        """Return True if standard opening theory applies."""
        standard_opening_variants = {
            GameVariant.STANDARD,
            GameVariant.THREE_CHECK,
            GameVariant.KING_OF_THE_HILL,
        }
        return self in standard_opening_variants

    @property
    def display_name(self) -> str:
        """Return human-readable name."""
        names = {
            GameVariant.STANDARD: "Standard",
            GameVariant.CHESS960: "Chess960",
            GameVariant.CRAZYHOUSE: "Crazyhouse",
            GameVariant.KING_OF_THE_HILL: "King of the Hill",
            GameVariant.THREE_CHECK: "Three-Check",
            GameVariant.RACING_KINGS: "Racing Kings",
            GameVariant.ANTICHESS: "Antichess",
            GameVariant.ATOMIC: "Atomic",
            GameVariant.HORDE: "Horde",
            GameVariant.FROM_POSITION: "From Position",
            GameVariant.OTHER: "Other",
        }
        return names.get(self, self.value.title())


class PlayerColor(str, Enum):
    """Player's piece color."""
    WHITE = "white"
    BLACK = "black"

    @property
    def opponent(self) -> "PlayerColor":
        """Return the opposite color."""
        return PlayerColor.BLACK if self == PlayerColor.WHITE else PlayerColor.WHITE


class MoveClassification(str, Enum):
    """
    Classification of move quality based on engine evaluation.

    Thresholds are configurable but these are the standard categories.
    """
    BRILLIANT = "brilliant"      # Exceptional move, often a sacrifice
    GREAT = "great"              # Top engine choice, significant advantage
    BEST = "best"                # Engine's top choice
    EXCELLENT = "excellent"      # Very strong move
    GOOD = "good"                # Solid move, minimal eval loss
    BOOK = "book"                # Opening theory move
    INACCURACY = "inaccuracy"    # Slight mistake (50-100 cp loss)
    MISTAKE = "mistake"          # Moderate error (100-200 cp loss)
    BLUNDER = "blunder"          # Serious error (200+ cp loss)
    MISSED_WIN = "missed_win"    # Failed to find winning move
    UNKNOWN = "unknown"          # Not evaluated

    @property
    def is_error(self) -> bool:
        """Return True if this is a negative classification."""
        errors = {
            MoveClassification.INACCURACY,
            MoveClassification.MISTAKE,
            MoveClassification.BLUNDER,
            MoveClassification.MISSED_WIN,
        }
        return self in errors


# Default thresholds for move classification (in centipawns)
DEFAULT_THRESHOLDS = {
    "blunder": 200,      # >= 200 cp loss
    "mistake": 100,      # >= 100 cp loss
    "inaccuracy": 50,    # >= 50 cp loss
    "good": 25,          # < 25 cp loss considered "good"
}
