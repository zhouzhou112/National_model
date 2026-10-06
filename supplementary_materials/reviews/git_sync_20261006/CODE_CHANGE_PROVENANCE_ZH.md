# 代码改动时间与运行版本追溯（2026-10-06）

结论：本地确有代码改动，但“10月6日提交72个工程文件”不等于“昨天新增了一代模型”。该提交补录了8月至10月积累的工作。9月V9修复已经进入当前云端2050冻结包；本地相对该运行包的主要新增是10月5日的隔离验证功能。不能把Git旧HEAD当成云端实际源码。

## 1. 怎么核对的

- 审计起点：本地HEAD `428a3f674664da10e96642f81b547a3aa2d52bee`；实时`git ls-remote github`确认GitHub main与工作分支同值。
- 对照对象：云端`20260930_base2050_v9_t48_m750_tol1e4_v1/repo`，即4844528对应冻结包。只通过SSH读取明确列出的源码；没有操作作业、部署文件或读取凭据。
- 既有清单覆盖`cispo_model/config/scripts/tests`内196个指定扩展名文件；本轮重新取回10个不同文件，SHA与上轮云端清单全部一致。对新取回的源码逐行审查，patch仅统一换行为LF，原始字节SHA另保留。
- 10月5日改动前的本地冻结副本，其8个相关模型模块与当前云2050对应模块逐字节相同。这直接连接了“云生产V9”与“本次A/C开发基线”。
- 本地351个受测工程文件仍全部匹配10月5日18:51:40 UTC启动的最终完整回归记录：412项、OK、1项Windows跳过。本轮没有修改模型或重复求解。

机器证据：[code_provenance.json](code_provenance.json)；逐行差异：[production_to_local.patch](production_to_local.patch)；复核脚本：[trace_deployed_code.py](trace_deployed_code.py)。原始源码取回副本仅保留本地`.codex_tmp/production_provenance_20261006/`。完整云清单见[cloud_versions.json](cloud_versions.json)。

## 2. 真正的时间线

| 有记录的时间 | 改动及用途 | 与当前云端关系 |
|---|---|---|
| 2026-08-25 | 基准数据中文分类归档、残余负荷提取脚本 | 历史辅助工具，未因本次提交自动运行 |
| 2026-08-27—28 | 历史Stage A恢复、结果备份/可视化、资源监测、GPU试验启动器及相应测试；另有早期Stage B工具 | 多数不包含在精简云release内，不代表新增物理模型；个别脚本首次编写分钟无法恢复 |
| 2026-09-13 | 水库输入修正表/读取接口、水量与梯级微量处理、周期库容和弃水界、VRE微小floor/headroom、2030 DAC关闭；随后V9按年开关使2040起恢复可选DAC | 已在云V9内。它们确实涉及模型/数据口径，不能说“没有科学含义”，但不是10月新增偏离 |
| 2026-09-14 | V9正式profile、实际参数回读、full-year runner的physical_v1与旧8192行缩放资格检查；08:51记录修复漏掉的构建后校验 | 已部署的历史运行修复；对应4614693新release，当前2050沿用 |
| 2026-09-19、09-30 | 2040/2050续接用solver profile与运行包 | 续年配置有显式差异；本地V9配置和2050 profile与运行包字节一致 |
| 2026-10-02 | config/README补充“运行Base使用V9”及后续情景资格说明 | 说明文档，不改模型 |
| 2026-10-05 | 0.2 factor-screen专用入口、A/B/C opt-in实现、构建审计、物理LP差异白名单和测试；目录审计默认合同及旧测试修正 | 本地相对云2050的主要新代码；仅factor入口进入独立F/S包，A/B/C在固定机独立数值包测试 |
| 2026-10-06 23:24:56英国时间 | 提交`865e966`：72文件、9323增/97删，汇总上述既有未提交工作 | 此时只做版本化，没有新改模型；北京时间为10月7日06:24:56 |
| 2026-10-06 23:26—23:27英国时间 | `95e8faf`、`428a3f6`：说明、证据与同步策略；推送GitHub | 没有更新云端或固定服务器工程目录 |

时间来源为`CODEX_HANDOFF.md`上述同名日期条目、对应review冻结包/manifest及Git提交记录。9月13日记录明确写有“0a03cc4+dirty、未提交”。因此不能靠`git blame`把所有改动归为10月6日；Git作者字段也是统一提交账户，不能据此判定每一行由Claude、Codex或人工何时编写。文件mtime亦未作为创作时间证据。缺少逐次原始提交的部分，只能定位到留档任务日/阶段，不能补造分钟级历史。

## 3. 当前相对云2050，具体差在哪

196个云包文件中，186个本地原始字节一致；另1个2040 profile仅CRLF/LF差异，JSON内容一致。真正有文本代码差异的是下表9个已有Python文件，统一换行后合计240增/41删。

