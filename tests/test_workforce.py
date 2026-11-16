from copy import deepcopy
import numpy as np
import pytest
from impact_assessment.case import load_data,run_case
from impact_assessment.workforce import (default_workspace,validate_workspace,delivery_model,staffing_model,
    targets_model,candidate_model,solve_problem,run_workspace,bundled)


@pytest.fixture(scope="module")
def baseline():return run_workspace()


def test_hand_solved_integer_allocation_and_unfunded_gap():
    # Need 2.3 FTE; integer places force three hires. Two cheap places plus
    # one expensive place is the unique cost optimum, not 2.3 fractional hires.
    p={"matrix":[[-1,-1,-1],[1,1,0]],"upper":[-2.3,3],
       "lower_bounds":[0,0,0],"upper_bounds":[2,2,2.3],"integrality":[1,1,0],
       "critical_objective":[0,0,1],"all_objective":[0,0,1],"cost_objective":[1,2,0]}
    x,stages,error=solve_problem(p)
    assert x==pytest.approx([2,1,0],abs=1e-6)
    assert all(r["status"]=="optimal" for r in stages) and error<1e-5
    p["upper"][1]=0
    x,_,_=solve_problem(p);assert x==pytest.approx([0,0,2.3])


def test_delivery_preserves_work_but_changes_peaks():
    w=default_workspace();d=delivery_model(w);w["economic_scenario"]["construction_years"]=4
    other=delivery_model(w)
    assert d["construction_job_years"]==pytest.approx(run_case(w["economic_scenario"])["construction"]["job_years_fte"]["total"])
    assert other["construction_job_years"]==pytest.approx(d["construction_job_years"])
    assert other["peak_monthly_fte"]<d["peak_monthly_fte"]
    np.testing.assert_allclose(np.array(d["occupation_fte"]).sum(axis=1),[r["annualised_fte"] for r in d["months"]])
    w["economic_scenario"]["capital_gbp_m"]=0
    assert delivery_model(w)["construction_job_years"]==0


def test_continuous_coverage_and_task_factor_are_not_heads():
    w=default_workspace();st=staffing_model(w)
    assert st[0]["required_service_fte"]==pytest.approx(6*8760/1650)
    w["staffing"]["routine_workload_factor"]=.5;changed=staffing_model(w)
    assert changed[0]["required_service_fte"]==st[0]["required_service_fte"]/2
    assert changed[2]["required_service_fte"]==st[2]["required_service_fte"]


def test_end_of_engagement_retention_and_apprenticeship_timing():
    w=default_workspace();ts=targets_model(w,delivery_model(w),staffing_model(w));cs=candidate_model(w,ts)
    apprentice=next(c for c in cs if c["target_id"]=="operate_5241" and c["pathway"]=="apprentice")
    assert not apprentice["eligible"] and apprentice["maximum_places"]==0
    hire=next(c for c in cs if c["target_id"]=="operate_5241" and c["pathway"]=="hire")
    assert hire["coverage_per_place"]==pytest.approx(.85*.88**3)
    assert hire["coverage_per_place"]<hire["checkpoint_coverage_per_place"]
    w["economic_scenario"]["construction_years"]=4
    ts=targets_model(w,delivery_model(w),staffing_model(w));cs=candidate_model(w,ts)
    assert next(c for c in cs if c["target_id"]=="operate_5241" and c["pathway"]=="apprentice")["eligible"]


def test_actual_capacity_constraints_and_monthly_gaps(baseline):
    a=baseline["allocation"];p=baseline["workspace"]["programme"]
    assert a["critical_gap_fte"]<1e-5 and a["expected_gap_fte"]>0
    for field,budget in [("employer_transition_gbp","employer_transition_budget_gbp"),("public_transition_gbp","public_transition_budget_gbp"),("mentor_hours","mentor_hours_available")]:assert a[field]<=p[budget]+1e-5
    for route,cap in p["pathway_capacity"].items():assert sum(c["places"] for c in a["selected"] if c["pathway"]==route)<=cap
    for role in a["roles"]:
        rows=[r for r in a["coverage_months"] if r["target_id"]==role["id"]]
        assert rows[-1]["expected_gap_fte"]==pytest.approx(role["expected_gap_fte"])
        assert all(r["expected_gap_fte"]<=rows[-1]["expected_gap_fte"]+1e-8 for r in rows)
    assert baseline["economic"]["operations"]["onsite_fte"]==0
    assert baseline["guarantee_stress"]["social_npv"] is None
    assert a["public_supported_retained_capacity_fte"]<=a["covered_role_period_fte"]


@pytest.mark.parametrize("mutate",[
    lambda w:w["staffing"].update(noncoverage_hours=1950),
    lambda w:w["programme"].update(mentor_hours_available=float("nan")),
    lambda w:w["programme"]["pathway_capacity"].update(hire=2.5),
    lambda w:w["economic_scenario"].update(onsite_fte=100),
    lambda w:w["programme"].update(construction_target_soc=[{}]),
    lambda w:w["programme"]["pathways"][0].update(success_rate=True),
    lambda w:w.update(unknown=1),
])
def test_malformed_inputs_fail_before_solver(mutate):
    w=default_workspace();mutate(w)
    with pytest.raises(ValueError):validate_workspace(w)


def test_official_evidence_preserves_population_and_missingness():
    local=bundled("local-evidence.json");facts=bundled("project-evidence.json")["facts"]
    assert len(local)==39 and len(facts)==11
    missing=[r for r in local if r["status"]=="suppressed"]
    assert missing and all(r["value"] is None and r["source_native_value"]=="#" for r in missing)
    assert next(r for r in facts if r["claim_id"]=="P05")["status"]=="announced_project_projection"
    assert all(r["source_url"].startswith("https://") for r in local+facts)


@pytest.mark.parametrize("contents",["null","[]","{}"])
def test_explicit_invalid_workspace_cannot_fall_back_to_default(tmp_path,contents):
    from impact_assessment.cli import main
    source=tmp_path/"bad.json";source.write_text(contents,encoding="utf8")
    assert main(["workforce","--scenario",str(source),"--output",str(tmp_path/"result")])==2
    assert not (tmp_path/"result/workforce-results.json").exists()


def test_zero_capacity_export_retains_allocation_schema(tmp_path):
    import csv
    from impact_assessment.workforce_report import export_workspace
    w=default_workspace();w["programme"]["pathway_capacity"]={k:0 for k in w["programme"]["pathway_capacity"]}
    result=export_workspace(tmp_path,w)
    assert not result["results"][2]["allocation"]["selected"]
    with (tmp_path/"programme-allocations.csv").open(encoding="utf8") as f:
        reader=csv.DictReader(f);assert "places" in reader.fieldnames and "coverage_per_place" in reader.fieldnames
        assert list(reader)==[]
