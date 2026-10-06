# 2050 Base续接与48线程启动核验

2026-09-30（英国时间）。Git基准`0a03cc452e95d158f36923ceb5210267979b6234`+既有dirty，未提交。用户明确要求“接续2040的启动2050求解，设置48线程”；本次授权覆盖2050的候选续接和正式提交，不覆盖2060或Stage B，不改变上游科学接受状态。

## 已启动状态

- Job `4844528`，名称`cispo2050_base_v9_t48`，节点`m4cm1802`；英国15:09:28提交、15:09:36放行、15:09:37开始（北京时间22:09:37）。已确认RUNNING、Restarts0，实际AllocTRES=cpu64/mem750G/node1/billing64，UNLIMITED。
- 计算节点Gurobi13.0.2许可小测试PASS，初始可用内存约724.65GiB；续接合同PASS，7项入口回归PASS；实际参数回读为Threads48/Method2/NF2/ScaleFlag2/Presolve2/Aggregate1/BarConvTol1e-4/Crossover0/SolutionTarget1，TimeLimit/SoftMemLimit/MemLimit/WorkLimit均无限。Seed沿用默认0。
- 已进入全年输入读取/模型构建；run_scope确认2050/边界2040/8760小时，内存门禁PASS，stderr为0字节。尚无全年build_report或Barrier迭代，不能称为已经收敛或已经通过全国求解验收。

## 运行身份与边界

release：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260930_base2050_v9_t48_m750_tol1e4_v1`。

输出：上述release下`output_8760/`。实际续接输入：上述release下`upstream_2040_bound_closed/planning_state_candidate/`。

前序2040：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260919_base2040_v9_t44_m750_tol1e4_v1`，job4682935。其preservation COMPLETE，173800条容量cohort、OPTIMAL但QC HARD_FAIL，原始结果完全保留。本次先验证原release清单，再复制其repo；195个原文件SHA逐项一致，新增2050 profile和启动辅助工具，未将本地其他dirty改动混入生产。

科学配置沿用`config/optimization_numeric_dac_by_year_v9.json`，solver profile为`config/solver_profiles/barrier_checkpoint_full_year_cloud_2050_numeric_v1_threads48.json`。2050解析后科学指纹`74b062e41cb83cb4616ca1b6f651f1d7796a556d3f36b512ce2997d6e137086c`。相对2040数值配置唯一变化为Threads44→48；年度参数由现有for_planning_year解析，DAC可用、Base情景不启用灵活性负荷。数据overlay链接原release，未修改气象、适宜性、负荷、成本或政策数据源。

全国31省、337城市负荷中心，2050年8760小时连续LP。容量投资、逐小时电源/储能/水库/输电决策、年度成本最小化及既有平衡、备用、惯量、碳、资源、网络约束保持。功率GW、电量GWh、碳MtCO2，目标million CNY/year；2040→2050间隔10年，技术寿命与退役规则不变，年度成本和流量政策缩放均1。

run_scope中的`scientific_acceptance_mode=ENGINEERING_BARRIER_CHECKPOINT_ONLY`、`planning_state_policy=UPSTREAM_UNACCEPTED_CANDIDATE_CANNOT_BECOME_ACCEPTED_STATE`。其中通用`result_use=SCIENTIFIC_PRODUCTION`仅表示全年用途，不覆盖未接受标记。本次续接容量状态，不复用2040的Barrier内部因子、迭代状态或求解器basis。

## 继承容量边界修正

原2040候选加载、来源QC/solve/cohort/summary和result_manifest完整性核验通过，但2050实际VRE边界审计发现129站上界越界（19陆风、2集中式PV、108分布式PV），无负容量；最大7.294387591kW、合计308.694665578kW，每站均低于既有10kW清理阈值。

