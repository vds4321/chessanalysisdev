"""
Lichess specific game type definitions.

Isolates all Lichess-specific game type parsing and mapping so that
changes to Lichess's format don't impact other platforms.

This module handles:
- Time control parsing and classification
- Game variant detection
- Termination reason mapping
- Result parsing
- Lichess-specific features (berserk, tournaments, etc.)
"""

from typing import Dict, Tuple, Optional, Set, Any

from src.core.constants import (
    TimeClass,
    GameVariant,
    TerminationReason,
    GameResult,
    PlayerColor,
)


# =============================================================================
# Time Control Parsing
# =============================================================================

# Lichess "speed" field mapping
LICHESS_SPEED_MAP: Dict[str, TimeClass] = {
    "ultraBullet": TimeClass.ULTRA_BULLET,
    "bullet": TimeClass.BULLET,
    "blitz": TimeClass.BLITZ,
    "rapid": TimeClass.RAPID,
    "classical": TimeClass.CLASSICAL,
    "correspondence": TimeClass.CORRESPONDENCE,
}


def parse_time_control(clock_data: Optional[Dict]) -> Tuple[int, int, TimeClass]:
    """
    Parse Lichess clock data to normalized format.

    Lichess format:
    {
        "initial": 300,      # Initial time in seconds
        "increment": 3,      # Increment in seconds
        "totalTime": 420     # Estimated total time
    }

    For correspondence games, clock may be absent or different.

    Args:
        clock_data: Clock dict from Lichess API

    Returns:
        Tuple of (initial_seconds, increment_seconds, time_class)
    """
    if not clock_data:
        return 0, 0, TimeClass.UNKNOWN

    initial = clock_data.get("initial", 0)
    increment = clock_data.get("increment", 0)

    # Use Lichess's totalTime for classification if available
    total_time = clock_data.get("totalTime")
    if total_time is None:
        total_time = initial + (increment * 40)

    time_class = TimeClass.from_seconds(initial, increment)

    return initial, increment, time_class


def map_speed_to_time_class(speed: str) -> TimeClass:
    """
    Map Lichess speed string to TimeClass.

    Args:
        speed: Lichess speed string (e.g., "blitz", "rapid")

    Returns:
        Corresponding TimeClass
    """
    return LICHESS_SPEED_MAP.get(speed, TimeClass.UNKNOWN)


# =============================================================================
# Variant Detection
# =============================================================================

# Lichess variant field mapping (Lichess uses camelCase)
LICHESS_VARIANT_MAP: Dict[str, GameVariant] = {
    "standard": GameVariant.STANDARD,
    "chess960": GameVariant.CHESS960,
    "crazyhouse": GameVariant.CRAZYHOUSE,
    "kingOfTheHill": GameVariant.KING_OF_THE_HILL,
    "threeCheck": GameVariant.THREE_CHECK,
    "antichess": GameVariant.ANTICHESS,
    "atomic": GameVariant.ATOMIC,
    "horde": GameVariant.HORDE,
    "racingKings": GameVariant.RACING_KINGS,
    "fromPosition": GameVariant.FROM_POSITION,
}

# Lowercase versions for case-insensitive matching
LICHESS_VARIANT_MAP_LOWER: Dict[str, GameVariant] = {
    k.lower(): v for k, v in LICHESS_VARIANT_MAP.items()
}


def detect_variant(variant_str: str) -> GameVariant:
    """
    Detect game variant from Lichess variant string.

    Args:
        variant_str: Lichess variant field value

    Returns:
        Corresponding GameVariant
    """
    if not variant_str:
        return GameVariant.STANDARD

    # Try exact match first
    if variant_str in LICHESS_VARIANT_MAP:
        return LICHESS_VARIANT_MAP[variant_str]

    # Try case-insensitive
    return LICHESS_VARIANT_MAP_LOWER.get(
        variant_str.lower(),
        GameVariant.OTHER
    )


# =============================================================================
# Termination Reason Mapping
# =============================================================================

# Lichess status field mapping
LICHESS_STATUS_MAP: Dict[str, TerminationReason] = {
    # Decisive
    "mate": TerminationReason.CHECKMATE,
    "resign": TerminationReason.RESIGNATION,
    "outoftime": TerminationReason.TIMEOUT,
    "timeout": TerminationReason.TIMEOUT,

    # Draws
    "stalemate": TerminationReason.STALEMATE,
    "draw": TerminationReason.AGREEMENT,
    "repetition": TerminationReason.THREEFOLD_REPETITION,  # Lichess uses this
    "insufficientMaterial": TerminationReason.INSUFFICIENT_MATERIAL,
    "fiftyMoves": TerminationReason.FIFTY_MOVES,  # Lichess uses camelCase

    # Special cases
    "noStart": TerminationReason.ABANDONMENT,
    "aborted": TerminationReason.ABANDONMENT,
    "cheat": TerminationReason.OTHER,
    "variantEnd": TerminationReason.OTHER,  # Variant-specific win condition
    "unknownFinish": TerminationReason.UNKNOWN,
}


def parse_status(status: str) -> TerminationReason:
    """
    Parse Lichess status to normalized termination reason.

    Args:
        status: Lichess status field value

    Returns:
        Corresponding TerminationReason
    """
    return LICHESS_STATUS_MAP.get(status, TerminationReason.UNKNOWN)


