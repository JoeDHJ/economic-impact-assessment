/* Solver-neutral workforce model. No remote requests; inputs never become markup. */
"use strict";
const Workforce = (() => {
  const clone = (x) => JSON.parse(JSON.stringify(x)),
    sum = (a) => a.reduce((x, y) => x + y, 0),
    dot = (a, b) => sum(a.map((x, i) => x * b[i]));
  function validate(w, t, m) {
    const fail = (s) => {
        throw Error(s);
      },
      keys = (o, p, n) => {
        if (
          !o ||
          Array.isArray(o) ||
          typeof o !== "object" ||
          Object.keys(o).sort().join("|") !== Object.keys(p).sort().join("|")
        )
          fail(n + ": fields do not match schema");
      };
    const num = (v, n, l, h) => {
        if (typeof v !== "number" || !Number.isFinite(v) || v < l || v > h)
          fail(n + ": outside valid range");
      },
      integer = (v, n, l, h) => {
        num(v, n, l, h);
        if (!Number.isInteger(v)) fail(n + ": integer required");
      };
    const text = (v, n, max) => {
      if (typeof v !== "string" || !v.trim() || v.length > max)
        fail(n + ": invalid text");
    };
    keys(w, t, "workspace");
    for (const k of [
      "schema_version",
      "project_evidence_id",
      "currency",
      "price_year",
      "status",
    ])
      if (w[k] !== t[k]) fail(k + ": unsupported snapshot");
    text(w.name, "name", 180);
    const s = w.economic_scenario,
      ts = t.economic_scenario;
    keys(s, ts, "economic_scenario");
    for (const k of ["schema_version", "geography", "currency", "price_year"])
      if (s[k] !== ts[k]) fail(k + ": unsupported model");
    text(s.name, "economic name", 500);
    num(s.capital_gbp_m, "capital", 0, 100000);
    integer(s.construction_years, "construction years", 1, 5);
    integer(s.operating_years, "operating years", 1, 100);
    for (const k of [
      "supplier_retention",
      "resident_share",
      "load_factor",
      "electricity_capture",
    ])
      num(s[k], k, 0, 1);
    num(s.pue, "pue", 1, 3);
    for (const k of [
      "it_load_mw",
      "electricity_gbp_per_mwh",
      "electricity_io_valuation_gbp_per_mwh",
      "onsite_fte",
      "onsite_compensation_gbp",
    ])
      num(s[k], k, 0, 1e7);
    if (s.onsite_fte !== 0)
      fail("IO on-site FTE must be zero in the workforce workspace");
    for (const [field, amount] of [
      ["capital_components", "share"],
      ["operating_procurement", "gbp_m"],
    ]) {
      if (!Array.isArray(s[field]) || !s[field].length)
        fail(field + ": nonempty list required");
      const seen = new Set();
      for (const r of s[field]) {
        keys(r, { industry: 0, [amount]: 0, capture: 0 }, field);
        if (!m.codes.includes(r.industry) || seen.has(r.industry))
          fail("unknown/duplicate industry");
        seen.add(r.industry);
        num(r[amount], amount, 0, amount === "share" ? 1 : 1e6);
        num(r.capture, "capture", 0, 1);
        if (field === "operating_procurement" && r.industry === "35.1")
          fail("Electricity must be derived once");
        if (
          r[amount] *
            r.capture *
            (field === "capital_components" ? s.capital_gbp_m : 1) >
            0 &&
          m.observed_output_gbp_m[m.codes.indexOf(r.industry)] === 0
        )
          fail("Uncalibrated industry demand");
      }
    }
    if (Math.abs(sum(s.capital_components.map((r) => r.share)) - 1) > 1e-9)
      fail("Capital shares must sum to one");
    if (!Array.isArray(s.onsite_roles) || !s.onsite_roles.length)
      fail("On-site role shares required");
    const legacySeen = new Set();
    for (const r of s.onsite_roles) {
      keys(r, { soc2020: 0, share: 0 }, "legacy role");
      if (!m.occupation_codes.includes(r.soc2020) || legacySeen.has(r.soc2020))
        fail("Invalid legacy SOC");
      legacySeen.add(r.soc2020);
      num(r.share, "legacy share", 0, 1);
    }
    if (Math.abs(sum(s.onsite_roles.map((r) => r.share)) - 1) > 1e-9)
      fail("Legacy shares must sum to one");
    const v = w.delivery;
    keys(v, t.delivery, "delivery");
    for (const k of ["phase_labels", "phase_boundaries"])
      if (JSON.stringify(v[k]) !== JSON.stringify(t.delivery[k]))
        fail("Four documented phase definitions required");
    keys(
      v.component_phase_weights,
      Object.fromEntries(s.capital_components.map((r) => [r.industry, 0])),
      "phase weights",
    );
    for (const values of Object.values(v.component_phase_weights)) {
      if (!Array.isArray(values) || values.length !== 4)
        fail("Four phase weights required");
      values.forEach((x) => num(x, "phase weight", 0, 1));
      if (Math.abs(sum(values) - 1) > 1e-9)
        fail("Phase weights must sum to one");
    }
    if (
      !v.construction_occupation_factors ||
      Array.isArray(v.construction_occupation_factors) ||
      typeof v.construction_occupation_factors !== "object"
    )
      fail("Invalid occupational factors");
    for (const [code, values] of Object.entries(
      v.construction_occupation_factors,
    )) {
      if (
        !m.occupation_codes.includes(code) ||
        !Array.isArray(values) ||
        values.length !== 4
      )
        fail("Known SOC and four factors required");
      values.forEach((x) => num(x, "factor", 0, 5));
    }
    const st = w.staffing;
    keys(st, t.staffing, "staffing");
    num(st.annual_paid_hours, "paid hours", 1000, 2500);
    num(
      st.noncoverage_hours,
      "noncoverage hours",
      0,
      st.annual_paid_hours - 100,
    );
    num(st.daytime_weekly_hours, "day hours", 1, 60);
    num(st.employer_oncost_fraction, "oncost", 0, 1);
    num(st.routine_workload_factor, "routine factor", 0.25, 2);
    if (!Array.isArray(st.roles) || !st.roles.length || st.roles.length > 30)
      fail("1–30 roles required");
    const seen = new Set();
    for (const r of st.roles) {
      keys(r, t.staffing.roles[0], "role");
      if (!m.occupation_codes.includes(r.soc2020) || seen.has(r.soc2020))
        fail("Unknown/duplicate SOC");
      seen.add(r.soc2020);
      text(r.label, "role label", 100);
      for (const k of ["continuous_posts", "daytime_posts"])
        num(r[k], k, 0, 100);
      num(r.salary_gbp_2022, "salary", 0, 250000);
      for (const k of ["critical", "routine_workload_sensitive"])
        if (typeof r[k] !== "boolean") fail(k + ": boolean required");
    }
    const p = w.programme;
    keys(p, t.programme, "programme");
    for (const k of [
      "employer_transition_budget_gbp",
      "public_transition_budget_gbp",
    ])
      num(p[k], k, 0, 1e8);
    num(p.mentor_hours_available, "mentor hours", 0, 1e6);
    num(p.mentor_hourly_cost_gbp, "mentor cost", 0, 1000);
    num(p.discount_rate, "discount", 0, 0.25);
    integer(p.operating_engagement_months, "engagement", 1, 120);
    integer(p.retention_checkpoint_months, "checkpoint", 0, 120);
    num(p.construction_target_share, "build target share", 0, 1);
    if (
      !Array.isArray(p.construction_target_soc) ||
      p.construction_target_soc.length > 12 ||
      p.construction_target_soc.some((c) => !m.occupation_codes.includes(c)) ||
      new Set(p.construction_target_soc).size !==
        p.construction_target_soc.length
    )
      fail("Unique known construction SOCs required");
    keys(
      p.construction_salary_gbp_2022,
      Object.fromEntries(p.construction_target_soc.map((c) => [c, 0])),
      "construction salary",
    );
    Object.values(p.construction_salary_gbp_2022).forEach((x) =>
      num(x, "salary", 0, 250000),
    );
    if (!Array.isArray(p.pathways) || p.pathways.length !== 4)
      fail("Four pathways required");
    const ids = new Set();
    for (const r of p.pathways) {
      keys(r, t.programme.pathways[0], "pathway");
      if (
        !["redeploy", "hire", "apprentice", "contract"].includes(r.id) ||
        ids.has(r.id)
      )
        fail("Unknown/duplicate pathway");
      ids.add(r.id);
      text(r.label, "path label", 100);
      if (r.kind !== (r.id === "contract" ? "contractor" : "employee"))
        fail("Invalid employment/contract kind");
      integer(r.lead_months, "lead", 0, 120);
      integer(r.max_places_per_role, "role places", 0, 200);
      for (const k of ["success_rate", "public_fee_share"]) num(r[k], k, 0, 1);
      num(r.annual_attrition, "attrition", 0, 0.8);
      for (const k of [
        "course_fee_gbp",
        "recruitment_fee_gbp",
        "paid_release_gbp",
        "onboarding_gbp",
      ])
        num(r[k], k, 0, 1e6);
      num(r.mentor_hours, "mentoring", 0, 1e4);
      num(r.annual_cost_multiplier, "cost multiplier", 0.5, 5);
    }
    keys(
      p.pathway_capacity,
      Object.fromEntries([...ids].map((k) => [k, 0])),
      "capacities",
    );
    Object.values(p.pathway_capacity).forEach((x) =>
      integer(x, "capacity", 0, 1000),
    );
    keys(w.guarantee_stress, t.guarantee_stress, "guarantee");
    for (const k of ["default_probability", "loss_given_default"])
      num(w.guarantee_stress[k], k, 0, 1);
    return w;
  }
  function inverse(m, r) {
    if (r === 1) return m.leontief;
    const n = m.codes.length,
      a = m.a.map((row, i) => [
        ...row.map((x, j) => (i === j ? 1 : 0) - r * x),
        ...Array.from({ length: n }, (_, j) => (i === j ? 1 : 0)),
      ]);
    for (let j = 0; j < n; j++) {
      let pivot = j;
      for (let i = j + 1; i < n; i++)
        if (Math.abs(a[i][j]) > Math.abs(a[pivot][j])) pivot = i;
      [a[j], a[pivot]] = [a[pivot], a[j]];
      const scale = a[j][j];
      if (Math.abs(scale) < 1e-12) throw Error("Singular IO system");
      for (let k = 0; k < 2 * n; k++) a[j][k] /= scale;
      for (let i = 0; i < n; i++)
        if (i !== j) {
          const q = a[i][j];
          for (let k = 0; k < 2 * n; k++) a[i][k] -= q * a[j][k];
        }
    }
    return a.map((row) => row.slice(n));
  }
  function demand(w, m) {
    const s = w.economic_scenario,
      v = w.delivery,
      N = s.construction_years * 12,
      b = v.phase_boundaries.map((x) => Math.round(x * N)),
      inv = inverse(m, s.supplier_retention),
      months = [],
      occupations = [],
      industries = [];
    const profiles = Array.from({ length: 4 }, (_, p) => {
      const a = clone(m.staffing),
        i = m.codes.indexOf("41-43");
      for (const [code, f] of Object.entries(v.construction_occupation_factors))
        a[i][m.occupation_codes.indexOf(code)] *= f[p];
      const total = sum(a[i]);
      if (total <= 0) throw Error("Empty construction occupation profile");
      a[i] = a[i].map((x) => x / total);
      return a;
    });
    for (let p = 0; p < 4; p++)
      for (let k = b[p]; k < b[p + 1]; k++) {
        const f = m.codes.map(() => 0);
        for (const c of s.capital_components)
          f[m.codes.indexOf(c.industry)] +=
            (s.capital_gbp_m *
              c.share *
              c.capture *
              v.component_phase_weights[c.industry][p]) /
            (b[p + 1] - b[p]);
        const x = inv.map((row) => dot(row, f)),
          jobs = x.map((v, i) => v * m.employment[i] * 12),
          occ = m.occupation_codes.map((_, j) =>
            sum(jobs.map((v, i) => v * profiles[p][i][j])),
          );
        industries.push(jobs);
        occupations.push(occ);
        months.push({
          month: k + 1,
          phase: v.phase_labels[p],
          scottish_output_gbp_m: sum(x),
          annualised_fte: sum(jobs),
          fte_job_years_in_month: sum(jobs) / 12,
        });
      }
    return {
      months,
      occupation_fte: occupations,
      industry_fte: industries,
      construction_job_years: sum(months.map((r) => r.fte_job_years_in_month)),
      peak_monthly_fte: Math.max(...months.map((r) => r.annualised_fte)),
      phase_boundaries: b,
      phase_occupational_profiles_status: "scenario_adjusted_UK_staffing_proxy",
    };
  }
  function roster(w) {
    const s = w.staffing;
    return s.roles.map((r) => {
      const h =
          (r.continuous_posts * 8760 +
            r.daytime_posts * 52 * s.daytime_weekly_hours) *
          (r.routine_workload_sensitive ? s.routine_workload_factor : 1),
        productive = s.annual_paid_hours - s.noncoverage_hours;
      return {
        ...r,
        annual_coverage_hours: h,
        productive_hours_per_fte: productive,
        required_service_fte: h / productive,
        annual_loaded_cost_per_fte:
          r.salary_gbp_2022 * (1 + s.employer_oncost_fraction),
        status: "task_coverage_scenario_not_employer_roster",
      };
    });
  }
  function targets(w, d, st, m) {
    const p = w.programme,
      result = [];
    for (const code of p.construction_target_soc) {
      const j = m.occupation_codes.indexOf(code),
        values = d.occupation_fte.map((r) => r[j]),
        peak = values.indexOf(Math.max(...values)),
        phase = d.phase_boundaries.findIndex(
          (b, i) => i < 4 && b <= peak && peak < d.phase_boundaries[i + 1],
        ),
        deadline = d.phase_boundaries[phase];
      result.push({
        id: "build_" + code,
        soc2020: code,
        label: m.occupation_labels[j],
        phase: "construction programme",
        required_fte: values[peak] * p.construction_target_share,
        regional_peak_fte: values[peak],
        target_share: p.construction_target_share,
        deadline_month: deadline,
        engagement_months: d.phase_boundaries[phase + 1] - deadline,
        critical: true,
        annual_loaded_cost_per_fte:
          p.construction_salary_gbp_2022[code] *
          (1 + w.staffing.employer_oncost_fraction),
        scope:
          "Scenario share of Scottish supply-chain occupation peak; not site headcount or measured local shortage",
      });
    }
    for (const r of st)
      result.push({
        id: "operate_" + r.soc2020,
        soc2020: r.soc2020,
        label: r.label,
        phase: "operating service roster",
        required_fte: r.required_service_fte,
        regional_peak_fte: null,
        target_share: null,
        deadline_month: w.economic_scenario.construction_years * 12,
        engagement_months: p.operating_engagement_months,
        critical: r.critical,
        annual_loaded_cost_per_fte: r.annual_loaded_cost_per_fte,
        scope:
          "Task-based technical service capacity; employment/contract mix determined separately",
      });
    return result;
  }
  function candidates(w, ts, allowed) {
    const p = w.programme,
      result = [];
    ts.forEach((t, i) =>
      p.pathways.forEach((r) => {
        if (allowed && !allowed.includes(r.id)) return;
        const eligible =
            r.lead_months <= t.deadline_month &&
            (r.id !== "apprentice" ||
              ["5241", "5315", "5225", "3131", "2137", "5246"].includes(
                t.soc2020,
              )),
          start = t.deadline_month - r.lead_months,
          pub = r.course_fee_gbp * r.public_fee_share,
          up =
            r.course_fee_gbp +
            r.recruitment_fee_gbp +
            r.paid_release_gbp +
            r.onboarding_gbp +
            r.mentor_hours * p.mentor_hourly_cost_gbp,
          transition =
            up * (start >= 0 ? (1 + p.discount_rate) ** (-start / 12) : 1);
        let pay = 0;
        for (let month = 0; month < t.engagement_months; month++)
          pay +=
            (r.success_rate *
              (1 - r.annual_attrition) ** ((month + 0.5) / 12) *
              t.annual_loaded_cost_per_fte *
              r.annual_cost_multiplier) /
            12 /
            (1 + p.discount_rate) ** ((t.deadline_month + month + 0.5) / 12);
        result.push({
          target_index: i,
          target_id: t.id,
          pathway: r.id,
          label: r.label,
          kind: r.kind,
          eligible,
          maximum_places: eligible ? r.max_places_per_role : 0,
          coverage_per_place:
            r.success_rate *
            (1 - r.annual_attrition) ** (t.engagement_months / 12),
          success_rate: r.success_rate,
          annual_attrition: r.annual_attrition,
          assessment_months: t.engagement_months,
          start_month: Math.max(0, start),
          ready_month: t.deadline_month,
          checkpoint_coverage_per_place:
            r.success_rate *
            (1 - r.annual_attrition) **
              (Math.min(p.retention_checkpoint_months, t.engagement_months) /
                12),
          public_transition_gbp: pub,
          employer_transition_gbp: up - pub,
          mentor_hours: r.mentor_hours,
          transition_pv_gbp: transition,
          employment_or_contract_pv_gbp: pay,
          resource_pv_gbp: transition + pay,
        });
      }),
    );
    return result;
  }
  function problem(w, ts, cs) {
    const n = cs.length,
      k = ts.length,
      p = w.programme,
      matrix = [],
      upper = [],
      labels = [];
    const row = (a, b, c) => {
      matrix.push(a);
      upper.push(b);
      labels.push(c);
    };
    for (const [field, key] of [
      ["employer_transition_gbp", "employer_transition_budget_gbp"],
      ["public_transition_gbp", "public_transition_budget_gbp"],
      ["mentor_hours", "mentor_hours_available"],
    ])
      row([...cs.map((c) => c[field]), ...Array(k).fill(0)], p[key], key);
    for (const [path, cap] of Object.entries(p.pathway_capacity))
      row(
        [...cs.map((c) => (c.pathway === path ? 1 : 0)), ...Array(k).fill(0)],
        cap,
        "capacity_" + path,
      );
    ts.forEach((t, i) => {
      const a = [
        ...cs.map((c) => (c.target_index === i ? -c.coverage_per_place : 0)),
        ...Array(k).fill(0),
      ];
      a[n + i] = -1;
      row(a, -t.required_fte, "coverage_" + t.id);
    });
    return {
      matrix,
      upper,
      constraint_labels: labels,
      lower_bounds: Array(n + k).fill(0),
      upper_bounds: [
        ...cs.map((c) => c.maximum_places),
        ...ts.map((t) => t.required_fte),
      ],
      integrality: [...Array(n).fill(1), ...Array(k).fill(0)],
      critical_objective: [
        ...Array(n).fill(0),
        ...ts.map((t) => (t.critical ? 1 : 0)),
      ],
      all_objective: [...Array(n).fill(0), ...Array(k).fill(1)],
      cost_objective: [
        ...cs.map((c) => c.resource_pv_gbp / 1000),
        ...Array(k).fill(0),
      ],
    };
  }
  function lp(p, obj, rows, limits) {
    const expression = (a) =>
      a
        .map((v, i) =>
          v ? `${v >= 0 ? "+" : "-"} ${Math.abs(v).toPrecision(16)} x${i}` : "",
        )
        .filter(Boolean)
        .join(" ") || "0 x0";
    return (
      "Minimize\n obj: " +
      expression(obj) +
      "\nSubject To\n" +
      rows
        .map(
          (r, i) => ` c${i}: ${expression(r)} <= ${limits[i].toPrecision(16)}`,
        )
        .join("\n") +
      "\nBounds\n" +
      p.upper_bounds
        .map((v, i) => ` 0 <= x${i} <= ${v.toPrecision(16)}`)
        .join("\n") +
      "\nGenerals\n " +
      p.integrality
        .map((v, i) => (v ? "x" + i : ""))
        .filter(Boolean)
        .join(" ") +
      "\nEnd\n"
    );
  }
  function solve(p, highs) {
    const rows = clone(p.matrix),
      limits = [...p.upper],
      diagnostics = [];
    let vector;
    for (const name of [
      "critical_objective",
      "all_objective",
      "cost_objective",
    ]) {
      const o = p[name],
        r = highs.solve(lp(p, o, rows, limits), {
          output_flag: false,
          time_limit: 15,
          mip_rel_gap: 1e-9,
        });
      if (r.Status !== "Optimal")
        throw Error(
          "Solver did not reach an optimum: " + r.Status + " (" + name + ")",
        );
      vector = o.map((_, i) => r.Columns["x" + i]?.Primal ?? 0);
      const value = dot(o, vector);
      diagnostics.push({ stage: name, status: "optimal", objective: value });
      if (name !== "cost_objective") {
        rows.push(o);
        limits.push(value + 1e-7);
      }
    }
    const violation = Math.max(
      0,
      ...rows.map((r, i) => dot(r, vector) - limits[i]),
    );
    if (violation > 1e-5)
      throw Error("Solver constraint residual exceeds tolerance");
    for (let i = 0; i < vector.length; i++)
      if (
        vector[i] < -1e-6 ||
        vector[i] > p.upper_bounds[i] + 1e-5 ||
        (p.integrality[i] && Math.abs(vector[i] - Math.round(vector[i])) > 1e-5)
      )
        throw Error("Invalid solver bounds/integrality");
    return { vector, diagnostics, violation };
  }
  function summary(w, ts, cs, sol) {
    const coverage = ts.map(() => 0),
      selected = [];
    let employer = 0,
      pub = 0,
      mentor = 0,
      pv = 0;
    cs.forEach((c, j) => {
      const places = Math.round(sol.vector[j]);
      if (!places) return;
      const qualified = places * c.coverage_per_place;
      coverage[c.target_index] += qualified;
      employer += places * c.employer_transition_gbp;
      pub += places * c.public_transition_gbp;
      mentor += places * c.mentor_hours;
      pv += places * c.resource_pv_gbp;
      selected.push({ ...c, places, expected_retained_fte: qualified });
    });
    const roles = ts.map((t, i) => ({
        ...t,
        expected_retained_capacity_fte: coverage[i],
        expected_gap_fte: Math.max(0, t.required_fte - coverage[i]),
      })),
      gap = sum(roles.map((r) => r.expected_gap_fte)),
      covered = sum(roles.map((r, i) => Math.min(r.required_fte, coverage[i]))),
      supported = sum(
        ts.map((t, i) =>
          Math.min(
            t.required_fte,
            sum(
              selected
                .filter(
                  (c) => c.target_index === i && c.public_transition_gbp > 0,
                )
                .map((c) => c.expected_retained_fte),
            ),
          ),
        ),
      ),
      months = [];
    ts.forEach((t, i) => {
      for (let month = 0; month <= t.engagement_months; month++) {
        const available = sum(
          selected
            .filter((c) => c.target_index === i)
            .map(
              (c) =>
                c.places *
                c.success_rate *
                (1 - c.annual_attrition) ** (month / 12),
            ),
        );
        months.push({
          target_id: t.id,
          project_month: t.deadline_month + month,
          months_since_readiness: month,
          required_service_fte: t.required_fte,
          expected_capacity_fte: available,
          expected_gap_fte: Math.max(0, t.required_fte - available),
        });
      }
    });
    return {
      status: gap < 1e-5 ? "expected_targets_covered" : "expected_gaps_remain",
      selected,
      roles,
      required_role_period_fte: sum(ts.map((t) => t.required_fte)),
      covered_role_period_fte: covered,
      expected_gap_fte: gap,
      critical_gap_fte: sum(
        roles.filter((r) => r.critical).map((r) => r.expected_gap_fte),
      ),
      employer_transition_gbp: employer,
      public_transition_gbp: pub,
      mentor_hours: mentor,
      resource_pv_gbp: pv,
      transition_cost_per_covered_fte_gbp: covered
        ? (employer + pub) / covered
        : null,
      public_supported_retained_capacity_fte: supported,
      public_cost_per_supported_capacity_fte_gbp: supported
        ? pub / supported
        : null,
      coverage_months: months,
      solver: sol.diagnostics,
      max_constraint_violation: sol.violation,
      units_note:
        "Disjoint occupation-period service capacities, not unique people or net new jobs. Expected qualification/retention is not safety clearance.",
    };
  }
  function build(w, m) {
    const delivery = demand(w, m),
      staffing = roster(w),
      ts = targets(w, delivery, staffing, m);
    return { delivery, staffing, targets: ts };
  }
  function run(w, m, highs, allowed) {
    const b = build(w, m),
      cs = candidates(w, b.targets, allowed),
      p = problem(w, b.targets, cs),
      allocation = summary(w, b.targets, cs, solve(p, highs)),
      g = w.guarantee_stress;
    return {
      schema_version: "workforce.v1",
      model_version: "0.2.0",
      status: "conditional_scenario_result",
      workspace: clone(w),
      ...b,
      allocation,
      operating_required_service_fte: sum(
        b.staffing.map((r) => r.required_service_fte),
      ),
      guarantee_stress: {
        face_value_gbp_m: 202,
        tranche_gbp_m: 252.5,
        facility_gbp_m_approximately: 300,
        coverage_fraction_of_tranche: 0.8,
        default_probability_scenario: g.default_probability,
        loss_given_default_scenario: g.loss_given_default,
        undiscounted_loss_illustration_gbp_m:
          202 * g.default_probability * g.loss_given_default,
        actual_expected_fiscal_cost: null,
        social_npv: null,
        benefit_cost_ratio: null,
      },
    };
  }
  function variants(w) {
    const none = clone(w),
      hire = clone(w),
      mixed = clone(w),
      phased = clone(w);
    none.name = "No workforce programme";
    Object.keys(none.programme.pathway_capacity).forEach(
      (k) => (none.programme.pathway_capacity[k] = 0),
    );
    hire.name = "Hire and contract only";
    phased.name =
      w.economic_scenario.construction_years < 5
        ? "Phased launch (+12 months)"
        : "Phased launch (5-year duration cap; unchanged)";
    phased.economic_scenario.construction_years = Math.min(
      5,
      phased.economic_scenario.construction_years + 1,
    );
    return [
      [none, null],
      [hire, ["hire", "contract"]],
      [mixed, null],
      [phased, null],
    ];
  }
  function comparison(results) {
    return results.map((r) => ({
      option: r.option || r.workspace.name,
      construction_years: r.workspace.economic_scenario.construction_years,
      required_role_period_fte: r.allocation.required_role_period_fte,
      expected_gap_fte: r.allocation.expected_gap_fte,
      critical_gap_fte: r.allocation.critical_gap_fte,
      employer_transition_gbp: r.allocation.employer_transition_gbp,
      public_transition_gbp: r.allocation.public_transition_gbp,
      resource_pv_gbp: r.allocation.resource_pv_gbp,
      peak_build_fte: r.delivery.peak_monthly_fte,
      operating_service_fte: r.operating_required_service_fte,
    }));
  }
  return {
    clone,
    validate,
    build,
    candidates,
    problem,
    solve,
    run,
    variants,
    comparison,
  };
})();
if (typeof module !== "undefined") module.exports = Workforce;
