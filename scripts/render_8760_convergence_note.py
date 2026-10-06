"""Create a three-page Chinese PDF and matching Markdown from audited log data.

Usage: python scripts/render_8760_convergence_note.py --report-dir PATH
Requires reportlab and a Chinese TrueType font; uses only existing small JSON/PNG.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def build_blocks(s):
    if (s["job_id"], s["last_iteration"], s["fingerprint"]) != (4139552, 607, "0xd16b4c7e"):
        raise ValueError("This historical note is specific to job4139552; re-audit narrative for other runs")
    blocks = []

    def add(kind, value, **kwargs):
        blocks.append({"kind": kind, "value": value, **kwargs})

    add("title", "2030 / 8760h · Stage A 收敛日志简报")
    add("meta", "原始任务 job4139552｜2026-08-06—08-26｜归档复核：2026-08-28")
    add("callout", "结论：607次 Barrier 迭代后，求解器返回 OPTIMAL；累计solver耗时20.53天，其中98.84%用于迭代。原LP严格质量仍为HARD_FAIL。Stage B未执行，8月28日的离线恢复不是第二轮求解。")
    add("p", "范围：2030/base、全年8760个连续小时、2025边界状态，空间层采用337个负荷中心。容量扩张与逐时运行联合连续LP，无整数变量；决策覆盖容量、发电、储能与输电，满足供需、运行及碳约束，最小化年度总成本。功率GW、电量GWh、碳MtCO2，目标单位为百万2025年不变价人民币。")
    add("h", "1  模型规模与数值范围")
    labels = {"constraints": "约束行", "variables": "变量列", "nonzeros": "矩阵非零项"}
    add("table", [["项目", "原始LP", "预求解后", "净减少"]] +
        [[labels[r["item"]], f"{r['original']:,}", f"{r['presolved']:,}", f"{r['net_reduction_percent']:.2f}%"] for r in s["dimensions"]], widths=[30, 50, 50, 52])
    add("small", "最终维度取Presolved行。日志另记删除9,308,795列，而前后列数净减少9,291,533；两者口径不同，不能把中途删除数当作最终净减少数。模型指纹0xd16b4c7e。")
    add("image", "figures/01_scale_and_time.png", width_mm=182)
    add("small", "图1｜原矩阵精确极值约1.000486e-6～6250，跨度6.246964e9；Objective跨度3.853190e9，RHS跨度4.518757e12。图中极值按显示精度取舍，CSV保留原始精度。全局比值不是条件数；各行列可能具有不同物理单位。完整presolved系数范围/分布与Kappa未保存/未计算，不能用旧1h模型代替。")
    add("h", "2  阶段时间账本")
    add("table", [["阶段", "实测秒数", "占solver时间", "主要记录"]] + [
        ["模型构建（solver外）", "2,336.984", "不计入", "38分57秒；构建峰48.574 GiB"],
        ["预求解", "17,414.510", "0.9819%", "4小时50分15秒；模型压缩见上表"],
        ["填充约简排序", "2,912.170", "0.1642%", "48分32秒；之后进入迭代初始化"],
        ["其他初始化", "303.506", "0.0171%", "由iter0时间减presolve/ordering得到"],
        ["Barrier：iter0→607", "1,752,971.911", "98.8365%", "20天6小时56分12秒；607个步间隔"],
        ["求解收尾", "4.883", "0.0003%", "末次callback至solver_end，未细分"]], widths=[49, 34, 29, 70])
    add("small", "solver总时长1,773,606.980 s；iter0累计时间20,630.186 s。总作业为8月6日01:17:53至8月26日14:39:04（北京时间），20天13小时21分11秒，含构建与导出收尾。日志摘要的Barrier solved时间也含前处理，不是纯迭代时间。")

    add("page", "")
    add("title", "完整收敛轨迹与里程碑")
    add("meta", "608个记录点 = iter0初值 + 607次迭代｜所有曲线均不平滑、不筛点")
    add("image", "figures/02_barrier_convergence.png", width_mm=182)
    add("small", "图2｜a、c仅用gurobi.log打印残差；b用callback高精度目标值；d为相邻callback时间差，包含该步全部墙钟开销。两种残差通道实际不同，未做拼接；末段放大固定为iter567—607。相对目标差是本报告分析指标，非MIPGap或最优性证书。")
    add("h", "3  从初值到末次迭代")
    add("table", [["迭代", "累计天数", "Primal残差", "Dual残差", "Compl.", "相对目标差"]] +
        [[str(r["iteration"]), f"{r['elapsed_days']:.3f}", f"{r['stdout_primal_infeasibility']:.2e}", f"{r['stdout_dual_infeasibility']:.2e}",
          f"{r['stdout_complementarity']:.2e}", f"{r['relative_objective_difference']:.2e}"] for r in s["milestones"]], widths=[18, 25, 35, 34, 33, 37])
    add("p", "原始stdout的Primal残差由6.77e11降至4.57e-5，Dual由4.42e1降至4.31e-8，Compl.由1.28e11降至4.41e-9。iter593时Compl.首次低于1e-8，但此后Primal/Dual残差出现反弹；不能将单一指标过线解释成全部质量检查通过。")
    add("p", f"实测步间隔中位数{s['iteration_interval_minutes']['median']:.2f}分钟、平均{s['iteration_interval_minutes']['mean']:.2f}分钟，范围{s['iteration_interval_minutes']['min']:.2f}—{s['iteration_interval_minutes']['max']:.2f}分钟；最后100步（507→607）仍消耗{s['last_100_intervals_days']:.3f}天。因此不是只在等待最后一次写盘，长尾主要仍是迭代计算。")
    add("small", "BarConvTol=1e-8控制内部收敛条件，不能机械要求所有打印残差或本报告自定义相对差均低于1e-8。Gurobi记录内部Barrier残差，并将预求解解映射回原问题；原LP质量需要另行查看。[Gurobi Barrier Logging](https://docs.gurobi.com/projects/optimizer/en/current/concepts/logging/barrier.html)")

    add("page", "")
    add("title", "终态质量、资源开销与恢复边界")
    add("h", "4  为什么单步计算如此昂贵？")
    add("table", [["指标", "本轮记录", "解释与限制"]] + [
        ["资源配置", "96分配CPU / 16求解线程", "700 GB申请内存；不能把16线程当作96核全用"],
        ["AA' NZ / Factor NZ", "7.469e8 / 3.395e10", "前者为AA'下三角非对角计数；后者为因子非零数"],
        ["因子运算量 / 内存估计", "1.931e15 / 约300 GB", "排序阶段给出的估计，不是逐步性能测量"],
        ["Dense cols / Free vars", "37,696 / 26", "稠密列与自由变量的结构统计"],
        ["实际进程树峰值RSS", "362.952 GiB", "全过程采样值；构建峰值48.574 GiB"],
        ["Gurobi内存峰值", "354.498 GB（十进制）", "求解器记账，与进程树RSS范围/单位不同"],
        ["用户callback累计时间", "19.27 s / 5,974,796次", "不支持把20天耗时归因于日志回调"]], widths=[53, 57, 72])
    add("p", "解释：预求解后仍有4.04亿非零项，且因子结构达339.5亿非零项，反复处理如此大的线性系统会带来高内存与高计算成本；结合实测每步约48分钟，可解释主要耗时来源。数值跨度大与末段残差反弹提示质量风险，但没有全尺寸条件数/性能剖析，不能把20天全部归因于病态或断言增加核心即可线性加速。")
    add("small", "关键设置：Gurobi13.0.2；Method=2，Crossover=0，SolutionTarget=1，Threads=16，Presolve=2，Aggregate=1，NumericFocus=2，ScaleFlag=2；FeasibilityTol/OptimalityTol=1e-6，BarConvTol=1e-8，BarIterLimit=1000，SoftMemLimit=600 GB，TimeLimit无限。日志预估5000 s/步仅是粗估，非实测。[Gurobi Barrier Logging](https://docs.gurobi.com/projects/optimizer/en/current/concepts/logging/barrier.html)")
    add("h", "5  OPTIMAL与原LP验收必须分开")
    add("table", [["检查层级 / 指标", "最终值", "解释"]] + [
        ["求解器终态", "OPTIMAL / status_code=2", "SolCount=1；nonbasic primal-dual；simplex=0"],
        ["原 / 对偶目标（callback）", "4,188,006.084013813 /\n4,188,005.770454277", "单位：百万2025年不变价人民币"],
        ["目标绝对差 / 相对差", "0.313559536 / 7.487084e-8", "仅本报告分析差值；best_bound记录为null"],
        ["原LP最大约束违反", "2.286829e-5", "高于项目原始primal门槛1e-5"],
        ["原LP最大边界 / 对偶违反", "8.128595e-9 / 9.994176e-7", "不等同于stdout或callback内部残差"],
        ["原LP最大互补性违反", "1.417875e-2", "记录原值；不可用内部Compl.替代"],
        ["项目严格质量 / 科研验收", "HARD_FAIL / false", "数据保留，但未变为已验收论文结果"]], widths=[55, 65, 62])
    add("small", "原LP质量字段是不同变量/约束上的最大值，不能统一标成GW。对照末次callback：Primal=4.765958e-5、Dual=4.661451e-8、Compl.=4.406024e-9；与stdout并非只有打印精度差异。这里不擅自推断其内部缩放公式。")
    add("h", "6  Stage B未运行；离线恢复只补全结果")
    add("p", "本轮Stage A以BarX/BarPi非基解checkpoint结束，原版本跳过完整业务结果导出。Crossover=0，未运行Stage B或第二次优化。8月28日job4396245按保存向量重建原LP并导出，完整变量/约束顺序及指纹匹配；optimize=0、presolve=0，采样时长3,843.847 s、峰值62.061 GiB，不能算入原来的607次迭代。")
    add("p", "恢复后solution_qc为FAIL（58项中56项通过），失败项为unidirectional_interprovincial_flow及objective_components。它与原LP HARD_FAIL是两层检查。恢复成功只表示数据导出完成，不意味着改进了原解、取得基解或通过科研验收；结果与候选跨年状态应保留，是否采用另行判断。")
    add("h", "证据与复现")
    add("small", "原始证据：gurobi.log第38—45行（模型/范围）、3501—3502行（预求解）、3794—3802行（排序/因子）、3806—4413行（轨迹）、4415—4419行（终态）；solver_telemetry.jsonl及build/solve/launch/terminal报告。原模型代码3f739fd6216b1c7fc356e8d3a1d9a257c666f0c5。输入文件SHA256及绝对路径见data/source_sha256.csv；逐步CSV保留日志行号，精确统计见data/summary.json。")
    add("small", "复现脚本：scripts/report_8760_convergence.py → scripts/render_8760_convergence_note.py；命令及环境见本目录README.md。本次仅解析既有日志，没有构建模型、presolve或optimize，也未操作正在运行的其他任务。")
    return blocks


def render(report_dir, font, bold_font):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    import re

    summary = json.loads((report_dir / "data/summary.json").read_text(encoding="utf-8"))
    blocks = build_blocks(summary)
    pdfmetrics.registerFont(TTFont("CN", str(font)))
    pdfmetrics.registerFont(TTFont("CNBold", str(bold_font)))
    styles = {
        "title": ParagraphStyle("title", fontName="CNBold", fontSize=17, leading=23, spaceAfter=7, textColor=colors.HexColor("#163c50")),
        "meta": ParagraphStyle("meta", fontName="CN", fontSize=8, leading=12, spaceAfter=9, textColor=colors.HexColor("#62737e")),
        "h": ParagraphStyle("h", fontName="CNBold", fontSize=10.2, leading=15, spaceBefore=7, spaceAfter=5, keepWithNext=True, textColor=colors.HexColor("#163c50")),
        "p": ParagraphStyle("p", fontName="CN", fontSize=8.8, leading=14, spaceAfter=6, wordWrap="CJK"),
        "small": ParagraphStyle("small", fontName="CN", fontSize=7.4, leading=11, spaceAfter=5, wordWrap="CJK", textColor=colors.HexColor("#4a5963")),
        "callout": ParagraphStyle("callout", fontName="CNBold", fontSize=9, leading=14, spaceAfter=8, borderPadding=7, backColor=colors.HexColor("#eef5f8"), wordWrap="CJK"),
        "cell": ParagraphStyle("cell", fontName="CN", fontSize=7.6, leading=10.6, wordWrap="CJK"),
        "cellhead": ParagraphStyle("cellhead", fontName="CNBold", fontSize=7.6, leading=11, textColor=colors.white, wordWrap="CJK"),
    }

    def markup(value):
        value = html.escape(str(value)).replace("\n", "<br/>")
        return re.sub(r"\[([^\]]+)\]\((https://[^)]+)\)", r'<link href="\2" color="#247A9E">\1</link>', value)

    story, md = [], []
    for block in blocks:
        kind, value = block["kind"], block["value"]
        if kind == "page":
            story.append(PageBreak())
            md.append("\n---\n")
        elif kind == "image":
            img = Image(str(report_dir / value))
            ratio = block["width_mm"] * mm / img.imageWidth
            img.drawWidth, img.drawHeight = img.imageWidth * ratio, img.imageHeight * ratio
            story.extend([img, Spacer(1, 4)])
            md.append(f"![求解日志图]({value})\n")
        elif kind == "table":
            rows = [[Paragraph(markup(cell), styles["cellhead" if i == 0 else "cell"]) for cell in row] for i, row in enumerate(value)]
            table = Table(rows, colWidths=[w * mm for w in block["widths"]], repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#245a72")),
                                      ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f3f6f8"), colors.white]),
                                      ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5),
                                      ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 3.1),
                                      ("BOTTOMPADDING", (0, 0), (-1, -1), 3.1)]))
            story.extend([table, Spacer(1, 5)])
            md.append("| " + " | ".join(value[0]) + " |")
            md.append("| " + " | ".join(["---"] * len(value[0])) + " |")
            md.extend("| " + " | ".join(str(x).replace("\n", "<br>") for x in row) + " |" for row in value[1:])
            md.append("")
        else:
            story.append(Paragraph(markup(value), styles[kind]))
            md.append(("# " if kind == "title" else "## " if kind == "h" else "") + value + "\n")

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#d5e0e6"))
        canvas.line(14 * mm, 13 * mm, 196 * mm, 13 * mm)
        canvas.setFont("CN", 7)
        canvas.setFillColor(colors.HexColor("#62737e"))
        canvas.drawString(14 * mm, 9 * mm, "2030 / 8760h · Stage A    |    已归档日志复核，不是新增求解")
        canvas.drawRightString(196 * mm, 9 * mm, str(doc.page))
        canvas.restoreState()

    target = report_dir / "2030_8760h_StageA_收敛日志简报.pdf"
    doc = SimpleDocTemplate(str(target), pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=13 * mm, bottomMargin=18 * mm, title="2030 / 8760h Stage A 收敛日志简报", author="National_model research log audit")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    (report_dir / "2030_8760h_StageA_收敛日志简报.md").write_text("\n".join(md), encoding="utf-8")
    print(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--font", type=Path, default=Path("C:/Windows/Fonts/msyh.ttc"))
    parser.add_argument("--bold-font", type=Path, default=Path("C:/Windows/Fonts/msyhbd.ttc"))
    args = parser.parse_args()
    if not args.font.exists() or not args.bold_font.exists():
        parser.error("Chinese font missing; specify --font and --bold-font")
    render(args.report_dir, args.font, args.bold_font)


if __name__ == "__main__":
    main()
