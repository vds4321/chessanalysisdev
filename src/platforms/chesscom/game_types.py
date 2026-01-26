"""
Chess.com specific game type definitions.

Isolates all Chess.com-specific game type parsing and mapping so that
changes to Chess.com's format don't impact other platforms.

This module handles:
- Time control parsing and classification
- Game variant detection
- Termination reason mapping
- Result parsing
"""

from typing import Dict, Tuple, Optional, Set
import re

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

def parse_time_control(time_control_str: str) -> Tuple[int, int, TimeClass]:
    """
    Parse Chess.com time control string to normalized format.

    Chess.com formats:
    - "180" (3 minutes, no increment)
    - "180+2" (3 minutes + 2 second increment)
    - "300" (5 minutes)
    - "600+5" (10 minutes + 5 second increment)
    - "1/86400" (1 day per move - correspondence)
    - "1/259200" (3 days per move - correspondence)
    - "-" (no time control / untimed)

    Args:
        time_control_str: Raw time control string from Chess.com

    Returns:
        Tuple of (initial_seconds, increment_seconds, time_class)
    """
    if not time_control_str or time_control_str == "-":
        return 0, 0, TimeClass.UNKNOWN

    # Correspondence format: "1/86400" means 1 move per 86400 seconds (1 day)
    if "/" in time_control_str:
        try:
            parts = time_control_str.split("/")
            seconds_per_move = int(parts[1])
            return seconds_per_move, 0, TimeClass.CORRESPONDENCE
        except (ValueError, IndexError):
            return 0, 0, TimeClass.UNKNOWN

    # Standard format: "initial" or "initial+increment"
    try:
        if "+" in time_control_str:
            parts = time_control_str.split("+")
            initial = int(parts[0])
            increment = int(parts[1])
        else:
            initial = int(time_control_str)
            increment = 0

        time_class = TimeClass.from_seconds(initial, increment)
        return initial, increment, time_class

    except ValueError:
        return 0, 0, TimeClass.UNKNOWN


# Chess.com time_class field mapping (when API provides it directly)
CHESSCOM_TIME_CLASS_MAP: Dict[str, TimeClass] = {
    "bullet": TimeClass.BULLET,
    "blitz": TimeClass.BLITZ,
    "rapid": TimeClass.RAPID,
    "daily": TimeClass.CORRESPONDENCE,
    "classical": TimeClass.CLASSICAL,
}


def map_time_class(chesscom_time_class: str) -> TimeClass:
    """Map Chess.com time_class string to normalized TimeClass."""
    return CHESSCOM_TIME_CLASS_MAP.get(
        chesscom_time_class.lower(),
        TimeClass.UNKNOWN
    )


# =============================================================================
# Variant Detection
# =============================================================================

# Chess.com variant field mapping
CHESSCOM_VARIANT_MAP: Dict[str, GameVariant] = {
    "chess": GameVariant.STANDARD,
    "standard": GameVariant.STANDARD,
    "chess960": GameVariant.CHESS960,
    "fischerandom": GameVariant.CHESS960,
    "crazyhouse": GameVariant.CRAZYHOUSE,
    "kingofthehill": GameVariant.KING_OF_THE_HILL,
    "threecheck": GameVariant.THREE_CHECK,
    "bughouse": GameVariant.OTHER,
    "oddschess": GameVariant.OTHER,
}


def detect_variant(
    game_url: str = "",
    rules_header: str = "",
    variant_header: str = "",
    game_data: Optional[Dict] = None,
) -> GameVariant:
    """
    Detect game variant from Chess.com game data.

    Checks multiple sources for variant information:
    1. Game URL patterns
    2. PGN headers (Rules, Variant)
    3. Game data fields

    Args:
        game_url: URL of the game
        rules_header: PGN Rules header value
        variant_header: PGN Variant header value
        game_data: Raw game data dict

    Returns:
        Detected GameVariant
    """
    # Check game data first (most reliable)
    if game_data:
        rules = game_data.get("rules", "")
        if rules:
            variant = CHESSCOM_VARIANT_MAP.get(rules.lower())
            if variant:
                return variant

    # Check URL patterns
    url_lower = game_url.lower()
    if "chess960" in url_lower or "/960/" in url_lower:
        return GameVariant.CHESS960
    if "crazyhouse" in url_lower:
        return GameVariant.CRAZYHOUSE
    if "kingofthehill" in url_lower:
        return GameVariant.KING_OF_THE_HILL
    if "3check" in url_lower or "threecheck" in url_lower:
        return GameVariant.THREE_CHECK

    # Check PGN headers
    for header in [variant_header, rules_header]:
        if header:
            header_lower = header.lower()
            for key, variant in CHESSCOM_VARIANT_MAP.items():
                if key in header_lower:
                    return variant

    return GameVariant.STANDARD


def is_chess960(game_data: Dict, pgn: str = "") -> bool:
    """
    Specifically check if a game is Chess960.

    More thorough check for the common case of Chess960 detection.

    Args:
        game_data: Raw game data from Chess.com
        pgn: PGN string if available

    Returns:
        True if game is Chess960
    """
    # Check rules field
    rules = game_data.get("rules", "")
    if rules.lower() in ("chess960", "fischerrandom"):
        return True

    # Check URL
    url = game_data.get("url", "")
    if "chess960" in url.lower() or "/960/" in url:
        return True

    # Check PGN headers
    if pgn:
        pgn_lower = pgn.lower()
        if '[variant "chess960"]' in pgn_lower:
            return True
        if '[rules "chess960"]' in pgn_lower or '[rules "fischerrandom"]' in pgn_lower:
            return True

    return False


