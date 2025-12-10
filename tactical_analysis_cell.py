# Tactical Analysis Cell - Add this to your main_analysis.ipynb notebook

"""
Copy this code into a new cell in your main_analysis.ipynb notebook
to run tactical analysis on your games.
"""

# Import tactical analyzer
from src.analyzers.tactical_analyzer import TacticalAnalyzer

print("🎯 Running Tactical Analysis...")

# Initialize tactical analyzer
tactical_analyzer = TacticalAnalyzer()

# Analyze tactics for your parsed games
if 'parsed_games' in locals() and parsed_games:
    print(f"Analyzing tactical patterns in {len(parsed_games)} games...")
    
    # Run tactical analysis
    tactical_analysis = tactical_analyzer.analyze_tactical_patterns(parsed_games)
    
    # Display results
    print(f"✅ Tactical analysis complete!")
    print(f"   Games analyzed: {tactical_analysis.get('total_games', 0)}")
    print(f"   Average accuracy: {tactical_analysis.get('average_accuracy', 0):.1f}%")
    print(f"   Total blunders: {tactical_analysis.get('total_blunders', 0)}")
    print(f"   Total mistakes: {tactical_analysis.get('total_mistakes', 0)}")
    
    # Get recommendations
    recommendations = tactical_analyzer.get_tactical_recommendations(tactical_analysis)
    
    print("\n🎯 Tactical Recommendations:")
    for i, rec in enumerate(recommendations[:5], 1):
        print(f"   {i}. {rec}")
    
    # Store results for further analysis
    tactical_results = tactical_analysis
    
else:
    print("❌ No parsed games available. Please run the game parsing cell first.")
