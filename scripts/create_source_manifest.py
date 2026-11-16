"""Record source identity and ordinary file metadata; no digests."""
from pathlib import Path
import json
import csv

ROOT=Path(__file__).resolve().parents[1]
base="https://content.explore-education-statistics.service.gov.uk/api/releases/b20e696c-8f0a-4dcc-a1e2-3cb4b963ab80/files/"
entries=[
    ("sg_io_2022","SUT-2022.xlsx","Scottish Government","https://www.gov.scot/binaries/content/documents/govscot/publications/statistics/2019/08/input-output-latest/documents/all-tables-latest-year/all-tables-latest-year/govscot%3Adocument/SUT-2022.xlsx","2022; release 10 December 2025","Scotland","SIC2007 industry × industry","GBP million, basic prices; FTE effects",2022,98),
    ("skills_england_staffing_2025","staffing.csv","Skills England",base+"3a1245a3-04f8-45b5-8cf5-899ab8a50a3c","2025 release; 2024 and 2025 records","United Kingdom","SOC2020 occupation × broad SIC industry","workers (headcount); official rounded estimates",None,14832),
    ("skills_england_demand_2025","occupation_demand.csv","Skills England",base+"a8afa497-df8d-4407-905f-f2af7179f2fb","2025 release","United Kingdom; ASHE components Great Britain","SOC2020 occupation","workers; demand index/category",None,368),
    ("skills_england_sic_map","sic_map.xlsx","Skills England",base+"16ccc5c4-f07d-4e06-a696-ee418bce9662","2025 release","United Kingdom","SIC2007 two-digit industry","classification lookup",None,88),
    ("sds_ma_2025_26","apprenticeships-2025-26.xlsx","Skills Development Scotland","https://www.skillsdevelopmentscotland.co.uk/media/josfrdus/modern-apprenticeship-supplementary-tables-quarter-4-2025-26.xlsx","2025/26 Q4; published 26 May 2026; amended 15 October 2026","Scotland","framework × gender","people/starts/achievements; achievement-leaver ratio",None,None),
    ("sg_ashe_2025","ASHE-2025.xlsx","Scottish Government analysis of ONS ASHE","https://www.gov.scot/binaries/content/documents/govscot/publications/statistics/2025/10/annual-survey-of-hours-and-earnings-2025/documents/annual-survey-of-hours-and-earnings-2025---supporting-tables/annual-survey-of-hours-and-earnings-2025---supporting-tables/govscot%3Adocument/Annual%2BSurvey%2Bof%2BHours%2Band%2BEarnings%2B2025%2B-%2BTables%2B-%2B07%2BOctober%2B2026.xlsx","2025 provisional; workbook updated 7 October 2026","Scotland","full-time employee jobs, all sexes","GBP per week; median gross earnings, nominal",2025,None),
]
sources=[]
for sid,name,owner,url,vintage,geo,unitobs,unit,priceyear,rows in entries:
    path=ROOT/"data/public/sources"/name
    sources.append({"source_id":sid,"source":owner,"source_url":url,"retrieved_at":"2026-11-16","accessed_date":"2026-11-16","source_vintage":vintage,
        "geography":geo,"unit_of_observation":unitobs,"period":vintage.split(';')[0],"unit":unit,"currency":"GBP" if priceyear else None,"price_year":priceyear,
        "schema_version":"portfolio.v1","status":"official_estimate_or_administrative_observation","path":str(path.relative_to(ROOT)).replace('\\','/'),"file_bytes":path.stat().st_size,"row_count":rows,
        "license":"Open Government Licence v3.0; source attribution retained"})
manifest={"schema_version":"portfolio.v1","snapshot":"2026-11-16-public-case-v1","sources":sources,
    "qualitative_sources":[{"source_id":"sg_ess_2024","source_url":"https://www.gov.scot/publications/employer-skills-survey-2024-scotland/pages/skill-shortage-vacancies/","source_vintage":"2024 survey; corrected January 2026","geography":"Scotland","retrieved_at":"2026-11-16","status":"official_survey_estimate","coverage":"5,080 employer sites; vacancy follow-ups have smaller bases"}],
    "missing_data":["site-level vacancies/applicant availability","training-provider spare capacity","actual project budget/staffing","counterfactual displacement/welfare/fiscal inputs"],
    "treatment":"Only 2025 staffing records used (7,416 rows); publisher punctuation differences matched by normalized exact labels. No statistical imputation or fuzzy occupation matching."}
text=json.dumps(manifest,indent=2,ensure_ascii=False)+"\n"
(ROOT/"data/source-manifest.json").write_text(text,encoding="utf8")
(ROOT/"src/impact_assessment/data/source-manifest.json").write_text(text,encoding="utf8")
profiles=[
    ("5241","electrician","Electrical systems; inspection and fault diagnosis; practical safety",26000,45000,"direct role reference"),
    ("2137","network-engineer","Network setup; system diagnosis; information security",25500,52000,"direct role reference"),
    ("3131","it-support-technician","Hardware diagnosis; operating systems; user support",24000,36000,"related role proxy; SOC3131 operations is broader/different from user support"),
    ("5225","refrigeration-and-air-conditioning-installer","Cooling-system installation; maintenance; practical engineering",25000,45000,"direct role reference"),
    ("2135","cyber-intelligence-officer","Threat analysis; security investigation; technical communication",32000,65000,"specialist subset of broader cyber-security occupation"),
    ("1251","facilities-manager","Building maintenance; supplier coordination; operational planning",26000,50000,"editorial related-role mapping; facilities roles may span management SOC codes"),
]
fields=["soc2020","ncs_profile","skill_tags_editorial","indicative_starter_salary_gbp","indicative_experienced_salary_gbp","mapping_type","source_url","source_id","accessed_date","taxonomy","status","geography","price_year"]
skills=[]
for soc,profile,tags,low,high,mapping in profiles:
    skills.append(dict(zip(fields,[soc,profile,tags,low,high,mapping,"https://nationalcareers.service.gov.uk/job-profiles/"+profile,"ncs_"+profile,"2026-11-16","case.qualitative-skills.v1","editorial_tags_from_official_career_guidance; salary_ranges_are_indicative_not_observed_wages","England career guidance",None])))
with (ROOT/"data/processed/skills-reference.csv").open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(skills)
(ROOT/"src/impact_assessment/data/skills.json").write_text(json.dumps(skills,indent=2)+"\n",encoding="utf8")
print("Recorded",len(sources),"source files and",len(profiles),"qualitative skill references")
