# Stage A 完整保全与离线恢复

2026-08-28 13:45终态更新：**历史8760h已在云端成功恢复**。job4396245于03:18:35 rc0完成，
总耗时1:04:39，完整恢复峰62.061GiB；LP fingerprint/完整顺序与历史精确一致，实际没有用到指纹豁免。
容量、运行、成本、碳、对偶、QC、结果清单、86900行candidate state和原模型/名称归档均完整保存。
86文件共约5.45GiB，QC56/58且raw LP2行超阈值，科学接受仍false。完整数据目前在云端，
本地只保留终态报告；下方“仍在重建”为历史记录，当前状态见MODEL_SERVER_STATUS。

2026-08-28 02:15更新：本地首次恢复因指纹差异失败；现按作者授权在**云端原环境**启动job4396245，
24CPU/128G，上限4h，新release为`20260828_8760_stagea_recovery_v1`。当前仍在重建，未完成导出。
历史入口新增`--allow-fingerprint-mismatch`：指纹差异只记录，不直接终止；维度/nnz、完整名称/sense
顺序和向量hash/finite仍检查。先归档重建模型再检查，并复用归档摘要；raw LP审计异常不阻断其他
可导出数据，明确标PARTIAL。该选项不改变默认严格接口、Stage B门禁或科学接受规则。

以下2026-08-27说明保留作历史记录，当前运行状态以`MODEL_SERVER_STATUS.md`为准。

2026-08-27 本地实现。23:47已在固定服务器独立历史release启动8760h离线恢复；这不是把当前完整
runner部署到生产checkout，也不能改变旧进程行为。当前恢复状态与路径见`MODEL_SERVER_STATUS.md`。

历史恢复使用新增`scripts/recover_historical_stage_a.py`和`run_historical_stage_a_recovery.sh`：
原release代码+仅保全补丁、显式路径映射、输入全校验、强制禁止optimize/presolve。当前原模型仍在
重建，不能宣称全年结果已恢复。历史版本1h对照、77条输入和实际CF全文件payload核验已经通过。

## 保存、评价、采用是三个独立步骤

所有 `Method=2/Crossover=0/SolutionTarget=1` 的 Stage A 都进入完整保全路径，不以 solver contract
或 physical QC 的 PASS 作为文件导出条件。旧 `--engineering-barrier-checkpoint-only` 名称保留以兼容
启动器，但现在不再表示“只保存两个向量”。不修改数据、目标、约束、单位或任何科学验收阈值。

- 先写原始 checkpoint/snapshot，再做语义导出与检查。可读取的 `BarX/X/BarPi/Pi/RC/Slack` 及
  `VBasis/CBasis` 都尝试保存；不存在的属性明确记为 unavailable，不能伪造 basis。
- 容量、逐时运行、成本、碳/CCS、对偶、QC、结果清单和候选跨年状态均保存。某个模块异常后继续
  其他模块，最终标记 PARTIAL 并保留错误及已有文件；QC FAIL 本身不使导出 PARTIAL。
- `result_manifest.json` 校验文件完整性，不认证科学可用性。它分别记录 export_status、qc_status、
  scientifically_accepted=false、author_decision=PENDING。`result_use` 仍描述年度/截断时域，不能
  单独据此判定科学接受。旧 accepted-only planning sequence 不会自动消费 candidate state。
- 没有可读解、非有限向量、磁盘错误或强制杀进程时，只能尽力保存部分内容，不能保证完整产物。
  每轮“求解任务”保全不等于每个 Barrier iteration 都有可恢复的内部 checkpoint。

## 默认与可选产物

```text
output_root/
  model_archive/
    original.mps.gz                 # 无压缩工具时回退 original.mps
    parameters.prm
    variable_names.jsonl.gz         # 完整原始 index/name
    constraint_names.jsonl.gz       # 完整原始 index/name/sense
    archive_manifest.json
    presolved_diagnostic.mps.gz     # 仅显式 --archive-presolved-model
  barrier_checkpoint/              # 兼容原 Stage B 门禁；具备资格时生成
  solution_snapshot/               # 可读取的原始数值、属性来源、哈希和 LP 顺序
  planning_state_candidate/        # 全部容量 cohort；零值/微小值/负值不筛除
    raw_new_cohorts.csv.gz
    capacity_cohorts.csv.gz
    state_transition_summary.csv
    state_metadata.json
  raw_lp_qc.json
  raw_lp_violations.csv.gz          # 超阈值原始约束/边界及 index/name/实测值
  solution_qc.json
  preservation_report.json         # 独立导出阶段及错误，不覆写原始 QC 为 PASS
  preservation_runtime_memory.json
  output_catalog.csv
  output_data_dictionary.csv
  result_manifest.json
  ...容量/运行/成本/碳/对偶结果表及数组
```

原模型在 optimize 之前归档，之后独立记录保全峰值内存。输入文件仍由版本化数据根和 SHA256 清单
管理，不为每轮求解重复复制所有气象原始数据；原数据版本必须继续可访问。此前 8760 h 的源码/向量
备份不等于原始数据已经全部备份。

