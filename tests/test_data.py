#!/usr/bin/env pytest
import pytest
from expony.data import (
    Position,
    Matched,
    Board,
    adjacent,
    range_tiles,
    same_tiles,
)

    
def test_board_basics():
    with pytest.raises(ValueError):
        Board((3,2))
    with pytest.raises(TypeError):
        Board("nope")
    b = Board()
    b.shape == Board.default_shape
    with pytest.raises(IndexError):
        b[10,10]
    b[0,0].value = 42
    assert b[0,0].value == 42

    shape = (3,3)
    ones = Board(same_tiles(shape, 1))
    assert ones.shape == shape
    assert len(list(ones.all_positions)) == 3*3
    for pos in ones.all_positions:
        assert ones[pos].value == 1

    counts = Board(range_tiles(shape))
    assert counts[0,0].value == 0
    assert counts[0,2].value == 2
    assert counts[1,0].value == 3


def test_board_cardinal():
    b = Board((5,5))
    cr = b.cardinal_ranges((2,2))
    assert len(cr) == 4
    for c, r in cr.items():
        l = list(r)
        assert len(l) == 2

def test_board_match():
    b = Board((3,3))
    targ = (1,1)
    b[targ].value = 5

    b[1,0].value = 5
    b[1,2].value = 5
    b[0,1].value = 5
    b[2,1].value = 5
    assert b[targ].value == 5

    m = b.matched(targ)
    assert isinstance(m, Matched)
    
    assert m.origin == targ
    assert len(m.matched) == 4
    assert m.value == 5 + 4 - 1

def test_stable():
    shape=(8,8)
    b = Board(same_tiles(shape, 1))
    print(f'before:\n{b}')
    b.assure_stable()
    print(f'after:\n{b}')
    s = set([b[pos].value for pos in b.all_positions])
    assert not b.all_matches()
    

def test_adjacent():
    assert adjacent((0,0), (0,1))
    assert adjacent((0,0), (1,0))
    assert adjacent((0,1), (0,0))
    assert adjacent((1,0), (0,0))

    assert not adjacent((0,0), (0,0))
    assert not adjacent((0,0), (0,2))    
    assert not adjacent((2,0), (0,0))    
    assert not adjacent((2,0), (0,2))
