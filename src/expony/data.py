#!/usr/bin/env python
'''
The expony game data.
'''

from typing import List, Tuple, Callable
import copy
from collections import defaultdict
import random
from itertools import product
from dataclasses import dataclass

# (row,col) order.  (0,0) is upper left corner.
Position = tuple

def adjacent(a: Position, b: Position) -> bool:
    '''
    Return True if a and be are adjacent.
    '''
    return ((a[0] == b[0] and abs(a[1] - b[1]) == 1) 
            or
            (a[1] == b[1] and abs(a[0] - b[0]) == 1))


tile_count = 0
class Tile:
    '''
    A Tile holds a value at a board position.

    Legal values are 1 or larger.

    The "points" for a value are two to the power of the value.
    '''
    value: int
    # ident: int
    # merged: None|Position = None

    def __init__(self, value: int = 0):
        self.value = value
        global tile_count
        tile_count += 1         # any ident == 0 is an error
        self.ident = tile_count

    def __repr__(self):
        return f'{self.ident:04d}:{self.value:01d}'

    @property
    def points(self):
        return 2**self.value 

TileArray = List[List[Tile]]

def same_tiles(shape: Tuple[int], value: int) -> TileArray:
    return [[Tile(value)
             for col in range(shape[1])]
            for row in range(shape[0])]
def range_tiles(shape: Tuple[int]) -> TileArray:
    return [[Tile(row*shape[1] + col)
             for col in range(shape[1])]
            for row in range(shape[0])]

def sum_tiles(shape: Tuple[int]) -> TileArray:
    return [[Tile(row+col)
             for col in range(shape[1])]
            for row in range(shape[0])]


class Matched:
    '''
    Record a set of positions of matching tiles and their new value.
    '''
    value: int
    origin: Position
    matched: List[Position]

    def __init__(self, value:int, origin:Position, matched:List[Position]):
        self.value = value
        self.origin = origin
        self.matched = matched

    def __repr__(self):
        return f'<Matched {self.origin}={self.value} -> {self.matched}>'

    @property
    def all_positions(self):
        return [self.origin] + self.matched
    

