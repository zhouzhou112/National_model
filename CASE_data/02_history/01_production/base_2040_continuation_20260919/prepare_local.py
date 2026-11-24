"""Freeze only the new execution profile and launcher; retain deployed v9 model."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PROFILE = 'barrier_checkpoint_full_year_cloud_2040_numeric_v1_threads44'

def main():
    raw = json.loads((REPO/'config/solver_profiles/barrier_stagea_numeric_repaired_v1_threads48.json').read_text())
    raw.update(profile_id=PROFILE, direct_nonbasic_scientific_acceptance=False,
               description='Author-authorized 2026-09-19 2040 Base continuation from job4614693 unaccepted 2030 candidate; existing engineering preservation route, upstream QC retained, no scientific promotion, no automatic successor. Same v9 model, 44 solver threads, NF2, BarConvTol1e-4, Crossover0, no time or soft-memory limit.')
    raw['numerics']['threads'] = 44
    path = REPO/'config/solver_profiles'/f'{PROFILE}.json'
    assert not path.exists() or json.loads(path.read_text()) == raw
    path.write_text(json.dumps(raw, indent=2)+'\n', encoding='utf-8')
    batch = (HERE.parent/'formal_launch_failure_20260914/formal_base.sbatch').read_text()
    batch = batch.replace('full 2030 v9 Base', 'full 2040 v9 Base candidate continuation')
    batch = batch.replace('cispo2030_base_v9_t48', 'cispo2040_base_v9_t44')
    batch = batch.replace('=48', '=44').replace('< 48', '< 44')
    batch = batch.replace('barrier_stagea_numeric_repaired_v1_threads48.json', PROFILE+'.json')
    batch = batch.replace('--horizon full_year --archive-original-model --allow-nonbasic-planning-state',
        '--planning-year 2040 --horizon full_year --archive-original-model \\\n+    --engineering-barrier-checkpoint-only --allow-candidate-state-in \\\n+    --state-in "$UPSTREAM_STATE"')
    batch = batch.replace(': "${SOURCE_RELEASE:?Immutable data/environment source required}"',
        ': "${SOURCE_RELEASE:?Immutable data/environment source required}"\n: "${UPSTREAM_STATE:?Verified 2030 candidate required}"')
    # Validate the actual predecessor state and unchanged execution contract before building.
    batch = batch.replace('cd "$RELEASE_ROOT/repo"',
        'cd "$RELEASE_ROOT/repo"\n"$PYTHON" "$RELEASE_ROOT/validate_2040.py" --contract-only > "$RELEASE_ROOT/continuation_contract_check.log" 2>&1')
    batch = batch.replace('\n+    --', '\n    --')
    (HERE/'base_2040.sbatch').write_text(batch, encoding='utf-8', newline='\n')
    print(path)

if __name__ == '__main__':
    main()
