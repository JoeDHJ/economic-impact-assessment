import numpy as np
import pytest
from impact_assessment.model import IOModel


def toy(a=None):
    return IOModel([[.2,.1],[.4,.2]] if a is None else a,[2,3],[.4,.5],[.2,.3],[.1,.1],[.05,.05])


def test_hand_solvable_orientation_and_no_double_count():
    # (I-A)=[.8,-.1;-.4,.8], f=[70,20] -> x=[290/3,220/3].
    r=toy().solve([70,20])
    np.testing.assert_allclose(r["total_output"],[290/3,220/3])
    assert r["employment_fte"]["direct"]==200
    assert r["employment_fte"]["total"]==pytest.approx(1240/3)
    assert r["employment_fte"]["indirect"]==pytest.approx(640/3)
    assert r["output_gbp_m"]["total"]==pytest.approx(170)
    assert r["balance_max_error"]<1e-12
    # Transposing A would produce a different result; test guards row/column inversion.
    assert not np.allclose(toy(np.array([[.2,.1],[.4,.2]]).T).solve([70,20])["total_output"],r["total_output"])


def test_leakage_at_each_round_and_zero_demand():
    f=[70,20];r=toy().solve(f,0)
    np.testing.assert_allclose(r["total_output"],f)
    assert r["employment_fte"]["indirect"]==0
    assert r["additional_supplier_leakage_gbp_m"]==pytest.approx(48)
    r0=toy().solve([0,0]);assert r0["employment_fte"]["total"]==0
    half=toy().solve(f,.5)
    assert half["employment_fte"]["total"]<toy().solve(f)["employment_fte"]["total"]


@pytest.mark.parametrize("a",[[],[[.1,.2]],[[1,0],[0,1]],[[1.2,0],[0,.1]],[[.1,-.1],[0,.1]],[[float('nan'),0],[0,.1]]])
def test_bad_systems_rejected(a):
    with pytest.raises(ValueError):toy(a)


@pytest.mark.parametrize("f",[[],[1],[1,-1],[1,None],[1,float('inf')],["x",1]])
def test_bad_final_demand(f):
    with pytest.raises(ValueError):toy().solve(f)


def test_ill_conditioning_and_coefficient_dimensions():
    with pytest.raises(ValueError):toy([[.999999999,0],[0,0]])
    with pytest.raises(ValueError):IOModel([[0]],[-1],[.5],[.3],[0],[0])
    with pytest.raises(ValueError):IOModel([[0]],[1,2],[.5],[.3],[0],[0])
