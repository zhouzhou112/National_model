"""Collect immutable small output snapshots, never MPS/NPY/NPZ/dispatch."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
from collect_t1 import LOCAL, ANALYSIS, remote


def collect(case, stage):
    root = ANALYSIS + "/" + case
    code = "from pathlib import Path\nimport json,hashlib,csv,time,math,io\nroot=Path(" + repr(root) + ")\nstage=" + repr(stage) + "\n"
    code += r'''
names=['input_identity.json','inputs_sha256.txt','row_order_verification.json',
       'row_extraction_summary.json','row_family_inventory.csv','annual_row_duals.csv',
       'corridor_duals.csv','corridor_duals_monthly.csv','run_parameters.json']
assert json.loads((root/'row_order_verification.json').read_text(encoding="utf-8"))['status']=='PASS'
assert json.loads((root/'row_extraction_summary.json').read_text(encoding="utf-8"))['status']=='PASS'
if stage=='final':
    assert json.loads((root/'terminal.json').read_text(encoding="utf-8"))['status']=='COMPLETE'
    names+=['terminal.json','logs/run.stdout.log','logs/run.stderr.log']
    if (root/'rc_screen/screening_summary.json').exists():
        names+=['rc_screen/'+x for x in ['vre_site_reduced_costs.csv','capacity_column_reduced_costs.csv',
               'screening_summary.json','column_family_summary.csv','rc_ratio_histogram.txt']]
else:
    names+=['logs/run.stdout.log','logs/run.stderr.log']
snapshot=root/('return_snapshot_'+stage)
assert not snapshot.exists(),'Do not overwrite a collected snapshot'
snapshot.mkdir()
files={}
for name in names:
    source=root/name
    original=source.read_bytes()
    b=original
    rows=None
    if name.endswith('.csv'):
        data=list(csv.reader(io.StringIO(b.decode('utf-8-sig'))))
        # Output representation only: missing nonfinite numbers are blank,
        # never zero; the original computed CSV remains in rc_screen.
        changed=False
        for row in data[1:]:
            for j,v in enumerate(row):
                if v.lower() in ('nan','inf','-inf','+inf'):
                    row[j]='';changed=True
        rows=len(data)-1
        if changed:
            text=io.StringIO(newline='');w=csv.writer(text);w.writerows(data)
            b=text.getvalue().encode('utf-8')
    target=name
    if name.endswith('.json') and '/' not in name:
        target='metadata/'+name
    if name=='inputs_sha256.txt':
        target='rc_screen/inputs_sha256.txt'
    if stage!='final' and name.startswith('logs/'):
        target=name.replace('run.','rows_stage.')
    dest=snapshot/target;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
    files[target]=dict(source=str(source),original_sha256=hashlib.sha256(original).hexdigest(),
        sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),rows=rows,serialization_only_changed=b!=original)
    assert len(b)<30_000_000,'Small-file ceiling exceeded: '+name
(snapshot/'sha256.txt').write_text(''.join(v['sha256']+'  '+k+'\n' for k,v in sorted(files.items())))
print(json.dumps(dict(snapshot=str(snapshot),files=files,stage=stage)))
'''
    result = remote(code)
    mapping = result["files"]
    tarcode = "import tarfile,sys\nfrom pathlib import Path\nroot=Path(" + repr(result["snapshot"]) + ")\nnames=" + repr(list(mapping)) + "\n"
    tarcode += "with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as tf:\n for name in names:tf.add(str(root/name),arcname=name,recursive=False)\n"
    content = remote(tarcode, binary=True)
    dest = LOCAL / case
    verified = json.loads((dest / "transfer_verification.json").read_text(encoding="utf-8"))
    with tarfile.open(fileobj=io.BytesIO(content)) as tf:
        for member in tf:
            assert member.isfile() and member.name in mapping
            b = tf.extractfile(member).read()
            h = hashlib.sha256(b).hexdigest()
            assert h == mapping[member.name]["sha256"], member.name
            target = dest / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                assert target.read_bytes() == b, "Conflicting already-returned file: " + member.name
            else:
                target.write_bytes(b)
            verified[member.name] = dict(mapping[member.name], local_sha256=h, verified=True)
    (dest / "transfer_verification.json").write_text(json.dumps(verified, indent=2) + "\n", encoding="utf-8")
    (dest / "sha256.txt").write_text("".join(v["sha256"]+"  "+name+"\n" for name,v in sorted(verified.items())), encoding="utf-8")
    summary = json.loads((dest / "summary.json").read_text(encoding="utf-8"))
    extraction = json.loads((dest / "metadata/row_extraction_summary.json").read_text(encoding="utf-8"))
    summary.update(T3="COMPLETE", T4="COMPLETE", row_extraction=extraction, files=verified,
                   return_bytes=sum(x["bytes"] for x in verified.values()))
    if stage == "final":
        summary["T2"] = "COMPLETE" if (dest / "rc_screen/vre_site_reduced_costs.csv").exists() else "LOCAL_REUSE_PENDING"
        summary["terminal"] = json.loads((dest / "metadata/terminal.json").read_text(encoding="utf-8"))
    (dest / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(case=case, stage=stage, files=len(mapping), T3="COMPLETE", T4="COMPLETE", T2=summary["T2"])), flush=True)


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("case")
    p.add_argument("--stage", choices=["rows","final"], required=True)
    a=p.parse_args()
    collect(a.case,a.stage)