| 文件 | 本地新增部分（10月5日） | 生产默认是否生效 |
|---|---|---|
| `cispo_model/master.py` | A：水电headroom、CCS改造微小UB清理、续接容量越界截断的调用及逐项审计 | 三个阈值缺省0；未启用清理/截断 |
| `cispo_model/planning_state.py` | A3：`clip_inherited_floor_overrun`；仅构建时截断，不改已归档cohort | 缺省0，直接返回原floor |
| `cispo_model/numerical_cleanup.py` | A1/A2两个新助手；原V9清理代码已在云端 | 缺省关闭 |
| `cispo_model/config.py` | A三个阈值和C分段配置的合法性校验、显式formulation入口 | 校验存在，但不主动打开新功能 |
| `cispo_model/run_contract.py` | 非零A阈值入科学指纹；关闭C按旧身份规范化 | 缺省/显式off的Base指纹保持原值 |
| `cispo_model/monolithic.py` | C：年度排放、捕集和生物质逐时求和的分块分支 | C缺省false，走原求和分支 |
| `cispo_model/load_center.py` | C：年度电量闭合/输送/注入/需求求和的分块调用 | C关闭时助手直接执行原整窗求和 |
| `cispo_model/physical_lp_diff.py` | 对审计明确列出的容量界收紧逐列核验；没有整族豁免 | 比较工具，不构造生产物理约束 |
| `scripts/run_cispo_2030_full_year.py` | 专用factor profile、`--vre-screen-csv`、五轮TEST_ONLY路径、MPS段SHA及A/C build_report审计 | 筛选需显式专用profile+CSV；普通生产入口不会自动筛选 |

此外，云生产包没有、本地新增的模型模块只有两个：`annual_dense_split.py`（41行，C助手）和`factor_screen.py`（110行，筛选合同/边界改写/五轮取证）。B没有新增求解器实现，因为原代码已支持`BarHomogeneous`；只新增独立profile。配套新增C formulation、factor/B solver profiles与测试。

本地比云精简包多155个同范围文件：模型2、配置4、脚本82、测试67。这里大量是早已存在但未打入云release的工具/测试，不能把155全部算作新功能或缺失部署。在72文件工程提交中，20个文件已与云2050字节相同、10个属于上述差异（含换行），42个未包含在云精简包内；逐文件名单在JSON中。

其他小改动也未隐藏：`audit_release_contract.py`把默认目录审计合同换成`release_contract_v1005_catalog_audit.json`，只更新既有情景目录，明确不授予V9科学资格；`test_flexible_portfolio.py`把过时的1e-9断言纠正为9月7日已选定的1e-4；`test_sensitivity_suite.py`增加子进程错误信息。它们不是这次新放宽生产容差或QC。

## 4. 生效范围与不能混同的版本

- **云2050生产包**：V9冻结源码，未包含上述A/C新代码及factor入口；本轮未更新。V9科学指纹仍为`937c3c6f4540dc2d217bd17eda44a4de0de76b41414e32d491d4283515b0d4f0`。
- **云F/S包**：V9加专用factor入口。其runner与本地仅差3行A/C审计写出；两个包是独立TEST_ONLY实验，不是原2050的替换版本。
- **固定机主repo**：仍clean/`ba8e09f`，较旧；它与固定机独立数值试验包不是同一个目录。
- **固定机数值包**：已包含A/C实现。同路径与本地只差B profile的`direct_nonbasic_scientific_acceptance` metadata，本地后改为false；不能称全包字节相同。
- **本地/GitHub**：代码一致，保留被否决的实验实现，但A/B/C没有晋级默认配置。A的1e-6GW组合、B的齐次模式、C的730h分段均在报告中否决，不因提交main而获得生产资格。

关闭新功能的既有真实24h回归中，旧V9与新代码的原MPS、`solution.npy`逐字节相同，均77轮、QC PASS；不是仅比较目标近似相等。证据`../numerical_robustness_20261005/disabled_regression.json`。这支持该窗口的关闭等价性，不能代替所有年份/8760的构建与求解证明。

**必须保留的追溯缺口**：10月5日17:19:45 UTC，在固定机A_off已加载代码后、C启用前，数值试验目录更换过`annual_dense_split.py`以修正常数逐块相加的浮点差。前版留在初始包，最终SHA为`0623b45eb962579e140b07239377ee2916293b43426003df09d42448662b66e4`；关闭分支未变，但A两侧不能声称整包源码逐字节相同，Boff也缺同期加载模块SHA。此事发生在隔离试验目录，未改云2050。详见数值报告5.2及5.5。后续必须改用新release处理修复，不再原地替换。

另一个实际复现风险是入口默认仍为`config/optimization_2030.json`。复现云V9必须显式指定V9配置、对应年份profile和继承状态/输入身份；“本地HEAD与GitHub相同”或直接使用无参数默认命令，不等于“与云2050运行模型相同”。本次未擅自改默认配置。

## 5. 收敛版本差异的执行约定

1. 现有2050包维持冻结，不为追上GitHub原地更新；本轮只新增审计脚本、证据和文档。
2. 新实验先以已提交、已测源码建立独立release，记录commit+逐文件SHA+配置/输入/继承状态；有修复就建新release，不覆盖已开始任务的目录。
3. V9作为当前生产比较基准，A/B/C保留显式关闭及否决记录，factor继续限定TEST_ONLY；不能把Git入库解释为改变默认科学模型。
4. 之后小批及时提交，区分模型、实验工具、文档，避免再积累一个多月的dirty后汇总。历史提交不重写、不伪造原始时间。

本报告及本轮文档提交不改变351个受测工程文件、不运行求解、不新增监听、不部署远端。后续复用的生产基线应以本清单和冻结包为准，而不是旧HEAD `0a03cc4`。
