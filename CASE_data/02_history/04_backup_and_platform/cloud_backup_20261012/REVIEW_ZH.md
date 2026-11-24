# T550 直连云端与 Base 三年结果备份

2026-10-12（英国日期）。起点 Git `ababe5d`。用户明确要求“已添加，测试 T550 能否直连云超算，确认后开始备份，2060 的清理和提交先不要继续”。

## 当前状态

T550 的专用公钥登记后已成功直连，远端返回 `ln301.para.bscc`。英国 16:24:11（UTC 15:24:11）启动单次串行备份，PID `4080225`；当前仍在传输/核验，**尚不宣称完成**。程序在 T550 运行，不依赖本机持续转发，没有周期监听或自动提交服务。2060 清理、派生状态、构建与提交均暂停，科学验收记录尚未签发。

## 范围与空间

源根：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/`。

目标根：`/home/zz2/National_model_server/cloud_backup/`。每个 release 保持原相对路径。

|release|文件数|T1 bytes|T2 bytes|T3 bytes|
|---|---:|---:|---:|---:|
|20260914_base_v9_t48_m750_tol1e4_v3|87|527926242|739001933|4048048342|
|20260919_base2040_v9_t44_m750_tol1e4_v1|87|529820602|739002082|4051693374|
|20260930_base2050_v9_t48_m750_tol1e4_v1|88|531781303|739002095|4051434705|

共 262 文件、15,957,710,678 bytes。T1 包含全部报告、CSV、日志、候选状态、价格与对偶及配套调度数组；T2 是 `barrier_checkpoint/`；T3 是 `model_archive/original.mps.gz`。额外包含明确列出的 release 根目录启动脚本、身份/提交记录与 Slurm 日志。不复制外部输入数据集、repo、环境或凭据，不把结果备份称为完整运行环境镜像。

启动前目标文件系统总量 4,029,616,283,648 bytes，可用 1,481,082,150,912 bytes，完整备份后估算可用比例 36.3589%，超过任务书的 30% 门槛，故三年 T3 全部纳入。每个传输阶段重新检查空间。

## 传输与核验合同

- T550 上使用独立配置 `/home/zz2/.ssh/paracloud_backup_20261012/ssh_config`，别名 `paracloud-backup`。严格主机验证、仅专用公钥认证、不转发 agent；私钥始终留在 T550，未读取或复制内容。
- `backup_on_t550.py plan` 只读盘点源输出，确认原 solve=OPTIMAL、preservation=COMPLETE；已有结果 manifest 成员直接使用原 bytes/SHA，未列出的少量日志/元数据在源端补算 SHA。未在云端加载模型、求解或扫描 MPS 内容。
- `run` 先三年 T1，再三年 T2，最后三年 T3；单进程、flock 防重复、每次只运行一个 rsync。新建目标，拒绝既有 release，未使用删除选项；中断残片保留在目标以便续传。
- 每层传完在 T550 对每个文件实际计算 SHA256，核对长度。最后重新读取云端清单/大小/mtime，确认源未变，再在三个目标 release 根各写 `backup_manifest.json`。
- 验证合格只表示备份完整，不修改原 QC、候选状态及科学验收标记。尚未签发的 relative_v1 验收记录不会凭空附入备份。

## 工具与证据

- 本地 `backup_on_t550.py` 已部署为 `/home/zz2/National_model_server/backup_tools/backup_on_t550_20261012.py`。
- 固定机操作目录：`/home/zz2/National_model_server/cloud_backup/_operations/20261012_base2030_2040_2050/`，含 `backup_plan.json`、`transfer_launch.json`、`transfer_status.json`、`runner.log` 及各层 rsync 日志/文件列表。
- 只读一次性查询：`python supplementary_materials/reviews/cloud_backup_20261012/collect_status.py`，保存本地时间戳快照与 `latest_status.json`，无自动轮询。
- 本机转发中途短暂握手超时，用户重连后先核实没有启动记录/进程，再启动单次备份，未重复启动。云端直连认证本身已通过。

下一步：完成三层传输、目标逐文件 SHA 与源不变核验，收集三个 `backup_manifest.json` 后追加完成记录。原文件不删、不移动；2060 继续暂停。


## 2026-10-12 连接恢复后的完成核验

T550原自主备份完成：262文件、15,957,710,678bytes，三年T1/T2/T3共9层SHA VERIFIED；三个backup_manifest均COMPLETE且与计划path/bytes/SHA逐项一致，见cloud_backup_20261012/backup_completion_verification.json。没有重复启动传输。三年正式验收JSON已同步到各release旁acceptance_relative_v1_20261012/，远端SHA与本地相同，acceptance_sync_status.json=VERIFIED，原归档未改。上海收口后2060在广东PHS极小余量处按D2停止，尚无新release/held作业。


补充：备份262原文件的SHA核验结论不变；旁置验收JSON的跨Windows/Linux换行字节差异已单独纠正，新增source_bytes精确副本，原canonical与output_8760均未改，见base_acceptance_relative_v1_20261012/acceptance_byte_sync_verification.json。
