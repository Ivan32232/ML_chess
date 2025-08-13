from const import *
from square import Square
from piece import *
from move import Move
import copy

class Board:
    def __init__(self):
        self.squares = [[0, 0, 0, 0, 0, 0, 0, 0,] for col in range(COLS)]
        self.last_move = None
        self.promotion_pending = None  # info о промоции
        self.game_over = None  # None, 'white', 'black', 'stalemate'
        self._create()
        self._add_pieces("white")
        self._add_pieces('black')

    def move(self, piece, move):
        initial = move.initial
        final = move.final

        en_passant_empty = self.squares[final.row][final.col].isempty()

        # console board move update
        self.squares[initial.row][initial.col].piece = None
        self.squares[final.row][final.col].piece = piece

        # pawn en passant 
        # pawn promotion
        if isinstance(piece, Pawn):
            diff = final.col - initial.col
            if diff != 0 and en_passant_empty:
                # console board move update
                self.squares[initial.row][initial.col + diff].piece = None
                self.squares[final.row][final.col].piece = piece

            if self.check_promotion_needed(piece, final):
                self.promotion_pending = {
                    'piece': piece,
                    'position': final,
                    'color': piece.color
                }
                return True  # Возвращаем True, чтобы указать, что нужна промоция

        # king castling - ИСПРАВЛЕНИ
        if isinstance(piece, King):
            if self.casteling(initial, final):
                diff = final.col - initial.col
                rook = piece.left_rook if (diff < 0) else piece.right_rook
                if rook and len(rook.moves) > 0:
                    # Перемещаем ладью напрямую без рекурсивного вызова move
                    rook_move = rook.moves[-1]
                    self.squares[rook_move.initial.row][rook_move.initial.col].piece = None
                    self.squares[rook_move.final.row][rook_move.final.col].piece = rook
                    rook.moved = True
                    rook.clear_moves()

        # move
        piece.moved = True

        # clear valid moves
        piece.clear_moves()

        # set last move
        self.last_move = move
        return False  # Промоция не нужна

    def check_promotion_needed(self, piece, final):
        return final.row == 0 or final.row == 7

    def casteling(self, initial, final):
        return abs(initial.col - final.col) == 2

    def promote_pawn(self, piece_type):
        if not self.promotion_pending:
            return
        
        position = self.promotion_pending['position']
        color = self.promotion_pending['color']
        
        # Создаем новую фигуру в зависимости от выбора
        if piece_type == 'queen':
            new_piece = Queen(color)
        elif piece_type == 'rook':
            new_piece = Rook(color)
        elif piece_type == 'bishop':
            new_piece = Bishop(color)
        elif piece_type == 'knight':
            new_piece = Knight(color)
        else:
            new_piece = Queen(color)  # По умолчанию королева
        
        # Помещаем новую фигуру на доску
        self.squares[position.row][position.col].piece = new_piece
        new_piece.moved = True
        
        # Очищаем состояние промоции
        self.promotion_pending = None

    def find_king(self, color):
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.squares[row][col].piece
                if isinstance(piece, King) and piece.color == color:
                    return (row, col)
        return None

    def is_in_check(self, color):
        king_pos = self.find_king(color)
        if not king_pos:
            return False
        
        king_row, king_col = king_pos
        
        # Проверяем все фигуры противника
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.squares[row][col].piece
                if piece and piece.color != color:
                    # Вычисляем возможные ходы без проверки шаха
                    self.calc_moves(piece, row, col, bool=False)
                    for move in piece.moves:
                        if move.final.row == king_row and move.final.col == king_col:
                            return True
        return False

    def get_all_possible_moves(self, color):
        moves = []
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.squares[row][col].piece
                if piece and piece.color == color:
                    self.calc_moves(piece, row, col, bool=True)
                    moves.extend(piece.moves)
        return moves

    def is_checkmate(self, color):
        if not self.is_in_check(color):
            return False
        
        moves = self.get_all_possible_moves(color)
        return len(moves) == 0

    def is_stalemate(self, color):
        if self.is_in_check(color):
            return False
        
        moves = self.get_all_possible_moves(color)
        return len(moves) == 0

    def check_game_over(self, current_player):
        if self.is_checkmate(current_player):
            # Мат - выигрывает противник
            winner = "black" if current_player == "white" else "white"
            self.game_over = winner
            return True
        elif self.is_stalemate(current_player):
            # Пат - ничья
            self.game_over = "stalemate"
            return True
        return False

    def valid_move(self, piece, move):
        return move in piece.moves
    
    def set_true_en_passant(self, piece):
        if not isinstance(piece, Pawn):
            return
        for row in range(ROWS):
            for col in range(COLS):
                if isinstance(self.squares[row][col].piece, Pawn):
                    self.squares[row][col].piece.en_passant = False
        piece.en_passant = True

    def set_false_en_passant(self):
        for row in range(ROWS):
            for col in range(COLS):
                if isinstance(self.squares[row][col].piece, Pawn):
                    pawn = self.squares[row][col].piece
                    if self.last_move:
                        if self.last_move.final.piece != pawn:
                            pawn.en_passant = False

    def in_check(self, piece, move):
        # ИСПРАВЛЕНИ: Проверка валидности координат
        if not Square.inrange(move.initial.row, move.initial.col):
            return False
        if not Square.inrange(move.final.row, move.final.col):
            return False
        
        # Специальная обработка для рокировки чтобы избежать рекурсии
        if isinstance(piece, King) and abs(move.final.col - move.initial.col) == 2:
            # Для рокировки проверяем только безопасность конечной позиции короля
            temp_board = copy.deepcopy(self)
            
            # Очищаем ссылки на ладьи чтобы избежать проблем с глубоким копированием
            for row in range(ROWS):
                for col in range(COLS):
                    if isinstance(temp_board.squares[row][col].piece, King):
                        temp_board.squares[row][col].piece.left_rook = None
                        temp_board.squares[row][col].piece.right_rook = None
            
            # Симулируем только перемещение короля на конечную позицию
            temp_board.squares[move.initial.row][move.initial.col].piece = None
            temp_board.squares[move.final.row][move.final.col].piece = piece
            
            # Проверяем может ли вражеская фигура атаковать новую позицию короля
            for row in range(ROWS):
                for col in range(COLS):
                    if temp_board.squares[row][col].has_enemy_piece(piece.color):
                        p = temp_board.squares[row][col].piece
                        temp_board.calc_moves(p, row, col, bool=False)
                        for m in p.moves:
                            if m.final.row == move.final.row and m.final.col == move.final.col:
                                return True
            return False
        
        # Стандартная проверка для обычных ходов
        temp_piece = copy.deepcopy(piece)
        temp_board = copy.deepcopy(self)
        
        # Очищаем ссылки на ладьи для предотвращения проблем с глубоким копированием
        if isinstance(temp_piece, King):
            temp_piece.left_rook = None
            temp_piece.right_rook = None
        
        temp_board.move(temp_piece, move)

        for row in range(ROWS):
            for col in range(COLS):
                if temp_board.squares[row][col].has_enemy_piece(piece.color):
                    p = temp_board.squares[row][col].piece
                    temp_board.calc_moves(p, row, col, bool=False)
                    for m in p.moves:
                        if isinstance(m.final.piece, King):
                            return True
        return False

    def calc_moves(self, piece, row, col, bool=True):
        '''
        Calculate all the possible/valid moves on a specific piece on a specific position
        '''
        piece.moves = []
        
        def pawn_moves():
            # steps
            steps = 1 if piece.moved else 2

            # vertical moves
            start = row + piece.dir
            end = row + (piece.dir * (1 + steps))
            for possible_move_row in range(start, end, piece.dir):
                if Square.inrange(possible_move_row):
                    if self.squares[possible_move_row][col].isempty():
                        # create initial and final move squares 
                        initial = Square(row, col)
                        final = Square(possible_move_row, col)
                        # create a move
                        move = Move(initial, final)

                        # check potential checks
                        if bool:
                            if not self.in_check(piece, move):
                                # append new move
                                piece.add_move(move)
                        else: 
                            piece.add_move(move)
                    # we are blocked 
                    else: break
                # not in range 
                else: break
            
            #diagonal moves 
            possible_move_row = row + piece.dir
            possible_move_cols = [col-1, col+1]
            for possible_move_col in possible_move_cols:
                if Square.inrange(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].has_enemy_piece(piece.color):
                        # create initial and final move squares 
                        initial = Square(row, col)
                        final_piece = self.squares[possible_move_row][possible_move_col].piece
                        final = Square(possible_move_row, possible_move_col, final_piece)
                        # create a move
                        move = Move(initial, final)
                        # append new move
                        if bool:
                            if not self.in_check(piece, move):
                                # append new move
                                piece.add_move(move)
                        else: 
                            piece.add_move(move)

            # en_passant moves 
            r = 3 if piece.color == 'white' else 4
            fr = 2 if piece.color == 'white' else 5
            # left en_passant 
            if Square.inrange(col-1) and row == r:
                if self.squares[row][col-1].has_enemy_piece(piece.color):
                    p = self.squares[row][col-1].piece
                    if isinstance(p, Pawn):
                        if p.en_passant:
                            # create initial and final move squares 
                            initial = Square(row, col)
                            final = Square(fr, col-1, p)
                            # create a move
                            move = Move(initial, final)
                            # append new move
                            if bool:
                                if not self.in_check(piece, move):
                                    # append new move
                                    piece.add_move(move)
                            else: 
                                piece.add_move(move)

            # right en_passant
            if Square.inrange(col+1) and row == r:
                if self.squares[row][col+1].has_enemy_piece(piece.color):
                    p = self.squares[row][col+1].piece
                    if isinstance(p, Pawn):
                        if p.en_passant:
                            # create initial and final move squares 
                            initial = Square(row, col)
                            final = Square(fr, col+1, p)
                            # create a move
                            move = Move(initial, final)
                            # append new move
                            if bool:
                                if not self.in_check(piece, move):
                                    # append new move
                                    piece.add_move(move)
                            else: 
                                piece.add_move(move)

        def knight_moves():
            # 8 possible moves
            possible_moves = [
                (row-2, col+1),
                (row-1, col+2),
                (row+1, col+2),
                (row+2, col+1),
                (row+2, col-1),
                (row+1, col-2),
                (row-1, col-2),
                (row-2, col-1),
            ]
            for possible_move in possible_moves:
                possible_move_row, possible_move_col = possible_move

                if Square.inrange(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].isempty_or_enemy(piece.color):
                        # create squares of the new move 
                        initial = Square(row, col)
                        final_piece = self.squares[possible_move_row][possible_move_col].piece
                        final = Square(possible_move_row, possible_move_col, final_piece)
                        # create move 
                        move = Move(initial, final)
                        if bool:
                            if not self.in_check(piece, move):
                                # append new move
                                piece.add_move(move)
                        else: 
                            piece.add_move(move)

        def straightline_move(incrs):
            for incr in incrs:
                row_incr, col_incr = incr
                possible_move_row = row + row_incr
                possible_move_col = col + col_incr

                while True:
                    if Square.inrange(possible_move_row, possible_move_col):
                        # create squares of the possible new move
                        initial = Square(row, col)
                        final_piece = self.squares[possible_move_row][possible_move_col].piece
                        final = Square(possible_move_row, possible_move_col, final_piece)
                        # create a possible new move
                        move = Move(initial, final)
 
                        # empty = continue looping
                        if self.squares[possible_move_row][possible_move_col].isempty():
                            # append new move
                            if bool:
                                if not self.in_check(piece, move):
                                    # append new move
                                    piece.add_move(move)
                            else: 
                                piece.add_move(move)

                        # has enemy piece = add move + break
                        elif self.squares[possible_move_row][possible_move_col].has_enemy_piece(piece.color):
                            # append new move
                            if bool:
                                if not self.in_check(piece, move):
                                    # append new move
                                    piece.add_move(move)
                            else: 
                                piece.add_move(move)
                            break

                        # has team piece = break
                        elif self.squares[possible_move_row][possible_move_col].has_team_piece(piece.color):
                            break

                    # not in range 
                    else: break

                    # increments
                    possible_move_row = possible_move_row + row_incr
                    possible_move_col = possible_move_col + col_incr

        def king_moves():
            adjs = [
                (row-1,col+0), 
                (row-1,col+1),
                (row+0,col+1),
                (row+1,col+1),
                (row+1,col+0),
                (row+1,col-1),
                (row+0,col-1),
                (row-1,col-1)
            ]

            # normal moves
            for possible_move in adjs:
                possible_move_row, possible_move_col = possible_move

                if Square.inrange(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].isempty_or_enemy(piece.color):
                        # create initial and final move squares 
                        initial = Square(row, col)
                        final = Square(possible_move_row, possible_move_col)
                        # create a move
                        move = Move(initial, final)
                        # append new move
                        if bool:
                            if not self.in_check(piece, move):
                                # append new move
                                piece.add_move(move)
                        else: 
                            piece.add_move(move)

            # ИСПРАВЛЕННАЯ РОКИРОВКА
            if not piece.moved:
                # Королевский фланг (короткая рокировка)
                if Square.inrange(row, 0):  # Проверяем валидность позиции
                    left_rook = self.squares[row][0].piece
                    if isinstance(left_rook, Rook) and not left_rook.moved:
                        can_castle = True
                        # Проверяем что клетки между королём и ладьёй пусты
                        for c in range(1, 4):
                            if self.squares[row][c].has_piece():
                                can_castle = False
                                break
                        
                        if can_castle:
                            # Добавляем ссылку на ладью к королю
                            piece.left_rook = left_rook
                            
                            # Ход ладьи
                            initial_rook = Square(row, 0)
                            final_rook = Square(row, 3)
                            moveR = Move(initial_rook, final_rook)
                            
                            # Ход короля
                            initial_king = Square(row, col)
                            final_king = Square(row, 2)
                            moveK = Move(initial_king, final_king)
                            
                            # Проверяем безопасность ходов
                            if bool:
                                try:
                                    king_safe = not self.in_check(piece, moveK)
                                    # Также проверяем промежуточную клетку
                                    intermediate = Square(row, 3)
                                    move_intermediate = Move(initial_king, intermediate)
                                    intermediate_safe = not self.in_check(piece, move_intermediate)
                                    
                                    if king_safe and intermediate_safe:
                                        left_rook.add_move(moveR)
                                        piece.add_move(moveK)
                                except:
                                    pass  # Пропускаем если проверка не удалась
                            else:
                                left_rook.add_move(moveR)
                                piece.add_move(moveK)

                # Ферзевый фланг (длинная рокировка)
                if Square.inrange(row, 7):  # Проверяем валидность позиции
                    right_rook = self.squares[row][7].piece
                    if isinstance(right_rook, Rook) and not right_rook.moved:
                        can_castle = True
                        # Проверяем что клетки между королём и ладьёй пусты
                        for c in range(5, 7):
                            if self.squares[row][c].has_piece():
                                can_castle = False
                                break
                        
                        if can_castle:
                            # Добавляем ссылку на ладью к королю
                            piece.right_rook = right_rook
                            
                            # Ход ладьи
                            initial_rook = Square(row, 7)
                            final_rook = Square(row, 5)
                            moveR = Move(initial_rook, final_rook)
                            
                            # Ход короля
                            initial_king = Square(row, col)
                            final_king = Square(row, 6)
                            moveK = Move(initial_king, final_king)
                            
                            # Проверяем безопасность ходов
                            if bool:
                                try:
                                    king_safe = not self.in_check(piece, moveK)
                                    # Также проверяем промежуточную клетку
                                    intermediate = Square(row, 5)
                                    move_intermediate = Move(initial_king, intermediate)
                                    intermediate_safe = not self.in_check(piece, move_intermediate)
                                    
                                    if king_safe and intermediate_safe:
                                        right_rook.add_move(moveR)
                                        piece.add_move(moveK)
                                except:
                                    pass  # Пропускаем если проверка не удалась
                            else:
                                right_rook.add_move(moveR)
                                piece.add_move(moveK)

        # Выполняем расчёт ходов в зависимости от типа фигуры
        if isinstance(piece, Pawn): 
            pawn_moves()
        elif isinstance(piece, Knight): 
            knight_moves()
        elif isinstance(piece, Bishop): 
            straightline_move([(-1, 1),(-1, -1),(1, 1),(1,-1)])
        elif isinstance(piece, Rook): 
            straightline_move([(-1, 0),(0, 1),(1, 0),(0, -1)])
        elif isinstance(piece, King): 
            king_moves()
        elif isinstance(piece, Queen): 
            straightline_move([
                (-1, 1),
                (-1, -1),
                (1, 1),
                (1,-1),
                (-1, 0),
                (0, 1),
                (1, 0),
                (0, -1)
            ])
    
    def _create(self):
        for row in range(ROWS):
            for col in range(COLS):
                self.squares[row][col] = Square(row, col)

    def _add_pieces(self, color):
        row_pawn, row_other = (6, 7) if color == "white" else (1, 0)

        for col in range(COLS): # all pawns
            self.squares[row_pawn][col] = Square(row_pawn, col, Pawn(color))
        
        # Knights
        self.squares[row_other][1] = Square(row_other, 1, Knight(color))
        self.squares[row_other][6] = Square(row_other, 6, Knight(color))

        # bishops
        self.squares[row_other][2] = Square(row_other, 2, Bishop(color))
        self.squares[row_other][5] = Square(row_other, 5, Bishop(color))

        #rooks
        self.squares[row_other][0] = Square(row_other, 0, Rook(color))
        self.squares[row_other][7] = Square(row_other, 7, Rook(color))

        #kings
        self.squares[row_other][4] = Square(row_other, 4, King(color))

        #queens
        self.squares[row_other][3] = Square(row_other, 3, Queen(color))