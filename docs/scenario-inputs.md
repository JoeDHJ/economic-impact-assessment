# Scenario inputs

Generate an editable complete file with `impact-assessment scenario --output scenario.json`. Run it with `impact-assessment run --scenario scenario.json --output my-results`. Missing and unknown fields, nonfinite values and inconsistent classifications/prices are rejected. Zero amounts are allowed where economically meaningful; zero is distinct from missing. Construction and operating durations must be positive whole years. A complete working file is bundled in `src/impact_assessment/data/scenario.json`.

| Field | Unit / interpretation | Validation |
| --- | --- | --- |
| `schema_version`, `geography`, `currency`, `price_year` | portfolio.v1, Scotland, GBP, 2022 basic prices | Must match the bundled model |
| `name` | Descriptive scenario label | Nonempty text |
| `capital_gbp_m` | Total capital final demand before Scottish capture, GBP m | 0–100,000 |
| `construction_years`, `operating_years` | Even-spend build duration; number of repeated annual operating years | Whole years 1–100 |
| `capital_components` | Industry, share of total capital, Scottish production capture | Known SIC IO codes, no duplicate codes, shares sum to 1, captures 0–1 |
| `operating_procurement` | Industry, `gbp_m` per year before capture, capture | Known codes, no duplicates; electricity 35.1 cannot be entered twice |
| `it_load_mw`, `load_factor`, `pue` | IT nameplate power, utilization and total/IT power | MW ≥0, load 0–1, PUE 1–3 |
| `electricity_gbp_per_mwh` | Contract electricity cost in 2022 price terms | ≥0; changes the bill only |
| `electricity_io_valuation_gbp_per_mwh` | Fixed 2022-price scenario valuation of physical electricity for IO final demand | ≥0; changes valuation calibration, not an observed tariff |
| `electricity_capture` | Scottish production share of physical electricity procurement | 0–1 |
| `onsite_fte` | Direct on-site FTE, excluding outsourced employees | ≥0; independent of the capital budget |
| `onsite_compensation_gbp` | Annual 2022-price compensation per on-site FTE | ≥0; includes employer cost as a scenario |
| `onsite_roles` | SOC2020 string code and share of on-site FTE | Known codes, no duplicates, shares sum to 1 |
| `resident_share` | Assumed fraction of place-of-work FTE held by Scottish residents | 0–1; no change to domestic output |
| `supplier_retention` | Extra retention of purchases otherwise made in Scotland | 0–1; base 1, since source A is already domestic |

All project inputs have scenario status. Changing the geography or price year requires another calibrated data snapshot; relabeling these fields is not an accepted conversion. Negative demand shocks are outside this investment tool's supported schema. A closure/economic-contraction study would need different interpretation and validation.
