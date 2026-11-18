"""Read one snapshot of the explicitly selected node test; no polling loop."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from node_access import powershell

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--version',choices=['v1','v2'],default='v2')
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
foreach($benchPair in @(@('stderr_tail',$benchSource+'\console.stderr.log'),@('gurobi_tail',$benchOut+'\gurobi.log'))) {
    if(Test-Path -LiteralPath $benchPair[1]){$benchResult[$benchPair[0]]=((Get-Content -LiteralPath $benchPair[1] -Tail 8|Where-Object {$_ -notmatch 'WLSACCESSID|WLSSECRET|PASSWORD'}|ForEach-Object {$_.ToString()})-join "`n")}
}
$benchResult|ConvertTo-Json -Depth 7 -Compress
'''.replace('__VERSION__',args.version)
data=json.loads(powershell(code,timeout=45))
root=Path(__file__).resolve().parent
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
snapshots=root/'test_snapshots';snapshots.mkdir(exist_ok=True)
(snapshots/(stamp+'_'+args.version+'.json')).write_text(json.dumps(data,indent=2),encoding='utf-8')
(root/'test_status_latest_20261118.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print(json.dumps(data,ensure_ascii=False,indent=2))
