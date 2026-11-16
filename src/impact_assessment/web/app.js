/* Browser calculator uses the same bundled Leontief inverse as the Python model.
   Controls alter final demand, never the technical coefficients. No network calls. */
"use strict";
const D=window.IMPACT_DATA,M=D.model;
const el=id=>document.getElementById(id);
const fmt=(n,d=0)=>new Intl.NumberFormat("en-GB",{maximumFractionDigits:d,minimumFractionDigits:d}).format(n);
const sum=a=>a.reduce((x,y)=>x+y,0);
const dot=(a,b)=>sum(a.map((x,i)=>x*b[i]));
const multiply=(a,b)=>a.map(row=>dot(row,b));
const copy=x=>JSON.parse(JSON.stringify(x));
let current, phase="construction";
function calculate(s){
  const f=M.codes.map(()=>0),of=M.codes.map(()=>0);
  for(const r of s.capital_components)f[M.codes.indexOf(r.industry)]+=s.capital_gbp_m*r.share*r.capture;
  for(const r of s.operating_procurement)of[M.codes.indexOf(r.industry)]+=r.gbp_m*r.capture;
  const mwh=s.it_load_mw*8760*s.load_factor*s.pue;
  of[M.codes.indexOf("35.1")]=mwh*s.electricity_io_valuation_gbp_per_mwh/1e6*s.electricity_capture;
  const cx=multiply(M.leontief,f),ox=multiply(M.leontief,of);
  const cJobs=cx.map((v,i)=>v*M.employment[i]),oJobs=ox.map((v,i)=>v*M.employment[i]);
  const occ=M.occupation_codes.map((code,j)=>{
    const cy=dot(cJobs,M.staffing.map(row=>row[j])),supplier=dot(oJobs,M.staffing.map(row=>row[j]));
    const onsite=s.onsite_fte*(s.onsite_roles.find(r=>r.soc2020===code)?.share||0);
    return {soc2020:code,label:M.occupation_labels[j],construction_job_years:cy,construction_annual_fte:cy/s.construction_years,onsite_fte:onsite,operating_supplier_fte:supplier,operating_total_fte:supplier+onsite,uk_demand_status_2025:M.demand_status[j]};
  });
  const cTotal=sum(cJobs),oTotal=sum(oJobs)+s.onsite_fte;
  const electricalRate=D.supply.find(r=>r.framework==="Electrical Installation").achievement_rate;
  const onsiteFor=codes=>sum(occ.filter(r=>codes.includes(r.soc2020)).map(r=>r.onsite_fte));
  const policies=[
    {name:"Incumbent IT conversion",seats:60,cost:240000,months:6,expected:60*.85*.6,demand:onsiteFor(["3131","2137"]),note:"60 seats × £4,000; 85% completion and 60% project matching assumed. Validate provider places and candidates."},
    {name:"Electrical apprenticeship cohort",seats:80,cost:1440000,months:48,expected:80*electricalRate*.6,demand:onsiteFor(["5241"]),note:"80 seats × £18,000; SDS achievement/leaver ratio used as a planning proxy, with 60% project matching assumed. Readiness takes an assumed 48 months."},
    {name:"Experienced-worker recruitment",seats:30,cost:180000,months:3,expected:30*.7,demand:onsiteFor(["5241","5225"]),note:"30 candidates × £6,000; 70% matching assumed. Confirm safety competence, retention and relocation requirements."}
  ].map(p=>({...p,onTime:p.months<=s.construction_years*12?Math.min(p.expected,p.demand):0}));
  return {scenario:s,f,cx,ox,cJobs,oJobs,occ,cTotal,oTotal,mwh,policies,
    retained:sum(f),cDirect:dot(M.employment,f),cGva:dot(M.gva,cx),cOutput:sum(cx),cIncome:dot(M.income,cx),oSupplier:sum(oJobs),oOutput:sum(ox),oGva:dot(M.gva,ox),
    electricityBill:mwh*s.electricity_gbp_per_mwh/1e6,
    constructionUnallocated:Math.max(0,cTotal-sum(occ.map(r=>r.construction_job_years))),operationUnallocated:Math.max(0,sum(oJobs)-sum(occ.map(r=>r.operating_supplier_fte)))};
}
function inputs(){
  const s=copy(D.scenario);
  s.capital_gbp_m=+el("capital").value;s.construction_years=+el("years").value;s.onsite_fte=+el("onsite").value;
  s.electricity_gbp_per_mwh=+el("power").value;
  s.capital_components.find(r=>r.industry==="41-43").capture=+el("capture").value/100;
  s.capital_components.find(r=>r.industry==="26").capture=+el("equipment").value/100;
  return s;
}
function timeline(r){
  const s=r.scenario,values=[...Array(s.construction_years).fill(r.cTotal/s.construction_years),...Array(s.operating_years).fill(r.oTotal)];
  const max=Math.max(...values,1);
  el("timeline").innerHTML=`<div class="timeline" role="img" aria-label="${s.construction_years} construction years at ${fmt(r.cTotal/s.construction_years)} annual FTE, then ${s.operating_years} operating years at ${fmt(r.oTotal)} annual FTE">${values.map((v,i)=>`<div class="time-col"><div class="time-bar ${i<s.construction_years?"build":""}" style="height:${v/max*85}%"><span>${i===0||i===s.construction_years?fmt(v):""}</span></div></div>`).join("")}</div><div class="year-labels">${values.map((_,i)=>`<span>${i+1}</span>`).join("")}</div><div class="legend"><span><b class="build"></b>Construction</span><span><b></b>Operation</span><span>Project year →</span></div>`;
}
function occupationView(){
  if(!current)return;
  const r=current,build=phase==="construction",key=build?"construction_annual_fte":"operating_total_fte";
  el("occupation-unit").textContent=build?"Annual average FTE":"Annual operating FTE";
  el("occupation-note").textContent=build?"Largest allocations of construction work, including Scottish suppliers. UK grouped-industry staffing shares proxy Scottish FTE composition.":"On-site scenario roles plus Scottish procurement suppliers. On-site staffing shares are explicit assumptions.";
  const rows=[...r.occ].sort((a,b)=>b[key]-a[key]).slice(0,15);
  el("occupations").replaceChildren();
  for(const row of rows){
    const tr=document.createElement("tr"),label=document.createElement("td"),value=document.createElement("td"),status=document.createElement("td");
    label.textContent=row.label;const code=document.createElement("span");code.className="soc";code.textContent=row.soc2020;label.append(code);
    value.textContent=fmt(row[key],1);const badge=document.createElement("span");badge.className="demand"+(row.uk_demand_status_2025==="Critical demand"?" critical":"");badge.textContent=row.uk_demand_status_2025;status.append(badge);tr.append(label,value,status);el("occupations").append(tr);
  }
  el("coverage").textContent=`${fmt(build?r.constructionUnallocated/r.scenario.construction_years:r.operationUnallocated,2)} FTE remains unallocated in this phase. UK context is not a local shortage measure; employment stocks are not available labor supply.`;
}
function render(){
  const s=inputs(),r=calculate(s);current=r;window.currentImpact=r;
  el("capital-value").textContent=`£${fmt(s.capital_gbp_m)}m`;
  el("years-value").textContent=`${s.construction_years} years`;
  el("capture-value").textContent=`${el("capture").value}%`;
  el("equipment-value").textContent=`${el("equipment").value}%`;
  el("onsite-value").textContent=`${fmt(s.onsite_fte)} FTE`;
  el("power-value").textContent=`£${fmt(s.electricity_gbp_per_mwh)}/MWh`;
  el("build-jobs").textContent=fmt(r.cTotal);el("build-annual").textContent=`${fmt(r.cTotal/s.construction_years)} average annual FTE · ${s.construction_years} years`;
  el("op-jobs").textContent=fmt(r.oTotal);el("op-split").textContent=`${fmt(s.onsite_fte)} on-site + ${fmt(r.oSupplier)} supplier FTE`;
  el("retained").textContent=`£${fmt(r.retained)}m`;el("external").textContent=`£${fmt(s.capital_gbp_m-r.retained)}m initial external procurement`;
  timeline(r);
  el("effects").innerHTML=[
    ["Gross output",`£${fmt(r.cOutput,1)}m`,"Includes intermediate sales"],
    ["Gross value added",`£${fmt(r.cGva,1)}m`,"A component of output"],
    ["Employee compensation",`£${fmt(r.cIncome,1)}m`,"Not an occupational salary"],
    ["Direct / indirect work",`${fmt(r.cDirect)} / ${fmt(r.cTotal-r.cDirect)}`,"FTE job-years; total already includes direct"],
    ["Operating electricity bill",`£${fmt(r.electricityBill,1)}m/year`,"Contract price changes cost; physical load and jobs stay fixed"]
  ].map(x=>`<div class="effect-row"><div>${x[0]}<small>${x[2]}</small></div><strong>${x[1]}</strong></div>`).join("");
  const inds=M.codes.map((code,i)=>({label:M.labels[i],value:r.cJobs[i]})).sort((a,b)=>b.value-a.value).slice(0,5),max=inds[0].value||1;
  el("industries").innerHTML=inds.map(x=>`<div class="industry-row"><div class="bar-label"><span>${x.label}</span><strong>${fmt(x.value)}</strong></div><div class="bar-track"><span style="width:${x.value/max*100}%"></span></div></div>`).join("");
  occupationView();
  el("policies").innerHTML=r.policies.map(p=>`<article class="policy-card"><div class="policy-head"><h3>${p.name}</h3><span class="tag ${p.months>s.construction_years*12?"late":""}">${p.months>s.construction_years*12?"After launch":"Ready by launch"}</span></div><div class="policy-grid"><div><strong>£${fmt(p.cost/1000)}k</strong><span>Scenario cohort cost</span></div><div><strong>${fmt(p.onTime,1)}</strong><span>On-time matches, capped at role demand</span></div><div><strong>${p.months} months</strong><span>Readiness · launch at ${s.construction_years*12} months</span></div></div><p>${p.note} Expected matches before timing/demand caps: ${fmt(p.expected,1)}. Cost per on-time match: ${p.onTime?"£"+fmt(p.cost/p.onTime):"unavailable (zero on-time matches)"}.</p></article>`).join("");
}
function download(name,text,type){
  const a=document.createElement("a"),url=URL.createObjectURL(new Blob([text],{type}));a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function exportScenario(){download("impact-scenario.json",JSON.stringify(current.scenario,null,2)+"\n","application/json");}
function csv(rows){const keys=Object.keys(rows[0]);const q=v=>`"${String(v??"").replaceAll('"','""')}"`;return [keys,...rows.map(r=>keys.map(k=>r[k]))].map(row=>row.map(q).join(",")).join("\r\n")+"\r\n";}
for(const id of ["capital","years","capture","equipment","onsite","power"])el(id).addEventListener("input",render);
el("reset").addEventListener("click",()=>{for(const [id,v] of Object.entries({capital:1000,years:3,capture:90,equipment:2,onsite:120,power:100}))el(id).value=v;render();});
for(const b of document.querySelectorAll("[data-view]"))b.addEventListener("click",()=>{for(const t of document.querySelectorAll("[data-view]")){const selected=t===b;t.classList.toggle("active",selected);t.setAttribute("aria-selected",String(selected));}for(const v of document.querySelectorAll(".view"))v.hidden=v.id!==b.dataset.view;});
for(const b of document.querySelectorAll("[data-phase]"))b.addEventListener("click",()=>{phase=b.dataset.phase;for(const t of document.querySelectorAll("[data-phase]"))t.classList.toggle("active",t===b);occupationView();});
el("export-scenario").addEventListener("click",exportScenario);el("export-scenario-2").addEventListener("click",exportScenario);
el("export-occupations").addEventListener("click",()=>download("impact-occupations.csv",csv(current.occ),"text/csv;charset=utf-8"));
el("export-brief").addEventListener("click",()=>{const r=current,s=r.scenario;download("impact-current-brief.md",`# Scotland AI data-centre investment: current scenario\n\nIndependent portfolio case by Haojian Dui. Model 0.1.0.\n\nAll money: GBP million, 2022 basic prices. Type I direct + indirect effects; household-induced effects excluded.\n\n- Capital: £${fmt(s.capital_gbp_m)}m; ${s.construction_years} construction years.\n- Scottish production capture: £${fmt(r.retained,1)}m.\n- Construction: ${fmt(r.cTotal,1)} FTE job-years, or ${fmt(r.cTotal/s.construction_years,1)} annual average FTE.\n- Construction GVA: £${fmt(r.cGva,1)}m; gross output £${fmt(r.cOutput,1)}m.\n- Operation: ${fmt(r.oTotal,1)} annual FTE = ${fmt(s.onsite_fte)} on-site scenario FTE + ${fmt(r.oSupplier,1)} supplier FTE.\n- Electricity: ${fmt(r.mwh/1000,1)} GWh/year at £${s.electricity_gbp_per_mwh}/MWh.\n\nSecure experienced electrical/cooling workers and reserve conversion-training places against verified roles. New apprenticeships take longer; evaluate their readiness against the launch date.\n\nUK grouped staffing shares proxy Scottish FTE composition. Training achievements are not available recruits. Gross activity is not net additional employment or net welfare. Project inputs are assumptions. Download the scenario JSON for complete inputs.\n\nOfficial source links and reproducible workflow: https://github.com/JoeDHJ/economic-impact-assessment\n`,"text/markdown;charset=utf-8");});
el("supply").innerHTML=D.supply.slice(0,5).map(r=>`<tr><td>${r.framework}</td><td>${fmt(r.starts)}</td><td>${fmt(r.in_training)}</td><td>${fmt(r.achievements)}</td></tr>`).join("");
el("validation").textContent=`The reconstructed inverse differs from the published inverse by at most ${M.validation.inverse_max_error.toExponential(2)}; employment effects differ by at most ${M.validation.employment_effect_max_error.toExponential(2)} FTE per £m. Column accounting residual is below £0.01.`;
render();
el("wage-reference").textContent=`Observed Scottish median gross weekly pay for full-time employee jobs: £${fmt(D.wages.value,2)} in April 2025 (provisional, nominal GBP). This all-occupation context is separate from 2022-price model inputs.`; el("skill-references").innerHTML=D.skills.map(r=>`<tr><td>${r.soc2020}<span class="soc">${r.mapping_type}</span></td><td><a href="${r.source_url}">${r.skill_tags_editorial}</a></td></tr>`).join("");
