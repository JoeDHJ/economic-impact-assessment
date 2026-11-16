"""Exercise the actual WASM solver, changed inputs, exports and narrow layouts."""
import argparse
import functools
import http.server
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright
from impact_assessment.workforce import default_workspace,run_workspace

ROOT=Path(__file__).resolve().parents[1]


def check(channel=None,screenshots=False,site=None):
    site=Path(site or ROOT/"site").resolve()
    handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(site))
    class Quiet(handler.func):
        def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(("127.0.0.1",0),functools.partial(Quiet,directory=str(site)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,**({"channel":channel} if channel else {}))
            page=browser.new_page(viewport={"width":1440,"height":1050})
            errors=[];page.on("pageerror",lambda e:errors.append(str(e)))
            page.goto(f"http://127.0.0.1:{server.server_port}")
            page.wait_for_function("window.currentWorkforce !== undefined")
            assert page.evaluate("""(()=>{const w=Workforce.clone(WORKFORCE_DATA.workspace);
                w.economic_scenario.capital_gbp_m=0;
                w.economic_scenario.capital_components=[{industry:'12',share:1,capture:1}];
                w.delivery.component_phase_weights={'12':[1,0,0,0]};
                Workforce.validate(w,WORKFORCE_DATA.workspace,IMPACT_DATA.model);
                w.economic_scenario.capital_gbp_m=1;
                try{Workforce.validate(w,WORKFORCE_DATA.workspace,IMPACT_DATA.model);return false}catch(e){return true}})()""")
            # Actual in-browser optimisation, not a precomputed lookup.
            page.locator("#run").click()
            page.wait_for_function("document.querySelector('#status').textContent.startsWith('Solved') || document.querySelector('#status').classList.contains('error')",timeout=180000)
            assert "Solved" in page.locator("#status").inner_text(),page.locator("#status").inner_text()
            baseline=run_workspace();actual=page.evaluate("window.currentWorkforce")
            parity(actual,baseline)
            print("Default browser MILP agrees with Python",flush=True)
            page.locator("#compare").click()
            page.wait_for_function("document.querySelector('#status').textContent.startsWith('Solved') || document.querySelector('#status').classList.contains('error')",timeout=180000)
            assert "Solved" in page.locator("#status").inner_text(),page.locator("#status").inner_text()
            options=page.evaluate("comparison");reference=page.evaluate("WORKFORCE_DATA.base.comparison")
            for row,ref in zip(options,reference):
                for key in ("expected_gap_fte","critical_gap_fte","resource_pv_gbp"):
                    assert abs(row[key]-ref[key])<max(1e-4,abs(ref[key])*1e-8)
            assert page.locator("#export-options").is_enabled()
            if screenshots:
                folder=ROOT/"docs/screenshots";folder.mkdir(exist_ok=True)
                page.evaluate("window.scrollTo(0,0)")
                page.screenshot(path=str(folder/"desktop-decision.png"),full_page=True)
            # Changed money, timing, task workload and multiplier retention.
            w=default_workspace();w["economic_scenario"]["construction_years"]=4
            w["economic_scenario"]["supplier_retention"]=.7
            w["programme"]["employer_transition_budget_gbp"]=400000
            w["programme"]["public_transition_budget_gbp"]=50000
            w["staffing"]["routine_workload_factor"]=.8
            page.locator("#import").set_input_files({"name":"changed.json","mimeType":"application/json","buffer":json.dumps(w).encode()})
            assert page.locator("#export-result").is_disabled()
            page.locator("#run").click()
            page.wait_for_function("document.querySelector('#status').textContent.startsWith('Solved') || document.querySelector('#status').classList.contains('error')",timeout=180000)
            assert "Solved" in page.locator("#status").inner_text(),page.locator("#status").inner_text()
            actual=page.evaluate("window.currentWorkforce");expected=run_workspace(w);parity(actual,expected)
            assert "Published default comparison" in page.locator("#comparison-note").inner_text()
            with page.expect_download() as dl:page.locator("#export-result").click()
            exported=json.loads(Path(dl.value.path()).read_text(encoding="utf8"));assert exported["workspace"]==w
            with page.expect_download() as dl:page.locator("#export-report").click()
            text=Path(dl.value.path()).read_text(encoding="utf8");assert "400,000" in text and "Only this current plan" in text
            page.locator('[data-view="workforce"]').click()
            with page.expect_download() as dl:page.locator("#export-months").click()
            assert Path(dl.value.path()).read_text(encoding="utf8").count("\n")==48*412+1
            # Full-input validation rejects bad imports and keeps last valid state.
            page.locator("#import").set_input_files({"name":"invalid.json","mimeType":"application/json","buffer":b'{"name":"bad"}'})
            assert "Import failed" in page.locator("#status").inner_text()
            page.locator("#reset").click()
            assert page.locator("#run").is_enabled()
            page.locator("details").evaluate("e=>e.open=true")
            page.locator("#advanced").fill("{}")
            assert page.locator("#run").is_disabled() and page.locator("#save").is_disabled()
            page.locator("#reset").click()
            assert page.locator("#run").is_enabled() and page.locator("#save").is_enabled()
            page.locator("#advanced").fill("{}")
            page.locator("#import").set_input_files({"name":"valid.json","mimeType":"application/json","buffer":json.dumps(default_workspace()).encode()})
            assert page.locator("#run").is_enabled() and page.locator("#save").is_enabled()
            page.locator("#reset").click()
            page.locator("#capital").fill("")
            assert page.locator("#inputs").evaluate("e=>!e.checkValidity()")
            assert page.evaluate("(()=>{try{readInputs();return false}catch(e){return true}})()")
            page.locator("#reset").click()
            page.locator("details").evaluate("e=>e.open=false")
            for width in (390,768,1440):
                page.set_viewport_size({"width":width,"height":844 if width==390 else 1050})
                for view in ("decision","workforce","evidence","method"):
                    page.locator(f'[data-view="{view}"]').click()
                    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"),(width,view)
                    if screenshots and width==390 and view in ("decision","workforce"):
                        page.screenshot(path=str(folder/f"mobile-{view}-v02.png"),full_page=True)
            assert not errors,errors
            browser.close()
            print(json.dumps({"default_and_changed_MILP":"Python/browser parity", "monthly_occupation_parity":"all months × 412 SOCs", "exports":"JSON, Markdown, monthly CSV", "widths":[390,768,1440],"page_errors":errors},indent=2))
    finally:server.shutdown();server.server_close()


def parity(actual,expected):
    for key in ("expected_gap_fte","critical_gap_fte","employer_transition_gbp","public_transition_gbp","mentor_hours","resource_pv_gbp"):
        assert abs(actual["allocation"][key]-expected["allocation"][key])<max(1e-4,abs(expected["allocation"][key])*1e-8),(key,actual["allocation"][key],expected["allocation"][key])
    for a,b in zip(actual["delivery"]["occupation_fte"],expected["delivery"]["occupation_fte"]):
        assert max(abs(x-y) for x,y in zip(a,b))<1e-7
    for a,b in zip(actual["targets"],expected["targets"]):assert abs(a["required_fte"]-b["required_fte"])<1e-7


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--channel");p.add_argument("--screenshots",action="store_true");p.add_argument("--site")
    args=p.parse_args();check(args.channel,args.screenshots,args.site)
