"""Read-only preflight: freeze the observed production CF fallback identity."""
from pathlib import Path
import json,os,sys,hashlib
import pandas as pd

root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'repo'))
from cispo_model.data import CapacityFactorStore,_resolve_vre_cf_sites

launch=json.loads((root/'launch_config.json').read_text())
data=Path(os.environ['CISPO_DATA_ROOT'])
points=pd.read_csv(data/'vre/optimization_points.csv')
source=root/'frozen_source'/launch['frozen_capacity_from']/'output_8760'
sites=pd.read_csv(source/'vre_capacity.csv').merge(points[['grid_uid','lon','lat','is_land']],on='grid_uid',how='left',validate='many_to_one')
cf=CapacityFactorStore(pd.read_csv(data/'vre/hourly_cf_index.csv'),2024,'beijing_natural_year_drop_feb29_v1')
resolved=_resolve_vre_cf_sites(points,sites,cf)
actual={(r.grid_uid,r.technology):int(r.cf_grid_id) for r in resolved.itertuples() if r.cf_fallback_method=='nearest_same_province_land_pv_grid'}
expected_file=root/'cf_fallback_cloud.json'
expected={(r['grid_uid'],r['technology']):r['cf_grid_id'] for r in json.loads(expected_file.read_text())['fallback']}
if actual!=expected:raise ValueError('Production CF fallback mapping differs from qualified gates')
report=dict(status='PASS',checked_mappings=len(actual),mapping_reference_sha256=hashlib.sha256(expected_file.read_bytes()).hexdigest(),rule_unchanged=True)
(root/'cf_mapping_preflight.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
