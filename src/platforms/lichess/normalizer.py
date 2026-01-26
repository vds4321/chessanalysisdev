"""
Lichess data normalizer.

Converts Lichess API responses to normalized schemas.
All Lichess-specific field mappings and transformations are here.
"""

import logging
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
    map_speed_to_time_class,
    detect_variant,
    parse_game_result,
    is_rated_game,
    is_tournament_game,
    extract_opening,
    get_opening_ply,
    get_player_rating,
    get_rating_diff,
    is_provisional_rating,
    get_player_title,
    player_berserked,
)

logger = logging.getLogger(__name__)


class LichessNormalizer:
    """
    Normalizes Lichess API data to common schemas.

    Handles all Lichess-specific data transformations so that
    the rest of the application works with normalized data.
    """

    def __init__(self):
        self.platform = Platform.LICHESS

    def normalize_game(
        self,
        raw_game: Dict[str, Any],
        player_username: str,
    ) -> NormalizedGame:
        """
        Convert Lichess game data to NormalizedGame.

        Lichess game format (from /api/games/user/{username}):
        {
            "id": "abc123",
            "rated": true,
            "variant": "standard",
            "speed": "blitz",
            "perf": "blitz",
            "createdAt": 1609459200000,
            "lastMoveAt": 1609460000000,
            "status": "mate",
            "players": {
                "white": {"user": {"name": "player1"}, "rating": 1500},
                "black": {"user": {"name": "player2"}, "rating": 1600}
            },
            "winner": "white",
            "moves": "e4 e5 Nf3 ...",
            "opening": {"eco": "C50", "name": "Italian Game", "ply": 6},
            "clock": {"initial": 300, "increment": 3}
        }

        Args:
            raw_game: Raw game data from Lichess API
            player_username: Username of the player we're analyzing

        Returns:
            NormalizedGame instance

        Raises:
            NormalizationError: If game data cannot be normalized
        """
        try:
            # Required fields
            game_id = raw_game.get("id")
            if not game_id:
                raise MissingDataError("id", platform="lichess")

            # Build URL
            url = f"https://lichess.org/{game_id}"

            # Parse timestamp (Lichess uses milliseconds)
            created_at = raw_game.get("createdAt")
            if created_at:
                played_at = datetime.fromtimestamp(created_at / 1000)
            else:
                played_at = datetime.now()

            # Parse time control
            clock_data = raw_game.get("clock")
            initial_sec, increment_sec, time_class = parse_time_control(clock_data)

            # Lichess also provides "speed" directly
            if raw_game.get("speed"):
                time_class = map_speed_to_time_class(raw_game["speed"])

            time_control = TimeControl(
                initial_seconds=initial_sec,
                increment_seconds=increment_sec,
                time_class=time_class,
                raw_string=f"{initial_sec}+{increment_sec}" if clock_data else "",
            )

            # Parse players
            white = self._parse_player_info(raw_game, "white")
            black = self._parse_player_info(raw_game, "black")

            # Determine player color
            player_lower = player_username.lower()
            if white.username.lower() == player_lower:
                player_color = PlayerColor.WHITE
            elif black.username.lower() == player_lower:
                player_color = PlayerColor.BLACK
            else:
                raise NormalizationError(
                    f"Player '{player_username}' not found in game",
                    platform="lichess",
                    field="player_username",
                )

            # Parse result and termination
            result, termination, winner = parse_game_result(raw_game, player_username)

            # Detect variant
            variant_str = raw_game.get("variant", "standard")
            variant = detect_variant(variant_str)

            # Parse opening
            opening = self._parse_opening(raw_game)

            # Extract moves
            moves_str = raw_game.get("moves", "")
            moves_san = moves_str.split() if moves_str else []

            # Is rated
            is_rated = is_rated_game(raw_game)

            # Build PGN (Lichess provides moves, we construct minimal PGN)
            pgn = self._construct_pgn(raw_game, white, black, moves_san)

            # Platform-specific metadata
            platform_metadata = {
                "speed": raw_game.get("speed"),
                "perf": raw_game.get("perf"),
                "tournament": raw_game.get("tournament"),
                "swiss": raw_game.get("swiss"),
                "is_tournament": is_tournament_game(raw_game),
                "source": raw_game.get("source"),
                "white_berserk": player_berserked(raw_game, "white"),
                "black_berserk": player_berserked(raw_game, "black"),
                "last_move_at": raw_game.get("lastMoveAt"),
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
            logger.error(f"Error normalizing Lichess game: {e}")
            raise NormalizationError(
                f"Failed to normalize game: {e}",
                platform="lichess",
            )

    def _parse_player_info(
        self,
        game_data: Dict[str, Any],
        color: str,
    ) -> PlayerInfo:
        """Parse player info from Lichess game data."""
        players = game_data.get("players", {})
        player_data = players.get(color, {})
        user_data = player_data.get("user", {})

        # Handle AI opponent (no user object)
        if not user_data:
            ai_level = player_data.get("aiLevel")
            if ai_level:
                username = f"Stockfish Level {ai_level}"
            else:
                username = "Anonymous"
        else:
            username = user_data.get("name", "Unknown")

        rating = get_player_rating(game_data, color)
        rating_diff = get_rating_diff(game_data, color)
        title = get_player_title(game_data, color)
        provisional = is_provisional_rating(game_data, color)

        return PlayerInfo(
            username=username,
            rating=rating,
            rating_diff=rating_diff,
            title=title,
            provisional=provisional,
        )

    def _parse_opening(self, game_data: Dict[str, Any]) -> Optional[Opening]:
        """Parse opening information from Lichess game data."""
        name, eco_code = extract_opening(game_data)

        if not name:
            return None

        ply_count = get_opening_ply(game_data)

        # Lichess opening explorer URL
        url = None
        if eco_code:
            url = f"https://lichess.org/opening/{eco_code}"

        return Opening(
            name=name,
            eco_code=eco_code,
            url=url,
            moves_in_theory=ply_count // 2,  # Convert ply to moves
            ply_count=ply_count,
        )

    def _construct_pgn(
        self,
        game_data: Dict[str, Any],
        white: PlayerInfo,
        black: PlayerInfo,
        moves: List[str],
    ) -> str:
        """
        Construct a minimal PGN from Lichess game data.

        Lichess provides moves as a space-separated string, not full PGN.
        We construct a basic PGN for compatibility with PGN parsers.
        """
        if not moves:
            return ""

        # Build headers
        headers = []
        headers.append(f'[Event "Lichess Game"]')
        headers.append(f'[Site "https://lichess.org/{game_data.get("id", "")}"]')

        created_at = game_data.get("createdAt")
        if created_at:
            date = datetime.fromtimestamp(created_at / 1000)
            headers.append(f'[Date "{date.strftime("%Y.%m.%d")}"]')

        headers.append(f'[White "{white.username}"]')
        headers.append(f'[Black "{black.username}"]')
        headers.append(f'[WhiteElo "{white.rating}"]')
        headers.append(f'[BlackElo "{black.rating}"]')

        # Result
        winner = game_data.get("winner")
        if winner == "white":
            result = "1-0"
        elif winner == "black":
            result = "0-1"
        else:
            result = "1/2-1/2"
        headers.append(f'[Result "{result}"]')

        # Variant
        variant = game_data.get("variant", "standard")
        if variant != "standard":
            headers.append(f'[Variant "{variant}"]')

        # Opening
        opening = game_data.get("opening", {})
        if opening:
            if eco := opening.get("eco"):
                headers.append(f'[ECO "{eco}"]')
            if name := opening.get("name"):
                headers.append(f'[Opening "{name}"]')

        # Time control
        clock = game_data.get("clock", {})
        if clock:
            tc = f"{clock.get('initial', 0)}+{clock.get('increment', 0)}"
            headers.append(f'[TimeControl "{tc}"]')

        # Construct move text
        move_pairs = []
        for i in range(0, len(moves), 2):
            move_num = (i // 2) + 1
            white_move = moves[i]
            black_move = moves[i + 1] if i + 1 < len(moves) else ""

            if black_move:
                move_pairs.append(f"{move_num}. {white_move} {black_move}")
            else:
                move_pairs.append(f"{move_num}. {white_move}")

        move_text = " ".join(move_pairs)
        if result:
            move_text += f" {result}"

        # Combine
        return "\n".join(headers) + "\n\n" + move_text

    def normalize_profile(
        self,
        raw_profile: Dict[str, Any],
        raw_stats: Optional[Dict[str, Any]] = None,
    ) -> PlayerProfile:
        """
        Convert Lichess profile data to PlayerProfile.

        Lichess profile format (from /api/user/{username}):
        {
            "id": "username",
            "username": "Username",
            "title": "GM",
            "createdAt": 1609459200000,
            "seenAt": 1609460000000,
            "playTime": {"total": 123456},
            "count": {"all": 1000, "win": 500, "loss": 400, "draw": 100},
            "perfs": {
                "bullet": {"games": 100, "rating": 1500, "prog": 50},
                "blitz": {"games": 200, "rating": 1600, "prog": -20}
            }
        }

        Args:
            raw_profile: Profile data from /api/user/{username}
            raw_stats: Not used for Lichess (stats included in profile)

        Returns:
            PlayerProfile instance
        """
        username = raw_profile.get("username", raw_profile.get("id", "Unknown"))
        url = f"https://lichess.org/@/{username}"

        # Parse timestamps
        created_at_ms = raw_profile.get("createdAt")
        joined_at = datetime.fromtimestamp(created_at_ms / 1000) if created_at_ms else None

        seen_at_ms = raw_profile.get("seenAt")
        last_online = datetime.fromtimestamp(seen_at_ms / 1000) if seen_at_ms else None

        # Profile info
        title = raw_profile.get("title")

        # Country (Lichess provides profile.country)
        profile_data = raw_profile.get("profile", {})
        country = profile_data.get("country")

        # Streaming/patron status
        is_streamer = raw_profile.get("streamer", False)
        verified = raw_profile.get("verified", False) or raw_profile.get("patron", False)

        # Parse ratings from perfs
        ratings: Dict[TimeClass, int] = {}
        perfs = raw_profile.get("perfs", {})

        perf_mappings = [
            ("ultraBullet", TimeClass.ULTRA_BULLET),
            ("bullet", TimeClass.BULLET),
            ("blitz", TimeClass.BLITZ),
            ("rapid", TimeClass.RAPID),
            ("classical", TimeClass.CLASSICAL),
            ("correspondence", TimeClass.CORRESPONDENCE),
        ]

        for perf_key, time_class in perf_mappings:
            perf_data = perfs.get(perf_key, {})
            if rating := perf_data.get("rating"):
                ratings[time_class] = rating

        # Game counts
        count = raw_profile.get("count", {})
        total_games = count.get("all", 0)
        wins = count.get("win", 0)
        losses = count.get("loss", 0)
        draws = count.get("draw", 0)

        # Platform-specific metadata
        platform_metadata = {
            "lichess_id": raw_profile.get("id"),
            "patron": raw_profile.get("patron", False),
            "streaming": raw_profile.get("streaming", False),
            "play_time_total": raw_profile.get("playTime", {}).get("total"),
            "completion_rate": raw_profile.get("completionRate"),
            "perfs": perfs,  # Full perf data for detailed analysis
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
