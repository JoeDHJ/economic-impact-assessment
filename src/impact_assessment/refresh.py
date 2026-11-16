"""Download the pinned official public sources. Existing files are preserved by default."""
from datetime import datetime,timezone
from importlib.resources import files
from pathlib import Path
import json
import urllib.request


def refresh(destination, overwrite=False):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    manifest=json.loads(files("impact_assessment").joinpath("data/source-manifest.json").read_text(encoding="utf8"))
    records=[]
    for source in manifest["sources"]:
        path=destination/Path(source["path"]).name
        if path.exists() and not overwrite:
            records.append({"source_id":source["source_id"],"path":str(path),"status":"existing_preserved","file_bytes":path.stat().st_size})
            continue
        with urllib.request.urlopen(source["source_url"],timeout=45) as response:
            body=response.read(25_000_001)
        if len(body)>25_000_000 or len(body)<100:
            raise ValueError(f"unexpected file size for {source['source_id']}")
        if path.suffix==".xlsx" and body[:2]!=b"PK":raise ValueError("source returned a page instead of an Excel workbook")
        if path.suffix==".csv" and b"<html" in body[:1000].lower():raise ValueError("source returned a page instead of CSV")
        path.write_bytes(body)
        records.append({"source_id":source["source_id"],"source_url":source["source_url"],"path":str(path),"status":"downloaded","file_bytes":len(body),"retrieved_at":datetime.now(timezone.utc).isoformat()})
    (destination/"retrieval-record.json").write_text(json.dumps(records,indent=2)+"\n",encoding="utf8")
    return records
