import pygame
import sys

import expony.data 
import expony.funcs 

# Initialize Pygame
pygame.init()

class Game:
    def __init__(self, shape=(8,8), tile_size=100, random_seed = None):
        self.shape = shape
        self.height, self.width  = [s*tile_size for s in shape]
        self.tile_size = tile_size
        # Set up the display
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.eboard = expony.data.Board(shape, random_seed=random_seed)
        self.eboard.assure_stable()
        self.total_points = 0

        # holds a selected position
        self.seed_pos = None

        self.delay_ms = 500

    def pix2pos(self, pix):
        '''
        Convert pix=(x_pixel,y_pixel) to pos=(row_index, col_index).
        '''
        return (pix[1] // self.tile_size, pix[0] // self.tile_size)

    def pos2pix(self, pos):
        '''
        Convert pos=(row_index, col_index) to pix=(x_pixel,y_pixel).
        '''
        return (pos[1]*self.tile_size, pos[0]*self.tile_size)

    def draw(self):
        self.screen.fill((0, 0, 0))
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


        rect = (pix[0], pix[1], self.tile_size, self.tile_size)
        center = (rect[0] + rect[2]//2, rect[1] + rect[3]//2)

        pygame.draw.rect(self.screen, color, rect)
        if tile.value:
            font = pygame.font.Font(None, 36) # fixme, make dependent on tile_size
            text = font.render(str(tile.points), True, font_color)
            text_rect = text.get_rect(center=center)
            self.screen.blit(text, text_rect)
        pygame.draw.rect(self.screen, border_color, rect, 10)


    def handle_event(self, event):
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
                return

            if self.seed_pos == pos:
                print(f'down: unseed tile at {pos}')
                self.seed_pos = None
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
            for bp in bps:
                print(f'points: {self.total_points} + {bp.points}')
                self.total_points += bp.points
                self.eboard = bp.board
                self.draw()

                pygame.time.delay(self.delay_ms)

                self.clock.tick(60)
            self.seed_pos = None

            # if expony.data.adjacent(pos, self.seed_pos):
            #     print(f'adjacent: {pos} and {self.seed_pos}')
            #     self.eboard = expony.funcs.swap_tiles(self.eboard, self.seed_pos, pos)
            #     self.seed_pos = None
            #     return
            # print(f'up: not adjacent')
            return

    def run(self):
        self.clock = pygame.time.Clock()
        while True:
            event = pygame.event.wait()
            self.handle_event(event)
            self.draw()
            self.clock.tick(60)

if __name__ == "__main__":
    game = Game()
    game.run()
