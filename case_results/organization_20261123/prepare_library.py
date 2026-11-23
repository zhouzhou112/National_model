"""Prepare explicit, non-secret case-library inputs from the reviewed catalog."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent


def main():
    catalog = json.loads((ROOT / 'case_results/case_catalog.json').read_text(encoding='utf-8-sig'))
    records = []
    for case in catalog['cases']:
        path = case.get('acceptance_path')
        if not path:
            choices = [p for p in case.get('local_evidence', [])
                       if Path(p).name.startswith('acceptance_author_')]
            path = sorted(choices)[-1] if choices else None
        evidence = None
        if path:
            p = ROOT / path
            raw = p.read_bytes()
            assert len(raw) < 1024 ** 2, p
            evidence = dict(local_path=str(p), sha256=hashlib.sha256(raw).hexdigest(),
                            bytes=len(raw), document=json.loads(raw.decode('utf-8-sig')))
        if case['kind'] in ('COMPLETED_PRODUCTION', 'COMPLETED_DIAGNOSTIC'):
            assert evidence is not None, case['release']
        records.append(dict(catalog=case, accepted_evidence=evidence))
    payload = dict(schema_version=1, cases=records,
                   remote_inventory=json.loads((WORK/'remote_inventory.json').read_text(encoding='utf-8-sig')))
    (WORK/'library_inputs.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(cases=len(records), bytes=(WORK/'library_inputs.json').stat().st_size)))


if __name__ == '__main__':
    main()
