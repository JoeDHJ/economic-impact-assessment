"use strict";
const D = window.WORKFORCE_DATA,
  M = window.IMPACT_DATA.model,
  $ = (id) => document.getElementById(id),
  C = Workforce.clone;
const fmt = (n, d = 1) =>
    new Intl.NumberFormat("en-GB", {
      maximumFractionDigits: d,
      minimumFractionDigits: d,
    }).format(n),
  money = (n) => "£" + fmt(n, 0),
  node = (tag, text, cls) => {
    const e = document.createElement(tag);
    if (text !== undefined) e.textContent = text;
    if (cls) e.className = cls;
    return e;
  };
let workspace = C(D.workspace),
  current = D.base.results[2],
  comparison = D.base.comparison,
  comparisonCurrent = true,
  dirty = false,
  worker,
  busy = false,
  advancedPending = false;
window.currentWorkforce = current;
const exportIds = [
  "export-report",
  "export-result",
  "export-roster",
  "export-gaps",
  "export-allocations",
  "export-retention",
  "export-months",
];
function status(s, error = false) {
  $("status").textContent = s;
  $("status").classList.toggle("error", error);
}
function syncInputs() {
  const p = workspace.programme;
  for (const [id, value] of Object.entries({
    capital: workspace.economic_scenario.capital_gbp_m,
    years: workspace.economic_scenario.construction_years,
    employer: p.employer_transition_budget_gbp,
    public: p.public_transition_budget_gbp,
    mentor: p.mentor_hours_available,
    routine: workspace.staffing.routine_workload_factor,
  }))
    $(id).value = value;
  $("advanced").value = JSON.stringify(workspace, null, 2);
}
function readInputs() {
  if (advancedPending)
    throw Error("Apply the advanced edits or reset before running or saving.");
  for (const id of [
    "capital",
    "years",
    "employer",
    "public",
    "mentor",
    "routine",
  ])
    if (!$(id).value.trim()) throw Error(id + ": a value is required");
  const w = C(workspace);
  w.economic_scenario.capital_gbp_m = +$("capital").value;
  w.economic_scenario.construction_years = +$("years").value;
  w.programme.employer_transition_budget_gbp = +$("employer").value;
  w.programme.public_transition_budget_gbp = +$("public").value;
  w.programme.mentor_hours_available = +$("mentor").value;
  w.staffing.routine_workload_factor = +$("routine").value;
  return Workforce.validate(w, D.workspace, M);
}
function markDirty() {
  dirty = true;
  exportIds.forEach((id) => ($(id).disabled = true));
  $("export-options").disabled = true;
  $("result-label").textContent = "PREVIOUS RESULT · INPUTS CHANGED";
  status("Inputs changed. Run the plan or compare options to update results.");
}
function table(id, rows) {
  $(id).replaceChildren(
    ...rows.map((values) => {
      const tr = node("tr");
      values.forEach((value) => {
        const td = node("td");
        if (value instanceof HTMLElement) td.append(value);
        else td.textContent = value;
        tr.append(td);
      });
      return tr;
    }),
  );
}
function label(a, b) {
  const e = node("span", a);
  e.append(node("small", b));
  return e;
}
function chart() {
  const rows = current.delivery.months,
    colors = ["#adc6ac", "#719b7d", "#246452", "#bd945b"],
    max = Math.max(...rows.map((r) => r.annualised_fte), 1),
    W = 800,
    H = 220,
    b = current.delivery.phase_boundaries,
    bw = 720 / rows.length;
  const bars = rows
    .map((r, i) => {
      const phase = b.findIndex((v, j) => j < 4 && i >= v && i < b[j + 1]),
        h = (r.annualised_fte / max) * 160;
      return `<rect x="${55 + i * bw}" y="${185 - h}" width="${Math.max(0.8, bw - 2)}" height="${h}" fill="${colors[phase]}"><title>Month ${r.month}: ${fmt(r.annualised_fte)} annualised FTE</title></rect>`;
    })
    .join("");
  $("chart").innerHTML =
    `<svg viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="chart-title chart-desc"><title id="chart-title">Phased Scottish construction demand</title><desc id="chart-desc">Peak ${fmt(current.delivery.peak_monthly_fte)} annualised FTE; cumulative ${fmt(current.delivery.construction_job_years)} FTE job-years. Detailed monthly occupations are available as CSV.</desc><text x="0" y="25" font-size="11" fill="#58675f">${fmt(max, 0)}</text><line x1="55" y1="185" x2="775" y2="185" stroke="#c8d5c8"/>${bars}<text x="55" y="208" font-size="11">Month 1</text><text x="710" y="208" font-size="11">${rows.length}</text></svg>`;
  $("phase-key").replaceChildren(
    ...workspace.delivery.phase_labels.map((s, i) => {
      const e = node("span", s);
      e.style.setProperty("--color", colors[i]);
      return e;
    }),
  );
}
function render() {
  const a = current.allocation,
    w = current.workspace,
    p = w.programme;
  window.currentWorkforce = current;
  $("gap").textContent = fmt(a.expected_gap_fte);
  $("critical").textContent = fmt(a.critical_gap_fte);
  $("cost").textContent =
    "£" +
    fmt((a.employer_transition_gbp + a.public_transition_gbp) / 1000, 0) +
    "k";
  $("recommendation").textContent =
    a.critical_gap_fte > 1e-5
      ? `Critical service capacity remains uncovered. Verify eligible candidates and increase the binding route or mentor capacity before treating this plan as launch-ready. Total expected gap: ${fmt(a.expected_gap_fte)} role-period FTE.`
      : `The plan covers expected critical-role requirements, while ${fmt(a.expected_gap_fte)} role-period FTE remain uncovered overall. Protect mentor time and verify qualified candidates before commissioning cohorts; non-critical service gaps still need a response.`;
  const resources = [
    [
      "Employer transition",
      a.employer_transition_gbp,
      p.employer_transition_budget_gbp,
      "£",
    ],
    [
      "Public training",
      a.public_transition_gbp,
      p.public_transition_budget_gbp,
      "£",
    ],
    ["Mentor time", a.mentor_hours, p.mentor_hours_available, "h"],
  ];
  for (const [path, cap] of Object.entries(p.pathway_capacity))
    resources.push([
      path + " places",
      a.selected
        .filter((r) => r.pathway === path)
        .reduce((v, r) => v + r.places, 0),
      cap,
      "places",
    ]);
  $("resources").replaceChildren(
    ...resources.map(([name, used, total, unit]) => {
      const e = node("div", undefined, "resource"),
        head = node("div", undefined, "resource-head"),
        track = node("div", undefined, "track"),
        bar = node("span");
      head.append(
        node("span", name),
        node(
          "span",
          unit === "£"
            ? `${money(used)} / ${money(total)}`
            : `${fmt(used, 0)} / ${fmt(total, 0)} ${unit}`,
        ),
      );
      bar.style.width = (total ? Math.min(100, (used / total) * 100) : 0) + "%";
      if (total > 0 && used / total > 0.98) bar.className = "binding";
      track.append(bar);
      e.append(head, track);
      return e;
    }),
  );
  $("comparison-note").textContent = comparisonCurrent
    ? "Same current inputs; the phased case extends construction by one year, up to five years."
    : "Published default comparison — run Compare four options for your current assumptions.";
  table(
    "options",
    comparison.map((r) => [
      label(
        r.option,
        `${r.construction_years} years · demand ${fmt(r.required_role_period_fte)} role-period FTE`,
      ),
      fmt(r.critical_gap_fte),
      fmt(r.expected_gap_fte),
      money(r.employer_transition_gbp),
      money(r.public_transition_gbp),
      "£" + fmt(r.resource_pv_gbp / 1e6, 2) + "m",
    ]),
  );
  $("jobyears").textContent =
    fmt(current.delivery.construction_job_years, 0) + " FTE job-years";
  const g = current.guarantee_stress;
  $("guarantee").textContent =
    `Uncalibrated PD ${fmt(g.default_probability_scenario * 100)}% × LGD ${fmt(g.loss_given_default_scenario * 100)}% gives a £${fmt(g.undiscounted_loss_illustration_gbp_m, 2)}m lifetime exposure illustration. Actual expected fiscal cost, social NPV and BCR remain unavailable.`;
  $("roster-note").textContent =
    `${fmt(current.operating_required_service_fte)} service FTE from ${w.staffing.annual_paid_hours - w.staffing.noncoverage_hours} productive hours per FTE. 24/7 coverage uses 8,760 annual hours; day posts use ${w.staffing.daytime_weekly_hours} hours × 52 weeks. This is not a verified employer roster.`;
  table(
    "roster",
    current.staffing.map((r) => [
      label(r.label, r.soc2020 + (r.critical ? " · critical" : "")),
      fmt(r.continuous_posts),
      fmt(r.daytime_posts),
      fmt(r.annual_coverage_hours, 0),
      fmt(r.required_service_fte, 2),
    ]),
  );
  table(
    "roles",
    a.roles.map((r) => [
      label(
        r.label,
        `${r.phase}${r.critical ? " · critical" : ""} · ${r.engagement_months} months`,
      ),
      r.deadline_month,
      fmt(r.required_fte, 2),
      fmt(r.expected_retained_capacity_fte, 2),
      node(
        "span",
        fmt(r.expected_gap_fte, 2),
        r.expected_gap_fte > 0.01 ? "gap" : "",
      ),
    ]),
  );
  table(
    "allocations",
    a.selected.length
      ? a.selected.map((r) => [
          label(a.roles[r.target_index].label, r.target_id + " / " + r.pathway),
          r.places,
          r.start_month,
          r.ready_month,
          fmt(r.expected_retained_fte, 2),
        ])
      : [["No cohorts selected", "—", "—", "—", "—"]],
  );
  $("solver-note").textContent =
    `Current result: ${a.solver.length} optimal stages; maximum constraint residual ${a.max_constraint_violation.toExponential(2)}. Combined programme resource present cost ${money(a.resource_pv_gbp)}. Public cost per supported retained capacity: ${a.public_cost_per_supported_capacity_fte_gbp === null ? "undefined" : money(a.public_cost_per_supported_capacity_fte_gbp)} (descriptive, not causal).`;
  chart();
  exportIds.forEach((id) => ($(id).disabled = dirty));
  $("export-options").disabled = dirty || !comparisonCurrent;
}
function showView(id) {
  for (const b of document.querySelectorAll("[data-view]")) {
    if (b.dataset.view === id) b.setAttribute("aria-current", "page");
    else b.removeAttribute("aria-current");
  }
  for (const view of document.querySelectorAll(".view"))
    view.hidden = view.id !== id;
}
function setBusy(value) {
  busy = value;
  for (const e of document.querySelectorAll(
    ".controls button,.controls input,.controls textarea",
  ))
    e.disabled = value;
  for (const id of ["run", "compare", "save"])
    $(id).disabled = value || advancedPending;
  for (const e of document.querySelectorAll("#inputs input"))
    e.disabled = value || advancedPending;
  $("import").disabled = value;
  exportIds.forEach((id) => ($(id).disabled = value || dirty));
  $("export-options").disabled = value || dirty || !comparisonCurrent;
}
function run(compare) {
  if (busy) return;
  try {
    if (!$("inputs").reportValidity()) return;
    workspace = readInputs();
    syncInputs();
    if (location.protocol === "file:")
      throw Error(
        "Local solver needs HTTP: run impact-assessment serve, then open http://127.0.0.1:8765. Published results and the regional calculator remain readable offline.",
      );
    setBusy(true);
    status("Starting local optimisation…");
    worker = worker || new Worker("workforce-worker.js");
    worker.onmessage = ({ data }) => {
      if (data.type === "progress") {
        status(data.message);
        return;
      }
      setBusy(false);
      if (data.type === "error") {
        status(data.message, true);
        return;
      }
      current = data.results[compare ? 2 : 0];
      if (compare) {
        comparison = data.comparison;
        comparisonCurrent = true;
      } else {
        comparison = D.base.comparison;
        comparisonCurrent =
          JSON.stringify(workspace) === JSON.stringify(D.workspace);
      }
      dirty = false;
      $("result-label").textContent = "CURRENT SOLVED INPUTS";
      render();
      status(
        "Solved locally · three optimal stages per option · no data uploaded.",
      );
    };
    worker.onerror = (e) => {
      setBusy(false);
      status("Local solver error: " + e.message, true);
      worker.terminate();
      worker = null;
    };
    worker.postMessage({ workspace, template: D.workspace, model: M, compare });
  } catch (e) {
    setBusy(false);
    status(e.message, true);
  }
}
function download(name, text, type = "application/json") {
  const url = URL.createObjectURL(new Blob([text], { type })),
    a = node("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function csv(rows, columns) {
  const keys = columns || (rows.length ? Object.keys(rows[0]) : []),
    q = (x) => '"' + String(x ?? "").replaceAll('"', '""') + '"';
  return (
    [keys, ...rows.map((r) => keys.map((k) => r[k]))]
      .map((r) => r.map(q).join(","))
      .join("\r\n") + "\r\n"
  );
}
function report() {
  const r = current,
    a = r.allocation,
    w = r.workspace;
  return `# AI investment and workforce decision record\n\nIndependent portfolio analysis by Haojian Dui. Model 0.2.0.\n\nCase: ${w.name}\n\nConditional scenario; money at 2022 prices. Not observed employer outcomes.\n\n- Construction: £${w.economic_scenario.capital_gbp_m}m independent capital assumption; ${w.economic_scenario.construction_years} years; ${fmt(r.delivery.construction_job_years, 2)} Scottish FTE job-years; peak ${fmt(r.delivery.peak_monthly_fte, 2)} annualised FTE. Financing is not capex.\n- Task roster: ${fmt(r.operating_required_service_fte, 2)} service FTE, not verified headcount. Contractor capacity is not added to IO supplier employment.\n- Critical gap: ${fmt(a.critical_gap_fte, 2)}; total gap: ${fmt(a.expected_gap_fte, 2)} role-period FTE. These are not unique people or additional jobs.\n- Employer transition: ${money(a.employer_transition_gbp)} / ${money(w.programme.employer_transition_budget_gbp)}.\n- Public transition: ${money(a.public_transition_gbp)} / ${money(w.programme.public_transition_budget_gbp)}.\n- Mentor time: ${a.mentor_hours} / ${w.programme.mentor_hours_available} hours.\n- Programme resource present cost: ${money(a.resource_pv_gbp)}, including expected ongoing pay/contract fees. Ongoing costs need funding beyond transition budgets.\n- Public supported retained capacity: ${fmt(a.public_supported_retained_capacity_fte, 2)}; descriptive public cost per supported FTE: ${a.public_cost_per_supported_capacity_fte_gbp === null ? "undefined" : money(a.public_cost_per_supported_capacity_fte_gbp)}. No causal additionality claim.\n\n## Role gaps\n\n| Target | Required | Expected end capacity | Gap |\n| --- | ---: | ---: | ---: |\n${a.roles.map((t) => `| ${t.id} | ${fmt(t.required_fte, 2)} | ${fmt(t.expected_retained_capacity_fte, 2)} | ${fmt(t.expected_gap_fte, 2)} |`).join("\n")}\n\n## Interpretation\n\nCritical-role deficits are minimised first, all deficits second, resource PV third. Expected engagement-end capacity uses scenario success and attrition rates. Cohorts are separate role-period allocations, not unique workers. Refreshers assume qualified incumbents; verify competence and provider places before commitment. No programme means no commissioned capacity through these pathways. Stocks are not available applicants. Public guarantee face value (£202m) is exposure, not expenditure; no calibrated expected fiscal cost, NPV or BCR is supplied. A later launch changes peak targets and discount timing; revenue, delay and escalation costs are absent.\n\nComparison status: ${comparisonCurrent ? "Current inputs, four options solved." : "Only this current plan has been solved; the page's four-option comparison is the published default."}\n\nSolver: ${JSON.stringify(a.solver)}; maximum constraint violation ${a.max_constraint_violation}.\n\nSave full inputs and result JSON alongside this brief for the complete decision trail.\n\nSources and methods: https://github.com/JoeDHJ/economic-impact-assessment\n`;
}
for (const e of document.querySelectorAll("#inputs input"))
  e.addEventListener("input", markDirty);
$("inputs").addEventListener("submit", (e) => {
  e.preventDefault();
  run(false);
});
$("compare").onclick = () => run(true);
$("reset").onclick = () => {
  workspace = C(D.workspace);
  current = D.base.results[2];
  comparison = D.base.comparison;
  comparisonCurrent = true;
  dirty = false;
  advancedPending = false;
  syncInputs();
  setBusy(false);
  render();
  $("result-label").textContent = "PUBLISHED DEFAULT";
  status("Published default results restored.");
};
$("save").onclick = () => {
  try {
    if (!$("inputs").reportValidity()) return;
    download(
      "workforce-inputs.json",
      JSON.stringify(readInputs(), null, 2) + "\n",
    );
  } catch (e) {
    status(e.message, true);
  }
};
function apply(w) {
  Workforce.validate(w, D.workspace, M);
  workspace = C(w);
  advancedPending = false;
  syncInputs();
  setBusy(false);
  markDirty();
}
$("apply").onclick = () => {
  try {
    apply(JSON.parse($("advanced").value));
  } catch (e) {
    status("Invalid inputs: " + e.message, true);
  }
};
$("import").onchange = async (e) => {
  try {
    const f = e.target.files[0];
    if (!f) return;
    if (f.size > 2000000) throw Error("Input file exceeds 2 MB limit");
    apply(JSON.parse((await f.text()).replace(/^\uFEFF/, "")));
  } catch (error) {
    status("Import failed: " + error.message, true);
  } finally {
    e.target.value = "";
  }
};
$("advanced").addEventListener("input", () => {
  advancedPending = true;
  markDirty();
  setBusy(false);
  status(
    "Advanced edits pending. Apply complete inputs before running or saving.",
  );
});
for (const b of document.querySelectorAll("[data-view]"))
  b.onclick = () => showView(b.dataset.view);
for (const a of document.querySelectorAll("[data-go]"))
  a.onclick = () => showView(a.dataset.go);
$("export-result").onclick = () =>
  download("workforce-results.json", JSON.stringify(current, null, 2) + "\n");
$("export-report").onclick = () =>
  download(
    "workforce-decision-brief.md",
    report(),
    "text/markdown;charset=utf-8",
  );
for (const [id, file, get] of [
  ["export-options", "decision-options", () => comparison],
  ["export-roster", "service-roster", () => current.staffing],
  ["export-gaps", "role-gaps", () => current.allocation.roles],
  [
    "export-allocations",
    "programme-allocations",
    () => current.allocation.selected,
  ],
  [
    "export-retention",
    "retention-coverage",
    () => current.allocation.coverage_months,
  ],
  ["export-local", "local-labour-observations", () => D.local],
  [
    "export-months",
    "monthly-occupations",
    () =>
      current.delivery.occupation_fte.flatMap((values, i) =>
        values.map((v, j) => ({
          month: i + 1,
          soc2020: M.occupation_codes[j],
          label: M.occupation_labels[j],
          annualised_fte: v,
          fte_job_years_in_month: v / 12,
        })),
      ),
  ],
])
  $(id).onclick = () =>
    download(
      file + ".csv",
      csv(
        get(),
        id === "export-allocations"
          ? [
              ...Object.keys(
                Workforce.candidates(current.workspace, current.targets)[0],
              ),
              "places",
              "expected_retained_fte",
            ]
          : undefined,
      ),
      "text/csv;charset=utf-8",
    );
$("claims").replaceChildren(
  ...D.evidence.facts.map((r) => {
    const e = node("article", undefined, "claim"),
      meta = node("div"),
      body = node("p"),
      a = node("a", "Primary source ↗");
    meta.append(
      node("strong", r.label),
      node("small", r.status.replaceAll("_", " ")),
    );
    body.append(
      node(
        "span",
        `${r.value === null ? "Not disclosed" : r.value} ${r.unit}. ${r.scope}. ${r.interpretation} `,
      ),
    );
    a.href = r.source_url;
    body.append(a);
    e.append(meta, body);
    return e;
  }),
);
table(
  "local-data",
  D.local.map((r) => [
    r.metric,
    label(
      r.value === null
        ? "Suppressed / unavailable"
        : fmt(r.value, r.unit.includes("GBP") ? 2 : 0),
      r.unit,
    ),
    r.period,
    label(r.population, r.source),
  ]),
);
syncInputs();
render();
if (location.protocol === "file:")
  status(
    "Published default results. For interactive optimisation, serve locally over HTTP; see reproducibility instructions.",
  );
