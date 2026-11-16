from pathlib import Path
from importlib.resources import files
import json
from .case import load_data, default_scenario, sensitivities
from .policy import supply_data, wage_data, skills_data
from .report import export_case
from .workforce import default_workspace, bundled
from .workforce_report import export_workspace


def build_site(output):
    path=Path(output);path.mkdir(parents=True,exist_ok=True)
    for asset in ("index.html","impact.html","style.css","app.js","workspace.css","workspace.js","workforce-core.js","workforce-worker.js"):
        path.joinpath(asset).write_text(files("impact_assessment").joinpath("web",asset).read_text(encoding="utf-8"),encoding="utf-8")
    r=export_case(path/"reports")
    payload={"model":load_data(),"scenario":default_scenario(),"base":r,"supply":supply_data(),"wages":wage_data(),"skills":skills_data(),"sensitivities":sensitivities()}
    # A classic script supports file:// use, with no fetch/CORS or external dependencies.
    path.joinpath("case-data.js").write_text("window.IMPACT_DATA="+json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(",",":"))+";\n",encoding="utf-8")
    vendor=path/"vendor";vendor.mkdir(exist_ok=True)
    for name in ("highs.js","highs.wasm","highs-js-LICENSE.txt","HiGHS-LICENSE.txt"):
        vendor.joinpath(name).write_bytes(files("impact_assessment").joinpath("web","vendor",name).read_bytes())
    workforce=export_workspace(path/"reports"/"workforce")
    data={"workspace":default_workspace(),"evidence":bundled("project-evidence.json"),"local":bundled("local-evidence.json"),"base":workforce}
    path.joinpath("workforce-data.js").write_text("window.WORKFORCE_DATA="+json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(",",":"))+";\n",encoding="utf8")
    for name in ("capability-and-interview.md","workforce-methodology.md","owner-rehearsal.md","employer-evidence.md"):
        path.joinpath("reports",name).write_bytes(files("impact_assessment").joinpath("data",name).read_bytes())
