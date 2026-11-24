"""Read-only terminal evidence analysis; no model loading, solving or job control."""
from pathlib import Path
import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
import shutil

HERE=Path(__file__).resolve().parent
SNAP=HERE/'status_20261006T154830Z'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path, data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    summary=load(SNAP/'factor_summary.json')
    audit=load(HERE/'terminal_readonly_audit.json')
    members=summary['members']
    receipt=load(SNAP/'receipt.json')['sha256_verified']
    for member,files in load(SNAP/'supplemental_receipt.json').items():receipt[member].update(files)
    for member,files in receipt.items():
        for rel,digest in files.items():
            assert hashlib.sha256((SNAP/member/rel).read_bytes()).hexdigest()==digest,(member,rel)
    accounts={r['JobIDRaw']:r for r in csv.DictReader(io.StringIO(audit['accounting']),delimiter='|')}
    raw_rows=[];timing_rows=[];warnings={}
    for row in members:
        member=row['member'];folder=SNAP/member;log=(folder/'output_8760/gurobi.log').read_text(encoding='utf-8')
        warnings[member]=[line for line in log.splitlines() if 'warning' in line.lower()]
        telemetry={int(r['iteration']):r for r in map(json.loads,(folder/'output_8760/solver_telemetry.jsonl').read_text().splitlines()) if r.get('phase')=='barrier'}
        printed={}
        for line in log.splitlines():
            fields=line.split()
            if len(fields)==7 and fields[0].isdigit() and fields[-1].endswith('s'):
                try:
                    values=[float(v) for v in fields[1:6]];runtime=int(fields[6][:-1])
                except ValueError:continue
                i=int(fields[0]);printed[i]=dict(zip(['primal_objective','dual_objective','primal_inf_log','dual_inf_log','complementarity'],values),member=member,iteration=i,log_runtime_seconds=runtime)
        assert set(printed)==set(telemetry)==set(range(6)),member
        for i in range(6):
            record=telemetry[i];p=printed[i];raw_rows.append(p)
            # Printed time is rounded to integer seconds; allow that granularity.
            assert abs(p['log_runtime_seconds']-record['runtime_seconds'])<=1.1
            if i:
                delta=record['runtime_seconds']-telemetry[i-1]['runtime_seconds']
                work=record['work_units']-telemetry[i-1]['work_units']
                assert delta>0 and work>0
                timing_rows.append(dict(member=member,iteration=i,seconds=delta,work=work,
                    log_seconds=p['log_runtime_seconds']-printed[i-1]['log_runtime_seconds']))
        terminal=row['terminal'];params=row['actual_parameters'];gate=audit['members'][member]
        assert terminal['status_code']==7 and terminal['barrier_iterations']==5
        assert terminal['scientific_acceptance_mode']=='NONE' and terminal['result_use']=='TEST_ONLY_FACTOR_SCREEN'
        assert not terminal['production_state_written'] and not terminal['publication_accepted'] and terminal['qc']=='NOT_EVALUATED'
        assert not gate['forbidden_outputs'] and gate['stderr_bytes']==0 and gate['release_hash_check_exit_code']==0
        assert params['Threads']==48 and params['BarIterLimit']==5
        acct=accounts[gate['job']];batch=accounts[gate['job']+'.batch']
        assert acct['State']=='COMPLETED' and acct['ExitCode']=='0:0' and acct['AllocCPUS']=='64'
        row['slurm']=acct;row['wall_seconds']=int(acct['ElapsedRaw'])
        row['node_hours']=row['wall_seconds']/3600
        row['allocated_core_hours']=int(acct['CPUTimeRAW'])/3600
        row['slurm_peak_rss_gib']=int(batch['MaxRSS'].rstrip('K'))/1024**2
        usage=(folder/'resource_usage.txt').read_text()
        row['gnu_time_peak_rss_kib']=int(re.search(r'Maximum resident set size \(kbytes\):\s*(\d+)',usage)[1])
        row['gnu_time_peak_rss_gib']=row['gnu_time_peak_rss_kib']/1024**2
        row['barrier_work_at_iteration5']=telemetry[5]['work_units']
        row['log_mean_2_to_5_seconds']=(printed[5]['log_runtime_seconds']-printed[1]['log_runtime_seconds'])/4
    assert members[0]['actual_parameters']==members[1]['actual_parameters']
    assert summary['only_vre_new_bounds_can_differ'] and summary['source_files_sha_equal']
    assert summary['input_identity_equal_after_member_path_normalization']
    screen=load(SNAP/'member_S/output_8760/build_report.json')['vre_screen']
    with (SNAP/'member_S/output_8760/candidate_selection.csv').open(encoding='utf-8-sig',newline='') as stream:
        selection=list(csv.DictReader(stream))
    identities={(r['grid_uid'],r['technology']) for r in selection}
    assert len(selection)==len(identities)==screen['sites']==36686
    removed=[r for r in selection if r['screened_out']=='True']
    assert all((float(r['rc_ratio'])>=.2 and float(r['original_new_ub_gw'])>0)==(r['screened_out']=='True') for r in selection)
    assert len(removed)==screen['fixed_columns']==20272
    assert math.isclose(math.fsum(float(r['original_new_ub_gw']) for r in removed),screen['fixed_headroom_gw'],rel_tol=1e-12)
    assert sum(float(r['original_new_ub_gw'])>0 and r['screened_out']=='False' for r in selection)==14167
    for name,rows in [('barrier_log_iterations.csv',raw_rows),('barrier_iteration_costs.csv',timing_rows)]:
        with (HERE/name).open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    ratio=summary['time_ratio_S_over_F'];dense_ratio=summary['dense_cols_ratio_S_over_F']
    assert ratio<=.75 and members[1]['Dense cols']==17413 and members[0]['Dense cols']==37678
    assessment=dict(decision='PASS_FACTOR_SCREEN_GATE',rule='Task section 0: mean runtime ratio <=0.75 and clearly lower Dense cols',
        reviewed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),time_ratio_S_over_F=ratio,
        mean_iteration_time_reduction_fraction=1-ratio,dense_cols_ratio_S_over_F=dense_ratio,
        dense_cols_reduction_fraction=1-dense_ratio,mechanism_evidence='37678 -> 17413; screened value lies in preregistered expected 16000-18000 range',
        scientific_acceptance=False,full_year_scenario_launched=False,convergence_assessed=False,
        source_snapshot=SNAP.name,raw_file_sha_checks=sum(map(len,receipt.values())),screen=screen,members=members,
        total_node_hours=sum(r['node_hours'] for r in members),total_allocated_core_hours=sum(r['allocated_core_hours'] for r in members),
        price_verified=False,currency_cost=None,log_warnings=warnings,
        residual_note='Text-log residuals and callback BARRIER_PRIMINF/BARRIER_DUALINF are kept separately; no equivalence of their numerical scales is assumed.')
    dump(HERE/'final_assessment.json',assessment)
    F,S=members
    def percent(a,b):return f'{(b/a-1)*100:+.2f}%'
    metrics=[
        ('Presolved rows',f"{F['presolved_rows']:,}",f"{S['presolved_rows']:,}",percent(F['presolved_rows'],S['presolved_rows'])),
        ('Presolved cols',f"{F['presolved_cols']:,}",f"{S['presolved_cols']:,}",percent(F['presolved_cols'],S['presolved_cols'])),
        ('Presolved nnz',f"{F['presolved_nnz']:,}",f"{S['presolved_nnz']:,}",percent(F['presolved_nnz'],S['presolved_nnz'])),
        ('Dense cols','37,678','17,413',percent(F['Dense cols'],S['Dense cols'])),
        ("AA' NZ",'7.561e8','6.608e8',percent(F["AA' NZ"],S["AA' NZ"])),
        ('Factor NZ','3.531e10','2.539e10',percent(F['Factor NZ'],S['Factor NZ'])),
        ('Factor Ops','2.055e15','1.070e15',percent(F['Factor Ops'],S['Factor Ops'])),
        ('Presolve / s',f"{F['presolve_seconds']:.2f}",f"{S['presolve_seconds']:.2f}",percent(F['presolve_seconds'],S['presolve_seconds'])),
        ('Ordering / s',f"{F['ordering_seconds']:.2f}",f"{S['ordering_seconds']:.2f}",percent(F['ordering_seconds'],S['ordering_seconds'])),
        ('第1轮 / s',f"{F['iteration_1_seconds']:.6f}",f"{S['iteration_1_seconds']:.6f}",percent(F['iteration_1_seconds'],S['iteration_1_seconds'])),
        ('第2–5轮均值 / s',f"{F['mean_iteration_2_to_5_seconds']:.6f}",f"{S['mean_iteration_2_to_5_seconds']:.6f}",percent(F['mean_iteration_2_to_5_seconds'],S['mean_iteration_2_to_5_seconds'])),
        ('第2–5轮平均Work',f"{F['mean_iteration_2_to_5_work']:.6f}",f"{S['mean_iteration_2_to_5_work']:.6f}",percent(F['mean_iteration_2_to_5_work'],S['mean_iteration_2_to_5_work'])),
        ('iter5累计Work',f"{F['barrier_work_at_iteration5']:.6f}",f"{S['barrier_work_at_iteration5']:.6f}",'含此前预处理，不等于五轮增量'),
        ('solver_end总Work',f"{F['terminal']['work_units']:.6f}",f"{S['terminal']['work_units']:.6f}",'含收尾，不作为每轮代价'),
        ('Slurm MaxRSS / GiB',f"{F['slurm_peak_rss_gib']:.3f}",f"{S['slurm_peak_rss_gib']:.3f}",'调度采样'),
        ('GNU time峰值RSS / GiB',f"{F['gnu_time_peak_rss_gib']:.3f}",f"{S['gnu_time_peak_rss_gib']:.3f}",percent(F['gnu_time_peak_rss_gib'],S['gnu_time_peak_rss_gib'])),
        ('Slurm elapsed','08:43:56','06:08:57','五轮测试总wall；不外推全年'),
    ]
    table='\n'.join('|'+ '|'.join(r)+'|' for r in metrics)
    costs='\n'.join(f"|{i}|"+'|'.join(f"{next(r for r in timing_rows if r['member']==m and r['iteration']==i)[k]:.6f}" for m,k in [('member_F','seconds'),('member_S','seconds'),('member_F','work'),('member_S','work')])+'|' for i in range(1,6))
    trajectory='\n'.join(f"|{r['member'][-1]}|{r['iteration']}|{r['primal_objective']:.8e}|{r['dual_objective']:.8e}|{r['primal_inf_log']:.3e}|{r['dual_inf_log']:.3e}|{r['complementarity']:.3e}|" for r in raw_rows)
    old=HERE/'REVIEW_PRE_TERMINAL_ZH.md'
    if not old.exists():shutil.copy2(HERE/'REVIEW_ZH.md',old)
    text=f'''# 8760h 对偶初筛五轮 Factor 配对：最终报告

**判定：通过本次 factor-screen 门槛。** 初筛S第2–5轮平均674.580974秒，完整F为1110.308785秒，S/F={ratio*100:.4f}%≤75%；Dense cols从37,678降至17,413（下降{(1-dense_ratio)*100:.4f}%），达到预期16–18k，未触发“Dense cols无明显下降则封存”的否决条款。

这只证明本组真实8760h LP前五轮中每轮计算代价下降。两者Gurobi均status7、BarIterCount5、Iteration limit reached；没有收敛、科学QC、影子价格或规划状态结论。按任务书第5节，**没有自动启动全年case3科学情景；正式采用、遗漏列重新定价与加回重解仍待另行授权**。

## 实验范围与终态

- 情景：case3_thermal_ev_v5，V9显式派生配置；planning_year2030、boundary2025、8760h/start0，逐小时周期边界，31省与原V9空间结构/单位沿用。决策变量、目标函数、约束和数据不变，S只限制未保留站点的vre_new上界为0。
- 保留既有连续LP的风光/水电/火电/储能/输电容量、小时运行和柔性服务签约决策；目标仍最小化年度系统总成本（million 2025 CNY/year），既有负荷平衡、备用/惯量、碳排放、储能SOC及水库水量等约束不变。功率/容量GW、电量GWh、时间步长1h；风光0.25°网格，水电坝址及原省/城市电网结构沿用。输入为冻结V9技术经济/资源/负荷/CF/水文/波浪与V5冷热/EV数据；本报告的输出指标是Factor规模、Runtime秒、Work和RSS，不是规划装机或发电量。
- 原始两LP均54,217,462行、43,761,608列、501,902,601非零；F保留全部36,686站原有边界，S按grid_uid × technology一对一对齐后保留14,167个当前可扩展站，20,272个正headroom列置零，累计限制headroom39,341.39949215136 GW；已有容量下界不变。
- 两节点均AMD EPYC9554、128物理/逻辑核、amd_a8_768，实际AllocTRES cpu64/mem750G/node1/billing64；Gurobi13.0.2、48线程、Seed0。
- 两成员实际参数全部一致：Method2、NF2、Scale2、Presolve2、Aggregate1、Crossover0、SolutionTarget1、BarConvTol1e-4、BarIterLimit5、BarHomogeneous−1；TimeLimit/SoftMemLimit/MemLimit/WorkLimit均无限，Slurm无限时且no-requeue。
- 两成员均COMPLETED/0:0，stderr为0B，原release_files.sha256终态重验通过；没有改动、停止或重提4844528，没有额外云作业。本轮终态阶段没有本机模型求解或测试。

|成员|job id / 节点|开始（英国）|结束（英国）|Slurm wall|
|---|---|---|---|---|
|F完整|4981130 / m4cg1707|10月5日18:12:35|10月6日02:56:31|8:43:56|
|S初筛|4981131 / m4cg1801|10月5日18:12:35|10月6日00:21:32|6:08:57|

终态原始证据：[{SNAP.name}/]({SNAP.name}/)，共{assessment['raw_file_sha_checks']}份取回文件逐bytes匹配远端SHA。精确scheduler记录及无科学产物清单见[terminal_readonly_audit.json](terminal_readonly_audit.json)。

## 配对指标与逐轮代价

|指标|F完整|S初筛|变化/口径|
|---|---:|---:|---|
{table}

计时使用callback Runtime精确值：第i轮=Runtime_i−Runtime_(i−1)，第2–5轮均值=(Runtime5−Runtime1)/4，排除Presolve、Ordering及iter0前开销。Work同样差分。Gurobi文本秒级时间独立复算均值F1110.25s/S674.75s，与精确口径在整数日志分辨率内一致，不改变判定。Factor统计按日志显示精度记录，不能增加虚假有效位。

|轮次|F秒|S秒|F Work增量|S Work增量|
|---|---:|---:|---:|---:|
{costs}

源码/输入/参数与原LP非边界部分一致，加上Dense下降53.78%、Factor Ops下降47.93%、Factor NZ下降28.09%，支持“被固定候选减少进入因子分解的稠密容量列，从而降低每轮代价”的机制。没有把短窗结果替代8760，也没有把本次39.24%的前五轮每轮降幅外推为完整求解倍率：后续轮数、重新定价与加回重解代价均未测量。

RSS分别报告Slurm采样与GNU time峰值；二者取样方式不同。monitor进程树峰值F705.154GiB/S679.566GiB另保留在solve_report。callback MEMUSED/MAXMEMUSED是另一个内部记账指标，不当作RSS，也不据其与物理内存的差异推断OOM；实际Slurm均正常终态，GNU time Swaps均0。

## 逐轮目标与残差（仅记录）

以下严格转录Gurobi文本日志显示值。callback BARRIER_PRIMINF/BARRIER_DUALINF与文本列数值不同，因此原始callback CSV另存，**不混用两种残差口径，也不猜测差异原因或评估五轮收敛**。例如F iter0文本PInf/DInf为1.23e11/82.9，而callback约3.14095e11/3.56829e7。

|成员|轮次|P|D|PInf（log）|DInf（log）|Compl（log）|
|---|---:|---:|---:|---:|---:|---:|
{trajectory}

文本原值CSV：[barrier_log_iterations.csv](barrier_log_iterations.csv)；精确代价：[barrier_iteration_costs.csv](barrier_iteration_costs.csv)；callback全部原值：[{SNAP.name}/barrier_iterations.csv]({SNAP.name}/barrier_iterations.csv)。没有读取X/BarX或发布BarPi，终态产物清单确认不存在planning_state、solution_qc、solution_snapshot或barrier_checkpoint。

## 身份与门禁证据

|门禁|结果|证据|
|---|---|---|
|V9源码|云源196个py/json/csv/sh/sbatch文件冻结；仅5个接口/配置/测试文件增改；F/S实际源码SHA全同，终态release散列复验PASS|cloud_source_repo_sha256.json、cloud_payload/、payload_sha256.json、各source_identity.json及terminal_readonly_audit.json|
|数值任务隔离|云包未混入A/B/C；BarHomogeneous−1，无年度分段或新headroom开关启用|原source_identity与参数回读|
|输入|80条input_manifest记录仅规范化member路径后全同；相同data_overlay/CF/hydro/wave roots|各input_manifest.csv、run_environment.json|
|源筛选CSV|SHA fe5d87a2adc6f5d6b8ad21606c571979312c1f632780fcdc9ea7500b7f0f2368；36,686条唯一身份，rc_ratio和当前headroom逐行重算PASS|S/candidate_selection.csv、build_report.json、final_assessment.json|
|真实1h门禁|ROWS/COLUMNS/RHS/目标SHA相同，仅20,272个vre_new上界置零|one_hour_pair_identity.json、gate_F/、gate_S/|
|两行真实Gurobi入口|3项PASS；不写QC/状态；两计算节点重跑也PASS|fixture日志、各startup_regression.log|
|真实8760 MPS|ROWS/COLUMNS/RHS/目标与非vre_new bounds段SHA相同；仅BOUNDS_VRE_NEW不同|各mps_section_sha256.json；下表|
|全套回归|412 tests /112.906s /OK /skip1（Windows无/proc）/exit0/source_unchanged=true|../validation_coordination_20261005/unittest_verified_20261005T185140Z.log及.json|

完整回归日志SHA：bf65c47c52747ef14fb6385b1c1518e822d5f7af1c0771c2b4b98a7077fa2d79。本机18:23蓝屏前中断轮次未计为通过，用户恢复授权后的串行重测证据独立保留。该事件不影响两个Slurm作业。

|MPS段|两成员共同SHA256|
|---|---|
|ROWS|32801212fcc23dd8897017360b9efd576e409fd0d3369fcb839b83910cb7edb4|
|COLUMNS（含目标）|e5266fd7a996062e2fd34de75c4f78bd9950e5da16d2913201480fd5f3f1c4a4|
|RHS|6ef4b21b7eb61823f8d639af20dd002b9b67618a1040c35507bbad2376c0c1e7|
|BOUNDS_OTHER|9c5ea9801c62cf3608065c4bde1845e17047d5e5b76b43113c6f30e9ef629126|

原MPS本体留在云端各成员output_8760/model_archive/，未下载数GB归档：F4,143,651,443 bytes，SHA9f426316dff40fa03398c24f6d675249edd02176380ee66c5110a1a1fde24460；S4,143,496,357 bytes，SHAe2861cfc3612eef82450b626c1fce0a4963ca1573fe800a4b2a18d38afdf258f。原归档manifest哈希与文件字节数已保存；本轮不重复读取8GB归档重算文件SHA，8760段SHA来自计算节点optimize前的流式读取。两份parameters.prm均185 bytes/SHA b57fdfe28a198b08ee3f01f87cc9a8a70998a5e589fbbedb510a71dd51ba4842，原PRM亦已取回。

## 资源费用与任务书差异

Slurm资源账：F{F['node_hours']:.6f}节点小时、{F['allocated_core_hours']:.6f}分配核时；S{S['node_hours']:.6f}节点小时、{S['allocated_core_hours']:.6f}分配核时；合计{assessment['total_node_hours']:.6f}节点小时、{assessment['total_allocated_core_hours']:.6f}分配核时。核时只取主作业CPUTimeRAW，不能再把batch/extern同一分配重复相加。账单单价未核验，货币费用记未知；作者事前18节点小时是估计，并非本次实际账单。

1. 任务书14,170来自源headroom>1e-6口径；当前V9已有1e-5GW cutoff，三个DPV候选原余量5.852501e-6、3.721000e-6、6.052454e-6GW被原规则归零，故实际14,167。没有为凑数改变V9。source_vs_current_headroom_difference.csv还含机器精度/更小微量行，不把57行全称作这3站。
2. held时AllocTRES为空：采用held核ReqTRES→release→batch核AllocTRES和内存通过才构建/求解。任务书文字顺序在未分配资源前无法直接核AllocTRES。
3. 本机归档实为original.mps，云为original.mps.gz；段解析兼容两者。frozen_local是1h门禁执行副本，其runner已加入接口，不称为未改动before；起始SHA另存，云正式测试基线直接复制V9源。
4. 旧runner嵌套primary_checkpoint_requested仍按SolutionTarget1记true；factor专用路径提前返回，实际无checkpoint/QC/状态，顶层TEST_ONLY_FACTOR_SCREEN/NONE正确。云包保持不可变，未为修饰字段热改正在运行的代码。
5. 文本日志与callback残差不同口径分别保存；sstat在作业结束后报告找不到活动step，这是终态查询差异，不是作业失败。终态内存取sacct与GNU time。

## 复现与最终处置

在本目录执行`python summarize.py {SNAP.name}`生成机械提取表，再执行`python finalize_report.py`重算终态身份/时间/资源与本报告；只读取已有小文件，不构建或求解模型。final_assessment.json为最终人工规则判定，factor_summary.json的PENDING字段仅表示机械提取器不擅自定义“明显下降”的新阈值，不覆盖本报告结论。部署命令和sbatch留在deploy.py/factor.sbatch/cloud_payload中，**不得再次运行submit/release**。

**逐项一句话判定：时间门槛通过（60.7562%≤75%）；稠密列机制通过（37,678→17,413）；配对身份通过（只变vre_new上界）；科学接受不适用（五轮上限、无QC）；自动正式投产未执行（后续采用另行授权）。** 本任务没有否决参数，因此不向FULL_YEAR_SOLVER_DECISION_20260817.md追加虚假的否决项；其他数值任务的否决独立维护。

本轮实验没有未完成的Factor证据项；未完成的是实验之外的完整收敛、重定价/加回策略与科学验收。早期状态与故障过程保留于[REVIEW_PRE_TERMINAL_ZH.md](REVIEW_PRE_TERMINAL_ZH.md)和各日期快照。
'''
    (HERE/'REVIEW_ZH.md').write_text(text,encoding='utf-8')
    evidence=[p for p in SNAP.rglob('*') if p.is_file()]+[HERE/name for name in ['REVIEW_ZH.md','final_assessment.json','barrier_log_iterations.csv','barrier_iteration_costs.csv','terminal_readonly_audit.json','finalize_report.py','summarize.py']]
    dump(HERE/'terminal_delivery_manifest.json',{p.relative_to(HERE).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(evidence)})
    print(json.dumps({k:assessment[k] for k in ['decision','time_ratio_S_over_F','dense_cols_ratio_S_over_F','raw_file_sha_checks','total_node_hours','total_allocated_core_hours']},indent=2))


if __name__=='__main__':main()
