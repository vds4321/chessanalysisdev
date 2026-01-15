"""
Opening Recommendation Engine

A production-ready recommendation system for chess openings using
collaborative filtering and content-based approaches.

This demonstrates ML engineering concepts applicable to marketplace recommendations:
- Feature engineering from game data
- Similarity-based recommendations
- Personalized ranking
- A/B testing framework
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class OpeningRecommender:
    """
    Recommends chess openings based on player performance and style.

    Analogous to e-commerce item recommendation systems:
    - Content-based filtering: Recommend openings similar to successful ones
    - Collaborative filtering: Recommend openings used by similar players
    - Hybrid approach: Combine multiple signals for better recommendations
    """

    def __init__(self):
        self.opening_features = None
        self.player_features = None
        self.opening_similarity_matrix = None

    def extract_opening_features(self, games_data: List[Dict]) -> pd.DataFrame:
        """
        Extract features for each opening variation.

        Features include:
        - Performance metrics: win rate, draw rate, average accuracy
        - Complexity: average game length, branching factor
        - Tactical nature: tactics per game, blunder rate
        - Positional: material imbalance tendency, pawn structure type

        Similar to: Extracting item features in e-commerce (category, price, brand)

        Args:
            games_data: List of parsed games with opening information

        Returns:
            DataFrame with opening features
        """
        opening_stats = defaultdict(lambda: {
            'games': 0,
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'total_moves': 0,
            'total_accuracy': 0,
            'blunders': 0,
            'tactical_opportunities': 0,
            'avg_rating_diff': []
        })

        for game in games_data:
            opening = game.get('opening_analysis', {}).get('opening_name', 'Unknown')
            result = game.get('game_metadata', {}).get('result', '')
            player_color = game.get('game_metadata', {}).get('player_color', '')

            stats = opening_stats[opening]
            stats['games'] += 1

            # Performance features
            if result == 'win':
                stats['wins'] += 1
            elif result == 'draw':
                stats['draws'] += 1
            else:
                stats['losses'] += 1

            # Complexity features
            game_stats = game.get('statistics', {})
            stats['total_moves'] += game_stats.get('total_moves', 0)
            stats['total_accuracy'] += game_stats.get('accuracy', 0)
            stats['blunders'] += game_stats.get('blunders', 0)
            stats['tactical_opportunities'] += game_stats.get('missed_tactics', 0)

            # Contextual features
            rating_diff = game.get('game_metadata', {}).get('rating_difference', 0)
            stats['avg_rating_diff'].append(rating_diff)

        # Convert to feature vectors
        features = []
        for opening, stats in opening_stats.items():
            if stats['games'] < 3:  # Minimum games threshold
                continue

            features.append({
                'opening': opening,
                'win_rate': stats['wins'] / stats['games'],
                'draw_rate': stats['draws'] / stats['games'],
                'avg_game_length': stats['total_moves'] / stats['games'],
                'avg_accuracy': stats['total_accuracy'] / stats['games'],
                'blunder_rate': stats['blunders'] / stats['games'],
                'tactical_density': stats['tactical_opportunities'] / stats['games'],
                'avg_rating_diff': np.mean(stats['avg_rating_diff']) if stats['avg_rating_diff'] else 0,
                'sample_size': stats['games']
            })

        self.opening_features = pd.DataFrame(features)
        logger.info(f"Extracted features for {len(self.opening_features)} openings")

        return self.opening_features

    def compute_opening_similarity(self) -> np.ndarray:
        """
        Compute similarity matrix between openings using cosine similarity.

        Similar to: Computing item-item similarity in collaborative filtering

        Returns:
            Similarity matrix (n_openings x n_openings)
        """
        if self.opening_features is None:
            raise ValueError("Must call extract_opening_features first")

        # Select numerical features for similarity computation
        feature_cols = ['win_rate', 'avg_game_length', 'avg_accuracy',
                       'blunder_rate', 'tactical_density']

        feature_matrix = self.opening_features[feature_cols].values

        # Normalize features (important for cosine similarity)
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        normalized_features = scaler.fit_transform(feature_matrix)

        # Compute pairwise similarity
        self.opening_similarity_matrix = cosine_similarity(normalized_features)

        logger.info("Computed opening similarity matrix")
        return self.opening_similarity_matrix

    def get_similar_openings(self, opening_name: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find openings similar to the given opening.

        Similar to: "Customers who liked this also liked..." in e-commerce

        Args:
            opening_name: Name of the opening
            top_k: Number of similar openings to return

        Returns:
            List of (opening_name, similarity_score) tuples
        """
        if self.opening_similarity_matrix is None:
            self.compute_opening_similarity()

        try:
            idx = self.opening_features[
                self.opening_features['opening'] == opening_name
            ].index[0]
        except IndexError:
            logger.warning(f"Opening '{opening_name}' not found")
            return []

        # Get similarity scores for this opening
        similarities = self.opening_similarity_matrix[idx]

        # Get top-k similar openings (excluding itself)
        similar_indices = np.argsort(similarities)[::-1][1:top_k+1]

        recommendations = [
            (self.opening_features.iloc[i]['opening'], similarities[i])
            for i in similar_indices
        ]

        return recommendations

    def recommend_openings(
        self,
        games_data: List[Dict],
        strategy: str = 'hybrid',
        top_k: int = 5
    ) -> List[Dict]:
        """
        Generate personalized opening recommendations.

        Strategies:
        - 'performance': Recommend high win-rate openings
        - 'exploration': Recommend underutilized openings with potential
        - 'similar': Recommend openings similar to successful ones
        - 'hybrid': Combine multiple strategies (RECOMMENDED)

        Similar to: E-commerce homepage recommendation algorithms

        Args:
            games_data: Player's game history
            strategy: Recommendation strategy
            top_k: Number of recommendations

        Returns:
            List of recommended openings with scores and reasoning
        """
        if self.opening_features is None:
            self.extract_opening_features(games_data)

        recommendations = []

        if strategy == 'performance':
            # Content-based: Recommend high-performing openings
            top_openings = self.opening_features.nlargest(top_k, 'win_rate')

            for _, opening in top_openings.iterrows():
                recommendations.append({
                    'opening': opening['opening'],
                    'score': opening['win_rate'],
                    'reason': f"High win rate: {opening['win_rate']:.1%}",
                    'confidence': min(opening['sample_size'] / 10, 1.0)
                })

        elif strategy == 'exploration':
            # Encourage trying new openings with potential
            # Openings with decent win rate but low sample size
            exploratory = self.opening_features[
                (self.opening_features['win_rate'] > 0.45) &
                (self.opening_features['sample_size'] < 10)
            ].nlargest(top_k, 'win_rate')

            for _, opening in exploratory.iterrows():
                recommendations.append({
                    'opening': opening['opening'],
                    'score': opening['win_rate'] * 0.8,  # Discount for uncertainty
                    'reason': f"Promising opening worth exploring (win rate: {opening['win_rate']:.1%})",
                    'confidence': 0.3  # Lower confidence due to small sample
                })

        elif strategy == 'similar':
            # Find player's most successful opening and recommend similar ones
            if len(self.opening_features) == 0:
                return []

            best_opening = self.opening_features.nlargest(1, 'win_rate').iloc[0]
            similar = self.get_similar_openings(best_opening['opening'], top_k)

            for opening_name, similarity in similar:
                opening_data = self.opening_features[
                    self.opening_features['opening'] == opening_name
                ].iloc[0]

                recommendations.append({
                    'opening': opening_name,
                    'score': similarity * opening_data['win_rate'],
                    'reason': f"Similar to your successful {best_opening['opening']} opening",
                    'confidence': similarity
                })

        elif strategy == 'hybrid':
            # Combine multiple signals (production-grade approach)
            for _, opening in self.opening_features.iterrows():
                # Score components (weighted combination)
                performance_score = opening['win_rate'] * 0.4
                accuracy_score = (opening['avg_accuracy'] / 100) * 0.3
                experience_bonus = min(opening['sample_size'] / 20, 0.15)

                # Penalize high blunder rate
                blunder_penalty = opening['blunder_rate'] * 0.1

                final_score = performance_score + accuracy_score + experience_bonus - blunder_penalty

                # Confidence based on sample size (Bayesian approach)
                confidence = 1 - np.exp(-opening['sample_size'] / 5)

                recommendations.append({
                    'opening': opening['opening'],
                    'score': final_score,
                    'reason': self._generate_reason(opening),
                    'confidence': confidence,
                    'metadata': {
                        'win_rate': opening['win_rate'],
                        'avg_accuracy': opening['avg_accuracy'],
                        'games_played': opening['sample_size']
                    }
                })

            # Sort by score and return top-k
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            recommendations = recommendations[:top_k]

        return recommendations

    def _generate_reason(self, opening: pd.Series) -> str:
        """Generate human-readable explanation for recommendation."""
        reasons = []

        if opening['win_rate'] > 0.6:
            reasons.append(f"strong win rate ({opening['win_rate']:.1%})")
        if opening['avg_accuracy'] > 80:
            reasons.append(f"high accuracy ({opening['avg_accuracy']:.1f}%)")
        if opening['blunder_rate'] < 0.5:
            reasons.append("low error rate")
        if opening['sample_size'] >= 10:
            reasons.append("well-practiced")

        return "Good choice: " + ", ".join(reasons) if reasons else "Consider trying this opening"

    def evaluate_recommendations(
        self,
        recommendations: List[Dict],
        actual_games: List[Dict]
    ) -> Dict[str, float]:
        """
        Evaluate recommendation quality (for A/B testing).

        Metrics:
        - Precision@K: How many recommended openings were actually played
        - Success rate: Win rate when following recommendations
        - Coverage: Diversity of recommendations

        Similar to: Evaluating e-commerce recommendation algorithm performance

        Args:
            recommendations: List of recommended openings
            actual_games: Games played after recommendations

        Returns:
            Dictionary of evaluation metrics
        """
        recommended_openings = {r['opening'] for r in recommendations}
        played_openings = {
            g.get('opening_analysis', {}).get('opening_name', '')
            for g in actual_games
        }

        # Precision@K: Did user play recommended openings?
        intersection = recommended_openings & played_openings
        precision = len(intersection) / len(recommended_openings) if recommended_openings else 0

        # Success rate: Win rate when following recommendations
        recommended_games = [
            g for g in actual_games
            if g.get('opening_analysis', {}).get('opening_name', '') in recommended_openings
        ]

        wins = sum(1 for g in recommended_games
                  if g.get('game_metadata', {}).get('result') == 'win')
        success_rate = wins / len(recommended_games) if recommended_games else 0

        # Coverage: Diversity of recommendations
        coverage = len(recommended_openings) / len(self.opening_features) if len(self.opening_features) > 0 else 0

        return {
            'precision_at_k': precision,
            'success_rate': success_rate,
            'coverage': coverage,
            'recommendations_followed': len(intersection)
        }


# Example usage and production patterns
if __name__ == "__main__":
    """
    Demonstrates production ML patterns:
    1. Feature engineering pipeline
    2. Model training (similarity computation)
    3. Inference (recommendation generation)
    4. Evaluation and monitoring
    """

    # This would be replaced with actual data loading
    print("Opening Recommender - Production ML System")
    print("\nKey concepts demonstrated:")
    print("- Feature engineering from raw game data")
    print("- Similarity-based collaborative filtering")
    print("- Hybrid recommendation strategies")
    print("- A/B testing evaluation framework")
    print("- Confidence scoring (similar to Thompson sampling)")
    print("\nApplicable to e-commerce recommendation engines for:")
    print("- Item recommendations on homepage")
    print("- Similar item suggestions")
    print("- Personalized search ranking")
