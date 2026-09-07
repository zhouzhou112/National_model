# 历史长时段水库残差只读复核（2026-09-07）

## 结论与边界

已连接固定服务器 `national-model-server` 与云端 `paracloud-bscc-a8`，读取历史报告，
对代表性保存水库数组重算水量平衡。全程无优化、presolve、模型松弛、新作业或运行 Base 干预。
生产模型、输入数据、物理边界与求解参数均未修改。

长时段历史结果中既有水量平衡未通过的工程候选，也有通过的严格结果。
旧云端 8760h 结果中 620 座水库的全部 5,431,200 条小时平衡，重算最大残差
0.0389985391 m³，全部通过现行 1 m³ 水量 QC；它的整体结果仍未通过其他检查。
因此不能把新三情景 24h 测试的失败直接推广为全年 Base 水库模型失效或来水数据错误。

## 对照结果

| 保存结果 | 求解设置/状态 | 最大水量残差 m³ | 水量 QC | 整体 QC |
|---|---|---:|---|---|
| 本地 24h case3 nonbasic | SUBOPTIMAL，Crossover=0 | 42651.779305 | 未通过 | HARD_FAIL |
| 固定服务器 744h strict reference | OPTIMAL，BarConvTol=1e-8，Crossover=2 | 0.0026784 | 通过 | PASS |
| 固定服务器 744h cf1e6 Stage A | OPTIMAL，BarConvTol=0.01，Crossover=0 | 4877.898095 | 未通过 | HARD_FAIL |
| 固定服务器 2160h case1 Stage A | OPTIMAL，BarConvTol=0.01，Crossover=0 | 14834.593126 | 未通过 | HARD_FAIL |
| 云端历史 8760h，job4139552恢复结果 | OPTIMAL，BarConvTol=1e-8，Crossover=0 | 0.038998539 | 通过 | FAIL（其他项目） |

744h 宽松案例只复核保存报告；表中其余四组均独立读取全部水库物理数组重算，
具体 SHA256、逐站最大残差与超限小时见 `evidence/` 和 `comparison.csv`。
固定服务器数据下载后 SHA256 与远端相同。云端 233 MB 压缩水库数组通过远端只读 NumPy
复核，返回小型报告；没有在云端写文件或调用 Gurobi。
此前尝试的慢速本地下载已停止，部分文件保留在 output 下并标为 INCOMPLETE_DO_NOT_LOAD，
它未用于任何数值结论；停止对象仅为本次检查的本地 SSH 下载进程。

## 24h 的局限及因果解释

当前水库状态使用截断窗口首尾相连的周期约束。24h 情况相当于要求这个测试日的结束
有效库存回到起点，不能表达跨日、跨季调节；遇到短窗口来水很少、有效库容很大的站点，
也可能出现不利的数值尺度。这是从当前方程与输入观察得到的解释，尚未通过同版本单因素
求解试验分离其因果贡献。

必须区分短期窗口的代表性与求解向量的合格性：24h 作为工程 smoke test 可以不代表全年
经济调度，但若保存向量明显违反其自身水量平衡，就仍是未通过验收的向量。不能把误差当作
真实调度，也不能据此自动删除水库或放宽守恒约束。744h/2160h 宽松 Stage A 同样出现残差，
说明时长不是唯一因素。

较好的历史 744h/8760h 与宽松 Stage A 的 BarConvTol、NumericFocus 等存在差异，
同时模型版本、窗口也不完全相同。这组历史观察支持“收敛质量需要单独核查”，不能证明
只改一个参数或只延长时段就一定解决。旧 8760h 在 Crossover=0 下水量通过，也说明
关闭 Crossover 不是水量不合格的充分条件。

历史严格 744h、宽松 744h、2160h 与云端 8760h 的站点表、逐小时来水、生态流量与显式
径流式水电输入记录 SHA256 一致；这些水文文件也与前轮本地 24h 输入核验记录一致。
这排除了这些特定输入文件被替换作为对照差异的解释，不证明水文来源、生态代理、梯级
协调等所有科学假设均无问题，也不保证不同版本生成的全部 LP 行相同。

## 更正此前容差说明

`cispo_model/solution_export.py` 的专门水量 QC 阈值是 **1 m³**。
此前说的 **10 m³** 来自通用原 LP 行容差 `1e-5` 在 million-m³ 行单位下的换算，
不能称为专门水量 QC 阈值。本轮未修改任一容差。

原 24h case3 保存数组：按 1 m³ 为 27 座水库、473 个站点小时超限；按 10 m³
为 24 座、415 个站点小时超限。此前的 24/415 计数适用于后一门槛，最大残差定位不变。
2160h 按 1 m³ 为 290 座、360183 个站点小时，按 10 m³ 为 177 座、3744 个站点小时。
严格 744h 与旧 8760h 在两种门槛下均零超限。

## 其他全年结果的区别

旧 8760h 的整体物理 QC 未通过 `unidirectional_interprovincial_flow` 与
`objective_components`；原 LP QC 另有两条超限行，最大约 2.28683e-5，最差行是
`load_center_ror_generation_closure_p43`。水库通过不等于整个结果可正式接受。

T44 job4496031 是作者受控中止后的未收敛保存向量，水量残差极大，不纳入已收敛解比较。
其他 INTERRUPTED / NOT_EVALUATED 或没有 QC 的历史目录不能被计为水量通过。
本轮早先只读作业快照中 T32 job4479238 为 RUNNING，elapsed 3-23:12:27，尚无终态 QC；
该记录是检查时的快照，不代表日后状态。未触碰其 STOP、参数、release 或作业生命周期。

## 可复现性与下一步

基线 Git：`0b077e8ec0a354f63e7c49a1e197ca4ef452a226`；本里程碑提交通过 Git 历史追溯。
新增两个通用只读脚本，不修改生产路径：

```text
python scripts/inspect_historical_water_qc.py --ssh-host national-model-server --root /data/zz2/National_model/outputs --root /home/zz2/National_model_server --output <new-json>
python scripts/inspect_historical_water_qc.py --ssh-host paracloud-bscc-a8 --root /publicfs01/fs1-a8/home/a8s001819/National_model_cloud --output <new-json>
python scripts/recompute_saved_reservoir_balance.py --source <existing-physical-export> --output-dir <new-audit-directory>
```

重算方程为 `S[t]-S[t-1]-3600*local[t]-3600*upstream[t]+3600*turbine[t]+3600*spill[t]`，
t=0 的前一项取窗口最后一小时；各流量 m³/s、库存 m³。仅适用于当前一小时周期水库导出。
云端本次精确只读重算命令保存在 `evidence/audit_cloud_readonly.py`；四组重算与原 QC 最大值
一致至浮点运算顺序误差，旧全年差值约 2.4e-9 m³。语法检查与 diff 检查通过。

清单包括固定服务器 112 个、云端 8 个 >=168h 或未记录时长的报告目录；含重试、恢复与备份，
不是 120 次独立实验。报告扫描读取深度上限 6，未声称覆盖未保存或扫描范围外的所有历史案例。

下一步继续离线审查新情景与已通过 Base 的矩阵尺度、周期处理及结果验收合同，保留精确 Base
一致性要求。新柔性情景的全国全年资格仍未完成，现有正式启动门禁保留；作者解除禁令前
不自行求解。未来若获准做匹配测试，应比较同输入、同版本的较长窗口与非 basic 收敛质量，
而不是仅以 24h 的失败决定全年方案。
