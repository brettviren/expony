#!/usr/bin/env python
'''
This module includes an abstract base class Tiling that represents an expony
board and some functions that operate on it.

A tile in a tiling is located with an abstract position object that is opaque to
the Tiling class.

See box and hex for two tiling implementations.
'''

from abc import abstractmethod, ABC
from contextlib import contextmanager
from collections import namedtuple
from math import floor

Matched = namedtuple("Matched", "origin others value")

class Tiling(ABC):
    '''
    A Tiling provides all methods to interact with the tiled state.

    It abstracts the "position" of a tile to be an opaque object for use by the
    implementation only.  See board.Board() for an ABC mapping this abstract
    position to pixels.
    '''


    @abstractmethod
    def clone(self):
        '''
        Return a copy of self.
        '''
        pass

    @abstractmethod
    def __getitem__(self, pos):
        '''
        Return the value of the tile at the given position.
        '''
        pass

    @abstractmethod
    def __setitem__(self, pos, val):
        '''
        Set value of the tile at the given position.
        '''
        pass

    @abstractmethod
    def to_string(self):
        '''
        Serialize self to a string.
        '''
        pass

    @abstractmethod
    def from_string(self, string):
        '''
        Deserialize string to self.
        '''
        pass

    @abstractmethod
    def swap(self, seed, targ):
        '''
        Swap the values at positions "seed" and "targ".
        '''
        pass

    @abstractmethod
    def positions(self):
        '''
        Yield all the positions in the tiling.
        '''
        pass

    @abstractmethod
    def neighbors(self):
        '''
        Yield unique, unordered pairs of positions that are considered
        neighbors.
        '''
        pass

    @abstractmethod
    def adjacent(self, a, b):
        '''
        Return True if positions a and b are adjacent.
        '''
        pass

    @abstractmethod
    def radii(self, seed):
        '''
        Return list of lists of positions radiating from seed position to edge.

        The outer list is ordered by angle of the corresponding radius and is
        length 2*N where N is the number of directions (2 for box, 3 for hex).

        The inner list starts from the neighbor of seed along a radial direction
        and extends to a position at the edge of the board.  An inner list may
        be empty.
        '''
        pass

    @abstractmethod
    def matched(self, seed) -> Matched:
        '''
        Return a Matched giving the positions matched with seed or None.
        '''
        pass


    @abstractmethod
    def compact(self, positions):
        '''
        Modify tiling so that values at positions are nullified and
        remaining values are moved into their place according to some sense of
        "gravity".

        Return the post-compactified positions that are left null.
        '''
        pass
        

def all_seeded_matches(tiling):
    '''
    Yield all Matched in tiling
    '''
    ret = list()
    for seed in tiling.positions():
        m = tiling.matched(seed)
        if m is None:
            continue
        yield m


def assure_stable(tiling, fresh):
    '''
    Mutate tiling with values from fresh until there are not matches.

    See fresh_values().
    '''
    while True:
        nmatched = 0
        for m in all_seeded_matches(tiling):
            nmatched += 1
            for p, r in zip(m.others, fresh):
                tiling[p] = r
        if not nmatched:
            return


def uniform_randoms(rng):
    '''
    Yield uniform randoms in [0,1].
    '''
    while True:
        yield rng.uniform()


def fresh_values(urands, vmin=1, vmax=4):
    '''
    Yield integer values in [vmin,vmax], inclusive given generator of
    uniform random numbers in [0.0,1.0].
    '''
    dv = vmax-vmin
    for urand in urands:
        yield int(floor(vmin + dv*urand))


@contextmanager
def swapped(tiling, seed, targ):
    '''
    A context manager that swaps a tiling
    '''
    tiling.swap(seed, targ)
    try:
        yield tiling
    finally:
        tiling.swap(seed, targ)


def can_swap(tiling, seed, targ):
    '''
    Return True if swapping seed and targ positions is legal.
    '''
    if not tiling.adjacent(seed, targ):
        return False

    with swapped(tiling, seed, targ) as tiling:
        if tiling.matched(seed):
            return True
        if tiling.matched(targ):
            return True
        return False


def apply_gravity(tiling, doomed, fresh):
    '''
    Compact the tiling and freshen nullified values. 
    '''
    for pos,val in zip(tiling.compact(doomed), fresh):
        tiling[pos] = val


def apply_swap_inplace(tiling, seed, targ, fresh):
    if not can_swap(tiling, seed, targ):
        return 0
    tiling.swap(seed, targ)
    return apply_existing_inplace(tiling, fresh)

