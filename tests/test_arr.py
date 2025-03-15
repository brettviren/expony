import time
import pytest
from expony.arr import (
    Board,
)

def first_move(moves):
    return next(moves)

def biggest_move(moves):

    moves = list(moves)
    moves.sort(key=lambda m: -m.points)
    return moves[0]
    

def test_possible_moves_go_big():
    b = Board(8)
    print()
    print(b.tiles)
    
    nturns = 0
    total_points = 0
    start = time.time()
    while True:
        nturns += 1

        # the strategy
        try:
            move = next(b.possible_moves())
        except StopIteration:
            break
        total_points += move.points
        print(f'{nturns}: {move.seed} -> {move.targ} = {move.points}/{total_points}')
        b = move.board

    dt = time.time() - start
    hz = nturns/dt
    print(f'finished after {nturns} turns with {total_points} points in {dt:.1f} s / {hz:.1f} Hz')


def test_autoplay_many():

    for game_number in range(100):

        b = Board(8)
        # print()
        # print(b.tiles)

        nturns = 0
        total_points = 0
        start = time.time()
        while True:
            nturns += 1

            got = b.automove_hint()
            # print(f'{got=}')
            if not got:
                break
            seed, targ = got
            points = b.maybe_swap(seed, targ)
            total_points += points
            # print(f'{nturns}: {seed} -> {targ} = {points}/{total_points}')

        maxval = b.tiles.max()
        maxpts = 2**maxval
        dt = time.time() - start
        hz = nturns/dt
        print(f'{game_number:4d}: {total_points:6d} points, max {maxval:2d}/{maxpts:4d} in {dt:.1f} s / {hz:.1f} Hz after {nturns:4d} plays, seed={b.random_seed}')
