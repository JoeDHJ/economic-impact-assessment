"""Bundle selected reader-facing method notes so wheel-built sites keep links."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
for name in ("capability-and-interview.md","workforce-methodology.md","owner-rehearsal.md","employer-evidence.md"):
    (ROOT/"src/impact_assessment/data"/name).write_bytes((ROOT/"docs"/name).read_bytes())
print("Bundled four documentation assets")
