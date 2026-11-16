"""Time-specific demand, task coverage and constrained workforce allocation.

All planning inputs are scenarios. Official stocks/disclosures are context and
never substituted for project capex, applicants or provider spare capacity.
"""
from copy import deepcopy
from importlib.resources import files
import json
from math import isfinite

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from .case import load_data, validate_scenario, run_case
from .model import scalar


def bundled(name):
    return json.loads(files("impact_assessment").joinpath("data", name).read_text(encoding="utf8"))


def default_workspace():
    return bundled("workspace.json")


def _exact_keys(obj, expected, name):
    if not isinstance(obj, dict) or set(obj) != set(expected):
        raise ValueError(f"{name} must contain exactly: {', '.join(sorted(expected))}")


def _integer(value, name, low=0, high=10000):
    scalar(value, name, low, high)
    if not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")


def validate_workspace(w, d=None):
    d = load_data() if d is None else d
    template = default_workspace()
    _exact_keys(w, template, "workspace")
    if w["schema_version"] != "workforce.v1" or w["currency"] != "GBP" or w["price_year"] != 2022:
        raise ValueError("workspace requires workforce.v1 and GBP at 2022 prices")
    if w["project_evidence_id"] != template["project_evidence_id"] or w["status"] != "conditional_planning_scenario":
        raise ValueError("project evidence and planning status must match this snapshot")
    if not isinstance(w["name"],str) or not 1 <= len(w["name"].strip()) <= 180:
        raise ValueError("workspace name must contain 1–180 characters")
    s = validate_scenario(w["economic_scenario"], d)
    if s["onsite_fte"] != 0:
        raise ValueError("workforce workspace keeps IO supplier jobs separate; economic_scenario.onsite_fte must be zero")
    if not 1 <= s["construction_years"] <= 5:
        raise ValueError("workforce construction duration must be 1–5 whole years")
    v = w["delivery"]
    _exact_keys(v, template["delivery"], "delivery")
    if v["phase_labels"] != template["delivery"]["phase_labels"] or v["phase_boundaries"] != template["delivery"]["phase_boundaries"]:
        raise ValueError("the four phase definitions must match the documented model")
    if not isinstance(v["component_phase_weights"],dict) or set(v["component_phase_weights"]) != {r["industry"] for r in s["capital_components"]}:
        raise ValueError("phase weights must cover each capital component exactly")
    for code, weights in v["component_phase_weights"].items():
        if not isinstance(weights,list) or len(weights)!=4:
            raise ValueError("each capital component requires four phase weights")
        for value in weights: scalar(value,"phase weight",0,1)
        if abs(sum(weights)-1)>1e-9: raise ValueError("component phase weights must sum to one")
    if not isinstance(v["construction_occupation_factors"],dict):
        raise ValueError("occupation factors must be an object")
    for code, factors in v["construction_occupation_factors"].items():
        if code not in d["occupation_codes"] or not isinstance(factors,list) or len(factors)!=4:
            raise ValueError("occupation factors require a known SOC2020 and four values")
        for f in factors: scalar(f,"occupation factor",0,5)
    st = w["staffing"]
    _exact_keys(st, template["staffing"], "staffing")
    scalar(st["annual_paid_hours"],"annual_paid_hours",1000,2500)
    scalar(st["noncoverage_hours"],"noncoverage_hours",0,st["annual_paid_hours"]-100)
    scalar(st["daytime_weekly_hours"],"daytime_weekly_hours",1,60)
    scalar(st["employer_oncost_fraction"],"employer_oncost_fraction",0,1)
    scalar(st["routine_workload_factor"],"routine_workload_factor",.25,2)
    if not isinstance(st["roles"],list) or not 1 <= len(st["roles"]) <= 30:
        raise ValueError("staffing requires 1–30 roles")
    seen=set()
    for role in st["roles"]:
        _exact_keys(role, template["staffing"]["roles"][0], "role")
        if role["soc2020"] not in d["occupation_codes"] or role["soc2020"] in seen:
            raise ValueError("roster occupation must be known and unique")
        seen.add(role["soc2020"])
        if not isinstance(role["label"],str) or not 1<=len(role["label"])<=100:
            raise ValueError("role label requires 1–100 characters")
        for k in ("continuous_posts","daytime_posts"):scalar(role[k],k,0,100)
        scalar(role["salary_gbp_2022"],"salary_gbp_2022",0,250000)
        for k in ("critical","routine_workload_sensitive"):
            if not isinstance(role[k],bool):raise ValueError(f"{k} must be boolean")
    p=w["programme"]
    _exact_keys(p,template["programme"],"programme")
    for k in ("employer_transition_budget_gbp","public_transition_budget_gbp"):
        scalar(p[k],k,0,100000000)
    scalar(p["mentor_hours_available"],"mentor_hours_available",0,1000000)
    scalar(p["mentor_hourly_cost_gbp"],"mentor_hourly_cost_gbp",0,1000)
    scalar(p["discount_rate"],"discount_rate",0,.25)
    _integer(p["operating_engagement_months"],"operating_engagement_months",1,120)
    _integer(p["retention_checkpoint_months"],"retention_checkpoint_months",0,120)
    scalar(p["construction_target_share"],"construction_target_share",0,1)
    if not isinstance(p["construction_target_soc"],list) or len(p["construction_target_soc"])>12 or not all(isinstance(c,str) for c in p["construction_target_soc"]) or len(set(p["construction_target_soc"]))!=len(p["construction_target_soc"]):
        raise ValueError("construction SOC list must be unique")
    for code in p["construction_target_soc"]:
        if code not in d["occupation_codes"]:raise ValueError("unknown construction SOC")
    if not isinstance(p["construction_salary_gbp_2022"],dict) or set(p["construction_salary_gbp_2022"])!=set(p["construction_target_soc"]):
        raise ValueError("construction wages must cover selected SOCs")
    for value in p["construction_salary_gbp_2022"].values():scalar(value,"construction salary",0,250000)
    if not isinstance(p["pathways"],list) or len(p["pathways"])!=4:
        raise ValueError("four documented pathways are required")
    ids=set()
    for path in p["pathways"]:
        _exact_keys(path,template["programme"]["pathways"][0],"pathway")
        if path["id"] not in {"redeploy","hire","apprentice","contract"} or path["id"] in ids:
            raise ValueError("unknown or duplicate pathway")
        ids.add(path["id"])
        if not isinstance(path["label"],str) or not 1 <= len(path["label"]) <= 100:
            raise ValueError("pathway label requires 1–100 characters")
        if path["kind"] not in {"employee","contractor"}:raise ValueError("unknown workforce kind")
        if (path["id"]=="contract")!=(path["kind"]=="contractor"):
            raise ValueError("contract pathway must be contractor; other paths must be employee")
        _integer(path["lead_months"],"lead_months",0,120)
        _integer(path["max_places_per_role"],"max_places_per_role",0,200)
        for k in ("success_rate","public_fee_share"):scalar(path[k],k,0,1)
        scalar(path["annual_attrition"],"annual_attrition",0,.8)
        for k in ("course_fee_gbp","recruitment_fee_gbp","paid_release_gbp","onboarding_gbp"):
            scalar(path[k],k,0,1000000)
        scalar(path["mentor_hours"],"mentor_hours",0,10000)
        scalar(path["annual_cost_multiplier"],"annual_cost_multiplier",.5,5)
    if not isinstance(p["pathway_capacity"],dict) or set(p["pathway_capacity"])!=ids:
        raise ValueError("capacity must be specified for each pathway")
    for x in p["pathway_capacity"].values():_integer(x,"pathway capacity",0,1000)
    _exact_keys(w["guarantee_stress"],template["guarantee_stress"],"guarantee stress")
    for k in ("default_probability","loss_given_default"):scalar(w["guarantee_stress"][k],k,0,1)
    return w


