"""Exact excluded identity comparison; a changed set is a failed launch gate."""
import argparse,csv,hashlib,json,pathlib

def excluded(path):
 with path.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
 keys=[(r['grid_uid'],r['technology']) for r in rows]
 if len(keys)!=len(set(keys)):raise ValueError('Duplicate candidate identities')
 if any(r['screened_out'].lower() not in ['true','false'] for r in rows):raise ValueError('Nonboolean screened_out')
 return set(keys),{(r['grid_uid'],r['technology']) for r in rows if r['screened_out'].lower()=='true'}
def compare(candidate,reference):
 ka,a=excluded(candidate);kb,b=excluded(reference)
 return dict(status='PASS' if ka==kb and a==b else 'FAIL',sites_equal=ka==kb,case3_excluded=len(a),C2060_excluded=len(b),case3_only=sorted(a-b),C2060_only=sorted(b-a),excluded_identity_sha256=hashlib.sha256(json.dumps(sorted(a),separators=(',',':')).encode()).hexdigest())
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['candidate','reference','screen','receipt','output']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 a=p.parse_args();assert not a.output.exists();r=compare(a.candidate,a.reference);receipt=json.loads(a.receipt.read_text());digest=hashlib.sha256(a.screen.read_bytes()).hexdigest()
 r['screen_sha256']=digest;r['screen_sha_matches_C2060']=digest==receipt['files']['source_screen.csv']['sha256'];r['reference_candidate_sha_matches']=hashlib.sha256(a.reference.read_bytes()).hexdigest()==receipt['files']['output_8760/candidate_selection.csv']['sha256'];r['margin']=.2;r['site_addbacks']=[]
 if not r['screen_sha_matches_C2060'] or not r['reference_candidate_sha_matches']:r['status']='FAIL'
 a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
 if r['status']!='PASS':raise SystemExit(2)
if __name__=='__main__':main()
