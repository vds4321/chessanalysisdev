"""
Chess Game Parser

This module parses PGN data from Chess.com games and extracts structured
information including move analysis, time usage, and game phases.
"""

import chess
import chess.pgn
import chess.engine
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from io import StringIO
import logging

from config.settings import Config

logger = logging.getLogger(__name__)


class GameParser:
    """Parses and analyzes chess games from PGN data."""
    
    def __init__(self, stockfish_path: Optional[str] = None):
        """
        Initialize the game parser.
        
        Args:
            stockfish_path: Path to Stockfish engine executable
        """
        self.stockfish_path = stockfish_path or Config.STOCKFISH_PATH
        self.engine = None
        self._init_engine()
    
    def _init_engine(self):
        """Initialize the Stockfish engine."""
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            logger.info("Stockfish engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Stockfish engine: {e}")
            logger.error("Analysis features requiring engine evaluation will be disabled")
    
    def __del__(self):
        """Clean up the engine when parser is destroyed."""
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass
    
    def parse_chess_com_game(self, game_data: Dict) -> Optional[Dict]:
        """
        Parse a single Chess.com game and extract analysis data.
        
        Args:
            game_data: Raw game data from Chess.com API
            
        Returns:
            Parsed game analysis or None if parsing failed
        """
        try:
            # Extract basic game metadata
            metadata = self._extract_metadata(game_data)
            if not metadata:
                return None
            
            # Parse PGN
            pgn_string = game_data.get('pgn', '')
            if not pgn_string:
                logger.warning("No PGN data found in game")
                return None
            
            game = chess.pgn.read_game(StringIO(pgn_string))
            if not game:
                logger.warning("Failed to parse PGN")
                return None
            
            # Extract move analysis
            move_analysis = self._analyze_moves(game, metadata['player_color'])
            
            # Determine game phases
            game_phases = self._determine_game_phases(move_analysis)
            
            # Calculate opening analysis
            opening_analysis = self._analyze_opening(game, move_analysis)
            
            # Calculate game statistics
            statistics = self._calculate_statistics(move_analysis, metadata['player_color'])
            
            return {
                'game_metadata': metadata,
                'opening_analysis': opening_analysis,
                'move_analysis': move_analysis,
                'game_phases': game_phases,
                'statistics': statistics,
                'pgn': pgn_string  # Preserve original PGN for tactical analysis
            }
            
        except Exception as e:
            logger.error(f"Error parsing game: {e}")
            return None
    
    def _extract_metadata(self, game_data: Dict) -> Optional[Dict]:
        """Extract game metadata from Chess.com game data."""
        try:
            # Determine player color and opponent info
            white_player = game_data.get('white', {})
            black_player = game_data.get('black', {})
            
            username = Config.CHESS_COM_USERNAME.lower()
            
            if white_player.get('username', '').lower() == username:
                player_color = 'white'
                opponent_rating = black_player.get('rating', 0)
                player_result = white_player.get('result', '')
            elif black_player.get('username', '').lower() == username:
                player_color = 'black'
                opponent_rating = white_player.get('rating', 0)
                player_result = black_player.get('result', '')
            else:
                logger.warning("Player not found in game data")
                return None
            
            # Convert result to standard format
            result_map = {
                'win': '1',
                'checkmated': '0',
                'agreed': '1/2',
                'resigned': '0',
                'timeout': '0',
                'repetition': '1/2',
                'stalemate': '1/2',
                'insufficient': '1/2'
            }
            
            result = result_map.get(player_result, '1/2')
            
            return {
                'game_id': game_data.get('uuid', ''),
                'url': game_data.get('url', ''),
                'date': datetime.fromtimestamp(game_data.get('end_time', 0)),
                'time_control': game_data.get('time_control', ''),
                'time_class': game_data.get('time_class', ''),
                'player_color': player_color,
                'opponent_rating': opponent_rating,
                'result': result,
                'termination': player_result,
                'rated': game_data.get('rated', False)
            }
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return None
    
    def _analyze_moves(self, game: chess.pgn.Game, player_color: str) -> List[Dict]:
        """
        Analyze each move in the game.
        
        Args:
            game: Parsed PGN game
            player_color: Color the player was playing ('white' or 'black')
            
        Returns:
            List of move analysis dictionaries
        """
        move_analysis = []
        board = game.board()
        node = game
        move_number = 1
        
        while node.variations:
            node = node.variation(0)
            move = node.move
            
            # Determine if this is the player's move
            is_player_move = (board.turn == chess.WHITE and player_color == 'white') or \
                           (board.turn == chess.BLACK and player_color == 'black')
            
            # Extract time information
            time_info = self._extract_time_info(node)
            
            # Get position evaluation if engine is available
            evaluation = None
            best_move = None
            if self.engine and is_player_move:
                try:
                    info = self.engine.analyse(board, chess.engine.Limit(depth=Config.ANALYSIS_DEPTH))
                    evaluation = info.get('score', chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE)).relative.score()
                    best_move = str(info.get('pv', [None])[0]) if info.get('pv') else None
                except:
                    pass
            
            # Classify move quality
            classification = self._classify_move(board, move, evaluation, best_move)
            
            move_data = {
                'move_number': move_number,
                'move': str(move),
                'san': board.san(move),
                'is_player_move': is_player_move,
                'time_spent': time_info.get('time_spent', 0),
                'time_remaining': time_info.get('time_remaining', 0),
                'evaluation': evaluation,
                'best_move': best_move,
                'classification': classification,
                'fen': board.fen()
            }
            
            move_analysis.append(move_data)
            
            # Make the move
            board.push(move)
            
            if board.turn == chess.WHITE:
                move_number += 1
        
        return move_analysis
    
    def _extract_time_info(self, node: chess.pgn.GameNode) -> Dict:
        """Extract time information from a move node."""
        comment = node.comment or ''
        
        # Parse time from comment (format: [%clk 0:05:23])
        time_pattern = r'\[%clk (\d+):(\d+):(\d+)\]'
        match = re.search(time_pattern, comment)
        
        if match:
            hours, minutes, seconds = map(int, match.groups())
            time_remaining = hours * 3600 + minutes * 60 + seconds
        else:
            time_remaining = 0
        
        # Time spent is calculated by comparing with previous move
        # This is a simplified calculation
        time_spent = 0  # Would need previous move's time to calculate
        
        return {
            'time_spent': time_spent,
            'time_remaining': time_remaining
        }
    
    def _classify_move(self, board: chess.Board, move: chess.Move, 
                      evaluation: Optional[int], best_move: Optional[str]) -> str:
        """
        Classify move quality based on evaluation.
        
        Args:
            board: Current board position
            move: Move played
            evaluation: Position evaluation after move
            best_move: Best move according to engine
            
        Returns:
            Move classification string
        """
        if not self.engine or evaluation is None:
            return 'unknown'
        
        try:
            # Get evaluation before the move
            board_copy = board.copy()
            board_copy.pop()  # Undo the move
            
            info = self.engine.analyse(board_copy, chess.engine.Limit(depth=Config.ANALYSIS_DEPTH))
            prev_eval = info.get('score', chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE)).relative.score()
            
            if prev_eval is None:
                return 'unknown'
            
            # Calculate centipawn loss
            eval_diff = abs(evaluation - prev_eval) if evaluation and prev_eval else 0
            
            # Classify based on centipawn loss
            if eval_diff >= Config.BLUNDER_THRESHOLD:
                return 'blunder'
            elif eval_diff >= Config.MISTAKE_THRESHOLD:
                return 'mistake'
            elif eval_diff >= Config.INACCURACY_THRESHOLD:
                return 'inaccuracy'
            else:
                return 'good'
                
        except:
            return 'unknown'
    
    def _determine_game_phases(self, move_analysis: List[Dict]) -> Dict:
        """
        Determine game phase boundaries.
        
        Args:
            move_analysis: List of move analysis data
            
        Returns:
            Dictionary with phase boundaries
        """
        # Simple heuristic: opening ends at move 15, endgame starts when few pieces remain
        opening_end = min(Config.OPENING_BOOK_DEPTH, len(move_analysis))
        
        # Endgame detection would require piece counting from FEN
        # For now, use a simple heuristic
        endgame_start = max(opening_end + 10, int(len(move_analysis) * 0.7))
        middlegame_end = endgame_start
        
        return {
            'opening_end': opening_end,
            'middlegame_end': middlegame_end,
            'endgame_start': endgame_start
        }
    
    def _analyze_opening(self, game: chess.pgn.Game, move_analysis: List[Dict]) -> Dict:
        """
        Analyze opening performance.
        
        Args:
            game: Parsed PGN game
            move_analysis: List of move analysis data
            
        Returns:
            Opening analysis data
        """
        # Extract opening information from PGN headers
        opening_name = game.headers.get('Opening', 'Unknown')
        eco_code = game.headers.get('ECO', '')
        
        # Count moves in theory (simplified - would need opening database)
        moves_in_theory = 0
        first_inaccuracy_move = None
        
        for i, move_data in enumerate(move_analysis[:Config.OPENING_BOOK_DEPTH]):
            if move_data['classification'] in ['inaccuracy', 'mistake', 'blunder']:
                if first_inaccuracy_move is None:
                    first_inaccuracy_move = i + 1
                break
            moves_in_theory += 1
        
        return {
            'opening_name': opening_name,
            'eco_code': eco_code,
            'moves_in_theory': moves_in_theory,
            'first_inaccuracy_move': first_inaccuracy_move,
            'opening_advantage': 0  # Would need engine evaluation
        }
    
    def _calculate_statistics(self, move_analysis: List[Dict], player_color: str) -> Dict:
        """
        Calculate game statistics.
        
        Args:
            move_analysis: List of move analysis data
            player_color: Player's color
            
        Returns:
            Game statistics
        """
        player_moves = [move for move in move_analysis if move['is_player_move']]
        
        if not player_moves:
            return {}
        
        # Count move classifications
        blunders = sum(1 for move in player_moves if move['classification'] == 'blunder')
        mistakes = sum(1 for move in player_moves if move['classification'] == 'mistake')
        inaccuracies = sum(1 for move in player_moves if move['classification'] == 'inaccuracy')
        good_moves = sum(1 for move in player_moves if move['classification'] == 'good')
        
        total_moves = len(player_moves)
        accuracy = (good_moves / total_moves * 100) if total_moves > 0 else 0
        
        # Calculate average centipawn loss (simplified)
        evaluations = [move['evaluation'] for move in player_moves if move['evaluation'] is not None]
        avg_centipawn_loss = sum(abs(e) for e in evaluations) / len(evaluations) if evaluations else 0
        
        return {
            'total_moves': total_moves,
            'accuracy': accuracy,
            'blunders': blunders,
            'mistakes': mistakes,
            'inaccuracies': inaccuracies,
            'good_moves': good_moves,
            'average_centipawn_loss': avg_centipawn_loss
        }
    
    def parse_games_batch(self, games_data: List[Dict]) -> List[Dict]:
        """
        Parse multiple games in batch.
        
        Args:
            games_data: List of raw game data from Chess.com
            
        Returns:
            List of parsed game analyses
        """
        parsed_games = []
        
        for i, game_data in enumerate(games_data):
            logger.info(f"Parsing game {i + 1}/{len(games_data)}")
            
            parsed_game = self.parse_chess_com_game(game_data)
            if parsed_game:
                parsed_games.append(parsed_game)
            else:
                logger.warning(f"Failed to parse game {i + 1}")
        
        logger.info(f"Successfully parsed {len(parsed_games)}/{len(games_data)} games")
        return parsed_games


def main():
    """Example usage of the game parser."""
    import os
    
    # Example: Parse games from a saved file
    raw_data_path = os.path.join(Config.RAW_DATA_DIR, "example_games.json")
    
    if os.path.exists(raw_data_path):
        with open(raw_data_path, 'r') as f:
            games_data = json.load(f)
        
        parser = GameParser()
        parsed_games = parser.parse_games_batch(games_data)
        
        # Save parsed games
        output_path = os.path.join(Config.PROCESSED_DATA_DIR, "parsed_games.json")
        os.makedirs(Config.PROCESSED_DATA_DIR, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(parsed_games, f, indent=2, default=str)
        
        print(f"Parsed {len(parsed_games)} games and saved to {output_path}")
    else:
        print(f"No games file found at {raw_data_path}")
        print("Run the data fetcher first to download games")


if __name__ == "__main__":
    main()