逐站检查发现2030的正小容量cohort仍在有效寿命内，但在2040构建时其继承floor已清为0，2040导出又保留这些历史cohort；2050叠加时可超过原技术上限。这是跨年清理和cohort记账不一致，不能全部称为浮点舍入。所有129站2040导出容量均在上界1e-9GW容差内；其中G000023798::dpv还包含极小浮点尾差。

按上次2040续接的独立工程副本做法，仅扣回这129站越界量；优先从最早仍有效的正cohort扣除，保留新建容量。实际改变130条capacity_delta：129条2030微小cohort，加上述站点一条2040记录的1.3877787807814457e-17GW尾差。合计减少308.694665581kW（0.308694666MW），最大站点减少7.294387591kW；173800条记录、所有其他字段和退役年份不变，未删除记录。

修改仅存在于`upstream_2040_bound_closed/`，不覆盖原2040状态、解、QC、技术上限或物理模型。副本仍`candidate_unaccepted=true/scientifically_accepted=false`，复制原HARD_FAIL和来源证据，重新建立cohort/summary/metadata/manifest SHA。调整后真实输入重审，VRE上/下界越界均0。

原cohort SHA：`565a36313b12032da3e2ec89b4b48d0c8cdec381e641d6d35a9a095e3fa1df15`；原metadata SHA：`cd3f09c479b72a115c493695017419c403fc9a032099573f4c4e462a046ba308`。每站/每cohort调整在`evidence/upstream_2040_bound_closed__bound_closure_audit.json`；原审计另存original_*。这是显式近似候选，不声称原2040精确解未变，也没有通用修复所有跨年记账问题。

## 验证证据

1. 原release SHA、195原repo文件与新repo逐字节检查PASS，Bash语法PASS；原2040完整候选来源加载通过。
2. 2050全输入preflight：67 PASS、3 WARN、2 INFO、0 HARD_FAIL；原有梯级低相关/最大滞后及长距离AC代理警告保留。
3. 衍生状态原字段/记录数保持、仅130个容量数值变化、来源原cohort哈希未变；派生manifest和来源验证PASS。VRE继承边界复审0越界。
4. 真实2050一小时构建：80104行、238529列、452584非零元，未调用optimize；年度行registry检查通过。
5. 真实全年runner使用两行Gurobi fixture验证候选状态、2050参数、原模型归档及科学接受门禁，PASS_BUILD_ARCHIVE_NO_OPTIMIZE；不冒充全年求解。
6. sbatch --test-only通过；先held提交核对64CPU/750G/billing64/UNLIMITED，再放行。计算节点许可、续接合同、实际48线程回读、7回归与正式入口scope均PASS。

启动回归中有既有numpy.ndarray size changed警告，但7测试通过，正式stderr为空；未改运行环境。后续若出现实际数组/二进制错误应另查，不以警告直接推断结果损坏。

## 文件、命令与下一步

本地新增2050 solver profile及本目录的launch_config.json、prepare_local.py、base_2050.sbatch、validate_2050.py、audit_state_bounds.py、prepare_bound_closed_state.py、deploy.py、证据与哈希。更新三份项目交接文档；无物理模型源码修改。

操作顺序：`prepare_local.py`；`deploy.py inspect`；`prepare`；首次`audit`（原候选）；诊断；`close-state`；`audit`（派生候选）；`preflight`；`validate`；`submit`；`release`；`collect`。每步输出保存在带时间的stdout/stderr日志。prepare/close-state/submit均有防覆盖/防重复保护，已启动后不要重复执行这些阶段。

后续只读入口：`python supplementary_materials/reviews/base_2050_continuation_20260930/deploy.py status`或`collect`。运行配置路径来自launch_config.json，环境复用既有release；没有重建求解工具链。

精确下一步：只读跟踪4844528的全年build_report、原MPS/PRM归档、gurobi.log参数/Presolve/Ordering/Barrier、资源与stderr。终态检查完整保全及原物理QC，不自动2060、Stage B、重启或放宽阈值。当前仍在构建，不给完成时间承诺。
