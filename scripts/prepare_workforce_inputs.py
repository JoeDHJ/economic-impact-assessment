"""Write the published, explicitly assumed workforce planning input template."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
legacy = json.loads((ROOT/"src/impact_assessment/data/scenario.json").read_text(encoding="utf8"))
legacy.update(name="Conditional North Lanarkshire expansion package",capital_gbp_m=250,onsite_fte=0)

rows = [
    ("3131","IT operations",6,0,38000,True,True),
    ("2137","Networks",2,0,50000,True,False),
    ("5241","Electrical systems",2,0,40000,True,False),
    ("5225","Cooling systems",1,0,42000,True,False),
    ("2135","Cyber security",0,5,55000,True,False),
    ("1251","Facilities management",0,4,50000,False,False),
    ("4159","Administration",0,4,28000,False,False),
    ("5246","Technical maintenance",0,4,40000,False,False),
    ("2139","IT engineering support",0,6,48000,False,True),
]
roles=[]
for soc,label,continuous,day,salary,critical,scalable in rows:
    roles.append({"soc2020":soc,"label":label,"continuous_posts":continuous,"daytime_posts":day,
        "salary_gbp_2022":salary,"critical":critical,"routine_workload_sensitive":scalable})

paths=[
    {"id":"redeploy","label":"Internal conversion / qualified-worker refresher","lead_months":6,"max_places_per_role":20,
     "success_rate":.90,"annual_attrition":.08,"course_fee_gbp":4500,"recruitment_fee_gbp":0,
     "paid_release_gbp":1800,"onboarding_gbp":500,"mentor_hours":30,"public_fee_share":.5,
     "annual_cost_multiplier":1,"kind":"employee"},
    {"id":"hire","label":"Experienced external hire","lead_months":3,"max_places_per_role":35,
     "success_rate":.85,"annual_attrition":.12,"course_fee_gbp":0,"recruitment_fee_gbp":6500,
     "paid_release_gbp":0,"onboarding_gbp":1000,"mentor_hours":10,"public_fee_share":0,
     "annual_cost_multiplier":1,"kind":"employee"},
    {"id":"apprentice","label":"New apprenticeship cohort","lead_months":48,"max_places_per_role":20,
     "success_rate":.75,"annual_attrition":.08,"course_fee_gbp":18000,"recruitment_fee_gbp":0,
     "paid_release_gbp":24000,"onboarding_gbp":1000,"mentor_hours":120,"public_fee_share":.5,
     "annual_cost_multiplier":1,"kind":"employee"},
    {"id":"contract","label":"Qualified specialist contract","lead_months":1,"max_places_per_role":15,
     "success_rate":1,"annual_attrition":0,"course_fee_gbp":0,"recruitment_fee_gbp":0,
     "paid_release_gbp":0,"onboarding_gbp":2500,"mentor_hours":0,"public_fee_share":0,
     "annual_cost_multiplier":1.45,"kind":"contractor"},
]
workspace={
    "schema_version":"workforce.v1","name":"North Lanarkshire AI infrastructure workforce decision case",
    "project_evidence_id":"datavita-dv1-dv3-public-evidence-v1","currency":"GBP","price_year":2022,
    "status":"conditional_planning_scenario","economic_scenario":legacy,
    "delivery":{"phase_labels":["Preparation and design","Civil works","Electrical and equipment fit-out","Commissioning"],
        "phase_boundaries":[0,1/6,.5,5/6,1],
        "component_phase_weights":{"41-43":[.05,.55,.35,.05],"26":[0,0,.35,.65],"27":[0,.1,.7,.2],"71":[.6,.25,.1,.05]},
        "construction_occupation_factors":{"5241":[.2,.5,2,1.5],"5315":[.2,.6,1.8,1.2],"2121":[1.3,1.4,.6,.7],"5316":[.2,1.6,.8,.3]},
        "interpretation":"Phase timing and within-construction occupational factors are assumptions; each industry/phase profile is renormalised to preserve total FTE work."},
    "staffing":{"annual_paid_hours":1950,"noncoverage_hours":300,"daytime_weekly_hours":37.5,
        "employer_oncost_fraction":.25,"routine_workload_factor":1,"roles":roles,
        "interpretation":"Technical service coverage requirements, not a verified employer roster. Security, cleaning and vendor equipment services remain outside these roles."},
    "programme":{"employer_transition_budget_gbp":1000000,"public_transition_budget_gbp":250000,
        "mentor_hours_available":1800,"mentor_hourly_cost_gbp":40,"discount_rate":.035,
        "operating_engagement_months":36,"retention_checkpoint_months":12,
        "construction_target_share":.25,"construction_target_soc":["5241","5315","2121"],
        "construction_salary_gbp_2022":{"5241":40000,"5315":39000,"2121":50000},
        "pathway_capacity":{"redeploy":35,"hire":60,"apprentice":20,"contract":20},
        "pathways":paths,
        "interpretation":"Budgets, capacities, costs, success/attrition rates and leads are scenario inputs. Training counts and employee stocks do not supply these limits. Construction and operating cohorts are disjoint planning allocations; do not sum them as unique new workers."},
    "guarantee_stress":{"default_probability":.05,"loss_given_default":.5,"interpretation":"Uncalibrated lifetime exposure illustration; not an estimate of NWF loss, subsidy cost or value for money."},
}
dest=ROOT/"src/impact_assessment/data/workspace.json"
dest.write_text(json.dumps(workspace,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8")
print(dest)
