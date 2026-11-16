# Implementation status

Version: 0.1.0 release candidate | 2026-11-16

## Keep / change / add
- Keep: independent repository, MIT license, original development brief.
- Change: replace placeholder README with decision-focused findings and reproducible workflow.
- Add: validated Leontief engine, public Scottish input-output case, occupation staffing adapter, labor-supply evidence, policy calculator, static interactive dashboard, CLI, tests, CI and release.

## Analytical design
Scotland is the assessment region because its official domestic 98-industry table explicitly separates imports from the rest of the UK and world. Money is in GBP million at 2022 basic prices; no future nominal budget is silently converted. Construction and ongoing operation remain separate. Employment units will follow the publisher definition. National occupation staffing shares will be transferred only as a documented proxy, with coverage reported. Household-induced effects are excluded from the Type I base model.

## Progress
- [x] Read common task brief and inspect clean initial repository.
- [x] Create codex/impact-assessment-v1 branch.
- [x] Retrieve Scottish Government 2022 official analytical workbook (850,062 bytes).
- [x] Ingestion and model implementation.
- [x] Complete public-data case, reports, industry/occupation/skill estimates, supply/policy assessment, management outline and demo script.
- [x] 46 local checks; desktop/mobile browser execution and JSON/CSV/Markdown exports; all 412 occupation rows agree with Python.
- [x] Two independent read-only reviews, fixes and targeted rechecks; no unresolved P0/P1 or material requirement gap.
- [x] Clean wheel installation outside checkout; source archive inclusion verified.
- [ ] Remote CI and publication.

## Access notes
BLS and ONS direct downloads returned HTTP 403 from this execution environment. Firecrawl connected account reported insufficient credits. Accessible official Scottish and UK education sources supplied all six included public files. Actual ASHE wage evidence was retrieved through the Scottish Government's own supporting workbook. No restricted data or private project inputs are used.

## Completed base case

- £1bn capital scenario at 2022 basic prices, £400m Scottish production capture.
- 3,981 FTE job-years of construction work, averaging 1,327 annual FTE over three years.
- £259.1m construction GVA; £614.0m gross output.
- 238 annual operating FTE = 120 scenario on-site FTE + 118 modeled supplier FTE.
- 98 official IO industries and 412 UK occupational staffing records; detailed Scottish staffing remains a proxy.
- Scottish apprenticeship achievements and reported recruitment constraints support sequencing recommendations; no local shortage is fabricated.
