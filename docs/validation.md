# Validation and independent review

Candidate version: 0.1.0. This file records checks actually executed; publication results are added after the remote workflow completes.

## Calculation and public-data checks

- Two-industry hand solution verifies orientation, direct/indirect decomposition and no double counting.
- Full 98-industry reconstruction verifies the publisher's Type I inverse and employment effects and reconciles column accounts.
- Investment scenarios test timing, geography/price compatibility, zero amounts, invalid/missing/negative/nonfinite values, duplicate/unknown industry and occupation IDs, singular/unstable systems and extra leakage.
- Occupational allocations reconcile with industry FTE; current data map all 98 industries and retain all 412 occupation records. Coverage does not validate the transferred UK staffing assumption.
- Policy checks cover readiness deadlines, demand caps and missing cost-per-match denominators.
- Pure electricity contract-price changes alter bills without creating a physical-output/employment change.

## Actual browser execution

`python scripts/browser_check.py --channel msedge --screenshots` passed in installed Microsoft Edge/Chromium. Checks use 1440×1050 desktop and 390×844 mobile viewports. All four views, controls, reset and JSON/CSV/Markdown downloads execute. Base and modified scenarios match Python totals; all 412 occupation rows match. No browser page errors were recorded. Mobile views have no page-level horizontal overflow; wide tables scroll within their module. Original-size screenshots are saved in `docs/screenshots/`.

## Independent review

Two independent read-only reviewers covered requirements, analytical logic, boundary cases, code quality, tests and actual execution. Findings and repairs:

| Finding | Repair and regression evidence |
| --- | --- |
| Explicit JSON `null` silently ran the default investment | Reject explicit non-object files; null/list/empty-object regression cases fail without output. |
| Positive demand in zero-source-output tobacco sector produced unsupported zero jobs/GVA | Reject positive Scottish demand to uncalibrated source sectors; zero-capture external procurement remains supported. |
| Custom reports retained base policy recommendations and timing | Generate advice from current on-site demand and deadline; zero-staff and five-year launch cases verified. |
| Numeric text and floating duration passed validation then failed calculation | Require numeric scalars and integer duration types. |
| Valid maximum capital failed automatic sensitivity export | Mark the out-of-domain +25% row explicitly unavailable; base calculation exports normally. |
| Zero-employment compensation ratio became a false zero | Store null/CSV missing for undefined ratios. |
| Early source archive omitted original data and rebuild script | Added explicit source-distribution inclusion manifest; final archive is checked before publication. |

Both reviewers rechecked affected paths and reported no unresolved P0/P1 or material requirement gaps. The methods reviewer independently confirmed the original ASHE workbook's £773.80 provisional nominal weekly median for Scottish full-time employee jobs. The complete local suite passes **46 tests**. These checks establish computational and reporting consistency within the scenario, not causal validity or observed project success.

## Installation and CI

The built wheel was installed into a clean local environment and executed from a separate working directory. Imports resolved to that environment's `site-packages`; validation, case export and dashboard build passed with only NumPy as an external runtime dependency. The rebuilt source archive includes original official inputs, the coefficient rebuild script, documentation and reports; local acquisition records are excluded. The remote workflow repeats installation outside the checkout. Remote run and release links will be recorded when available. The public sources are bundled, so network data refresh is not part of the core runtime or CI.
