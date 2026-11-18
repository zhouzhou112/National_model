# 32线程测试已获放行，等待新节点许可配置（2026-11-18 18:46UTC）

**尚未启动测试。** 作者明确要求“可以测试一下了，当前云端只剩下一个在运行的项目”。这已撤销之前只预设环境的暂停条件，本次授权限定原OPS-Open2050归档MPS的32线程排序及前5轮。

- 云端squeue只读确认：5587177 / late_open_2050_t44 / RUNNING。未操作作业或冻结包。
- 新节点：44 vCPU、约800GiB总内存、785.056GiB可用；没有Python/Gurobi进程。
- 缺项：GRB_LICENSE_FILE的进程/用户/系统三个作用域均为空；C:/Users/zz2/gurobi.lic和C:/gurobi/gurobi.lic均不存在。只检查路径与存在性，不读取凭据。
- 授权文件已更新为AUTHORIZED，allowed_modes仅run；此前PREPARE_ONLY文件在新节点setup中另存before_test_release副本，历史准备记录保留。
- 修改benchmark_mps.py：许可检查与大MPS复用同一个Env，不分别申请两个会话；没有许可文件时在导入gurobipy前拒绝执行；Env启动失败时释放资源；资源采样线程先退出再dispose模型，避免清理时竞态。
- 验证：AST、缺许可阻断且无gurobipy导入、run中单次Env创建及共享smoke检查通过；源LP/参数/线程数/停止轮数不变。没有运行Gurobi小模型或大模型，未新增许可会话。
- 代码部署SHA：a109e69b115fb37fadc61db1819b815512335e990f8238b1c415c10b49e8ffaa；与本机一致。证据pretest_check_20261118.json、single_session_validation_20261118.json、test_release_pending_license_20261118.json。
- Git基准ff4ed8cb6773a3ea57c3d4326345ea0f0abc2dfe；仅提交本次脚本、授权和小证据，既有其他未提交内容保留。

下一步：作者将现有WLS客户端许可配置在新节点C:/Users/zz2/gurobi.lic，或告知已配置路径；不在聊天发送许可内容。配置到位后，先检查现有进程/名额，再按本次授权启动单环境有界测试。无需作者重新放行；不建后台文件监听，不自动重复启动。