def apply_swap_stepped(tiling, seed, targ, fresh, inplace=True):
    if not can_swap(tiling, seed, targ):
        return (0, [])
    tiling.swap(seed, targ)
    tiling = tiling.clone()
    points, tilings = apply_existing_stepped(tiling, fresh)
    return points, [tiling] + tilings


    # matches = [m for m in [
    #     tiling.matched(seed),
    #     tiling.matched(targ)] if m]
    # if not matches:
    #     tiling.swap(targ, seed) # swap back
    #     return fail()
    # points, doomed = apply_matches(tiling, matches)
    

        
def apply_matches(tiling, matches):

    doomed = set()
    points = 0

    for m in matches:
        tiling[m.origin] = m.value
        points += 2**m.value
        doomed.update(m.others)

    for null in doomed:
        tiling[null] = 0

    return points, doomed
    



# def try_swap(tiling, seed, targ, return_nulled=False):
#     '''
#     Attempt swap seed and targ positions.

#     If successful, this leaves the tiling board with the value of the origin
#     position increased and value of other positions in the match(es) null.

#     Points earned are returned.

#     If return_nulled is True return tuple of (points,nulled) where nulled are
#     positions that are nulled.

#     Note, this leaves the tiling in an intermediate, unstable state.  To reach
#     stability call apply_gravity() and apply_matches().  See also apply_swap()
#     for these all bundled.
#     '''

#     if not tiling.adjacent(seed, targ):
#         return 0

#     tiling.swap(seed, targ)
#     ms = tiling.matched(seed)
#     mt = tiling.matched(targ)

#     if not any ([ms, mt]):
#         tiling.swap(targ, seed) # swap back
#         if return_nulled:
#             return (0, [])
#         return 0

#     # we mutate the seed tile value to reflect the points of the group.
#     doomed = set()
#     points = 0

#     for m in [ms, mt]:
#         if m:
#             tiling[m.origin] = m.value
#             points += 2**m.value
#             doomed.update(m.others)

#     for null in doomed:
#         tiling[null] = 0

#     if return_nulled:
#         return points, doomed
#     return points


# def _apply_swap(tiling, seed, targ, fresh, return_intermediates=False):
#     '''
#     Try to swap seed and targ, update tiling and return points.

#     If return_intermediates is True, tiling is not mutated and a tuple of
#     (points, tilings) is returned with tilings holding a list of tiling objects
#     representing intermediate states.
#     '''
#     points, doomed = try_swap(tiling, seed, targ, return_nulled=True)
#     if not points:
#         if return_intermediates:
#             return (0, [])
#         return 0

#     if return_intermediates:
#         tiling = tiling.clone()
#     apply_gravity(tiling, doomed, fresh)

#     if return_intermediates:
#         newpoints, newtilings = apply_matches(tiling, fresh, True)
#         return points+newpoints, [tiling] + newtilings
#     return points + apply_matches(tiling, fresh, False)


def existing_matches(tiling):
    '''
    Return all existing matches
    '''
    match_values = sorted(all_seeded_matches(tiling),
                          key=lambda m: m.value,
                          reverse=True)

    seen_positions = set()
    result = []

    for match in match_values:
        positions = [match.origin] + match.others
        if any(pos in seen_positions for pos in positions):
            continue
        seen_positions.update(positions)
        result.append(match)
    return result


def apply_existing_inplace(tiling, fresh):
    points = 0
    while matches := existing_matches(tiling):
        newpoints, doomed = apply_matches(tiling, matches)
        points += newpoints

        apply_gravity(tiling, doomed, fresh)
    return points


def apply_existing_stepped(tiling, fresh):
    tiling = tiling.clone()

    points = 0
    intermediates = list()
    while matches := existing_matches(tiling):
        newpoints, doomed = apply_matches(tiling, matches)
        points += newpoints
        intermediates.append(tiling.clone())

        apply_gravity(tiling, doomed, fresh)
        intermediates.append(tiling.clone())        
    return points, intermediates

# def _apply_existing_matches(tiling, fresh, return_intermediates=False):
#     '''
#     Find any matches and apply them.

#     Return points gained.

#     If return_intermediates is True, do not mutate tiling and instead return
#     tuple (points,tilings) where tilings are copies of intermediate states of
#     tiling.
#     '''

#     matches = existing_matches(tiling)
#     points = 0

#     while matches:
#         if return_intermediates:
#             tiling = tiling.clone()
#         for m in matches:
#             tiling[m[0]] = m.value
#             points += 2**m.value
#             if return_intermediates:
#                 intermediates.append(tiling.clone())

#         apply_gravity(tiling, doomed, fresh)
#         # ...
#         # apply_gravity(tiling, [m[1:] for m in matches], fresh)
#         matches = existing_matches(tiling)

#     return points

