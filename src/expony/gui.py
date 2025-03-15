import pygame
import sys

import expony.data 
import expony.funcs 

CLOCK_TICK=60

pygame.init()
screen = None


class Frame:
    def __init__(self, rect):
        self.rect = rect
    @property
    def width(self):
        return self.rect.width
    @property
    def height(self):
        return self.rect.height

    @property
    def center(self):
        return (self.rect.x + self.rect.width//2,
                self.rect.y + self.rect.height//2)

    def local_to_global(self, pix):
        if isinstance(pix, pygame.Rect):
            pix = (pix.x, pix.y)
        if isinstance(pix, tuple):
            return (self.rect.x + pix[0],
                    self.rect.y + pix[1])
        raise TypeError(f'unknown location type: {type(pix)}')

    def global_to_local(self, pix):
        if isinstance(pix, pygame.Rect):
            pix = (pix.x, pix.y)
        if isinstance(pix, tuple):
            return (pix[0] - self.rect.x,
                    pix[1] - self.rect.y)
        raise TypeError(f'unknown location type: {type(pix)}')
    

import random

class Board:
    def __init__(self, frame, shape=(8,8), random_seed=None):
        self.frame = frame

        # Note: a tile position ("pos") is in (row,col) order while a pixel
        # location ("pix") is in (x,y) order.
        self.tile_shape_pix = (int(frame.width/shape[1]),
                               int(frame.height/shape[0]))

        self.shape = shape
        self.random_seed = random_seed
        self.reset()

    def reset(self):
        print("RESET")

        # debug, when something goes weird, we want to reproduce it. 
        if self.random_seed is None:
            random_seed = random.randint(0, 2**8)

        self.eboard = expony.data.Board(self.shape, random_seed=random_seed)
        self.eboard.assure_stable()
        self.total_points = 0
        self.nturns = 0
        # holds a selected position
        self.seed_pos = None

        self.delay_ms = 100

        self.find_possible_moves()
        print(f'Board constructed with seed {random_seed}')


        

    def find_possible_moves(self):
        self.possible_moves = list(expony.funcs.possible_moves(self.eboard))
        print(f'{len(self.possible_moves)} moves possible')
        for m in self.possible_moves:
            print(m)
        return len(self.possible_moves)

    @property
    def game_over(self):
        return len(self.possible_moves) == 0

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
        text = font.render(msg, True, (0,255,0))
        text_rect = text.get_rect(center=self.frame.center)
        screen.blit(text, text_rect)
        pygame.display.flip()


    def draw_tile(self, pos):
        pix = self.pos2pix(pos)
        tile = self.eboard[pos]

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
        color = tile_colors[tile.value]
        font_color = (255, 255, 255)
        if tile.value in (2, 8, 9, 10, 11, 12, 13):
            font_color = (0, 0, 0) # black
        
        border_color = (255, 255, 255)  # default tile color
        if self.seed_pos == pos:
            border_color = (0, 0, 0)
        if self.game_over:
            border_color = (255, 0, 0)

        rect = (pix[0], pix[1], self.tile_shape_pix[0], self.tile_shape_pix[1])
        center = (rect[0] + rect[2]//2, rect[1] + rect[3]//2)

        pygame.draw.rect(screen, color, rect)
        if tile.value:
            font = pygame.font.Font(None, 36) # fixme, make dependent on tile_size
            text = font.render(str(tile.points), True, font_color)
            text_rect = text.get_rect(center=center)
            screen.blit(text, text_rect)
        pygame.draw.rect(screen, border_color, rect, 10)

    def draw(self):
        self.draw_board()
        self.maybe_draw_end()


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
            self.find_possible_moves()

            self.draw_board()
            self.maybe_draw_end()
            return

    def maybe_draw_end(self):
        if self.game_over:
            self.draw_board()
            self.draw_end()


from pygame.locals import K_q, K_r
class Gui:
    def __init__(self, widgets):
        self.widgets = widgets

    def run(self):
        self.clock = pygame.time.Clock()
        while True:
            event = pygame.event.wait()
            if pygame.key.get_pressed()[K_r]:
                for wid in self.widgets:
                    if hasattr(wid, "reset"):
                        wid.reset()
                        wid.draw()
                continue

            if pygame.key.get_pressed()[K_q]:
                return
            if event.type == pygame.MOUSEMOTION:
                continue
            if event.type == pygame.QUIT:
                return
            if event.type in [
                    pygame.WINDOWSHOWN,
                    pygame.WINDOWRESIZED,
                    pygame.WINDOWEXPOSED,
                              ]:
                print(f'{event}')
                for wid in self.widgets:
                    wid.draw()
                continue

            if event.type in [pygame.MOUSEBUTTONUP,
                              pygame.MOUSEBUTTONDOWN]:
                print(f'{event}')
                for wid in self.widgets:
                    if wid.frame.rect.collidepoint(*event.pos):
                        wid.handle_event(event)
                        break




if __name__ == "__main__":
    screen_size = (600,600)
    print(screen)
    screen = pygame.display.set_mode(screen_size)
    board = Board(Frame(pygame.Rect(0,0,*screen_size)), (3,3))
    gui = Gui([board])
    gui.run()

