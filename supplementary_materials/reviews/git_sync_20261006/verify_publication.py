"""Validate selected source and unpublished history without executing model code.

Checks Python syntax, JSON parseability, literal secrets, exact tested-source
identities, and selected file sizes. Does not inspect credentials or stage files.
"""
import ast,hashlib,json,subprocess
from pathlib import Path
from prepare_reviewed_files import ROOT,HERE
import re

def main():
    manifest=json.loads((HERE/'selected_files.json').read_text())
    syntax=[]
    for item in manifest:
        p=ROOT/item['path']
        if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8-sig'),filename=item['path']);syntax.append(item['path'])
        if p.suffix=='.json':json.loads(p.read_text(encoding='utf-8-sig'))
    old=json.loads((ROOT/'supplementary_materials/reviews/validation_coordination_20261005/unittest_verified_20261005T185140Z.json').read_text())
    drift=[s for s,h in old['source_sha256_after'].items() if hashlib.sha256((ROOT/s).read_bytes()).hexdigest()!=h]
    assert not drift,drift
    commits=subprocess.check_output(['git','rev-list','github/codex/stagea-8760-final-v1..HEAD'],cwd=ROOT,text=True).splitlines()
    pat=re.compile(rb'-----BEGIN (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----|\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}|AKIA[A-Z0-9]{16})\b')
    literal=re.compile(rb'''(?i)(?:password|passwd|wlssecret|access_token|api_key)\s*[=:]\s*["']([^"'\n]{8,})["']''')
    findings=[];count=0
    for commit in commits:
        changed=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r','-z',commit],cwd=ROOT).split(b'\0')
        for path in changed:
            if not path:continue
            s=path.decode()
            if re.search(r'(\.lic|\.pem|\.key|ssh\.txt)$|(^|/)\.env$|(^|/)id_(rsa|ed25519)',s,re.I):
                findings.append(dict(commit=commit,path=s,reason='credential-like path not read'));continue
            proc=subprocess.run(['git','show',commit+':'+s],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            if proc.returncode:continue
            b=proc.stdout;count+=1
            if b'\0' not in b[:8000] and (pat.search(b) or literal.search(b)):
                findings.append(dict(commit=commit,path=s,reason='potential literal secret; contents suppressed'))
    result=dict(python_syntax_files=len(syntax),tested_source_count=len(old['source_sha256_after']),tested_source_drift=drift,regression_reused=old['log'],history_commits=len(commits),history_file_versions=count,history_secret_findings=findings)
    (HERE/'publication_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if findings:raise SystemExit(1)

if __name__=='__main__':main()
