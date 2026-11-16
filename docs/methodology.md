# Model, units and accounting boundaries

Version 0.1.0 · Scotland · 2022 basic prices · portfolio.v1

## Supply-chain calculation

The source is the Scottish Government's domestic industry-by-industry (IxI) table for 2022, published in December 2025. Its 98 rows are supplying industries and its 98 columns are buying industries. `Z[i,j]` is Scottish industry i's intermediate sale to industry j. With output `q[j]`, the technical coefficient is `A[i,j] = Z[i,j] / q[j]`. The model solves:

```text
x = A x + f
x = (I - A)^(-1) f
direct output = f
indirect output = x - f
employment = e' x
GVA = v' x
employee compensation = w' x
```

There is no matrix transpose in coefficient construction. Columns are divided by the buying industry's output. The official Leontief table stores each inverse element multiplied by 1,000; ingestion divides it by 1,000 before comparing every cell. Reconstructed maximum differences are 1.97e-7 for inverse coefficients and 1.03e-6 FTE per £m for published employment effects. Column accounts reconcile within 5.46e-12 £m.

Employment coefficients are recovered as Type I employment effect divided by the Type I employment multiplier. Both publisher measures include their respective direct denominator; taking this ratio recovers the direct FTE per £m of industry output. GVA and compensation coefficients divide the corresponding accounts rows by output. Zero-output tobacco has zero transactions; its coefficient column is zero, with an identity diagonal in the inverse. Compensation per FTE is unavailable where there is no employment.

The implementation rejects missing, negative and nonfinite technical coefficients and demand, non-square or mismatched dimensions, nonproductive matrices (spectral radius ≥1), and systems with condition number above 1e8. The real model's condition number is 2.02 and spectral radius is 0.348. These diagnostics establish numerical suitability, not causal validity or economic capacity.

## Hand-solvable orientation check

```text
A = [0.2  0.1]       f = [70]
    [0.4  0.2]           [20]

(I-A)^(-1) = (1/0.60) [0.8  0.1]
                          [0.4  0.8]

x = [290/3, 220/3] = [96.6667, 73.3333]
e = [2, 3] FTE per £m
direct FTE = 200; indirect FTE = 640/3; total FTE = 1240/3
```

Tests also transpose A deliberately and verify that the result changes. The multiplier total is never added to direct output or employment again.

## Prices and project final demand

All modeled monetary quantities are GBP million at 2022 basic prices. Capital is an explicitly assumed constant-price envelope, not a current announced project budget. The default ledger assigns mutually exclusive owner purchases to construction, computer/electronics manufacture, electrical equipment, and architectural/engineering services. Purchased equipment is excluded from the construction line. A live purchaser-price budget would require an explicit allocation of VAT, trade margins, transport and imports; this tool does not guess those allocations.

Initial Scottish final demand equals each production component times its scenario Scottish capture share. Capture concerns production, not the address of a reseller or contractor. Uncaptured project purchases are external leakage; they generate no Scottish first-round demand. The domestic A matrix already excludes rest-of-UK and rest-of-world imports. Imported intermediate requirements are calculated from the source import coefficients and modeled output, but are never added to domestic impacts. No final-demand subtraction is repeated at every round.

The optional `supplier_retention` parameter uniformly scales domestic intermediate coefficients. Its base value is 1. At 0.8, 20% of purchases otherwise made in Scotland leak externally at every supply-chain round: `x = (I - 0.8A)^(-1) f`. This is an adverse supplier-purchasing scenario; it does not estimate a subregional economy. Additional leakage is `(1-r) 1' A x`, on top of source import coefficients. At zero supplier retention, total domestic output equals f.

## Construction, operations and commuting

The full capital vector represents purchases over the entire build. Multiplying by annual FTE/output coefficients yields **FTE job-years**, or full-time work-volume equivalents across the build. Dividing by construction years gives an annual average FTE under even spending. Neither is a count of unique workers. Peak labor demand requires a month-by-month schedule.

Operations use a separate procurement vector for electricity, telecommunications, repair, security and building services. Its direct effects belong to first-tier suppliers; indirect effects belong to upstream suppliers. Assumed on-site FTE and compensation are added once, outside that procurement model. The centre's own output, GVA, profits, taxes and revenue remain unestimated. No sector-63 final-demand shock is applied, so on-site employees do not reappear inside a multiplied data-centre revenue number. Outsourced employees must stay out of the on-site staffing input.

Electricity volume equals IT MW × 8,760 × load factor × PUE. The IO vector values that physical volume at an explicitly assumed fixed 2022 benchmark (`electricity_io_valuation_gbp_per_mwh`, base £100/MWh). The contract-price input determines the bill. Changing only a contract price changes procurement cost and the price-only difference; it does not change physical generation or jobs. The benchmark is a scenario valuation, not an observed Scottish average tariff. A future nominal tariff must first be put on a consistent price basis. This distinction prevents a pure electricity price increase from being reported as more real employment.

The resident share allocates place-of-work FTE to residents as a scenario; it does not rescale output or supply chains. Commuting affects household-spending closure if such a closure is introduced. This release excludes household-induced effects altogether. Their exclusion is not a measured zero. Ten operating years in the schedule repeat annual activity and do not imply ten different annual workforces.

## Occupational and skill mapping

Skills England's 2025 supporting file provides UK worker counts for 412 SOC2020 occupations in 18 grouped industries. Only its 2025 rows are used. The official SIC-to-industry workbook maps every Scottish IO industry to a group using its two-digit SIC prefix; all subdivisions of one broad group share a staffing profile. Differences in commas and capitalization are reconciled through normalized exact labels, without fuzzy matching.

Each staffing weight is occupation workers in that industry group divided by all provided occupation workers in that group. Industry FTE × staffing weights yields occupational FTE. All 98 IO industries map and all 412 occupation records are preserved; numerical allocation coverage is 100%, while **geographic, industry-detail and FTE-pattern validity remain proxies**. UK headcount shares are not observed Scottish FTE shares. The framework allows unmatched groups to remain unallocated; it never silently redistributes missing demand. On-site occupation shares are independent scenario assumptions. SOC IDs remain strings; the original taxonomy and vintage are retained.

NCS profiles support selected qualitative skill tags. The role-to-SOC matches are editorial references, with related-role/subset mappings marked in `skills-reference.csv`; they are not an official crosswalk. NCS salary ranges are indicative England career guidance, not observed occupational wages or Scottish salary estimates. The Scottish industry data include official compensation-based labor-cost benchmarks. Compensation includes employer contributions and the FTE denominator includes self-employment, so the ratio is not a payroll wage.

## Supply, uncertainty and net appraisal

SDS framework achievements are annual administrative flows of people, many already employed. Starts, achievements and in-training stocks concern different cohorts. The published achievement/leaver ratio is used transparently as a policy planning proxy, not a cohort completion probability. No unobserved provider capacity or available labor pool is invented. ESS reports recruitment difficulty among surveyed employers; it cannot establish a site-specific vacancy gap. UK demand categories are not labor-shortage classifications.

Sensitivity rows vary named assumptions separately; they are not confidence intervals. Fixed coefficients assume no capacity constraint, substitution, price feedback or displacement. The results quantify gross associated activity. Net welfare and fiscal appraisal require a counterfactual, opportunity costs, externalities, public funding costs, discounting and additionality; none can be recovered by labeling gross output as a benefit.

Official definitions: [Scottish Government multipliers guide](https://www.gov.scot/publications/about-supply-use-input-output-tables/pages/user-guide-multipliers/), [Skills England release and methods](https://explore-education-statistics.service.gov.uk/find-statistics/occupations-in-demand/2025).
