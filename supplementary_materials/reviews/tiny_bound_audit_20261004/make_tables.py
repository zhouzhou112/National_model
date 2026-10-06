"""Generate report tables directly from verified local cloud outputs."""
from pathlib import Path
import csv
import json

HERE=Path(__file__).resolve().parent
YEARS=[2030,2040,2050]


def table(headers,rows):
    return '\n'.join(['|'+'|'.join(headers)+'|','|'+'|'.join(['---']*len(headers))+'|']+
                     ['|'+'|'.join(str(v) for v in row)+'|' for row in rows])+'\n'


def read_csv(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def main():
    summaries={y:json.loads((HERE/'cloud_results'/f'result_{y}'/f'audit_summary_{y}.json').read_text()) for y in YEARS}
    families={y:{r['family']:r for r in read_csv(HERE/'cloud_results'/f'result_{y}'/f'bound_family_summary_{y}.csv')} for y in YEARS}
    labels={'range_0_1e12':'0 < range ≤ 1e-12','range_1e12_1e9':'1e-12 < range ≤ 1e-9',
            'range_1e9_1e6':'1e-9 < range ≤ 1e-6','range_1e6_1e3':'1e-6 < range ≤ 1e-3',
            'fixed':'range = 0（已固定）','positive_lb_range_lt_1e6':'LB > 0、range < 1e-6（含已固定）',
            'positive_lb_tiny_nonfixed':'LB > 0、0 < range < 1e-6',
            'zero_lb_positive_ub_lt_1e6':'LB = 0、0 < UB < 1e-6','tiny_nonfixed':'0 < range < 1e-6（严格非零）',
            'finite_positive':'有限正区间','infinite_range':'无限区间','tiny_nnz_ge_1000':'非零极小区间中nnz ≥ 1000',
            'tiny_nnz_ge_8760':'非零极小区间中nnz ≥ 8760'}
    text=['## 三年份全模型统计\n',table(['指标','2030','2040','2050'],
          [[v]+[f"{summaries[y]['totals'][k]:,}" for y in YEARS] for k,v in labels.items()])]
    selected=sorted({f for t in families.values() for f,r in t.items() if int(r['tiny_nonfixed'])>0} |
                    {'vre_capacity_gw','vre_new_gw','hydro_capacity_gw','hydro_new_gw','thermal_capacity_gw','thermal_new_gw','storage_capacity_gw','storage_new_gw'})
    text+=['## 重点族：严格非零极小区间\n',table(['变量族','列数（2030/2040/2050）','2030极小区间','2040极小区间','2050极小区间'],
           [[f,' / '.join(families[y].get(f,{}).get('columns','0') for y in YEARS)]+[families[y].get(f,{}).get('tiny_nonfixed','0') for y in YEARS] for f in selected])]
    text+=['## 重点族：四档区间和固定列\n','单元格内依次为2030 / 2040 / 2050。阈值单位为变量原单位。\n',
           table(['族','(0,1e-12]','(1e-12,1e-9]','(1e-9,1e-6]','(1e-6,1e-3]','已固定'],
           [[f]+[' / '.join(families[y].get(f,{}).get(k,'0') for y in YEARS) for k in ['range_0_1e12','range_1e12_1e9','range_1e9_1e6','range_1e6_1e3','fixed']] for f in selected])]
    text+=['## 矩阵系数绝对值范围\n','不含目标函数行；所有族完整min/max见three_year_family_comparison.csv。\n',
           table(['变量族','2030 min — max','2040 min — max','2050 min — max'],
           [[f]+['{} — {}'.format(families[y].get(f,{}).get('matrix_abs_min',''),families[y].get(f,{}).get('matrix_abs_max','')) for y in YEARS] for f in selected])]
    bins=sorted({int(k) for s in summaries.values() for k in s['histogram_log10']})
    text+=['## 全模型log10(range)直方图\n','仅有限正区间，混合变量原单位，只用于数值尺度诊断。\n',
           table(['log10区间','2030','2040','2050'],[[f'[{k}, {k+1})']+[summaries[y]['histogram_log10'].get(str(k),0) for y in YEARS] for k in range(min(bins),max(bins)+1)])]
    for y in YEARS:
        rows=read_csv(HERE/'cloud_results'/f'result_{y}'/f'smallest_50_nonfixed_{y}.csv')
        text+=['## {}：range最小的{}个非固定列\n'.format(y,len(rows)),
               'LB、UB和range保留归档转float64后的完整往返精度；按range升序，同值按原列序。\n',
               table(['名称','LB','UB','range','矩阵非零数'],[[r[k] for k in ['name','lb','ub','range','matrix_nnz']] for r in rows])]
    (HERE/'TABLES_ZH.md').write_text('\n'.join(text),encoding='utf-8')


if __name__=='__main__':main()
