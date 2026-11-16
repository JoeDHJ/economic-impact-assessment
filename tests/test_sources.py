import json
from pathlib import Path
import numpy as np
import pandas as pd
from impact_assessment.case import load_data

ROOT=Path(__file__).resolve().parents[1]


def test_source_reconstruction_from_official_transactions():
    d=load_data()
    io=pd.read_excel(ROOT/"data/public/sources/SUT-2022.xlsx",sheet_name="IxI",header=None)
    z=io.iloc[7:105,3:101].to_numpy(float);output=io.iloc[114,3:101].to_numpy(float)
    np.testing.assert_allclose(np.array(d["a"])*output[None,:],z)
    assert output[d["codes"].index("12")]==0
    assert np.array(d["a"])[:,d["codes"].index("12")].sum()==0


def test_real_staffing_crosswalk_uses_worker_weights():
    d=load_data();s=pd.read_csv(ROOT/"data/public/sources/staffing.csv",dtype={"soc20_unit":str})
    group=s[(s.year==2025)&(s.SIC_name=="Construction")]
    value=group.loc[group.soc20_unit=="5241","industry_workers"].iloc[0]/group.industry_workers.sum()
    assert d["staffing"][d["codes"].index("41-43")][d["occupation_codes"].index("5241")]==value


def test_zero_employment_wage_ratios_are_missing_and_observed_wage_is_separate():
    d=load_data()
    assert d["compensation_per_fte_gbp"][d["codes"].index("12")] is None
    assert d["compensation_per_fte_gbp"][d["codes"].index("68.2IMP")] is None
    from impact_assessment.policy import wage_data
    w=wage_data();assert w["value"]==773.8 and w["price_year"]==2025
