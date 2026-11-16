import argparse
import functools
import http.server
import json
from pathlib import Path
import sys
from .case import default_scenario, run_case
from .report import export_case
from .site import build_site
from .refresh import refresh


def main(argv=None):
    parser=argparse.ArgumentParser(description="Scottish regional investment impact and workforce assessment")
    parser.add_argument("--version",action="version",version="0.1.0")
    subs=parser.add_subparsers(dest="command",required=True)
    run=subs.add_parser("run",help="calculate case and write CSV, JSON and Markdown reports")
    run.add_argument("--scenario",type=Path);run.add_argument("--output",type=Path,default=Path("outputs"))
    subs.add_parser("validate",help="validate bundled official coefficients and base scenario")
    init=subs.add_parser("scenario",help="write an editable, complete scenario JSON")
    init.add_argument("--output",type=Path,default=Path("scenario.json"))
    update=subs.add_parser("refresh",help="download pinned official public source files")
    update.add_argument("--destination",type=Path,default=Path("data/public/sources"))
    update.add_argument("--overwrite",action="store_true",help="replace existing pinned source files")
    site=subs.add_parser("build-site",help="build an offline interactive dashboard")
    site.add_argument("--output",type=Path,default=Path("site"))
    serve=subs.add_parser("serve",help="serve a built dashboard on loopback only")
    serve.add_argument("--directory",type=Path,default=Path("site"));serve.add_argument("--port",type=int,default=8765)
    args=parser.parse_args(argv)
    try:
        if args.command=="run":
            scenario=json.loads(args.scenario.read_text(encoding="utf-8-sig")) if args.scenario else None
            if args.scenario and not isinstance(scenario,dict):
                raise ValueError("scenario file must contain a JSON object")
            r=export_case(args.output,scenario)
            print(json.dumps({"output":str(args.output.resolve()),"construction_fte_job_years":r["construction"]["job_years_fte"]["total"],"operating_annual_fte":r["operations"]["total_annual_fte"]},indent=2))
        elif args.command=="validate":
            r=run_case();print(json.dumps(r["diagnostics"],indent=2))
        elif args.command=="scenario":
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps(default_scenario(),indent=2)+"\n",encoding="utf-8")
            print(args.output.resolve())
        elif args.command=="refresh":
            print(json.dumps(refresh(args.destination,args.overwrite),indent=2))
        elif args.command=="build-site":
            build_site(args.output);print(args.output.resolve())
        elif args.command=="serve":
            if not (args.directory/"index.html").is_file():raise ValueError("build the dashboard first")
            handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(args.directory.resolve()))
            with http.server.ThreadingHTTPServer(("127.0.0.1",args.port),handler) as server:
                print(f"Dashboard: http://127.0.0.1:{args.port}",flush=True)
                try:server.serve_forever()
                except KeyboardInterrupt:pass
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(f"Error: {exc}",file=sys.stderr)
        return 2
    return 0


if __name__=="__main__":raise SystemExit(main())
