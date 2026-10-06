"""Summarize all retained probes; failed and incomplete runs remain visible."""
from pathlib import Path
import csv
import json

OUT=Path(__file__).parent


def master_status(qc):
    if not qc:return 'NOT_EVALUATED'
    residuals=['maximum_center_balance_residual_gwh','maximum_province_net_exchange_residual_gwh',
               'maximum_intra_capacity_violation_gwh','maximum_vre_annual_availability_violation_gwh',
               'maximum_ror_annual_availability_violation_gwh']
    return 'PASS' if (all(qc.get(k,float('inf'))<=1e-5 for k in residuals)
        and qc.get('bidirectional_active_edge_count',1)==0 and qc.get('dpv_spur_augmentation_max_gw',float('inf'))<=1e-8) else 'HARD_FAIL'


def main():
    rows=[]
    for folder in sorted((OUT/'probes').iterdir()):
        if not folder.is_dir():continue
        path=folder/'result.json'
        if not path.exists():
            rows.append(dict(probe=folder.name,status='INCOMPLETE_ARTIFACT',full_cf_design=False))
            continue
        r=json.loads(path.read_text(encoding='utf-8'));raw=r['raw'];qc=r.get('physical_export_qc',{})
        ms=master_status(qc.get('master',{}));os=qc.get('operational_status','NOT_EVALUATED')
        rows.append(dict(probe=folder.name,full_cf_design=r.get('compute_max_cf',False),
            status={2:'OPTIMAL',9:'TIME_LIMIT',12:'NUMERIC',13:'SUBOPTIMAL'}.get(r['status'],str(r['status'])),
            solve_seconds=r['runtime'],barrier_iterations=r['barrier_iterations'],
            objective=r.get('objective'),raw_max_row_violation=r.get('raw_max_row_violation'),
            bound_violation=r.get('bound_violation'),dual_violation=r.get('dual_violation'),
            coefficient_min=raw['coefficient_min_abs'],coefficient_max=raw['coefficient_max_abs'],
            coefficient_ratio=raw['coefficient_max_abs']/raw['coefficient_min_abs'],
            min_bound=raw.get('min_bound'),max_bound=raw.get('max_bound'),
            master_qc=ms,operational_qc=os,
            business_hard_checks=len(qc.get('hard_checks') or {}),
            failed_business_checks=';'.join(k for k,v in (qc.get('hard_checks') or {}).items() if not v),
            strict_acceptance=bool(r['status']==2 and ms=='PASS' and os=='PASS'
                and r.get('raw_max_row_violation',float('inf'))<=1e-5
                and r.get('bound_violation',float('inf'))<=1e-5 and r.get('dual_violation',float('inf'))<=1e-5),
            export_error=r.get('physical_export_error',''),archive_error=r.get('archive_error','')))
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with (OUT/'probe_summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    lines=['# 局部验证记录（自动由 result.json 汇总）','',
           '原始约束、变量界和对偶误差采用 1e-5 的既有严格质量门槛；城市层和小时业务检查同时通过才标记完整通过。',
           '所有实验在同一台本地 i9-14900HX、Gurobi 13.0.2、8 线程下串行执行。局部窗口不代表全年运行。','',
           '| 测试目录 | 全年 CF 送出设计 | 终态 | 求解秒 | 原行最大误差 | 城市 QC | 小时 QC | 完整通过 |',
           '|---|---|---|---:|---:|---|---|---|']
    for r in rows:
        seconds=f"{r['solve_seconds']:.3f}" if r.get('solve_seconds') is not None else '—'
        residual=f"{r['raw_max_row_violation']:.3e}" if r.get('raw_max_row_violation') is not None else '—'
        lines.append(f"| {r['probe']} | {r.get('full_cf_design',False)} | {r['status']} | {seconds} | {residual} | {r.get('master_qc','—')} | {r.get('operational_qc','—')} | {r.get('strict_acceptance',False)} |")
    lines.extend(['','早期目录 `capped_nf2_24h_s0_cross0` 的日志显示 Barrier OPTIMAL，但 MPS 压缩写出异常使 result.json 未完成，保留为不完整证据。',
        '`cleaned_nf2_24h_s0_cross0` 在配置校验处退出，后续版本修正了显式科学基准 ID 的兼容校验；未进行求解。',
        '早期 compute_max_cf=False 的结构测试不纳入生产送出设计的性能比较。',
        '带 `_final` 的测试采用最终完整精确零小时识别；此前 fullcf 测试只对独立站小时识别精确零。',
        '早期 Crossover=0 的解若只有小时 QC PASS、城市 QC HARD_FAIL，必须视为未完整验收。',
        '矩阵跨度改善并不等于条件数已被证明健康；保留小的有意义既有容量与目标项。未构建或求解新的 8760h LP。',''])
    (OUT/'VALIDATION_ZH.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(rows,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
