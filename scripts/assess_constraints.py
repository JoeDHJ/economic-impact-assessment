"""Small, declared decision sensitivities; no statistical search or calibration."""
from copy import deepcopy
from pathlib import Path
import json
from impact_assessment.workforce import default_workspace,run_workspace
from impact_assessment.workforce_report import write_csv

ROOT=Path(__file__).resolve().parents[1]
base=default_workspace();variants=[("Published mixed plan",base)]
budget=deepcopy(base);budget["programme"]["employer_transition_budget_gbp"]=1500000
variants.append(("Employer transition budget £1m → £1.5m",budget))
mentor=deepcopy(base);mentor["programme"]["mentor_hours_available"]=3000
variants.append(("Mentor capacity 1,800 → 3,000 hours",mentor))
routes=deepcopy(base);routes["programme"]["pathway_capacity"].update(redeploy=60,hire=100)
routes["programme"]["mentor_hours_available"]=3000
variants.append(("Redeploy 60 / hire 100 places; mentor 3,000h",routes))
rows=[]
for label,w in variants:
    r=run_workspace(w);a=r["allocation"]
    rows.append({"scenario":label,"employer_budget_gbp":w["programme"]["employer_transition_budget_gbp"],
        "public_budget_gbp":w["programme"]["public_transition_budget_gbp"],
        "mentor_capacity_hours":w["programme"]["mentor_hours_available"],
        "redeploy_capacity":w["programme"]["pathway_capacity"]["redeploy"],
        "hire_capacity":w["programme"]["pathway_capacity"]["hire"],
        **{k:a[k] for k in ["critical_gap_fte","expected_gap_fte","employer_transition_gbp","public_transition_gbp","mentor_hours","resource_pv_gbp"]}})
dest=ROOT/"outputs/workforce/constraint-sensitivities.csv";dest.parent.mkdir(parents=True,exist_ok=True)
write_csv(dest,rows)
for row in rows:print(json.dumps(row,ensure_ascii=True),flush=True)
