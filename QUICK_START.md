# 🚀 Quick Start Guide

## Step-by-Step Instructions to Try the Chess Analysis Application

### 1. Prerequisites Check
- ✅ Python 3.8+ installed (you have Python 3.13)
- ✅ Chess.com account with game history
- ✅ Virtual environment created

### 2. Installation Status
The dependencies are currently being installed. Once complete, you'll see a success message.

### 3. Configuration Setup

After installation completes, set up your configuration:

```bash
# Copy the example environment file
cp config/.env.example .env

# Edit the .env file with your details
nano .env  # or use any text editor
```

In the `.env` file, update:
```bash
CHESS_COM_USERNAME=your_actual_username
STOCKFISH_PATH=/opt/homebrew/bin/stockfish  # or wherever stockfish is installed
ANALYSIS_DEPTH=15
```

### 4. Install Stockfish (Optional but Recommended)

For advanced position analysis, install Stockfish:

```bash
# On macOS with Homebrew
brew install stockfish

# Check installation
which stockfish
```

### 5. Test Basic Functionality

Run the test script to verify everything works:

```bash
# Activate virtual environment
source chess_analysis_env/bin/activate

# Run basic tests
python3 test_basic_functionality.py
```

### 6. Start Analysis

Launch the main analysis notebook:

```bash
# Start Jupyter
jupyter notebook notebooks/main_analysis.ipynb
```

### 7. Configure the Notebook

In the notebook, update the configuration cell:

```python
# Replace with your actual Chess.com username
USERNAME = "your_chess_username"  

# Set analysis period (months)
ANALYSIS_MONTHS = 6  # or None for all games

# Choose time controls
TIME_CONTROLS = ["bullet", "blitz", "rapid"]
```

### 8. Run the Analysis

Execute the notebook cells step by step:

1. **Setup & Imports** - Load libraries
2. **Download Games** - Fetch from Chess.com
3. **Parse Games** - Extract analysis data
4. **Opening Analysis** - Analyze opening performance
5. **Visualizations** - Interactive charts
6. **Recommendations** - Get improvement suggestions

## 🎯 What You'll Get

### Opening Insights
- Success rates by opening variation
- Preparation depth analysis
- Color-specific performance
- Repertoire recommendations

### Performance Metrics
- Win/draw/loss statistics
- Accuracy measurements
- Blunder frequency analysis
- Time management insights

### Visual Analysis
- Interactive performance charts
- Opening success rate graphs
- Rating progression trends
- Opponent strength analysis

## 🔧 Troubleshooting

### Common Issues

**"python-chess not found"**
```bash
pip install python-chess
```

**"Stockfish not found"**
```bash
# Install Stockfish
brew install stockfish

# Update .env file with correct path
STOCKFISH_PATH=/opt/homebrew/bin/stockfish
```

**"No games found"**
- Verify your Chess.com username is correct
- Ensure your games are public (required for API access)
- Check the date range includes games

**"Import errors in notebook"**
```bash
# Make sure virtual environment is activated
source chess_analysis_env/bin/activate

# Install missing packages
pip install jupyter ipywidgets
```

## 📊 Sample Output

Once running, you'll see insights like:

```
📊 Top 10 Most Played Openings:
==================================================
 1. Sicilian Defense                      | Games:  45 | Score:  58.9%
 2. Ruy Lopez                            | Games:  32 | Score:  65.6%
 3. French Defense                       | Games:  28 | Score:  42.9%
 4. Queen's Gambit Declined              | Games:  24 | Score:  54.2%
 5. English Opening                      | Games:  19 | Score:  63.2%

🎯 Personalized Opening Recommendations:
==================================================
1. 💪 Your strongest opening: Ruy Lopez
   You score 65.6% with this opening (32 games). Consider playing it more often.

2. ⚠️ Opening to improve: French Defense
   You score only 42.9% with this opening (28 games). Consider studying this opening more.
```

## 🎮 Next Steps

After your first analysis:

1. **Study Recommendations** - Focus on suggested improvements
2. **Track Progress** - Re-run analysis monthly to see improvement
3. **Explore Patterns** - Use the detailed notebooks for deeper analysis
4. **Customize Analysis** - Modify parameters for specific insights

## 🆘 Need Help?

- Check the full [`README.md`](README.md) for detailed documentation
- Review [`TECHNICAL_SPECS.md`](TECHNICAL_SPECS.md) for advanced configuration
- Run `python3 test_basic_functionality.py` to diagnose issues

Happy analyzing! 🚀♟️