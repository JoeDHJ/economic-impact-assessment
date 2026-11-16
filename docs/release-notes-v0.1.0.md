# Economic Impact Assessment 0.1.0

An independently reproducible consulting case connects an AI data-centre investment scenario to Scottish suppliers, occupations, training evidence and policy readiness.

The £1bn scenario at 2022 basic prices purchases £400m of Scottish production. It supports 3,981 construction FTE job-years (1,327 annual average FTE over three years), £259.1m construction GVA and 238 annual operating FTE, including 120 assumed on-site FTE. These are conditional gross activity estimates, separate from net additional jobs, welfare and tax returns.

The release includes a reusable Python CLI, offline interactive dashboard, official 98-industry input-output accounts, 412 occupational allocations, actual Scottish apprenticeship and wage data, qualitative skills references, an executive brief, economic report, policy options, management presentation outline and two-minute demo. Original public inputs and provenance are included. No paid API or live sibling application is required.

The model separates construction and operations, cumulative work and annual staffing, domestic production capture and imports, and on-site employees and supplier jobs. Contract electricity price changes affect the bill without generating extra physical output or employment. The workforce assessment explains why training achievements are not an available labor pool and why a 48-month electrical cohort misses the base 36-month launch.

Validation: 46 tests; desktop/mobile Chromium execution; numerical parity for all 412 occupational rows; clean wheel installation outside the checkout; reconstruction against official published inverse and employment effects. Two independent read-only reviews have no unresolved P0/P1 or material requirement gaps after repairs.

Use the wheel for the CLI, the source archive for the original data and complete reconstruction, or unpack the dashboard ZIP and open `index.html` offline.

- [Live dashboard](https://joedhj.github.io/economic-impact-assessment/)
- [Full report](https://github.com/JoeDHJ/economic-impact-assessment/blob/main/outputs/economic-impact-report.md)
- [Executive brief](https://github.com/JoeDHJ/economic-impact-assessment/blob/main/outputs/executive-brief.md)
- [Implementation review and merge](https://github.com/JoeDHJ/economic-impact-assessment/pull/1)
- [Passed main CI](https://github.com/JoeDHJ/economic-impact-assessment/actions/runs/43825140265)

Geographic staffing transfer, fixed technology and scenario procurement remain material assumptions. Actual site-level applicants, provider spare capacity, project costs and a welfare counterfactual are not observed. Python 3.11+; MIT code license, source-attributed public data under their original terms.