def delivery_model(w, d=None):
    d=load_data() if d is None else d
    s=w["economic_scenario"]; n=len(d["codes"]); months=s["construction_years"]*12
    boundaries=[round(x*months) for x in w["delivery"]["phase_boundaries"]]
    f=np.zeros((months,n)); phases=[]
    for phase in range(4):
        start,end=boundaries[phase:phase+2]
        for c in s["capital_components"]:
            total=s["capital_gbp_m"]*c["share"]*c["capture"]
            f[start:end,d["codes"].index(c["industry"])]+=total*w["delivery"]["component_phase_weights"][c["industry"]][phase]/(end-start)
        phases.extend([phase]*(end-start))
    inverse=np.linalg.solve(np.eye(n)-s["supplier_retention"]*np.array(d["a"]),np.eye(n))
    output=f@inverse.T; industry_fte=output*np.array(d["employment"])[None,:]*12
    baseline=np.array(d["staffing"]); occ=np.zeros((months,len(d["occupation_codes"])))
    profiles=[]
    for phase in range(4):
        profile=baseline.copy(); row=d["codes"].index("41-43")
        for code,factors in w["delivery"]["construction_occupation_factors"].items():
            profile[row,d["occupation_codes"].index(code)]*=factors[phase]
        if profile[row].sum()<=0:raise ValueError("construction occupational profile has no positive weights")
        profile[row]/=profile[row].sum();profiles.append(profile)
    for m,phase in enumerate(phases):occ[m]=industry_fte[m]@profiles[phase]
    rows=[]
    for m in range(months):
        rows.append({"month":m+1,"phase":w["delivery"]["phase_labels"][phases[m]],
            "scottish_output_gbp_m":float(output[m].sum()),"annualised_fte":float(industry_fte[m].sum()),
            "fte_job_years_in_month":float(industry_fte[m].sum()/12)})
    return {"months":rows,"occupation_fte":occ.tolist(),"industry_fte":industry_fte.tolist(),
        "construction_job_years":float(industry_fte.sum()/12),"peak_monthly_fte":float(industry_fte.sum(axis=1).max()),
        "phase_boundaries":boundaries,"phase_occupational_profiles_status":"scenario_adjusted_UK_staffing_proxy"}


