#!/usr/bin/env python3
"""
Test script to verify Chess.com username configuration
"""

from config.settings import Config
from src.data_fetcher import ChessComDataFetcher

print("🔧 Testing Chess.com Username Configuration")
print("=" * 45)

print(f"Username from config: '{Config.CHESS_COM_USERNAME}'")

# Check if username is set properly
if not Config.CHESS_COM_USERNAME:
    print("❌ No username set in .env file")
    print("   Please add: CHESS_COM_USERNAME=your_actual_username")
    exit(1)

if Config.CHESS_COM_USERNAME in ["your_username_here", "your_actual_chess_username"]:
    print("❌ Username is still using placeholder value")
    print(f"   Current: {Config.CHESS_COM_USERNAME}")
    print("   Please update .env file with your real Chess.com username")
    exit(1)

print(f"✅ Username configured: {Config.CHESS_COM_USERNAME}")

# Test if this username exists on Chess.com
print(f"\n🌐 Testing Chess.com API access...")
try:
    fetcher = ChessComDataFetcher(Config.CHESS_COM_USERNAME)
    profile = fetcher.get_player_profile()
    print(f"✅ Successfully found profile for: {profile['username']}")
    
    # Test game archives
    archives = fetcher.get_available_archives()
    print(f"✅ Found {len(archives)} game archives")
    
    if len(archives) > 0:
        print("✅ Ready to analyze your games!")
    else:
        print("⚠️  No game archives found - you may not have any public games")
    
except Exception as e:
    print(f"❌ Failed to access Chess.com profile: {e}")
    print("\nPossible issues:")
    print("1. Username might be incorrect")
    print("2. Chess.com profile might be private")
    print("3. No games in your profile")
    print("4. Network/API issue")
