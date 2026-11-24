# Base2060 与 Case3 2030 本地验收包

任务：作者于2026-10-20要求验收两套已解结果并取回本地。Git起点 `f04bf22`；复用既有 `collect_evidence.py`、`cispo_model/relative_acceptance.py` 与 `scripts/assess_relative_v1.py`，没有修改模型或验收判据。源结果、严格标签、候选状态及运行中的其他作业均保持不变。

截图所述2060“没有备份/仍在求解”是旧状态。本次以实际云端/T550文件与交接记录为准，历史条目保留，当前快照追加更正。没有修改其他会话中的SI模块或稿件。

## 离线评估结果

两套均通过现行 `relative_v1_author_20261014_extended`。这是作者定义的质量参考验收；不将其改写为原严格检查PASS，也不自动改变科学采纳标记。Case3筛选状态已由作者于10月19日明确采纳，该决定与本次技术验收分开记录。

| 检查 | Base2060 | Case3 2030 | 判据 |
|---|---:|---:|---|
| relative_v1 | PASS | PASS | 全年8760h |
| 最大功率平衡残差 GW | 3.683015590e-6 | 2.703891084e-7 | 各省 max(1e-3 GW, 1e-6×年峰荷) |
| 成本分项相对闭合残差 | 1.988788200e-11 | 3.087821615e-12 | ≤1e-7 |
| 双向流额外损耗/系统负荷 | 1.199859818e-5 | 3.574347760e-6 | ≤1e-4；结果报告净流 |
| Barrier primal infeasibility（合同口径） | 0.0080533881 | 0.0026068103 | ≤1e-2 |
| 相对原始/对偶目标差 | 0.0008169667 | 0.0003179627 | ≤1e-2 |
| 扩展GW/GWh物理检查失败项 | 无 | 无 | max(严格容差, 1e-3 GW或GWh) |
| 其余保留严格检查失败项 | 无 | 无 | 原判据 |
| 原严格QC标签 | HARD_FAIL（保留） | HARD_FAIL（保留） | 不覆盖 |

合同口径的Barrier残差与Gurobi打印日志并非同一组数字，不混用。两者均使用Barrier、48线程、Crossover=0、BarConvTol=1e-4、NumericFocus=2；Base2060 Aggregate=1，Case3 Aggregate=0。工程对偶等级为 `BARRIER_DUAL_ENGINEERING_GRADE`。

水库按 `DEFERRED_BY_AUTHOR_20261012` 暂缓逐站判定：Base2060最大713.857706641m³，HydroCHN_00136、第2881小时、活动库容1,043,104,323m³；Case3最大0.282365064m³，HydroCHN_00473、第4444小时、活动库容18,435,387.49m³。T550从原`reservoir_dispatch.npz`重算，数值与原QC最大值核对一致，披露完整。

Case3定价证书与本次下载的原MPS/BarPi及两manifest身份一致：B=347.782067869 million CNY，B/obj=8.304198763e-5，ACCEPT/INTERVAL_WITH_B，无需因当前证书启动重解。包内保留Claude原证书、列清单、脚本和日志；此次不重复计算证书。

## 本地内容与溯源

- `evidence/base2060/`：30个原始小文件，共13,579,632 bytes；29项与原结果manifest一致，manifest自身另核源端SHA。
- `evidence/case3_2030/`：31个原始小文件，共13,156,856 bytes；30项与原结果manifest一致，manifest自身另核源端SHA。
- `assessments/<case>/`：T550计算的输入、完整扩展评估、证据清单、正式技术验收记录及最终备份manifest。全部按原字节回传核SHA，不用文本换行归一化冒充字节一致。
- `packages/<case>/` 和同目录ZIP：含上述小证据、评估、启动/身份元数据与逐成员SHA。Case3另含定价证书。
- MPS、BarX/BarPi和完整逐时调度不下载到本机包内；通过原manifest和T550备份manifest引用其bytes/SHA，完整原件保存在云端与T550。

`assessment_byte_verification.json`记录评估回传SHA；`backup_completion_verification.json`记录备份六层及两最终manifest；`acceptance_sync_verification.json`记录正式JSON回写T550旁置目录后的字节SHA；`package_summary.json`记录ZIP大小/SHA与解压后逐成员验证。以这些最终文件存在并通过核验为交付完成依据，不把尚在传输的原模型记为完整备份。

## 执行与验证

在项目根运行：

```powershell
python supplementary_materials/reviews/completed_acceptance_20261020/collect_evidence.py
python supplementary_materials/reviews/completed_acceptance_20261020/assess_on_t550.py
python supplementary_materials/reviews/completed_acceptance_20261020/finalize_acceptance.py
```

最终打包要求T550完整备份已COMPLETE，既有最终包目录会拒绝覆盖。完成后应读既有证据，不能盲目重复运行；需要新评估时建立新目录。

验收模块14项既有回归通过；新编排脚本语法检查通过，并通过实际两套源文件采集、T550离线评估、源SHA前后核对、两端原字节校验和ZIP逐成员校验。不求解新LP，不执行Stage B，不修改源状态。


## 本轮最终交付

两套验收PASS，T550备份六层全部VERIFIED、184文件/10,828,735,197bytes已COMPLETE；源身份复核不变。正式验收JSON已旁置回写T550且两端原字节SHA一致。

| 本地ZIP | 大小bytes | 成员数（含manifest） | SHA256 |
|---|---:|---:|---|
| base2060_acceptance_20261020.zip | 4279063 | 49 | 528b070f58ec09a00216f2bac9a91a1adced2bda73ddfe1a29eb8e5a8cdbbbc6 |
| case3_2030_acceptance_20261020.zip | 7449859 | 58 | 8e60df39a08c1b7b5747b7489ca91759d4ec364a984abe0d17894f5f259ab4ec |

两个ZIP均通过CRC和逐成员bytes/SHA核验；完整解和大数组仍在云端/T550。本机验收包已可直接供复核，无待取回文件。
