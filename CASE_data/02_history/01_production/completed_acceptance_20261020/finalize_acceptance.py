"""Finalize two local, hash-verified acceptance ZIPs and exact T550 sidecars.

Requires completed T550 backups and offline assessments. Never changes frozen
outputs or candidate flags. Existing final package directories are refused.
"""
from pathlib import Path
from datetime import datetime, timezone
import base64
import hashlib
import json
import shutil
import subprocess
import zipfile
from collect_evidence import RELEASES
from assess_on_t550 import SSH

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def remote(code):
    process = subprocess.run(SSH + ["python3 -"], input=code, capture_output=True,
                             text=True, encoding="utf-8", timeout=120)
    if process.returncode:
        raise RuntimeError(process.stderr)
    return json.loads(process.stdout)


def main():
    assert all(not (HERE / "packages" / key).exists() for key in RELEASES)
    payload = remote("releases=" + repr(RELEASES) + "\n" + r'''
from pathlib import Path
import json,base64,hashlib
base=Path('/home/zz2/National_model_server/cloud_backup')
op=base/'_operations/20261020_base2060_case3_2030'
status=json.loads((op/'transfer_status.json').read_text())
assert status['status']=='COMPLETE', 'Wait for final backup verification; never restart transfer'
assert len(status['stages'])==6 and all(s['status']=='VERIFIED' for s in status['stages'])
plan=json.loads((op/'backup_plan.json').read_text())
result={}
for key,release in releases.items():
    root=base/release
    manifest=json.loads((root/'backup_manifest.json').read_text())
    expected=plan['releases'][release]['files']
    assert manifest['status']=='COMPLETE' and manifest['source_unchanged_after_transfer']
    assert manifest['files']==expected and not manifest['deferred_files']
    records={'backup_manifest.json':root/'backup_manifest.json'}
    records.update({'root_metadata/'+f['path']:root/f['path'] for f in expected
                    if not f['path'].startswith('output_8760/')})
    files={}
    for name,path in records.items():
        raw=path.read_bytes()
        assert len(raw)<32*1024*1024
        if name.startswith('root_metadata/'):
            item=next(f for f in expected if f['path']==name[len('root_metadata/'):])
            assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
        files[name]={'base64':base64.b64encode(raw).decode(),
                     'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
    result[key]={'files':files,'backup_directory':str(root)}
print(json.dumps({'status':status,'releases':result}))
''')
    collection = json.loads((HERE / "collection_manifest.json").read_text())
    sync = {}
    summaries = {}
    for key, release in RELEASES.items():
        evidence = HERE / "evidence" / key
        assessment_dir = HERE / "assessments" / key
        for name, item in payload["releases"][key]["files"].items():
            raw = base64.b64decode(item.pop("base64"))
            assert len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"]
            path = assessment_dir / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                assert path.read_bytes() == raw
            else:
                path.write_bytes(raw)
        assessment = json.loads((assessment_dir / "solution_qc_relative_v1.json").read_text())
        profile = assessment["acceptance_profiles"]["relative_v1"]
        qc = json.loads((evidence / "solution_qc.json").read_text())
        solve = json.loads((evidence / "solve_report.json").read_text())
        checkpoint = json.loads((evidence / "barrier_checkpoint/barrier_checkpoint_manifest.json").read_text())
        source = checkpoint["source"]
        archive = json.loads((evidence / "model_archive/archive_manifest.json").read_text())
        backup = json.loads((assessment_dir / "backup_manifest.json").read_text())
        members = {f["path"]: f for f in backup["files"]}
        for name, item in collection[key]["files"].items():
            path = evidence / name
            assert sha(path) == item["sha256"] == members["output_8760/" + name]["sha256"]
            assert path.stat().st_size == item["bytes"] == members["output_8760/" + name]["bytes"]
        for prefix, items in [
                ("model_archive/", archive["files"]),
                ("barrier_checkpoint/", checkpoint["vectors"].values())]:
            for item in items:
                backup_item = members["output_8760/" + prefix + item["path"]]
                assert item["sha256"] == backup_item["sha256"] and item["bytes"] == backup_item["bytes"]
        assert profile["scope"] == "FULL_YEAR" and profile["checks"]["reservoir_transition"]["disclosure_complete"]
        water = profile["checks"]["reservoir_transition"]
        assert abs(abs(water["station"]["residual_m3"]) - water["maximum_residual_m3"]) <= 1e-9
        assert water["station"]["active_storage_m3"] > 0
        assert 0 <= water["station"]["hour_index"] < 8760
        assert source["optimization_hours"] == 8760
        assert (source["planning_year"], source["scenario_id"]) == (
            (2060, "base") if key == "base2060" else (2030, "case3_thermal_ev_v5"))
        parameters = solve["solver_parameters"]
        assert all(parameters[n] == v for n, v in {
            "method": 2, "threads": 48, "crossover": 0,
            "barrier_convergence_tolerance": 1e-4, "numeric_focus": 2,
            "aggregate": 1 if key == "base2060" else 0}.items())
        record = dict(
            generated_at_utc=datetime.now(timezone.utc).isoformat(),
            acceptance_status=profile["status"],
            acceptance_scope="AUTHOR_DEFINED_TECHNICAL_QUALITY_REFERENCE",
            author_request="2026-10-20: assess Base2060 and Case3 2030 and retrieve local acceptance packages",
            prior_author_adoption="CASE3_SCREENED_STATE_ADOPTED_20261019" if key == "case3_2030"
                else "NO_NEW_AUTOMATIC_SCIENTIFIC_ADOPTION",
            source=source, assessment=profile,
            strict_status_preserved=qc["status"],
            strict_failed_checks=[k for k, v in qc["hard_checks"].items() if not v],
            source_result_manifest_sha256=sha(evidence / "result_manifest.json"),
            assessment_sha256=sha(assessment_dir / "solution_qc_relative_v1.json"),
            assessment_evidence_sha256=sha(assessment_dir / "evidence_manifest.json"),
            backup_manifest_sha256=sha(assessment_dir / "backup_manifest.json"),
            backup_status="COMPLETE_SHA_VERIFIED", backup_directory=payload["releases"][key]["backup_directory"],
            source_candidate_flags_unchanged=True, frozen_archive_unchanged=True)
        certificate_files = {}
        if key == "case3_2030":
            cert_dir = ROOT.parent / "claude_workspace/evidence/case3_2030_certificate_claude_20261019"
            identity_path = ROOT / "supplementary_materials/reviews/case3_2040_C2050_launch_20261019/certificate_identity_check.json"
            identity = json.loads(identity_path.read_text())
            assert sha(cert_dir / "screen_pricing_certificate.json") == identity["certificate_sha256"]
            assert sha(evidence / "model_archive/archive_manifest.json") == identity["identity"]["archive_manifest_sha256"]
            assert sha(evidence / "barrier_checkpoint/barrier_checkpoint_manifest.json") == identity["identity"]["checkpoint_manifest_sha256"]
            assert checkpoint["vectors"]["dual"]["sha256"] == identity["identity"]["barpi_sha256"]
            record["screening_certificate"] = {
                k: identity[k] for k in ["certificate_sha256", "B_million_cny",
                                        "B_over_objective", "near_optimality", "comparison"]}
            certificate_files = {f.name: f for f in cert_dir.iterdir() if f.is_file()}
            certificate_files["certificate_identity_check.json"] = identity_path
        record_path = assessment_dir / "acceptance_relative_v1.json"
        assert not record_path.exists()
        record_path.write_bytes(json_bytes(record))
        evidence_meta = json.loads((assessment_dir / "evidence_manifest.json").read_text())
        sync[evidence_meta["sidecar"] + "/acceptance_relative_v1.json"] = base64.b64encode(record_path.read_bytes()).decode()
        folder = HERE / "packages" / key
        folder.mkdir(parents=True)
        shutil.copytree(evidence, folder / "source_evidence")
        shutil.copytree(assessment_dir, folder / "assessment")
        for name, path in certificate_files.items():
            target = folder / "screening_certificate" / name
            target.parent.mkdir(exist_ok=True)
            shutil.copyfile(path, target)
        readme = (
            f"# {key} 本地验收包\n\n"
            f"当前扩展 relative_v1：{profile['status']}；原严格口径：{qc['status']}（保留）。\n\n"
            "source_evidence/ 为云端原始小文件，assessment/ 为 T550 离线评估与正式技术验收记录。\n"
            "逐省逐时功率平衡及水库残差由 T550 备份中的原始数组重算；水量平衡按作者规则暂缓，站点/小时/活动库容均披露。\n"
            "原模型、BarX/BarPi及完整逐时调度留在云端和已完成SHA核验的T550备份，本ZIP不含这些大文件。\n"
            f"T550目录：{payload['releases'][key]['backup_directory']}\n\n"
            "结果清单、模型/检查点清单、备份清单和验收来源SHA相互关联；package_manifest.json列出本包每个成员的原字节SHA。\n"
            "本次验收是质量参考，不改原候选状态或严格QC，不执行Stage B，也不自动启动后续求解。\n")
        (folder / "README_ZH.md").write_bytes(readme.encode())
        entries = [{"path": f.relative_to(folder).as_posix(), "bytes": f.stat().st_size, "sha256": sha(f)}
                   for f in sorted(folder.rglob("*")) if f.is_file()]
        (folder / "package_manifest.json").write_bytes(json_bytes({
            "case": key, "acceptance_status": profile["status"], "files": entries,
            "self_excluded": "package_manifest.json"}))
        zip_path = HERE / "packages" / (key + "_acceptance_20261020.zip")
        assert not zip_path.exists()
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for f in sorted(folder.rglob("*")):
                if f.is_file():
                    z.write(f, f.relative_to(folder).as_posix())
        with zipfile.ZipFile(zip_path) as z:
            assert z.testzip() is None
            assert set(z.namelist()) == {x["path"] for x in entries} | {"package_manifest.json"}
            for item in entries:
                data = z.read(item["path"])
                assert len(data) == item["bytes"] and hashlib.sha256(data).hexdigest() == item["sha256"]
        summaries[key] = dict(status=profile["status"], zip_path=str(zip_path.resolve()),
            zip_bytes=zip_path.stat().st_size, zip_sha256=sha(zip_path),
            source_file_count=len(collection[key]["files"]),
            package_member_count=len(entries)+1, uncompressed_bytes=sum(e["bytes"] for e in entries),
            acceptance_sha256=sha(record_path), checks=profile["checks"],
            strict_status=qc["status"], backup_status=record["backup_status"])
    sync_result = remote("records=" + repr(sync) + "\n" + r'''
from pathlib import Path
import base64,hashlib,json
result={}
for name,data in records.items():
    path=Path(name)
    assert path.parent.name=='acceptance_relative_v1_20261020_completed'
    raw=base64.b64decode(data)
    if path.exists():assert path.read_bytes()==raw
    else:path.write_bytes(raw)
    result[name]=hashlib.sha256(path.read_bytes()).hexdigest()
print(json.dumps(result))
''')
    for key, item in summaries.items():
        sidecar = json.loads((HERE/"assessments"/key/"evidence_manifest.json").read_text())["sidecar"]
        assert sync_result[sidecar+"/acceptance_relative_v1.json"] == item["acceptance_sha256"]
    (HERE / "backup_completion_verification.json").write_bytes(json_bytes(payload))
    (HERE / "acceptance_sync_verification.json").write_bytes(json_bytes(sync_result))
    (HERE / "package_summary.json").write_bytes(json_bytes(summaries))
    print(json.dumps({k: {n: v for n, v in x.items() if n != "checks"} for k, x in summaries.items()}, indent=2))


if __name__ == "__main__":
    main()
