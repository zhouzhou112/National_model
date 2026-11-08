"""Check numerical closure and preserve SHA provenance of this read-only review."""
import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd

from audit_hydro import OUT, ROOT, RETURNS, EVIDENCE, digest, save_json


def main():
    checks = json.loads((OUT/'checks.json').read_text())
    provenance = json.loads((OUT/'provenance_checks.json').read_text())
    verifications = []
    def check(name, condition):
        verifications.append({'check':name,'pass':bool(condition)})
        if not condition:
            raise AssertionError(name)
    for name in ['hourly_hold_max_error_m3s','negative_clipping_max_error_m3s',
                 'monthly_p30_recompute_max_error_m3s','missing_station_comids',
                 'independent_vs_production_available_flow_max_abs_m3s']:
        check(name, checks[name] == 0)
    check('aggregate_curve_recomputed', checks['aggregate_profile_recompute_max_abs_cf_error'] < 1e-12)
    check('matching_reproduced',provenance['match_pair_sets_equal'])
    check('archived_production_inputs_same',provenance['all_archived_production_hydro_inputs_match'])
    original = json.loads((OUT/'original_grfr_verification.json').read_text())
    check('all_original_target_values_equal',all(x['all_values_equal'] and x['time_axis_equal'] for x in original))
    check('original_value_count',sum(x['compared_values'] for x in original)==1857*2920)
    provinces = pd.read_csv(OUT/'province_diagnostic.csv')
    check('all_31_provinces',len(provinces)==31 and provinces.province_code.nunique()==31)
    station = pd.read_csv(OUT/'station_diagnostic.csv')
    national = pd.read_csv(OUT/'actual_national_by_technology.csv')
    y2060 = national[national.year==2060]
    check('2060_generation_closes',np.isclose(provinces.actual2060_generation_gwh.sum(),y2060.generation_gwh.sum(),rtol=0,atol=1e-7))
    check('2060_capacity_closes',np.isclose(provinces.actual2060_total_capacity_gw.sum(),y2060.capacity.sum(),rtol=0,atol=1e-9))
    check('station_sum_closes',np.isclose(provinces.existing_capacity_gw.sum(),station.existing_capacity_gw.sum(),rtol=0,atol=1e-9))
    ablation = pd.read_csv(OUT/'national_arithmetic_ablations.csv').set_index('scenario')
    check('p30_reduces_more_than_p10',ablation.loc['p30_no_share','existing_total_instant_proxy_twh'] < ablation.loc['p10_no_share','existing_total_instant_proxy_twh'])
    check('comid_share_reduces_availability',ablation.loc['p30_with_share','existing_total_instant_proxy_twh'] < ablation.loc['p30_no_share','existing_total_instant_proxy_twh'])
    manifest = json.loads((EVIDENCE/'result_manifest.json').read_text())
    expected={f['path']:f['sha256'] for f in manifest['files']}
    for filename in ['annual_generation_by_province_technology.csv','annual_capacity_by_province_technology.csv']:
        check('base2060_export_'+filename,digest(RETURNS/'base2060'/filename)==expected[filename])
    for path in OUT.glob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'))
    check('python_ast',True)
    # Recheck original core source identities after all calculations, no new raw-data read needed.
    for item in json.loads((OUT/'input_manifest.json').read_text()):
        check('source_unchanged_'+Path(item['path']).name,digest(item['path'])==item['sha256'])
    save_json('delivery_verification.json',{'status':'PASS','scope':'audit arithmetic, provenance, output closure; not scientific acceptance of hydro model','checks':verifications})
    outputs=[p for p in OUT.iterdir() if p.is_file() and p.name!='artifact_manifest.json']
    save_json('artifact_manifest.json',[{'path':p.name,'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(outputs)])
    print(json.dumps({'status':'PASS','checks':len(verifications),'files':len(outputs)}))


if __name__=='__main__':
    main()
