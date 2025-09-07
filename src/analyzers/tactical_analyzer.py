"""
Tactical Analysis Module

This module analyzes chess games for tactical patterns, blunders, mistakes,
and missed opportunities using Stockfish engine evaluation.
"""

import chess
import chess.engine
import chess.pgn
from typing import List, Dict, Optional, Tuple
import logging
from config.settings import Config

logger = logging.getLogger(__name__)


class TacticalAnalyzer:
    """Analyzes tactical patterns and errors in chess games."""
    
    def __init__(self, stockfish_path: Optional[str] = None):
        """
        Initialize the tactical analyzer.
        
        Args:
            stockfish_path: Path to Stockfish engine
        """
        self.stockfish_path = stockfish_path or Config.STOCKFISH_PATH
        self.engine = None
        
    def _init_engine(self):
        """Initialize Stockfish engine."""
        if self.engine is None:
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
                logger.info("Stockfish engine initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Stockfish: {e}")
                raise
    
    def _close_engine(self):
        """Close Stockfish engine."""
        if self.engine:
            self.engine.quit()
            self.engine = None
    
    def analyze_game_tactics(self, pgn_string: str, player_name: str) -> Dict:
        """
        Analyze tactical patterns in a single game.
        
        Args:
            pgn_string: PGN string of the game
            player_name: Name of the player to analyze
            
        Returns:
            Dictionary with tactical analysis results
        """
        try:
            self._init_engine()
            
            # Parse PGN
            from io import StringIO
            game = chess.pgn.read_game(StringIO(pgn_string))
            if not game:
                return {}
            
            board = game.board()
            moves = list(game.mainline_moves())
            
            # Determine player color
            white_player = game.headers.get("White", "").lower()
            black_player = game.headers.get("Black", "").lower()
            player_color = "white" if player_name.lower() in white_player else "black"
            
            tactical_data = {
                'player_color': player_color,
                'total_moves': len(moves),
                'blunders': [],
                'mistakes': [],
                'inaccuracies': [],
                'missed_tactics': [],
                'good_moves': [],
                'move_evaluations': []
            }
            
            # Analyze each move
            for move_num, move in enumerate(moves):
                # Only analyze player's moves
                is_player_move = (move_num % 2 == 0 and player_color == "white") or \
                               (move_num % 2 == 1 and player_color == "black")
                
                if not is_player_move:
                    board.push(move)
                    continue
                
                # Get position before move
                position_before = board.copy()
                
                # Evaluate position before move
                try:
                    if not self.engine:
                        logger.warning("Engine not initialized, skipping move analysis")
                        board.push(move)
                        continue
                    eval_before = self.engine.analyse(
                        position_before,
                        chess.engine.Limit(depth=Config.ANALYSIS_DEPTH)
                    )
                    score_before = eval_before.get('score', chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE)).relative.score(mate_score=10000)
                    
                    # Make the move
                    board.push(move)
                    
                    # Evaluate position after move
                    eval_after = self.engine.analyse(
                        board,
                        chess.engine.Limit(depth=Config.ANALYSIS_DEPTH)
                    )
                    score_after = -eval_after.get('score', chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE)).relative.score(mate_score=10000)
                    
                    # Calculate evaluation change
                    eval_change = score_after - score_before
                    
                    # Find best move
                    best_move_info = self.engine.analyse(
                        position_before,
                        chess.engine.Limit(depth=Config.ANALYSIS_DEPTH)
                    )
                    best_move = best_move_info.get('pv', [None])[0] if best_move_info.get('pv') else None
                    
                    # Categorize the move
                    move_analysis = {
                        'move_number': move_num // 2 + 1,
                        'move': move.uci(),
                        'move_san': position_before.san(move),
                        'eval_before': score_before,
                        'eval_after': score_after,
                        'eval_change': eval_change,
                        'best_move': best_move.uci() if best_move else None,
                        'best_move_san': position_before.san(best_move) if best_move else None
                    }
                    
                    tactical_data['move_evaluations'].append(move_analysis)
                    
                    # Classify move quality
                    if eval_change <= -Config.BLUNDER_THRESHOLD:
                        tactical_data['blunders'].append(move_analysis)
                    elif eval_change <= -Config.MISTAKE_THRESHOLD:
                        tactical_data['mistakes'].append(move_analysis)
                    elif eval_change <= -Config.INACCURACY_THRESHOLD:
                        tactical_data['inaccuracies'].append(move_analysis)
                    elif eval_change >= 50:  # Good move
                        tactical_data['good_moves'].append(move_analysis)
                    
                    # Check for missed tactics (if best move is much better)
                    if best_move and best_move != move:
                        position_after_best = position_before.copy()
                        position_after_best.push(best_move)
                        eval_best = self.engine.analyse(
                            position_after_best,
                            chess.engine.Limit(depth=Config.ANALYSIS_DEPTH)
                        )
                        score_best = -eval_best.get('score', chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE)).relative.score(mate_score=10000)
                        
                        if score_best - score_after >= 100:  # Missed significant improvement
                            tactical_data['missed_tactics'].append({
                                **move_analysis,
                                'missed_eval': score_best,
                                'missed_opportunity': score_best - score_after
                            })
                    
                except Exception as e:
                    logger.warning(f"Error analyzing move {move_num}: {e}")
                    board.push(move)
                    continue
            
            # Calculate summary statistics
            tactical_data['summary'] = {
                'total_blunders': len(tactical_data['blunders']),
                'total_mistakes': len(tactical_data['mistakes']),
                'total_inaccuracies': len(tactical_data['inaccuracies']),
                'total_good_moves': len(tactical_data['good_moves']),
                'total_missed_tactics': len(tactical_data['missed_tactics']),
                'accuracy': self._calculate_accuracy(tactical_data['move_evaluations'])
            }
            
            return tactical_data
            
        except Exception as e:
            logger.error(f"Error in tactical analysis: {e}")
            return {}
        finally:
            self._close_engine()
    
    def _calculate_accuracy(self, move_evaluations: List[Dict]) -> float:
        """Calculate accuracy percentage based on move evaluations."""
        if not move_evaluations:
            return 0.0
        
        total_eval_loss = 0
        for move_eval in move_evaluations:
            eval_change = move_eval.get('eval_change', 0)
            if eval_change < 0:  # Only count evaluation losses
                total_eval_loss += abs(eval_change)
        
        # Simple accuracy calculation (can be refined)
        avg_eval_loss = total_eval_loss / len(move_evaluations)
        accuracy = max(0, 100 - (avg_eval_loss / 10))  # Scale to percentage
        return min(100, accuracy)
    
    def analyze_tactical_patterns(self, games_data: List[Dict]) -> Dict:
        """
        Analyze tactical patterns across multiple games.
        
        Args:
            games_data: List of game dictionaries with tactical analysis
            
        Returns:
            Dictionary with pattern analysis results
        """
        if not games_data:
            return {}
        
        patterns = {
            'common_blunder_positions': [],
            'frequent_mistake_types': {},
            'time_pressure_correlation': {},
            'opponent_rating_correlation': {},
            'opening_tactical_performance': {},
            'endgame_tactical_performance': {}
        }
        
        # Analyze patterns across games
        for game_data in games_data:
            tactical_data = game_data.get('tactical_analysis', {})
            if not tactical_data:
                continue
            
            # Analyze blunder patterns
            for blunder in tactical_data.get('blunders', []):
                move_num = blunder.get('move_number', 0)
                if move_num <= 15:  # Opening
                    patterns['opening_tactical_performance']['blunders'] = \
                        patterns['opening_tactical_performance'].get('blunders', 0) + 1
                elif move_num >= 40:  # Endgame
                    patterns['endgame_tactical_performance']['blunders'] = \
                        patterns['endgame_tactical_performance'].get('blunders', 0) + 1
        
        return patterns
    
    def get_tactical_recommendations(self, tactical_analysis: Dict) -> List[Dict]:
        """
        Generate tactical improvement recommendations.
        
        Args:
            tactical_analysis: Results from tactical analysis
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        if not tactical_analysis:
            return recommendations
        
        summary = tactical_analysis.get('summary', {})
        blunders = summary.get('total_blunders', 0)
        mistakes = summary.get('total_mistakes', 0)
        accuracy = summary.get('accuracy', 0)
        missed_tactics = summary.get('total_missed_tactics', 0)
        
        # Blunder recommendations
        if blunders > 2:
            recommendations.append({
                'priority': 'high',
                'type': 'blunder_reduction',
                'title': 'Reduce Blunders',
                'description': f'You made {blunders} blunders in this game. Focus on double-checking moves that involve material.',
                'specific_advice': 'Before each move, ask: "What is my opponent threatening?" and "Is my piece safe?"'
            })
        
        # Accuracy recommendations
        if accuracy < 70:
            recommendations.append({
                'priority': 'high',
                'type': 'accuracy',
                'title': 'Improve Calculation Accuracy',
                'description': f'Your accuracy of {accuracy:.1f}% needs improvement.',
                'specific_advice': 'Practice tactical puzzles daily and calculate 2-3 moves deeper.'
            })
        
        # Missed tactics recommendations
        if missed_tactics > 3:
            recommendations.append({
                'priority': 'medium',
                'type': 'tactical_vision',
                'title': 'Improve Tactical Vision',
                'description': f'You missed {missed_tactics} tactical opportunities.',
                'specific_advice': 'Look for forcing moves (checks, captures, threats) in every position.'
            })
        
        return recommendations


def main():
    """Example usage of the tactical analyzer."""
    analyzer = TacticalAnalyzer()
    
    # Example PGN (you would load this from your games)
    sample_pgn = """
    [Event "Sample Game"]
    [White "Player"]
    [Black "Opponent"]
    [Result "1-0"]
    
    1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 1-0
    """
    
    try:
        result = analyzer.analyze_game_tactics(sample_pgn, "Player")
        print("Tactical Analysis Results:")
        print(f"Blunders: {result['summary']['total_blunders']}")
        print(f"Mistakes: {result['summary']['total_mistakes']}")
        print(f"Accuracy: {result['summary']['accuracy']:.1f}%")
        
        recommendations = analyzer.get_tactical_recommendations(result)
        print("\nRecommendations:")
        for rec in recommendations:
            print(f"- {rec['title']}: {rec['description']}")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Stockfish is installed and the path is correct in your .env file")


if __name__ == "__main__":
    main()