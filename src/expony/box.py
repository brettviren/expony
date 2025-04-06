from expony.tiling import (
    assure_stable,
    Matched,
    Tiling as BaseTiling
)
import numpy
value_dtype = numpy.uint8



class Tiling(BaseTiling):
    def __init__(self, data, min_match=3):
        '''
        Initialize Box tiling with data.
        '''
        self._min_match = min_match
        if isinstance(data, str):
            self.from_string(data)
            return
        if isinstance(data, numpy.ndarray):
            self._tiles = numpy.array(data, copy=True, dtype=value_dtype)
            return
        raise TypeError(f'expony.box.Box can not be constructed from: {type(data)}')

    def clone(self):
        '''
        Return a copy of self
        '''
        return Tiling(self._tiles)

    def to_string(self):
        '''
        Serialize self to a string.
        '''
        text = [f'{self._tiles.shape[1]} ']
        text += [chr(ord("A")-1+val for v in self._tiles.flatten())]
        return ''.join(text)

    def from_string(self, string):
        '''
        Deserialize string to self.
        '''
        nrows, letters = string.split(" ", 1)
        nrows = int(nrows)
        ncols = len(letters)//nrows
        values = [ord(letter) - ord("A") + 1 for letter in letters]
        return numpy.array(values, dtype=value_dtype).reshape((nrows, ncols))


    def __getitem__(self, pos):
        '''
        Return the value of the tile at the given position.
        '''
        return self._tiles[pos]

    def __setitem__(self, pos, val):
        '''
        Set value of the tile at the given position.
        '''
        self._tiles[pos] = value_dtype(val)

    def swap(self, s, t):
        '''
        Swap the values at positions "seed" and "targ".
        '''
        self._tiles[s],self._tiles[t] = self._tiles[t],self._tiles[s]

    def positions(self):
        '''
        Yield all the positions in the tiling.

        This gives column-major order.  
        '''
        nrows, ncols = self._tiles.shape
        for irow in range(nrows):
            for icol in range(ncols):
                yield (irow, icol)

    def adjacent(self, a, b):
        '''
        Return True if positions a and b are adjacent.
        '''
        return ((a[0] == b[0] and abs(a[1] - b[1]) == 1) 
                or
                (a[1] == b[1] and abs(a[0] - b[0]) == 1))
        

    def neighbors(self):
        '''
        Yield unique, unordered pairs of positions that are considered
        neighbors.
        '''
        nrows, ncols = self._tiles.shape
        for irow in range(nrows):
            for icol in range(ncols):
                pos = (irow, icol)
                if irow+1 < nrows:
                    yield (pos, (irow+1, icol))
                if icol+1 < ncols:
                    yield (pos, (irow  , icol+1))

    def radii(self, pos):
        '''
        Return list of lists of positions radiating from seed position to edge.

        The outer list is size 4 in order right, up, left, down.
        '''

        row,col = pos
        nrows,ncols = self._tiles.shape
        return [
            ((row,c) for c in range(col+1,ncols)),
            ((r,col) for r in range(row-1,-1,-1)),
            ((row,c) for c in range(col-1,-1,-1)),
            ((r,col) for r in range(row+1,nrows))
        ]

    def matched(self, seed):
        '''
        Return a Matched for seed or None.
        '''
        target = self._tiles[seed]

        dir_matches = [[],[]]
        for idir, prange in enumerate(self.radii(seed)):
            idir = idir%2
            for pos in prange:
                if self._tiles[pos] != target:
                    break;
                dir_matches[idir].append(pos)
                
        others = set()
        for dir_match in dir_matches:
            if 1+len(dir_match) >= self._min_match:
                others.update(dir_match)
        if not others:
            return
        return Matched(seed, list(others), self[seed] + len(others) - 1)
    
    def compact(self, positions):
        '''
        Modify the tiling so that values at positions are nullified and the
        remaining positions are moved "down".

        Return the post-compactified positions that are left null.
        '''
        nrows, ncols = self._tiles.shape

        ret = set()
        for col in range(ncols):
            nempty_below = 0
            for row in range(nrows-1, -1, -1):
                if (row,col) in positions:
                    nempty_below += 1
                    continue
                self._tiles[row+nempty_below, col] = self._tiles[row, col]
            # fill in
            for row in range(nempty_below):
                ret.add((row,col))
        return ret

        
def make(fresh, size=8):
    '''
    Return a box of given size.

    The size is an int for square (size,size) or a tuple giving (nrows,ncols)
    '''
    if isinstance(size, int):
        size = (size, size)

    if not isinstance(size, tuple):
        raise TypeError(f'can not make expony.box.Tiling from data of type '
                        ' {type(data)}')        
    data = numpy.zeros(size, dtype=value_dtype)
    t = Tiling(data)
    for p, r in zip(t.positions(), fresh):
        t[p] = r
    assure_stable(t, fresh)
    return t


