"""Verify exact tested source/input identity and freeze this review's evidence."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(2**20),b""):h.update(b)
    return h.hexdigest()


def main():
    # Only a CLI range guard was appended after the completed runs. Reconstruct
    # the EXACT executed bytes, accepting them only if the run-time SHA agrees.
    source=(HERE/"run_screen_probe.py").read_text(encoding="utf-8")
    guard=('    if not (np.isfinite(a.margin) and a.margin >= 0 and 1 <= a.max_rounds <= 8):\n'
           '        p.error("Margin must be finite/nonnegative; pricing rounds must be between 1 and 8")\n')
    assert source.count(guard)==1
    executed=source.replace(guard,"").encode("utf-8")
    expected=json.loads((HERE/"local_case3_24_full/scope.json").read_text())["script_sha256"]
    assert hashlib.sha256(executed).hexdigest()==expected
    (HERE/"executed_probe_source.py").write_bytes(executed)
    original=json.loads((HERE/"experiment_manifest.json").read_text())
    checked=[]
    for e in original["files"]:
        rel=e["path"]
        if rel.startswith(("repo/cispo_model/","repo/config/")):
            p=ROOT/rel.removeprefix("repo/")
        elif rel.startswith("data/"):
            p=ROOT/rel
        else:continue
        assert digest(p)==e["sha256"],str(p)
        checked.append(rel)
    small=[p for p in HERE.rglob("*") if p.is_file() and p.suffix in {".py",".sh",".md",".json",".csv",".log",".txt"}
           and p.name!="delivery_manifest.json"]
    records=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(small)]
    decision=dict(status="MECHANISM_VALIDATED_LONG_HORIZON_SPEED_UNVERIFIED",hours_2016="NOT_STARTED_SSH_TUNNEL_UNAVAILABLE",
        production_changed=False,cloud_base_interrupted=False,physical_deletion="PENDING_USER_CONFIRMATION",
        git_head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        checked_unchanged_core_config_input_files=len(checked),executed_probe_sha256=expected,
        publication_accepted=False,scenario_priority="case3_thermal_ev_v5 independent 2030->2040->2050->2060")
    (HERE/"decision.json").write_text(json.dumps(decision,indent=2)+"\n",encoding="utf-8")
    manifest=dict(generated_at_utc=datetime.now(timezone.utc).isoformat(),decision=decision,files=records,
        candidate_package=dict(file="experiment_v2.tar.gz",bytes=(HERE/"experiment_v2.tar.gz").stat().st_size,
                               sha256=digest(HERE/"experiment_v2.tar.gz")))
    (HERE/"delivery_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(decision,indent=2))


if __name__=="__main__":main()
