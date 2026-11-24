"""Finite read-only T550 small-file collector. Writes only 02_server_returns."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

LOCAL = Path(__file__).resolve().parents[2]
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=12",
       "-o", "HostName=127.0.0.1", "-o", "BindAddress=127.0.0.1",
       "national-model-server"]
REMOTE_BASE = "/home/zz2/National_model_server/cloud_backup"
ANALYSIS = "/home/zz2/National_model_server/analysis_tools_20261020"
PYTHON = "/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python"
RELEASES = {
    "base2040": "20260919_base2040_v9_t44_m750_tol1e4_v1",
    "base2030": "20260914_base_v9_t48_m750_tol1e4_v3",
    "base2050": "20260930_base2050_v9_t48_m750_tol1e4_v1",
    "base2060": "20261012_base2060_v9a12_t48_m750_tol1e4_v1",
    "case3_2030": "20261014_case3_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1",
}
T1 = [
    "hourly_marginal_prices.csv.gz", "annual_constraint_shadow_prices.csv",
    "dual_export_status.json", "barrier_checkpoint/barrier_checkpoint_manifest.json",
    "annual_adequacy_by_province.csv", "annual_capacity_by_province_technology.csv",
    "annual_generation_by_province_technology.csv", "annual_resource_accounting_by_province.csv",
    "monthly_energy_by_technology.csv", "cost_components.csv", "annual_summary.json",
    "annual_carbon_ccs.json", "transmission_capacity.csv", "storage_capacity.csv",
    "thermal_nuclear_capacity.csv", "vre_capacity.csv",
]
EXTRAS = [
    "load_center_annual_balance.csv", "load_center_intra_transmission.csv",
    "province_annual_load_center_accounts.csv", "model_config_snapshot.json",
    "model_archive/archive_manifest.json",
]


def remote(code, binary=False, timeout=120):
    p = subprocess.run(SSH + ["python3 -"], input=code.encode(), capture_output=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors="replace") + p.stdout.decode(errors="replace")[-2000:])
    return p.stdout if binary else json.loads(p.stdout)


def collect(case):
    dest = LOCAL / case
    root = REMOTE_BASE + "/" + RELEASES[case]
    code = "root=Path(" + repr(root) + ")\nnames=" + repr(T1 + EXTRAS) + "\n"
    code = "from pathlib import Path\nimport json,hashlib,csv,gzip,time\n" + code + r'''
start=time.time()
backup=json.loads((root/'backup_manifest.json').read_text())
mb=(root/'output_8760/result_manifest.json').read_bytes()
assert hashlib.sha256(mb).hexdigest()==backup['source_result_manifest_sha256'],'result manifest mismatch'
manifest=json.loads(mb)
records={x['path']:x for x in manifest['files']}
brec={x['path']:x for x in backup['files']}
files={}
for name in names:
    p=root/'output_8760'/name
    expected=records.get(name,brec.get('output_8760/'+name))
    assert expected and p.is_file(),name
    assert p.stat().st_size<30_000_000,name
    b=p.read_bytes();actual=hashlib.sha256(b).hexdigest()
    assert actual==expected['sha256'],name
    rows=None
    if '.csv' in name:
        opener=gzip.open if name.endswith('.gz') else open
        with opener(str(p),'rt',encoding='utf-8-sig',newline='') as stream:
            rows=sum(1 for _ in csv.reader(stream))-1
    files[name]=dict(bytes=len(b),sha256=actual,rows=rows,source=str(p))
for name in ['result_manifest.json','backup_manifest.json']:
    p=root/'output_8760'/name if name=='result_manifest.json' else root/name
    b=p.read_bytes()
    files['__metadata__/'+name]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),source=str(p))
print(json.dumps(dict(status='PASS',release=str(root),files=files,seconds=time.time()-start)))
'''
    audit = remote(code)
    mapping = {}
    for name, value in audit["files"].items():
        if name in T1:
            target = name
        elif name.startswith("__metadata__/"):
            target = "metadata/" + name.split("/")[-1]
        else:
            target = "metadata/" + name.replace("/", "__")
        mapping[target] = value
    tarcode = "import tarfile,sys\nmapping=" + repr(mapping) + "\n"
    tarcode += "with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as tf:\n"
    tarcode += " for name,value in mapping.items():tf.add(value['source'],arcname=name,recursive=False)\n"
    data = remote(tarcode, binary=True)
    verification = {}
    with tarfile.open(fileobj=io.BytesIO(data)) as tf:
        for member in tf:
            assert member.name in mapping and member.isfile()
            content = tf.extractfile(member).read()
            h = hashlib.sha256(content).hexdigest()
            assert h == mapping[member.name]["sha256"], member.name
            p = dest / member.name
            p.parent.mkdir(parents=True, exist_ok=True)
            if p.exists():
                assert p.read_bytes() == content, p
            else:
                p.write_bytes(content)
            verification[member.name] = dict(mapping[member.name], local_sha256=h, verified=True)
    assert len(verification) == len(mapping)
    (dest / "transfer_verification.json").write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
    (dest / "metadata/t1_input_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    (dest / "summary.json").write_text(json.dumps(dict(
        case=case, release=root, T1="COMPLETE", T1_files=16, T2="PENDING", T3="PENDING", T4="PENDING",
        result_label="初步结果", dual_grade="BARRIER_DUAL_ENGINEERING_GRADE",
        seconds_T1=audit["seconds"], return_bytes=sum(x["bytes"] for x in verification.values()),
        exceptions=[], files=verification), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (dest / "sha256.txt").write_text("".join(v["sha256"] + "  " + name + "\n" for name, v in sorted(verification.items())), encoding="utf-8")
    print(json.dumps(dict(case=case, T1="COMPLETE", files=16, bytes=sum(x["bytes"] for x in verification.values()))), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cases", nargs="*", choices=list(RELEASES))
    args = p.parse_args()
    for case in args.cases or RELEASES:
        collect(case)
