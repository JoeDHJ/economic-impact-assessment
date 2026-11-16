# Implementation status

## Version 0.2.0 delivery

Branch: `codex/workforce-decision-v02`. Full implementation authorised 16 November 2026 for labour markets, personnel economics, AI economics and economic consulting.

- Added scoped DV1/DV3 primary-project claim ledger and 39 official North Lanarkshire observations with periods, populations, units and suppression.
- Added phased occupation demand, task-based technical coverage, integer workforce allocation and four programme options; separate regional, employer, public-programme and guarantee ledgers.
- Added local browser MILP workflow, complete input editing/import/save and current-scenario exports; preserved the original regional calculator at `impact.html`.
- Added methods/evaluation extension, capability/interview guide, owner rehearsal and decision presentation.
- 63 local tests and actual browser Python/WASM parity passed. Two reviewers completed both rounds; all five substantive findings were repaired and verified in `v0.2-review-record.md`.
- A clean environment installed the wheel with NumPy/SciPy and successfully ran validation, workforce comparison and site construction without an editable checkout. Remote CI and release steps are in progress. Prior version record follows unchanged.

Version: 0.1.0 | 2026-11-16

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
- [x] Remote CI and public dashboard publication; release package verification completed.

## Access notes
BLS and ONS direct downloads returned HTTP 403 from this execution environment. Firecrawl connected account reported insufficient credits. Accessible official Scottish and UK education sources supplied all six included public files. Actual ASHE wage evidence was retrieved through the Scottish Government's own supporting workbook. No restricted data or private project inputs are used.

## Completed base case

- £1bn capital scenario at 2022 basic prices, £400m Scottish production capture.
- 3,981 FTE job-years of construction work, averaging 1,327 annual FTE over three years.
- £259.1m construction GVA; £614.0m gross output.
- 238 annual operating FTE = 120 scenario on-site FTE + 118 modeled supplier FTE.
- 98 official IO industries and 412 UK occupational staffing records; detailed Scottish staffing remains a proxy.
- Scottish apprenticeship achievements and reported recruitment constraints support sequencing recommendations; no local shortage is fabricated.

## Publication record

- [Merged implementation PR](https://github.com/JoeDHJ/economic-impact-assessment/pull/1).
- [Main-branch CI: passed](https://github.com/JoeDHJ/economic-impact-assessment/actions/runs/43825140265), including 46 tests, source rebuilding, Chromium runtime and clean wheel installation outside checkout.
- [Dashboard deployment: passed](https://github.com/JoeDHJ/economic-impact-assessment/actions/runs/43825140364).
- [Live dashboard](https://joedhj.github.io/economic-impact-assessment/): HTTP 200 and actual browser execution verified the 3,981 construction FTE job-years, 238 operating annual FTE and observed wage context.
- [Version 0.1.0 release](https://github.com/JoeDHJ/economic-impact-assessment/releases/tag/v0.1.0): wheel, source archive and offline dashboard bundle.
