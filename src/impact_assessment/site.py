from pathlib import Path
from importlib.resources import files
import json
from .case import load_data, default_scenario, sensitivities
from .policy import supply_data, wage_data, skills_data
from .report import export_case


def build_site(output):
    path=Path(output);path.mkdir(parents=True,exist_ok=True)
    for asset in ("index.html","style.css","app.js"):
        path.joinpath(asset).write_text(files("impact_assessment").joinpath("web",asset).read_text(encoding="utf-8"),encoding="utf-8")
    r=export_case(path/"reports")
    payload={"model":load_data(),"scenario":default_scenario(),"base":r,"supply":supply_data(),"wages":wage_data(),"skills":skills_data(),"sensitivities":sensitivities()}
    # A classic script supports file:// use, with no fetch/CORS or external dependencies.
    path.joinpath("case-data.js").write_text("window.IMPACT_DATA="+json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(",",":"))+";\n",encoding="utf-8")
