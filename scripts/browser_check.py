"""Check rendered dashboard, Python/browser numerical parity and downloads."""
import argparse
import json
from pathlib import Path
import tempfile
from playwright.sync_api import sync_playwright
from impact_assessment.case import default_scenario,run_case
from impact_assessment.site import build_site

ROOT=Path(__file__).resolve().parents[1]


def check(channel=None,screenshots=False):
    with tempfile.TemporaryDirectory(prefix="impact-browser-") as tmp:
        site=Path(tmp)/"site";build_site(site)
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,**({"channel":channel} if channel else {}))
            page=browser.new_page(viewport={"width":1440,"height":1050},device_scale_factor=1)
            errors=[];page.on("pageerror",lambda error:errors.append(str(error)))
            page.goto((site/"index.html").as_uri());page.wait_for_function("window.currentImpact !== undefined")
            base=run_case();calc=page.evaluate("({c:currentImpact.cTotal,o:currentImpact.oTotal,g:currentImpact.cGva})")
            assert abs(calc["c"]-base["construction"]["job_years_fte"]["total"])<1e-7
            assert abs(calc["o"]-base["operations"]["total_annual_fte"])<1e-7
            assert abs(calc["g"]-base["construction"]["gva_gbp_m"]["total"])<1e-7
            assert page.locator("#build-jobs").inner_text()=="3,981"
            if screenshots:
                folder=ROOT/"docs/screenshots";folder.mkdir(exist_ok=True)
                page.screenshot(path=str(folder/"desktop-impact.png"),full_page=True)
            for view in ("workforce","policy","evidence","impact"):
                page.locator(f"#tab-{view}").click();assert page.locator(f"#{view}").is_visible()
            for key,value in {"capital":1500,"years":4,"capture":70,"equipment":10,"onsite":180,"power":140}.items():
                page.locator(f"#{key}").fill(str(value));page.locator(f"#{key}").dispatch_event("input")
            s=default_scenario();s.update(capital_gbp_m=1500,construction_years=4,onsite_fte=180,electricity_gbp_per_mwh=140)
            for row in s["capital_components"]:
                if row["industry"]=="41-43":row["capture"]=.7
                if row["industry"]=="26":row["capture"]=.1
            expected=run_case(s)
            actual=page.evaluate("({c:currentImpact.cTotal,o:currentImpact.oTotal,occ:currentImpact.occ,policies:currentImpact.policies})")
            assert abs(actual["c"]-expected["construction"]["job_years_fte"]["total"])<1e-7
            assert abs(actual["o"]-expected["operations"]["total_annual_fte"])<1e-7
            for a,b in zip(actual["occ"],expected["occupations"]):
                assert abs(a["operating_total_fte"]-b["operating_total_fte"])<1e-8
                assert abs(a["construction_job_years"]-b["construction_job_years"])<1e-8
            assert actual["policies"][1]["onTime"]==27
            with page.expect_download() as download:
                page.locator("#export-scenario").click()
            exported=json.loads(Path(download.value.path()).read_text(encoding="utf8"))
            assert run_case(exported)["operations"]["total_annual_fte"]==expected["operations"]["total_annual_fte"]
            page.locator("#tab-workforce").click()
            with page.expect_download() as download:page.locator("#export-occupations").click()
            assert Path(download.value.path()).read_text(encoding="utf8").count("\n")==413
            page.locator("#tab-impact").click()
            with page.expect_download() as download:page.locator("#export-brief").click()
            brief=Path(download.value.path()).read_text(encoding="utf8")
            assert "1,500" in brief and "180 on-site" in brief
            page.locator("#reset").click();assert page.locator("#build-jobs").inner_text()=="3,981"
            page.set_viewport_size({"width":390,"height":844})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            if screenshots:page.screenshot(path=str(folder/"mobile-impact.png"),full_page=True)
            for view in ("workforce","policy","evidence"):
                page.locator(f"#tab-{view}").click()
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                if screenshots and view=="workforce":page.screenshot(path=str(folder/"mobile-workforce.png"),full_page=True)
            assert not errors,errors
            browser.close()
            print(json.dumps({"browser":"chromium"+("/"+channel if channel else ""),"desktop":"1440x1050","mobile":"390x844","exports":["scenario JSON","occupation CSV","current Markdown brief"],"numeric_parity":"all 412 occupation rows and headline totals","console_errors":errors},indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--channel");p.add_argument("--screenshots",action="store_true")
    args=p.parse_args();check(args.channel,args.screenshots)
