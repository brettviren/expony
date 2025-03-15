#!/usr/bin/env python
'''
An implementation of expony board on numpy.

This implementation differs from the list-based:

- No explicit tile object, a board holds tiles as a 2D integer array.
- No copy-on-modify pattern, board state is mutated in-place.

'''
import numpy
from typing import List, Generator
from .data import Position, Matched, adjacent, Move
from itertools import product
from collections import defaultdict
from time import time

def positions(shape):
    pos = list(product(range(shape[0]), range(shape[1])))
    pos.sort(key=lambda x: x[1])
    return pos


class Board:

    # Must have at least this many values in a row or col to form a match.
    min_match = 3

    # The maximum value for newly generated tile values.
    max_init_value = 4

    # The default shape of the board.
    default_shape = (8,8)

    def __init__(self, source, random_seed=None):
        '''
        Construct from size, shape, tile array or board object.
        '''
        if random_seed is None:
            random_seed = numpy.random.randint(0, 2**31)
        self.random_seed = random_seed

        self.rng = numpy.random.default_rng(random_seed)

        if source is None:
            source = self.default_shape
        if isinstance(source, int): # square
            source = (source, source)
        if isinstance(source, tuple): # default or custom shape
            if source[0] < self.min_match or source[1] < self.min_match:
                raise ValueError(f'Board shape is too small: {source}')

            self.tiles = self.randint(1, self.max_init_value, source)
            self.all_positions = positions(self.tiles.shape)
            self.assure_stable()
            return

        if isinstance(source, numpy.ndarray): # premade
            self.tiles = numpy.copy(source)
            self.all_positions = positions(self.tiles.shape)
            return

        if isinstance(source, Board): # copy
            self.tiles = numpy.copy(source.tiles)
            self.rng.bit_generator.state = source.rng.bit_generator.state
            self.all_positions = positions(self.tiles.shape)
            return

        raise TypeError(f'Board can not be constructed from: {type(source)}')
        
    def cardinal_ranges(self, pos: Position):
        '''
        Return dict of ranges of positions along each cardinal direction.

        The dict gives a range positions starting from pos and going in one of
        each cardinal direction.  The directions are the dictionary keys are
        "up", "down", "left", "right".
        '''
        row,col = pos
        nrows,ncols = self.tiles.shape
        return dict(
            up =  ((r,col) for r in range(row-1,-1,-1)),
            down= ((r,col) for r in range(row+1,nrows)),
            left= ((row,c) for c in range(col-1,-1,-1)),
            right=((row,c) for c in range(col+1,ncols))
        )

    def matched(self, seed: Position) -> Matched:
        '''
        Return a matched for pos or None.

        Does not change board.
        '''
        target = self.tiles[seed]

        m = defaultdict(list)
        for card, prange in self.cardinal_ranges(seed).items():
            for pos in prange:
                if self.tiles[pos] != target:
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
    def all_tiles(self):
        return self.tiles.flatten()

    def all_matches(self) -> List[Matched]:
        '''
        Return all matches in the current board.
        '''
        ret = list()
        for seed in self.all_positions:
            m = self.matched(seed)
            if m is None:
                continue
            ret.append(m)
        return ret

    def randint(self, vmin, vmax, shape=None):
        r = self.rng.integers(vmin, vmax, shape)
        return r


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
            ms = list(ms)
            rands = self.randint(0, mvmo, len(ms))
            for m,r in zip(ms,rands):
                val = self.tiles[m.origin]
                self.tiles[m.origin] = ((val + r - 1) % mvmo) + 1

    def set_random(self, pos):
        '''
        Set a random value at pos that is within bounds
        '''
        self.tiles[pos] = self.randint(1, self.max_init_value)

    def swap(self, seed, targ):
        '''
        Swap seed and targ values unconditionally.
        '''
        self.tiles[seed],self.tiles[targ] = self.tiles[targ],self.tiles[seed]
    
    def apply_gravity(self, matches: List[Matched]):
        '''
        Move tile values downward as possible. 
        '''

        if matches and not isinstance(matches[0], Matched):
            raise TypeError(f'expect List[Matched] not List[{type(matches[0])}]')

        all_m = set()
        for m in matches:
            all_m.update(m.matched)

        for col in range(self.tiles.shape[1]):
            nempty_below = 0
            for row in range(self.tiles.shape[0]-1, -1, -1):
                if (row,col) in all_m:
                    nempty_below += 1
                    continue
                self.tiles[row+nempty_below, col] = self.tiles[row, col]
            # fill in
            for row in range(nempty_below):
                self.set_random((row,col))

    def unique_new_matches(self) -> List[Matched]:
        match_values = sorted(self.all_matches(),
                              key=lambda x: x.value,
                              reverse=True)

        seen_positions = set()
        result = []

        for m in match_values:
            if any(pos in seen_positions for pos in m.all_positions):
                continue
            seen_positions.update(m.all_positions)
            result.append(m)
        return result

    def find_and_do_combos(self) -> int:
        """
        Find and perform combos on the given board. return points.
        """
        result = []
        matches = self.unique_new_matches()
        points = 0

        while matches:
            for m in matches:
                self.tiles[m.origin] = m.value

            self.apply_gravity(matches)
            points += sum(2 ** match.value for match in matches)
            matches = self.unique_new_matches()

        return points

    def can_swap(self, seed: Position, targ: Position) -> bool:
        if not adjacent(seed, targ):
            return False

        self.swap(seed, targ)
        ms = self.matched(seed)
        mt = self.matched(targ)
        self.swap(seed, targ)
        if ms or mt:
            return True

    def maybe_swap(self, seed: Position, targ: Position) -> int:
        '''
        Attempt to swap tiles, return points earned.

        zero points means move is illegal.
        '''
        if not adjacent(seed, targ):
            return 0
        self.swap(seed, targ)

        ms = self.matched(seed)
        mt = self.matched(targ)

        if not any ([ms, mt]):
            self.swap(targ, seed) # swap back
            return 0

        # we mutate the seed tile value to reflect the points of the group.
        all_matches = list()
        if ms:
            self.tiles[seed] = ms.value
            all_matches.append(ms)
        if mt:
            self.tiles[targ] = mt.value
            all_matches.append(mt)
        points = sum(2 ** match.value for match in all_matches)

        self.apply_gravity(all_matches)
        points += self.find_and_do_combos()
        return points

    def possible_moves(self) -> Generator[Move, None, None]:
        '''
        Generate possible moves in board.
        '''
        for seed in self.all_positions:
            row, col = seed

            # possible swaps above or left of seed
            for targ in [(row-1, col), (row, col-1)]:
                if targ[0] < 0 or targ[1] < 0:
                    continue
                if not self.can_swap(seed, targ):
                    continue
                board = Board(self)
                points = board.maybe_swap(seed, targ)
                if not points:
                    continue
                yield Move(seed, targ, points, board)

    def automove_hint(self) -> List[Position]:
        '''
        Return the automove hint as pair (seed,targ) positions.
        '''
        for seed in self.all_positions:
            row, col = seed

            for targ in [(row-1, col), (row, col-1)]:
                if targ[0] < 0 or targ[1] < 0:
                    continue
                if self.can_swap(seed, targ):
                    return (seed, targ)
        return

