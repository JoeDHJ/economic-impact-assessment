"""Portable workforce decision records; money and capacity ledgers stay separate."""
import csv
import json
from pathlib import Path
from .workforce import compare_workspaces, load_data, candidate_model


def write_csv(path, rows, fieldnames=None):
    if not rows and not fieldnames:
        path.write_text("", encoding="utf8")
        return
    with path.open("w", newline="", encoding="utf8") as handle:
        writer=csv.DictWriter(handle,fieldnames=fieldnames or list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def brief(result, comparison):
    a=result["allocation"];w=result["workspace"];g=result["guarantee_stress"]
    text=f"""# AI investment and workforce decision brief

Independent portfolio analysis by Haojian Dui. Model 0.2.0. Case: {w['name']}

## Decision

The mixed programme leaves **{a['expected_gap_fte']:.2f} role-period FTE** uncovered, including **{a['critical_gap_fte']:.2f} critical-role FTE**. A role-period FTE is a service-capacity requirement for one occupation and engagement period; these quantities are not unique people, observed hires or additional jobs. Critical-role coverage has first priority; total coverage has second priority; resource cost has third priority.

Commitments should remain conditional on qualified candidates, provider places and mentor availability being verified. Do not treat expected qualification/retention as safe operational clearance. Missing non-critical capacity still requires a funded service response. This is a programme-allocation comparison, not a causal estimate of training effectiveness.

## Four options

| Option | Years to launch | Critical gap | All-role gap | Employer transition £ | Public transition £ | Resource PV £m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
"""
    for row in comparison:
        text+=f"| {row['option']} | {row['construction_years']} | {row['critical_gap_fte']:.2f} | {row['expected_gap_fte']:.2f} | {row['employer_transition_gbp']:,.0f} | {row['public_transition_gbp']:,.0f} | {row['resource_pv_gbp']/1e6:.3f} |\n"
    text+=f"""
The no-programme case means no capacity commissioned through these four pathways. It does not assume the existing employer has no workers. The phased option changes timing and peak construction targets, so coverage denominators differ. It leaves cumulative IO work unchanged. Its later payments also receive more discounting; no project revenue, delay penalty, capex escalation or forgone output is modeled. Do not infer that postponement maximises project value.

## Distinct ledgers

- Scottish gross construction work: **{result['delivery']['construction_job_years']:,.2f} FTE job-years**, peak **{result['delivery']['peak_monthly_fte']:,.2f} annualised FTE**. The £{w['economic_scenario']['capital_gbp_m']:,.0f}m capital envelope is an independent 2022-basic-price assumption, not the announced financing converted into capex.
- Technical operating roster: **{result['operating_required_service_fte']:.2f} service FTE** from tasks and productive hours. This is a scenario, not DataVita's disclosed roster. Contracted capacity is not added again to modeled IO supplier jobs.
- Employer transition outlay: **£{a['employer_transition_gbp']:,.0f}**; public programme outlay: **£{a['public_transition_gbp']:,.0f}**; mentor demand: **{a['mentor_hours']:,.0f} hours**. Budgets constrain undiscounted scenario transition costs expressed at 2022 prices. Programme budget excludes ongoing pay/contract fees, which need separate funding.
- Combined programme resource present cost: **£{a['resource_pv_gbp']/1e6:.3f}m**. Includes transition resources and expected retained-worker pay/contract fees during engagements. Wages are employer costs here, not automatically social opportunity costs. Public funding is allocated between payers once; it is not added again as a resource cost.
- Public programme cost per supported retained capacity: **{('£'+format(a['public_cost_per_supported_capacity_fte_gbp'],',.0f')) if a['public_cost_per_supported_capacity_fte_gbp'] is not None else 'undefined'}**. Capacity is capped by role demand and restricted to publicly supported training routes. This is a descriptive scenario cost-effectiveness ratio, not incremental causal value for money.
- Announced guarantee: **£202m face value** on a £252.5m tranche (80% coverage), within approximately £300m financing. Under uncalibrated PD {g['default_probability_scenario']:.1%} and LGD {g['loss_given_default_scenario']:.1%}, the simple lifetime exposure illustration is **£{g['undiscounted_loss_illustration_gbp_m']:.2f}m**. Actual fiscal expected cost, social NPV and benefit-cost ratio remain unavailable; tenor, fees, calibrated risk and social counterfactuals are missing.

## What is observed

DataVita's DV1 expansion and DV3 new-build are the announced financed package. The developer's approximately 600 construction jobs and 100 permanent roles are forward-looking announcements without disclosed FTE or duration definitions. DV2 and the wider growth-zone employment headline are separate scopes. A disclosed 15-year lease is not a disclosed guarantee tenor or an observed utilisation rate.

Nomis North Lanarkshire records include resident occupation stocks (APS July 2025–June 2026), workplace employee jobs (BRES 2024) and nominal pay (ASHE 2025). These do not identify available applicants or spare training seats. Suppressed APS unemployment remains missing. Resident and workplace pay are separate populations and are not the 2022 salary assumptions used here.

## Next evidence and decisions

1. Request basic-price capex lines, timing and Scottish supplier contracts; replace assumed capture and phase weights only when verified.
2. Obtain the employer task/shift roster, baseline qualified staff, vendor responsibilities and competence requirements. Decide which service gaps must be treated as critical.
3. Confirm qualified-worker refresher eligibility, actual candidate pools, provider seats and protected mentor hours. Six-month refreshers do not qualify novice electricians; the 48-month apprenticeship assumption is a different route.
4. Fund ongoing payroll/contract costs separately from the transition budget. Test retention and demand scenarios before making commitments.
5. For a causal training evaluation, specify outcomes, treatment assignment and a defensible comparison group before claiming additional employment or productivity.

Sources: [DataVita disclosure](https://blog.datavita.co.uk/blog/datavita-secures-funding-data-centre-expansion), [UK Government announcement](https://www.gov.uk/government/news/lanarkshire-ai-growth-zone-secures-300-million-investment-as-dell-establishes-scottish-base), [Nomis local profile](https://www.nomisweb.co.uk/reports/lmp/lad/1778385246/report.aspx), [Green Book 2026](https://www.gov.uk/government/publications/the-green-book--2/the-green-book-2026). Frozen claim and observation records include dates, status, geography and units.
"""
    return text


def export_workspace(output, workspace=None):
    path=Path(output);path.mkdir(parents=True,exist_ok=True)
    comparison=compare_workspaces(workspace);result=comparison["results"][2]
    for name,value in [("workforce-results.json",result),("workforce-comparison.json",comparison),("workforce-inputs.json",result["workspace"])]:
        path.joinpath(name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8")
    write_csv(path/"decision-options.csv",comparison["comparison"])
    write_csv(path/"monthly-delivery.csv",result["delivery"]["months"])
    write_csv(path/"service-roster.csv",result["staffing"])
    allocation_fields=[*candidate_model(result["workspace"],result["targets"])[0],"places","expected_retained_fte"]
    write_csv(path/"programme-allocations.csv",result["allocation"]["selected"],allocation_fields)
    write_csv(path/"role-gaps.csv",result["allocation"]["roles"])
    write_csv(path/"retention-coverage.csv",result["allocation"]["coverage_months"])
    d=load_data()
    rows=[{"month":m+1,"soc2020":code,"label":d["occupation_labels"][j],"annualised_fte":values[j],"fte_job_years_in_month":values[j]/12} for m,values in enumerate(result["delivery"]["occupation_fte"]) for j,code in enumerate(d["occupation_codes"])]
    write_csv(path/"monthly-occupations.csv",rows)
    path.joinpath("workforce-decision-brief.md").write_text(brief(result,comparison["comparison"]),encoding="utf8")
    return comparison
