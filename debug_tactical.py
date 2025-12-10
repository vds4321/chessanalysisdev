#!/usr/bin/env python3
"""
Debug script to identify why tactical analysis shows 0 games analyzed
"""

import sys
sys.path.append('src')
sys.path.append('config')

from src.data_fetcher import ChessComDataFetcher
from src.game_parser import GameParser
from src.analyzers.tactical_analyzer import TacticalAnalyzer
from config.settings import Config
from datetime import datetime, timedelta

def debug_tactical_analysis():
    print("🔍 Debugging Tactical Analysis Pipeline")
    print("=" * 50)
    
    # Step 1: Test data fetching
    print("1️⃣ Testing data fetching...")
    fetcher = ChessComDataFetcher(Config.CHESS_COM_USERNAME)
    
    # Get recent games
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Last 30 days
    
    try:
        raw_games = fetcher.get_all_games(start_date=start_date, end_date=end_date)
        print(f"✅ Downloaded {len(raw_games)} raw games")
        
        if len(raw_games) == 0:
            print("❌ No games found for the time period")
            return
            
        # Filter by time controls
        time_controls = ["blitz", "rapid"]
        filtered_games = []
        for game in raw_games:
            time_class = game.get('time_class', '').lower()
            if time_class in [tc.lower() for tc in time_controls]:
                filtered_games.append(game)
        
        print(f"✅ Filtered to {len(filtered_games)} games matching time controls: {time_controls}")
        
        if len(filtered_games) == 0:
            print("⚠️ No games match the time control filter")
            print("Available time controls in your games:")
            time_controls_found = set()
            for game in raw_games[:10]:  # Check first 10 games
                tc = game.get('time_class', 'unknown')
                time_controls_found.add(tc)
            print(f"   Found: {list(time_controls_found)}")
            
            # Use all games for testing
            filtered_games = raw_games[:5]  # Just test with first 5
            print(f"   Using first {len(filtered_games)} games for testing")
    
    except Exception as e:
        print(f"❌ Data fetching failed: {e}")
        return
    
    # Step 2: Test game parsing
    print(f"\n2️⃣ Testing game parsing...")
    parser = GameParser()
    print(f"   Game parser initialized: {parser is not None}")
    print(f"   Stockfish engine available: {parser.engine is not None}")
    
    parsed_games = []
    sample_games = filtered_games[:3]  # Test with just 3 games
    
    for i, game in enumerate(sample_games):
        try:
            print(f"   Parsing game {i+1}/{len(sample_games)}...")
            
            # Debug: Check game structure
            print(f"     Game keys: {list(game.keys())}")
            print(f"     Has PGN: {'pgn' in game}")
            if 'pgn' in game:
                print(f"     PGN length: {len(game['pgn'])} characters")
            
            parsed_game = parser.parse_chess_com_game(game)
            
            if parsed_game:
                print(f"     ✅ Game {i+1} parsed successfully")
                print(f"     White: {parsed_game.get('white_username', 'Unknown')}")
                print(f"     Black: {parsed_game.get('black_username', 'Unknown')}")
                print(f"     Result: {parsed_game.get('result', 'Unknown')}")
                parsed_games.append(parsed_game)
            else:
                print(f"     ❌ Game {i+1} parsing returned None")
                
        except Exception as e:
            print(f"     ❌ Game {i+1} parsing failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"✅ Successfully parsed {len(parsed_games)} out of {len(sample_games)} games")
    
    if len(parsed_games) == 0:
        print("❌ No games could be parsed - tactical analysis will show 0 games")
        return
    
    # Step 3: Test tactical analysis
    print(f"\n3️⃣ Testing tactical analysis...")
    try:
        tactical_analyzer = TacticalAnalyzer()
        print("   Tactical analyzer initialized")
        
        # Test with parsed games
        tactical_results = tactical_analyzer.analyze_tactical_patterns(parsed_games)
        
        print(f"✅ Tactical analysis results:")
        print(f"   Games analyzed: {tactical_results.get('total_games', 0)}")
        print(f"   Average accuracy: {tactical_results.get('average_accuracy', 0):.1f}%")
        print(f"   Total moves: {tactical_results.get('total_moves', 0)}")
        
        if tactical_results.get('total_games', 0) == 0:
            print("❌ Tactical analyzer still shows 0 games - there's an issue in the analyzer")
        
    except Exception as e:
        print(f"❌ Tactical analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_tactical_analysis()
