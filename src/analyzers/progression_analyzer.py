
"""
Progression Analysis Module

This module analyzes how a player's chess capabilities and playing style
have evolved over time, tracking trends in various performance metrics.
"""

import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ProgressionAnalyzer:
    """Analyzes chess playing style evolution and capability progression over time."""
    
    def __init__(self):
        """Initialize the progression analyzer."""
        self.time_periods = ['3_months', '6_months', '1_year', 'all_time']
        self.metrics = [
            'rating_progression', 'accuracy_trends', 'tactical_improvement',
            'opening_evolution', 'time_management', 'opponent_strength',
            'game_phase_performance', 'consistency_metrics'
        ]
    
    def analyze_progression(self, games_data: List[Dict]) -> Dict:
        """
        Comprehensive analysis of player progression over time.
        
        Args:
            games_data: List of parsed game data sorted by date
            
        Returns:
            Dictionary containing all progression analysis results
        """
        if not games_data:
            return {}
        
        # Sort games by date
        sorted_games = self._sort_games_by_date(games_data)
        
        # Group games by time periods
        time_groups = self._group_games_by_time_periods(sorted_games)
        
        progression_data = {
            'rating_progression': self._analyze_rating_progression(sorted_games),
            'accuracy_trends': self._analyze_accuracy_trends(sorted_games),
            'tactical_improvement': self._analyze_tactical_improvement(sorted_games),
            'opening_evolution': self._analyze_opening_evolution(sorted_games),
            'time_management_evolution': self._analyze_time_management_evolution(sorted_games),
            'opponent_strength_progression': self._analyze_opponent_strength_progression(sorted_games),
            'game_phase_performance': self._analyze_game_phase_performance(sorted_games),
            'consistency_metrics': self._analyze_consistency_metrics(sorted_games),
            'playing_style_evolution': self._analyze_playing_style_evolution(sorted_games),
            'improvement_velocity': self._calculate_improvement_velocity(sorted_games),
            'time_periods': time_groups,
            'summary': {}
        }
        
        # Generate summary insights
        progression_data['summary'] = self._generate_progression_summary(progression_data)
        
        return progression_data
    
    def _sort_games_by_date(self, games_data: List[Dict]) -> List[Dict]:
        """Sort games by date, handling various date formats."""
        def get_game_date(game):
            metadata = game.get('game_metadata', {})
            date = metadata.get('date')
            if isinstance(date, str):
                try:
                    return datetime.strptime(date, '%Y-%m-%d')
                except:
                    try:
                        return datetime.strptime(date, '%Y.%m.%d')
                    except:
                        return datetime.min
            elif hasattr(date, 'year'):
                return date
            return datetime.min
        
        return sorted(games_data, key=get_game_date)
    
    def _group_games_by_time_periods(self, sorted_games: List[Dict]) -> Dict:
        """Group games by different time periods for comparison."""
        if not sorted_games:
            return {}
        
        now = datetime.now()
        periods = {
            'last_3_months': now - timedelta(days=90),
            'last_6_months': now - timedelta(days=180),
            'last_year': now - timedelta(days=365),
            'all_time': datetime.min
        }
        
        grouped = {}
        for period_name, cutoff_date in periods.items():
            grouped[period_name] = [
                game for game in sorted_games
                if self._get_game_datetime(game) >= cutoff_date
            ]
        
        # Also group by months for trend analysis
        monthly_groups = defaultdict(list)
        for game in sorted_games:
            game_date = self._get_game_datetime(game)
            month_key = f"{game_date.year}-{game_date.month:02d}"
            monthly_groups[month_key].append(game)
        
        grouped['monthly'] = dict(monthly_groups)
        return grouped
    
    def _get_game_datetime(self, game: Dict) -> datetime:
        """Extract datetime from game metadata."""
        metadata = game.get('game_metadata', {})
        date = metadata.get('date')
        if isinstance(date, str):
            try:
                return datetime.strptime(date, '%Y-%m-%d')
            except:
                try:
                    return datetime.strptime(date, '%Y.%m.%d')
                except:
                    return datetime.min
        elif hasattr(date, 'year'):
            return date
        return datetime.min
    
    def _analyze_rating_progression(self, sorted_games: List[Dict]) -> Dict:
        """Analyze rating progression over time."""
        rating_data = []
        
        for game in sorted_games:
            metadata = game.get('game_metadata', {})
            player_rating = metadata.get('player_rating', 0)
            date = self._get_game_datetime(game)
            
            if player_rating > 0:
                rating_data.append({
                    'date': date,
                    'rating': player_rating,
                    'result': metadata.get('result', '1/2')
                })
        
        if not rating_data:
            return {}
        
        # Calculate trends
        df = pd.DataFrame(rating_data)
        df = df.sort_values('date')
        
        # Calculate moving averages
        df['rating_ma_10'] = df['rating'].rolling(window=10, min_periods=1).mean()
        df['rating_ma_30'] = df['rating'].rolling(window=30, min_periods=1).mean()
        
        # Calculate rating changes
        df['rating_change'] = df['rating'].diff()
        
        # Peak and current ratings
        peak_rating = df['rating'].max()
        current_rating = df['rating'].iloc[-1] if len(df) > 0 else 0
        starting_rating = df['rating'].iloc[0] if len(df) > 0 else 0
        
        # Rating volatility
        rating_std = df['rating'].std()
        
        # Trend analysis (linear regression)
        if len(df) > 1:
            x = np.arange(len(df))
            slope, intercept = np.polyfit(x, df['rating'], 1)
            trend_direction = 'improving' if slope > 5 else 'declining' if slope < -5 else 'stable'
        else:
            slope = 0
            trend_direction = 'stable'
        
        return {
            'peak_rating': int(peak_rating),
            'current_rating': int(current_rating),
            'starting_rating': int(starting_rating),
            'total_gain': int(current_rating - starting_rating),
            'rating_volatility': round(rating_std, 1),
            'trend_slope': round(slope, 2),
            'trend_direction': trend_direction,
            'games_tracked': len(rating_data),
            'rating_history': df.to_dict('records')
        }
    
    def _analyze_accuracy_trends(self, sorted_games: List[Dict]) -> Dict:
        """Analyze accuracy improvement over time."""
        accuracy_data = []
        
        for game in sorted_games:
            tactical_analysis = game.get('tactical_analysis', {})
            summary = tactical_analysis.get('summary', {})
            accuracy = summary.get('accuracy', 0)
            
            if accuracy > 0:
                accuracy_data.append({
                    'date': self._get_game_datetime(game),
                    'accuracy': accuracy,
                    'blunders': summary.get('total_blunders', 0),
                    'mistakes': summary.get('total_mistakes', 0),
                    'inaccuracies': summary.get('total_inaccuracies', 0)
                })
        
        if not accuracy_data:
            return {}
        
        df = pd.DataFrame(accuracy_data)
        df = df.sort_values('date')
        
        # Calculate moving averages
        df['accuracy_ma_10'] = df['accuracy'].rolling(window=10, min_periods=1).mean()
        
        # Trend analysis
        if len(df) > 1:
            x = np.arange(len(df))
            slope, _ = np.polyfit(x, df['accuracy'], 1)
            trend = 'improving' if slope > 0.5 else 'declining' if slope < -0.5 else 'stable'
        else:
            slope = 0
            trend = 'stable'
        
        # Calculate periods
        recent_accuracy = df['accuracy'].tail(10).mean() if len(df) >= 10 else df['accuracy'].mean()
        early_accuracy = df['accuracy'].head(10).mean() if len(df) >= 10 else df['accuracy'].mean()
        
        return {
            'current_accuracy': round(recent_accuracy, 1),
            'starting_accuracy': round(early_accuracy, 1),
            'accuracy_improvement': round(recent_accuracy - early_accuracy, 1),
            'trend_slope': round(slope, 3),
            'trend_direction': trend,
            'best_accuracy': round(df['accuracy'].max(), 1),
            'worst_accuracy': round(df['accuracy'].min(), 1),
            'consistency': round(100 - df['accuracy'].std(), 1),
            'games_analyzed': len(accuracy_data)
        }
    
    def _analyze_tactical_improvement(self, sorted_games: List[Dict]) -> Dict:
        """Analyze tactical skill improvement over time."""
        tactical_data = []
        
        for game in sorted_games:
            tactical_analysis = game.get('tactical_analysis', {})
            summary = tactical_analysis.get('summary', {})
            
            if summary:
                tactical_data.append({
                    'date': self._get_game_datetime(game),
                    'blunders': summary.get('total_blunders', 0),
                    'mistakes': summary.get('total_mistakes', 0),
                    'inaccuracies': summary.get('total_inaccuracies', 0),
                    'good_moves': summary.get('total_good_moves', 0),
                    'missed_tactics': summary.get('total_missed_tactics', 0)
                })
        
        if not tactical_data:
            return {}
        
        df = pd.DataFrame(tactical_data)
        df = df.sort_values('date')
        
        # Calculate error rates per game
        df['error_rate'] = df['blunders'] + df['mistakes'] + df['inaccuracies']
        df['tactical_score'] = df['good_moves'] - df['error_rate']
        
        # Moving averages
        df['error_rate_ma'] = df['error_rate'].rolling(window=10, min_periods=1).mean()
        df['tactical_score_ma'] = df['tactical_score'].rolling(window=10, min_periods=1).mean()
        
        # Compare periods
        recent_period = df.tail(20) if len(df) >= 20 else df
        early_period = df.head(20) if len(df) >= 20 else df
        
        recent_error_rate = recent_period['error_rate'].mean()
        early_error_rate = early_period['error_rate'].mean()
        
        recent_missed_tactics = recent_period['missed_tactics'].mean()
        early_missed_tactics = early_period['missed_tactics'].mean()
        
        return {
            'current_error_rate': round(recent_error_rate, 1),
            'starting_error_rate': round(early_error_rate, 1),
            'error_rate_improvement': round(early_error_rate - recent_error_rate, 1),
            'current_missed_tactics': round(recent_missed_tactics, 1),
            'starting_missed_tactics': round(early_missed_tactics, 1),
            'tactical_vision_improvement': round(early_missed_tactics - recent_missed_tactics, 1),
            'best_tactical_game': int(df['tactical_score'].max()),
            'worst_tactical_game': int(df['tactical_score'].min()),
            'tactical_consistency': round(100 - df['tactical_score'].std(), 1)
        }
    
    def _analyze_opening_evolution(self, sorted_games: List[Dict]) -> Dict:
        """Analyze how opening repertoire has evolved."""
        # Split games into periods
        total_games = len(sorted_games)
        early_games = sorted_games[:total_games//3] if total_games >= 30 else sorted_games[:total_games//2]
        recent_games = sorted_games[-total_games//3:] if total_games >= 30 else sorted_games[-total_games//2:]
        
        def get_opening_stats(games):
            opening_counts = Counter()
            opening_performance = defaultdict(list)
            
            for game in games:
                opening_data = game.get('opening_analysis', {})
                opening_name = opening_data.get('opening_name', 'Unknown')
                result = game.get('game_metadata', {}).get('result', '1/2')
                
                opening_counts[opening_name] += 1
                score = 1 if result == '1' else 0.5 if result == '1/2' else 0
                opening_performance[opening_name].append(score)
            
            return opening_counts, opening_performance
        
        early_counts, early_performance = get_opening_stats(early_games)
        recent_counts, recent_performance = get_opening_stats(recent_games)
        
        # Calculate repertoire diversity
        early_diversity = len(early_counts)
        recent_diversity = len(recent_counts)
        
        # Find new openings
        early_openings = set(early_counts.keys())
        recent_openings = set(recent_counts.keys())
        new_openings = recent_openings - early_openings
        abandoned_openings = early_openings - recent_openings
        
        # Calculate performance changes
        performance_changes = {}
        for opening in early_openings & recent_openings:
            if len(early_performance[opening]) >= 3 and len(recent_performance[opening]) >= 3:
                early_score = sum(early_performance[opening]) / len(early_performance[opening]) * 100
                recent_score = sum(recent_performance[opening]) / len(recent_performance[opening]) * 100
                performance_changes[opening] = recent_score - early_score
        
        return {
            'repertoire_expansion': recent_diversity - early_diversity,
            'early_diversity': early_diversity,
            'recent_diversity': recent_diversity,
            'new_openings': list(new_openings),
            'abandoned_openings': list(abandoned_openings),
            'performance_changes': performance_changes,
            'most_improved_opening': max(performance_changes.items(), key=lambda x: x[1]) if performance_changes else None,
            'most_declined_opening': min(performance_changes.items(), key=lambda x: x[1]) if performance_changes else None
        }
    
    def _analyze_time_management_evolution(self, sorted_games: List[Dict]) -> Dict:
        """Analyze how time management has evolved."""
        time_data = []
        
        for game in sorted_games:
            metadata = game.get('game_metadata', {})
            time_control = metadata.get('time_control', '')
            time_class = metadata.get('time_class', '')
            
            # Extract time usage data if available
            if 'time_analysis' in game:
                time_analysis = game['time_analysis']
                time_data.append({
                    'date': self._get_game_datetime(game),
                    'time_control': time_control,
                    'time_class': time_class,
                    'avg_move_time': time_analysis.get('avg_move_time', 0),
                    'time_pressure_moves': time_analysis.get('time_pressure_moves', 0),
                    'time_efficiency': time_analysis.get('time_efficiency', 0)
                })
        
        if not time_data:
            return {'status': 'no_time_data'}
        
        df = pd.DataFrame(time_data)
        
        # Group by time control
        time_control_evolution = {}
        for tc in df['time_class'].unique():
            tc_data = df[df['time_class'] == tc].sort_values('date')
            if len(tc_data) >= 5:
                early_avg = tc_data['avg_move_time'].head(10).mean()
                recent_avg = tc_data['avg_move_time'].tail(10).mean()
                
                time_control_evolution[tc] = {
                    'early_avg_move_time': round(early_avg, 1),
                    'recent_avg_move_time': round(recent_avg, 1),
                    'improvement': round(early_avg - recent_avg, 1)
                }
        
        return {
            'time_control_evolution': time_control_evolution,
            'games_with_time_data': len(time_data)
        }
    
    def _analyze_opponent_strength_progression(self, sorted_games: List[Dict]) -> Dict:
        """Analyze progression in opponent strength faced."""
        opponent_data = []
        
        for game in sorted_games:
            metadata = game.get('game_metadata', {})
            opponent_rating = metadata.get('opponent_rating', 0)
            player_rating = metadata.get('player_rating', 0)
            result = metadata.get('result', '1/2')
            
            if opponent_rating > 0 and player_rating > 0:
                rating_diff = opponent_rating - player_rating
                score = 1 if result == '1' else 0.5 if result == '1/2' else 0
                
                opponent_data.append({
                    'date': self._get_game_datetime(game),
                    'opponent_rating': opponent_rating,
                    'player_rating': player_rating,
                    'rating_difference': rating_diff,
                    'score': score
                })
        
        if not opponent_data:
            return {}
        
        df = pd.DataFrame(opponent_data)
        df = df.sort_values('date')
        
        # Calculate moving averages
        df['opponent_rating_ma'] = df['opponent_rating'].rolling(window=20, min_periods=1).mean()
        df['rating_diff_ma'] = df['rating_difference'].rolling(window=20, min_periods=1).mean()
        
        # Performance against different strength levels
        stronger_opponents = df[df['rating_difference'] > 100]
        weaker_opponents = df[df['rating_difference'] < -100]
        similar_opponents = df[abs(df['rating_difference']) <= 100]
        
        return {
            'avg_opponent_rating': round(df['opponent_rating'].mean()),
            'opponent_rating_trend': round(df['opponent_rating_ma'].iloc[-1] - df['opponent_rating_ma'].iloc[0], 1),
            'performance_vs_stronger': round(stronger_opponents['score'].mean() * 100, 1) if len(stronger_opponents) > 0 else 0,
            'performance_vs_weaker': round(weaker_opponents['score'].mean() * 100, 1) if len(weaker_opponents) > 0 else 0,
            'performance_vs_similar': round(similar_opponents['score'].mean() * 100, 1) if len(similar_opponents) > 0 else 0,
            'games_vs_stronger': len(stronger_opponents),
            'games_vs_weaker': len(weaker_opponents),
            'games_vs_similar': len(similar_opponents)
        }
    
    def _analyze_game_phase_performance(self, sorted_games: List[Dict]) -> Dict:
        """Analyze performance evolution in different game phases."""
        phase_data = {
            'opening': [],
            'middlegame': [],
            'endgame': []
        }
        
        for game in sorted_games:
            tactical_analysis = game.get('tactical_analysis', {})
            move_evaluations = tactical_analysis.get('move_evaluations', [])
            
            if not move_evaluations:
                continue
            
            # Categorize moves by game phase
            opening_moves = [m for m in move_evaluations if m.get('move_number', 0) <= 15]
            middlegame_moves = [m for m in move_evaluations if 15 < m.get('move_number', 0) <= 40]
            endgame_moves = [m for m in move_evaluations if m.get('move_number', 0) > 40]
            
            date = self._get_game_datetime(game)
            
            for phase, moves in [('opening', opening_moves), ('middlegame', middlegame_moves), ('endgame', endgame_moves)]:
                if moves:
                    avg_eval_change = sum(m.get('eval_change', 0) for m in moves) / len(moves)
                    error_count = sum(1 for m in moves if m.get('eval_change', 0) < -50)
                    
                    phase_data[phase].append({
                        'date': date,
                        'avg_eval_change': avg_eval_change,
                        'error_count': error_count,
                        'move_count': len(moves)
                    })
        
        # Calculate trends for each phase
        phase_trends = {}
        for phase, data in phase_data.items():
            if len(data) >= 10:
                df = pd.DataFrame(data).sort_values('date')
                
                # Calculate improvement
                early_performance = df['avg_eval_change'].head(10).mean()
                recent_performance = df['avg_eval_change'].tail(10).mean()
                
                early_errors = df['error_count'].head(10).mean()
                recent_errors = df['error_count'].tail(10).mean()
                
                phase_trends[phase] = {
                    'performance_change': round(recent_performance - early_performance, 1),
                    'error_reduction': round(early_errors - recent_errors, 1),
                    'games_analyzed': len(data)
                }
        
        return phase_trends
    
    def _analyze_consistency_metrics(self, sorted_games: List[Dict]) -> Dict:
        """Analyze consistency in performance over time."""
        performance_data = []
        
        for game in sorted_games:
            metadata = game.get('game_metadata', {})
            tactical_analysis = game.get('tactical_analysis', {})
            
            result = metadata.get('result', '1/2')
            score = 1 if result == '1' else 0.5 if result == '1/2' else 0
            
            accuracy = tactical_analysis.get('summary', {}).get('accuracy', 0)
            
            performance_data.append({
                'date': self._get_game_datetime(game),
                'score': score,
                'accuracy': accuracy
            })
        
        if len(performance_data) < 10:
            return {}
        
        df = pd.DataFrame(performance_data).sort_values('date')
        
        # Calculate rolling statistics
        df['score_ma_10'] = df['score'].rolling(window=10).mean()
        df['accuracy_ma_10'] = df['accuracy'].rolling(window=10).mean()
        
        # Calculate consistency metrics
        score_std = df['score'].std()
        accuracy_std = df['accuracy'].std()
        
        # Streak analysis
        df['win_streak'] = (df['score'] == 1).astype(int).groupby((df['score'] != 1).cumsum()).cumsum()
        df['loss_streak'] = (df['score'] == 0).astype(int).groupby((df['score'] != 0).cumsum()).cumsum()
        
        max_win_streak = df['win_streak'].max()
        max_loss_streak = df['loss_streak'].max()
        
        return {
            'score_consistency': round(100 - (score_std * 100), 1),
            'accuracy_consistency': round(100 - accuracy_std, 1),
            'max_win_streak': int(max_win_streak),
            'max_loss_streak': int(max_loss_streak),
            'performance_volatility': round(score_std, 3)
        }
    
    def _analyze_playing_style_evolution(self, sorted_games: List[Dict]) -> Dict:
        """Analyze how playing style has evolved."""
        # This would analyze patterns like:
        # - Aggression vs defensive play
        # - Tactical vs positional preferences
        # - Risk-taking tendencies
        # - Game length preferences
        
        style_data = []
        
        for game in sorted_games:
            metadata = game.get('game_metadata', {})
            tactical_analysis = game.get('tactical_analysis', {})
            
            # Calculate style indicators
            total_moves = len(tactical_analysis.get('move_evaluations', []))
            aggressive_moves = len([m for m in tactical_analysis.get('move_evaluations', []) 
                                  if m.get('eval_change', 0) > 50])  # Risk-taking moves
            
            style_data.append({
                'date': self._get_game_datetime(game),
                'game_length': total_moves,
                'aggression_rate': aggressive_moves / max(total_moves, 1),
                'time_class': metadata.get('time_class', 'unknown')
            })
        
        if len(style_data) < 10:
            return {}
        
        df = pd.DataFrame(style_data).sort_values('date')
        
        # Compare early vs recent style
        early_period = df.head(len(df)//3)
        recent_period = df.tail(len(df)//3)
        
        return {
            'game_length_change': round(recent_period['game_length'].mean() - early_period['game_length'].mean(), 1),
            'aggression_change': round((recent_period['aggression_rate'].mean() - early_period['aggression_rate'].mean()) * 100, 2),
            'style_evolution': 'more_aggressive' if recent_period['aggression_rate'].mean() > early_period['aggression_rate'].mean() else 'more_cautious'
        }
    
    def _calculate_improvement_velocity(self, sorted_games: List[Dict]) -> Dict:
        """Calculate the rate of improvement across different metrics."""
        if len(sorted_games) < 20:
            return {}
        
        # Sample games at regular intervals
        sample_size = min(50, len(sorted_games))
        step = len(sorted_games) // sample_size
        sampled_games = sorted_games[::step]
        
        metrics_over_time = []
        
        for i, game in enumerate(sampled_games):
            tactical_analysis = game.get('tactical_analysis', {})
            summary = tactical_analysis.get('summary', {})
            
            metrics_over_time.append({
                'game_index': i,
                'accuracy': summary.get('accuracy', 0),
                'error_rate': summary.get('total_blunders', 0) + summary.get('total_mistakes', 0),
                'tactical_score': summary.get('total_good_moves', 0) - summary.get('total_blunders', 0)
            })
        
        if len(metrics_over_time) < 10:
            return {}
        
        df = pd.DataFrame(metrics_over_time)
        
        # Calculate improvement rates (linear regression slopes)
        x = df['game_index'].values
        
        improvement_rates = {}
        for metric in ['accuracy', 'error_rate', 'tactical_score']:
            if df[metric].std() > 0:  # Only if there's variation
                slope, _ = np.polyfit(x.astype(float), df[metric].astype(float), 1)
                improvement_rates[metric] = round(slope, 4)
        
        return improvement_rates
    
    def _generate_progression_summary(self, progression_data: Dict) -> Dict:
        """Generate a summary of key progression insights."""
        summary = {
            'overall_trend': 'stable',
            'strongest_improvement': None,
            'areas_needing_work': [],
            'key_insights': []
        }
        
        # Analyze rating progression
        rating_data = progression_data.get('rating_progression', {})
        if rating_data:
            total_gain = rating_data.get('total_gain', 0)
            if total_gain > 100:
                summary['overall_trend'] = 'strong_improvement'
                summary['key_insights'].append(f"Rating improved by {total_gain} points")
            elif total_gain > 50:
                summary['overall_trend'] = 'moderate_improvement'
            elif total_gain < -50:
                summary['overall_trend'] = 'declining'
        
        # Analyze accuracy trends
        accuracy_data = progression_data.get('accuracy_trends', {})
        if accuracy_data:
            accuracy_improvement = accuracy_data.get('accuracy_improvement', 0)
            if accuracy_improvement > 5:
                summary['key_insights'].append(f"Accuracy improved by {accuracy_improvement:.1f}%")
            elif accuracy_improvement < -5:
                summary['areas_needing_work'].append('Accuracy declining')
        
        # Analyze tactical improvement
        tactical_data = progression_data.get('tactical_improvement', {})
        if tactical_data:
            error_improvement = tactical_data.get('error_rate_improvement', 0)
            if error_improvement > 1:
                summary['key_insights'].append(f"Error rate reduced by {error_improvement:.1f} per game")
        
        # Analyze opening evolution
        opening_data = progression_data.get('opening_evolution', {})
        if opening_data:
            repertoire_expansion = opening_data.get('repertoire_expansion', 0)
            if repertoire_expansion > 2:
                summary['key_insights'].append(f"Expanded opening repertoire by {repertoire_expansion} openings")
        
        return summary
    
    def get_progression_recommendations(self, progression_data: Dict) -> List[Dict]:
        """Generate recommendations based on progression analysis."""
        recommendations = []
        
        # Rating progression recommendations
        rating_data = progression_data.get('rating_progression', {})
        if rating_data.get('trend_direction') == 'declining':
            recommendations.append({
                'priority': 'high',
                'type': 'rating_recovery',
                'title': 'Address Rating Decline',
                'description': f"Your rating has declined by {abs(rating_data.get('total_gain', 0))} points. Focus on fundamentals.",
                'specific_advice': 'Review recent losses, practice tactics daily, and consider studying endgames.'
            })
        
        # Accuracy recommendations
        accuracy_data = progression_data.get('accuracy_trends', {})
        if accuracy_data.get('accuracy_improvement', 0) < 0:
            recommendations.append({
                'priority': 'high',
                'type': 'accuracy_improvement',
                'title': 'Improve Calculation Accuracy',
                'description': f"Your accuracy has declined by {abs(accuracy_data.get('accuracy_improvement', 0)):.1f}%. Focus on calculation training.",
                'specific_advice': 'Practice tactical puzzles daily and slow down your calculation process.'
            })
        
        # Tactical improvement recommendations
        tactical_data = progression_data.get('tactical_improvement', {})
        if tactical_data.get('error_rate_improvement', 0) < 0:
            recommendations.append({
                'priority': 'medium',
                'type': 'tactical_training',
                'title': 'Reduce Tactical Errors',
                'description': 'Your error rate has increased. Focus on tactical pattern recognition.',
                'specific_advice': 'Spend 15-20 minutes daily on tactical puzzles and review your blunders.'
            })
        
        # Opening evolution recommendations
        opening_data = progression_data.get('opening_evolution', {})
        if opening_data.get('repertoire_expansion', 0) < 0:
            recommendations.append({
                'priority': 'low',
                'type': 'opening_study',
                'title': 'Expand Opening Repertoire',
                'description': 'Your opening repertoire has become narrower. Consider learning new openings.',
                'specific_advice': 'Study 1-2 new opening systems to add variety to your play.'
            })
        
        # Consistency recommendations
        consistency_data = progression_data.get('consistency_metrics', {})
        if consistency_data.get('performance_volatility', 0) > 0.3:
            recommendations.append({
                'priority': 'medium',
                'type': 'consistency',
                'title': 'Improve Consistency',
                'description': 'Your performance varies significantly between games.',
                'specific_advice': 'Focus on maintaining the same preparation routine and mindset for each game.'
            })
        
        return recommendations


def main():
    """Example usage of the progression analyzer."""
    import json
    import os
    from config.settings import Config
    
    # Load parsed games
    processed_data_path = os.path.join(Config.PROCESSED_DATA_DIR, "parsed_games.json")
    
    if os.path.exists(processed_data_path):
        with open(processed_data_path, 'r') as f:
            games_data = json.load(f)
        
        analyzer = ProgressionAnalyzer()
        
        # Analyze progression
        progression_analysis = analyzer.analyze_progression(games_data)
        
        print("Chess Progression Analysis:")
        print("=" * 50)
        
        # Rating progression
        rating_data = progression_analysis.get('rating_progression', {})
        if rating_data:
            print(f"\n📈 Rating Progression:")
            print(f"  Starting Rating: {rating_data.get('starting_rating', 0)}")
            print(f"  Current Rating: {rating_data.get('current_rating', 0)}")
            print(f"  Total Gain: {rating_data.get('total_gain', 0)}")
            print(f"  Peak Rating: {rating_data.get('peak_rating', 0)}")
            print(f"  Trend: {rating_data.get('trend_direction', 'unknown')}")
        
        # Accuracy trends
        accuracy_data = progression_analysis.get('accuracy_trends', {})
        if accuracy_data:
            print(f"\n🎯 Accuracy Trends:")
            print(f"  Starting Accuracy: {accuracy_data.get('starting_accuracy', 0):.1f}%")
            print(f"  Current Accuracy: {accuracy_data.get('current_accuracy', 0):.1f}%")
            print(f"  Improvement: {accuracy_data.get('accuracy_improvement', 0):.1f}%")
            print(f"  Trend: {accuracy_data.get('trend_direction', 'unknown')}")
        
        # Tactical improvement
        tactical_data = progression_analysis.get('tactical_improvement', {})
        if tactical_data:
            print(f"\n⚔️ Tactical Improvement:")
            print(f"  Error Rate Change: {tactical_data.get('error_rate_improvement', 0):.1f}")
            print(f"  Tactical Vision Improvement: {tactical_data.get('tactical_vision_improvement', 0):.1f}")
        
        # Opening evolution
        opening_data = progression_analysis.get('opening_evolution', {})
        if opening_data:
            print(f"\n📚 Opening Evolution:")
            print(f"  Repertoire Expansion: {opening_data.get('repertoire_expansion', 0)}")
            print(f"  New Openings: {len(opening_data.get('new_openings', []))}")
            print(f"  Abandoned Openings: {len(opening_data.get('abandoned_openings', []))}")
        
        # Get recommendations
        recommendations = analyzer.get_progression_recommendations(progression_analysis)
        
        print(f"\n🎯 Progression Recommendations:")
        print("=" * 50)
        
        for rec in recommendations:
            print(f"\n{rec['title']} ({rec['priority']} priority)")
            print(f"  {rec['description']}")
            print(f"  💡 {rec['specific_advice']}")
        
        # Summary
        summary = progression_analysis.get('summary', {})
        if summary:
            print(f"\n📊 Summary:")
            print(f"  Overall Trend: {summary.get('overall_trend', 'unknown')}")
            for insight in summary.get('key_insights', []):
                print(f"  ✅ {insight}")
            for area in summary.get('areas_needing_work', []):
                print(f"  ⚠️ {area}")
        
    else:
        print(f"No parsed games found at {processed_data_path}")
        print("Run the game parser first to process games")


if __name__ == "__main__":
    main()