import time
import pytest
from expony import box
from expony.tiling import (
    assure_stable,
    fresh_values,
    uniform_randoms,
    all_seeded_matches,
    can_swap,
    existing_matches,
    apply_matches,
    apply_swap_inplace,
    apply_swap_stepped,
)
import numpy


def make_fresh(seed=0):
    rng = numpy.random.default_rng(seed)
    fresh = fresh_values(uniform_randoms(rng))
    return fresh
    

def test_make_box():
    fresh = make_fresh(12345)
    b = box.make(fresh, 8)
    print(f'\n{b._tiles}')
    bwant = numpy.array([[1, 1, 3, 3, 2, 1, 2, 1],
                         [3, 3, 1, 3, 3, 1, 2, 3],
                         [3, 1, 3, 1, 1, 2, 1, 2],
                         [1, 3, 1, 3, 1, 2, 3, 2],
                         [3, 3, 2, 1, 2, 3, 2, 1],
                         [2, 2, 1, 3, 1, 2, 1, 2],
                         [1, 2, 1, 1, 2, 1, 1, 2],
                         [1, 1, 2, 2, 1, 1, 3, 1]])
    assert numpy.all(b._tiles == bwant)
    b2 = box.Tiling(bwant)
    assert numpy.all(b._tiles == b2._tiles)

    asm = all_seeded_matches(b)
    with pytest.raises(StopIteration):
        next(asm)

    assert not can_swap(b, (0,0), (0,1))
    assert     can_swap(b, (0,2), (1,2))

    got = apply_swap(b, (0,2), (1,2), fresh)
    print(b._tiles)
    assert got == 68

def test_existing_matches():
    bdata = numpy.array([[1, 1, 1, 3, 2, 1, 2, 1],
                         [3, 3, 3, 3, 3, 1, 2, 3],
                         [3, 1, 3, 1, 1, 2, 1, 2],
                         [1, 3, 1, 3, 1, 2, 3, 2],
                         [3, 3, 2, 1, 2, 3, 2, 1],
                         [2, 2, 1, 3, 1, 2, 1, 2],
                         [1, 2, 1, 1, 2, 1, 1, 2],
                         [1, 1, 2, 2, 1, 1, 3, 1]])
    b = box.Tiling(bdata)
    matches = existing_matches(b)

    assert len(matches) == 2
    # the 3's in row 1
    assert matches[0].origin == (1,0)
    assert len(matches[0].others) == 4
    assert matches[0].value == 6

    # the 1's in row 0
    assert matches[1].origin == (0,0)
    assert len(matches[1].others) == 2
    assert matches[1].value == 2

    fresh = make_fresh(12345)
    points, doomed = apply_matches(b, matches)
    assert(points == 68)
    # print(b._tiles)
    want = numpy.array(bdata)
    want[0] = [2, 0, 0, 3, 2, 1, 2, 1]
    want[1] = [6, 0, 0, 0, 0, 1, 2, 3]
    assert numpy.all(b._tiles == want)


def test_swap_inplace():
    fresh = make_fresh(12345)
    b = box.make(fresh, 8)
    print()
    print(b._tiles)
    got = apply_swap_inplace(b, (0,2), (1,2), fresh)
    print(b._tiles)
    print(got)
    
def test_swap_stepped():
    fresh = make_fresh(12345)
    b = box.make(fresh, 8)
    print()
    print(b._tiles)
    got, intermediates = apply_swap_stepped(b, (0,2), (1,2), fresh, True)
    for bi in intermediates:
        print(bi._tiles)
    print(got)
    
def test_board():
    fresh = make_fresh(12345)
    b = box.Board(box.make(fresh, 8), 100)
    assert b.frame[0] == (0,0)
    assert b.frame[1] == (800,800)
    assert numpy.all(b.position((50,50)) == (0,0))
    assert numpy.all(b.pixel((1,1)) == (150,150))

    b.set_frame((10,20), (80,80))
    assert b.frame[0] == (10,20)
    assert b.frame[1] == (80,80)