def parse_game_result(
    game_data: Dict[str, Any],
    player_username: str,
) -> Tuple[GameResult, TerminationReason, Optional[PlayerColor]]:
    """
    Parse Lichess game data to determine result, termination, and winner.

    Lichess format:
    - "winner": "white" or "black" (absent for draws)
    - "status": "mate", "resign", "stalemate", etc.
    - "players": {"white": {...}, "black": {...}}

    Args:
        game_data: Raw game data from Lichess
        player_username: Username of the player we're analyzing

    Returns:
        Tuple of (GameResult, TerminationReason, winner_color or None)
    """
    # Determine winner
    winner_str = game_data.get("winner")
    winner: Optional[PlayerColor] = None

    if winner_str == "white":
        winner = PlayerColor.WHITE
    elif winner_str == "black":
        winner = PlayerColor.BLACK
    # If winner is absent, it's a draw

    # Determine termination
    status = game_data.get("status", "")
    termination = parse_status(status)

    # Determine player color
    players = game_data.get("players", {})
    white_user = players.get("white", {}).get("user", {})
    black_user = players.get("black", {}).get("user", {})

    player_lower = player_username.lower()
    white_name = white_user.get("name", "").lower() if white_user else ""
    black_name = black_user.get("name", "").lower() if black_user else ""

    if white_name == player_lower:
        player_color = PlayerColor.WHITE
    elif black_name == player_lower:
        player_color = PlayerColor.BLACK
    else:
        # Player not found, assume white (shouldn't happen in normal use)
        player_color = PlayerColor.WHITE

    # Determine result from player's perspective
    if winner is None:
        result = GameResult.DRAW
    elif winner == player_color:
        result = GameResult.WIN
    else:
        result = GameResult.LOSS

    return result, termination, winner


# =============================================================================
# Game Source/Mode Detection
# =============================================================================

# Lichess game sources
LICHESS_GAME_SOURCES: Set[str] = {
    "lobby",       # Random pairing from lobby
    "friend",      # Friend challenge
    "ai",          # vs Stockfish
    "pool",        # Arena/Swiss pool
    "tournament",  # Tournament game
    "swiss",       # Swiss tournament
    "simul",       # Simultaneous exhibition
    "import",      # Imported game
    "api",         # API challenge
}


def get_game_source(game_data: Dict) -> str:
    """Get the source/origin of a Lichess game."""
    return game_data.get("source", "unknown")


def is_rated_game(game_data: Dict) -> bool:
    """Check if game was rated."""
    return game_data.get("rated", False)


def is_tournament_game(game_data: Dict) -> bool:
    """Check if game was part of a tournament."""
    return game_data.get("tournament") is not None


def is_swiss_game(game_data: Dict) -> bool:
    """Check if game was part of a Swiss tournament."""
    return game_data.get("swiss") is not None


def is_friend_game(game_data: Dict) -> bool:
    """Check if game was a friend challenge."""
    return game_data.get("source") == "friend"


def is_ai_game(game_data: Dict) -> bool:
    """Check if game was against Stockfish AI."""
    return game_data.get("source") == "ai"


# =============================================================================
# Lichess-Specific Features
# =============================================================================


def player_berserked(game_data: Dict, color: str) -> bool:
    """
    Check if player berserked in a tournament game.

    Berserk halves your clock time but gives extra tournament points
    if you win.

    Args:
        game_data: Raw game data
        color: "white" or "black"

    Returns:
        True if player berserked
    """
    players = game_data.get("players", {})
    player_data = players.get(color, {})
    return player_data.get("berserk", False)


def get_player_rating(game_data: Dict, color: str) -> int:
    """
    Get player's rating from game data.

    Args:
        game_data: Raw game data
        color: "white" or "black"

    Returns:
        Player's rating, or 0 if not found
    """
    players = game_data.get("players", {})
    player_data = players.get(color, {})
    return player_data.get("rating", 0)


def get_rating_diff(game_data: Dict, color: str) -> Optional[int]:
    """
    Get rating change after game.

    Args:
        game_data: Raw game data
        color: "white" or "black"

    Returns:
        Rating change (+/-), or None if not available
    """
    players = game_data.get("players", {})
    player_data = players.get(color, {})
    return player_data.get("ratingDiff")


def is_provisional_rating(game_data: Dict, color: str) -> bool:
    """
    Check if player's rating is provisional.

    Args:
        game_data: Raw game data
        color: "white" or "black"

    Returns:
        True if rating is provisional
    """
    players = game_data.get("players", {})
    player_data = players.get(color, {})
    return player_data.get("provisional", False)


def get_player_title(game_data: Dict, color: str) -> Optional[str]:
    """
    Get player's title (GM, IM, etc.) from game data.

    Args:
        game_data: Raw game data
        color: "white" or "black"

    Returns:
        Title string or None
    """
    players = game_data.get("players", {})
    player_data = players.get(color, {})
    user_data = player_data.get("user", {})
    return user_data.get("title")


# =============================================================================
# Opening Extraction
# =============================================================================


def extract_opening(game_data: Dict) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract opening information from Lichess game data.

    Lichess format:
    {
        "opening": {
            "eco": "B20",
            "name": "Sicilian Defense",
            "ply": 4
        }
    }

    Args:
        game_data: Raw game data

    Returns:
        Tuple of (opening_name, eco_code)
    """
    opening = game_data.get("opening", {})
    if not opening:
        return None, None

    name = opening.get("name")
    eco = opening.get("eco")

    return name, eco


def get_opening_ply(game_data: Dict) -> int:
    """
    Get the number of ply in the opening phase.

    Args:
        game_data: Raw game data

    Returns:
        Opening ply count, or 0 if not available
    """
    opening = game_data.get("opening", {})
    return opening.get("ply", 0)
