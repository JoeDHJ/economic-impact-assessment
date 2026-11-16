from copy import deepcopy
import json
import numpy as np
import pytest
from impact_assessment.case import default_scenario,load_data,run_case,sensitivities
from impact_assessment.cli import main
from impact_assessment.policy import evaluate_option,policy_options
from impact_assessment.report import export_case


def test_real_case_and_published_reconciliation():
    d=load_data();r=run_case(data=d)
    assert len(d["codes"])==98 and len(d["occupation_codes"])==412
    assert d["validation"]["inverse_max_error"]<1e-6
    assert d["validation"]["employment_effect_max_error"]<1e-5
    assert d["validation"]["column_accounting_max_error_gbp_m"]<1e-5
    c,o=r["construction"],r["operations"]
    assert c["job_years_fte"]["total"]==pytest.approx(3981.2910823859947)
    assert c["gva_gbp_m"]["total"]==pytest.approx(259.0933009248394)
    assert c["output_gbp_m"]["direct"]==400
    assert o["total_annual_fte"]==pytest.approx(237.9607676329299)
    assert o["electricity_mwh"]==pytest.approx(189216)
    assert o["total_annual_fte"]==o["onsite_fte"]+o["supplier_employment_fte"]["total"]
    assert len(r["schedule"])==13
    assert sum(row["annual_fte"] for row in r["schedule"][:3])==pytest.approx(c["job_years_fte"]["total"])
    assert sum(row["construction_job_years"] for row in r["occupations"])+r["coverage"]["construction_unallocated_job_years"]==pytest.approx(c["job_years_fte"]["total"])
    assert sum(row["operating_total_fte"] for row in r["occupations"])+r["coverage"]["operations_unallocated_supplier_fte"]==pytest.approx(o["total_annual_fte"])
    np.testing.assert_allclose(np.array(d["staffing"]).sum(axis=1),1)


def test_timing_staffing_residence_and_zero_capital_are_independent():
    s=default_scenario();base=run_case(s)
    s["construction_years"]=4;s["onsite_fte"]=0;s["resident_share"]=0
    other=run_case(s)
    assert other["construction"]["job_years_fte"]==base["construction"]["job_years_fte"]
    assert other["construction"]["annual_average_fte"]["total"]==pytest.approx(base["construction"]["job_years_fte"]["total"]/4)
    assert other["operations"]["total_annual_fte"]==pytest.approx(base["operations"]["supplier_employment_fte"]["total"])
    assert other["operations"]["resident_annual_fte"]==0
    assert other["operations"]["output_gbp_m"]==base["operations"]["output_gbp_m"]
    s["capital_gbp_m"]=0
    assert run_case(s)["construction"]["job_years_fte"]["total"]==0


def test_contract_price_changes_bill_not_physical_activity():
    s=default_scenario();base=run_case(s);s["electricity_gbp_per_mwh"]=140;r=run_case(s)
    assert r["operations"]["electricity_gbp_m"]==pytest.approx(base["operations"]["electricity_gbp_m"]*1.4)
    assert r["operations"]["total_annual_fte"]==base["operations"]["total_annual_fte"]
    assert r["operations"]["electricity_io_value_gbp_m"]==base["operations"]["electricity_io_value_gbp_m"]


@pytest.mark.parametrize("field,value",[("price_year",2025),("geography","USA"),("capital_gbp_m",-1),("capital_gbp_m",None),("capital_gbp_m","1000"),("construction_years",0),("construction_years",2.5),("construction_years",3.0),("construction_years","3"),("onsite_fte",float('nan')),("pue",.9),("load_factor",2),("resident_share",True),("capital_components",[]),("onsite_roles",[])])
def test_invalid_scenarios(field,value):
    s=default_scenario();s[field]=value
    with pytest.raises(ValueError):run_case(s)