class Board:
    '''
    An expony game board is NxM grid of tiles.
    '''

    tiles: TileArray

    # Must have at least this many values in a row or col to form a match.
    min_match = 3

    # The maximum value for newly generated tile values.
    max_init_value = 4

    # The default shape of the board.
    default_shape = (8,8)

    def __init__(self,
                 source: int|TileArray|'Board'|None = None,
                 random_seed = None):
        '''
        Construct a board.

        The source may be one of several types:
        - int :: gives the size of a square board
        - Tuple[int] :: gives the shape of a rectangular board
        - TileArray :: the board contents
        - Board :: another board and a deepcopy of its tiles is done
        - NoneType :: defaults are used.

        When the board is constructed with shape only, it is initialized
        randomly using the provied random_seed until "stable".

        When the board is constructed with another board or a TileArray, this
        boards tiles are set without constraint, the provided random_seed is
        ignored the boards random is seeded from a digest of the tiles.
        '''

        if source is None:
            source = self.default_shape
        if isinstance(source, int): # square
            source = (source, source)
        if isinstance(source, tuple): # default or custom shape
            if source[0] < self.min_match or source[1] < self.min_match:
                raise ValueError(f'Board shape is too small: {source}')

            self.rng = random.Random(random_seed)
            self.tiles = [[Tile(self.random_value())
                           for col in range(source[1])]
                          for row in range(source[0])]
            self.assure_stable()
            return

        if isinstance(source, Board): # copy
            self.tiles = copy.deepcopy(source.tiles)
            self.rng = random.Random(self.digest())
            return

        if isinstance(source, list): # premade
            self.tiles = copy.deepcopy(source)
            self.rng = random.Random(self.digest())
            return
        raise TypeError(f'Board can not be constructed from: {type(source)}')


    def __repr__(self):
        lines = []
        for row in self.tiles:
            lines.append(' '.join([f'{col.value:1d}' for col in row]))
        return '\n'.join(lines)

    def __getitem__(self, ind: int):
        if isinstance(ind, tuple):
            return self.tiles[ind[0]][ind[1]]
        raise TypeError(f'invalid index type: {type(ind)}')

    def __setitem__(self, ind: int, value: Tile):
        if not isinstance(value, Tile):
            raise TypeError(f'Board holds Tile not {type(value)}')
        if isinstance(ind, tuple):
            self.tiles[ind[0]][ind[1]] = value
            return value
        raise TypeError(f'invalid index type: {type(ind)}')

    @property
    def shape(self):
        return (len(self.tiles), len(self.tiles[0]))

    def cardinal_ranges(self, pos: Position):
        '''
        Return dict of ranges of positions along each cardinal direction.

        The dict gives a range positions starting from pos and going in one of
        each cardinal direction.  The directions are the dictionary keys are
        "up", "down", "left", "right".
        '''
        row,col = pos
        nrows,ncols = self.shape
        return dict(
            up =  ((r,col) for r in range(row-1,-1,-1)),
            down= ((r,col) for r in range(row+1,nrows)),
            left= ((row,c) for c in range(col-1,-1,-1)),
            right=((row,c) for c in range(col+1,ncols))
        )
            
    def matched(self, seed: Position) -> Matched:
        '''
        Return a matched for pos or None 

        getMatchedTile
        '''
        target = self[seed].value

        m = defaultdict(list)
        for card, prange in self.cardinal_ranges(seed).items():
            for pos in prange:
                if self[pos].value != target:
                    break;
                m[card].append(pos)
                
        s = set()
        nvert = 1 + len(m["up"]) + len(m["down"])
        if nvert >= self.min_match:
            s.update(m["up"])
            s.update(m["down"])
        nhoriz = 1 + len(m["left"]) + len(m["right"])
        if nhoriz >= self.min_match:
            s.update(m["left"])
            s.update(m["right"])
        if not s:
            return
        points = target + len(s) - 1
        return Matched(points, seed, list(s))

    @property
    def all_positions(self) -> List[Position]:
        return product(range(self.shape[0]), range(self.shape[1]))

    @property
    def all_tiles(self):
        for row in self.tiles:
            for tile in row:
                yield tile

    def digest(self):
        '''
        Return a binary digest of the state
        '''
        dat = ' '.join([str(t.value) for t in self.all_tiles])
        return dat.encode()


    def all_matches(self) -> List[Matched]:
        '''
        Return all matches in the current board.

        getMatchesOnBoard
        '''
        ret = list()
        for seed in self.all_positions:
            m = self.matched(seed)
            if m is None:
                continue
            ret.append(m)
        return ret

    def at_least_one(self) -> bool:
        '''
        Return true if there is at least one move possible.
        '''
        for seed in self.all_positions:
            m = self.matched(seed)
            if m: return True
        return False
        

    def assure_stable(self):
        '''
        Randomize until there are no matches.
        '''
        mvmo = self.max_init_value - 1

        while True:
            ms = self.all_matches()
            if not ms:
                return
            # pick a new for each match seed which is not the current value.
            for m in ms:
                val = self[m.origin].value
                val += self.rng.randint(0, mvmo-1) - 1
                self[m.origin].value = (val % mvmo) + 1

    def random_value(self):
        '''
        Return a random integer value in the allowed init range.
        '''
        return self.rng.randint(1, self.max_init_value)

    def set_random(self, pos):
        '''
        Set a random value at pos that is within bounds
        '''
        self[pos].value = self.random_value()


@dataclass
class BoardPoints:
    '''
    A new board and the points accrued in producing it form some prior
    board.
    '''

    board: Board
    points: int


@dataclass
class Move:
    '''
    The new board and points accrued if seed and targ were to swap from some
    prior board.
    '''

    seed: Position
    targ: Position
    points: int
    board: Board
    


class GameState:
    board: Board
    points: int
    moves: int
    
