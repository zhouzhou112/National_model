from pathlib import Path
import subprocess,json
remote = r'''
import numpy as np, json, hashlib, pathlib, csv
root=pathlib.Path('/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260828_8760_stagea_recovery_v1/recovered_8760')
source=root/'reservoir_dispatch.npz'
with np.load(source,allow_pickle=False) as data:
    volume=data['active_storage_m3']
    residual=volume-np.roll(volume,1,axis=1)
    for key,sign in [('local_inflow_m3s',-1),('upstream_release_m3s',-1),('turbine_flow_m3s',1),('spill_flow_m3s',1)]:
        values=data[key]
        assert values.shape==volume.shape and np.isfinite(values).all()
        residual+=sign*3600.0*values
    assert np.isfinite(volume).all()
    absolute=np.abs(residual)
    stations=data['hydrochn_row_id'].astype(str)
    hours=data['hour_index']
    pos=absolute.argmax(axis=1)
    table=[dict(hydrochn_row_id=str(stations[i]),maximum_absolute_residual_m3=float(absolute[i].max()),maximum_residual_hour_index=int(hours[pos[i]]),hours_above_1m3=int((absolute[i]>1).sum()),hours_above_10m3=int((absolute[i]>10).sum())) for i in range(volume.shape[0])]
digest=hashlib.sha256()
with source.open('rb') as stream:
    for chunk in iter(lambda:stream.read(8*1024*1024),b''):digest.update(chunk)
qc=json.loads((root/'solution_qc.json').read_text())
report=dict(status='READ_ONLY_SAVED_ARRAY_AUDIT',optimize_called=False,presolve_called=False,remote_writes=False,source=str(source),source_sha256=digest.hexdigest(),hours=volume.shape[1],reservoirs=volume.shape[0],maximum_water_residual_m3=float(absolute.max()),stations_above_1m3=int((absolute.max(axis=1)>1).sum()),station_hours_above_1m3=int((absolute>1).sum()),stations_above_10m3=int((absolute.max(axis=1)>10).sum()),station_hours_above_10m3=int((absolute>10).sum()),reported_overall_qc=qc.get('status'),reported_maximum_water_residual_m3=qc.get('maximum_reservoir_transition_residual_m3'),water_pass_at_current_physical_qc_1m3=bool(absolute.max()<=1),worst=max(table,key=lambda x:x['maximum_absolute_residual_m3']))
print(json.dumps(dict(report=report,stations=table),allow_nan=False))
'''
result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','paracloud-bscc-a8','/publicfs01/fs1-a8/home/a8s001819/.conda/envs/gurobipy310/bin/python -'],input=remote.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120)
if result.returncode:raise RuntimeError(result.stderr.decode(errors='replace'))
payload=json.loads(result.stdout)
out=Path('output/historical_water_20260907/recomputed/cloud_8760_readonly')
out.mkdir(parents=True,exist_ok=False)
(out/'water_balance_audit.json').write_text(json.dumps(payload['report'],indent=2)+'\n')
import csv
with (out/'water_residual_by_station.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=payload['stations'][0].keys());writer.writeheader();writer.writerows(payload['stations'])
print(json.dumps(payload['report'],indent=2))
