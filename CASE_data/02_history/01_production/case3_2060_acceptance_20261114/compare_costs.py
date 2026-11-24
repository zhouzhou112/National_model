"""T550-only A2060 point differences and author-defined engineering intervals."""
from pathlib import Path
import base64,csv,hashlib,json,subprocess,sys

RELEASES={
 'Base':'20261012_base2060_v9a12_t48_m750_tol1e4_v1',
 'B':'20261027_basefrozen_2060_v9a12_agg0_t48_m750_tol1e4_v2',
 'C':'20261030_lateentry_2060_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1',
 'A':'20261106_case3_2060_v9a12_screen0p2_agg0_t44_m750_tol1e4_v1',
}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def interval(ref,a):
 """Positive means A costs less than reference; all inputs million CNY/year."""
 return dict(point=ref['P']-a['P'],lower=ref['D']-ref['B']-a['P'],upper=ref['P']-a['D']+a['B'])

def remote():
 base=Path('/home/zz2/National_model_server/cloud_backup');out=base/RELEASES['A']/'cost_comparison_20261114'
 assert not out.exists(),'Inspect prior comparison, never overwrite'
 metrics={};sources={}
 for label,release in RELEASES.items():
  b=base/release;root=b/'output_8760';backup=json.loads((b/'backup_manifest.json').read_text())
  assert backup['status']=='COMPLETE' and backup['source_unchanged_after_transfer']
  assert sha(root/'result_manifest.json')==backup['source_result_manifest_sha256']
  entries={e['path']:e for e in json.loads((root/'result_manifest.json').read_text())['files']}
  files={}
  for name in ['solve_report.json','model_config_snapshot.json']:
   p=root/name;e=entries[name];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256']
   files[name]=dict(bytes=e['bytes'],sha256=e['sha256'])
  solve=json.loads((root/'solve_report.json').read_text());config=json.loads((root/'model_config_snapshot.json').read_text())['resolved_configuration']
  assert solve['status']=='OPTIMAL' and config['planning_year']==2060 and config['hours']==8760
  m=solve['solution_contract']['barrier_primal_dual_metrics'];metrics[label]=dict(P=float(m['primal_objective']),D=float(m['dual_objective']),B=0.)
  if label in ['A','C']:
   date='20261114' if label=='A' else '20261108'
   acceptance=b/('author_review_'+date)/('acceptance_author_'+date+'.json')
   certpath=b/('postprocess_'+date)/'pricing/screen_pricing_certificate.json'
   receipt=json.loads((b/('postprocess_'+date)/'pricing_receipt.json').read_text())['files']['screen_pricing_certificate.json']
   assert sha(certpath)==receipt['sha256'] and certpath.stat().st_size==receipt['bytes']
   acc=json.loads(acceptance.read_text());cert=json.loads(certpath.read_text())
   assert acc['status']=='PASS' and acc['source_evidence']['source_sha256']['result_manifest.json']==backup['source_result_manifest_sha256']
   checkpoint=json.loads((root/'barrier_checkpoint/barrier_checkpoint_manifest.json').read_text())
   assert cert['identity']['barpi_sha256']==checkpoint['vectors']['dual']['sha256']
   assert cert['input_sha256'][str(root/'solve_report.json')]==sha(root/'solve_report.json')
   assert acc['certificate']['B_million_cny']==cert['B_million_cny']
   metrics[label]['B']=float(cert['B_million_cny'])
   files.update(acceptance_sha256=sha(acceptance),certificate_sha256=sha(certpath),barpi_sha256=cert['identity']['barpi_sha256'])
  else:
   selection=root/'candidate_selection.csv'
   if selection.exists():
    e=entries['candidate_selection.csv'];assert sha(selection)==e['sha256']
    with selection.open(newline='') as f:assert not any(r.get('screened_out','false').lower()=='true' for r in csv.DictReader(f))
   files['screening_bound_basis']='unscreened reference; no screened-out candidates; B=0'
  sources[label]=dict(release=release,result_manifest_sha256=backup['source_result_manifest_sha256'],files=files)
 rows=[]
 for label in ['Base','B','C']:
  values=interval(metrics[label],metrics['A'])
  rows.append(dict(reference=label,target='A',units='yi CNY/year',point_saving=values['point']/100,lower_saving=values['lower']/100,upper_saving=values['upper']/100,reference_B_yi_cny=metrics[label]['B']/100,A_B_yi_cny=metrics['A']['B']/100,formula='[D_reference-B_reference-P_A, P_reference-D_A+B_A]',interval_contains_zero=values['lower']<=0<=values['upper']))
 out.mkdir()
 summary=dict(status='PASS',computed_on='T550',metrics_million_cny=metrics,comparisons=rows,sources=sources,sign_convention='reference minus A; positive means A saving',label='BARRIER_DUAL_ENGINEERING_GRADE',interpretation='Author engineering comparison intervals, not market settlement or statistical confidence intervals. No causal attribution or automatic re-solve.')
 (out/'comparison_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 with (out/'A2060_cost_intervals.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 payload={}
 for p in out.iterdir():
  raw=p.read_bytes();assert len(raw)<1024**2;payload[p.name]=dict(bytes=len(raw),sha256=sha(p),base64=base64.b64encode(raw).decode())
 print(json.dumps(dict(remote_directory=str(out),files=payload)))

def local():
 here=Path(__file__).resolve().parent;assert not (here/'cost_comparison_receipt.json').exists()
 ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server']
 p=subprocess.run(ssh+['/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python - --remote'],input=Path(__file__).read_text(),text=True,encoding='utf-8',capture_output=True,timeout=180)
 (here/'cost_comparison.stderr.log').write_text(p.stderr);p.check_returncode();r=json.loads(p.stdout)
 dest=here/'cost_comparison';dest.mkdir(exist_ok=True)
 for n,e in r['files'].items():
  raw=base64.b64decode(e.pop('base64'));assert len(raw)==e['bytes'] and hashlib.sha256(raw).hexdigest()==e['sha256']
  with (dest/n).open('xb') as f:f.write(raw)
 (here/'cost_comparison_receipt.json').write_text(json.dumps(r,indent=2)+'\n');print((dest/'comparison_summary.json').read_text())

if __name__=='__main__':remote() if '--remote' in sys.argv else local()
