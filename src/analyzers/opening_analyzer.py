"""
Opening Analysis Module

This module analyzes chess opening performance, including success rates,
preparation depth, and repertoire analysis.
"""

import pandas as pd
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class OpeningAnalyzer:
    """Analyzes chess opening performance from parsed game data."""
    
    def __init__(self):
        """Initialize the opening analyzer."""
        self.opening_database = self._load_opening_database()
    
    def _load_opening_database(self) -> Dict[str, Dict]:
        """
        Load opening database with ECO codes and variations.
        
        Returns:
            Dictionary mapping ECO codes to opening information
        """
        # Simplified opening database - in a real implementation,
        # this would be loaded from a comprehensive database
        return {
            # Major opening categories
            'B20': {'name': 'Sicilian Defense', 'category': 'Semi-Open'},
            'B90': {'name': 'Sicilian Defense: Najdorf Variation', 'category': 'Semi-Open'},
            'C60': {'name': 'Ruy Lopez', 'category': 'Open'},
            'C89': {'name': 'Ruy Lopez: Marshall Attack', 'category': 'Open'},
            'C00': {'name': 'French Defense', 'category': 'Semi-Closed'},
            'B10': {'name': 'Caro-Kann Defense', 'category': 'Semi-Open'},
            'B01': {'name': 'Scandinavian Defense', 'category': 'Open'},
            'B02': {'name': 'Alekhine Defense', 'category': 'Hypermodern'},
            'A10': {'name': 'English Opening', 'category': 'Flank'},
            'A04': {'name': 'Reti Opening', 'category': 'Hypermodern'},
            'D00': {'name': 'Queen Pawn Game', 'category': 'Closed'},
            'D20': {'name': 'Queen Gambit Accepted', 'category': 'Closed'},
            'D30': {'name': 'Queen Gambit Declined', 'category': 'Closed'},
            'E60': {'name': 'King Indian Defense', 'category': 'Indian'},
            'E20': {'name': 'Nimzo-Indian Defense', 'category': 'Indian'},
            'A40': {'name': 'Queen Pawn Game', 'category': 'Closed'},
            'C50': {'name': 'Italian Game', 'category': 'Open'},
            'C42': {'name': 'Petrov Defense', 'category': 'Open'},
            'C45': {'name': 'Scotch Game', 'category': 'Open'},
            'B06': {'name': 'Modern Defense', 'category': 'Hypermodern'},
            'B07': {'name': 'Pirc Defense', 'category': 'Hypermodern'},
        }
    
    def analyze_opening_performance(self, games_data: List[Dict]) -> Dict:
        """
        Analyze opening performance across all games.
        
        Args:
            games_data: List of parsed game data
            
        Returns:
            Dictionary containing opening analysis results
        """
        if not games_data:
            return {}
        
        # Extract opening data from games
        opening_stats = {}
        
        for game in games_data:
            opening_data = game.get('opening_analysis', {})
            metadata = game.get('game_metadata', {})
            
            opening_name = opening_data.get('opening_name', 'Unknown')
            eco_code = opening_data.get('eco_code', '')
            
            # Use ECO code if available, otherwise use opening name
            opening_key = eco_code if eco_code else opening_name
            
            # Initialize stats if not exists
            if opening_key not in opening_stats:
                opening_stats[opening_key] = {
                    'games': [],
                    'wins': 0,
                    'draws': 0,
                    'losses': 0,
                    'total_games': 0,
                    'avg_opponent_rating': 0,
                    'preparation_depths': [],
                    'first_inaccuracies': []
                }
            
            stats = opening_stats[opening_key]
            stats['games'].append(game)
            stats['total_games'] += 1
            
            # Count results
            result = metadata.get('result', '1/2')
            if result == '1':
                stats['wins'] += 1
            elif result == '0':
                stats['losses'] += 1
            else:
                stats['draws'] += 1
            
            # Track opponent ratings
            opponent_rating = metadata.get('opponent_rating', 0)
            if opponent_rating > 0:
                stats['avg_opponent_rating'] += opponent_rating
            
            # Track preparation depth
            moves_in_theory = opening_data.get('moves_in_theory', 0)
            if moves_in_theory > 0:
                stats['preparation_depths'].append(moves_in_theory)
            
            # Track first inaccuracy
            first_inaccuracy = opening_data.get('first_inaccuracy_move')
            if first_inaccuracy:
                stats['first_inaccuracies'].append(first_inaccuracy)
        
        # Calculate final statistics
        results = {}
        for opening, stats in opening_stats.items():
            if stats['total_games'] == 0:
                continue
            
            win_rate = stats['wins'] / stats['total_games'] * 100
            draw_rate = stats['draws'] / stats['total_games'] * 100
            loss_rate = stats['losses'] / stats['total_games'] * 100
            
            avg_opponent_rating = stats['avg_opponent_rating'] / stats['total_games'] if stats['total_games'] > 0 else 0
            avg_preparation_depth = sum(stats['preparation_depths']) / len(stats['preparation_depths']) if stats['preparation_depths'] else 0
            avg_first_inaccuracy = sum(stats['first_inaccuracies']) / len(stats['first_inaccuracies']) if stats['first_inaccuracies'] else 0
            
            # Get opening category
            opening_info = self.opening_database.get(opening, {'name': opening, 'category': 'Other'})
            
            results[opening] = {
                'name': opening_info['name'],
                'category': opening_info['category'],
                'total_games': stats['total_games'],
                'win_rate': round(win_rate, 1),
                'draw_rate': round(draw_rate, 1),
                'loss_rate': round(loss_rate, 1),
                'score_percentage': round((stats['wins'] + stats['draws'] * 0.5) / stats['total_games'] * 100, 1),
                'avg_opponent_rating': round(avg_opponent_rating),
                'avg_preparation_depth': round(avg_preparation_depth, 1),
                'avg_first_inaccuracy_move': round(avg_first_inaccuracy, 1) if avg_first_inaccuracy > 0 else None,
                'games': stats['games']
            }
        
        return results
    
    def get_opening_recommendations(self, opening_analysis: Dict) -> List[Dict]:
        """
        Generate opening recommendations based on performance analysis.
        
        Args:
            opening_analysis: Results from analyze_opening_performance
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        if not opening_analysis:
            return recommendations
        
        # Sort openings by number of games played
        sorted_openings = sorted(
            opening_analysis.items(),
            key=lambda x: x[1]['total_games'],
            reverse=True
        )
        
        # Find best and worst performing openings
        best_openings = []
        worst_openings = []
        
        for opening, stats in sorted_openings:
            if stats['total_games'] >= 5:  # Only consider openings with sufficient games
                if stats['score_percentage'] >= 60:
                    best_openings.append((opening, stats))
                elif stats['score_percentage'] <= 40:
                    worst_openings.append((opening, stats))
        
        # Recommendations for best openings
        if best_openings:
            best_opening = best_openings[0]
            recommendations.append({
                'type': 'strength',
                'priority': 'high',
                'title': f"Your strongest opening: {best_opening[1]['name']}",
                'description': f"You score {best_opening[1]['score_percentage']}% with this opening "
                             f"({best_opening[1]['total_games']} games). Consider playing it more often.",
                'opening': best_opening[0],
                'stats': best_opening[1]
            })
        
        # Recommendations for worst openings
        if worst_openings:
            worst_opening = worst_openings[0]
            recommendations.append({
                'type': 'weakness',
                'priority': 'high',
                'title': f"Opening to improve: {worst_opening[1]['name']}",
                'description': f"You score only {worst_opening[1]['score_percentage']}% with this opening "
                             f"({worst_opening[1]['total_games']} games). Consider studying this opening more.",
                'opening': worst_opening[0],
                'stats': worst_opening[1]
            })
        
        # Preparation depth recommendations
        shallow_prep_openings = [
            (opening, stats) for opening, stats in sorted_openings
            if stats['total_games'] >= 3 and stats['avg_preparation_depth'] < 8
        ]
        
        if shallow_prep_openings:
            opening, stats = shallow_prep_openings[0]
            recommendations.append({
                'type': 'preparation',
                'priority': 'medium',
                'title': f"Improve preparation in {stats['name']}",
                'description': f"Your average preparation depth is only {stats['avg_preparation_depth']} moves. "
                             f"Study more theory to improve your opening play.",
                'opening': opening,
                'stats': stats
            })
        
        # Color-specific recommendations
        white_openings = []
        black_openings = []
        
        for opening, stats in sorted_openings:
            if stats['total_games'] >= 3:
                # This is simplified - would need to track color in game data
                if opening in ['C60', 'C89', 'D20', 'D30', 'C50', 'C45']:  # Typical white openings
                    white_openings.append((opening, stats))
                else:  # Typical black openings
                    black_openings.append((opening, stats))
        
        # Repertoire diversity recommendation
        total_games = sum(stats['total_games'] for _, stats in sorted_openings)
        if total_games > 20:
            top_3_games = sum(stats['total_games'] for _, stats in sorted_openings[:3])
            if top_3_games / total_games > 0.8:
                recommendations.append({
                    'type': 'diversity',
                    'priority': 'low',
                    'title': "Consider expanding your opening repertoire",
                    'description': f"You play your top 3 openings in {top_3_games/total_games*100:.0f}% of games. "
                                 f"Adding variety could make you less predictable.",
                    'opening': None,
                    'stats': None
                })
        
        return recommendations
    
    def get_opening_trends(self, games_data: List[Dict]) -> Dict:
        """
        Analyze opening performance trends over time.
        
        Args:
            games_data: List of parsed game data
            
        Returns:
            Dictionary containing trend analysis
        """
        if not games_data:
            return {}
        
        # Sort games by date
        sorted_games = sorted(
            games_data,
            key=lambda x: x.get('game_metadata', {}).get('date', ''),
            reverse=False
        )
        
        # Group games by month
        monthly_data = defaultdict(lambda: defaultdict(list))
        
        for game in sorted_games:
            date = game.get('game_metadata', {}).get('date')
            if not date:
                continue
            
            month_key = f"{date.year}-{date.month:02d}"
            opening = game.get('opening_analysis', {}).get('opening_name', 'Unknown')
            
            monthly_data[month_key][opening].append(game)
        
        # Calculate monthly statistics
        trends = {}
        for month, openings in monthly_data.items():
            month_stats = {}
            total_games = sum(len(games) for games in openings.values())
            
            for opening, games in openings.items():
                if len(games) >= 2:  # Only include openings with multiple games
                    wins = sum(1 for game in games 
                             if game.get('game_metadata', {}).get('result') == '1')
                    score_pct = (wins + sum(0.5 for game in games 
                                          if game.get('game_metadata', {}).get('result') == '1/2')) / len(games) * 100
                    
                    month_stats[opening] = {
                        'games': len(games),
                        'score_percentage': round(score_pct, 1),
                        'frequency': round(len(games) / total_games * 100, 1)
                    }
            
            if month_stats:
                trends[month] = month_stats
        
        return trends
    
    def analyze_color_preferences(self, games_data: List[Dict]) -> Dict:
        """
        Analyze opening preferences by color.
        
        Args:
            games_data: List of parsed game data
            
        Returns:
            Dictionary with color-specific opening analysis
        """
        white_games = []
        black_games = []
        
        for game in games_data:
            color = game.get('game_metadata', {}).get('player_color', '')
            if color == 'white':
                white_games.append(game)
            elif color == 'black':
                black_games.append(game)
        
        return {
            'white': self.analyze_opening_performance(white_games),
            'black': self.analyze_opening_performance(black_games),
            'white_games': len(white_games),
            'black_games': len(black_games)
        }


def main():
    """Example usage of the opening analyzer."""
    import json
    import os
    from config.settings import Config
    
    # Load parsed games
    processed_data_path = os.path.join(Config.PROCESSED_DATA_DIR, "parsed_games.json")
    
    if os.path.exists(processed_data_path):
        with open(processed_data_path, 'r') as f:
            games_data = json.load(f)
        
        analyzer = OpeningAnalyzer()
        
        # Analyze opening performance
        opening_analysis = analyzer.analyze_opening_performance(games_data)
        
        print("Opening Performance Analysis:")
        print("=" * 50)
        
        # Sort by number of games
        sorted_openings = sorted(
            opening_analysis.items(),
            key=lambda x: x[1]['total_games'],
            reverse=True
        )
        
        for opening, stats in sorted_openings[:10]:  # Top 10 most played
            print(f"\n{stats['name']} ({opening}):")
            print(f"  Games: {stats['total_games']}")
            print(f"  Score: {stats['score_percentage']}%")
            print(f"  Win Rate: {stats['win_rate']}%")
            print(f"  Avg Opponent Rating: {stats['avg_opponent_rating']}")
            print(f"  Avg Preparation Depth: {stats['avg_preparation_depth']}")
        
        # Get recommendations
        recommendations = analyzer.get_opening_recommendations(opening_analysis)
        
        print("\n\nRecommendations:")
        print("=" * 50)
        
        for rec in recommendations:
            print(f"\n{rec['title']} ({rec['priority']} priority)")
            print(f"  {rec['description']}")
        
        # Analyze by color
        color_analysis = analyzer.analyze_color_preferences(games_data)
        
        print(f"\n\nColor Analysis:")
        print("=" * 50)
        print(f"White games: {color_analysis['white_games']}")
        print(f"Black games: {color_analysis['black_games']}")
        
    else:
        print(f"No parsed games found at {processed_data_path}")
        print("Run the game parser first to process games")


if __name__ == "__main__":
    main()