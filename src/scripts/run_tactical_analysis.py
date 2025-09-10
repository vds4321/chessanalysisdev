#!/usr/bin/env python3
"""
Tactical Analysis Runner

This script runs tactical analysis on your chess games to identify
blunders, mistakes, and missed tactical opportunities.
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.data_fetcher import ChessComDataFetcher
from src.game_parser import GameParser
from src.analyzers.tactical_analyzer import TacticalAnalyzer
from config.settings import Config

def main():
    print("🎯 Chess Tactical Analysis")
    print("=" * 50)
    
    # Check if we have analyzed games
    parsed_games_path = os.path.join(Config.PROCESSED_DATA_DIR, "parsed_games.json")
    
    if not os.path.exists(parsed_games_path):
        print("❌ No analyzed games found.")
        print("   Please run the main analysis first to download and parse your games.")
        print("   You can do this by running the Jupyter notebook or:")
        print("   python -c \"from src.data_fetcher import ChessComDataFetcher; fetcher = ChessComDataFetcher(); games = fetcher.get_all_games(); print(f'Downloaded {len(games)} games')\"")
        return
    
    # Load parsed games
    print("📂 Loading analyzed games...")
    with open(parsed_games_path, 'r') as f:
        parsed_games = json.load(f)
    
    print(f"✅ Loaded {len(parsed_games)} games")
    
    if not parsed_games:
        print("❌ No games to analyze")
        return
    
    # Initialize tactical analyzer
    print("🔧 Initializing tactical analyzer...")
    try:
        tactical_analyzer = TacticalAnalyzer()
        print("✅ Tactical analyzer ready")
    except Exception as e:
        print(f"❌ Failed to initialize tactical analyzer: {e}")
        print("   Make sure Stockfish is installed and the path is correct in your .env file")
        print("   You can install Stockfish with: brew install stockfish")
        return
    
    # Analyze games for tactical patterns
    print(f"🔄 Analyzing tactical patterns in {len(parsed_games)} games...")
    
    tactical_results = []
    total_blunders = 0
    total_mistakes = 0
    total_inaccuracies = 0
    total_accuracy = 0
    games_with_stats = 0
    
    for i, game in enumerate(parsed_games):
        print(f"   Analyzing game {i+1}/{len(parsed_games)}...", end='\r')
        
        # Extract basic tactical stats from existing analysis
        stats = game.get('statistics', {})
        metadata = game.get('game_metadata', {})
        
        if stats:
            games_with_stats += 1
            blunders = stats.get('blunders', 0)
            mistakes = stats.get('mistakes', 0)
            inaccuracies = stats.get('inaccuracies', 0)
            accuracy = stats.get('accuracy', 0)
            
            total_blunders += blunders
            total_mistakes += mistakes
            total_inaccuracies += inaccuracies
            total_accuracy += accuracy
            
            tactical_results.append({
                'game_id': metadata.get('game_id', f'game_{i}'),
                'time_class': metadata.get('time_class', 'unknown'),
                'result': metadata.get('result', 'unknown'),
                'player_color': metadata.get('player_color', 'unknown'),
                'opponent_rating': metadata.get('opponent_rating', 0),
                'blunders': blunders,
                'mistakes': mistakes,
                'inaccuracies': inaccuracies,
                'accuracy': accuracy,
                'total_errors': blunders + mistakes + inaccuracies
            })
    
    print(f"\n✅ Tactical analysis complete!")
    
    if games_with_stats == 0:
        print("❌ No tactical statistics found in the analyzed games")
        print("   The games may need to be re-analyzed with engine evaluation")
        return
    
    # Calculate averages
    avg_blunders = total_blunders / games_with_stats
    avg_mistakes = total_mistakes / games_with_stats
    avg_inaccuracies = total_inaccuracies / games_with_stats
    avg_accuracy = total_accuracy / games_with_stats
    avg_total_errors = (total_blunders + total_mistakes + total_inaccuracies) / games_with_stats
    
    # Display results
    print("\n📊 TACTICAL ANALYSIS RESULTS")
    print("=" * 50)
    print(f"Games analyzed: {games_with_stats}")
    print(f"Average accuracy: {avg_accuracy:.1f}%")
    print(f"Average blunders per game: {avg_blunders:.1f}")
    print(f"Average mistakes per game: {avg_mistakes:.1f}")
    print(f"Average inaccuracies per game: {avg_inaccuracies:.1f}")
    print(f"Average total errors per game: {avg_total_errors:.1f}")
    
    # Analyze by time control
    print("\n⏱️  PERFORMANCE BY TIME CONTROL")
    print("=" * 50)
    time_controls = {}
    for result in tactical_results:
        tc = result['time_class']
        if tc not in time_controls:
            time_controls[tc] = {
                'games': 0, 'blunders': 0, 'mistakes': 0, 
                'inaccuracies': 0, 'accuracy': 0
            }
        time_controls[tc]['games'] += 1
        time_controls[tc]['blunders'] += result['blunders']
        time_controls[tc]['mistakes'] += result['mistakes']
        time_controls[tc]['inaccuracies'] += result['inaccuracies']
        time_controls[tc]['accuracy'] += result['accuracy']
    
    for tc, data in time_controls.items():
        if data['games'] > 0:
            print(f"{tc.capitalize():10}: {data['games']:3d} games | "
                  f"Accuracy: {data['accuracy']/data['games']:5.1f}% | "
                  f"Blunders: {data['blunders']/data['games']:4.1f} | "
                  f"Mistakes: {data['mistakes']/data['games']:4.1f}")
    
    # Analyze by game result
    print("\n🎮 PERFORMANCE BY GAME RESULT")
    print("=" * 50)
    results = {}
    for result in tactical_results:
        res = result['result']
        if res not in results:
            results[res] = {
                'games': 0, 'blunders': 0, 'mistakes': 0, 
                'inaccuracies': 0, 'accuracy': 0
            }
        results[res]['games'] += 1
        results[res]['blunders'] += result['blunders']
        results[res]['mistakes'] += result['mistakes']
        results[res]['inaccuracies'] += result['inaccuracies']
        results[res]['accuracy'] += result['accuracy']
    
    result_names = {'1': 'Wins', '0': 'Losses', '1/2': 'Draws'}
    for res, data in results.items():
        if data['games'] > 0:
            name = result_names.get(res, res)
            print(f"{name:10}: {data['games']:3d} games | "
                  f"Accuracy: {data['accuracy']/data['games']:5.1f}% | "
                  f"Blunders: {data['blunders']/data['games']:4.1f} | "
                  f"Mistakes: {data['mistakes']/data['games']:4.1f}")
    
    # Generate recommendations
    print("\n🎯 TACTICAL IMPROVEMENT RECOMMENDATIONS")
    print("=" * 50)
    
    recommendations = []
    
    # Accuracy recommendations
    if avg_accuracy < 70:
        recommendations.append({
            'priority': 'HIGH',
            'area': 'Overall Accuracy',
            'issue': f'Your average accuracy is {avg_accuracy:.1f}%, which is below the target of 70%+',
            'recommendation': 'Focus on basic tactical training. Solve 10-15 tactical puzzles daily.'
        })
    elif avg_accuracy < 80:
        recommendations.append({
            'priority': 'MEDIUM',
            'area': 'Accuracy Improvement',
            'issue': f'Your accuracy of {avg_accuracy:.1f}% is decent but can be improved',
            'recommendation': 'Work on calculation depth. Practice visualizing 3-4 moves ahead.'
        })
    
    # Blunder recommendations
    if avg_blunders > 2:
        recommendations.append({
            'priority': 'HIGH',
            'area': 'Blunder Reduction',
            'issue': f'You average {avg_blunders:.1f} blunders per game, which is quite high',
            'recommendation': 'Before each move, ask: "What is my opponent threatening?" and "Is my piece safe?"'
        })
    elif avg_blunders > 1:
        recommendations.append({
            'priority': 'MEDIUM',
            'area': 'Blunder Control',
            'issue': f'You average {avg_blunders:.1f} blunders per game',
            'recommendation': 'Slow down in critical positions. Take extra time when material is at stake.'
        })
    
    # Mistake recommendations
    if avg_mistakes > 3:
        recommendations.append({
            'priority': 'MEDIUM',
            'area': 'Mistake Reduction',
            'issue': f'You average {avg_mistakes:.1f} mistakes per game',
            'recommendation': 'Improve your positional understanding. Study typical pawn structures and piece placement.'
        })
    
    # Time control specific recommendations
    worst_tc = None
    worst_error_rate = 0
    for tc, data in time_controls.items():
        if data['games'] >= 3:  # Only consider time controls with enough games
            error_rate = (data['blunders'] + data['mistakes']) / data['games']
            if error_rate > worst_error_rate:
                worst_error_rate = error_rate
                worst_tc = tc
    
    if worst_tc and worst_error_rate > 2:
        recommendations.append({
            'priority': 'LOW',
            'area': f'{worst_tc.capitalize()} Time Control',
            'issue': f'You make {worst_error_rate:.1f} errors per game in {worst_tc} games',
            'recommendation': f'Consider playing longer time controls to improve your {worst_tc} performance.'
        })
    
    # Display recommendations
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            priority_emoji = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}
            print(f"\n{i}. {priority_emoji[rec['priority']]} {rec['area']} ({rec['priority']} Priority)")
            print(f"   Issue: {rec['issue']}")
            print(f"   💡 Recommendation: {rec['recommendation']}")
    else:
        print("\n🎉 Excellent tactical performance! Your error rates are very low.")
        print("   Continue your current training routine and consider more advanced tactical themes.")
    
    # General training suggestions
    print("\n📚 GENERAL TRAINING SUGGESTIONS")
    print("=" * 50)
    print("• Daily tactical puzzles (10-15 minutes)")
    print("• Analyze your games, especially losses")
    print("• Practice endgames to improve calculation")
    print("• Study master games in your openings")
    print("• Play longer time controls occasionally")
    print("• Focus on candidate moves before calculating")
    
    print(f"\n✅ Tactical analysis complete! Analyzed {games_with_stats} games.")
    print("💡 Run this analysis regularly to track your improvement!")

if __name__ == "__main__":
    main()