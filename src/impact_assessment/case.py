"""Construction final demand and procurement-led operations without double counting."""
import json
from importlib.resources import files
from copy import deepcopy
import numpy as np
from .model import IOModel, scalar


def load_data():
    return json.loads(files("impact_assessment").joinpath("data/model.json").read_text(encoding="utf-8"))


def default_scenario():
    return json.loads(files("impact_assessment").joinpath("data/scenario.json").read_text(encoding="utf-8"))


def validate_scenario(s, data):
    if not isinstance(s, dict):
        raise ValueError("scenario must be a JSON object")
    required = set(default_scenario())
    missing = required - s.keys()
    unknown = s.keys() - required
    if missing or unknown:
        raise ValueError(f"scenario fields: missing={sorted(missing)}, unknown={sorted(unknown)}")
    if s["schema_version"] != "portfolio.v1" or s["price_year"] != 2022 or s["currency"] != "GBP" or s["geography"] != "Scotland":
        raise ValueError("this snapshot requires portfolio.v1, Scotland, GBP and 2022 basic prices")
    if not isinstance(s["name"], str) or not s["name"].strip():
        raise ValueError("name must be nonempty text")
    scalar(s["capital_gbp_m"], "capital_gbp_m", 0, 100000)
    for k in ("construction_years", "operating_years"):
        v = scalar(s[k], k, 1, 100)
        if not isinstance(s[k], int):
            raise ValueError(f"{k} must be an integer")
    for k in ("supplier_retention", "resident_share", "load_factor"):
        scalar(s[k], k, 0, 1)
    scalar(s["pue"], "pue", 1, 3)
    for k in ("it_load_mw", "electricity_gbp_per_mwh", "electricity_io_valuation_gbp_per_mwh", "onsite_fte", "onsite_compensation_gbp"):
        scalar(s[k], k, 0, 1e7)
    codes = set(data["codes"])
    for field, amount in (("capital_components", "share"), ("operating_procurement", "gbp_m")):
        rows = s[field]
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"{field} must be a nonempty list")
        seen = set()
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"industry", amount, "capture"}:
                raise ValueError(f"{field} rows need industry, {amount} and capture only")
            if row["industry"] not in codes or row["industry"] in seen:
                raise ValueError(f"{field} contains unknown or duplicate industry")
            seen.add(row["industry"])
            scalar(row[amount], amount, 0, 1 if amount == "share" else 1e6)
            scalar(row["capture"], "capture", 0, 1)
            if row["industry"] == "35.1" and field == "operating_procurement":
                raise ValueError("electricity is derived from load/PUE/price; do not enter it again")
    if abs(sum(r["share"] for r in s["capital_components"]) - 1) > 1e-9:
        raise ValueError("capital component shares must sum to one")
    scalar(s["electricity_capture"], "electricity_capture", 0, 1)
    roles = s["onsite_roles"]
    if not isinstance(roles, list) or not roles:
        raise ValueError("onsite_roles must be a nonempty list")
    seen = set()
    for role in roles:
        if not isinstance(role, dict) or set(role) != {"soc2020", "share"}:
            raise ValueError("onsite_roles rows need soc2020 and share only")
        if role["soc2020"] not in data["occupation_codes"] or role["soc2020"] in seen:
            raise ValueError("onsite_roles contains unknown or duplicate SOC2020")
        seen.add(role["soc2020"])
        scalar(role["share"], "onsite role share", 0, 1)
    if abs(sum(r["share"] for r in roles)-1) > 1e-9:
        raise ValueError("onsite role shares must sum to one")
    return s


