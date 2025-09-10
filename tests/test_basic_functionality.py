#!/usr/bin/env python3
"""
Basic Functionality Test Script

This script tests the core components of the chess analysis application
to ensure everything is working correctly.
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add project root to path for imports
project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_imports():
    """Test that all required modules can be imported."""
    print("🔄 Testing imports...")
    
    try:
        # Try multiple import strategies for data_fetcher
        try:
            from data_fetcher import ChessComDataFetcher  # type: ignore
        except ImportError:
            from src.data_fetcher import ChessComDataFetcher  # type: ignore
        print("✅ data_fetcher imported successfully")
    except ImportError as e:
        # Check if it's a missing dependency vs import path issue
        if "No module named 'requests'" in str(e) or "No module named 'pandas'" in str(e):
            print("⚠️  data_fetcher import failed due to missing dependencies (expected)")
            print("   Import path resolution is working correctly")
        else:
            print(f"❌ Failed to import data_fetcher: {e}")
            return False
    
    try:
        # Try multiple import strategies for game_parser
        try:
            from game_parser import GameParser  # type: ignore
        except ImportError:
            from src.game_parser import GameParser  # type: ignore
        print("✅ game_parser imported successfully")
    except ImportError as e:
        # Check if it's a missing dependency vs import path issue
        if "No module named 'pandas'" in str(e) or "No module named 'chess'" in str(e):
            print("⚠️  game_parser import failed due to missing dependencies (expected)")
            print("   Import path resolution is working correctly")
        else:
            print(f"❌ Failed to import game_parser: {e}")
            return False
    
    try:
        # Try multiple import strategies for opening_analyzer
        try:
            from analyzers.opening_analyzer import OpeningAnalyzer  # type: ignore
        except ImportError:
            from src.analyzers.opening_analyzer import OpeningAnalyzer  # type: ignore
        print("✅ opening_analyzer imported successfully")
    except ImportError as e:
        # Check if it's a missing dependency vs import path issue
        if "No module named 'pandas'" in str(e) or "No module named 'numpy'" in str(e):
            print("⚠️  opening_analyzer import failed due to missing dependencies (expected)")
            print("   Import path resolution is working correctly")
        else:
            print(f"❌ Failed to import opening_analyzer: {e}")
            return False
    
    try:
        # Try multiple import strategies for config.settings
        try:
            from config.settings import Config
        except ImportError:
            import sys
            import os
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config')
            if config_path not in sys.path:
                sys.path.insert(0, config_path)
            from settings import Config  # type: ignore
        print("✅ config.settings imported successfully")
    except ImportError as e:
        # Check if it's a missing dependency vs import path issue
        if "No module named 'dotenv'" in str(e):
            print("⚠️  config.settings import failed due to missing dependencies (expected)")
            print("   Import path resolution is working correctly")
        else:
            print(f"❌ Failed to import config.settings: {e}")
            return False
    
    return True

def test_config():
    """Test configuration setup."""
    print("\n🔄 Testing configuration...")
    
    try:
        from config.settings import Config
        
        print(f"✅ Chess.com base URL: {Config.CHESS_COM_BASE_URL}")
        print(f"✅ Data directory: {Config.DATA_DIR}")
        print(f"✅ Analysis depth: {Config.ANALYSIS_DEPTH}")
        print(f"✅ Time controls: {Config.TIME_CONTROLS}")
        
        # Check if directories exist or can be created
        os.makedirs(Config.RAW_DATA_DIR, exist_ok=True)
        os.makedirs(Config.PROCESSED_DATA_DIR, exist_ok=True)
        os.makedirs(Config.CACHE_DIR, exist_ok=True)
        print("✅ Data directories created/verified")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_data_fetcher():
    """Test data fetcher with a public profile."""
    print("\n🔄 Testing data fetcher...")
    
    try:
        # Try multiple import strategies for data_fetcher
        try:
            from data_fetcher import ChessComDataFetcher  # type: ignore
        except ImportError:
            from src.data_fetcher import ChessComDataFetcher  # type: ignore
        
        # Test with a well-known public profile
        test_username = "hikaru"  # Hikaru Nakamura's public profile
        fetcher = ChessComDataFetcher(test_username)
        
        # Test profile fetching
        profile = fetcher.get_player_profile()
        if profile:
            print(f"✅ Successfully fetched profile for {profile.get('username', 'unknown')}")
            print(f"   Joined: {datetime.fromtimestamp(profile.get('joined', 0)).strftime('%Y-%m-%d')}")
        else:
            print("❌ Failed to fetch player profile")
            return False
        
        # Test archives fetching
        archives = fetcher.get_available_archives()
        if archives:
            print(f"✅ Found {len(archives)} game archives")
        else:
            print("❌ No game archives found")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Data fetcher test failed: {e}")
        return False

def test_opening_analyzer():
    """Test opening analyzer with sample data."""
    print("\n🔄 Testing opening analyzer...")
    
    try:
        # Try multiple import strategies for opening_analyzer
        try:
            from analyzers.opening_analyzer import OpeningAnalyzer  # type: ignore
        except ImportError:
            from src.analyzers.opening_analyzer import OpeningAnalyzer  # type: ignore
        
        analyzer = OpeningAnalyzer()
        
        # Test with sample game data
        sample_games = [
            {
                'game_metadata': {
                    'result': '1',
                    'player_color': 'white',
                    'opponent_rating': 1500
                },
                'opening_analysis': {
                    'opening_name': 'Ruy Lopez',
                    'eco_code': 'C60',
                    'moves_in_theory': 12,
                    'first_inaccuracy_move': 15
                }
            },
            {
                'game_metadata': {
                    'result': '0',
                    'player_color': 'black',
                    'opponent_rating': 1600
                },
                'opening_analysis': {
                    'opening_name': 'Sicilian Defense',
                    'eco_code': 'B20',
                    'moves_in_theory': 8,
                    'first_inaccuracy_move': 10
                }
            }
        ]
        
        # Test opening analysis
        analysis = analyzer.analyze_opening_performance(sample_games)
        if analysis:
            print(f"✅ Opening analysis completed for {len(analysis)} openings")
            for opening, stats in analysis.items():
                print(f"   {stats['name']}: {stats['total_games']} games, {stats['score_percentage']}% score")
        else:
            print("❌ Opening analysis failed")
            return False
        
        # Test recommendations
        recommendations = analyzer.get_opening_recommendations(analysis)
        if recommendations:
            print(f"✅ Generated {len(recommendations)} recommendations")
        else:
            print("✅ No recommendations generated (normal for limited data)")
        
        return True
    except Exception as e:
        print(f"❌ Opening analyzer test failed: {e}")
        return False

def test_chess_utils():
    """Test chess utility functions."""
    print("\n🔄 Testing chess utilities...")
    
    try:
        # Try multiple import strategies for chess_utils
        try:
            from utils.chess_utils import (  # type: ignore
                parse_time_control, classify_time_control,
                count_pieces, format_time
            )
        except ImportError:
            from src.utils.chess_utils import (  # type: ignore
                parse_time_control, classify_time_control,
                count_pieces, format_time
            )
        
        # Test time control parsing
        tc_info = parse_time_control("600+5")
        if tc_info['base_time'] == 600 and tc_info['increment'] == 5:
            print("✅ Time control parsing works")
        else:
            print("❌ Time control parsing failed")
            return False
        
        # Test time control classification
        tc_class = classify_time_control("180+2")
        if tc_class == "blitz":
            print("✅ Time control classification works")
        else:
            print("❌ Time control classification failed")
            return False
        
        # Test piece counting
        start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        piece_count = count_pieces(start_fen)
        if piece_count == 32:
            print("✅ Piece counting works")
        else:
            print("❌ Piece counting failed")
            return False
        
        # Test time formatting
        formatted_time = format_time(3661)  # 1:01:01
        if formatted_time == "1:01:01":
            print("✅ Time formatting works")
        else:
            print("❌ Time formatting failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Chess utilities test failed: {e}")
        return False

def test_dependencies():
    """Test that required dependencies are installed."""
    print("\n🔄 Testing dependencies...")
    
    required_packages = [
        'requests', 'pandas', 'numpy', 'matplotlib', 
        'seaborn', 'plotly', 'tqdm', 'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    # Test chess library separately (it might not be installed)
    try:
        import chess
        import chess.pgn
        import chess.engine
        print("✅ python-chess is installed")
    except ImportError:
        print("❌ python-chess is missing")
        missing_packages.append('python-chess')
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def main():
    """Run all tests."""
    print("🚀 Chess Analysis Application - Basic Functionality Test")
    print("=" * 60)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Data Fetcher", test_data_fetcher),
        ("Opening Analyzer", test_opening_analyzer),
        ("Chess Utilities", test_chess_utils),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name} test PASSED")
            else:
                print(f"\n❌ {test_name} test FAILED")
        except Exception as e:
            print(f"\n❌ {test_name} test FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to use.")
        print("\nNext steps:")
        print("1. Set your Chess.com username in config/.env")
        print("2. Install Stockfish for advanced analysis")
        print("3. Run: jupyter notebook notebooks/main_analysis.ipynb")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)