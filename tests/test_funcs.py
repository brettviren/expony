#!/usr/bin/env pytest
import pytest
from expony.funcs import (
    swap_tiles,
    merge_matches,
    apply_gravity,
    find_and_do_combos,
    maybe_swap,
)
from expony.data import (
    range_tiles,
    same_tiles,
    Board,
)
def test_swap_tiles():
    b = Board(range_tiles((3,3)))
    assert b[(0,0)].value == 0
    assert b[(0,1)].value == 1
    b2 = swap_tiles(b, (0,0), (0,1))
    assert b2[(0,0)].value == 1
    assert b2[(0,1)].value == 0

    
def test_merge_matches_apply_gravity():
    b = Board(same_tiles((3,3), 5))
    b[1,1].value = 6
    b[0,1].value = 6
    b[2,1].value = 6
    b[1,0].value = 6
    b[1,2].value = 6
    
    print(f'\nb=\n{b}')
    m = b.matched((1,1))
    assert m.origin == (1,1)
    assert len(m.matched) == 4
    assert m.value == 9        # 6+1 for merge-3 on the vert +2 more on the horiz
    
    b[m.origin].value = m.value
    bb = merge_matches(b, [m])

    gg = apply_gravity(b, [m])
    print(f'gg=\n{gg}')
    gg[(2,1)] == m.value

def test_combos():
    b = Board(same_tiles((3,3), 5))
    b[1,1].value = 6
    b[0,1].value = 6
    b[2,1].value = 6
    b[1,0].value = 6
    b[1,2].value = 6

    bps = find_and_do_combos(b)
    for bp in bps:
        print(f'{bp.points=}:\n{bp.board}')


def test_move():        
    b = Board(3)
    b[0,1].value = 6
    b[1,0].value = 6
    b[1,2].value = 6
    print(f'\n{b}')
    bps = maybe_swap(b, (0,1), (1,1))
    for bp in bps:
        print(f'{bp.points=}:\n{bp.board}')


