import pygame
from const import *
from board import Board
from dragger import Dragger

class Game:
    def __init__(self):
        self.next_player = "white"
        self.hovered_sqr = None
        self.board = Board() 
        self.dragger = Dragger()
        self.promotion_menu = False

    def show_bg(self, surface):  # this is going to be a show methods 
        for row in range(ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 0:
                    color = (234, 235, 200) # light green
                else:
                    color = (199, 154, 88) # dark green
                
                rect = (col * SQSIZE, row * SQSIZE, SQSIZE, SQSIZE)

                pygame.draw.rect(surface, color, rect)

    def show_pieces(self, surface):
        for row in range(ROWS):
            for col in range(COLS):
                if self.board.squares[row][col].has_piece():
                    piece = self.board.squares[row][col].piece

                    # all except dragging piece
                    if piece is not self.dragger.piece:
                        piece.set_texture(size=80)
                        img = pygame.image.load(piece.texture)
                        img_center = col * SQSIZE + SQSIZE // 2, row * SQSIZE + SQSIZE // 2
                        piece.texture_rect = img.get_rect(center=img_center)
                        surface.blit(img, piece.texture_rect)

    def show_moves(self, surface):
        if self.dragger.dragging:
            piece = self.dragger.piece

            # loop all valid moves
            for move in piece.moves:
                # color
                color = '#C86464' if (move.final.row + move.final.col) % 2 == 0 else '#844646'
                # rect
                rect = (move.final.col * SQSIZE, move.final.row * SQSIZE, SQSIZE, SQSIZE)
                # blit
                pygame.draw.rect(surface, color, rect)

    def show_last_move(self, surface):
        if self.board.last_move:
            initial = self.board.last_move.initial
            final = self.board.last_move.final

            for pos in [initial, final]:
                # color
                color = (244,247,116) if (pos.row + pos.col) % 2 == 0 else (172,195,51)
                # rect
                rect = (pos.col * SQSIZE, pos.row * SQSIZE, SQSIZE, SQSIZE)
                # blit
                pygame.draw.rect(surface, color, rect)

    def show_hover(self, surface):
        if self.hovered_sqr:
            # color
            color = (180,180,180)
            # rect
            rect = (self.hovered_sqr.col * SQSIZE, self.hovered_sqr.row * SQSIZE, SQSIZE, SQSIZE)
            # blit
            pygame.draw.rect(surface, color, rect, width=3)

    def show_promotion_menu(self, surface):
        """menu for choice in pawn promotion"""
        if not self.board.promotion_pending:
            return

        # alpha move bg
        overlay = pygame.Surface((WIDTH, HIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        # menu size
        menu_width = 400
        menu_height = 150
        menu_x = (WIDTH - menu_width) // 2
        menu_y = (HIGHT - menu_height) // 2

        # bg menu
        pygame.draw.rect(surface, (240, 240, 240), (menu_x, menu_y, menu_width, menu_height))
        pygame.draw.rect(surface, (0, 0, 0), (menu_x, menu_y, menu_width, menu_height), 3)

        # Title
        font = pygame.font.Font(None, 36)
        text = font.render("Выберите фигуру для промоции:", True, (0, 0, 0))
        text_rect = text.get_rect(center=(menu_x + menu_width // 2, menu_y + 30))
        surface.blit(text, text_rect)

        # pieces variants choice
        pieces = ['queen', 'rook', 'bishop', 'knight']
        piece_size = 60
        spacing = (menu_width - 4 * piece_size) // 5
        color = self.board.promotion_pending['color']

        for i, piece_name in enumerate(pieces):
            x = menu_x + spacing + i * (piece_size + spacing)
            y = menu_y + 70

            # bg for pieces
            pygame.draw.rect(surface, (255, 255, 255), (x, y, piece_size, piece_size))
            pygame.draw.rect(surface, (0, 0, 0), (x, y, piece_size, piece_size), 2)

            try:
                piece_image_path = f'assets/images/imgs-80px/{color}_{piece_name}.png'
                piece_img = pygame.image.load(piece_image_path)
                img_rect = piece_img.get_rect(center=(x + piece_size // 2, y + piece_size // 2))
                surface.blit(piece_img, img_rect)
            except pygame.error:
                font_small = pygame.font.Font(None, 24)
                text = font_small.render(piece_name[0].upper(), True, (0, 0, 0))
                text_rect = text.get_rect(center=(x + piece_size // 2, y + piece_size // 2))
                surface.blit(text, text_rect)

    def handle_promotion_click(self, pos):
        """hanlde click on piece in promotion choice"""
        if not self.board.promotion_pending:
            return None

        menu_width = 400
        menu_height = 150
        menu_x = (WIDTH - menu_width) // 2
        menu_y = (HIGHT - menu_height) // 2

        if (menu_x <= pos[0] <= menu_x + menu_width and 
            menu_y + 70 <= pos[1] <= menu_y + 70 + 60):
            
            pieces = ['queen', 'rook', 'bishop', 'knight']
            piece_size = 60
            spacing = (menu_width - 4 * piece_size) // 5
            
            for i, piece_name in enumerate(pieces):
                x = menu_x + spacing + i * (piece_size + spacing)
                if x <= pos[0] <= x + piece_size:
                    return piece_name
        
        return None

    # other methods

    def next_turn(self):
        self.next_player = "white" if self.next_player == "black" else "black"

    def set_hover(self, row, col):
        self.hovered_sqr = self.board.squares[row][col]

    def reset(self):
        self.__init__()