def staffing_model(w):
    st=w["staffing"]; productive=st["annual_paid_hours"]-st["noncoverage_hours"]
    rows=[]
    for role in st["roles"]:
        factor=st["routine_workload_factor"] if role["routine_workload_sensitive"] else 1
        hours=(role["continuous_posts"]*8760+role["daytime_posts"]*52*st["daytime_weekly_hours"])*factor
        rows.append({**role,"annual_coverage_hours":hours,"productive_hours_per_fte":productive,
            "required_service_fte":hours/productive,"annual_loaded_cost_per_fte":role["salary_gbp_2022"]*(1+st["employer_oncost_fraction"]),
            "status":"task_coverage_scenario_not_employer_roster"})
    return rows


def targets_model(w, delivery, staffing, d=None):
    d=load_data() if d is None else d; p=w["programme"]; targets=[]
    occ=np.array(delivery["occupation_fte"])
    for code in p["construction_target_soc"]:
        values=occ[:,d["occupation_codes"].index(code)]
        peak=int(np.argmax(values)); phase=next(i for i in range(4) if delivery["phase_boundaries"][i]<=peak<delivery["phase_boundaries"][i+1])
        deadline=delivery["phase_boundaries"][phase]
        duration=delivery["phase_boundaries"][phase+1]-deadline
        targets.append({"id":"build_"+code,"soc2020":code,"label":d["occupation_labels"][d["occupation_codes"].index(code)],
            "phase":"construction programme","required_fte":float(values[peak])*p["construction_target_share"],
            "regional_peak_fte":float(values[peak]),"target_share":p["construction_target_share"],
            "deadline_month":deadline,"engagement_months":duration,"critical":True,
            "annual_loaded_cost_per_fte":p["construction_salary_gbp_2022"][code]*(1+w["staffing"]["employer_oncost_fraction"]),
            "scope":"Scenario share of Scottish supply-chain occupation peak; not site headcount or measured local shortage"})
    for role in staffing:
        targets.append({"id":"operate_"+role["soc2020"],"soc2020":role["soc2020"],"label":role["label"],
            "phase":"operating service roster","required_fte":role["required_service_fte"],"regional_peak_fte":None,"target_share":None,
            "deadline_month":w["economic_scenario"]["construction_years"]*12,"engagement_months":p["operating_engagement_months"],
            "critical":role["critical"],"annual_loaded_cost_per_fte":role["annual_loaded_cost_per_fte"],
            "scope":"Task-based technical service capacity; employment/contract mix determined separately"})
    return targets


