"""Audit all changed transfer hours, conservative energy ceilings and groups."""
from pathlib import Path
import copy,json,sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import numpy as np
from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.hydro import HydroProfileReader
from cispo_model.timeblocks import TimeBlock
from cispo_model.numerical_cleanup import cyclic_inventory_upper_m3
from probe_annual_water import components


def main():
    out=Path(__file__).resolve().parent
    c0=load_model_config(path='config/optimization_2030_numeric_simplified_no_dac_v6.json')
    c1=load_model_config(path='config/optimization_2030_numeric_final_v8.json')
    data=load_model_data(c1)
    with HydroProfileReader(c0,data) as reader:old=reader.read_linear_block(TimeBlock(0,0,8760))
    with HydroProfileReader(c1,data) as reader:new=reader.read_linear_block(TimeBlock(0,0,8760))
    np.testing.assert_array_equal(old.reservoir_local_inflow_m3s,new.reservoir_local_inflow_m3s)
    full=copy.copy(old);full.reservoir_active_storage_m3=np.full(620,np.finfo(float).max/100)
    budgets=cyclic_inventory_upper_m3(full)
    loss_volume=np.zeros(620);changed_stations=set();hours=set();minimum=np.inf;maximum=0.
    audit=copy.deepcopy(new.cascade_reconciliation_audit['cascade_transfer_cleanup'])
    for e,src in enumerate(old.cascade_edge_source_local_rows):
        dropped=old.cascade_edge_transfer_fraction[e]-new.cascade_edge_transfer_fraction[e]
        if np.any(dropped<0):raise ValueError('Cleanup added a transfer')
        if np.any(dropped>0):
            changed_stations.update(map(int,src));changed_stations.update(map(int,old.cascade_edge_target_local_rows[e]))
            hours.update(map(int,np.flatnonzero(dropped>0)))
            bound=float(budgets[src].sum()*dropped.max())
            for target,w in zip(old.cascade_edge_target_local_rows[e],old.cascade_edge_target_weights[e]):
                loss_volume[target]+=bound*float(w)
        for w in new.cascade_edge_target_weights[e]:
            coef=3.6*float(w)*new.cascade_edge_transfer_fraction[e];positive=coef[coef>0]
            if len(positive):minimum=min(minimum,float(positive.min()));maximum=max(maximum,float(positive.max()))
    lost=copy.copy(full);lost.reservoir_local_inflow_m3s=np.zeros((620,8760));lost.reservoir_local_inflow_m3s[:,0]=loss_volume/3600
    propagated=cyclic_inventory_upper_m3(lost)
    energy=float(propagated@old.reservoir_generation_conversion_gw_per_m3s/3600)
    groups=components(new);affected=[i for i,g in enumerate(groups) if changed_stations.intersection(g)]
    audit.update(affected_groups=affected,changed_model_hours=sorted(hours),
        minimum_remaining_cascade_coefficient=minimum,maximum_cascade_coefficient=maximum,
        conservative_including_downstream_energy_upper_gwh=energy,
        source_to_target_water_loss_upper_m3=float(loss_volume.sum()),local_inflow_unchanged=True,
        first_24h_transfer_arrays_unchanged=all(np.array_equal(a[:24],b[:24]) for a,b in zip(old.cascade_edge_transfer_fraction,new.cascade_edge_transfer_fraction)),
        first_168h_transfer_arrays_unchanged=all(np.array_equal(a[:168],b[:168]) for a,b in zip(old.cascade_edge_transfer_fraction,new.cascade_edge_transfer_fraction)),
        interpretation_of_upper_bound='Each source may release its entire safe annual water budget during a removed-fraction hour; propagate resulting maximum losses downstream. This is deliberately conservative and is not a national dispatch-loss estimate.')
    (out/'transfer_cleanup_budget.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print(json.dumps(audit,indent=2),flush=True)


if __name__=='__main__':main()
