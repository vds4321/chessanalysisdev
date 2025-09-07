#!/usr/bin/env python3
"""
Quick Chess Analysis

Downloads your recent games and runs basic analysis including tactical patterns.
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add src to path
sys.path.append('src')
sys.path.append('config')

from src.data_fetcher import ChessComDataFetcher
from src.game_parser import GameParser
from config.settings import Config

def main():
    print("🚀 Quick Chess Analysis Setup")
    print("=" * 40)
    
    username = Config.CHESS_COM_USERNAME
    if not username or username == "your_username_here":
        print("❌ Please set your Chess.com username in the .env file")
        return
    
    print(f"👤 Analyzing games for: {username}")
    
    # Download recent games (last 3 months)
    print("📥 Downloading recent games...")
    try:
        fetcher = ChessComDataFetcher(username)
        
        # Get games from last 3 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        games = fetcher.get_all_games(start_date=start_date, end_date=end_date)
        
        if not games:
            print("❌ No games found. Make sure your Chess.com profile is public.")
            return
        
        print(f"✅ Downloaded {len(games)} games")
        
        # Filter for common time controls
        filtered_games = []
        for game in games:
            time_class = game.get('time_class', '')
            if time_class in ['bullet', 'blitz', 'rapid']:
                filtered_games.append(game)
        
        games = filtered_games[:20]  # Limit to 20 games for quick analysis
        print(f"📊 Analyzing {len(games)} games (limited for quick analysis)")
        
    except Exception as e:
        print(f"❌ Error downloading games: {e}")
        return
    
    # Parse games (basic analysis without deep engine evaluation)
    print("🔄 Parsing games...")
    try:
        parser = GameParser()
        
        # Parse games with basic statistics
        parsed_games = []
        for i, game in enumerate(games):
            print(f"   Parsing game {i+1}/{len(games)}...", end='\r')
            
            try:
                # Basic parsing without engine analysis for speed
                parsed_game = parser.parse_chess_com_game(game)
                if parsed_game:
                    parsed_games.append(parsed_game)
            except Exception as e:
                print(f"   Warning: Could not parse game {i+1}: {e}")
                continue
        
        print(f"\n✅ Parsed {len(parsed_games)} games successfully")
        
        if not parsed_games:
            print("❌ No games could be parsed")
            return
        
        # Save parsed games
        os.makedirs(Config.PROCESSED_DATA_DIR, exist_ok=True)
        output_path = os.path.join(Config.PROCESSED_DATA_DIR, "parsed_games.json")
        
        with open(output_path, 'w') as f:
            json.dump(parsed_games, f, indent=2, default=str)
        
        print(f"💾 Saved parsed games to: {output_path}")
        
    except Exception as e:
        print(f"❌ Error parsing games: {e}")
        return
    
    # Basic tactical analysis from game results
    print("\n📊 BASIC TACTICAL ANALYSIS")
    print("=" * 40)
    
    total_games = len(parsed_games)
    wins = 0
    draws = 0
    losses = 0
    
    time_control_stats = {}
    color_stats = {'white': {'games': 0, 'wins': 0}, 'black': {'games': 0, 'wins': 0}}
    
    for game in parsed_games:
        metadata = game.get('game_metadata', {})
        result = metadata.get('result', 'unknown')
        time_class = metadata.get('time_class', 'unknown')
        player_color = metadata.get('player_color', 'unknown')
        
        # Count results
        if result == '1':
            wins += 1
            if player_color in color_stats:
                color_stats[player_color]['wins'] += 1
        elif result == '1/2':
            draws += 1
        else:
            losses += 1
        
        # Count by color
        if player_color in color_stats:
            color_stats[player_color]['games'] += 1
        
        # Count by time control
        if time_class not in time_control_stats:
            time_control_stats[time_class] = {'games': 0, 'wins': 0, 'draws': 0}
        time_control_stats[time_class]['games'] += 1
        if result == '1':
            time_control_stats[time_class]['wins'] += 1
        elif result == '1/2':
            time_control_stats[time_class]['draws'] += 1
    
    # Display results
    print(f"🎮 Total Games: {total_games}")
    print(f"✅ Wins: {wins} ({wins/total_games*100:.1f}%)")
    print(f"🤝 Draws: {draws} ({draws/total_games*100:.1f}%)")
    print(f"❌ Losses: {losses} ({losses/total_games*100:.1f}%)")
    print(f"📊 Overall Score: {(wins + draws*0.5)/total_games*100:.1f}%")
    
    print(f"\n♔♛ Performance by Color:")
    for color, stats in color_stats.items():
        if stats['games'] > 0:
            score = (stats['wins'] / stats['games']) * 100
            print(f"   {color.capitalize()}: {stats['games']} games, {score:.1f}% score")
    
    print(f"\n⏱️  Performance by Time Control:")
    for tc, stats in time_control_stats.items():
        if stats['games'] > 0:
            score = ((stats['wins'] + stats['draws']*0.5) / stats['games']) * 100
            print(f"   {tc.capitalize()}: {stats['games']} games, {score:.1f}% score")
    
    # Basic recommendations
    print(f"\n🎯 QUICK RECOMMENDATIONS")
    print("=" * 40)
    
    overall_score = (wins + draws*0.5)/total_games*100
    
    if overall_score < 45:
        print("🔴 Focus on basic tactics and opening principles")
        print("   • Solve 10-15 tactical puzzles daily")
        print("   • Learn 2-3 solid openings")
        print("   • Practice basic endgames")
    elif overall_score < 55:
        print("🟡 Good foundation, work on consistency")
        print("   • Analyze your losses to find patterns")
        print("   • Improve time management")
        print("   • Study typical middlegame plans")
    else:
        print("🟢 Strong performance! Focus on refinement")
        print("   • Deepen your opening repertoire")
        print("   • Study advanced tactical themes")
        print("   • Work on complex endgames")
    
    # Color-specific advice
    white_score = (color_stats['white']['wins'] / color_stats['white']['games']) * 100 if color_stats['white']['games'] > 0 else 0
    black_score = (color_stats['black']['wins'] / color_stats['black']['games']) * 100 if color_stats['black']['games'] > 0 else 0
    
    if abs(white_score - black_score) > 15:
        weaker_color = 'white' if white_score < black_score else 'black'
        print(f"\n💡 You perform better with {'black' if weaker_color == 'white' else 'white'} pieces")
        print(f"   Consider studying {weaker_color} openings and typical plans")
    
    print(f"\n✅ Quick analysis complete!")
    print("💡 For detailed tactical analysis including blunder patterns,")
    print("   run: python run_tactical_analysis.py")
    print("🚀 For full analysis with opening insights, use the Jupyter notebook!")

if __name__ == "__main__":
    main()