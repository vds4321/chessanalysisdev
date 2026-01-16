# Chess.com Coach

**Analyze your Chess.com games. Get better at chess.**

Built by a chess player who wanted to stop guessing what to improve and start knowing.

---

## What This Does

Analyzes your Chess.com game history and tells you:

- **What openings work for you** (and which don't)
- **Why you're losing games** (blunders, missed tactics, time pressure)
- **If you're actually improving** (rating trends, accuracy over time)

No fluff. Just insights you can act on.

## Quick Start

```bash
# 1. Install
git clone https://github.com/vds4321/chessdotcomcoach.git
cd chessdotcomcoach
pip install -r requirements.txt

# 2. Install Stockfish (required for tactical analysis)
# macOS:
brew install stockfish

# Ubuntu/Debian:
sudo apt-get install stockfish

# Windows: Download from https://stockfishchess.org/download/

# 3. Configure
cp .env.example .env
# Edit .env and add your Chess.com username

# 4. Analyze your games
jupyter notebook notebooks/main_analysis.ipynb
```

**That's it.** The notebook walks you through everything else.

---

## What You'll See

### Opening Performance
*Your best and worst openings, ranked by win rate and accuracy*

**Sample insights:**
- "Italian Game: 71% win rate across 28 games - keep playing it"
- "French Defense: 38% win rate - consider switching to Caro-Kann"
- "You're underperforming with Black (-12% win rate vs. expected)"

### Tactical Mistakes
*Where and when you're making mistakes*

**Sample insights:**
- "You blunder 3.2x more often with <30 seconds on the clock"
- "Missing fork patterns in 18% of tactical positions"
- "Accuracy drops from 84% to 67% when opponent rated 200+ points higher"

### Progression Tracking
*Are you improving? This answers it.*

**Sample insights:**
- "Rating up 147 points in last 6 months (+24/month trend)"
- "Average accuracy improved from 74% → 81%"
- "Opening preparation depth increased from 8 moves → 12 moves"

---

## How It Works

```
Chess.com API → Parse PGN → Stockfish Analysis → Statistical Insights → Recommendations
      ↓             ↓              ↓                    ↓                    ↓
  Your games    Move-by-move    Position eval      Pattern detection    Action plan
```

**Tech stack:**
- `python-chess` for game parsing
- `Stockfish` for position evaluation
- `pandas` for data analysis
- `plotly` for interactive visualizations

---

## Project Structure

```
chessdotcomcoach/
├── src/
│   ├── data_fetcher.py          # Chess.com API client
│   ├── game_parser.py           # PGN parsing + Stockfish integration
│   ├── analyzers/
│   │   ├── opening_analyzer.py      # Opening performance metrics
│   │   ├── tactical_analyzer.py     # Blunder/mistake detection
│   │   ├── progression_analyzer.py  # Rating/accuracy trends
│   │   └── opening_recommender.py   # ML-based opening suggestions
│   ├── visualizers/
│   │   └── progression_visualizer.py
│   └── utils/
│       └── chess_utils.py
│
├── notebooks/
│   ├── main_analysis.ipynb          # 👈 Start here
│   ├── progression_analysis.ipynb   # Deep-dive: improvement over time
│   ├── tactical_review_simple.ipynb # Deep-dive: tactical mistakes
│   └── ml_recommender_demo.ipynb    # Deep-dive: opening recommendations
│
├── tests/
│   ├── test_basic_functionality.py  # Core module tests
│   └── test_integration.py          # End-to-end tests
│
├── config/
│   └── settings.py                  # Configuration (thresholds, paths)
│
└── requirements.txt
```

---

## Requirements

- **Python 3.8+**
- **Stockfish chess engine** ([install guide](https://stockfishchess.org/download/))
- **Chess.com account** (free - just need your username)

Your games must be **public** for the API to access them.

---

## Configuration

Edit `.env`:

```bash
# Your Chess.com username
CHESS_COM_USERNAME=your_username

# Stockfish path (auto-detected on most systems)
STOCKFISH_PATH=/opt/homebrew/bin/stockfish

# Analysis depth (higher = more accurate, slower)
ANALYSIS_DEPTH=15
```

Advanced configuration in `config/settings.py`:
- Blunder/mistake thresholds (centipawns)
- Time pressure definition
- Time controls to analyze

---

## Notebooks Guide

### 1. [main_analysis.ipynb](notebooks/main_analysis.ipynb) - Start Here
**What:** Complete analysis dashboard
**Time:** 2-5 minutes (depending on game count)
**Output:** Opening stats, tactical errors, progression charts

### 2. [tactical_review_simple.ipynb](notebooks/tactical_review_simple.ipynb)
**What:** Deep-dive into tactical mistakes
**When:** After main analysis, if you want to understand specific blunders
**Output:** Move-by-move breakdown, pattern identification

### 3. [progression_analysis.ipynb](notebooks/progression_analysis.ipynb)
**What:** Long-term improvement tracking
**When:** Monthly check-ins to measure progress
**Output:** Rating trends, accuracy evolution, consistency metrics

### 4. [ml_recommender_demo.ipynb](notebooks/ml_recommender_demo.ipynb)
**What:** ML-powered opening recommendations
**When:** Building or refining your opening repertoire
**Output:** Personalized opening suggestions based on your style

---

## Example Analysis

**Player:** 1650-rated blitz player, 62 games analyzed

**Key Findings:**
1. **Sicilian Defense performing well** (68% win rate) - keep playing
2. **Time pressure issue** (42% of blunders occur with <30 sec)
3. **Missing tactical patterns** (forks: 23% miss rate, pins: 31% miss rate)
4. **Improving steadily** (+127 rating in 6 months)

**Recommendations:**
1. Continue Sicilian, drop French Defense (32% win rate)
2. Practice tactics specifically: pin positions
3. Play longer time controls (10+0 instead of 3+0) to reduce time pressure blunders
4. Focus training on endgame technique (conversion rate: 64%, should be 80%+)

**Time to generate:** 3 minutes
**Time to review:** 10-15 minutes
**Actionability:** High (specific openings, specific tactical themes, specific time controls)

---

## FAQ

**Q: Will this make me a better chess player?**
A: If you act on the insights, yes. It's like having a coach point out patterns you can't see yourself.

**Q: How much data do I need?**
A: Minimum 20 games for useful insights. 50+ games for reliable patterns.

**Q: Does it work for other chess sites (Lichess)?**
A: Not yet. Chess.com only for now.

**Q: What ratings is this useful for?**
A: 800-2200. Below 800: focus on basic tactics first. Above 2200: you probably don't need this.

**Q: How often should I run analysis?**
A: Monthly is good. More frequent = less data = noisier insights.

**Q: Can I analyze other players?**
A: Yes, if their games are public. Just change the username in `.env`.

---

## Development

### Running Tests

```bash
# All tests
pytest tests/ -v

# Just unit tests (fast)
pytest tests/test_basic_functionality.py -v

# Integration tests (requires API)
pytest tests/test_integration.py -v
```

### Contributing

PRs welcome. Guidelines:
- Keep it simple (reject feature bloat)
- Focus on chess value (not tech demos)
- Test with real games
- Update documentation

**See experimental work at:** [vds4321/chessAnalysit](https://github.com/vds4321/chessAnalysit)

---

## Roadmap

**Current (v1.0):**
- ✅ Opening performance analysis
- ✅ Tactical mistake detection
- ✅ Progression tracking
- ✅ ML-based opening recommendations

**Planned (v2.0):**
- [ ] LLM-enhanced coaching (explain *why* mistakes happen)
- [ ] Personalized training plans
- [ ] Lichess integration
- [ ] Position-specific drill recommendations

**Not Planned:**
- Real-time game analysis (use Chess.com's built-in analysis)
- Opening database (use dedicated opening tools)
- Playing engine (use Stockfish directly)

---

## Credits

**Built by:** [vds4321](https://github.com/vds4321)
**Inspired by:** Too many blunders in time pressure
**Powered by:**
- [python-chess](https://github.com/niklasf/python-chess) - Chess logic
- [Stockfish](https://stockfishchess.org/) - Position evaluation
- [Chess.com API](https://www.chess.com/news/view/published-data-api) - Game data

---

## License

MIT License - Use it, modify it, share it.

If this helps your chess, ⭐ the repo.

---

**Stop guessing. Start knowing.**

Built by a chess enthusiast for chess enthusiasts.
