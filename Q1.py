import chess
import pygame
import sys
import random
from pygame.locals import *

# Initialize pygame
pygame.init()

# Constants
SQUARE_SIZE = 80
BOARD_SIZE = 8 * SQUARE_SIZE
WINDOW_SIZE = (BOARD_SIZE, BOARD_SIZE)
FPS = 30

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT = (255, 255, 0, 50)  # Semi-transparent yellow

# Set up the display
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption('Chess Game with Alpha-Beta AI')
clock = pygame.time.Clock()

# Load chess piece images
piece_images = {}
pieces_map = {
    'wp': 'white-pawn.png', 'wn': 'white-knight.png', 'wb': 'white-bishop.png', 'wr': 'white-rook.png', 'wq': 'white-queen.png', 'wk': 'white-king.png',
    'bp': 'black-pawn.png', 'bn': 'black-knight.png', 'bb': 'black-bishop.png', 'br': 'black-rook.png', 'bq': 'black-queen.png', 'bk': 'black-king.png'
}

for piece_id, filename in pieces_map.items():
    try:
        # This uses a relative path, which is more robust
        image_path = f"images/{filename}"
        img = pygame.image.load(image_path)
        img = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))
        piece_images[piece_id] = img
    except pygame.error:
        print(f"Warning: Could not load image for {piece_id} from {image_path}")
        # Create a placeholder image if loading fails
        img = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(img, (255, 0, 0, 128), (0, 0, SQUARE_SIZE, SQUARE_SIZE))
        piece_images[piece_id] = img
# Function to evaluate the chess board
def evaluate_board(board):
    """
    Evaluate the current board state.
    Returns a score where positive values favor White and negative values favor Black.
    """
    # Terminal states
    if board.is_checkmate():
        return -10000 if board.turn else 10000
    
    if board.is_stalemate() or board.is_insufficient_material():
        return 0  # Draw
    
    # Piece values (standard chess piece weights)
    piece_values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000  # High value for the king
    }
    
    # Material score calculation
    material_score = 0
    for piece_type in piece_values:
        material_score += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
        material_score -= len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]
    
    # Positional considerations
    positional_score = 0
    
    # Central control bonus
    central_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
    for square in central_squares:
        piece = board.piece_at(square)
        if piece:
            if piece.color == chess.WHITE:
                positional_score += 10
            else:
                positional_score -= 10
    
    # Development bonus
    knights_bishops = [chess.KNIGHT, chess.BISHOP]
    for piece_type in knights_bishops:
        for square in board.pieces(piece_type, chess.WHITE):
            # Encourage development from back rank
            rank = chess.square_rank(square)
            if rank > 0:  # Piece has moved from back rank
                positional_score += 5
                
        for square in board.pieces(piece_type, chess.BLACK):
            # Encourage development from back rank
            rank = chess.square_rank(square)
            if rank < 7:  # Piece has moved from back rank
                positional_score -= 5
    
    # Combine scores
    total_score = material_score + positional_score
    
    return total_score

