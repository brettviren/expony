import pygame
import sys

import expony.data 
import expony.funcs 

CLOCK_TICK=60

pygame.init()
screen = pygame.display.set_mode((0,0))


class Frame:
    def __init__(self, rect):
        self.rect = rect
    @property
    def width(self):
        return self.rect.width
    @property
    def height(self):
        return self.rect.height

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
    


class Board:
    def __init__(self, frame, shape=(8,8), random_seed=None):

        self.frame = frame

        # Note: a tile position ("pos") is in (row,col) order while a pixel
        # location ("pix") is in (x,y) order.
        self.tile_shape_pix = (int(frame.width/shape[1]),
                               int(frame.height/shape[0]))

        self.eboard = expony.data.Board(shape, random_seed=random_seed)
        self.eboard.assure_stable()
        self.total_points = 0

        # holds a selected position
        self.seed_pos = None

        self.delay_ms = 0

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

    def draw(self):
        screen.fill((0, 0, 0))
        for pos in self.eboard.all_positions:
            self.draw_tile(pos)
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
            font_color = (0, 0, 0)
        
        border_color = (255, 255, 255)  # default tile color
        if self.seed_pos == pos:
            border_color = (0, 0, 0)


        rect = (pix[0], pix[1], self.tile_shape_pix[0], self.tile_shape_pix[1])
        center = (rect[0] + rect[2]//2, rect[1] + rect[3]//2)

        pygame.draw.rect(screen, color, rect)
        if tile.value:
            font = pygame.font.Font(None, 36) # fixme, make dependent on tile_size
            text = font.render(str(tile.points), True, font_color)
            text_rect = text.get_rect(center=center)
            screen.blit(text, text_rect)
        pygame.draw.rect(screen, border_color, rect, 10)


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
                self.draw()
                return

            if self.seed_pos == pos:
                print(f'down: unseed tile at {pos}')
                self.seed_pos = None
                self.draw()
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

            self.draw()
            for bp in bps:
                print(f'points: {self.total_points} + {bp.points}')
                self.total_points += bp.points
                self.eboard = bp.board

                if self.delay_ms:
                    pygame.time.delay(self.delay_ms)

                self.draw()

            self.seed_pos = None

            return

class Gui:
    def __init__(self, widgets):
        self.widgets = widgets

    def run(self):
        self.clock = pygame.time.Clock()
        while True:
            event = pygame.event.wait()
            if event.type == pygame.MOUSEMOTION:
                continue
            if event.type == pygame.QUIT:
                return
            print(f'{event}')
            if event.type in [pygame.WINDOWSHOWN,
                              pygame.WINDOWRESIZED,
                              pygame.WINDOWEXPOSED,
                              ]:
                for wid in self.widgets:
                    wid.draw()
                continue

            if event.type in [pygame.MOUSEBUTTONUP,
                              pygame.MOUSEBUTTONDOWN]:
                for wid in self.widgets:
                    if wid.frame.rect.collidepoint(*event.pos):
                        wid.handle_event(event)
                        break




if __name__ == "__main__":
    screen_size = (600,600)
    print(screen)
    screen = pygame.display.set_mode(screen_size)
    board = Board(Frame(pygame.Rect(0,0,*screen_size)), (6,6))
    gui = Gui([board])
    gui.run()

