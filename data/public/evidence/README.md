# Project and local labour evidence snapshot

Snapshot: 16 November 2026. Structured factual records, not copied corporate articles.

| File | Coverage | Source and interpretation |
| --- | --- | --- |
| `project-claim-ledger.json` | 11 scoped claim records, three primary owners | DataVita, National Wealth Fund and UK Government disclosures; financing, guarantee, announcements and unavailable roster/capex remain distinct statuses |
| `nomis-table-snapshot.json` | Selected native official table cells | Nomis North Lanarkshire profile S12000050, including table captions and suppressed `#` values |
| `local-labour-observations.csv` | 39 selected observations | APS resident employment by occupation, BRES workplace employee jobs and ASHE resident/workplace pay; source-native values, periods and units retained |

The original full local HTML was acquired from the [official Nomis profile](https://www.nomisweb.co.uk/reports/lmp/lad/1778385246/report.aspx). Only the selected factual table snapshot is redistributed. `scripts/prepare_project_evidence.py` rebuilds from the original acquisition if available, otherwise from the frozen table snapshot, without network access. Project records are short manually scoped factual attributions with source URLs and locators; the script freezes them without requiring private materials or copying full articles.

Original acquired pages stay under ignored `data/raw/`. No file hashes are generated. Paths, snapshot labels, record counts, native cells and source metadata provide the provenance trail. Crown copyright/ONS/Nomis data attribution and Open Government Licence terms apply to official statistical content; project announcements remain attributed to their owners. Code is MIT licensed separately.

APS July 2025–June 2026 occupation counts are survey estimates of residents, not recruits. BRES 2024 counts are workplace employee jobs, excluding self-employment and other categories in the source definition. Rounded full-time and part-time counts need not add exactly to the published total. ASHE 2025 pay is nominal and distinguishes residence from workplace. APS suppressed unemployment is null; model-based unemployment is a separate estimate and is never substituted into the suppressed field.
