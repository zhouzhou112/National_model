"""Compare observed Barrier iteration times; no causal thread benchmark claim."""
from pathlib import Path
import hashlib
import json
import re
import statistics

ROOT = Path(__file__).resolve().parent
SOURCES = {
    'base48_4614693': ROOT.parent/'base_v9_terminal_20260919/evidence/output_8760__gurobi.log',
    'base44_4496031': ROOT/'evidence/base_t44_4496031.log',
    'thermal44_4533060': ROOT/'evidence/thermal_t44_4533060.log',
}
PAT = re.compile(r'^\s*(\d+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+(\d+)s\s*$', re.M)

def main():
    result = {}
    for label, path in SOURCES.items():
        log = path.read_text(encoding='utf-8')
        rows = {int(m[1]): int(m[7]) for m in PAT.finditer(log)}
        stats = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'last_iteration': max(rows), 'windows': {}}
        for key, pattern in {
            'threads': r'Thread count:.*using up to (\d+) threads',
            'factor_nz': r'Factor NZ\s*:\s*(\S+)',
            'factor_ops': r'Factor Ops\s*:\s*(\S+)',
            'presolved': r'Presolved: (.*)',
            'numeric_focus': r'NumericFocus\s+(\d+)',
        }.items():
            match = re.search(pattern, log)
            stats[key] = match.group(1) if match else None
        for a, b in [(0, 39), (10, 39), (20, 39), (50, 97), (50, 200), (200, 300), (300, 348), (0, max(rows))]:
            if a not in rows or b not in rows or b <= a:
                continue
            differences = [rows[i]-rows[i-1] for i in range(a+1, b+1)]
            stats['windows'][f'{a}-{b}'] = {'mean_minutes': statistics.mean(differences)/60, 'median_minutes': statistics.median(differences)/60}
        result[label] = stats
    (ROOT/'thread_comparison.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
