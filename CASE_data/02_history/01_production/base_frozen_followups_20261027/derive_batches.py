"""Derive all four launch scripts from the latest successful B2030 v3 batch."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud'
TEMPLATE=BASE+'/20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v3/base_frozen_2030.sbatch'
SOURCES={2040:'20260919_base2040_v9_t44_m750_tol1e4_v1',2050:'20260930_base2050_v9_t48_m750_tol1e4_v1',2060:'20261012_base2060_v9a12_t48_m750_tol1e4_v1'}


def main():
    raw=subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','paracloud-bscc-a8','cat '+TEMPLATE])
    expected=(HERE.parent/'base_frozen_B_20261026/base_frozen_2030_v3.sbatch').read_bytes().replace(b'\r\n',b'\n')
    assert raw==expected
    (HERE/'successful_B2030_v3_template.sbatch').write_bytes(raw)
    text=raw.decode().replace('optimization_numeric_dac_by_year_v9.json','optimization_numeric_dac_by_year_v9_a12.json')
    text=text.replace("gates['framework'] == 'B' and gates['planning_year'] == 2030", "gates['framework'] == launch['framework'] and gates['planning_year'] == launch['planning_year']")
    outputs={}
    for year,source in SOURCES.items():
        batch=text.replace('cispo2030_B_frozen','cispo'+str(year)+'_B_frozen').replace('--planning-year 2030','--planning-year '+str(year))
        batch=batch.replace('20260914_base_v9_t48_m750_tol1e4_v3',source).replace('frozen_capacity_B_20261026','frozen_capacity_B_20261027')
        batch=batch.replace('# Author 2026-10-26: B2030 v3, derived from case3 2040 v2; scientific gates reused.', '# Author 2026-10-27: B follow-up; derived from successful B2030 v3, new year-specific gates.')
        p=HERE/('B'+str(year)+'.sbatch');p.write_text(batch,encoding='utf-8',newline='\n');outputs[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    batch=text.replace('cispo2030_B_frozen','cispo2050_case3').replace('--planning-year 2030','--planning-year 2050')
    batch=batch.replace('OMP_NUM_THREADS=48 OPENBLAS_NUM_THREADS=48 MKL_NUM_THREADS=48','OMP_NUM_THREADS=40 OPENBLAS_NUM_THREADS=40 MKL_NUM_THREADS=40').replace('getaffinity(0)) < 48','getaffinity(0)) < 40')
    batch=batch.replace('barrier_stagea_base_frozen_agg0_v1_threads48.json','barrier_stagea_screened_agg0_case3_2050_v1_threads40.json')
    a=batch.index('    --frozen-capacity-from ');b=batch.index('    --planning-year ',a)
    batch=batch[:a]+'''    --vre-screen-csv "$RELEASE_ROOT/source_screen.csv" \\
    --state-in "$RELEASE_ROOT/upstream_state/planning_state_candidate" --allow-candidate-state-in \\
'''+batch[b:]
    batch=batch.replace('# Author 2026-10-26: B2030 v3, derived from case3 2040 v2; scientific gates reused.', '# Author 2026-10-27: framework-A case3 2050; derived from successful B2030 v3, 40 threads.')
    p=HERE.parent/'case3_2050_launch_20261027/continuation.sbatch';p.write_text(batch,encoding='utf-8',newline='\n');outputs[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    (HERE/'batch_derivation.json').write_text(json.dumps(dict(template=TEMPLATE,template_sha256=hashlib.sha256(raw).hexdigest(),outputs=outputs),indent=2)+'\n')
    print('Derived four scripts; no deployment or submission')


if __name__=='__main__':main()
