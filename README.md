# Chess Analysis Application

A comprehensive Python-based tool for analyzing your Chess.com games to identify patterns, strengths, weaknesses, and areas for improvement.

## 🎯 Features

### Core Analysis
- **Opening Performance**: Analyze success rates, preparation depth, and repertoire gaps
- **Tactical Analysis**: Identify blunders, missed opportunities, and tactical patterns
- **Progression Analysis**: Track performance evolution and improvement trends over time
- **Time Management**: Analyze time usage patterns and efficiency
- **Rating Progression**: Monitor performance trends over time

### Interactive Interface
- **Jupyter Notebooks**: Rich, interactive analysis with visualizations
- **Comprehensive Reports**: Detailed insights with actionable recommendations
- **Visual Charts**: Performance trends, opening statistics, and pattern analysis
- **Export Capabilities**: Save analysis results for further study

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Chess.com account with game history
- Stockfish chess engine (optional, for advanced position analysis)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chessAnalysit
   ```

2. **Create virtual environment**
   ```bash
   python -m venv chess_analysis_env
   source chess_analysis_env/bin/activate  # On Windows: chess_analysis_env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # For full installation with all features
   pip install -r requirements.txt
   
   # Or for minimal installation
   pip install -r requirements_simple.txt
   ```

4. **Install Stockfish** (optional, for advanced analysis)
   - **macOS**: `brew install stockfish`
   - **Ubuntu/Debian**: `sudo apt-get install stockfish`
   - **Windows**: Download from [Stockfish website](https://stockfishchess.org/download/)

5. **Configure settings**
   ```bash
   cp config/.env.example .env
   # Edit .env file with your Chess.com username and Stockfish path
   ```

### Basic Usage

1. **Test the installation**
   ```bash
   python tests/test_basic_functionality.py
   ```

2. **Start Jupyter Notebook**
   ```bash
   jupyter notebook notebooks/main_analysis.ipynb
   ```

3. **Update Configuration**
   - Set your Chess.com username in the notebook
   - Choose analysis period (e.g., last 6 months)
   - Select time controls to analyze

4. **Run Analysis**
   - Execute notebook cells step by step
   - Download and parse your games
   - Generate comprehensive analysis reports

## 📊 Analysis Modules

### Opening Analyzer
```python
from src.analyzers.opening_analyzer import OpeningAnalyzer

analyzer = OpeningAnalyzer()
opening_analysis = analyzer.analyze_opening_performance(parsed_games)
recommendations = analyzer.get_opening_recommendations(opening_analysis)
```

**Features:**
- Success rates by opening variation
- ECO code classification
- Preparation depth analysis
- Color-specific performance
- Repertoire gap identification

### Tactical Analyzer
```python
from src.analyzers.tactical_analyzer import TacticalAnalyzer

analyzer = TacticalAnalyzer()
tactical_analysis = analyzer.analyze_tactical_patterns(parsed_games)
recommendations = analyzer.get_tactical_recommendations(tactical_analysis)
```

**Features:**
- Move quality classification (blunders, mistakes, inaccuracies)
- Tactical pattern recognition
- Position evaluation with Stockfish
- Accuracy calculations
- Time pressure impact analysis

### Progression Analyzer
```python
from src.analyzers.progression_analyzer import ProgressionAnalyzer

analyzer = ProgressionAnalyzer()
progression_data = analyzer.analyze_progression(parsed_games)
recommendations = analyzer.get_progression_recommendations(progression_data)
```

**Features:**
- Rating progression over time
- Accuracy trend analysis
- Opening repertoire evolution
- Time management improvement
- Playing style development
- Consistency metrics

### Game Parser
```python
from src.game_parser import GameParser

parser = GameParser()
parsed_games = parser.parse_games_batch(raw_games)
```

**Features:**
- PGN parsing and validation
- Move-by-move analysis with Stockfish
- Time extraction and calculation
- Game phase identification
- Move quality classification

### Data Fetcher
```python
from src.data_fetcher import ChessComDataFetcher

fetcher = ChessComDataFetcher("your_username")
games = fetcher.get_all_games(start_date=start_date, end_date=end_date)
```

**Features:**
- Chess.com API integration
- Automatic rate limiting
- Response caching
- Date range filtering
- Progress tracking

## 📁 Project Structure

```
chessAnalysit/
├── src/                          # Core application code
│   ├── data_fetcher.py          # Chess.com API integration
│   ├── game_parser.py           # PGN parsing and analysis
│   ├── analyzers/               # Analysis modules
│   │   ├── opening_analyzer.py  # Opening performance analysis
│   │   ├── tactical_analyzer.py # Tactical pattern analysis
│   │   └── progression_analyzer.py # Performance progression analysis
│   ├── scripts/                 # Standalone analysis scripts
│   │   ├── quick_analysis.py    # Quick analysis runner
│   │   └── run_tactical_analysis.py # Tactical analysis runner
│   ├── visualizers/             # Chart generation modules
│   └── utils/                   # Utility functions
├── notebooks/                   # Interactive analysis notebooks
│   ├── main_analysis.ipynb      # Main dashboard
│   ├── progression_analysis.ipynb # Progression tracking
│   └── data/                    # Notebook-specific data storage
│       ├── raw/                 # Downloaded games for notebooks
│       ├── processed/           # Analyzed games for notebooks
│       └── cache/               # API response cache for notebooks
├── data/                        # Centralized data storage
│   ├── raw/                     # Downloaded games
│   ├── processed/               # Analyzed games
│   └── cache/                   # API response cache
├── config/                      # Configuration files
├── tests/                       # Test files
│   ├── test_basic_functionality.py # Comprehensive functionality test
│   └── test_imports_only.py     # Import validation test
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md          # System architecture
│   ├── IMPLEMENTATION_GUIDE.md  # Implementation details
│   ├── PROJECT_SUMMARY.md       # Project overview
│   └── TECHNICAL_SPECS.md       # Technical specifications
├── requirements.txt             # Full dependencies
├── requirements_simple.txt      # Minimal dependencies
├── QUICK_START.md              # Quick start guide
└── README.md                   # This file
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Chess.com Configuration
CHESS_COM_USERNAME=your_username_here

