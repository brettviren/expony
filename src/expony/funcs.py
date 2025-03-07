#!/usr/bin/env python
'''
Functions to implement original exponentile game logic.

These functions tend to produce new board for each step instead of mutating an
existing board in order to allow a GUI to animate transitions.

Also, the functions leave the tiles in place in their board and only change
their values.
'''

from typing import List
from expony.data import (
    Board,
    Tile,
    Position,
    Matched,
    BoardPoints,
    adjacent,
)



def swap_tiles(board: Board, seed: Position, targ: Position) -> Board:
    '''
    Make a new board and swap its seed and target tile values without constraint.
    '''
    swapped = Board(board)
    swapped[seed].value = board[targ].value
    swapped[targ].value = board[seed].value
    return swapped


def merge_matches(board: Board, matches: List[Matched]) -> Board:
    '''
    Return board with matches marked as merged.

    First half of moveTilesDown()
    '''
    removed = Board(board)
    for m in matches:
        for pos in m.matched:
            # set a special attribute on the tile
            removed[pos].merged = m.origin
    return removed


def apply_gravity(board: Board, matches: List[Matched]) -> Board:
    '''
    Move matched tiles in board downward, return new board.

    Second half of moveTilesDown()
    '''
    if matches and not isinstance(matches[0], Matched):
        raise TypeError(f'expect List[Matched] not List[{type(matches[0])}]')

    all_m = set()
    for m in matches:
        all_m.update(m.matched)

    gravity = Board(board)
    for col in range(gravity.shape[1]):
        nempty_below = 0
        for row in range(gravity.shape[0]-1, -1, -1):
            if (row,col) in all_m:
                nempty_below += 1
                continue
            gravity[row+nempty_below, col].value = gravity[row, col].value
        # fill in
        for row in range(nempty_below):
            gravity.set_random((row, col))
    return gravity


def move_tiles_down(board: Board, matches: List[Matched]) -> List[Board]:
    '''
    Merge matches and apply gravity returning two boards.

    This method is a monolith in the original exponentile but are actually
    independent functions.

    moveTilesDown().
    '''
    return [merge_matches(board, matches),
            apply_gravity(board, matches)]


def unique_new_matches(board) -> List[Matched]:
    '''
    Returns a list of positions that are the highest value matches.

    For example if there's a tile that matches 5 vertically and 2 horizontally,
    it will return that tile but not any of the other tiles of the match.

    uniqueNewMatches
    '''
    match_values = sorted(board.all_matches(),
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


def find_and_do_combos(board: Board) -> List[BoardPoints]:
    """
    Find and perform combos on the given board.

    Args:
        board (Board): The current state of the game board.

    Returns:
        List[Dict]: A list of dictionaries containing information about board points.
    """
    result = []
    matches = unique_new_matches(board)
    previous_board = Board(board)

    while matches:
        new_board = Board(previous_board)

        for m in matches:
            new_board[m.origin].value = m.value

        gravity = apply_gravity(new_board, matches)
        points = sum(2 ** match.value for match in matches)

        # Combine the current board with its points and the boards after gravity
        result.append(BoardPoints(new_board, points))
        result.append(BoardPoints(gravity,0))

        # Prepare for the next iteration
        matches = unique_new_matches(gravity)
        previous_board = gravity

    return result
    

def maybe_swap(board: Board, seed: Position, targ: Position) -> List[BoardPoints]:
    '''
    Attempt to swap tiles, return list of BoardPoints giving intermediate
    and final boards and points contributions if swap is legal else return None.
    '''
    if not adjacent(seed, targ):
        return
    swapped = swap_tiles(board, seed, targ)

    new_board = Board(swapped)

    ms = new_board.matched(seed)
    mt = new_board.matched(targ)
        
    # we mutate the seed tile value to reflect the points of the group.
    all_matches = list()
    if ms:
        new_board[seed].value = ms.value
        all_matches.append(ms)
    if mt:
        new_board[targ].value = mt.value
        all_matches.append(mt)
    if not all_matches:
        return

    merged, gravitied = move_tiles_down(new_board, all_matches)
    comboed = find_and_do_combos(gravitied)

    points = sum(2 ** match.value for match in all_matches)

    return [
        BoardPoints(swapped, 0),
        BoardPoints(new_board, points),
        BoardPoints(merged, 0),
        BoardPoints(gravitied, 0),
    ] + comboed        
        
