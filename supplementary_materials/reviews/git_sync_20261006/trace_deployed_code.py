"""Read-only provenance audit against the already-recorded production manifest.

Run from any directory with Python and the existing paracloud-bscc-a8 SSH alias.
Only explicitly listed project source files are read remotely; no solver runs.
Writes code_provenance.json and production_to_local.patch beside this script.
Raw retrieved copies remain in the ignored .codex_tmp directory for inspection.
"""
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MANIFEST = HERE / "cloud_versions.json"
SNAPSHOT = ROOT / ".codex_tmp" / "production_provenance_20261006"
REMOTE = r'''
import base64, hashlib, json, sys
from pathlib import Path
request = json.loads(sys.argv[1]); out = {}
for label, spec in request.items():
    root = Path(spec['root']); files = {}
    for name in spec['files']:
        p = root / name
        if '..' in Path(name).parts or Path(name).is_absolute():
            raise ValueError('Unsafe source path')
        raw = p.read_bytes()
        files[name] = dict(sha256=hashlib.sha256(raw).hexdigest(),
                          data=base64.b64encode(raw).decode('ascii'))
    out[label] = files
print(json.dumps(out))
'''


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    import base64
    manifests = json.loads(MANIFEST.read_text(encoding="utf-8"))
    prod = manifests["production2050"]
    changed = [p for p, h in prod["files"].items()
               if (ROOT / p).is_file() and digest((ROOT / p).read_bytes()) != h]
    request = {"production2050": {"root": prod["root"], "files": changed},
               "factor_F": {"root": manifests["factor_F"]["root"],
                            "files": ["scripts/run_cispo_2030_full_year.py"]}}
    run = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=12",
         "paracloud-bscc-a8", "python3 - " + shlex.quote(json.dumps(request))],
        input=REMOTE, encoding="utf-8", capture_output=True, timeout=60,
        check=True)
    retrieved = json.loads(run.stdout)
    patches, details = [], []
    for label, files in retrieved.items():
        for name, record in files.items():
            old = base64.b64decode(record["data"])
            expected = manifests[label]["files"][name]
            if digest(old) != expected or record["sha256"] != expected:
                raise ValueError("Remote source drift: " + label + "/" + name)
            target = SNAPSHOT / label / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(old)
            new = (ROOT / name).read_bytes()
            lines = list(difflib.unified_diff(
                [s + "\n" for s in old.decode("utf-8-sig").splitlines()],
                [s + "\n" for s in new.decode("utf-8-sig").splitlines()],
                fromfile=label + "/" + name, tofile="local/" + name, n=3))
            patches.extend(lines)
            details.append(dict(baseline=label, path=name, baseline_sha256=expected,
                                local_sha256=digest(new),
                                additions=sum(s.startswith("+") and not s.startswith("+++") for s in lines),
                                deletions=sum(s.startswith("-") and not s.startswith("---") for s in lines)))
    core = {}
    for folder in ("cispo_model", "config", "scripts", "tests"):
        for p in (ROOT / folder).rglob("*"):
            if p.is_file() and p.suffix in {".py", ".json", ".csv", ".sh", ".sbatch"}:
                core[p.relative_to(ROOT).as_posix()] = digest(p.read_bytes())
    commit_files = subprocess.check_output(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "865e966"],
        cwd=ROOT, text=True).splitlines()
    production_matches = [p for p in commit_files if p in prod["files"]
                          and p in core and prod["files"][p] == core[p]]
    frozen = ROOT / "supplementary_materials/reviews/factor_pair_8760_20261005/frozen_local"
    frozen_matches = {p: digest((frozen / p).read_bytes()) == prod["files"][p]
                      for p in changed if p.startswith("cispo_model/")}
    regression = json.loads((ROOT / "supplementary_materials/reviews/validation_coordination_20261005/"
                             "unittest_verified_20261005T185140Z.json").read_text(encoding="utf-8"))
    tested = regression["source_sha256_after"]
    tested_drift = [p for p, h in tested.items() if digest((ROOT / p).read_bytes()) != h]
    result = dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),
                  local_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  prior_manifest_sha256=digest(MANIFEST.read_bytes()),
                  remote_readback_matched_prior_manifest=True,
                  patch_line_endings="Normalized LF for review only; SHA256 values cover raw bytes",
                  frozen_pre_optin_model_matches_production=frozen_matches,
                  tested_source_count=len(tested), tested_source_drift=tested_drift,
                  production_root=prod["root"],
                  production_file_count=len(prod["files"]),
                  local_core_file_count=len(core),
                  same_shared_paths=[p for p, h in prod["files"].items() if core.get(p) == h],
                  missing_production_paths=[p for p in prod["files"] if p not in core],
                  local_only_paths=sorted(set(core) - set(prod["files"])),
                  changed_details=details,
                  commit_865e966_files_already_byte_identical_in_production=production_matches,
                  commit_865e966_files=commit_files)
    (HERE / "code_provenance.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (HERE / "production_to_local.patch").write_text("".join(patches), encoding="utf-8")
    print(json.dumps({"remote_manifest_match": True, "local_core": len(core),
                      "production_core": len(prod["files"]), "shared_identical": len(result["same_shared_paths"]),
                      "local_only": len(result["local_only_paths"]),
                      "commit_files_already_in_production": production_matches,
                      "changed_details": details}, indent=2))


if __name__ == "__main__":
    main()
