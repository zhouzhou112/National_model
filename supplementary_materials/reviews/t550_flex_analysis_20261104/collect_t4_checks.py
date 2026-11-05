"""Run and retrieve tiny T4 checks from T550; preserve prior files."""
import argparse,base64,hashlib,json
from dispatch import HERE,RET,BASE,OUT,PY,RELEASES,remote

def run(case):
 source=(HERE/'t4_price_checks.py').read_bytes();out=OUT+'/'+case;root=BASE+'/cloud_backup/'+RELEASES[case]
 code='from pathlib import Path\nimport base64,json,subprocess,hashlib\nout=Path('+repr(out)+')\nb=base64.b64decode('+repr(base64.b64encode(source).decode())+')\np=out/"scripts/t4_price_checks.py"\nif p.exists():\n assert p.read_bytes()==b\nelse:p.write_bytes(b)\n'
 code+='r=subprocess.run('+repr([PY,str(out+'/scripts/t4_price_checks.py'),'--root',root,'--out',out])+',capture_output=True,text=True)\nassert r.returncode==0,r.stderr\nnames=["t4_price_checks.json","annual_price_checks_by_province.csv","scripts/t4_price_checks.py"]\nprint(json.dumps({n:dict(sha256=hashlib.sha256((out/n).read_bytes()).hexdigest(),base64=base64.b64encode((out/n).read_bytes()).decode(),bytes=(out/n).stat().st_size) for n in names}))'
 result=remote(code);receipt={}
 for n,v in result.items():
  target='metadata/'+n if n.endswith('.json') else n
  b=base64.b64decode(v.pop('base64'));assert hashlib.sha256(b).hexdigest()==v['sha256'];p=RET/case/target;p.parent.mkdir(exist_ok=True,parents=True)
  if p.exists():assert p.read_bytes()==b
  else:p.write_bytes(b)
  receipt[target]=dict(v,verified=True,source=out+'/'+n)
 (HERE/(case+'_t4_check_receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(json.loads((RET/case/'metadata/t4_price_checks.json').read_text())))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('case',choices=list(RELEASES));run(p.parse_args().case)