def candidate_model(w, targets, allowed=None):
    p=w["programme"]; candidates=[]
    for i,target in enumerate(targets):
        for path in p["pathways"]:
            if allowed is not None and path["id"] not in allowed:continue
            # New apprenticeships/refresher paths do not qualify civil engineers
            # or generic management/admin roles in this four-path template.
            eligible=not (path["id"]=="apprentice" and target["soc2020"] not in {"5241","5315","5225","3131","2137","5246"})
            if path["lead_months"]>target["deadline_month"]:eligible=False
            # Monotone attrition: covering the engagement-end requirement also
            # covers earlier months. A one-year checkpoint alone would conceal
            # later vacancies in a three-year service commitment.
            assess=target["engagement_months"]
            retention=(1-path["annual_attrition"])**(assess/12)
            coverage=path["success_rate"]*retention
            public=path["course_fee_gbp"]*path["public_fee_share"]
            mentor_cost=path["mentor_hours"]*p["mentor_hourly_cost_gbp"]
            upfront=sum(path[k] for k in ["course_fee_gbp","recruitment_fee_gbp","paid_release_gbp","onboarding_gbp"])+mentor_cost
            start=target["deadline_month"]-path["lead_months"]
            discount=(1+p["discount_rate"])**(-start/12) if start>=0 else 1
            wage_pv=0.
            for month in range(target["engagement_months"]):
                surviving=path["success_rate"]*(1-path["annual_attrition"])**((month+.5)/12)
                wage_pv+=surviving*target["annual_loaded_cost_per_fte"]*path["annual_cost_multiplier"]/12/(1+p["discount_rate"])**((target["deadline_month"]+month+.5)/12)
            candidates.append({"target_index":i,"target_id":target["id"],"pathway":path["id"],"label":path["label"],"kind":path["kind"],
                "eligible":eligible,"maximum_places":path["max_places_per_role"] if eligible else 0,
                "coverage_per_place":coverage,"success_rate":path["success_rate"],"annual_attrition":path["annual_attrition"],
                "assessment_months":assess,"start_month":max(0,start),"ready_month":target["deadline_month"],
                "checkpoint_coverage_per_place":path["success_rate"]*(1-path["annual_attrition"])**(min(p["retention_checkpoint_months"],assess)/12),
                "public_transition_gbp":public,"employer_transition_gbp":upfront-public,"mentor_hours":path["mentor_hours"],
                "transition_pv_gbp":upfront*discount,"employment_or_contract_pv_gbp":wage_pv,
                "resource_pv_gbp":upfront*discount+wage_pv})
    return candidates


def allocation_problem(w, targets, candidates):
    """Return a solver-neutral dense model (at most 210 variables)."""
    n=len(candidates); k=len(targets); width=n+k; p=w["programme"]
    rows=[]; upper=[]; labels=[]
    def constraint(values, limit, label):rows.append(values);upper.append(limit);labels.append(label)
    for field,key in [("employer_transition_gbp","employer_transition_budget_gbp"),("public_transition_gbp","public_transition_budget_gbp"),("mentor_hours","mentor_hours_available")]:
        constraint([c[field] for c in candidates]+[0.]*k,p[key],key)
    for path,cap in p["pathway_capacity"].items():
        constraint([1. if c["pathway"]==path else 0. for c in candidates]+[0.]*k,cap,"capacity_"+path)
    for i,t in enumerate(targets):
        row=[-c["coverage_per_place"] if c["target_index"]==i else 0. for c in candidates]+[0.]*k
        row[n+i]=-1.;constraint(row,-t["required_fte"],"coverage_"+t["id"])
    return {"matrix":rows,"upper":upper,"constraint_labels":labels,
        "lower_bounds":[0.]*width,"upper_bounds":[c["maximum_places"] for c in candidates]+[t["required_fte"] for t in targets],
        "integrality":[1]*n+[0]*k,
        "critical_objective":[0.]*n+[1. if t["critical"] else 0. for t in targets],
        "all_objective":[0.]*n+[1.]*k,"cost_objective":[c["resource_pv_gbp"]/1000 for c in candidates]+[0.]*k}