# Alpha-Beta pruning algorithm
def alpha_beta(board, depth, alpha, beta):
    """
    Alpha-beta pruning algorithm.
    Returns the evaluation score of the best move from the current position.
    """
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)
    
    if board.turn:  # White's turn (maximizing)
        max_value = float('-inf')
        for move in board.legal_moves:
            board.push(move)
            eval = alpha_beta(board, depth - 1, alpha, beta)
            board.pop()
            max_value = max(max_value, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break  # Beta cutoff
        return max_value
    else:  # Black's turn (minimizing)
        min_value = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval = alpha_beta(board, depth - 1, alpha, beta)
            board.pop()
            min_value = min(min_value, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break  # Alpha cutoff
        return min_value

# Function to get the best move using alpha-beta pruning
def get_best_move(board, depth=3, alpha=float('-inf'), beta=float('inf')):
    """
    Find the best move for the current player using alpha-beta pruning.
    """
    best_move = None
    
    if board.turn:  # White's turn (maximizing)
        best_value = float('-inf')
        for move in board.legal_moves:
            board.push(move)
            move_value = alpha_beta(board, depth - 1, alpha, beta)
            board.pop()
            
            if move_value > best_value:
                best_value = move_value
                best_move = move
            
            alpha = max(alpha, best_value)
    else:  # Black's turn (minimizing)
        best_value = float('inf')
        for move in board.legal_moves:
            board.push(move)
            move_value = alpha_beta(board, depth - 1, alpha, beta)
            board.pop()
            
            if move_value < best_value:
                best_value = move_value
                best_move = move
            
            beta = min(beta, best_value)
    
    # If no best move found (unlikely), choose a random move
    if best_move is None and board.legal_moves:
        best_move = random.choice(list(board.legal_moves))
        
    return best_move

# Draw the board and pieces
def draw_board(board, selected_square=None):
    """Draw the chess board and pieces"""
    # Draw the squares
    for row in range(8):
        for col in range(8):
            color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
    
    # Highlight selected square if any
    if selected_square is not None:
        col, row = selected_square % 8, 7 - (selected_square // 8)
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        s.fill(HIGHLIGHT)
        screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
    
    # Draw the pieces
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            # Convert chess square to row, col
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)  # Invert row because chess uses 1-8 from bottom to top
            
            piece_id = ('w' if piece.color else 'b') + piece.symbol().lower()
            if piece_id in piece_images:
                screen.blit(piece_images[piece_id], (col * SQUARE_SIZE, row * SQUARE_SIZE))
            else:
                print(f"Missing image for piece: {piece_id}")

# Convert mouse position to chess square
def get_square_from_pos(pos):
    """Convert mouse position to chess square"""
    col = pos[0] // SQUARE_SIZE
    row = pos[1] // SQUARE_SIZE
    # Convert to chess.py's square representation (0-63, a1 is 0, h8 is 63)
    square = chess.square(col, 7 - row)
    return square

# Main game function
def main():
    # Create a new chess board
    board = chess.Board()
    
    # Ask player to choose color
    print("Welcome to Chess with Alpha-Beta AI!")
    player_color = None
    while player_color not in [chess.WHITE, chess.BLACK]:
        choice = input("Do you want to play as White or Black? (w/b): ").lower()
        if choice == 'w':
            player_color = chess.WHITE
        elif choice == 'b':
            player_color = chess.BLACK
        else:
            print("Invalid input. Please enter 'w' for White or 'b' for Black.")
    
    human_turn = player_color == board.turn
    selected_square = None
    moves_from_selected = []
    
    running = True
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            
            if human_turn and event.type == MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                square = get_square_from_pos(pos)
                
                # If a square is already selected
                if selected_square is not None:
                    # Try to make a move
                    move = chess.Move(selected_square, square)
                    
                    # Check for pawn promotion
                    if (board.piece_at(selected_square) 
                        and board.piece_at(selected_square).piece_type == chess.PAWN 
                        and (chess.square_rank(square) == 0 or chess.square_rank(square) == 7)):
                        move = chess.Move(selected_square, square, promotion=chess.QUEEN)
                    
                    # If the move is legal, make it
                    if move in board.legal_moves:
                        board.push(move)
                        print(f"Human move: {move.uci()}")
                        human_turn = False
                        selected_square = None
                        moves_from_selected = []
                    else:
                        # If the square contains a piece of the player's color, select it
                        piece = board.piece_at(square)
                        if piece and piece.color == player_color:
                            selected_square = square
                            # Find all legal moves from this square
                            moves_from_selected = [move for move in board.legal_moves if move.from_square == square]
                        else:
                            selected_square = None
                            moves_from_selected = []
                else:
                    # Select the square if it contains a piece of the player's color
                    piece = board.piece_at(square)
                    if piece and piece.color == player_color:
                        selected_square = square
                        # Find all legal moves from this square
                        moves_from_selected = [move for move in board.legal_moves if move.from_square == square]
        
        # AI's turn
        if not human_turn and not board.is_game_over():
            print("AI is thinking...")
            ai_move = get_best_move(board, depth=3)  # Adjust depth for stronger AI (3-4 is reasonable)
            if ai_move:
                board.push(ai_move)
                print(f"AI move: {ai_move.uci()}")
            human_turn = True
        
        # Draw the board
        draw_board(board, selected_square)
        
        # Display game status
        if board.is_checkmate():
            winner = "Black" if board.turn == chess.WHITE else "White"
            print(f"Checkmate! {winner} wins.")
            running = False
        elif board.is_stalemate() or board.is_insufficient_material():
            print("Game drawn.")
            running = False
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()