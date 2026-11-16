"""Export usable analytical artifacts; no server or proprietary service required."""
import csv
import json
from pathlib import Path
from .case import load_data, run_case, sensitivities
from .policy import policy_options, supply_data, skills_data


def write_csv(path, rows):
    if not rows:
        raise ValueError("cannot export an empty table without a schema")
    with Path(path).open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def markdown_table(rows, columns, headers=None):
    def cell(v):
        if v is None:return "Unavailable"
        if isinstance(v,float):return f"{v:,.1f}"
        return str(v).replace("|","/").replace("\n"," ")
    return "| "+" | ".join(headers or columns)+" |\n| "+" | ".join("---" for _ in columns)+" |\n"+"\n".join("| "+" | ".join(cell(r[c]) for c in columns)+" |" for r in rows)+"\n"


def executive_brief(r):
    c,o=r["construction"],r["operations"]
    options=policy_options(r)
    recommendation=("Prioritise conversion training for existing IT staff and early recruitment of experienced electrical/cooling workers." if r["scenario"]["onsite_fte"]>0 else "The current scenario has no on-site workforce, so the modeled on-site training/recruitment options yield no role matches; verify supplier needs separately.")
    timing=("extends beyond" if options[1]["months_to_ready"]>r["scenario"]["construction_years"]*12 else "fits within")
    return f'''# Scotland AI data-centre investment: executive brief

Haojian Dui | Independent portfolio case | Model 0.1.0 | Evidence retrieved 16 November 2026

## Decision

Condition workforce commitments on a procurement schedule and a verified skills pipeline. {recommendation} The assumed electrical cohort readiness period {timing} the current construction schedule. A longer-term regional case needs its own demand evidence.

## What the model says

The illustrative £{r['scenario']['capital_gbp_m']:,.0f}m investment supports **{c['job_years_fte']['total']:,.0f} FTE job-years** of gross Scottish activity during construction, equivalent to **{c['annual_average_fte']['total']:,.0f} FTE per year** over {r['scenario']['construction_years']} years. Of the capital allocation, **£{sum(c['direct_output']):,.0f}m** is assumed to purchase Scottish production at basic prices. Construction gross value added is **£{c['gva_gbp_m']['total']:,.1f}m**; turnover/output is **£{c['output_gbp_m']['total']:,.1f}m**. These are different measures (economic-impact-report.md, Table 2).

Operations support **{o['total_annual_fte']:,.0f} annual FTE**, consisting of {o['onsite_fte']:,.0f} assumed on-site FTE and {o['supplier_employment_fte']['total']:,.0f} modeled supplier FTE. The electricity scenario requires {o['electricity_mwh']/1000:,.1f} GWh each year and costs £{o['electricity_gbp_m']:,.1f}m in 2022 prices. Supplier activity excludes the centre's own revenue and value added (Table 3).

## What changes the decision

Construction duration changes annual staffing pressure without changing cumulative job-years. Procurement capture and the split between imported computers and domestic building work change the scale of local activity. Operating headcount is an independent project assumption; the investment budget cannot establish it. Sensitivities are separate scenario comparisons, not confidence intervals (Table 7).

## Workforce evidence

Scottish administrative data record **659 Electrical Installation apprenticeship achievements** in 2025/26 from 834 starts in that year and 3,037 apprentices in training. These are different cohorts and cannot be divided to estimate a success rate. The published achievement/leaver ratio is 79.5%. The same source records 74 HVAC/refrigeration achievements and 510 Digital Technology Technical Apprenticeship achievements. These workers are already linked to employers; the counts measure an existing training channel, not applicants available to this project.

The Scottish Employer Skills Survey 2024 reports that 60% of vacancies in skilled trades were hard to fill for skill reasons. This supports early employer/provider engagement, while it does not measure shortages in a particular site or occupation. UK 2025 industry staffing shares proxy Scottish occupational composition. Actual local applicants, training-provider spare capacity and contractor schedules are needed before any shortage can be quantified.

## Next investment-committee gate

Obtain a site-specific supplier bill of quantities, binding grid terms, role/shift requirements, provider seats with start dates, and applicant/contractor evidence. Assess displacement, alternative use of public funds, grid and water costs, carbon impacts and tax commitments separately. The present model measures gross activity; it does not establish net welfare, additional jobs or a subsidy return.

Sources: [Scottish Government IO 2022](https://www.gov.scot/publications/input-output-latest/), [Skills England 2025 staffing](https://explore-education-statistics.service.gov.uk/find-statistics/occupations-in-demand/2025/explore), [SDS apprenticeship tables](https://www.skillsdevelopmentscotland.co.uk/media/josfrdus/modern-apprenticeship-supplementary-tables-quarter-4-2025-26.xlsx), [ESS 2024 Scotland](https://www.gov.scot/publications/employer-skills-survey-2024-scotland/pages/skill-shortage-vacancies/).
'''