def run_case(scenario=None, data=None):
    d = data if data is not None else load_data()
    s = validate_scenario(deepcopy(default_scenario() if scenario is None else scenario), d)
    model = IOModel(d["a"], d["employment"], d["gva"], d["income"], d["imports_ruk"], d["imports_row"])
    index = {v: i for i, v in enumerate(d["codes"])}
    n = len(index)
    f = np.zeros(n)
    for row in s["capital_components"]:
        f[index[row["industry"]]] += s["capital_gbp_m"] * row["share"] * row["capture"]
    unsupported=(np.asarray(d["observed_output_gbp_m"])==0)
    if np.any(f[unsupported]>0):
        raise ValueError("positive Scottish demand targets an industry with no calibrated source output")
    construction = model.solve(f, s["supplier_retention"])
    construction["job_years_fte"] = construction.pop("employment_fte")
    construction["annual_average_fte"] = {k:v/s["construction_years"] for k,v in construction["job_years_fte"].items()}
    construction["initial_external_procurement_gbp_m"] = float(s["capital_gbp_m"]-f.sum())
    op = np.zeros(n)
    for row in s["operating_procurement"]:
        op[index[row["industry"]]] += row["gbp_m"] * row["capture"]
    mwh = s["it_load_mw"] * 8760 * s["load_factor"] * s["pue"]
    electricity = mwh * s["electricity_gbp_per_mwh"] / 1e6
    electricity_io=mwh*s["electricity_io_valuation_gbp_per_mwh"]/1e6
    op[index["35.1"]] = electricity_io * s["electricity_capture"]
    if np.any(op[unsupported]>0):
        raise ValueError("positive operating procurement targets an industry with no calibrated source output")
    operations = model.solve(op, s["supplier_retention"])
    operations["supplier_employment_fte"] = operations.pop("employment_fte")
    operations["onsite_fte"] = s["onsite_fte"]
    operations["total_annual_fte"] = s["onsite_fte"] + operations["supplier_employment_fte"]["total"]
    operations["resident_annual_fte"] = operations["total_annual_fte"] * s["resident_share"]
    operations["electricity_mwh"] = mwh
    operations["electricity_gbp_m"] = electricity
    operations["electricity_io_value_gbp_m"] = electricity_io
    operations["price_only_difference_gbp_m"] = electricity-electricity_io
    operations["annual_procurement_bill_gbp_m"] = electricity+sum(r["gbp_m"] for r in s["operating_procurement"])
    operations["onsite_compensation_gbp_m"] = s["onsite_fte"]*s["onsite_compensation_gbp"]/1e6
    operations["total_compensation_gbp_m"] = operations["income_gbp_m"]["total"]+operations["onsite_compensation_gbp_m"]
    operations["initial_external_procurement_gbp_m"] = float(sum(r["gbp_m"] for r in s["operating_procurement"])+electricity_io-op.sum())
    staffing = np.array(d["staffing"])  # industry x occupation; row sums may be <1
    c_jobs = np.array(construction["total_output"]) * model.employment
    o_jobs = np.array(operations["total_output"]) * model.employment
    onsite = np.zeros(len(d["occupation_codes"]))
    for role in s["onsite_roles"]:
        onsite[d["occupation_codes"].index(role["soc2020"])]+=s["onsite_fte"]*role["share"]
    occupation = []
    for i, code in enumerate(d["occupation_codes"]):
        occupation.append({"soc2020":code,"label":d["occupation_labels"][i],
            "construction_job_years":float(c_jobs@staffing[:,i]),
            "construction_annual_fte":float(c_jobs@staffing[:,i])/s["construction_years"],
            "operating_supplier_fte":float(o_jobs@staffing[:,i]),"onsite_fte":float(onsite[i]),
            "operating_total_fte":float(o_jobs@staffing[:,i]+onsite[i]),
            "uk_workers_observed_2025":d["occupation_workers"][i],"uk_demand_status_2025":d["demand_status"][i]})
    coverage = {
        "construction_allocated_job_years":float((c_jobs@staffing).sum()),
        "construction_unallocated_job_years":max(0.,float(c_jobs.sum()-(c_jobs@staffing).sum())),
        "operations_allocated_supplier_fte":float((o_jobs@staffing).sum()),
        "operations_unallocated_supplier_fte":max(0.,float(o_jobs.sum()-(o_jobs@staffing).sum())),
    }
    schedule = []
    for year in range(1,s["construction_years"]+s["operating_years"]+1):
        build=year<=s["construction_years"]
        schedule.append({"year":year,"phase":"construction" if build else "operation",
                         "annual_fte":construction["annual_average_fte"]["total"] if build else operations["total_annual_fte"],
                         "capital_gbp_m":s["capital_gbp_m"]/s["construction_years"] if build else 0})
    return {"schema_version":"portfolio.v1","status":"scenario_model_estimate","model_version":"0.1.0",
        "geography":"Scotland","price_year":2022,"currency":"GBP","scenario":s,
        "source_id":"sg_io_2022;skills_england_staffing_2025;sds_ma_2025_26",
        "source_url":"https://www.gov.scot/publications/input-output-latest/",
        "retrieved_at":"2026-11-16","source_vintage":"IO 2022; UK staffing 2025; training 2025/26",
        "unit_of_observation":"phase by SIC2007 industry and SOC2020 occupation",
        "period":"construction scenario followed by annual operation scenario",
        "construction":construction,"operations":operations,"occupations":occupation,"coverage":coverage,"schedule":schedule,
        "diagnostics":{"industries":n,"condition_number":model.condition,"spectral_radius":model.spectral_radius,
        "published_inverse_max_error":d["validation"]["inverse_max_error"]},
        "boundaries":["Type I: household-induced effects excluded, not estimated as zero.",
        "Construction FTE job-years and operating annual FTE must not be added as contemporaneous jobs.",
        "Operations are procurement-led: on-site FTE plus supplier FTE; data-centre revenue/output/GVA is not imputed.",
        "Gross modeled activity is not net job creation, net welfare, fiscal return or a causal impact.",
        "UK grouped-industry headcount staffing shares proxy Scottish FTE composition; unallocated demand is retained."]}


