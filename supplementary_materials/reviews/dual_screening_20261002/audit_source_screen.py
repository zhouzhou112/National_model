"""Recalculate source-screen statistics with explicit GW/kW/MW thresholds."""
from pathlib import Path
import hashlib
import json
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
source=ROOT.parent/"claude_workspace/evidence/rc_screen_2030/vre_site_reduced_costs.csv"
d=pd.read_csv(source)
if d.duplicated(["grid_uid","technology"]).any():raise ValueError("Duplicate sites")
rows=[]
for margin in [.05,.1,.15,.2,.3]:
    keep=(d.headroom_gw>1e-9)&(d.rc_ratio<margin)
    dropped=d.loc[~keep]
    rows.append(dict(margin=margin,retained=int(keep.sum()),retained_nnz=int(d.loc[keep,"cap_nnz"].sum()),
        dropped_positive_capacity_gw=float(dropped.new_capacity_gw.sum()),
        dropped_above_1kw=int((dropped.new_capacity_gw>1e-6).sum()),
        dropped_above_1mw=int((dropped.new_capacity_gw>1e-3).sum())))
s=d[(d.new_capacity_gw>1e-6)&(d.new_capacity_gw<=1e-3)]
out=dict(source=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),sites=len(d),
    between_1kw_1mw=dict(count=len(s),sum_mw=float(s.new_capacity_gw.sum()*1000),
        min_kw=float(s.new_capacity_gw.min()*1e6),max_kw=float(s.new_capacity_gw.max()*1e6)),margins=rows)
(HERE/"source_screen_audit.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
pd.DataFrame(rows).to_csv(HERE/"source_screen_margins.csv",index=False)
print(json.dumps(out,indent=2))