def full_report(r,d,industry,sen,pol):
    c,o=r["construction"],r["operations"]
    top=sorted(r["occupations"],key=lambda x:x["construction_job_years"],reverse=True)[:12]
    op=sorted(r["occupations"],key=lambda x:x["operating_total_fte"],reverse=True)[:12]
    components=[{"industry":d["labels"][d["codes"].index(x["industry"])],"capital_share_pct":x["share"]*100,"scottish_capture_pct":x["capture"]*100} for x in r["scenario"]["capital_components"]]
    component_table=markdown_table(components,["industry","capital_share_pct","scottish_capture_pct"],["Industry","Capital share %","Scottish production capture %"])
    if o["onsite_fte"]>0:
        recommendation=f"The current conversion option has {pol[0]['on_time_matches_capped']:,.1f} on-time matches after the role-demand cap, at £{pol[0]['cost_gbp']:,.0f} cohort cost. Reserve places only after employers confirm eligible workers and a provider confirms capacity. The recruitment option has {pol[2]['on_time_matches_capped']:,.1f} on-time matches; competence and relocation require verification."
    else:
        recommendation="The current scenario specifies zero on-site FTE. All three options therefore have zero on-site role matches. Do not commission these cohorts against an absent on-site roster; establish supplier requirements separately."
    ap_timing="misses" if pol[1]["months_to_ready"]>r["scenario"]["construction_years"]*12 else "fits"
    return f'''# Economic impact and workforce assessment

Scotland AI data-centre investment | Haojian Dui | 16 November 2026 | Version 0.1.0

This independent portfolio case asks what a hypothetical AI data-centre investment could mean for Scottish suppliers, occupations and workforce policy. The investment is a scenario; no client engagement, investment announcement or observed project outcome is claimed. Monetary amounts are GBP million at **2022 basic prices**, excluding VAT and separately purchased margins. Public economic accounts are estimates of observed economic activity; modeled project impacts depend on the scenario.

## 1. Investment and procurement

The capital envelope is £{r['scenario']['capital_gbp_m']:,.0f}m, spread evenly across {r['scenario']['construction_years']} years. Table 1 shows the current component shares and production capture assumptions. The components are mutually exclusive owner purchases: construction excludes separately purchased IT and electrical assets. Capture applies to production, not reseller invoice location. A procurement analyst must translate a purchaser-price budget into basic-price production and trade/transport margins before applying this case to a live project.

### Table 1. Current capital allocation

{component_table}

Exactly £{sum(c['direct_output']):,.1f}m enters Scottish final demand. The remaining £{c['initial_external_procurement_gbp_m']:,.1f}m is initial external procurement, with no Scottish multiplier applied. Scotland's domestic coefficient matrix already excludes imports from the rest of the UK and the rest of the world. No national multiplier is presented as a local multiplier.

## 2. Construction impact

### Table 2. Gross construction activity over the full build

'''+markdown_table([
    {"measure":"Output, GBP m",**c["output_gbp_m"]},
    {"measure":"GVA, GBP m",**c["gva_gbp_m"]},
    {"measure":"Employee compensation, GBP m",**c["income_gbp_m"]},
    {"measure":"FTE job-years",**c["job_years_fte"]},
    {"measure":"Annual average FTE",**c["annual_average_fte"]}], ["measure","direct","indirect","total"])+f'''
Notes: Type I domestic requirements; direct means production meeting the capital final-demand vector, including building contractors and equipment producers. Indirect means their Scottish supply chains. Each row's total already includes direct effects. FTE job-years are work volume, not unique workers or permanent jobs. Even spending is a timing assumption; peak staffing is not estimated. Household-induced effects are excluded.

The model implies £{c['gva_gbp_m']['total']:,.1f}m in construction GVA compared with £{c['output_gbp_m']['total']:,.1f}m in gross output. Gross output counts intermediate sales, so it is not GDP and cannot be treated as a benefit-cost numerator. Scottish production also uses £{c['intermediate_imports_ruk_gbp_m']:,.1f}m of inputs from the rest of the UK and £{c['intermediate_imports_row_gbp_m']:,.1f}m from the world. These intermediate imports are separate from the initial external procurement allocation; none is added to domestic output.

## 3. Operating activity

### Table 3. Annual operation: project staff and procurement supply chains

'''+markdown_table([
    {"measure":"On-site FTE (scenario)","value":o["onsite_fte"]},
    {"measure":"Scottish first-tier supplier FTE","value":o["supplier_employment_fte"]["direct"]},
    {"measure":"Scottish upstream supplier FTE","value":o["supplier_employment_fte"]["indirect"]},
    {"measure":"On-site + all supplier annual FTE","value":o["total_annual_fte"]},
    {"measure":"Supplier output, GBP m/year","value":o["output_gbp_m"]["total"]},
    {"measure":"Supplier GVA, GBP m/year","value":o["gva_gbp_m"]["total"]},
    {"measure":"On-site + supplier compensation, GBP m/year","value":o["total_compensation_gbp_m"]},
    {"measure":f"Resident annual FTE at assumed {r['scenario']['resident_share']*100:g}% share","value":o["resident_annual_fte"]}], ["measure","value"])+f'''
Notes: The operating demand vector purchases electricity, telecommunications, repairs, security and building services. It does not purchase a data centre's own output. On-site staffing is added once and excludes outsourced supplier staff. On-site compensation is a scenario £{r['scenario']['onsite_compensation_gbp']:,.0f} per FTE in 2022 prices. The resident share changes the residence allocation of employment only; it does not reduce place-of-work output. No household spending closure is used. Centre revenue, own GVA, tax and profits remain unestimated.

The engineering scenario is {r['scenario']['it_load_mw']} MW IT load × 8,760 hours × {r['scenario']['load_factor']} load factor × {r['scenario']['pue']} power usage effectiveness = {o['electricity_mwh']:,.0f} MWh/year. A £{r['scenario']['electricity_gbp_per_mwh']} per MWh contract price yields a £{o['electricity_gbp_m']:,.1f}m annual electricity bill. The IO vector values physical output at the fixed scenario benchmark £{r['scenario']['electricity_io_valuation_gbp_per_mwh']} per MWh in 2022 prices, or £{o['electricity_io_value_gbp_m']:,.1f}m before capture. Contract-price changes alter the bill, not physical output or FTE. This is a valuation scenario, not a tariff forecast or confirmation of grid capacity.

## 4. Industries, occupations and skills

### Table 4A. Largest construction occupation allocations

'''+markdown_table(top,["soc2020","label","construction_job_years","construction_annual_fte"],["SOC2020","Occupation","FTE job-years","Annual average FTE"])+'''
### Table 4B. Largest operating occupation allocations

'''+markdown_table(op,["soc2020","label","onsite_fte","operating_supplier_fte","operating_total_fte"],["SOC2020","Occupation","On-site FTE","Supplier FTE","Total annual FTE"])+f'''
Notes: UK 2025 worker counts from Skills England define staffing shares within 18 broad industries, transferred to 98 Scottish IO industries using the publisher's SIC mapping. The same broad shares apply within a group; this does not recover detailed Scottish staffing or data-centre-specific roles. Applying headcount shares to FTE assumes similar part-time patterns across occupations within a group. On-site role shares are project assumptions. UK demand classifications are contextual indicators, not Scottish shortage estimates. The allocated construction total is {r['coverage']['construction_allocated_job_years']:,.1f} FTE job-years; {r['coverage']['construction_unallocated_job_years']:,.1f} remains unallocated.

Occupation demand points to separate delivery channels. Electricians and cooling technicians require practical training, safety competence and experience; IT operations and network roles require hardware, operating-system and fault-diagnosis capability. The selected National Careers Service profiles in `skills-reference.csv` provide traceable qualitative skill tags. The tags are editorial mappings of official role descriptions, with no invented score, validation label or transition probability. They cover selected decision-relevant roles, not every occupation in Table 4.

The industry file reports 2022 compensation per FTE derived from official compensation and employment coefficients. It is an industry labor-cost benchmark, not an occupational salary: compensation includes employer contributions and employment includes self-employment. Sector differences and future wage pressure must not be inferred from this ratio alone.

Separately, Scottish Government analysis of the ONS Annual Survey of Hours and Earnings reports median gross weekly pay of £773.80 for full-time employee jobs in April 2025 (provisional). The observation is reproduced from supporting Table 1.1.1 in `data/processed/regional-wages.csv`. It is an all-occupation wage context, not a salary estimate for these roles. Its 2025 nominal price basis is kept separate from the model's 2022 compensation assumptions; no direct wage-premium comparison or automatic deflation is made. [Official wage source](https://www.gov.scot/publications/annual-survey-of-hours-and-earnings-2025/pages/employee-earnings/).

## 5. Supply and recruitment evidence

SDS records an existing Scottish training pipeline in Table 5. Its achievements, starts and in-training counts concern different cohorts. Learners and achievers are generally already employed and are not a pool of available recruits. Frameworks map to multiple jobs; occupation demand measured in FTE cannot be subtracted from framework achievements measured in people to create a shortage. The sources do not identify provider spare places, willing applicants, competing projects or site-level labor mobility.

### Table 5. Selected Scottish Modern Apprenticeship channels, 2025/26

'''+markdown_table(supply_data(),["framework","starts","in_training","achievements","achievement_rate"])+'''
Notes: Source: SDS table 2.1, totals across gender. An unavailable cell remains missing. The achievement rate is achievements divided by leavers during the financial year, not starts during that year and not a longitudinal cohort probability. The underlying workbook was amended on 15 October 2026 for disclosure control in Table 2.1.

The Scottish Employer Skills Survey 2024 reports 20,000 skill-shortage vacancies and a 27% skill-shortage share of all vacancies. For skilled trades, the share is 60%. This measures employers' reported recruitment difficulty in 2024 and provides a reason to investigate trade-specific constraints; it does not estimate the unfilled positions caused by the proposed project. Among followed-up skill-shortage vacancies, 65% involved missing specialist knowledge and 43% complex problem-solving skills; these categories overlap. Training should therefore combine practical specialist capability with fault diagnosis and supervised work experience.

## 6. Policy options and delivery

### Table 6. Independent option scenarios, ready by operating launch

'''+markdown_table(pol,["option","cost_gbp","months_to_ready","expected_project_matches","on_time_matches_capped","cost_per_on_time_match_gbp"],["Option","Scenario cost GBP","Months to readiness","Expected matches","On-time matches","GBP/on-time match"])+f'''
Notes: Seats, unit costs, project match rates and readiness periods are scenario assumptions. The electrical option's completion input uses the published SDS achievement/leaver ratio as a planning proxy. Each option targets the assumed on-site role demand and is capped at that demand. Options are alternatives and cannot be summed without resolving overlapping target roles. Matches are not net additional jobs or measured treatment effects. A missing cost per match means zero on-time matches, not zero cost.

{recommendation} The 80-seat electrical apprenticeship cohort costs an assumed £1.44m and takes 48 months; it {ap_timing} the current {r['scenario']['construction_years']*12}-month launch deadline, with {pol[1]['on_time_matches_capped']:,.1f} on-time matches after the role cap. Wider regional and later-expansion benefits are outside this calculation. These options support workforce readiness; they do not establish that public subsidy is warranted.

## 7. Sensitivity and uncertainty

### Table 7. One-change scenario comparisons

'''+markdown_table(sen,["scenario","construction_job_years","construction_annual_fte","operating_annual_fte","construction_gva_gbp_m","annual_electricity_bill_gbp_m"],["Scenario","Build FTE job-years","Build annual FTE","Operate annual FTE","Build GVA GBP m","Annual power bill GBP m"])+'''
Notes: Each row changes the named input from the base case. The composition variant shifts 10 percentage points from computers to construction. Additional supplier leakage retains 80% of purchases otherwise made in Scotland at every round, on top of the official domestic import structure. It is an adverse purchasing scenario, not another geographic calibration. These are conditional ranges, not statistical confidence intervals; input uncertainty is not assigned a probability distribution.

Fixed 2022 technology, prices and labor productivity may change before a future project is delivered. The model assumes spare productive capacity, fixed proportions, no price response and no crowding out. It captures Scottish supply chains across the whole region, not a municipal catchment. A large investment can strain capacity and displace activity; neither effect can be quantified from these tables alone.

## 8. Appraisal gate and monitoring

Before a final investment or subsidy decision, obtain an independently reviewed bill of quantities, local-production evidence, construction schedule, shift roster and occupational job descriptions. Verify grid connection and power quality, water availability, embodied and operational carbon, alternative land use, infrastructure costs, public incentives and tax receipts. A net welfare appraisal needs an explicit counterfactual, additionality, displacement, opportunity costs, discounting and distributional analysis. Turnover and GVA cannot substitute for that appraisal.

Record tender-level supplier location and domestic content, monthly contractor FTE/hours, on-site hires and retention, training starts/completions and the destinations of trainees. Keep unique people separate from FTE and cumulative work volume. Compare realized procurement and staffing with this scenario after each stage; replace assumptions only with documented observations.

## Reproduction and sources

Run `impact-assessment run --output outputs` for all calculation tables and this report. `python scripts/prepare_data.py` reconstructs coefficients from the included official source files. The source inventory in `data/source-manifest.json` records URLs, vintages, geography, units, retrieval dates and file sizes. `docs/methodology.md` specifies equations, orientation, price and effect boundaries. The workflow needs no paid API, proprietary multiplier or sibling project. No statistical significance tests are attached to deterministic scenario calculations.
'''