# Stockfish Configuration
STOCKFISH_PATH=/usr/local/bin/stockfish

# Analysis Configuration
ANALYSIS_DEPTH=15
```

### Analysis Parameters (config/settings.py)
```python
# Move classification thresholds (centipawns)
BLUNDER_THRESHOLD = 200
MISTAKE_THRESHOLD = 100
INACCURACY_THRESHOLD = 50

# Time controls to analyze
TIME_CONTROLS = ["bullet", "blitz", "rapid"]

# Opening analysis settings
OPENING_BOOK_DEPTH = 15
TIME_PRESSURE_THRESHOLD = 30
```

## 📈 Sample Insights

### Opening Performance
- "Your Sicilian Defense has a 65% win rate, but your French Defense only 45%"
- "You perform 150 rating points better in the Ruy Lopez when you castle early"
- "Your opening preparation averages 12 moves, but drops to 8 in time pressure"

### Tactical Analysis
- "You miss 23% of tactical opportunities in positions with <30 seconds remaining"
- "Your blunder rate increases 3x when your opponent's rating is >100 points higher"
- "Fork patterns are your strongest tactical motif (85% success rate)"

### Progression Analysis
- "Your accuracy has improved from 75% to 82% over the last 6 months"
- "Your opening repertoire has expanded by 40% this year"
- "You show consistent improvement in endgame conversion rates"

### Time Management
- "You spend 40% of your time on the first 15 moves but only 20% on critical decisions"
- "Your accuracy drops from 85% to 65% when you have <10% time remaining"
- "You perform best in 10+0 time control with 72% win rate"

## 🛠️ Development

### Running Tests
```bash
# Run comprehensive functionality test
python tests/test_basic_functionality.py

# Run import validation test
python tests/test_imports_only.py

# Run unit tests (if available)
pytest tests/
```

### Code Formatting
```bash
black src/
flake8 src/
```

### Adding New Analyzers
1. Create new analyzer in `src/analyzers/`
2. Implement analysis methods following existing patterns
3. Add visualization components
4. Update notebooks with new analysis

## 📚 API Reference

### ChessComDataFetcher
- `get_player_profile()` - Get player information
- `get_available_archives()` - Get list of available game archives
- `get_games_for_month(year, month)` - Get games for specific month
- `get_all_games(start_date, end_date)` - Download games in date range
- `save_games_to_file(games, filename)` - Save games to JSON file

### GameParser
- `parse_chess_com_game(game_data)` - Parse single game
- `parse_games_batch(games_data)` - Parse multiple games
- `_analyze_moves(game, player_color)` - Analyze move sequence
- `_classify_move(board, move, evaluation, best_move)` - Classify move quality

### OpeningAnalyzer
- `analyze_opening_performance(games_data)` - Analyze opening statistics
- `get_opening_recommendations(opening_analysis)` - Generate recommendations
- `analyze_color_preferences(games_data)` - Color-specific analysis
- `get_opening_trends(games_data)` - Opening trend analysis

### TacticalAnalyzer
- `analyze_game_tactics(pgn_string, player_name)` - Analyze single game tactics
- `analyze_tactical_patterns(games_data)` - Analyze tactical patterns across games
- `get_tactical_recommendations(tactical_analysis)` - Generate tactical recommendations

### ProgressionAnalyzer
- `analyze_progression(games_data)` - Comprehensive progression analysis
- `get_progression_recommendations(progression_data)` - Generate improvement recommendations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [python-chess](https://github.com/niklasf/python-chess) - Chess library for Python
- [Stockfish](https://stockfishchess.org/) - Chess engine for position analysis
- [Chess.com](https://chess.com) - Game data source
- [Plotly](https://plotly.com/) - Interactive visualizations

## 🐛 Troubleshooting

### Common Issues

**"Import chess could not be resolved"**
- Install python-chess: `pip install python-chess`

**"Stockfish engine not found"**
- Install Stockfish and update path in `.env` file
- Check path with: `which stockfish` (macOS/Linux) or `where stockfish` (Windows)

**"No games found"**
- Verify Chess.com username is correct
- Check if games are public (required for API access)
- Ensure date range includes games

**"API rate limiting"**
- The application handles rate limiting automatically
- If issues persist, wait a few minutes and retry

**"Dependencies missing"**
- Run the test script: `python tests/test_basic_functionality.py`
- Install missing packages: `pip install -r requirements.txt`

### Getting Help

- Run the comprehensive test: `python tests/test_basic_functionality.py`
- Check the [QUICK_START.md](QUICK_START.md) for step-by-step instructions
- Review the [docs/PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md) for project overview
- Check the [docs/TECHNICAL_SPECS.md](docs/TECHNICAL_SPECS.md) for advanced configuration
- Check the [Issues](../../issues) page for known problems
- Create a new issue with detailed error information
- Include your Python version, OS, and error messages

## 🔮 Future Enhancements

- [ ] Integration with Lichess API
- [ ] Machine learning models for pattern prediction
- [ ] Mobile-friendly web interface
- [ ] Comparative analysis with similar-rated players
- [ ] Tournament performance analysis
- [ ] Opening repertoire builder
- [ ] Automated training recommendations
- [ ] Endgame-specific analyzer
- [ ] Time management analyzer
- [ ] Rating-specific analyzer

---

**Happy analyzing!** 🚀♟️