def solve_problem(problem):
    matrix=np.array(problem["matrix"],float); upper=np.array(problem["upper"],float)
    diagnostics=[]; vector=None
    for name in ("critical_objective","all_objective","cost_objective"):
        objective=np.array(problem[name],float)
        result=milp(objective,integrality=np.array(problem["integrality"]),
            bounds=Bounds(problem["lower_bounds"],problem["upper_bounds"]),
            constraints=LinearConstraint(matrix,np.full(len(upper),-np.inf),upper),
            options={"time_limit":15,"mip_rel_gap":1e-9})
        if not result.success or result.x is None:
            raise ValueError(f"workforce optimisation did not reach an optimum ({name}: {result.message})")
        vector=result.x
        value=float(objective@vector)
        diagnostics.append({"stage":name,"status":"optimal","objective":value,"mip_gap":float(getattr(result,"mip_gap",0) or 0)})
        if name!="cost_objective":
            matrix=np.vstack([matrix,objective]);upper=np.append(upper,value+1e-7)
    violation=float(max(0,np.max(matrix@vector-upper)))
    if violation>1e-5:raise ValueError("solver output violates resource/coverage constraints")
    for i,value in enumerate(vector):
        if value < -1e-6 or value > problem["upper_bounds"][i]+1e-5 or (problem["integrality"][i] and abs(value-round(value))>1e-5):
            raise ValueError("solver output violates bounds/integrality")
    return vector.tolist(),diagnostics,violation


def summarise_allocation(w, targets, candidates, vector, diagnostics, violation):
    n=len(candidates); selected=[]; coverage=np.zeros(len(targets)); private=public=mentor=pv=0.
    for j,c in enumerate(candidates):
        places=int(round(vector[j]))
        if not places:continue
        qualified=places*c["coverage_per_place"];coverage[c["target_index"]]+=qualified
        private+=places*c["employer_transition_gbp"];public+=places*c["public_transition_gbp"]
        mentor+=places*c["mentor_hours"];pv+=places*c["resource_pv_gbp"]
        selected.append({**c,"places":places,"expected_retained_fte":qualified})
    role_rows=[]; total_gap=critical_gap=covered=0.
    for i,t in enumerate(targets):
        gap=max(0.,t["required_fte"]-coverage[i]);role_rows.append({**t,"expected_retained_capacity_fte":float(coverage[i]),"expected_gap_fte":gap})
        total_gap+=gap;critical_gap+=gap if t["critical"] else 0;covered+=min(coverage[i],t["required_fte"])
    total=sum(t["required_fte"] for t in targets)
    supported=0.
    for i,t in enumerate(targets):
        training=sum(c["expected_retained_fte"] for c in selected if c["target_index"]==i and c["public_transition_gbp"]>0)
        supported+=min(training,t["required_fte"])
    coverage_months=[]
    for i,t in enumerate(targets):
        for month in range(t["engagement_months"]+1):
            available=sum(c["places"]*c["success_rate"]*(1-c["annual_attrition"])**(month/12) for c in selected if c["target_index"]==i)
            coverage_months.append({"target_id":t["id"],"project_month":t["deadline_month"]+month,
                "months_since_readiness":month,"required_service_fte":t["required_fte"],
                "expected_capacity_fte":available,"expected_gap_fte":max(0,t["required_fte"]-available)})
    return {"status":"expected_targets_covered" if total_gap<1e-5 else "expected_gaps_remain",
        "selected":selected,"roles":role_rows,"required_role_period_fte":total,"covered_role_period_fte":covered,
        "expected_gap_fte":total_gap,"critical_gap_fte":critical_gap,
        "employer_transition_gbp":private,"public_transition_gbp":public,"mentor_hours":mentor,
        "resource_pv_gbp":pv,"transition_cost_per_covered_fte_gbp":(private+public)/covered if covered>0 else None,
        "public_supported_retained_capacity_fte":supported,
        "public_cost_per_supported_capacity_fte_gbp":public/supported if supported>0 else None,
        "coverage_months":coverage_months,
        "solver":diagnostics,"max_constraint_violation":violation,
        "units_note":"Targets are disjoint occupation-period service capacities. Do not sum as unique people, realised hires or net new jobs. Expected qualification/retention is not safety clearance."}


