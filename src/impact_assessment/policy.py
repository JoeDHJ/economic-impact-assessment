"""Illustrative delivery options, bounded by relevant demand and available timing."""
import json
from importlib.resources import files
from .model import scalar


def supply_data():
    return json.loads(files("impact_assessment").joinpath("data/supply.json").read_text(encoding="utf-8"))


def wage_data():
    return json.loads(files("impact_assessment").joinpath("data/wages.json").read_text(encoding="utf-8"))


def skills_data():
    return json.loads(files("impact_assessment").joinpath("data/skills.json").read_text(encoding="utf-8"))


def evaluate_option(*, seats, cost_per_seat_gbp, completion_rate, project_match_rate,
                    months_to_ready, deadline_months, relevant_fte_demand):
    seats=scalar(seats,"seats",0,1e6)
    cost=scalar(cost_per_seat_gbp,"cost_per_seat_gbp",0,1e7)
    completion=scalar(completion_rate,"completion_rate",0,1)
    match=scalar(project_match_rate,"project_match_rate",0,1)
    months=scalar(months_to_ready,"months_to_ready",0,1200)
    deadline=scalar(deadline_months,"deadline_months",0,1200)
    demand=scalar(relevant_fte_demand,"relevant_fte_demand",0,1e7)
    expected=seats*completion*match
    ready=min(expected,demand) if months<=deadline else 0.
    return {"seats":seats,"cost_gbp":seats*cost,"expected_project_matches":expected,
            "on_time_matches_capped":ready,"cost_per_on_time_match_gbp":seats*cost/ready if ready>0 else None,
            "months_to_ready":months,"deadline_months":deadline,"relevant_fte_demand":demand}


def policy_options(result):
    s=result["scenario"]
    onsite={r["soc2020"]:r["onsite_fte"] for r in result["occupations"]}
    rates={r["framework"]:r["achievement_rate"] for r in supply_data()}
    specs=[
        {"option":"Incumbent IT conversion","seats":60,"cost_per_seat_gbp":4000,
         "completion_rate":.85,"project_match_rate":.6,"months_to_ready":6,
         "deadline_months":s["construction_years"]*12,
         "relevant_fte_demand":onsite.get("3131",0)+onsite.get("2137",0),
         "evidence":"Official NCS network-engineer work and college routes; costs, rates and seats are scenario assumptions."},
        {"option":"Electrical apprenticeship cohort","seats":80,"cost_per_seat_gbp":18000,
         "completion_rate":rates["Electrical Installation"],"project_match_rate":.6,"months_to_ready":48,
         "deadline_months":s["construction_years"]*12,
         "relevant_fte_demand":onsite.get("5241",0),
         "evidence":"Completion ratio uses SDS Electrical Installation 2025/26 leavers, not a cohort success probability. 48-month readiness is a scenario."},
        {"option":"Experienced-worker recruitment","seats":30,"cost_per_seat_gbp":6000,
         "completion_rate":1,"project_match_rate":.7,"months_to_ready":3,
         "deadline_months":s["construction_years"]*12,
         "relevant_fte_demand":onsite.get("5241",0)+onsite.get("5225",0),
         "evidence":"Licensed/experienced applicants are assumed; screening, relocation and retention require validation. All numerical inputs are scenarios."},
    ]
    rows=[]
    for spec in specs:
        args={k:v for k,v in spec.items() if k not in ("option","evidence")}
        row={"option":spec["option"],"status":"scenario_option","evidence":spec["evidence"],**evaluate_option(**args)}
        row["completion_rate"]=spec["completion_rate"]
        row["project_match_rate"]=spec["project_match_rate"]
        rows.append(row)
    return rows
