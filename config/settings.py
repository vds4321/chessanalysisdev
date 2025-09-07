import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Chess.com API settings
    CHESS_COM_BASE_URL = "https://api.chess.com/pub"
    
    # User settings
    CHESS_COM_USERNAME = os.getenv("CHESS_COM_USERNAME", "")
    
    # Analysis settings
    STOCKFISH_PATH = os.getenv("STOCKFISH_PATH", "/usr/local/bin/stockfish")
    ANALYSIS_DEPTH = int(os.getenv("ANALYSIS_DEPTH", "15"))
    
    # Data storage paths
    DATA_DIR = "data"
    RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
    PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
    CACHE_DIR = os.path.join(DATA_DIR, "cache")
    
    # Analysis parameters
    BLUNDER_THRESHOLD = 200  # centipawns
    MISTAKE_THRESHOLD = 100  # centipawns
    INACCURACY_THRESHOLD = 50  # centipawns
    
    # Time controls to analyze
    TIME_CONTROLS = ["bullet", "blitz", "rapid"]
    
    # API settings
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    
    # Analysis settings
    OPENING_BOOK_DEPTH = 15  # moves to consider as opening
    TIME_PRESSURE_THRESHOLD = 30  # seconds
    ENDGAME_PIECE_THRESHOLD = 6  # pieces remaining
    TACTICAL_SEARCH_DEPTH = 12  # ply for tactical analysis
    EVALUATION_MARGIN = 25  # centipawns for "equal" positions