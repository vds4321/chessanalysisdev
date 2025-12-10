#!/usr/bin/env python3
"""
Fixed tactical analyzer that properly processes parsed games
"""

import sys
sys.path.append('src')
sys.path.append('config')

from src.data_fetcher import ChessComDataFetcher
from src.game_parser import GameParser
from src.analyzers.tactical_analyzer import TacticalAnalyzer
from config.settings import Config
from datetime import datetime, timedelta

def run_fixed_tactical_analysis():
    print("🔧 Running Fixed Tactical Analysis")
    print("=" * 50)
    
    # Get recent games
    print("📥 Fetching games...")
    fetcher = ChessComDataFetcher(Config.CHESS_COM_USERNAME)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    raw_games = fetcher.get_all_games(start_date=start_date, end_date=end_date)
    
    # Filter by time controls
    time_controls = ["blitz", "rapid"]
    filtered_games = []
    for game in raw_games:
        time_class = game.get('time_class', '').lower()
        if time_class in [tc.lower() for tc in time_controls]:
            filtered_games.append(game)
    
    print(f"✅ Found {len(filtered_games)} games to analyze")
    
    # Parse games
    print("🔍 Parsing games...")
    parser = GameParser()
    parsed_games = []
    
    # Analyze just a few games for testing
    sample_games = filtered_games[:5]  
    
    for i, game in enumerate(sample_games):
        try:
            parsed_game = parser.parse_chess_com_game(game)
            if parsed_game:
                parsed_games.append(parsed_game)
                print(f"   Parsed game {i+1}/{len(sample_games)}")
        except Exception as e:
            print(f"   Failed to parse game {i+1}: {e}")
    
    print(f"✅ Successfully parsed {len(parsed_games)} games")
    
    # NOW THE FIX: Run tactical analysis on individual games first
    print("🎯 Running tactical analysis...")
    tactical_analyzer = TacticalAnalyzer()
    
    # Analyze each game individually and collect results
    analyzed_games = []
    total_blunders = 0
    total_mistakes = 0
    total_inaccuracies = 0
    total_moves = 0
    total_accuracy = 0.0
    
    for i, parsed_game in enumerate(parsed_games):
        try:
            # Get PGN from parsed game
            pgn = parsed_game.get('pgn', '')
            if not pgn:
                print(f"   Game {i+1}: No PGN data")
                continue
            
            print(f"   Analyzing game {i+1}/{len(parsed_games)}...")
            
            # Run tactical analysis on individual game
            game_tactics = tactical_analyzer.analyze_game_tactics(pgn, Config.CHESS_COM_USERNAME)
            
            if game_tactics:
                analyzed_games.append({
                    **parsed_game,
                    'tactical_analysis': game_tactics
                })
                
                # Accumulate statistics
                total_blunders += game_tactics.get('blunders', 0)
                total_mistakes += game_tactics.get('mistakes', 0) 
                total_inaccuracies += game_tactics.get('inaccuracies', 0)
                total_moves += game_tactics.get('total_moves', 0)
                total_accuracy += game_tactics.get('accuracy', 0)
                
                print(f"     ✅ Accuracy: {game_tactics.get('accuracy', 0):.1f}%")
                print(f"     Blunders: {game_tactics.get('blunders', 0)}, Mistakes: {game_tactics.get('mistakes', 0)}")
            else:
                print(f"   Game {i+1}: Tactical analysis returned None")
                
        except Exception as e:
            print(f"   Game {i+1}: Tactical analysis failed: {e}")
    
    # Calculate overall statistics
    games_analyzed = len(analyzed_games)
    if games_analyzed > 0:
        avg_accuracy = total_accuracy / games_analyzed
        
        print(f"\n🎯 Tactical Analysis Results:")
        print(f"========================================")
        print(f"Games analyzed: {games_analyzed}")
        print(f"Average accuracy: {avg_accuracy:.1f}%")
        print(f"Total moves: {total_moves}")
        print(f"Total blunders: {total_blunders}")
        print(f"Total mistakes: {total_mistakes}")
        print(f"Total inaccuracies: {total_inaccuracies}")
        
        if total_moves > 0:
            blunder_rate = (total_blunders / total_moves) * 100
            print(f"Blunder rate: {blunder_rate:.2f}%")
        
        # Generate recommendations
        print(f"\n🎯 Tactical Recommendations:")
        recommendations = tactical_analyzer.get_tactical_recommendations({
            'total_games': games_analyzed,
            'average_accuracy': avg_accuracy,
            'total_blunders': total_blunders,
            'total_mistakes': total_mistakes,
            'total_inaccuracies': total_inaccuracies,
            'game_data': analyzed_games
        })
        
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"   {i}. {rec}")
    
    else:
        print("❌ No games could be analyzed for tactics")

if __name__ == "__main__":
    run_fixed_tactical_analysis()
