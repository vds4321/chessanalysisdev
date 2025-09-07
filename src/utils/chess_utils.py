"""
Chess Utilities

Common utility functions for chess analysis.
"""

import chess
import chess.pgn
from typing import Dict, List, Optional, Tuple
import re


def parse_time_control(time_control: str) -> Dict[str, int]:
    """
    Parse time control string into components.
    
    Args:
        time_control: Time control string (e.g., "600", "180+2", "300+5")
        
    Returns:
        Dictionary with base_time and increment in seconds
    """
    if not time_control:
        return {'base_time': 0, 'increment': 0}
    
    # Handle different formats
    if '+' in time_control:
        parts = time_control.split('+')
        base_time = int(parts[0]) if parts[0].isdigit() else 0
        increment = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    else:
        base_time = int(time_control) if time_control.isdigit() else 0
        increment = 0
    
    return {'base_time': base_time, 'increment': increment}


def classify_time_control(time_control: str) -> str:
    """
    Classify time control into standard categories.
    
    Args:
        time_control: Time control string
        
    Returns:
        Time control category (bullet, blitz, rapid, classical)
    """
    time_info = parse_time_control(time_control)
    total_time = time_info['base_time'] + time_info['increment'] * 40  # Estimate for 40 moves
    
    if total_time < 180:  # Less than 3 minutes
        return 'bullet'
    elif total_time < 600:  # Less than 10 minutes
        return 'blitz'
    elif total_time < 1800:  # Less than 30 minutes
        return 'rapid'
    else:
        return 'classical'


def get_game_phase(move_number: int, total_moves: int, piece_count: Optional[int] = None) -> str:
    """
    Determine game phase based on move number and piece count.
    
    Args:
        move_number: Current move number
        total_moves: Total moves in the game
        piece_count: Number of pieces on board (optional)
        
    Returns:
        Game phase (opening, middlegame, endgame)
    """
    if piece_count and piece_count <= 6:
        return 'endgame'
    
    if move_number <= 15:
        return 'opening'
    elif move_number > total_moves * 0.7:
        return 'endgame'
    else:
        return 'middlegame'


def extract_eco_code(pgn_headers: Dict[str, str]) -> str:
    """
    Extract ECO code from PGN headers.
    
    Args:
        pgn_headers: Dictionary of PGN headers
        
    Returns:
        ECO code or empty string if not found
    """
    return pgn_headers.get('ECO', '')


def extract_opening_name(pgn_headers: Dict[str, str]) -> str:
    """
    Extract opening name from PGN headers.
    
    Args:
        pgn_headers: Dictionary of PGN headers
        
    Returns:
        Opening name or 'Unknown' if not found
    """
    return pgn_headers.get('Opening', 'Unknown')


def count_pieces(fen: str) -> int:
    """
    Count total pieces on board from FEN string.
    
    Args:
        fen: FEN position string
        
    Returns:
        Total number of pieces on board
    """
    if not fen:
        return 32
    
    board_part = fen.split()[0]
    piece_count = 0
    
    for char in board_part:
        if char.isalpha():
            piece_count += 1
    
    return piece_count


def is_endgame_position(fen: str) -> bool:
    """
    Determine if position is an endgame based on material.
    
    Args:
        fen: FEN position string
        
    Returns:
        True if position is considered endgame
    """
    piece_count = count_pieces(fen)
    return piece_count <= 6


def calculate_material_balance(fen: str) -> int:
    """
    Calculate material balance from white's perspective.
    
    Args:
        fen: FEN position string
        
    Returns:
        Material balance in centipawns (positive = white advantage)
    """
    if not fen:
        return 0
    
    piece_values = {
        'P': 100, 'N': 300, 'B': 300, 'R': 500, 'Q': 900,
        'p': -100, 'n': -300, 'b': -300, 'r': -500, 'q': -900
    }
    
    board_part = fen.split()[0]
    balance = 0
    
    for char in board_part:
        if char in piece_values:
            balance += piece_values[char]
    
    return balance


def parse_clock_time(clock_string: str) -> int:
    """
    Parse clock time string to seconds.
    
    Args:
        clock_string: Clock time string (e.g., "0:05:23")
        
    Returns:
        Time in seconds
    """
    if not clock_string:
        return 0
    
    # Remove brackets and %clk if present
    clean_time = clock_string.replace('[%clk ', '').replace(']', '')
    
    # Parse H:M:S format
    time_pattern = r'(\d+):(\d+):(\d+)'
    match = re.match(time_pattern, clean_time)
    
    if match:
        hours, minutes, seconds = map(int, match.groups())
        return hours * 3600 + minutes * 60 + seconds
    
    return 0


