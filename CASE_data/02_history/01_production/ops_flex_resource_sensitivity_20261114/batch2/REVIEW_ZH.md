# 第二批OPS-Open 2030/2040/2060执行记录

> 最新：2040/2060已通过全部门禁并release；2030在24h碳预算门禁停止，等待作者决定。下方早期连接阻塞记录已由本次恢复覆盖。

作者已确认第一批经Claude复核并采纳，授权第二批其余三案逐年门禁通过后提交/release。44线程，64CPU/750G/UNLIMITED/no-requeue，启动可用内存≥700GiB；与LATE-Open2050/5587177合计最多4个。第三批仍需作者确认。LATE终态后按第一批MPS ROWS+自身BarPi完整行序校验恢复年度行对偶，已记入AGENTS与案例收尾要求。

已核对对应B2030 v3/B2040 v1/B2060 v2的真实启动命令、数据清单及冻结源。T550三个冻结源逐文件SHA与云端匹配。2040/2060闭合SHA分别5e927a864e974f7476611d27d2b6e7da969b3b213daaa467c32d0da577cc2b03、24a551f1d8f8b3e9693a41e6c5c0f7d82f2a758efb7f580074569b72df0981a0，直接复用；2030原B无独立闭合文件。2030使用V9，其余v9_a12。原B2030数据根有90个文件，后两年58个；其中4个历史元数据/水库审计原件与既有共享T550根不同，须从B2030原件按SHA复制到独立根，不重建任何作者输入。

新独立T550目录runtime_batch2_20261115。第一次复制4个文件因源为符号链接而被rsync跳过，原失败日志保留；改用--copy-links只复制这4个已列明数据文件后续作安装。随后SSH连接中断，恢复检查连续在banner握手阶段超时，已请求用户重连。安装可能已经完成，当前不能确认；不得直接重跑prepare脚本。恢复先读installation_receipt.json、核旧进程和已存在目录；若缺失则按现有完成阶段补齐，不覆盖旧验证记录。

门禁准备：resource_gate_batch2.py/resource_audit_batch2.py仅扩展诊断助手到2030参数（V1G调用30元/MWh、供暖参与率0.25等均由原中央参数表与2030已验收审计核对），不改模型。每年先open 1h，再原B同窗数据基准/原样副本中性/开放/保守/零签约24h，最后真实生产profile 1h。24h各侧使用同一Base实际窗口净排放×1.0001预算；2030需只读补算预算，后两年复用原B已校验预算。保守短窗只是单调性对照，不是第三批全年作业。要求全部容量固定/输出≤1e-9、relative_v1 PASS、中性/单调性目标相对1e-7。完整回归尚待执行，不把语法与CLI检查当门禁通过。

新deploy_batch2.py仅能表示获授权的三个Open年份，以最新成功LATE-Open正式sbatch为模板；逐年PASS证据缺失即拒绝prepare，preflight缺失即拒绝提交，squeue账户作业数≥4即拒绝新增。明确不会创建第三批或重复LATE。Python编译与三个年份CLI静态检查通过。

当前三个新作业均未提交，门禁尚未启动。继续动作依赖T550转发恢复；已完成独立的来源审计和脚本准备。云端现有LATE未修改，无后台监听、无凭据读取、无输入重生成或科学模型修改。

## 2026-11-15 第二批2040/2060已放行；2030在24h碳预算门禁停止

恢复T550后先确认旧安装仅有original数据根、无新门禁进程；按断点补齐原件，后续缺少历史诊断助手目录已在新运行目录补齐，没有重建作者输入或改科学模型。安装PASS；537项测试完整覆盖（T550535通过，2项本机原归档测试已通过且源码SHA未变）。2040/2060原件SHA、原闭合/预算、三端BUILD_AUDIT身份、1h资源与全部投资固定审计、24h可行/容量身份/中性/单调性、真实44线程profile1h全部PASS。中性相对目标差均0；单调性最大浮点反向分别1.30e-16/2.14e-15，低于既有1e-7比较容差。证据提交db8e1915。

OPS-Open2040 Job5590946、2060 Job5590961已逐案新建冻结release、preflight PASS、held核对后release。根分别20261115_opsopen_2040_v9a12_t44_m750_tol1e4_v1和20261115_opsopen_2060_v9a12_t44_m750_tol1e4_v1，源码db8e1915；生产参数44线程/64CPU/750G/UNLIMITED/no-requeue，节点启动必须可用内存≥700GiB。22:41UTC快照为LATE5587177 RUNNING+两新案PENDING(Resources)，无实际AllocTRES/startup资源文件，不能宣称启动检查已通过。2030未提交，总队列3项，第三批未提交。

