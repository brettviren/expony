import pygame
import sys
import expony.funcs 
from expony.gui import Frame
from expony.arr import Board as ArrayBoard

CLOCK_TICK=60

pygame.init()
screen = None


class Board:
    def __init__(self, frame, shape=(8,8), random_seed=None):
        self.frame = frame

        # Note: a tile position ("pos") is in (row,col) order while a pixel
        # location ("pix") is in (x,y) order.
        self.tile_shape_pix = (int(frame.width/shape[1]),
                               int(frame.height/shape[0]))

        self.shape = shape
        self.random_seed = random_seed
        self.delay_ms = 0

        self.reset()

    def reset(self):

        self.game_over = False
        self.eboard = ArrayBoard(self.shape, random_seed=self.random_seed)
        self.eboard.assure_stable()
        self.total_points = 0
        self.nturns = 0
        # holds a selected position
        self.seed_pos = None


    def faster(self):
        self.delay_ms = int(self.delay_ms*0.9)
        print(f'delay {self.delay_ms} ms')
    def slower(self):
        if self.delay_ms == 0:
            self.delay_ms = 10;
        self.delay_ms = int(self.delay_ms*1.1)
        print(f'delay {self.delay_ms} ms')        


    def pix2pos(self, pix):
        '''
        Convert absolute pix=(x_pixel,y_pixel) to pos=(row_index, col_index).
        '''
        pix = self.frame.global_to_local(pix)
        return (pix[1] // self.tile_shape_pix[1],
                pix[0] // self.tile_shape_pix[0])

    def pos2pix(self, pos):
        '''
        Convert pos=(row_index, col_index) to absolute pix=(x_pixel,y_pixel).
        '''
        pix = (pos[1]*self.tile_shape_pix[0],
               pos[0]*self.tile_shape_pix[1])
        return self.frame.local_to_global(pix)

    def draw_board(self):
        screen.fill((0, 0, 0))
        for pos in self.eboard.all_positions:
            self.draw_tile(pos)
        pygame.display.flip()

    def draw_end(self):
        font = pygame.font.Font(None, 2*36)
        msg = f'{self.total_points} points / {self.nturns} moves'
        print(f'{msg}, seed: {self.eboard.random_seed}')
        text = font.render(msg, True, (0,255,0))
        text_rect = text.get_rect(center=self.frame.center)
        screen.blit(text, text_rect)
        pygame.display.flip()


    def draw_tile(self, pos):
        pix = self.pos2pix(pos)
        value = self.eboard[pos]

        tile_colors = [
            '#000000', # black               0 
            '#0A9396', # Dark cyan           1/2
            '#E9D8A6', # Beige               2/4
            '#EE9B00', # Yellowish orange    3/8
            '#CA6702', # Browny orange       4/16
            '#005F73', # Petrol              5/32
            '#AE2012', # Deep red            6/64  
            '#86350F', # Reddish brown       7/128 
            '#94D2BD', # Pale teal           8/256 
            '#FF8080', # Salmon pink         9/512 
            '#FFCC80', # Wheat              10/1024
            '#E6FF80', # Light yellow green 11/2048
            '#99FF80', # Light green        12/4096
            '#80FFB3', #                    13/8096
        ]
        color = tile_colors[value]
        font_color = (255, 255, 255)
        if value in (2, 8, 9, 10, 11, 12, 13):
            font_color = (0, 0, 0) # black
        
        border_color = (255, 255, 255)  # default tile color
        if self.seed_pos == pos:
            border_color = (0, 0, 0)
        if self.game_over:
            border_color = (255, 0, 0)

        rect = (pix[0], pix[1], self.tile_shape_pix[0], self.tile_shape_pix[1])
        center = (rect[0] + rect[2]//2, rect[1] + rect[3]//2)

        points = 2**value 

        pygame.draw.rect(screen, color, rect)
        if value:
            font = pygame.font.Font(None, 36) # fixme, make dependent on tile_size
            text = font.render(str(points), True, font_color)
            text_rect = text.get_rect(center=center)
            screen.blit(text, text_rect)
        pygame.draw.rect(screen, border_color, rect, 10)


    def do_move(self, seed, targ):
        points = self.eboard.maybe_swap(seed, targ)
        if points == 0:
            return 0
        self.nturns += 1
        self.total_points += points
        self.draw_board()

    def handle_event(self, event):
        # print(f"handle event: {event}")
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:

            pix = event.pos
            pos = self.pix2pos(pix)
            print(f'{pix=} {pos=} {event.type}')

            if self.seed_pos is None:
                print(f'down: set seed tile at {pos}')
                self.seed_pos = pos
                self.draw_board()
                return

            if self.seed_pos == pos:
                print(f'down: unseed tile at {pos}')
                self.seed_pos = None
                self.draw_board()
                return

            return

        if event.type == pygame.MOUSEBUTTONUP:
            
            pix = event.pos
            pos = self.pix2pos(pix)
            print(f'{pix=} {pos=} {event.type}')

            if self.seed_pos is None:
                print(f'up: no seed at {pos}')
                return

            if self.seed_pos == pos:
                print(f'up: on seed at {pos}')
                return

            seed_pos = self.seed_pos
            self.seed_pos = None
            print(f'up: at other pos: {seed_pos} -> {pos}')
            bps = expony.funcs.maybe_swap(self.eboard, seed_pos, pos)
            if not bps:
                print(f'up: illegal move {seed_pos} -> {pos}')
                return
            self.nturns += 1

            self.draw_board()
            for bp in bps:
                print(f'points: {self.total_points} + {bp.points}')
                self.total_points += bp.points
                self.eboard = bp.board

                if self.delay_ms:
                    pygame.time.delay(self.delay_ms)

                self.draw_board()

            self.seed_pos = None
            print('New board state after move')

            self.draw_board()
            return

from pygame.locals import K_q, K_r, K_f, K_s

class AutoGui:
    def __init__(self, board):
        self.board = board
    def run(self):
        self.clock = pygame.time.Clock()
        while True:
            move = self.board.eboard.automove_hint()
            if not move:
                self.board.game_over = True
                self.board.draw_board()
                self.board.draw_end()
                break
            self.board.do_move(*move)
            pygame.event.pump()

        while True:
            event = pygame.event.wait()

            if event.type in [
                    pygame.KEYUP,
            ]:
                if event.key == K_q:
                    return

                if event.key == K_r:
                    self.board.reset()
                    self.board.draw_board()
                    return self.run()


if '__main__' == __name__:
    tsize = 8
    bsize = 800

    shape = (tsize, tsize)
    screen_size = (bsize, bsize)

    screen = pygame.display.set_mode(screen_size)

    board = Board(Frame(pygame.Rect(0,0,*screen_size)), shape)
    gui = AutoGui(board)
    gui.run()
