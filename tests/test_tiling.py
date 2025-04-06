import time
import pytest
from expony.tiling import (
    Tiling,
    fresh_values,
)
import random

def test_no_abc_instantiate():
    with pytest.raises(TypeError):
        t = Tiling()            # abc 
    
def make_fresh(seed=12345):
    rng = random.Random(seed)
    return fresh_values(rng)
    
def test_rands():
    fresh = make_fresh()
    gots = list([next(fresh) for n in range(10)])
    fresh = make_fresh()
    wants = [4, 1, 3, 3, 2, 3, 4, 2, 3, 1]
    for want, have in zip(wants, fresh):
        assert want == have
        assert have >= 1 and have <= 4
