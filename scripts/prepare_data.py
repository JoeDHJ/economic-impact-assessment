"""Rebuild compact model from downloaded official public sources. No network required."""
from pathlib import Path
import json
import re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/public/sources"
DEST = ROOT / "src/impact_assessment/data"
DEST.mkdir(parents=True, exist_ok=True)


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, allow_nan=False, separators=(",", ":"))+"\n", encoding="utf-8")


def prepare():
    io = pd.read_excel(RAW/"SUT-2022.xlsx", sheet_name="IxI", header=None)
    m = pd.read_excel(RAW/"SUT-2022.xlsx", sheet_name="Type I multipliers", header=None).iloc[7:105]
    codes = io.iloc[7:105, 1].astype(str).tolist()
    if io.iloc[5,3:101].astype(str).tolist()!=codes or m[1].astype(str).tolist()!=codes:
        raise ValueError("IO row/column/multiplier industry order does not match")
    if set(io.iloc[7:105,0])!={2022} or io.iloc[114,1]!="TOut":
        raise ValueError("unexpected source vintage or layout")
    z = io.iloc[7:105,3:101].to_numpy(float)
    output = io.iloc[114,3:101].to_numpy(float)
    if np.any(z[:,output==0]) or np.any(z[output==0,:]):
        raise ValueError("zero-output industry has nonzero intermediate transactions")
    def per_output(v):
        return np.divide(v, output, out=np.zeros_like(v,dtype=float), where=output>0)
    a = np.divide(z,output[None,:],out=np.zeros_like(z),where=output[None,:]>0)
    leontief = np.linalg.solve(np.eye(98)-a,np.eye(98))
    official = pd.read_excel(RAW/"SUT-2022.xlsx",sheet_name="Leontief type I",header=None).iloc[7:105,3:101].to_numpy(float)/1000
    emp = np.divide(m[7].to_numpy(float),m[13].to_numpy(float),out=np.zeros(98),where=m[13].to_numpy(float)!=0)
    gva = per_output(io.iloc[113,3:101].to_numpy(float))
    income = per_output(io.iloc[111,3:101].to_numpy(float))
    inverse_error = float(np.max(abs(official-leontief)))
    emp_error = float(np.max(abs(emp@leontief-m[7].to_numpy(float))))
    if inverse_error>1e-6 or emp_error>1e-5:
        raise ValueError("reconstructed model disagrees with published multipliers")
    # Accounts: domestic + imported inputs + net product taxes + GVA = output.
    accounting = z.sum(axis=0)+io.iloc[106:108,3:101].sum(axis=0).to_numpy(float)+io.iloc[109,3:101].to_numpy(float)+io.iloc[113,3:101].to_numpy(float)
    account_error=float(np.max(abs(accounting-output)))
    if account_error>1e-5:
        raise ValueError("source column accounting does not reconcile")
    staff=pd.read_csv(RAW/"staffing.csv",dtype={"soc20_unit":str})
    staff=staff[staff.year==2025].copy()
    if staff.duplicated(["soc20_unit","SIC_name"]).any():
        raise ValueError("duplicate industry/occupation staffing rows")
    staff["industry_workers"]=pd.to_numeric(staff.industry_workers,errors="raise")
    occ=staff[["soc20_unit","soc20_label","occupation_workers"]].drop_duplicates().sort_values("soc20_unit")
    if occ.soc20_unit.duplicated().any():raise ValueError("inconsistent occupation totals")
    occ_codes=occ.soc20_unit.tolist()
    mapping=pd.read_excel(RAW/"sic_map.xlsx",dtype=str)
    normalize=lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
    actual_names={normalize(name):name for name in staff.SIC_name.unique()}
    sic_to_name={str(sic).zfill(2):actual_names.get(normalize(name)) for sic,name in zip(mapping.SIC,mapping.Name)}
    groups=[];weights=[];coverage=[]
    for code in codes:
        sic=re.match(r"\d{2}",code).group()
        group=sic_to_name.get(sic)
        # Follow the publisher's SIC -> broad industry map. Never fuzzy-match labels.
        rows=staff[staff.SIC_name==group].set_index("soc20_unit")
        if rows.empty:
            weights.append([0.]*len(occ));coverage.append(0.);groups.append(None)
        else:
            vals=rows.industry_workers.reindex(occ_codes)
            if vals.isna().any() or (vals<0).any():raise ValueError("missing or negative staffing counts")
            weights.append((vals/vals.sum()).to_list());coverage.append(1.);groups.append(group)
    demand=pd.read_csv(RAW/"occupation_demand.csv",dtype={"soc20_unit":str}).set_index("soc20_unit")
    result={"schema_version":"portfolio.v1","source_id":"sg_io_2022","source_url":"https://www.gov.scot/publications/input-output-latest/",
        "retrieved_at":"2026-11-16","source_vintage":"2022; December 2025 release","geography":"Scotland",
        "unit_of_observation":"SIC2007 industry","period":"2022","currency":"GBP","price_year":2022,
        "status":"official_estimates_with_derived_coefficients","codes":codes,"labels":io.iloc[7:105,2].tolist(),
        "a":a.tolist(),"employment":emp.tolist(),"gva":gva.tolist(),"income":income.tolist(),
        "imports_ruk":per_output(io.iloc[106,3:101].to_numpy(float)).tolist(),
        "imports_row":per_output(io.iloc[107,3:101].to_numpy(float)).tolist(),
        "observed_output_gbp_m":output.tolist(),"observed_fte":(emp*output).tolist(),
        "compensation_per_fte_gbp":[float(income[i]*1e6/emp[i]) if emp[i]>0 else None for i in range(98)],
        "leontief":leontief.tolist(),"staffing":weights,"staffing_groups":groups,"staffing_coverage":coverage,
        "occupation_codes":occ_codes,"occupation_labels":occ.soc20_label.tolist(),
        "occupation_workers":occ.occupation_workers.astype(int).tolist(),
        "demand_status":[demand.loc[c,"demand_level"] if c in demand.index else "Not classified / unavailable" for c in occ_codes],
        "validation":{"inverse_max_error":inverse_error,"employment_effect_max_error":emp_error,"column_accounting_max_error_gbp_m":account_error}}
    dump(DEST/"model.json",result)
    summary=pd.DataFrame({"sic2007_io":codes,"industry":result["labels"],"output_gbp_m_2022":output,"fte_2022_derived":emp*output,
        "direct_fte_per_gbp_m":emp,"compensation_per_fte_gbp_2022":result["compensation_per_fte_gbp"],"staffing_proxy_group":groups,
        "source":"Scottish Government; Skills England","accessed_date":"2026-11-16"})
    summary.to_csv(ROOT/"data/processed/industries.csv",index=False)
    ap=pd.read_excel(RAW/"apprenticeships-2025-26.xlsx",sheet_name="2.1",header=None)
    selected=["Electrical Installation","Heating, Ventilation, Air Conditioning and Refrigeration","Digital Technology Technical Apprenticeship","Digital Technology","Plumbing and Heating","Engineering Asset Lifecycle and Maintenance"]
    supply=[]
    for label in selected:
        r=ap.loc[ap[1]==label].iloc[0]
        def number(i):return float(r[i]) if isinstance(r[i],(int,float)) and pd.notna(r[i]) else None
        supply.append({"framework":label,"starts":number(5),"in_training":number(13),"achievements":number(17),"leavers":number(9),
            "achievement_rate":number(21),"period":"2025/26","geography":"Scotland","status":"observed_official_administrative_count",
            "source":"Skills Development Scotland","source_id":"sds_ma_2025_26","source_url":"https://www.skillsdevelopmentscotland.co.uk/media/josfrdus/modern-apprenticeship-supplementary-tables-quarter-4-2025-26.xlsx","accessed_date":"2026-11-16"})
    dump(DEST/"supply.json",supply)
    pd.DataFrame(supply).to_csv(ROOT/"data/processed/training_supply.csv",index=False)
    wages=pd.read_excel(RAW/"ASHE-2025.xlsx",sheet_name="Table_1_1_1",header=None)
    if wages.iloc[4,0]!="All" or not str(wages.iloc[17,0]).startswith("2025"):
        raise ValueError("unexpected Scottish ASHE table layout")
    wage={"source_id":"sg_ashe_2025","source":"Scottish Government analysis of ONS ASHE",
        "source_url":"https://www.gov.scot/publications/annual-survey-of-hours-and-earnings-2025/pages/employee-earnings/",
        "retrieved_at":"2026-11-16","accessed_date":"2026-11-16","source_vintage":"2025 provisional; supporting workbook updated 7 October 2026",
        "geography":"Scotland","unit_of_observation":"full-time employee jobs, all sexes","period":"April 2025",
        "currency":"GBP","price_year":2025,"unit":"nominal GBP per week; median gross earnings",
        "status":"official_survey_estimate_provisional","schema_version":"portfolio.v1","value":float(wages.iloc[17,3])}
    dump(DEST/"wages.json",wage)
    pd.DataFrame([wage]).to_csv(ROOT/"data/processed/regional-wages.csv",index=False)
    crosswalk=pd.DataFrame({"sic2007_io":codes,"source_sic2":[re.match(r'\d{2}',c).group() for c in codes],"proxy_group":groups,
        "weighting":"UK 2025 industry worker counts / group total; same shares for each IO industry in group",
        "coverage":coverage,"source_id":"skills_england_staffing_2025"})
    crosswalk.to_csv(ROOT/"data/processed/industry_crosswalk.csv",index=False)
    print(json.dumps({"industries":len(codes),"occupations":len(occ),"mapped_industries":sum(coverage),"validation":result["validation"]},indent=2))


if __name__=="__main__":prepare()
