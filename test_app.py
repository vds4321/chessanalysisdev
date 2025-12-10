#!/usr/bin/env python3
"""
Quick test script for Chess Analysis App
Tests all major components with your actual configuration.
"""

import sys
import os
sys.path.append('src')

from src.data_fetcher import ChessComDataFetcher
from src.game_parser import GameParser
from src.analyzers.opening_analyzer import OpeningAnalyzer
from config.settings import Config

def test_chess_analysis_app():
    """Test all major components of the chess analysis app."""
    
    print("🚀 Chess Analysis App - Quick Test")
    print("=" * 50)
    
    # Test 1: Configuration
    print("\n1️⃣  Testing Configuration...")
    print(f"   Username: {Config.CHESS_COM_USERNAME}")
    print(f"   Stockfish Path: {Config.STOCKFISH_PATH}")
    
    if not Config.CHESS_COM_USERNAME or Config.CHESS_COM_USERNAME == "your_username_here":
        print("⚠️  Please set your Chess.com username in the .env file")
        return False
    
    # Test 2: Data Fetcher
    print(f"\n2️⃣  Testing Data Fetcher with username: {Config.CHESS_COM_USERNAME}")
    try:
        fetcher = ChessComDataFetcher(Config.CHESS_COM_USERNAME)
        profile = fetcher.get_player_profile()
        print(f"✅ Profile loaded: {profile['username']}")
        
        archives = fetcher.get_available_archives()
        print(f"✅ Found {len(archives)} game archives")
        
        if archives:
            # Get a small sample of recent games
            latest_archive = archives[-1]
            parts = latest_archive.split('/')
            year, month = int(parts[-2]), int(parts[-1])
            
            print(f"   Getting sample games from {year}-{month:02d}...")
            games = fetcher.get_games_for_month(year, month)
            sample_games = games[:2] if games else []
            print(f"✅ Downloaded {len(sample_games)} sample games")
        
    except Exception as e:
        print(f"❌ Data Fetcher failed: {e}")
        return False
    
    # Test 3: Game Parser
    print("\n3️⃣  Testing Game Parser...")
    try:
        parser = GameParser()
        print(f"✅ Game Parser initialized")
        print(f"   Stockfish engine: {'✅ Available' if parser.engine else '❌ Not available'}")
        
        if sample_games:
            parsed_game = parser.parse_chess_com_game(sample_games[0])
            if parsed_game:
                print(f"✅ Successfully parsed sample game")
                print(f"   Game details: {parsed_game.get('white_username')} vs {parsed_game.get('black_username')}")
            else:
                print("⚠️  Game parsing returned None")
        
    except Exception as e:
        print(f"❌ Game Parser failed: {e}")
        return False
    
    # Test 4: Opening Analyzer
    print("\n4️⃣  Testing Opening Analyzer...")
    try:
        analyzer = OpeningAnalyzer()
        
        if sample_games:
            parsed_games = []
            for game in sample_games:
                parsed = parser.parse_chess_com_game(game)
                if parsed:
                    parsed_games.append(parsed)
            
            if parsed_games:
                opening_analysis = analyzer.analyze_opening_performance(parsed_games)
                print(f"✅ Opening analysis completed")
                print(f"   Analyzed {len(parsed_games)} games")
            else:
                print("⚠️  No games could be parsed for opening analysis")
        
    except Exception as e:
        print(f"❌ Opening Analyzer failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Your Chess Analysis App is ready to use!")
    print("\nNext steps:")
    print("1. Open Jupyter Notebook: http://localhost:8888")
    print("2. Run the main_analysis.ipynb notebook")
    print("3. Analyze your games and get insights!")
    
    return True

if __name__ == "__main__":
    test_chess_analysis_app()
