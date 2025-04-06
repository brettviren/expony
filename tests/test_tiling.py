import time
import pytest
from expony.tiling import (
    Tiling,
    uniform_randoms,
    fresh_values,
)
import numpy

def test_no_abc_instantiate():
    with pytest.raises(TypeError):
        t = Tiling()            # abc 
    
def test_rands():
    rng = numpy.random.default_rng(12345)
    fresh = fresh_values(uniform_randoms(rng))
    wants = [1, 1, 3, 3, 2, 1, 2, 1, 3, 3]
    for want, have in zip(wants, fresh):
        assert want == have
        
        
