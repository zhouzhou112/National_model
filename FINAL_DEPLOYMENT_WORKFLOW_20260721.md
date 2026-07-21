# CISPO 最终部署工作流（2026-07-21）

## 1. 三层计算环境

| 层级 | 当前角色 | 允许任务 | 禁止事项 |
|---|---|---|---|
| 本地工作站 | 开发、参数审计、单元测试、1–24h smoke | 代码修改、数据表生成、1h/24h 单年或顺序链 | 不承担 8760h 科学求解 |
| 固定服务器 | 部署前门控、24h/168h 四年顺序链、必要时 744h | Linux/Gurobi 13.0.2 回归、数据/状态/输出闭合验证 | 可用内存不足时不得启动 8760h；不得占用其他用户进程 |
| BSCC-A8 云节点 | 最终 8760h 生产与后续 LP/QP 前沿 | 先单年 8760h，再顺序四年；互补 LP/QP | 登录节点不得计算；未过 24h/168h 门控不得提交付费全量任务 |

当前云端 WLS 与代理已打通，但每个 Slurm 脚本必须显式设置：

```bash
export http_proxy=http://172.16.110.3:8888
export https_proxy=http://172.16.110.3:8888
export ftp_proxy=http://172.16.110.3:8888
```

在修复云端 `.bashrc` 的非标准空白前，不依赖交互 shell 自动继承代理。

## 2. 唯一生产入口与顺序边界

- 单年：`scripts/run_cispo_2030_full_year.py`
- 四年：`scripts/run_cispo_planning_sequence.py`
- 生产时序：2030 → 2040 → 2050 → 2060
- 生产 horizon：`full_year=8760h`
- `--diagnostic-hours` 仅用于工程门控，年成本和政策约束不按截断小时缩放。

四年联合一次求解会显著增加变量、内存和跨期耦合复杂度。当前逐年求解更适合现阶段，但它是 myopic sequential planning，不是 2025–2060 跨期 NPV 最优；论文中必须按此表述。

## 3. 状态安全规则

`capacity_cohorts_v2` 强制验证：

- `capacity_cohorts.csv.gz`
- `state_transition_summary.csv`
- `solution_qc.json`
- `solve_report.json`
- 源 `result_manifest.json`
- 源 solve 的 `planning_year` 与 `result_use`
- predecessor 的实际路径与输入 SHA256

诊断 state 标记为 `TEST_ONLY_TRUNCATED_HORIZON`，只有同时使用 `--allow-diagnostic-state-in` 和测试 horizon 才能加载；生产 8760h 会硬拒绝。

顺序 driver 的运行目录必须为空。`--resume` 只接受 manifest、state、run ID 与 predecessor 指纹全部匹配的链；失败目录不得原地覆盖，应换新的版本化 `output-root`。

## 4. 参数权威链

运行时权威参数是：

```text
config/optimization_2030.json
    +
$CISPO_DATA_ROOT/technology/*.csv
    +
其他模块化 model-ready tables
```

`config/technology_parameters.json` 和若干 source/build tables 不是运行时权威源。每次生产数据部署后必须执行：

```bash
$PYTHON scripts/audit_model_parameters.py \
  --data-root "$CISPO_DATA_ROOT" \
  --output-dir outputs/parameter_audit_<version>
```

并要求：

- `parameter_audit_summary.json.qc_hard_fail == 0`
- `bio/bioccs` 燃料成本均为正且覆盖 31 省 × 5 数据年 × 2 技术
- CapEx、RUC、OM、storage、fuel、emissions、DAC、CCS 的键唯一与公式闭合通过
- 未决科学口径进入 `parameter_risk_register.csv`，不得用默认值静默覆盖

## 5. 门控顺序与停止规则

### Gate A：本地静态与单元测试

```powershell
& 'C:\Users\ZZ\.conda\envs\RL\python.exe' -m unittest discover -s tests -v
```

要求全部 PASS。

### Gate B：本地 1h 四年真实链

```powershell
& 'C:\Users\ZZ\.conda\envs\RL\python.exe' `
  scripts\run_cispo_planning_sequence.py `
  --diagnostic-hours 1 `
  --output-root outputs\planning_sequence_1h_<version>
```

要求四年均 `OPTIMAL + solution_qc=PASS`，`sequence_report.json.status=PASS`。

### Gate C：固定服务器 24h 四年链

```bash
$PYTHON scripts/run_cispo_planning_sequence.py \
  --diagnostic-hours 24 \
  --output-root /data/zz2/National_model/outputs/planning_sequence_24h_<version>
```

### Gate D：固定服务器 168h 四年链

同上改为 `--diagnostic-hours 168`。任一年失败即停止，不继续后年。

### Gate E：云端单年 8760h

先只跑 2030。检查实际构建内存、Barrier factor 内存、运行时、输出 manifest 和全量导出大小，再决定是否启动 2040–2060。

### Gate F：云端四年生产链

为每个科学情景建立独立 `output-root` 和独立 state 链；严禁跨情景复用 predecessor。

## 6. 每个昂贵 Case 必须保存的输出

当前输出契约已覆盖：

- 输入/config/environment/Git/SHA256 provenance；
- 省—技术与全国容量、发电、成本、碳、资源约束；
- 小时级省平衡、安全、价格及各技术 dispatch arrays；
- 省际与省内网络容量、流量、拥塞和 load-center closure；
- 水库站点索引、出力、库容、弃水、流量和 cascade metadata；
- storage SOC/charge/discharge/reserve；
- planning state 与跨年 summary；
- file catalog、field dictionary、result manifest。

完整运行代价高，因此后续新增 wave、flexible load、H2、compute 时，模块必须同步补充：

1. 容量/逐时运行原始数组；
2. 年度和省级汇总；
3. 成本分解；
4. 约束 slack/dual 或不可用原因；
5. QC 与数据字典；
6. 可直接用于论文绘图的 tidy CSV。

## 7. 当前仍未关闭的生产阻断项

1. BECCS 需要拆分 gross biogenic CO2、capture、stored CO2、lifecycle emissions 与 net removal。
2. 成本松弛前需要把总 objective 拆成固定外生、legacy、新建与运行成本。
3. 核电寿命 40/60 年、容量裕度 5/15%、惯量 3.0/3.5 s 需要形成明确情景，而非静默换值。
4. 未来 CapEx 与长期煤/气/生物质价格需要 low/base/high 和币值基年。
5. 现有 VRE 退役年龄、正式多年 hydrology/P30、PHS 水力配对仍是结构性限制。

上述问题不都阻止经济性基线的首轮 8760h，但必须在论文主结果冻结前分级关闭或做敏感性。