def export_case(output, scenario=None):
    path=Path(output);path.mkdir(parents=True,exist_ok=True)
    d=load_data();r=run_case(scenario,d);sen=sensitivities(r["scenario"],d);pol=policy_options(r)
    r["policy_options"]=pol
    (path/"results.json").write_text(json.dumps(r,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    write_csv(path/"occupations.csv",r["occupations"])
    occ={row["soc2020"]:row for row in r["occupations"]}
    skills=[]
    for ref in skills_data():
        row=occ[ref["soc2020"]]
        skills.append({"soc2020":ref["soc2020"],"occupation":row["label"],"skill_tags_editorial":ref["skill_tags_editorial"],
            "construction_job_years_in_linked_occupation":row["construction_job_years"],
            "operating_fte_in_linked_occupation":row["operating_total_fte"],
            "mapping_type":ref["mapping_type"],"skill_taxonomy":ref["taxonomy"],"source_url":ref["source_url"],
            "status":"editorial_reference_linked_to_scenario_occupation_estimate"})
    write_csv(path/"occupation_skills.csv",skills)
    write_csv(path/"sensitivities.csv",sen);write_csv(path/"policy_options.csv",pol);write_csv(path/"schedule.csv",r["schedule"])
    industry=[]
    for i,code in enumerate(d["codes"]):
        industry.append({"sic2007_io":code,"industry":d["labels"][i],"construction_direct_output_gbp_m":r["construction"]["direct_output"][i],
            "construction_indirect_output_gbp_m":r["construction"]["indirect_output"][i],
            "construction_job_years":r["construction"]["total_output"][i]*d["employment"][i],
            "operating_supplier_output_gbp_m":r["operations"]["total_output"][i],
            "operating_supplier_fte":r["operations"]["total_output"][i]*d["employment"][i],
            "status":"scenario_model_estimate","source_id":"sg_io_2022","price_year":2022})
    write_csv(path/"industries.csv",industry)
    (path/"executive-brief.md").write_text(executive_brief(r),encoding="utf-8")
    (path/"economic-impact-report.md").write_text(full_report(r,d,industry,sen,pol),encoding="utf-8")
    return r