# =============================================================================
# Termination Reason Mapping
# =============================================================================

# Mapping from Chess.com result strings to termination reasons
# Chess.com uses format like "win", "checkmated", "timeout", etc.
CHESSCOM_TERMINATION_MAP: Dict[str, TerminationReason] = {
    # Checkmate
    "checkmated": TerminationReason.CHECKMATE,
    "win": TerminationReason.CHECKMATE,  # Default for wins, may be overridden

    # Resignation
    "resigned": TerminationReason.RESIGNATION,

    # Timeout
    "timeout": TerminationReason.TIMEOUT,
    "timevsinsufficient": TerminationReason.TIMEOUT_VS_INSUFFICIENT,

    # Draws
    "agreed": TerminationReason.AGREEMENT,
    "repetition": TerminationReason.THREEFOLD_REPETITION,
    "stalemate": TerminationReason.STALEMATE,
    "insufficient": TerminationReason.INSUFFICIENT_MATERIAL,
    "50move": TerminationReason.FIFTY_MOVES,

    # Abandonment
    "abandoned": TerminationReason.ABANDONMENT,
    "kingofthehill": TerminationReason.OTHER,  # Variant-specific win
    "threecheck": TerminationReason.OTHER,  # Variant-specific win
    "bughousepartnerlose": TerminationReason.OTHER,  # Bughouse
}


def parse_termination(
    white_result: str,
    black_result: str,
    player_color: PlayerColor,
) -> Tuple[TerminationReason, GameResult, Optional[PlayerColor]]:
    """
    Parse Chess.com game termination details.

    Chess.com provides separate result strings for white and black.
    This function determines the termination reason, game result from
    the player's perspective, and the winner.

    Args:
        white_result: White's result string (e.g., "win", "checkmated")
        black_result: Black's result string
        player_color: Which color the analyzed player was

    Returns:
        Tuple of (TerminationReason, GameResult, winner_color or None)
    """
    white_result_lower = white_result.lower() if white_result else ""
    black_result_lower = black_result.lower() if black_result else ""

    # Determine winner
    winner: Optional[PlayerColor] = None
    if white_result_lower == "win" or black_result_lower in CHESSCOM_TERMINATION_MAP:
        if "win" in white_result_lower:
            winner = PlayerColor.WHITE
        elif "win" in black_result_lower:
            winner = PlayerColor.BLACK

    # Determine termination reason (from loser's result)
    loser_result = black_result_lower if winner == PlayerColor.WHITE else white_result_lower
    termination = CHESSCOM_TERMINATION_MAP.get(
        loser_result,
        TerminationReason.UNKNOWN
    )

    # Handle draws
    if white_result_lower in ("agreed", "repetition", "stalemate", "insufficient", "50move"):
        winner = None
        termination = CHESSCOM_TERMINATION_MAP.get(white_result_lower, TerminationReason.AGREEMENT)

    # Determine result from player's perspective
    if winner is None:
        result = GameResult.DRAW
    elif winner == player_color:
        result = GameResult.WIN
    else:
        result = GameResult.LOSS

    return termination, result, winner


# =============================================================================
# Game Mode Detection
# =============================================================================

# Chess.com game modes/contexts
CHESSCOM_GAME_MODES: Set[str] = {
    "rated",
    "casual",
    "tournament",
    "arena",
    "swiss",
    "team_match",
    "live",
    "daily",
}


def is_rated_game(game_data: Dict) -> bool:
    """Check if game was rated."""
    return game_data.get("rated", False)


def is_tournament_game(game_data: Dict) -> bool:
    """Check if game was part of a tournament."""
    tournament = game_data.get("tournament")
    match = game_data.get("match")
    return bool(tournament or match)


def is_daily_game(game_data: Dict) -> bool:
    """Check if game was a daily (correspondence) game."""
    time_class = game_data.get("time_class", "")
    return time_class == "daily"


# =============================================================================
# Opening Extraction
# =============================================================================

def extract_opening_from_url(eco_url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract opening name and ECO code from Chess.com ECO URL.

    Chess.com format: "https://www.chess.com/openings/Sicilian-Defense-2.Nf3-d6-3.d4"

    Args:
        eco_url: Chess.com opening URL

    Returns:
        Tuple of (opening_name, eco_code) - ECO code may be None
    """
    if not eco_url:
        return None, None

    try:
        # Extract the opening part from URL
        # Format: /openings/Opening-Name-With-Moves
        match = re.search(r'/openings/([^/]+)$', eco_url)
        if not match:
            return None, None

        opening_path = match.group(1)

        # Remove move sequence (everything after the main opening name that looks like moves)
        # Moves typically start with numbers: "2.Nf3", "3.d4", etc.
        opening_name = re.split(r'-\d+\.', opening_path)[0]

        # Replace dashes with spaces
        opening_name = opening_name.replace('-', ' ')

        # Clean up common patterns
        opening_name = opening_name.strip()

        return opening_name, None  # Chess.com URLs don't contain ECO codes

    except Exception:
        return None, None
