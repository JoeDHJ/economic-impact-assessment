# AI investment and workforce allocation: methods

Model 0.2.0 · Independent portfolio case by Haojian Dui · 16 November 2026.

## Decision, evidence and baseline

The question is which combination of qualified-worker conversion, external hiring, apprenticeships and specialist contracts can supply the specified service capacity by its deadline, within transition budgets and delivery constraints. This is an implementable conditional planning model. It does not estimate the treatment effect of an investment or a training programme.

The public case is DataVita's DV1 expansion and DV3 new-build. The approximately £300m facility, £202m guarantee and announced employment projections have their own claim records. The £250m 2022-basic-price capital envelope, 36-month construction schedule, technical operating roster, wages, applicant/route limits and all programme yields are separate assumptions. No financing-to-capex conversion is implied. Actual North Lanarkshire labour observations are context, with source, geography, population, units, period and missingness retained.

The no-programme comparator commissions no capacity through these four modeled pathways. It is not an assertion that the employer currently has no staff. Existing workers enter only through assumed eligible redeployment places. A real engagement would first record incumbent service coverage, subtract it from incremental requirements and avoid paying again for baseline staff. The current default takes every modeled target as a programme requirement.

## Regional demand and phases

Let A be the 98-industry Scottish domestic technical-coefficient matrix, r the extra supplier-retention scenario and f_m the Scottish final-demand vector for month m. Then:

`x_m = (I − rA)^−1 f_m`

`industry annualised FTE_m = 12 × diag(e) x_m`

Here spending is in £m at 2022 basic prices and e is FTE per £m output. Capital shares, first-round Scottish capture and four component-specific phase weights determine f_m. The four phases occupy 0–1/6, 1/6–1/2, 1/2–5/6 and 5/6–1 of the construction period. Their boundaries are whole months for the permitted whole-year durations. Monthly FTE divided by 12 gives work during that month in FTE job-years; summing reconciles to the original capital model.

UK grouped-industry SOC2020 staffing shares proxy the occupational composition of Scottish work. Selected construction-industry SOC shares receive declared phase factors and are then renormalised within that industry and phase. This preserves total work but changes occupational timing. It is not an employer observation or a national-to-local estimate of headcount. Supplier work can occur outside North Lanarkshire. Imported procurement is excluded from Scottish production demand. Household-induced effects and general-equilibrium price/wage responses are absent.

For selected construction occupations, the programme target is a scenario share of the Scottish occupational peak. Its readiness deadline is the start of the peak phase; its engagement lasts that phase. This is a workforce-development target, not the site's full construction staffing requirement. The model does not ensure coverage of construction demand in every phase. All monthly occupation demands are exported so this simplification is visible.

## Tasks and service capacity

For role o, `required FTE_o = annual coverage hours_o / productive hours per FTE`.

Continuous posts use 8,760 hours each; daytime posts use weekly hours × 52. Default paid hours are 1,950, of which 300 are leave, training or other time unavailable for coverage. A routine-workload factor changes only the two identified IT roles. It represents a task-demand scenario, not an estimated AI productivity elasticity. The resulting 85.58 service FTE includes capacities that may ultimately be contracted. It is neither an observed employee roster nor a claim that exactly 85.58 people can operate a safe shift system. Shift sequencing, skill redundancy, leave correlation, statutory constraints and reliability under simultaneous absences require a separate operational roster design.

Security, cleaning and vendor equipment services are excluded from the task roster. The workspace keeps on-site employment at zero in its IO operating scenario, reporting supplier activity separately. Changing the programme's employee/contractor mix does not automatically create new IO procurement. Original v0.1 assumptions remain independently available in the regional calculator.

## Integer programme allocation

For target i and pathway p, choose integer cohort places z_ip. A place has lead L_p, success/matching rate q_p, annual attrition a_p, capacity ceiling, transition cost and mentor requirement. The default success and attrition rates are uncalibrated assumptions shared across roles. Places on a pathway finishing after the target's readiness deadline have upper bound zero. Apprenticeships are eligible only for the six explicitly listed occupational routes. Six-month refreshers assume already qualified workers where licensure/technical competence is required; they do not confer novice trade qualifications.

For engagement length H_i months, expected retained capacity per place is:

`y_ip = q_p × (1 − a_p)^(H_i / 12)`.

The capacity requirement is `Σ_p y_ip z_ip + deficit_i ≥ required_i`, with nonnegative continuous deficits. Capacity attrition is monotone; satisfying the engagement-end requirement therefore covers earlier times in this expected-value model. Separate monthly outputs show readiness, the one-year checkpoint and engagement-end capacity. The checkpoint does not replace the end constraint. No stochastic availability guarantee is claimed.

Upper-bound constraints cover employer transition outlay, public course-fee contributions, protected mentor hours, total places per route and places per role-route. Public contributions transfer part of a course fee between payers; the combined resource ledger includes each fee once. Mentor time has both a hard capacity limit and a scenario opportunity cost. Qualified candidates, provider places and mentor time are not inferred from employment stocks or aggregate apprenticeship completions.