def sensitivities(s=None, data=None):
    s=default_scenario() if s is None else s
    d=load_data() if data is None else data
    variants=[("Base",{}),("Capital -25%",{"capital_gbp_m":s["capital_gbp_m"]*.75}),
        ("Capital +25%",{"capital_gbp_m":s["capital_gbp_m"]*1.25}),
        ("Build in 2 years",{"construction_years":2}),("Build in 4 years",{"construction_years":4}),
        ("On-site 60 FTE",{"onsite_fte":60}),("On-site 180 FTE",{"onsite_fte":180}),
        ("Extra supplier leakage 20%",{"supplier_retention":.8}),
        ("Electricity GBP60/MWh",{"electricity_gbp_per_mwh":60}),
        ("Electricity GBP140/MWh",{"electricity_gbp_per_mwh":140})]
    # Composition: shift 10 percentage points of capital from computers to construction.
    comp=deepcopy(s["capital_components"])
    if any(r["industry"]=="26" and r["share"]>=.1 for r in comp) and any(r["industry"]=="41-43" for r in comp):
        for r in comp:
            if r["industry"]=="26":r["share"]-=.1
            if r["industry"]=="41-43":r["share"]+=.1
        variants.append(("10pp capital to construction",{"capital_components":comp}))
    for capture,label in ((.7,"Construction capture 70%"),(1,"Construction capture 100%")):
        comp=deepcopy(s["capital_components"])
        for r in comp:
            if r["industry"]=="41-43":r["capture"]=capture
        variants.append((label,{"capital_components":comp}))
    rows=[]
    for name,changes in variants:
        v=deepcopy(s);v.update(changes)
        if v["capital_gbp_m"]>100000:
            rows.append({"scenario":name+" (outside supported capital range)","construction_job_years":None,
                "construction_annual_fte":None,"operating_annual_fte":None,"construction_gva_gbp_m":None,
                "annual_electricity_bill_gbp_m":None})
            continue
        r=run_case(v,d)
        rows.append({"scenario":name,"construction_job_years":r["construction"]["job_years_fte"]["total"],
            "construction_annual_fte":r["construction"]["annual_average_fte"]["total"],
            "operating_annual_fte":r["operations"]["total_annual_fte"],
            "construction_gva_gbp_m":r["construction"]["gva_gbp_m"]["total"],
            "annual_electricity_bill_gbp_m":r["operations"]["electricity_gbp_m"]})
    return rows
