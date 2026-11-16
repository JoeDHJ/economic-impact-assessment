# portfolio.v1 analytical interface

This project is independent. It reads no live Atlas, Corporate or Career Fit service. The bundled public snapshot, CLI and dashboard reproduce the entire case without a sibling repository or API key.

`outputs/results.json` is the phase-level export. Its top-level fields include `schema_version`, `source_id`, `source_url`, `retrieved_at`, `source_vintage`, `geography`, `unit_of_observation`, `period`, `currency`, `price_year`, `status`, `model_version` and the complete `scenario`. The source inventory provides separate per-source metadata. Input fields are scenario values; public inputs retain source-native SIC2007 and SOC2020 identifiers.

The result contains `construction.job_years_fte` and `construction.annual_average_fte`, `operations.supplier_employment_fte` and `operations.onsite_fte`. These must not be collapsed into one undated jobs number. `occupations` rows use `soc2020` strings; a consumer should identify the taxonomy as UK SOC2020, not US SOC2018 or O*NET-SOC. An Atlas adapter must supply an explicit crosswalk before combining taxonomies.

`data/processed/industry_crosswalk.csv` records source two-digit SIC, target broad group, the weighting rule and mapping coverage. Staffing weights live in `model.json`, with one industry row and one SOC2020 occupation column. Within each group, weights are proportional to official UK worker counts. It is a many-to-one industry aggregation and a proxy transfer to detailed Scottish sectors, not a one-to-one detailed staffing crosswalk. Headcount-to-FTE composition is an assumption. Missing values stay null/unallocated rather than becoming zero.

`skills-reference.csv` uses the local qualitative taxonomy `case.qualitative-skills.v1`, with NCS source URLs and mapping type. It contains editorial tags and indicative advisory salary ranges, not skill scores or measured individual abilities. It is optional context and has no effect on the Leontief calculation. Potential future sibling snapshots must be versioned and frozen locally before inclusion; no silent source replacement is allowed.
