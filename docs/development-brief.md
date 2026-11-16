# Economic Impact Assessment — Development Brief

Date: 2026-11-16
Repository: JoeDHJ/economic-impact-assessment
Product: Labor Market and Economic Impact Assessment.

## Decision to support

A region is considering a major AI data-center investment and needs a defensible view of employment, industry linkages, local skills supply and training options. Build a focused consulting case with reusable methods and actual public economic data. The proposed project itself may be a clearly labeled scenario.

## Scope

- Build a reproducible analytical package/CLI and an accessible local dashboard with source manifests, input schemas, an offline runnable example and refresh commands.
- Select a U.S. region or another geography with adequate official public input-output, industry employment, occupational staffing and wage data. Document the geography, vintage, price year and mappings. Favor an independently reproducible public-data case over a commercial black-box multiplier.
- Implement input-output calculations from real official tables with documented dimensions, industry aggregation, technical coefficients and a coherent final-demand vector. Test accounting identities, orientation and the multiplier calculation against a hand-solvable system.
- Separate construction from operations, temporary job-years from recurring jobs, spending from value added, and direct/indirect/induced effects. Include induced effects only if the closure and household assumptions are implemented and documented.
- Model local retention/import leakage and commuting consistently. Never add a direct effect to a multiplier total that already contains it. National multipliers cannot silently become local estimates. Keep gross modeled activity separate from a supported net welfare/fiscal assessment.
- Map industry demand to occupations/skills using public staffing and skill references. Assess local employment, training capacity or other actual supply proxies with explicit coverage. Do not claim a labor shortage from employment stocks alone.
- Compare feasible training and recruitment/policy options using costs, capacity and implementation timing. Add useful sensitivities to spending composition, localization, construction duration and operating staffing; report the assumptions that drive decisions.
- Complete one full public-data case yielding actual regenerated industry/occupation results, clear scenario ranges and a reasoned recommendation. Preserve real observations separately from project budget/staffing assumptions.
- Deliver an economic impact report, executive brief, industry/occupation estimates, supply-demand assessment, policy recommendations, client presentation outline and a two-minute demonstration script. Default to Markdown, data and figures; no unrequested Word/PDF files.
- README and dashboard must make the client's question, key findings, units, methods, sources and reproduction visible. Use complete module screenshots with margins. Provide optional portfolio.v1 adapters without a hard sibling-service dependency.

## Completion evidence

Map 2–3 actual official economic-consulting/policy-economist JDs to checkable artifacts. Verify dimensions, units, current/constant dollars, horizon, zero/negative/missing/invalid input behavior, singular/ill-conditioned systems, double counting, leakage arithmetic, package installation and browser usability. Independent read-only review covers all six dimensions; repair material findings and re-run affected checks before publication.

## Development workflow

Maintain this as a focused, independently reproducible consulting project. Develop in scoped feature branches, complete the public-data case and resolve independent-review findings before release. Preserve the distinction between observed regional economic data and assumed project inputs throughout the code, dashboard and deliverables.
