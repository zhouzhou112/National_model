# T550 全量归档 → 标准核心 → 本地 CASE_data

此流程只做归档后的只读提取，不求解、不重新验收、不补造缺失数据。标准核心结构由 `core_schema_v1.json` 定义，正式情景名由 `case_results/paper_scenarios.json` 定义。

## 1. 先完成全量备份与验收

按既有规则核终态、旧传输和源身份，T550 完整备份的三层均 VERIFIED、`backup_manifest.json` 为 COMPLETE，验收/证书旁置。科学质量标签不影响原件完整保全。不得以本地小文件齐全代替完整备份。

## 2. 在 T550 从原件提取

把 `extract_core_from_backup.py`、`flat_core_engine.py`、`export_core_on_t550.py`、`core_schema_v1.json` 和情景映射安装到T550独立工具目录；`import_core_package.py` 与 `build_navigation.py` 在本地使用。创建明确的请求 JSON，逐案列出已经登记的身份与验收文件 SHA，不接受猜测的来源：

```json
{
  "cases": [{
    "legacy_case": "OPS-Conservative",
    "year": 2060,
    "release": "填写已登记的release",
    "kind": "COMPLETED_PRODUCTION",
    "acceptance_status": "PASS",
    "source_result_manifest_sha256": "填写已核验的result_manifest SHA256",
    "acceptance_record": "/home/zz2/National_model_server/cloud_backup/填写release/填写验收目录/acceptance_record.json",
    "acceptance_sha256": "填写已审查验收记录的SHA256"
  }]
}
```

命令（实际目录必须为新的版本目录）：

```bash
PY=/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python
$PY extract_core_from_backup.py --request request.json --out /home/zz2/National_model_server/core_staging_NEW_VERSION
$PY export_core_on_t550.py --library /home/zz2/National_model_server/core_staging_NEW_VERSION --out /home/zz2/National_model_server/paper_core_NEW_VERSION
```

第一步逐文件核对原件 SHA，用已有生产导出和 V5 服务池公式汇总。第二步验证来源后按八模块组织、提取独立碳核算对象、生成逐文件 manifest 并打包。已有统一平面核心库也可直接作为第二步的 `--library`；本轮采用该路径，不重复重算已有科学结果。

## 3. 只回传小包并安装

只取 `.tar.gz` 和 `.receipt.json`。本地执行：

```powershell
C:/Users/ZZ/.conda/envs/RL/python.exe CASE_data/workflow/import_core_package.py --archive 路径/paper_core_NEW_VERSION.tar.gz --receipt 路径/paper_core_NEW_VERSION.receipt.json
C:/Users/ZZ/.conda/envs/RL/python.exe CASE_data/workflow/build_navigation.py
```

导入器在落盘前验证整个包：只允许 JSON/CSV、无绝对路径或路径穿越、无符号链接、单文件≤1MiB、每案例≤3MiB；所有文件大小/SHA必须匹配。已有不同内容不得覆盖，须改用新版本。正式核心存入 `CASE_data/01_cases/<论文情景>/<year>/<release>/<模块>/`。

新批次只含部分案例时，导入器按 release 增量合并目录台账，保留旧案例；逐批原始 manifest/catalog 另存 `00_registry/deliveries/<包SHA前16位>/`。同一 release 的既有文件或元数据发生差异时停止，不能覆盖；不同内容必须使用新版本。

## 4. 固定模块与解释边界

完整案例：八模块、22份核心文件，CSV列名一致；旧 `case` 键仅用于映射，查看入口用 REF/OPS/LATE/PLAN/PLAN-NC。资源情景单列后缀。

1. 身份与验收：release、来源、质量标签、验收全文。
2. 系统与成本：年度规模、P/D、成本分项。
3. 容量与网络：分省技术装机、新建、储能容量、省际与城市网络、充裕度。
4. 运行：发电、风光弃电、储能充放电、连续火电启停等效量。
5. 柔性：31省×4服务的签约、容量信用、上下调、等效小时；REF明确不适用。
6. 价格：年度约束工程影子值。**不是完整逐时负荷价格，也不是结算价。** 逐时价格、典型周等扩展结果按单独小表清单在T550提取，留在该案扩展分析目录，不强行塞入核心。
7. 碳：化石未减排排放、捕集、DAC、净排放和年度上限。
8. 溯源：T550原件路径、大小/SHA、已有分析目录和提取校验。

失败与排序测试保留同样的模块状态索引，科学结果标不适用，不用空CSV或零值冒充完整案例。

## 5. 历史目录与整理规则

`02_history` 保留启动、门禁、数值实验、失败、备份与分析证据；`03_legacy_deliveries` 保留过去交付包。它们不作为日常文章数据首选入口。旧路径联接只是兼容复算，不能当作第二份备份；统计磁盘时不跟随联接。

后续求解数据和收尾脚本不得新写入 `supplementary_materials/reviews`。新增运行记录写 `CASE_data/02_history`；新增统一核心写 `CASE_data/01_cases`；论文/SI审查仍可留补充材料目录。

仅有文件老、失败、未晋级或重复 SHA 均不是删除条件。删除需要单独的文件级保留源、备份身份、引用与授权检查。
