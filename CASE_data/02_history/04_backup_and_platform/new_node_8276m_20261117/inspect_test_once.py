"""Read one snapshot of the explicitly selected node test; no polling loop."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from node_access import powershell

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--version',choices=['v1','v2'],default='v2')
parser.add_argument('--compact',action='store_true')
args=parser.parse_args()
code=r'''
$benchVersion='__VERSION__'
$benchRoot='C:\NationalModelBench\ops_open2050_t32_20261118'
$benchSource=$benchRoot+'\runsource\t32_factor5_'+$benchVersion
$benchOut=$benchRoot+'\runs\t32_factor5_'+$benchVersion
$benchTask='NationalModel_OPS2050_T32_Factor5_20261118_'+$benchVersion
$benchResult=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');version=$benchVersion;task_state=(Get-ScheduledTask -TaskName $benchTask).State.ToString();task_result=(Get-ScheduledTaskInfo -TaskName $benchTask).LastTaskResult}
foreach($benchName in @('controller_started.json','controller_finished.json')) {if(Test-Path -LiteralPath ($benchSource+'\'+$benchName)){$benchResult[$benchName]=Get-Content -LiteralPath ($benchSource+'\'+$benchName) -Raw|ConvertFrom-Json}}
foreach($benchName in @('license_smoke.json','identity_before_optimize.json','terminal.json','external_resources_summary.json')) {if(Test-Path -LiteralPath ($benchOut+'\'+$benchName)){$benchResult[$benchName]=Get-Content -LiteralPath ($benchOut+'\'+$benchName) -Raw|ConvertFrom-Json}}
foreach($benchName in @('resources.jsonl','barrier_iterations.jsonl','external_resources.jsonl')) {if(Test-Path -LiteralPath ($benchOut+'\'+$benchName)){
    $benchRecord=$null
    foreach($benchLine in @(Get-Content -LiteralPath ($benchOut+'\'+$benchName) -Tail 2)) {try{$benchRecord=$benchLine|ConvertFrom-Json -ErrorAction Stop}catch{}}
    $benchResult[$benchName]=$benchRecord
}}
foreach($benchPair in @(@('stderr_tail',($benchSource+'\console.stderr.log')),@('gurobi_tail',($benchOut+'\gurobi.log')))) {
    if(Test-Path -LiteralPath $benchPair[1]){
        try{$benchResult[$benchPair[0]]=((Get-Content -LiteralPath $benchPair[1] -Tail 8 -ErrorAction Stop|Where-Object {$_ -notmatch 'WLSACCESSID|WLSSECRET|PASSWORD'}|ForEach-Object {$_.ToString()})-join "`n")}
        catch{$benchResult[$benchPair[0]+'_read_error']=$_.Exception.Message}
    }
}
$benchResult|ConvertTo-Json -Depth 7 -Compress
'''.replace('__VERSION__',args.version)
data=json.loads(powershell(code,timeout=45))
root=Path(__file__).resolve().parent
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
snapshots=root/'test_snapshots';snapshots.mkdir(exist_ok=True)
(snapshots/(stamp+'_'+args.version+'.json')).write_text(json.dumps(data,indent=2),encoding='utf-8')
(root/'test_status_latest_20261118.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
if args.compact:
    resource=data.get('external_resources.jsonl') or data.get('resources.jsonl') or {}
    data={k:data.get(k) for k in ['utc','version','task_state','task_result','license_smoke.json','terminal.json','barrier_iterations.jsonl','gurobi_tail','stderr_tail','gurobi_tail_read_error','stderr_tail_read_error']} | {
        'stage':(data.get('resources.jsonl') or {}).get('stage'),
        'resource':{k:round(resource[k]/2**30,3) for k in ['rss_bytes','os_lifetime_peak_rss_bytes','private_bytes','available_bytes'] if k in resource},
        'cpu_seconds':resource.get('cpu_seconds'),'threads':resource.get('threads')}
print(json.dumps(data,ensure_ascii=False,indent=2))
