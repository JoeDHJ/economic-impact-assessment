"""Freeze selected official local observations and a scoped project claim ledger.

Original pages stay in the ignored acquisition directory. Public snapshots contain
factual table cells and short, attributed claim records, not copied articles.
"""
from pathlib import Path
import csv
import json
import re
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "src/impact_assessment/data"
PUBLIC = ROOT / "data/public/evidence"
PUBLIC.mkdir(parents=True, exist_ok=True)

NOMIS = "https://www.nomisweb.co.uk/reports/lmp/lad/1778385246/report.aspx"
VITA = "https://blog.datavita.co.uk/blog/datavita-secures-funding-data-centre-expansion"
NWF = "https://umbraco-prod.nationalwealthfund.org.uk/news-and-publications/news/datavita-secures-300-million-for-data-centre-rollout-in-scotland-s-ai-growth-zone-with-backing-from-national-wealth-fund-and-major-lenders/"
GOV = "https://www.gov.uk/government/news/lanarkshire-ai-growth-zone-secures-300-million-investment-as-dell-establishes-scottish-base"


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf8")


def freeze():
    raw=ROOT/"data/raw/nomis_north_lanarkshire.html"
    tables={}
    if raw.is_file():
        soup = BeautifulSoup(raw.read_bytes(), "html.parser")
        for table in soup.find_all("table"):
            caption = table.find("caption")
            if caption:
                title = caption.get_text(" ", strip=True)
                tables[title] = [[c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"], recursive=False)] for tr in table.find_all("tr")]
    else:
        tables=json.loads((PUBLIC/"nomis-table-snapshot.json").read_text(encoding="utf8"))["tables"]
    selected = {k:v for k,v in tables.items() if any(k.startswith(t) for t in ["Employment by occupation", "Employee jobs", "Earnings by place", "Employment and unemployment", "Model-based unemployment"])}
    snapshot = {"source_id":"nomis_north_lanarkshire_20261116", "source_url":NOMIS,
        "retrieved_at":"2026-11-16", "geography":"North Lanarkshire", "geography_id":"S12000050",
        "schema_version":"portfolio.v1", "status":"official_table_snapshot", "tables":selected,
        "license":"Crown copyright; ONS/Nomis Open Government Licence attribution retained"}
    dump(PUBLIC/"nomis-table-snapshot.json", snapshot)
    observations = []

    def add(metric, value, native, unit, period, population, source, taxonomy=None):
        observations.append({"metric":metric,"value":value,"source_native_value":native,"unit":unit,"period":period,
            "geography":"North Lanarkshire","population":population,"taxonomy":taxonomy,
            "source":source,"source_id":snapshot["source_id"],"source_url":NOMIS,"retrieved_at":"2026-11-16",
            "status":"suppressed" if value is None else "official_estimate",
            "availability_interpretation":"Context only; not people available to this project"})

    def num(text):
        try:return float(text.replace(",", ""))
        except ValueError:return None

    for caption, rows in selected.items():
        period = re.search(r"\(([^)]+)\)", caption).group(1)
        if caption.startswith("Employment by occupation"):
            for row in rows:
                if row and re.match(r"^[1-9] ", row[0]):
                    add(row[0],num(row[1]),row[1],"resident employed people",period,"Residents aged 16+ in employment","ONS Annual Population Survey","SOC2020 major group")
        elif caption.startswith("Employee jobs"):
            for row in rows:
                if row and (row[0] in ["Total employee jobs","Full-time","Part-time"] or re.match(r"^[B-S] :",row[0])):
                    add(row[0],num(row[1]),row[1],"workplace employee jobs",period,"Employee jobs excluding farm agriculture, self-employment, HM Forces and government-supported trainees","ONS BRES open access","SIC2007 section")
        elif caption.startswith("Earnings by place"):
            basis="residence" if "residence" in caption else "workplace"
            pay="weekly"
            for row in rows:
                if row and "Hourly pay" in row[0]:pay="hourly excluding overtime"
                if row and row[0]=="Full-time workers":
                    add(f"Median full-time gross pay ({basis}, {pay})",num(row[1]),row[1],"nominal GBP/week" if pay=="weekly" else "nominal GBP/hour",period,f"Full-time employee jobs; {basis} basis","ONS ASHE")
        elif caption.startswith("Model-based unemployment"):
            for row in rows:
                if row and row[0].startswith("Unemployed (model-based)"):
                    add("Unemployment (model-based)",num(row[1]),row[1],"people",period,"Economically active residents aged 16+; model-based estimate","ONS model-based unemployment")
        else:
            for row in rows:
                if row and row[0]=="Males":break
                if row and row[0] in ["In employment†","Employees†","Self employed†","Unemployed§"]:
                    add(row[0],num(row[1]),row[1],"resident people",period,"Residents aged 16+; APS count","ONS Annual Population Survey")
    if len(observations)<30:raise ValueError("Nomis snapshot layout changed")
    dump(DEST/"local-evidence.json",observations)
    with (PUBLIC/"local-labour-observations.csv").open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=list(observations[0]));w.writeheader();w.writerows(observations)

    facts=[]
    def fact(id,label,value,unit,status,scope,source,locator,interpretation):
        facts.append({"claim_id":id,"label":label,"value":value,"unit":unit,"status":status,"scope":scope,
            "source_id":"nwf_datavita_20260818" if source==NWF else "datavita_funding_20260818" if source==VITA else "ukgov_lanarkshire_20260818",
            "source_url":source,"source_locator":locator,"retrieved_at":"2026-11-16","publication_date":"2026-08-18",
            "interpretation":interpretation})
    fact("P01","Debt facility",300,"nominal GBP million, approximately","disclosed_financing","DV1 expansion and DV3 new-build",NWF,"financing transaction","Financing is not a disclosed bill of quantities or 2022-price capex.")
    fact("P02","NWF guarantee face value",202,"nominal GBP million","disclosed_guarantee","Covered lending tranche",NWF,"guarantee structure","Face exposure is not immediate expenditure or expected fiscal loss.")
    fact("P03","Covered lenders' tranche",252.5,"nominal GBP million","disclosed_financing","ING, ABN AMRO, Santander tranche",NWF,"guarantee structure","SNIB and Siemens financing sit outside this guarantee.")
    fact("P04","Guarantee fraction of covered tranche",.8,"fraction","disclosed_guarantee","Covered tranche, not entire facility",NWF,"guarantee structure","202/252.5 = 80%; 202/300 is a different denominator.")
    fact("P05","Construction jobs announcement",600,"jobs, approximately; duration/FTE basis unspecified","announced_project_projection","DV1 and DV3",VITA,"project employment paragraph","Not observed hires, unique workers or FTE job-years; do not calibrate the IO model to reproduce it.")
    fact("P06","Permanent skilled roles announcement",100,"roles, approximately; FTE basis unspecified","announced_project_projection","DV1 and DV3",VITA,"project employment paragraph","A forward-looking announcement; not a verified payroll or task-based roster.")
    fact("P07","CoreWeave capacity agreement",15,"years","disclosed_contract","Both facilities",VITA,"facility and lease paragraph","AI infrastructure demand evidence; contract length is not the disclosed guarantee tenor or proof of operating utilisation.")
    fact("P08","Facilities in financed package","DV1 expansion; DV3 new-build","facility identifiers","disclosed_project_scope","Chapelhall, North Lanarkshire",VITA,"facility and lease paragraph","DV2 is a separate Glasgow facility. DV4 and the wider growth zone are outside this package.")
    fact("P09","Wider growth-zone jobs announcement",3400,"jobs, more than","announced_area_projection","Wider Lanarkshire AI Growth Zone",GOV,"wider development","Not the job count attributable to the financed DV1/DV3 package.")
    fact("P10","Publicly itemised project capex",None,"GBP and price year unavailable","not_disclosed_in_selected_sources","DV1/DV3 selected public sources",VITA,"disclosure coverage","Conditional model capital is an independent analytical input, not a conversion of the financing facility.")
    fact("P11","Verified detailed operating roster",None,"occupation FTE unavailable","not_disclosed_in_selected_sources","DV1/DV3 selected public sources",VITA,"disclosure coverage","Task/shift staffing in this assessment is a scenario, not an employer workforce observation.")
    dossier={"schema_version":"portfolio.v1","case_id":"datavita-dv1-dv3-public-evidence-v1",
        "title":"DataVita DV1 / DV3: public project evidence and conditional workforce assessment",
        "geography":"North Lanarkshire, Scotland","retrieved_at":"2026-11-16","facts":facts,
        "scope_note":"Independent public-data work sample. No client engagement, access to internal personnel data or verification of forecast employment is claimed.",
        "sources":[{"source_id":"nwf_datavita_20260818","url":NWF,"owner":"National Wealth Fund","publication_date":"2026-08-18"},
            {"source_id":"datavita_funding_20260818","url":VITA,"owner":"DataVita","publication_date":"2026-08-18"},
            {"source_id":"ukgov_lanarkshire_20260818","url":GOV,"owner":"UK Government","publication_date":"2026-08-18"}],
        "unknowns":["Itemised basic-price capital expenditure","Actual occupation and shift roster","Provider spare seats","Available qualified applicants","Independent realised employment","Guarantee tenor, fees and default/loss evidence"]}
    dump(PUBLIC/"project-claim-ledger.json",dossier);dump(DEST/"project-evidence.json",dossier)
    print("Frozen",len(facts),"project claims and",len(observations),"official local observations")


if __name__=="__main__":freeze()
