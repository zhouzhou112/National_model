"""Read-only cross-platform CF fallback mapping diagnosis, no model changes."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd
import scipy
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2];sys.path.insert(0,str(ROOT))
from cispo_model.data import CapacityFactorStore,_resolve_vre_cf_sites

points=pd.read_csv(ROOT/'data/vre/optimization_points.csv')
source=ROOT/'supplementary_materials/reviews/base_frozen_followups_20261027/source_base/20260919_base2040_v9_t44_m750_tol1e4_v1/output_8760'
sites=pd.read_csv(source/'vre_capacity.csv').merge(points[['grid_uid','lon','lat','is_land']],on='grid_uid',how='left',validate='many_to_one')
cf=CapacityFactorStore(pd.read_csv(ROOT/'data/vre/hourly_cf_index.csv'),2024,'beijing_natural_year_drop_feb29_v1')
resolved=_resolve_vre_cf_sites(points,sites,cf)
print(json.dumps(dict(scipy=scipy.__version__,numpy=np.__version__,pandas=pd.__version__,
    fallback=resolved[resolved.cf_fallback_method=='nearest_same_province_land_pv_grid'][['grid_uid','technology','cf_grid_id','lon','lat']].to_dict('records'))))
