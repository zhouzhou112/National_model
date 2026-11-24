"""Bind returned Base2060 pricing to local small evidence and run the P4 audit.

The descriptor records remote verification; MPS/BarPi are not downloaded.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    screen=HERE.parent/'base_2060_screen_20261026'
    identity=json.loads((screen/'screen_identity.json').read_text())
    receipt=json.loads((screen/'screen_receipt.json').read_text())
    source=HERE.parent/'completed_acceptance_20261020/evidence/base2060'
    evidence=screen/'source_evidence';evidence.mkdir(exist_ok=False)
    files={}
    for name in ['vre_capacity.csv','model_config_snapshot.json']:
        candidates=[h for path,h in identity['input_sha256'].items() if Path(path).name==name]
        assert candidates==[sha(source/name)],'Local source evidence differs from T550'
        (evidence/name).write_bytes((source/name).read_bytes())
        files[name]=dict(sha256=candidates[0],bytes=(source/name).stat().st_size,verified=True,local_copy=True)
    for name,key in [('model_archive/original.mps.gz','mps_sha256'),('barrier_checkpoint/dual_barpi.npy','barpi_sha256')]:
        files[name]=dict(sha256=identity['identity'][key],verified=True,local_copy=False,
            verification_location='T550 full backup; build_vre_screen_list.archive_paths')
    descriptor=dict(source_release=identity['candidate_screen']['source_release'],files=files,
        description='REMOTE_VERIFICATION_DESCRIPTOR_NOT_FULL_LOCAL_DOWNLOAD',
        remote_directory=receipt['remote_directory'],remote_receipt_sha256=sha(screen/'screen_receipt.json'))
    (evidence/'download_identity.json').write_text(json.dumps(descriptor,indent=2)+'\n')
    cmd=[sys.executable,str(HERE.parent/'case3_2030_launch_20261014/audit_p4_screens.py'),
         '--screen',str(screen),'--archive',str(evidence),'--year','2060',
         '--source-release',identity['candidate_screen']['source_release'],'--output',str(screen/'ready')]
    p=subprocess.run(cmd,capture_output=True,text=True)
    (screen/'readiness_audit.log').write_text(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    print(p.stdout)

if __name__=='__main__':main()