def run_workspace(workspace=None, allowed=None):
    w=validate_workspace(deepcopy(default_workspace() if workspace is None else workspace))
    d=load_data(); delivery=delivery_model(w,d); staffing=staffing_model(w)
    targets=targets_model(w,delivery,staffing,d); candidates=candidate_model(w,targets,allowed)
    problem=allocation_problem(w,targets,candidates)
    vector,diagnostics,violation=solve_problem(problem)
    allocation=summarise_allocation(w,targets,candidates,vector,diagnostics,violation)
    economic=run_case(w["economic_scenario"],d)
    gap=abs(economic["construction"]["job_years_fte"]["total"]-delivery["construction_job_years"])
    if gap>1e-7:raise ValueError("delivery model does not reconcile with capital IO total")
    stress=w["guarantee_stress"]
    return {"schema_version":"workforce.v1","model_version":"0.2.0","status":"conditional_scenario_result",
        "workspace":w,"delivery":delivery,"staffing":staffing,"targets":targets,"allocation":allocation,
        "economic":economic,"operating_required_service_fte":sum(r["required_service_fte"] for r in staffing),
        "guarantee_stress":{"face_value_gbp_m":202,"tranche_gbp_m":252.5,"facility_gbp_m_approximately":300,
            "coverage_fraction_of_tranche":202/252.5,"default_probability_scenario":stress["default_probability"],
            "loss_given_default_scenario":stress["loss_given_default"],
            "undiscounted_loss_illustration_gbp_m":202*stress["default_probability"]*stress["loss_given_default"],
            "actual_expected_fiscal_cost":None,"social_npv":None,"benefit_cost_ratio":None,
            "note":"No observed default/loss evidence, tenor, fee/counterfactual or social benefits. This stress illustration is not an official loss estimate or subsidy appraisal."},
        "reconciliation_error_job_years":gap}


def compare_workspaces(workspace=None):
    w=deepcopy(default_workspace() if workspace is None else workspace); variants=[]
    none=deepcopy(w);none["name"]="No workforce programme"
    for k in none["programme"]["pathway_capacity"]:none["programme"]["pathway_capacity"][k]=0
    variants.append((none,None))
    hire=deepcopy(w);hire["name"]="Hire and contract only";variants.append((hire,{"hire","contract"}))
    mixed=deepcopy(w);variants.append((mixed,None))
    phased=deepcopy(w);phased["name"]="Phased launch (+12 months)" if w["economic_scenario"]["construction_years"]<5 else "Phased launch (5-year duration cap; unchanged)"
    if phased["economic_scenario"]["construction_years"]<5:
        phased["economic_scenario"]["construction_years"]+=1
    variants.append((phased,None))
    results=[run_workspace(v,allowed) for v,allowed in variants]
    for r,label in zip(results,["No workforce programme","Hire and contract only","Mixed workforce plan",phased["name"]]):r["option"]=label
    return {"schema_version":"workforce.v1","results":results,"comparison":[{
        "option":r["option"],"construction_years":r["workspace"]["economic_scenario"]["construction_years"],
        "required_role_period_fte":r["allocation"]["required_role_period_fte"],"expected_gap_fte":r["allocation"]["expected_gap_fte"],
        "critical_gap_fte":r["allocation"]["critical_gap_fte"],"employer_transition_gbp":r["allocation"]["employer_transition_gbp"],
        "public_transition_gbp":r["allocation"]["public_transition_gbp"],"resource_pv_gbp":r["allocation"]["resource_pv_gbp"],
        "peak_build_fte":r["delivery"]["peak_monthly_fte"],"operating_service_fte":r["operating_required_service_fte"]} for r in results]}