def test_unknown_duplicate_and_missing_inputs():
    s=default_scenario();del s["capital_gbp_m"]
    with pytest.raises(ValueError):run_case(s)
    s=default_scenario();s["new"]=1
    with pytest.raises(ValueError):run_case(s)
    s=default_scenario();s["capital_components"][0]["industry"]="unknown"
    with pytest.raises(ValueError):run_case(s)
    s=default_scenario();s["capital_components"][0]["share"]=.1
    with pytest.raises(ValueError):run_case(s)
    s=default_scenario();s["operating_procurement"][0]["industry"]="35.1"
    with pytest.raises(ValueError):run_case(s)
    s=default_scenario();s["onsite_roles"][0]["soc2020"]=s["onsite_roles"][1]["soc2020"]
    with pytest.raises(ValueError):run_case(s)


def test_policy_deadline_demand_cap_and_zero_denominator():
    kwargs=dict(seats=80,cost_per_seat_gbp=18000,completion_rate=.8,project_match_rate=.6,months_to_ready=48,deadline_months=36,relevant_fte_demand=18)
    p=evaluate_option(**kwargs)
    assert p["cost_gbp"]==1440000 and p["on_time_matches_capped"]==0
    assert p["cost_per_on_time_match_gbp"] is None
    kwargs["deadline_months"]=48;p=evaluate_option(**kwargs)
    assert p["on_time_matches_capped"]==18
    s=default_scenario();s["onsite_fte"]=0
    assert all(p["on_time_matches_capped"]==0 for p in policy_options(run_case(s)))


def test_positive_demand_for_unobserved_sector_rejected():
    s=default_scenario();s["capital_components"]=[{"industry":"12","share":1,"capture":1}]
    with pytest.raises(ValueError,match="no calibrated source output"):run_case(s)
    s["capital_components"][0]["capture"]=0
    assert run_case(s)["construction"]["job_years_fte"]["total"]==0


def test_custom_report_policy_adapts_to_zero_staff_and_later_launch(tmp_path):
    s=default_scenario();s.update(onsite_fte=0,construction_years=5)
    export_case(tmp_path,s)
    text=(tmp_path/"economic-impact-report.md").read_text(encoding="utf8")
    assert "zero on-site FTE" in text and "fits the current 60-month" in text
    assert "Commission a 60-seat" not in text


def test_exports_cli_unicode_and_malformed_json(tmp_path,capsys):
    out=tmp_path/"苏格兰 results";r=export_case(out)
    assert json.loads((out/"results.json").read_text(encoding="utf8"))["construction"]==r["construction"]
    assert (out/"occupations.csv").read_text(encoding="utf8").count("\n")==413
    assert main(["validate"])==0
    bad=tmp_path/"bad.json";bad.write_text("{",encoding="utf8")
    assert main(["run","--scenario",str(bad),"--output",str(out)])==2
    assert "Error:" in capsys.readouterr().err


@pytest.mark.parametrize("contents",["null","[]","{}"])
def test_explicit_nonobject_or_empty_scenario_does_not_run_default(tmp_path,contents):
    p=tmp_path/"scenario.json";p.write_text(contents)
    assert main(["run","--scenario",str(p),"--output",str(tmp_path/"out")])==2
    assert not (tmp_path/"out/results.json").exists()


def test_upper_capital_limit_exports_with_out_of_domain_variant_missing(tmp_path):
    s=default_scenario();s["capital_gbp_m"]=100000
    export_case(tmp_path,s)
    assert "outside supported capital range" in (tmp_path/"sensitivities.csv").read_text()


def test_sensitivities_have_interpretable_independent_changes():
    rows={r["scenario"]:r for r in sensitivities()};base=rows["Base"]
    assert rows["Build in 2 years"]["construction_job_years"]==base["construction_job_years"]
    assert rows["10pp capital to construction"]["construction_job_years"]>base["construction_job_years"]
    assert rows["Extra supplier leakage 20%"]["construction_job_years"]<base["construction_job_years"]
