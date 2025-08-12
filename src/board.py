from const import *
from square import Square
from piece import *
from move import Move

class Board:
    def __init__(self):
        self.squares = [[0, 0, 0, 0, 0, 0, 0, 0,] for col in range(COLS)]
        self.last_move = None
        self.promotion_pending = None  # info о промоции
        self._create()
        self._add_pieces("white")
        self._add_pieces('black')

    def move(self, piece, move):
        initial = move.initial
        final = move.final

        # console board move update
        self.squares[initial.row][initial.col].piece = None
        self.squares[final.row][final.col].piece = piece

        # pawn promotion
        if isinstance(piece, Pawn):
            if self.check_promotion_needed(piece, final):
                self.promotion_pending = {
                    'piece': piece,
                    'position': final,
                    'color': piece.color
                }
                return True  # Возвращаем True, чтобы указать, что нужна промоция

        # king castiling
        if isinstance(piece, King):
            if self.casteling(initial, final):
                diff = final.col - initial.col
                rook = piece.left_rook if (diff < 0) else piece.right_rook
                self.move(rook, rook.moves[-1])


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
        """Выполняет промоцию пешки в выбранную фигуру"""
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

    def valid_move(self, piece, move):
        return move in piece.moves

    def calc_moves(self, piece, row, col):
        '''
        Calculate all the possible/vlaid moves on a specific piece on a specific position
        '''
        piece.moves = [] # ЧЕРТ ПРОСТО ЧЕРТ
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
                        # append new move
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
                        final = Square(possible_move_row, possible_move_col)
                        # create a move
                        move = Move(initial, final)
                        # append new move
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
                        final = Square(possible_move_row, possible_move_col) # piece=piece  
                        # create move 
                        move = Move(initial, final)
                        piece.add_move(move)
                        # append new valid move 

        def straightline_move(incrs):
            for incr in incrs:
                row_incr, col_incr = incr
                possible_move_row = row + row_incr
                possible_move_col = col + col_incr

                while True:
                    if Square.inrange(possible_move_row, possible_move_col):
                        # create squares of the possible new move
                        initial = Square(row, col)
                        final = Square(possible_move_row, possible_move_col)
                        # create a possible new move
                        move = Move(initial, final)
 
                        # empty = continue looping
                        if self.squares[possible_move_row][possible_move_col].isempty():
                            # append new move
                            piece.add_move(move)

                        # has enemy piece = add move + break
                        if self.squares[possible_move_row][possible_move_col].has_enemy_piece(piece.color):
                            # append new move
                            piece.add_move(move)
                            break

                        # has team piece = break
                        if self.squares[possible_move_row][possible_move_col].has_team_piece(piece.color):
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
                        piece.add_move(move)

            # castling moves
            if not piece.moved:
                # queen castling
                left_rook = self.squares[row][0].piece
                if isinstance(left_rook, Rook):
                    if not left_rook.moved:
                        for c in range(1, 4):
                            # casteling is not possible because pieces in between
                            if self.squares[row][c].has_piece(): 
                                break
                            
                            if c == 3:
                                # adds left rook to king 
                                piece.left_rook = left_rook

                                # rook move
                                initial = Square(row, 0)
                                final = Square(row, 3)
                                move = Move(initial, final)
                                left_rook.add_move(move)
                                # king move
                                initial = Square(row, col)
                                final = Square(row, 2)
                                move = Move(initial, final)
                                piece.add_move(move)

                # king castling
                right_rook = self.squares[row][7].piece
                if isinstance(right_rook, Rook):
                    if not right_rook.moved:
                        for c in range(5, 7):
                            # casteling is not possible because pieces in between
                            if self.squares[row][c].has_piece(): 
                                break
                            
                            if c == 6:
                                # adds right rook to king 
                                piece.right_rook = right_rook

                                # rook move
                                initial = Square(row, 7)
                                final = Square(row, 5)
                                move = Move(initial, final)
                                right_rook.add_move(move)
                                # king move
                                initial = Square(row, col)
                                final = Square(row, 6)
                                move = Move(initial, final)
                                piece.add_move(move)



        if isinstance(piece, Pawn): pawn_moves()
        elif isinstance(piece, Knight): knight_moves()
        elif isinstance(piece, Bishop): straightline_move([(-1, 1),(-1, -1),(1, 1),(1,-1)])
        elif isinstance(piece, Rook): straightline_move([(-1, 0),(0, 1),(1, 0),(0, -1)])
        elif isinstance(piece, King): king_moves()
        elif isinstance(piece, Queen): straightline_move([
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