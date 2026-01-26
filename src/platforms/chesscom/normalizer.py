"""
Chess.com data normalizer.

Converts Chess.com API responses to normalized schemas.
All Chess.com-specific field mappings and transformations are here.
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

from src.core.constants import (
    Platform,
    GameResult,
    TerminationReason,
    TimeClass,
    GameVariant,
    PlayerColor,
)
from src.core.schemas import (
    NormalizedGame,
    PlayerProfile,
    PlayerInfo,
    TimeControl,
    Opening,
)
from src.core.exceptions import NormalizationError, MissingDataError

from .game_types import (
    parse_time_control,
    map_time_class,
    detect_variant,
    is_chess960,
    parse_termination,
    is_rated_game,
    is_tournament_game,
    extract_opening_from_url,
)

logger = logging.getLogger(__name__)


class ChessComNormalizer:
    """
    Normalizes Chess.com API data to common schemas.

    Handles all Chess.com-specific data transformations so that
    the rest of the application works with normalized data.
    """

    def __init__(self):
        self.platform = Platform.CHESS_COM

    def normalize_game(
        self,
        raw_game: Dict[str, Any],
        player_username: str,
    ) -> NormalizedGame:
        """
        Convert Chess.com game data to NormalizedGame.

        Args:
            raw_game: Raw game data from Chess.com API
            player_username: Username of the player we're analyzing

        Returns:
            NormalizedGame instance

        Raises:
            NormalizationError: If game data cannot be normalized
        """
        try:
            # Required fields
            game_id = raw_game.get("uuid")
            if not game_id:
                # Fall back to URL-based ID
                game_id = raw_game.get("url", "").split("/")[-1]
            if not game_id:
                raise MissingDataError("game_id", platform="chesscom")

            url = raw_game.get("url", "")

            # Parse timestamp
            end_time = raw_game.get("end_time")
            if end_time:
                played_at = datetime.fromtimestamp(end_time)
            else:
                played_at = datetime.now()

            # Parse time control
            tc_string = raw_game.get("time_control", "")
            initial_sec, increment_sec, time_class = parse_time_control(tc_string)

            # Chess.com also provides time_class directly
            if raw_game.get("time_class"):
                time_class = map_time_class(raw_game["time_class"])

            time_control = TimeControl(
                initial_seconds=initial_sec,
                increment_seconds=increment_sec,
                time_class=time_class,
                raw_string=tc_string,
            )

            # Parse players
            white_data = raw_game.get("white", {})
            black_data = raw_game.get("black", {})

            white = self._parse_player_info(white_data)
            black = self._parse_player_info(black_data)

            # Determine player color
            player_lower = player_username.lower()
            if white.username.lower() == player_lower:
                player_color = PlayerColor.WHITE
            elif black.username.lower() == player_lower:
                player_color = PlayerColor.BLACK
            else:
                raise NormalizationError(
                    f"Player '{player_username}' not found in game",
                    platform="chesscom",
                    field="player_username",
                )

            # Parse result and termination
            white_result = white_data.get("result", "")
            black_result = black_data.get("result", "")
            termination, result, winner = parse_termination(
                white_result, black_result, player_color
            )

            # Detect variant
            pgn = raw_game.get("pgn", "")
            variant = detect_variant(
                game_url=url,
                game_data=raw_game,
            )

            # Double-check Chess960
            if variant == GameVariant.STANDARD and is_chess960(raw_game, pgn):
                variant = GameVariant.CHESS960

            # Parse opening
            opening = self._parse_opening(raw_game, pgn)

            # Extract moves from PGN
            moves_san = self._extract_moves_from_pgn(pgn)

            # Is rated
            is_rated = is_rated_game(raw_game)

            # Platform-specific metadata
            platform_metadata = {
                "accuracy_white": raw_game.get("accuracies", {}).get("white"),
                "accuracy_black": raw_game.get("accuracies", {}).get("black"),
                "tournament": raw_game.get("tournament"),
                "match": raw_game.get("match"),
                "is_tournament": is_tournament_game(raw_game),
            }

            return NormalizedGame(
                game_id=game_id,
                platform=self.platform,
                url=url,
                played_at=played_at,
                time_control=time_control,
                white=white,
                black=black,
                player_username=player_username,
                result=result,
                termination=termination,
                winner=winner,
                opening=opening,
                pgn=pgn,
                moves_san=moves_san,
                variant=variant,
                is_rated=is_rated,
                platform_metadata=platform_metadata,
            )

        except MissingDataError:
            raise
        except NormalizationError:
            raise
        except Exception as e:
            logger.error(f"Error normalizing Chess.com game: {e}")
            raise NormalizationError(
                f"Failed to normalize game: {e}",
                platform="chesscom",
            )

    def _parse_player_info(self, player_data: Dict[str, Any]) -> PlayerInfo:
        """Parse player info from Chess.com game data."""
        username = player_data.get("username", "Unknown")
        rating = player_data.get("rating", 0)

        # Extract title if present (embedded in username like "@username")
        # Chess.com doesn't always provide title in game data
        title = None

        return PlayerInfo(
            username=username,
            rating=rating,
            rating_diff=None,  # Not provided in game data
            title=title,
            provisional=False,  # Chess.com doesn't indicate this in game data
        )

    def _parse_opening(
        self,
        game_data: Dict[str, Any],
        pgn: str,
    ) -> Optional[Opening]:
        """Parse opening information from game data or PGN."""
        # Try ECO URL first (Chess.com specific)
        eco_url = game_data.get("eco")
        if eco_url:
            name, eco_code = extract_opening_from_url(eco_url)
            if name:
                return Opening(
                    name=name,
                    eco_code=eco_code,
                    url=eco_url,
                )

        # Try to extract from PGN headers
        if pgn:
            opening_name = self._extract_pgn_header(pgn, "Opening")
            eco_code = self._extract_pgn_header(pgn, "ECO")

            if opening_name:
                return Opening(
                    name=opening_name,
                    eco_code=eco_code,
                )

        return None

    def _extract_pgn_header(self, pgn: str, header_name: str) -> Optional[str]:
        """Extract a header value from PGN."""
        pattern = rf'\[{header_name}\s+"([^"]+)"\]'
        match = re.search(pattern, pgn, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _extract_moves_from_pgn(self, pgn: str) -> List[str]:
        """Extract move list from PGN."""
        if not pgn:
            return []

        try:
            # Find the move section (after headers)
            # Headers are in format [Header "value"]
            lines = pgn.split("\n")
            move_lines = []

            in_moves = False
            for line in lines:
                line = line.strip()
                if not line:
                    in_moves = True
                    continue
                if in_moves and not line.startswith("["):
                    move_lines.append(line)

            move_text = " ".join(move_lines)

            # Remove comments {comment}
            move_text = re.sub(r'\{[^}]*\}', '', move_text)

            # Remove annotations like $1, $2
            move_text = re.sub(r'\$\d+', '', move_text)

            # Remove result at end
            move_text = re.sub(r'\s*(1-0|0-1|1/2-1/2|\*)\s*$', '', move_text)

            # Extract moves (format: 1. e4 e5 2. Nf3 Nc6)
            # Split on move numbers
            moves = []
            parts = re.split(r'\d+\.+\s*', move_text)

            for part in parts:
                part = part.strip()
                if not part:
                    continue
                # Each part may have one or two moves (white and black)
                move_parts = part.split()
                for move in move_parts:
                    move = move.strip()
                    if move and not move.endswith('.'):
                        moves.append(move)

            return moves

        except Exception as e:
            logger.warning(f"Error extracting moves from PGN: {e}")
            return []

    def normalize_profile(
        self,
        raw_profile: Dict[str, Any],
        raw_stats: Optional[Dict[str, Any]] = None,
    ) -> PlayerProfile:
        """
        Convert Chess.com profile data to PlayerProfile.

        Args:
            raw_profile: Profile data from /player/{username}
            raw_stats: Stats data from /player/{username}/stats

        Returns:
            PlayerProfile instance
        """
        username = raw_profile.get("username", "Unknown")
        url = raw_profile.get("url", f"https://www.chess.com/member/{username}")

        # Parse join date
        joined_timestamp = raw_profile.get("joined")
        joined_at = datetime.fromtimestamp(joined_timestamp) if joined_timestamp else None

        # Parse last online
        last_online_timestamp = raw_profile.get("last_online")
        last_online = datetime.fromtimestamp(last_online_timestamp) if last_online_timestamp else None

        # Country (Chess.com provides as URL)
        country_url = raw_profile.get("country", "")
        country = country_url.split("/")[-1] if country_url else None

        # Title
        title = raw_profile.get("title")

        # Streaming status
        is_streamer = raw_profile.get("is_streamer", False)
        verified = raw_profile.get("verified", False)

        # Parse ratings from stats
        ratings: Dict[TimeClass, int] = {}
        total_games = 0
        wins = 0
        losses = 0
        draws = 0

        if raw_stats:
            rating_categories = [
                ("chess_bullet", TimeClass.BULLET),
                ("chess_blitz", TimeClass.BLITZ),
                ("chess_rapid", TimeClass.RAPID),
                ("chess_daily", TimeClass.CORRESPONDENCE),
            ]

            for stat_key, time_class in rating_categories:
                stat_data = raw_stats.get(stat_key, {})
                if stat_data:
                    last_rating = stat_data.get("last", {}).get("rating")
                    if last_rating:
                        ratings[time_class] = last_rating

                    # Aggregate game counts
                    record = stat_data.get("record", {})
                    total_games += record.get("win", 0) + record.get("loss", 0) + record.get("draw", 0)
                    wins += record.get("win", 0)
                    losses += record.get("loss", 0)
                    draws += record.get("draw", 0)

        # Platform-specific metadata
        platform_metadata = {
            "player_id": raw_profile.get("player_id"),
            "status": raw_profile.get("status"),
            "followers": raw_profile.get("followers"),
            "is_streamer": is_streamer,
        }

        return PlayerProfile(
            username=username,
            platform=self.platform,
            url=url,
            joined_at=joined_at,
            last_online=last_online,
            country=country,
            title=title,
            is_streamer=is_streamer,
            verified=verified,
            ratings=ratings,
            total_games=total_games,
            wins=wins,
            losses=losses,
            draws=draws,
            platform_metadata=platform_metadata,
        )