2030开放1h PASS，随后原B参考24h在201.84秒判INFEASIBLE，IIS另用841.74秒提取62214约束/82613界；门禁STOP，日志、原MPS和27.14MB IIS完整保留T550。只读比较本轮与原已通过B2030的24h MPS：NAME/ROWS/COLUMNS（含目标）/全部BOUNDS/ENDATA逐字节相同，唯一RHS差为annual_net_carbon_limit从10.95890410958904降至9.002825025595003 Mt，IIS包含该碳行。原额为4000×24/8760，新额按一般规则取Base同窗实际净排放×1.0001；该短窗不可行不等于全年OPS2030不可行。

已提交具体停止报告batch2/2030/STOP_REPORT_ZH.md并询问作者：是否只对2030全部24h对照恢复原B已验证10.95890410958904 Mt，全年4000 Mt/冻结容量/容差保持不变。当前尚未获该例外授权，不改预算、不重跑、不放行2030。等待答复时继续收尾两案登记和启动资源核验，不创建第三批。LATE结束后的年度行对偶恢复保持已授权安排。

操作入口：prepare_batch2_runtime.py的受限断点恢复、start_batch2_validation.py的有限回归/逐年门禁、collect_batch2_progress.py的一次性读回、finalize_batch2_year_gate.py及deploy_batch2.py。精确下一步：先读现有两job排队/启动状态；2030只有作者明确例外后才在新目录重跑相关门禁，旧失败目录不得覆盖。所有运行保留，无监听、无凭据读取，未改5587177或其他冻结包。

## 2026-11-15 22:53UTC 第二批2040/2060启动检查通过

Job5590946（OPS-Open2040/m4cm1702）和5590961（OPS-Open2060/m4cm1803）均于22:48:15UTC开始运行；实配cpu64/mem750G/node1/billing64、UNLIMITED/no-requeue。启动可用内存分别720.655060与719.145313GiB，均≥700，Gurobi13.0.2计算节点smoke PASS，stderr空，配置44线程；全年模型仍在构建，实际求解参数/全年服务上界读回待构建完成。云端3运行（含LATE5587177），无新增第四项；2030仍在门禁STOP等待作者窗口预算决定，不能因另两案已运行而绕过该门禁。

证据batch2/startup_verification_2040_2060.json及snapshots/20261115T225352Z/snapshot.json。放行与2030停止证据eb85777c，模型源码相对537项覆盖回归无变化。case_catalog已改RUNNING。下一步：作者明确2030短窗例外前不重跑或提交2030；后续询问时只读核实际模型构建/迭代，终态按5%余量规则备份、T550恢复年度对偶和验收；第三批未提交，无监听。

## 2026-11-15 23:20UTC OPS-Open2030已按作者例外放行，第二批齐备

作者明确批准2030的24h工程门禁及全部对照使用原B额度10.95890410958904Mt；全年4000Mt/冻结容量/求解容差保持不变。新目录runtime_batch2_2030_author_window_20261115七项门禁全部PASS：Open1h、原B/复制根中性/Open/Conservative/zero24h、真实生产profile1h。数据根中性目标差0，单调性最大反向1.5609e-15<1e-7。原537项模型回归源码LF SHA未变，额外3项例外作用域测试本机/T550均PASS。证据/冻结源提交02c4dd84，例外工具125fdfdd；旧失败MPS/IIS/日志完整保留。

新release20261115_opsopen_2030_v9_t44_m750_tol1e4_v1，沿用B2030 v3原冻结源，无新增闭合或筛选；90项原数据与作者输入SHA匹配，负荷逐行一致。sbatch从最新成功启动OPS-Open2060/5590961派生，preflight PASS，经held核对后release Job5591162。全年命令horizon=full_year、V9、44线程、64CPU/750G/UNLIMITED/no-requeue，不传短窗预算；原模型/BarX/BarPi/状态保全开启。

23:20UTC快照：LATE5587177、OPS-Open2040/5590946、2060/5590961三项RUNNING；2030/5591162 PENDING等待Resources，实际启动内存/smoke尚待分配节点，不宣称已通过。四项已全部提交，未超过4个并发/排队名额。2030启动脚本继续强制可用内存≥700GiB。

精确证据：batch2/2030/author_window_v2/、batch2/2030/FINAL_YEAR_RELEASE_GATES.json、batch2/deployment/ops_open_2030/。注意batch2/2030/YEAR_GATES_STOP.json与原窗口预算仍是历史失败记录，当前有效门禁/预算位于author_window_v2，不得用旧STOP再次拦截已获作者例外通过的新作业，也不得删除旧失败。

下一步询问时核原2030job实际分配/启动内存及四案运行，禁止重复提交；任何终态按5%余量规则完整备份T550、relative_v1与小文件交付。LATE-Open结束后按第一批在原MPS+自身BarPi上恢复年度核算行对偶并核完整行序SHA。第三批仍须作者明确确认，无后台监听，原有三项运行和冻结包未修改。
