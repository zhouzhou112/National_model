"""Assess archived QC without modifying it. Requires a separate --output path.

Input: output directory, or solution_qc.json with optional --solve/--inputs JSON.
Output: standalone solution_qc_relative_v1.json (source SHA provenance included).
Includes the 2026-10-14 GW/GWh extension; strict labels and all source data
remain immutable. A FAIL/ERROR exit is a reference label, never a deletion rule.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cispo_model.relative_acceptance import add_relative_profile, archived_inputs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--solve',type=Path)
    parser.add_argument('--inputs',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    qcpath=args.source/'solution_qc.json' if args.source.is_dir() else args.source
    root=qcpath.parent
    solvepath=args.solve or root/'solve_report.json'
    if args.output.resolve()==qcpath.resolve() or args.output.resolve().is_relative_to(root.resolve()):
        parser.error('--output must be outside the immutable source output directory')
    sources=[qcpath,solvepath]+([args.inputs] if args.inputs else [])
    identity={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    qc=json.loads(qcpath.read_text(encoding='utf-8'))
    solve=json.loads(solvepath.read_text(encoding='utf-8'))
    factory=(lambda:json.loads(args.inputs.read_text(encoding='utf-8'))) if args.inputs else lambda:archived_inputs(root)
    profile=add_relative_profile(qc,solve,inputs_factory=factory)
    result=dict(source_sha256=identity,acceptance_profiles={'relative_v1':profile})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    if args.output.exists():
        parser.error('Refuse overwrite; choose a new assessment path')
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    assert identity=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    print(json.dumps(dict(status=profile['status'],output=str(args.output))))
    return 0 if profile['status']=='PASS' else 2

if __name__=='__main__':raise SystemExit(main())
