"""Publish this review's concise snapshot while preserving prior handoff bytes."""
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
START="<!-- dual_screening_20261002_current_start -->"
END="<!-- dual_screening_20261002_current_end -->"


def read(p):
    with p.open(encoding="utf-8",newline="") as f:return f.read()


def write(p,s):
    with p.open("w",encoding="utf-8",newline="") as f:f.write(s)


def main():
    path=ROOT/"CODEX_HANDOFF.md";old=read(path)
    nl="\r\n" if "\r\n" in old else "\n"
    body=read(HERE/"CURRENT_SNAPSHOT.md").replace("\r\n","\n").strip().replace("\n",nl)
    new=START+nl+body+nl+END
    if START in old:
        i=old.index(START);j=old.index(END,i)+len(END)
        updated=old[:i]+new+old[j:]
    else:
        key="## Current validated snapshot"
        if old.count(key)!=1:raise ValueError("Ambiguous handoff heading")
        updated=old.replace(key,key+nl+nl+new+nl+nl+"## Superseded current-snapshot entries (preserved before the 2026-10-02 screening review)",1)
    if START not in updated:raise AssertionError("Snapshot was not inserted")
    write(path,updated)
    note=("2026-10-02 筛选复核覆盖：Base2050/4844528保持运行，最新只读日志116→117的PInf3.72e3→4.40e11、Compl416→5.15e11；135仍未恢复。"
          "旧“残差持续改善”仅为历史状态。本轮24h联合全候选/筛选加回配对通过物理QC与定价，但无短窗提速；"
          "固定服务器转发上传中途失联，2016h尚未启动，不能登记为通过。下一轮联合独立2030→2060，见SCENARIO_EXECUTION_PLAN_20261002.md；"
          "本轮证据supplementary_materials/reviews/dual_screening_20261002/。云端作业未暂停、改参或新提交。")
    for name in ["MODEL_SERVER_STATUS.md","SERVER_RUNBOOK.md"]:
        p=ROOT/name;s=read(p);newline="\r\n" if "\r\n" in s else "\n"
        marker="<!-- dual_screening_20261002_status -->"
        if marker not in s:
            pos=s.index(newline)+len(newline)
            s=s[:pos]+newline+marker+newline+"> "+note+newline+s[pos:]
            write(p,s)
    marker="## 2026-10-02 对偶筛选独立复核与情景/文档梳理"
    p=ROOT/"CODEX_HANDOFF.md";s=read(p)
    if marker not in s:
        entry=("\n\n"+marker+"\n\n"
          "- Git：0a03cc452e95d158f36923ceb5210267979b6234 + 已有 dirty；不提交/推送，不改核心模型/生产输入。\n"
          "- 范围：用户确认case3完整独立四年路径；Base不中断；2016h隔离资格研究，清理前逐项确认。\n"
          "- 改动：新增SCENARIO_EXECUTION_PLAN_20261002.md、DOCUMENT_STATUS_20261002.md与本轮review；README、config/README、旧架构/路线图加状态标识；规格更正历史短窗预算描述；三交接更新，旧条目原样保留。\n"
          "- 复现：python review/audit_source_screen.py；python review/test_pricing_mechanism.py；RL Python+现有output/portfolio_runtime_gurobi13运行review/run_screen_probe.py --mode solve --hours 24 --start 3960，base/full、case3/full、case3/screen分别独立目录；python review/summarize_experiment.py。review指supplementary_materials/reviews/dual_screening_20261002。\n"
          "- 验证：5机制测试PASS；24h full/restricted/refill物理QC PASS；MPS除20272个new容量上界外逐段SHA相同；100列加回后定价通过，目标相对差6.54e-15。筛选两轮43.839s对完整23.595s，不能宣称提速。24h无新建VRE/柔性签约，局限明确。\n"
          "- 故障保留：首次Windows压缩MPS写出失败（求解前），改用普通MPS/as_posix后重新在v2目录完成；服务器上传中断、SSH握手超时、仅终止自身SCP客户端，2016h未运行。\n"
          "- 云端：只读发现2050/4844528迭代117数值跳升，135仍很大；不停止、不改参，不能把此观察当最终失败。\n"
          "- 未决及下一步：恢复固定服务器转发，核验隔离包和输入，做2016h同参数五轮factor对照并计入重新定价总成本；未授权自动全年投产或削弱QC。删除候选仅6文件，待作者确认。\n")
        write(p,s+entry.replace("\n",nl))


if __name__=="__main__":main()