Three MILP stages implement lexicographic priorities:

1. Minimise critical-role deficits.
2. Hold that optimum within 1e−7 FTE and minimise all deficits.
3. Hold both coverage optima within 1e−7 FTE and minimise combined resource present cost.

This priority choice can allocate resources away from non-critical roles. It is an explicit management assumption. Deficit weights are FTE units; the model does not estimate the economic damage of each vacancy. Final residuals must be below 1e−5, and optimal solver status is required at every stage. Positive gaps remain in the result instead of being hidden by a forced feasibility claim.

Construction and operation targets are disjoint occupation-period service allocations. Places are not recycled between phases and summed FTE requirements are not unique individuals. Provider/global route limits are deliberately conservative totals over all cohorts; mentor hours are pooled over the programme rather than scheduled by month. These assumptions can be replaced by time-indexed flows when actual cohort calendars and worker transitions are available.

## Costs and appraisal

Employer/public transition budgets cap undiscounted constant-price outlays. Training release pay is included as an assumed transition resource; payroll for unsuccessful training time beyond that assumption is not separately imputed. Ongoing pay and specialist fees are outside transition budgets and require separate funding. Expected ongoing costs follow successful retained capacity, including integer rounding surplus; they are discounted monthly at the declared rate. A route is backward-scheduled to finish at its deadline. Upfront transition resources are charged at its start; no speculative prelaunch idle payroll is added.

The combined programme present-cost ledger includes transition resources, mentor cost and expected pay/contract fees over the modeled engagements. It is a partial employer/programme resource view, not a complete project cash-flow statement or social cost-benefit appraisal. Wages are not automatically social opportunity costs. The descriptive public cost-effectiveness denominator counts publicly supported retained training capacity, capped by each role requirement. It is not an incremental treatment-effect denominator.

The guarantee stress is simply `£202m × assumed lifetime PD × assumed LGD`. No guarantee tenor is inferred from the 15-year lease. Fees, calibrated default probabilities, correlated loss, recoveries, discount timing, counterfactual lending and social benefits are missing. Fiscal expected cost, subsidy additionality, NPV and BCR therefore remain null. See [Green Book 2026](https://www.gov.uk/government/publications/the-green-book--2/the-green-book-2026) for the wider appraisal questions a real commission would need to answer.

The phased comparison adds one construction year up to a five-year ceiling. It lowers peak demand and changes training readiness and discount timing. It does not price delayed revenue, escalation, disruption or forgone output, so it cannot establish an optimal launch date or investment value.

## Economic interpretation and an empirical extension

The occupation-to-task distinction follows the research question in [Autor, Levy and Murnane (2003)](https://doi.org/10.1162/003355303322552801). The separate displacement and new-task mechanisms discussed by [Acemoglu and Restrepo (2019)](https://www.aeaweb.org/articles?id=10.1257/jep.33.2.3) motivate testing workload changes rather than assuming all AI exposure eliminates a job. Neither paper calibrates this project's numerical workload factor. Recruitment selection, skill formation, retention and allocation connect this planning exercise to [Lazear and Shaw's personnel-economics perspective](https://www.nber.org/papers/w13653). Incentives and endogenous wage/retention responses are not estimated by the current model.

A future evaluation could randomise an oversubscribed training offer among eligible, willing candidates, while maintaining mandatory safety training for everyone. Define the treatment as an offer, estimate intention-to-treat effects, record take-up and distinguish completion from employment, earnings, retention and task performance. Specify assignment and analysis before outcomes are observed. A lottery effect applies to its eligible population; it does not automatically generalise to all regional workers. If randomisation is unavailable, document the actual selection mechanism and the evidence supporting a comparison design before choosing an estimator. Do not add a generic DID label to a scenario model.

No such participant study or causal result has been conducted in this release. The next substantive research gain would come from verified worker/provider evidence and observed task outcomes, not more decorative indicators.

## Computation and reproducibility

Python uses SciPy MILP/HiGHS. The browser uses locally bundled highs-js 1.15.4/HiGHS WebAssembly in a worker. Both construct identical coefficients and perform the same three stages; stage limits are 15 seconds with relative MIP gap 1e−9. A time-limited solve is reported as an error rather than an optimum. Dense IO inversion is cubic in 98 industries; monthly occupation translation is linear in months × industries × occupations. MILP has exponential worst-case complexity. This is a bounded case tool, not a claim of large-scale optimality.

The hand-solvable integer case checks indivisible places and explicit gaps. Full-case tests cover timing, cumulative-work reconciliation, task coverage, retention, resources and missingness. Real browser tests compare default and altered inputs against Python for all monthly occupations, targets, gaps and costs, then exercise imports, stale-result prevention and downloads at desktop/tablet/mobile widths. Reviewer notes and repairs are recorded separately; automated/AI review is not a human field study or professional accreditation.
