# 三个全年Base归档的极小界审计

本目录仅包含数值诊断工具与证据，不改变任何科研模型、源数据或求解参数。读取三个归档original.mps.gz，无BarPi、无求解器调用。生产作业4844528不在本工具的作业控制范围内。

## 入口

- `audit_bounds.py --inputs inputs.json --year YEAR --out NEW_OUTPUT_DIR`：仅在已分配的计算节点运行，先验证归档字节数/SHA256，再流式解析；既有输出目录会被拒绝，避免覆盖证据。
- `test_audit_bounds.py`：本地小型合成MPS机制检查，保留每次fixture输出。
- `dispatch.py`：已执行一次，提交三个指定规格的小作业；有提交尝试标记后拒绝再次提交，不能直接重跑。
- `status.py`：只用squeue/sacct查看这三个审计作业并保存快照。
- `collect.py`：完成后取回结果及Slurm日志，逐文件核对远端输出manifest的bytes/SHA；不下载原始MPS或scratch。
- `compare_results.py`：只读本地结果，复算计数、区间和，再生成三年份并排CSV和物理量影响摘要。

每个Slurm作业：`amd_m8_768-a`、4 CPU、16G、02:00:00；调度收据见`submission_receipt.json`。环境只source用户指定的既有loader，并使用其中的`$PYTHON`；不打印环境变量、不读取许可文件。

## 统计口径

默认LB=0、UB=+inf，按出现顺序应用UP/LO/FX/MI/PL/FR。只支持本任务的Gurobi自由格式连续LP；不支持的整数/二次等格式报错。默认界也计入全模型列数。矩阵非零和绝对系数min/max排除目标函数行及显式零。

`range_0_1e12`对应`0<UB-LB<=1e-12`，随后三档依次为`(1e-12,1e-9]`、`(1e-9,1e-6]`、`(1e-6,1e-3]`。字段名中的1e12/1e9等表示这里说明的负指数阈值。`tiny_nonfixed`严格为`0<range<1e-6`，因此不包含恰好1e-6者。所有比较均基于归档十进制文本转float64后的值，不擅自四舍五入。

`positive_lb_range_lt_1e6`按用户原表达式，包含正下界的已固定列；`positive_lb_tiny_nonfixed`额外排除已固定，供风险分析。正下界不能单独证明继承因果。`zero_lb_positive_ub_lt_1e6`严格按LB=0且0<UB<1e-6。

`tiny_bound_columns_YEAR.csv`遵循“range<1e-6的全部列”，包含固定列，并以`is_fixed`标注。讨论“几乎固定”时必须筛选is_fixed=0。最小50列与非零数分布只统计严格非零极小区间。直方图使用log10(range)的整数左闭右开分箱，排除固定与无限区间。

阈值首先按各变量原单位统计；GW、GWh、m3/s等不能混合解释为装机。影响摘要单列GW容量列，配对的capacity/new不能重复算作物理损失。`>=1000`和`>=8760`个非零仅作描述性稠密列筛查，不等同Gurobi内部Dense cols分类。

## 验证和局限

归档必须COMPLETE/errors为空，压缩字节和SHA与manifest完全一致；解析前后文件mtime/bytes保持。名称哈希全列唯一且每个界查询以原始名称再核验；0界、有限正区间和无限区间计数守恒，直方图/非零分布计数守恒，维度及矩阵非零数须与各自Gurobi启动日志完全一致。局部fixture覆盖六种界规则、阈值端点、稠密列、目标项排除和错误拒绝。

解析器是原始LP审计，不读取预求解矩阵、内部缩放、KKT条件数或Barrier重启决策。不能由原始窄区间直接证明其保留到Barrier阶段，也不能把删除这些列的原始nnz当作Factor时间收益。是否因果、是否可无影响固定，需另行批准的隔离模型对照与物理QC；本任务不执行这些修改或求解。