## 怎样续接

同年 Stage B：继续使用既有 `--primal-dual-checkpoint-in`、`--allow-primal-dual-crossover` 和
`--allow-engineering-barrier-checkpoint`，通过 exact-LP/input/order 门禁后才能设置 PStart/DStart。
保存成功不意味着任何 incomplete/非有限向量都有求解续接资格。Stage B 不自动执行。

跨年：用 `--state-in <source>/planning_state_candidate --allow-candidate-state-in` 显式选择候选。
读入仍严格检查文件哈希、年份、资产标识、数值结构与单位；只是不再因源 QC FAIL 而拒绝作者选择。
来源 QC、source solver contract 和前序状态沿链保留；新结果继续走候选保全路径，不自动变成科学接受。
截断状态另需 `--allow-diagnostic-state-in`，且只能进入截断测试，不能冒充年度 anchor。

候选 state 保留既有建造/退役、GW/GWh/MtCO2_per_year 等定义，不裁剪微小负值。作者若以后决定
清理数值，必须另建派生状态、记录变换和重新检查，不能直接改原始 cohort 或 QC 文件。

## 离线恢复，不做 presolve

`scripts/run_cispo_2030_full_year.py` 新增 `--recover-stage-a-from <source_output>`，支持新
`solution_snapshot` 和历史 `barrier_checkpoint`。必须提供独立 `--output-dir`，以及与源一致的
config、scenario、solver、formulation、规划年、小时窗口和前序 state。输入与版本先核验，再重建
原 LP 并核对规模、Fingerprint、完整顺序及数值文件哈希；不调用 optimize、presolve 或 start 注入。

```bash
# 示例仅为 1h 截断测试；在匹配的 Gurobi 13.0.2 环境运行，目标目录必须不存在。
python scripts/run_cispo_2030_full_year.py --diagnostic-hours 1 \
  --solver-config config/solver_profiles/barrier_16_nonbasic_primal_dual_v1.json \
  --output-dir outputs/my_stage_a_1h

python scripts/run_cispo_2030_full_year.py --diagnostic-hours 1 \
  --solver-config config/solver_profiles/barrier_16_nonbasic_primal_dual_v1.json \
  --recover-stage-a-from outputs/my_stage_a_1h \
  --output-dir outputs/my_recovered_1h
```

只有已审查的实现变更才使用 `--allow-compatible-primal-dual-implementation`；它不豁免任何模型、
数据或顺序检查。跨机器路径迁移没有隐式放宽，必须另行核对并实现经审计的路径映射。

恢复以保存的 x 计算原线性表达式，以保存的 y 对应原约束；不重新寻找最优解、不提高原解精度。
原始残差审计使用一份 CSR 矩阵加分块残差缓存，历史全年矩阵这份副本约 5.7–7.7 GiB；大于744h的
离线恢复最低可用内存门禁为90 GiB。历史构建峰值48.574 GiB/约39分钟不是总恢复耗时或内存保证。
正式8760h恢复仍需原release源码、原数据和单独资源复核；本次没有执行。

## 原模型和 presolved 模型的区别

原始 MPS 可以重新读入，配合顺序校验和解向量复用；完整语义结果仍需要对应的数据和导出逻辑。
`--archive-presolved-model` 会额外调用一次 `Model.presolve()` 并保存诊断副本，增加内存、时间和IO，
因此不默认开启。该副本可能与 optimize 内部的 presolved model 不同，也没有可移植的 uncrush 映射、
Barrier/KKT 因子分解或内部迭代状态，不能保证直接接回原变量或从某次 Barrier iteration 原地继续。

官方依据：[Model.presolve](https://docs.gurobi.com/projects/optimizer/en/current/reference/python/model.html#Model.presolve)、
[How does presolve work](https://support.gurobi.com/hc/en-us/articles/360024738352-How-does-presolve-work)。

溯源：2026-08-16 13:13 作者问“pre solve 模型保存是否可行”；13:14 的答复明确是未来版本可加的方案，
并说明不能从另一进程导出正在运行任务的内部模型。历史 runner 只有显式 `--write-mps`，job4139552
的启动脚本没有传入，且不存在 presolved 模型导出调用；不是已成功写出的模型丢失。本轮才把原模型
归档接入默认流程，并给 presolved 诊断副本增加显式开关。

## 验证

```bash
python -m unittest discover -s tests -p test_solution_preservation.py -v
python scripts/validate_stage_a_recovery.py --hours 1 --output-dir outputs/my_recovery_validation
```

验证程序先做一个有120秒上限的1h诊断Barrier求解，再重建未求解模型；恢复期间将 optimize 和 presolve
替换为立即报错，防止误入求解。比较直接在线导出与离线导出的容量/运行/成本/对偶/碳及候选state，
并验证QC失败、缺少dual、非法映射、原模型MPS读回和显式候选状态采用。