def format_time(seconds: int) -> str:
    """
    Format seconds into H:M:S string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    if seconds < 0:
        return "0:00:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    return f"{hours}:{minutes:02d}:{secs:02d}"


def get_piece_square_value(piece: str, square: str, endgame: bool = False) -> int:
    """
    Get piece-square table value for positional evaluation.
    
    Args:
        piece: Piece character (e.g., 'P', 'N', 'B', 'R', 'Q', 'K')
        square: Square name (e.g., 'e4')
        endgame: Whether position is endgame
        
    Returns:
        Piece-square value in centipawns
    """
    # Simplified piece-square tables
    # In a real implementation, these would be more comprehensive
    
    if not square or len(square) != 2:
        return 0
    
    file_idx = ord(square[0]) - ord('a')  # 0-7
    rank_idx = int(square[1]) - 1  # 0-7
    
    # Center squares are generally better
    center_bonus = 0
    if 2 <= file_idx <= 5 and 2 <= rank_idx <= 5:
        center_bonus = 10
    if 3 <= file_idx <= 4 and 3 <= rank_idx <= 4:
        center_bonus = 20
    
    piece_bonuses = {
        'P': center_bonus // 2,  # Pawns benefit less from center
        'N': center_bonus,       # Knights love the center
        'B': center_bonus // 2,  # Bishops like center but also diagonals
        'R': 0,                  # Rooks are more about files/ranks
        'Q': center_bonus // 3,  # Queen is powerful anywhere
        'K': -center_bonus if not endgame else center_bonus  # King safety vs activity
    }
    
    return piece_bonuses.get(piece.upper(), 0)


def analyze_pawn_structure(fen: str) -> Dict[str, int]:
    """
    Analyze pawn structure from FEN.
    
    Args:
        fen: FEN position string
        
    Returns:
        Dictionary with pawn structure metrics
    """
    if not fen:
        return {}
    
    board = chess.Board(fen)
    
    white_pawns = []
    black_pawns = []
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.piece_type == chess.PAWN:
            file_idx = chess.square_file(square)
            rank_idx = chess.square_rank(square)
            
            if piece.color == chess.WHITE:
                white_pawns.append((file_idx, rank_idx))
            else:
                black_pawns.append((file_idx, rank_idx))
    
    # Count doubled pawns
    white_files = [f for f, r in white_pawns]
    black_files = [f for f, r in black_pawns]
    
    white_doubled = sum(1 for f in range(8) if white_files.count(f) > 1)
    black_doubled = sum(1 for f in range(8) if black_files.count(f) > 1)
    
    # Count isolated pawns (simplified)
    white_isolated = 0
    black_isolated = 0
    
    for f in range(8):
        if f in white_files:
            adjacent_files = [f-1, f+1]
            if not any(af in white_files for af in adjacent_files if 0 <= af <= 7):
                white_isolated += white_files.count(f)
        
        if f in black_files:
            adjacent_files = [f-1, f+1]
            if not any(af in black_files for af in adjacent_files if 0 <= af <= 7):
                black_isolated += black_files.count(f)
    
    return {
        'white_pawns': len(white_pawns),
        'black_pawns': len(black_pawns),
        'white_doubled': white_doubled,
        'black_doubled': black_doubled,
        'white_isolated': white_isolated,
        'black_isolated': black_isolated
    }


def get_tactical_motifs(board: chess.Board) -> List[str]:
    """
    Identify potential tactical motifs in position.
    
    Args:
        board: Chess board position
        
    Returns:
        List of potential tactical motifs
    """
    motifs = []
    
    # This is a simplified implementation
    # A real implementation would use more sophisticated pattern recognition
    
    # Check for pins
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
            # Simplified pin detection would go here
            pass
    
    # Check for forks
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.piece_type == chess.KNIGHT:
            # Simplified fork detection would go here
            pass
    
    # Check for skewers
    # Simplified skewer detection would go here
    
    return motifs


def estimate_position_complexity(board: chess.Board) -> int:
    """
    Estimate position complexity based on various factors.
    
    Args:
        board: Chess board position
        
    Returns:
        Complexity score (0-100)
    """
    complexity = 0
    
    # More pieces = more complex
    piece_count = len(board.piece_map())
    complexity += min(piece_count * 2, 40)
    
    # More legal moves = more complex
    legal_moves = len(list(board.legal_moves))
    complexity += min(legal_moves, 30)
    
    # Tactical elements add complexity
    if board.is_check():
        complexity += 10
    
    # Pawn structure complexity
    pawn_structure = analyze_pawn_structure(board.fen())
    if pawn_structure:
        complexity += (pawn_structure.get('white_doubled', 0) + 
                      pawn_structure.get('black_doubled', 0)) * 2
    
    return min(complexity, 100)