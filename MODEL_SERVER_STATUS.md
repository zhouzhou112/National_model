# CISPO 2030 full-year server status

**2026-10-29 19:26 GMT C2050备份已自主启动。** 作者“再次尝试t550备份”解除本次等待确认；连接恢复后已确认无同名目标/operation、无活跃传输、全局锁可用。新计划105文件5,511,013,265bytes，完整T1/T2/T3含原MPS及显式启动元数据，30%余量门禁PASS，预计余35.2781%。PID351788/SID351788独立session、stdin DEVNULL，当前RUNNING/T1 TRANSFERRING，尚未完成校验；本机断线不影响T550直连云端任务。

**2026-10-29 19:09 GMT（北京10月30日03:09）：云端1项RUNNING，C2050已完成。** C2050/5207165于16:28:53GMT（北京10月30日00:28:53）COMPLETED/0:0，总9天04:04:06，496轮OPTIMAL，目标5700892.181056213 million CNY，峰值RSS623.282GiB；保全COMPLETE/errors=[]，原模型已归档。最终PInf0.02918/DInf2.17e-6/Compl3.34e-5，旧10-14 relative_v1 HARD_FAIL（co2_source及solver原始残差>0.01）；10-27独立复评/筛选证书尚未执行，不自动采纳或放行2060。Case3 2050/5294579第129轮，运行2天05:38:15，PInf3.319e8/DInf4.760/Compl1.410e6，近10轮下降67.99%/89.88%/68.21%，22.12分钟/轮，stderr空。T550转发连接拒绝，备份配置已准备，尚未计划或启动传输，已请作者恢复。

**2026-10-29 10:30 GMT（北京18:30）：云端2项RUNNING，无新终态。** C2050/5207165第482轮，运行8天22:05:17，PInf0.08179/DInf4.91e-6/Compl1.0438e-4；472→482三项下降58.02%/48.55%/58.83%，约25.41分钟/轮。Case3 2050/5294579第105轮，运行1天20:58:58，PInf3.65e9/DInf1467.65/Compl1.516e7；95→105下降36.09%/68.58%/36.58%，约23.00分钟/轮。两者stderr为空，仍未完成；不由互补性数值推断终止或ETA。B三年仍COMPLETED，既有完整备份与扩展PASS记录不变，未重复传输。

**2026-10-28 收尾：B2040/2050/2060 完整备份及扩展验收完成，初步分析在 T550。** 三年330文件16,566,391,148bytes备份于17:26:52 UTC完成，九层VERIFIED且source_unchanged；独立relative_v1（10-27 Mt口径）均PASS，三套验收JSON已同步本机/T550，原QC保留。18:48GMT只读云端2项RUNNING：C2050/5207165第444轮（PInf1.1663/DInf1.53e-5/Compl0.001693），Case3 2050/5294579第63轮（1.65e10/4.02e4/7.12e7）。T550汇总11个已解案例；仅取回606,996bytes压缩包，101载荷文件2,991,005bytes，包和逐文件SHA通过。本机case_results统一索引15个案例版本，原件未移动/删除。

**2026-10-28 16:46 GMT（北京10月29日00:46）：云端2项RUNNING，B三年完成。** C2050/5207165第439轮（PInf1.4375/DInf1.91e-5/Compl0.002149），Case3 2050/5294579第58轮（1.8736e10/5.49e4/8.2191e7）。B2040/5297384、B2050/5297390、B2060 v2/5297410均COMPLETED/0:0、OPTIMAL，162/160/178轮，作业耗时17:43:38/15:48:52/15:49:52，保全COMPLETE且errors=[]。T550恢复后16:49UTC已启动三年完整自主备份，PID2538534/PPID1/SID2538534，330文件16,566,391,148bytes，预计余35.4185%；当前RUNNING/T1 TRANSFERRING，不称备份完成。本机可关机，不影响T550直连云端。

**2026-10-28 11:14 GMT（北京19:14）：云端5项RUNNING，无新终态。** B2040/5297384第132轮（PInf0.00532/DInf6.01e-6/Compl1.08e-4），B2050/5297390第145轮（2.72e-4/4.91e-6/5.89e-5），B2060 v2/5297410第159轮（9.33e-4/7.17e-6/6.74e-5）；三者近10轮全部指标改善，均已通过构建/排序进入Barrier，仍未结束。Case3 2050/5294579第43轮（2.58e10/1.48e5/1.18e8），近10轮三项下降54.71%/58.08%/55.03%，23.12分钟/轮。C2050/5207165第427轮（2.37/2.86e-5/0.00367），近10轮三项下降33.95%/10.08%/36.30%，26.90分钟/轮。五项stderr无错误；不据此预估结束时间。

**2026-10-27 21:25 GMT T550恢复核验：** 云端5项RUNNING；C2050/5207165第396轮，Case3 2050/5294579第7轮，B2040/5297384、B2050/5297390、B2060 v2/5297410仍构建且启动检查PASS。T550遗留筛选CSV已完整到达（7,470,093bytes，SHA fe5d87a2adc6f5d6b8ad21606c571979312c1f632780fcdc9ea7500b7f0f2368），未重复传输；设置与全套回归相同数据环境后，tests.test_production_screen 6项全部PASS，解决上一轮唯一缺夹具报错。

**2026-10-27 第二批 B 放行：** 云端快照 2026-10-27T21:21:33.430034+00:00 为 5 RUNNING、0 PENDING。B2040/5297384、B2050/5297390 已 release 且启动 smoke PASS；B2060 v2/5297410 已 release 且启动 smoke PASS。三年云端一致映射 1h/3×24h、目标/双向交叉可行/成本门禁 PASS，年度碳上限不变。首次 B2060/5295127 构建闭合核验 FAILED，已完整保全现存文件并 T550 SHA 备份；不是解。

- **2026-10-27 B 静态闭合后最新状态：** 三年 1h 闭合通过，B2060 全部门禁 PASS；B2040/2050 24h 仍受碳预算 IIS 阻塞，非网络残差，三年均未提交。等待作者决定短窗年度碳预算门禁规则。492 项回归通过（1 跳过），见 base_frozen_closure_20261027/STOP_REPORT_ZH.md。5207165/5294579 仅只读确认运行。


**2026-10-26 20:01 GMT：B2030 v3 已启动，Job5276703 RUNNING。** 源码仍9f0a042，479项源码/输入/冻结来源与v2逐字节一致、原门禁复用；新WLS路径字符串preflight PASS，未读取许可内容。m4cg1603实配64CPU/750G/billing64、48线程、UNLIMITED/no-requeue，Gurobi13.0.2启动smoke PASS，可用731.251629GiB。尚无Barrier轮次/最终RSS；既有日志持续记录，无后台监听。保留v1/v2及5276670失败备份，不碰5201318/5207165/case3 2050；后续年份仍等作者线程确认。

- **2026-10-26 19:43 GMT：B2030 Job5276670已提交/release但启动许可失败，停止重提。** 最终源码9f0a042、v2冻结/preflight和481回归/两道身份/参数门禁PASS；m4cg1603实配64CPU/750G/billing64、UNLIMITED。19:39:55–19:39:59 gp.Env.start报旧License2847107过期，尚未构建模型/无output_8760，无全年RSS/轮数指标。部署误沿用旧默认许可；记录已有10-20独立WLS路径，未读凭据，未自动重试。23文件/92,477,291bytes启动失败记录已T550逐项SHA备份COMPLETE，余36.2379%；不是完整解备份。下一步引用已登记WLS路径验证许可并新建v3；保留v1/v2、不重启旧Job、不碰保护作业。详见B review第9节。

- **2026-10-26 GMT：作者修订后 B2030 本地全部门禁 PASS，准备生产冻结。** 门禁1按保存 X 补成本分项，最大相对差1.64e-13；变化列 reduced cost≤2.29e-15，原目标差/双向交叉可行通过。Cross2 relative_v1 已修复，basic 语义导出选 X/Pi、Cross0不变；开放柔性24h门禁2容量差≤2.84e-14、relative_v1 PASS、保全 COMPLETE。2030中央参数及“仅投资界变化”原MPS对比 PASS；全套480 tests OK。以 `base_frozen_B_20261026/FINAL_GATES_PASSED.json` 为本地放行依据，下一步独立 B2030 48线程冻结/preflight/held资源核验后直接release；后续年份仍等作者线程确认。

- **2026-10-26 GMT：框架 B 候选实现已验证，身份门禁失败，停止放行。** 源码 `ba7a23f`；X 未保全，按授权回退 BarX，36686 个 VRE 新建值同次解析零差，hydro spur 独立补表 SHA 已核。默认关闭 MPS 字节一致；1h 固定 86745 列、clip 合计 2.64e-10 GW；最终回归 477 tests OK。24h 固定 Base/零签约 B 目标相对差 8.67e-16，但风光出力最大差 8.57 GW、正向潮流 2.81 GW，逐时一致门禁未通过；保存解双向交叉可行且等成本，支持退化多解，未自行豁免。Cross2 的 relative_v1 缺 barrier_primal_dual_metrics，须修复兼容性。未做开放柔性 B24h、参数核准或任何 B 生产提交/release；保护作业与 case3 2050 未触碰。详见 `supplementary_materials/reviews/base_frozen_B_20261026/REVIEW_ZH.md`。下一步等待作者处理逐时一致判据，再修复 QC/续做门禁；后续年份线程仍待作者确认。

> 2026-10-20 C2050 OOM追加取证：5201262于英国04:08:53在ordering2005s终止，signal9/137与Slurm OOM一致，无Barrier迭代。实际750G，启动723.370GiB，进程RSS峰723.333GiB、Slurm峰719.855GiB；没有FactorNZ或终止时cgroup/kernel记录，不断言精确峰值需求。预处理nnz较成功case32030增加21.16%，启动门禁/短窗不保证全年峰值。原MPS与全部现存文件保留，无解可导出；未重启、改参或干预其他作业。详见case3_2040_C2050_launch_20261019/REVIEW_ZH.md与C2050_oom_20261020/。下一步先核实大内存资源，改变线程需作者核准。

> 2026-10-12英国12:10（北京19:10）取证：原2050/4844528已COMPLETED/0:0，结束英国04:54:27（北京11:54:27），总运行11天13小时44分50秒；Gurobi716轮OPTIMAL、runtime996416.02秒，目标5751972.5053 million CNY。终轮打印PInf2.25e-4/DInf1.45e-6/Compl6.01e-5、目标差4631.44，callback相对差0.08052%；717条连续/8源SHA PASS，stderr空。preservation COMPLETE/errors=[]，BarPi导出可用。原冻结包旧QC HARD_FAIL/PENDING不能自动当新口径结论；新口径功率平衡0.265kW和成本相对闭合1.68e-11可过，但双向流重叠0.12034%高于0.01%约12倍、额外损耗198.73GWh，水库29.27m³尚缺逐站分母复核，科学验收未全部通过。证据`base_2050_continuation_20260930/status_20261012T111059Z/`。Git基准a4d4727；仅取证/交接小文件同步，本次交接条目部分暂存，其他SI未提交内容/稿件留工作区。未改作业/归档/模型，无scontrol/scancel、Stage B、新求解、部署或监听。下一步按作者新口径验收，不据此自动启动2060/case3。

> 2026-10-11英国15:43（北京22:43）原2050/4844528 RUNNING/m4cm1802、11天0小时33分42秒，iter682/48线程沿用。PInf0.00118/Compl0.000338/目标差26080.73，较670下降36.56%/37.52%/37.44%；DInf4.39e-6较670上升78.46%，679–682连续4轮上升，为678的1.969倍，低于642峰值但反弹尚未恢复，不能沿用上次连续下降描述。其他三项逐轮下降，近期拟合每轮3.56%/3.65%/3.65%，较前窗放缓；暂无同步大跃升/显式警告/终态，stderr空。22.3867分钟每轮，RSS420.09GiB/峰685.98GiB；683条连续/4源SHA PASS。证据`base_2050_continuation_20260930/status_20261011T144319Z/`。历史主指标约9–15小时类比未覆盖新对偶反弹，不将此前半天至一天作倒计时；2040 PInf匹配终轮不等于整体结束。Git基准e577e13；仅取证/交接与小文件GitHub同步，未改运行包、无scontrol/scancel、新作业、Stage B、部署或监听。下一步只读关注对偶恢复/终态，按作者最新规则验收。

> 2026-10-11英国11:30（北京18:30）原2050/4844528 RUNNING/m4cm1802、10天20小时21分1秒，iter670/48线程沿用。PInf0.00186/DInf2.46e-6/Compl0.000541/目标差41691.32，较642下降67.65%/63.01%/69.94%/69.91%。DInf646/651/654小反弹后654→670连续16轮下降，仍为636反弹前5.655倍；近10轮四项逐轮下降，无新大跃升/显式警告/终态，stderr空。拟合每轮下降3.98%/3.60%/4.29%/4.28%，PInf/Compl/目标差较前窗加快。23.46分钟每轮，RSS423.31GiB/峰685.98GiB；671条连续/4源SHA PASS。证据`base_2050_continuation_20260930/status_20261011T103038Z/`。历史对应2030第309–321/2040第553–604轮，余10.56–15.25/0.39–20.33小时，仅条件性半天至一天安排，不以2040 PInf单项判仅余1轮，不保证/不含验收。Git基准78319c4；仅取证/交接与小文件GitHub同步，未改运行包、无scontrol/scancel、新作业、Stage B、部署或监听。下一步只读观察恢复/终态，验收按最新作者规则。

> 2026-10-11英国00:18（北京07:18）原2050/4844528 RUNNING/m4cm1802、10天9小时9分19秒，iter642/48线程沿用。PInf0.00575/Compl0.00180/目标差138551.01，较628下降28.84%/31.56%/31.65%；DInf6.65e-6，较628升9.925倍，636→642升15.287倍，新反弹未恢复。其他三项逐轮下降，近期拟合每轮2.41%/2.62%/2.63%，较前窗放缓；无同步PInf/Compl大跃升、显式警告/终态，stderr空。近10轮22.555分钟，RSS420.09GiB/峰685.98GiB，643条连续/4源SHA PASS。证据`base_2050_continuation_20260930/status_20261010T231856Z/`（UTC日期）；历史其他三项类比余0.41–1.36天，但未覆盖新对偶反弹，当前不可靠承诺此前1–2天。Git基准15c00c8，保留作者新决定/其他稿件；未改冻结运行包，无scontrol/scancel、新作业、Stage B、部署或监听。下一步只读观察对偶恢复和终态，按最新作者规则验收。

> 2026-10-10英国18:57（北京10-11 01:57）原2050/4844528 RUNNING/m4cm1802、10天3小时48分18秒，iter628/48线程沿用。PInf0.00808/DInf6.70e-7/Compl0.00263/目标差202708.07，较610下降41.87%/39.64%/44.98%/44.98%。DInf611进一步升至2.21e-6，当前较该峰下降69.68%，仍为609反弹前2.669倍；614/627有小反弹，不能称完全恢复或单调下降。其他三项逐轮下降，近指数拟合每轮2.95%/3.29%/3.28%，暂无PInf/Compl大跃升、警告/终态，stderr空。近10轮23.1883分钟，RSS420.09GiB/峰685.98GiB；629条连续/4源SHA PASS。证据`base_2050_continuation_20260930/status_20261010T175755Z/`。历史对应2030第290–307/2040第505–571轮，当前速度余0.66–0.93/0.55–1.61天，条件性约1–2天，不保证/不含QC。Git基准ea7e392；仅取证/交接及小文件GitHub同步，未改模型/作业、无scontrol/scancel、新求解、监听或部署。下一步只读观察残差及终态/QC。

> 2026-10-10英国12:01（北京19:01）原2050/4844528 RUNNING/m4cm1802、9天20小时52分19秒，iter610/48线程沿用。PInf0.0139/Compl0.00478/目标差368429.13，较578下降54.28%/57.70%/57.54%；DInf1.11e-6，610较609回升4.4223倍，较578上升78.17%。其他三项仍逐轮下降，未伴随PInf/Compl大跃升；不能称四项稳定指数收敛，DInf含反弹拟合R²仅0.4795。近10轮23.5683分钟，RSS420.09GiB/峰685.98GiB；611条连续/4源SHA PASS，stderr空、无显式警告/终态。证据`base_2050_continuation_20260930/status_20261010T110156Z/`。历史对应2030第281–300轮/2040第485–558轮，当前速度余0.79–1.10/0.77–1.96天，若反弹恢复可条件性约1–2天，非保证/不含QC。Git基准b273b2c；仅取证/交接和小文件GitHub同步，未用scontrol/scancel、未改模型/作业，无新求解/监听/部署。下一步只读关注610反弹后走势、终态与QC。

> 2026-10-09英国23:03（北京10-10 06:03）原2050/4844528 RUNNING/m4cm1802、9天7小时53分29秒，iter578/48线程沿用。PInf0.0304/DInf6.23e-7/Compl0.0113，较568下降18.50%/24.48%/20.98%，目标差8.6768901e5下降21.42%。近10轮四项逐轮下降，无新反弹/大跃升/警告、stderr空、无终态；23.8483分钟每轮。RSS422.50GiB/峰685.98GiB，579条连续/源SHA PASS。证据`base_2050_continuation_20260930/status_20261009T220306Z/`。历史近期速度余0.98–1.32/1.13–2.57天，条件性仍约1–3天，不含QC/非保证。Git基准8640d96；仅取证/交接和小文件GitHub同步，未用scontrol/scancel、未改模型/作业，无新求解/监听/部署。下一步只读看终态/QC。

> 2026-10-09英国18:53（北京10-10 01:53）原2050/4844528 RUNNING/m4cm1802、9天3小时44分20秒，iter568/48线程沿用。PInf0.0373/DInf8.25e-7/Compl0.0143，较553下降29.62%/34.00%/32.23%，目标差1.10423232e6下降32.10%；553后四项逐轮下降，无新反弹/大跃升，stderr空、无警告/终态。打印DInf<1e-6不等于整体收敛，callback定义不同。短窗口每轮下降2.24%/2.80%/2.54%，近10轮24.3267分钟；RSS420.09GiB/峰685.98GiB。569条连续/源SHA PASS，证据`base_2050_continuation_20260930/status_20261009T175357Z/`。历史当前速度余1.06–1.42/1.27–2.77天，条件性仍约1–3天，非保证/不含QC。Git基准d0cbc9f；仅取证/交接和小文件GitHub同步，无scontrol/scancel、模型/作业更改、新求解/监听/部署。下一步只读观察终态与科学QC。

> 2026-10-09英国12:47（北京19:47）原2050/4844528 RUNNING/m4cm1802、8天21小时38分2秒，iter553/48线程沿用。PInf0.0530/DInf1.25e-6/Compl0.0211，较521下降50.00%/57.04%/53.83%，目标差1.62625172e6下降53.79%。DInf424→551连续下降127轮，552回升9.09%，553降至新低；当前较424峰值下降97.45%，不能称连续129轮。521–553近指数衰减，每轮2.15%/2.50%/2.37%，较上一1.60%/1.78%/1.69%回升；近10轮24.255分钟。RSS420.09GiB/峰685.98GiB，stderr空、无大幅跃升/显式警告/终态；554条连续/源SHA PASS。证据`base_2050_continuation_20260930/status_20261009T114739Z/`。历史当前速度余1.16–1.50/1.48–3.02天，条件性安排约1–3天（英国10月10–12日），非保证且不含QC。Git基准d8c7419，仅取证/交接和小文件GitHub同步；无scontrol/scancel、模型/作业改动、新求解、监听或部署。下一步关注波动/终态QC。

> 2026-10-09英国00:07（北京07:07）原2050/4844528 RUNNING/m4cm1802、8天8小时58分7秒，iter521/48线程沿用。PInf0.106/DInf2.91e-6/Compl0.0457，较489下降42.08%/45.61%/44.13%，目标差3.51891586e6下降44.16%。DInf自424连续97轮回落94.06%，489后无新跳升；仍高于399水平。489–521近指数衰减，每轮1.60%/1.78%/1.69%，比上一2.24%/2.54%/2.42%放缓；近10轮22.99分钟。RSS420.09GiB/峰685.98GiB，stderr空、无显式警告/终态；522条连续/源SHA通过。证据`base_2050_continuation_20260930/status_20261008T230744Z/`（UTC目录日期）。历史当前速度余1.29–1.66/1.79–3.48天，条件性安排约2–4天（英国10月11–13日），速率放缓不机械倒计时，非保证且不含QC。Git基准9c4058b；仅只读取证/交接与小文件GitHub同步，无scontrol/scancel、模型/作业改动、新求解、监听或部署。下一步关注速率和终态QC。

> 2026-10-08英国11:37（北京18:37）原2050/4844528 RUNNING/m4cm1802、7天20小时27分28秒，iter489/48线程沿用。PInf0.183/DInf5.35e-6/Compl0.0818，较459下降49.17%/53.48%/51.88%，目标差6.30133597e6下降51.84%。DInf自424峰值连续65轮回落89.08%，459后无新跳升，仍高于399水平。459–489近指数衰减，每轮2.24%/2.54%/2.42%，比上一窗口3.05%/3.62%/3.26%放缓；近10轮25.025分钟。RSS420.09GiB/峰685.98GiB，stderr空、无显式警告/终态；490条连续/源SHA通过。证据`base_2050_continuation_20260930/status_20261008T103705Z/`。历史按近期速度余1.55–2.05/2.36–4.34天，安排仍约2–5天，非保证且不含QC。Git基准57f21e5；仅只读取证/交接及小文件GitHub同步，无scontrol/scancel、模型/作业改动、新求解、监听或部署。下一步关注速率/对偶回落和终态QC。

> 2026-10-07英国22:49（北京10-08 05:49）原2050/4844528 RUNNING/m4cm1802、7天7小时40分4秒，iter459/48线程沿用。PInf0.360/DInf1.15e-5/Compl0.170，较435下降54.55%/61.41%/57.18%，目标绝对差1.308507692e7下降57.06%。DInf自424峰值连续35轮回落76.53%，435后无新上跳；仍高于399水平。435–459三项近指数衰减，每轮3.05%/3.62%/3.26%，log拟合R²0.9940/0.9872/0.9927。近10轮24.115分钟，stderr空、无显式警告/终态；RSS420.09GiB/峰685.98GiB，460条连续/源SHA通过。证据`base_2050_continuation_20260930/status_20261007T214941Z/`。历史类比条件性余约2–5天（英国10月9–12日），非保证且不含QC。Git基准899fd88；仅只读取证/状态交接与已审查小文件同步，未改原作业/模型/配置，未用scontrol/scancel、无新求解/监听。下一步关注三项下降能否保持、终态和科学QC。

> 2026-10-07英国13:03（北京20:03）原2050/4844528 RUNNING/m4cm1802、6天21小时53分44秒，iter435、48线程沿用。PInf0.792/Compl0.397较399下降68.57%/72.62%，仍近指数衰减（399–435每轮3.11%/3.49%，log拟合R²0.9972/0.9988）。DInf需修正此前同步下降判断：405轮20.88倍、424轮8.46倍上跳，现2.98e-5为399的121.63倍；已从424峰值连续11轮回落39.18%。没有117式PInf/Compl同步暴涨，但不能称无数值跃升。近10轮25.5333分钟，RSS420.08GiB/峰685.98GiB，stderr空、无终态；436条连续及源SHA通过。证据`base_2050_continuation_20260930/status_20261007T120321Z/`，含独立对偶跳升统计与指数拟合。历史余时类比未考虑对偶反弹，不据此缩短/承诺先前3–6天预期。Git基准a857302；仅只读取证/交接并按GIT_SYNC_POLICY同步已审查小文件，保留未审核稿件/原日志本地。无模型/配置/作业改动、无scontrol/scancel、无新求解或监听；下一步关注对偶回落及终态QC。

> 2026-10-06英国22:12（北京10-07 05:12）原2050/4844528只读复查：squeue/sacct确认RUNNING/m4cm1802、6天7小时3分15秒，64CPU/750G/UNLIMITED、48线程沿用；未用scontrol/scancel。最新iter399，PInf2.52/DInf2.45e-7/Compl1.45，绝对目标差1.106989703e8；较385轮下降30.19%/37.97%/36.68%/36.61%。近389→399 PInf/Compl/目标差逐轮下降，DInf在394/399小幅回升；24.0967分钟/3821.32Work每轮，较前22.9067分钟略慢。117轮后无同定义大跃升，stderr空、无显式警告/终态；RSS当前420.08GiB/峰值685.98GiB，400条连续/源SHA核验PASS。历史匹配2030第196/167/167轮、2040第333/255/254轮，当前速度余2.54–3.03/4.55–5.87天；条件性安排仍约3–6天（英国10月9–12日），非保证上限且不含QC。证据`base_2050_continuation_20260930/status_20261006T211252Z/`。Git0a03cc4+既有dirty，仅取证与状态文档；原作业及其他窗口试验/自动化未操作，保留其他窗口连接阻塞记录。下一步继续观察原作业终态与QC，不自动改界或提交求解。

> 2026-10-06英国16:49（北京23:49）原2050/4844528仍RUNNING，48线程沿用，iter385，运行6天1小时39分。PInf3.61/DInf3.95e-7/Compl2.29，较325轮下降74.03%/89.58%/83.41%，绝对目标差1.746321979e8下降83.22%。近期22.9067分钟/3298.72Work每轮，PInf/Compl/目标差逐轮下降，DInf有小幅波动；未见同类再次大跃升、显式警告或终态。RSS420.08GiB/峰值685.98GiB，stderr空，386条连续/源SHA核验PASS。历史类比条件性余约3–6天（英国10月9–12日），非保证日期、不含QC验收。证据status_20261006T154913Z/；仅只读核验，未操作原作业或其他窗口试验/自动化。

> 2026-10-05英国17:23（北京10-06 00:23）只读核验2050/4844528仍RUNNING，48线程沿用，iter325，运行5天2小时13分。PInf13.9/DInf3.79e-6/Compl13.8，较273轮下降75.66%/38.97%/80.99%，目标绝对差1.040477959e9下降80.42%。近期21.41分钟/2639.79Work每轮，PInf/Compl/目标差逐轮下降，DInf小幅波动；未见同类再次大跃升、显式警告或终态。RSS420.07GiB/峰值685.98GiB，stderr空，326条迭代连续/源SHA核验PASS。历史类比条件性余约3–7天（英国10月8–12日），非保证日期、不含QC验收。证据status_20261005T162312Z/；仅squeue/sacct/sstat及文件读取，无scontrol/scancel，极小界建议未应用。

> 2026-10-04英国22:30（北京10-05 05:30）2050/4844528 RUNNING/48线程/Restarts0，iter273，运行4天7小时21分。PInf57.1/DInf6.21e-6/Compl72.6，较250轮下降76.88%/37.02%/75.64%；目标差5.31280163e9，下降74.35%。近期22.31分钟每轮，DInf有局部波动；无同类再次大跃升、显式警告或终态。历史阶段对齐约2030第95–134轮、2040第139–226轮；条件性余时仍约4–8天（英国10月8–12日），非保证上限、不含QC验收。RSS当前420.06GiB/峰值685.98GiB、stderr空，274条迭代连续/源SHA核验PASS。证据status_20261004T213051Z/，未干预求解。

> 2026-10-04英国14:04（北京21:04）复查仍RUNNING/iter250。应用户要求的条件性历史类比：当前约处于2030第80–110、2040第120–170轮阶段；历史对应剩余约3.6–3.9/7.0–7.7天。安排上粗估还需4–8天（英国10月8–12日），前提是不再大跳升/平台且后段类似历史，非保证上限或成功概率；仅Barrier完成、不含QC验收。详细方法/哈希与复现见convergence_eta_20261004/REVIEW_ZH.md；无作业改动。

> 2026-10-04英国13:54（北京20:54）2050/4844528 RUNNING/48线程/Restarts0，iter250、运行3天22小时44分。PInf247/DInf9.86e-6/Compl298、目标绝对差2.071438044e10，四项均已优于116轮跃升前水平；首次同时达到该比较条件为242轮。最近10轮四项逐轮下降、21.005分钟/2447.91Work每轮，未见同类大跃升；仍未收敛。RSS当前420.04GiB/峰值685.98GiB、stderr空、无终态。证据status_20261004T125431Z/及SHA核验PASS，仅取证和交接。

> 2026-10-03英国18:25（北京10-04 01:25）2050/4844528 RUNNING/48线程/Restarts0，iter193、运行3天3小时15分。PInf5.43e5/DInf0.00159/Compl6.47e5，较179轮下降约98.84%/98.55%/98.60%；最近10轮19.2117分钟/1644.16Work每轮。PInf/Compl/目标差持续下降，DInf末轮小幅回升；未见同类大跃升，仍未恢复116轮水平、未收敛。RSS当前420.00GiB/峰值685.98GiB、stderr空、无终态。证据status_20261003T172509Z/及SHA核验PASS，仅取证和交接。

> 2026-10-03英国14:03（北京21:03）2050/4844528 RUNNING/48线程/Restarts0，iter179、运行2天22小时53分。PInf4.69e7/DInf0.11/Compl4.61e7，较138轮均下降超过99.9%；最近10轮三残差逐轮下降、19.3667分钟/1717.69Work每轮，117轮后未检出同类大跃升。仍远高于116轮水平、未收敛，不给ETA。当前RSS419.96GiB/峰值685.98GiB、stderr空、无终态。证据status_20261003T130314Z/及SHA核验PASS，仅只读取证和交接。

> 2026-10-02英国23:14（北京10-03 06:14）2050/4844528仍RUNNING/48线程/Restarts0，iter138、2天8小时4分。PInf6.15e10/DInf3430/Compl6.16e10；最近10轮三残差逐轮下降约74%/84%/76%，但仍比跃升前差7–8个数量级，恢复迹象不等于成功保证。五例日志/冻结源码/输入诊断见barrier_jump_diagnosis_20261002/REVIEW_ZH.md；内部恢复/重初始化是推断，唯一根因未定。源SHA与离线复算通过；原作业继续保留，无参数或模型更改。

> 2026-10-02英国23:03（北京10-03 06:03）2050/4844528仍RUNNING/m4cm1802，运行2天7小时54分、iter137、48线程/Restarts0。**116→117数值严重退步**：PInf3.72e3→4.40e11、Compl416→5.15e11；137轮虽回落至PInf7.32e10/DInf3890/Compl7.24e10，仍远高于跳升前，未收敛。最近10轮21.9283分钟/2884.03Work每轮，与前次近期速度接近。当前RSS419.82GiB、峰值685.98GiB，两份stderr空、无终态或显式数值警告；不能据RUNNING/空stderr称数值正常，也不能提前判定NUMERIC终态。证据status_20261002T220350Z/、SHA核验PASS；只读，无作业干预，跳升原因尚未定位。

> 2026-10-02英国11:58（北京18:58）2050/4844528 RUNNING/m4cm1802，已运行1天20小时49分，Barrier iter108。最近98→108约21.9450分钟/2884.04Work每轮，较前次19.2283分钟慢约14.1%，内部Work也增加，不能归因线程。日志PInf4.79e3/DInf8.83e-5/Compl513；PInf/Compl持续下降，DInf在104轮回升后部分回落，尚未收敛。当前RSS419.58GiB、峰值685.98GiB，48线程配置不变，两份错误日志0字节、Restarts0、无终态文件。证据见base_2050_continuation_20260930/status_20261002T105846Z/，SHA核验PASS；只读，无作业干预。

> 2026-10-01英国21:40（北京10-02 04:40）2050/4844528 RUNNING/m4cm1802，已运行1天6小时30分，Barrier iter67。最近57→67约19.2283分钟/1649.84Work每轮，三残差持续下降；最新PInf2.41e7/DInf0.0142/Compl2.64e6，仍未收敛。当前RSS418.90GiB、峰值685.98GiB，48线程配置不变，两份错误日志0字节、Restarts0。证据见base_2050_continuation_20260930/status_20261001T204025Z/；只读，无作业干预。

> 2026-10-01英国14:48（北京21:48）2050/4844528 RUNNING/m4cm1802，已运行23小时38分，无重启。Presolve17448.75s、Ordering4729.31s已完成；Barrier iter47，最近37→47约21.4433分钟/轮，日志三残差下降但PInf6.15e9/DInf25.3/Compl6.34e8仍很大，远未收敛。Factor NZ3.519e10/Ops2.098e15；当前RSS418.24GiB/峰值685.98GiB（分配750GiB），两份stderr空。48线程设置不变；只读、无作业干预。完整证据见base_2050_continuation_20260930/status_20261001T134804Z/。

> 2026-09-30英国17:58（北京10-01 00:58）2050/4844528仍RUNNING/m4cm1802、约2小时49分。全年构建与原模型归档已完成：50907233行/41458383列/485386301非零，MPS4051434705bytes、manifest COMPLETE/errors=[]。实证48线程/NF2/1e-4/Cross0；目前Presolve7305s，尚未Ordering/Barrier。当前RSS约87GiB、峰值101.5GiB，两份stderr均空，无重启。只读，无作业变更；证据见base_2050_continuation_20260930/status_presolve_20260930_summary.json。下一步等待Presolve/Ordering及Barrier首轮。

> 2026-09-30英国15:09（北京22:09）2050已按用户授权启动：job4844528 RUNNING/m4cm1802，实际64CPU/750G/billing64/UNLIMITED；Gurobi48/NF2/1e-4/Cross0，无Time/SoftMem限制。计算节点许可、续接合同、7回归PASS，正式scope2050/边界2040/8760，当前全年构建，尚无Barrier。release=20260930_base2050_v9_t48_m750_tol1e4_v1。原2040候选129站小越界在独立bound-closed副本中仅扣回合计308.6947kW（单站最大7.2944kW），原结果和HARD_FAIL保留；派生173800条、仅130个容量值变化，边界复审零越界、输入及真实小构建/归档入口PASS。195原repo文件SHA一致，未改物理模型或原输入。详情base_2050_continuation_20260930/REVIEW_ZH.md；下一步只读构建/归档/Barrier，不自动2060/Stage B。此条覆盖下方队列空及未启动2050的历史状态。

> 2026-09-30（英国时间）只读终态与线程对比：2040/4682935已COMPLETED/605轮/solver843709.49s，squeue空；2030/4614693为OPTIMAL/348轮/451391.62s但QC门禁退出2，两例QC均HARD_FAIL。V9/NF2共同iter10→348：48线程20.6596、44线程21.7142分钟/轮，44慢5.10%；额外257轮占日志总差90.86%，非线程因果分解。旧44/NF1约17分钟每轮不可作为当前V9优势证明。两例64CPU/750G/billing64；速度优先暂倾向48，未改配置或启动配对/2050/Stage B。证据与限制见supplementary_materials/reviews/thread_comparison_20260930/REVIEW_ZH.md。此条更新下方历史RUNNING状态。

- 2026-09-19 19:22 北京时间：用户明确授权续接2040并恢复44线程。新Base2040 job4682935于19:19:50启动，当前RUNNING/m4cg1701，进入全年构建；实际64CPU/750GiB/billing64/UNLIMITED，Gurobi44线程/NF2/1e-4/Cross0，无TimeLimit/SoftMemLimit。尚未Barrier，不宣称收敛。

<!-- dual_screening_20261002_status -->
> 2026-10-02 筛选复核覆盖：Base2050/4844528保持运行，最新只读日志116→117的PInf3.72e3→4.40e11、Compl416→5.15e11；135仍未恢复。旧“残差持续改善”仅为历史状态。本轮24h联合全候选/筛选加回配对通过物理QC与定价，但无短窗提速；固定服务器转发上传中途失联，2016h尚未启动，不能登记为通过。下一轮联合独立2030→2060，见SCENARIO_EXECUTION_PLAN_20261002.md；本轮证据supplementary_materials/reviews/dual_screening_20261002/。云端作业未暂停、改参或新提交。
  44/48日志同iter10→39复算：旧Base4496031为17.2264、新Base4614693为19.3270分钟/轮，后者慢12.19%；模型/NF/节点不同，不能因果归于线程数。
  原2030候选86900条；2040真实小构建发现一站G000021474::dpv因2030清掉5.709kW存量、2040再叠加而超上限4.352942kW。独立derived candidate只收回该站4.352942kW（小于既有10kW清理尺度），原结果和HARD_FAIL/未接受标记保留，非原始精确解不变。
  194个原repo文件SHA一致，物理代码/输入/上限/QC阈值未改；新44线程engineering profile、batch及状态副本。原/派生输入preflight PASS，2040真实1h构建80104行/238529列/452584nnz、真实入口两行归档fixture PASS；计算节点Gurobi13.0.2许可/7回归/44线程参数/续接合同PASS。
  release=/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260919_base2040_v9_t44_m750_tol1e4_v1，output_8760；state=其下upstream_2030_bound_closed/planning_state_candidate。Git0a03cc452e95d158f36923ceb5210267979b6234+既有dirty，未提交。
  命令/源码与输入身份/状态调整SHA/原日志/验证/局限见supplementary_materials/reviews/base_2040_continuation_20260919/REVIEW_ZH.md。此授权覆盖旧“不得自动推进后续年”，仅2040，不改变科学接受标记；下一步只读构建/归档/Ordering/Barrier与资源，不自动2050/Stage B。未来需统一跨年微小floor清理的cohort记账。


> 2026-09-19 18:59北京时间终态：Base4614693于16:42:17结束，SlurmFAILED2:0但Gurobi OPTIMAL2/348轮/SolCount1，wall5天06:21、solver约5.224天。严格原始约束门禁及QC失败后完整保全退出；非NUMERIC/OOM/timeout。59项小时硬QC55过4败（功率平衡185.54kW、水库1.6018m3、跨省双向流、成本闭合73.83元），城市另619边反向流，对偶发布亦未过。保全COMPLETE；BarX/BarPi实际SHA/维度/有限值均PASS，原MPS存在，候选规划状态未接受。末轮原对偶相对差0.0073069%，队列现空。详见supplementary_materials/reviews/base_v9_terminal_20260919/REVIEW_ZH.md；只读，不自动重跑或Stage B。

> 2026-09-15 23:31历史原因澄清：重新读取原4139552云端日志，607轮OPTIMAL及终点目标接近属实；QC失败不能否定其已完成求解。4479238在NF2→1、年度行/8192、线程/容差及少量物理行修正组合下NUMERIC；没有单因素全年证据锁定唯一根因。不能把容差放宽或求解后QC检查说成已证实触发原因。原输入/规模统计相同也不等于LP逐项相同。详见supplementary_materials/reviews/base_regression_explanation_20260915/REVIEW_ZH.md；本轮只读，不改当前V9。

> 2026-09-15 23:25指数与部署独立复核：Base4614693仍RUNNING/iter98。203云端/198本地文件与冻结清单全部匹配，实际修正水库输入SHA一致，最终数值修复和48线程/1e-4/Cross0/NF2/无限时均应用。原矩阵[3.7e-5,5945.8478]，截图1.607e8是最大/最小之比的正指数；最小系数对应燃气CCS剩余排放，日志4.12e-8则是对偶残差。PInf470/Compl61.4仍未收敛；日志无独立presolved范围，不能据范围或小DInf宣称数值问题解决。仅只读采证，无作业变化；报告numeric_applied_verification_20260915/REVIEW_ZH.md。

> 2026-09-15 23:22部署审计：引用任务“诊断最新 base 数值错误”最终保留修复均已部署；203云端文件/198本地对应文件SHA与冻结清单一致，实际修正表及运行配置/参数一致。Base4614693最新iter98/PInf470/DInf4.12e-8/Compl61.4，仍RUNNING。38.9倍仅原始矩阵极值比，不能作性能倍数或数值健康证明；原168h的6250→168不能外推8760，全年资源年度系数仍约5946。原Cross2局部QC通过不能当作当前Cross0验收。细节见supplementary_materials/reviews/deployed_repair_audit_20260915/REVIEW_ZH.md；只读无作业变更。

> 2026-09-15 23:10三案例对照：旧Base4479238与Thermal4533060均NUMERIC12、无可用解，但尚未定位同一失败约束。当前Base4614693运行1天12:49/iter97，诊断相对目标差109.51%，尚未收敛。同iter97对偶残差/Compl较好，但相对Thermal的PInf仍较高。相对旧Base，raw nnz-1.73%、presolved nnz-2.85%/列+4.56%、Factor NZ-2.07%/Ops+0.27%；系数跨度改善约38.9倍，结构计算量没有大幅降低。共同50→97轮每轮新Base18.15分钟、旧Base20.69、Thermal17.16；模型/参数不同不能直接归因。峰值RSS678.11GiB、当前404.13GiB，内存峰值未降。纠正此前宽泛表述：早期DInf/目标差并非单调下降。报告及三日志SHA/解析证据见supplementary_materials/reviews/cloud_failure_comparison_20260915/REVIEW_ZH.md；只读、无作业改动，继续核验Base而不重提旧案例或给ETA。

> 2026-09-15 23:05终态更正：当前仅Base V9 job4614693运行；Thermal4533060已于9月14日21:08:54结束，Slurm FAILED2:0，根因Gurobi status12 NUMERIC。Thermal Barrier568轮/605210.75s，末轮P3.574e8、D-2.556e8、PInf3.37、DInf6.71e-5、Compl7.84；solution_count0、BarX/X不可读、QC未评估、保全PARTIAL、仅原模型归档完整，无结果或续接状态。峰值RSS637.3GiB，非OOM/时限/用户停止。Base运行约1天12小时42分，Barrier iter97，P4.212e8、D-4.430e9、PInf516、DInf2.06e-7、Compl65.3，持续改善但远未收敛；Factor NZ3.305e10、Gurobi估300GB，Slurm峰值RSS678.1GiB、当前404.1GiB，750G分配尚存约71.9GiB峰值余量，stderr空、节点MIXED。本轮只读，未改Base。

> 2026-09-14 16:12实时状态：Base4614693与Thermal4533060均RUNNING/UNLIMITED、stderr为空。Base Presolve在17124.39s结束，得到37,019,835行/33,634,377列/392,787,298非零，已进入Ordering约440s，尚无Barrier；峰值RSS约639.8GiB、当前约299.8GiB，750G分配尚未OOM但Factor峰值未知。Thermal最新iter550，P4.929e8、D-4.393e8、PInf4.62、DInf1.08e-4、Compl11.9；PInf/Compl继续改善，但DInf自iter547明显回升，仍未恢复或收敛。节点均MIXED且无重启标志。本轮只读，无作业改动。

> 2026-09-14 11:32实时状态：Base V9 job4614693与Thermal4533060均RUNNING。Base实际64CPU/750G/billing64、Gurobi48线程/1e-4/Cross0/NF2/无限时且无内存软限；WLS和7项启动回归PASS，已构建50,907,233行/41,458,383列/484,299,937非零的physical_v1/exponent0全年LP并归档4,048,048,342-byte MPS。当前Presolve约1420s，已去除13,366,655行/7,591,741列，尚未Ordering/Barrier，RSS约96GiB、stderr为空。Thermal运行约6天15小时，iter534，P6.226e8、D-6.777e8、PInf5.80、DInf4.58e-5、Compl16.7，仍恢复未收敛，峰值RSS637.3GiB。m4cm2204的REBOOT_REQUESTED已清除；仅slurmd于09:30重启，OS BootTime未变且作业Restarts0。未改动两作业。

> 2026-09-14 08:51 当前状态纠正：4613045已于05:05:59 FAILED1:0（39分41秒），原因是构建后的第二处旧8192校验遗漏，未进入优化，非NUMERIC/OOM/许可/时限问题。前次解除8192绑定不完整。本次统一前后校验，物理行exponent0、旧版仍exponent13，实际矩阵验证保留；45项测试PASS，新增真实runner两行矩阵归档路径回归。旧实际分配已证实64CPU/750G/billing64、UNLIMITED。新v3作业4614693已提交放行，当前PENDING；48线程/1e-4/Cross0/NF2/不限时等配置及输入不变，计算节点先跑入口7项回归。Thermal4533060未改动。详细更正、证据、源码SHA、命令及下一步见supplementary_materials/reviews/formal_launch_failure_20260914/REVIEW_ZH.md。


> 2026-09-14 08:36终态更正：当前仅Thermal4533060仍RUNNING，约6天12小时，最新Barrier iter524，P=7.62334426e8、D=-9.49331512e8、PInf7.06、DInf4.46e-5、Compl21.9；仍在恢复且未收敛，峰值RSS约637.3GiB，stderr为空。新Base V9 job4613045已于05:05:59 FAILED1:0，实际64CPU/750G/billing64、wall39:41、峰值约56--57GiB、无swap；计算节点许可和输入preflight通过，但在建完整LP/调用optimize前被`exact VRE/ROR annual capacity-link exponent 13 runtime evidence`接受guard阻断。无MPS、gurobi.log、Barrier、解或续接状态；不是OOM、许可证或NUMERIC。未自动重提或改动Thermal。节点m4cm2204仍MIXED+REBOOT_REQUESTED。

> 2026-09-14 02:14 当前执行状态更正：作者已授权正式不限时2030 Base。新作业4613045已放行，PENDING(Resources)，ReqTRES=64CPU/750G/billing64、Slurm UNLIMITED；Gurobi48线程、1e-4、Cross0/target1/NF2、无TimeLimit/SoftMemLimit，默认1000轮改为最大允许整数。768G超出节点RealMemory=768000MiB，实际改申请750GiB。实际分配与计算节点许可尚待启动脚本回读；不能据此宣称已进入Barrier或全年数值恢复。Thermal4533060保持RUNNING。源v9物理模型与数据修复不变；独立正式profile解除旧8192入口绑定。本地/云端输入PASS，66项必需身份一致，69+4项测试通过。202文件v2包SHA61c24b5283a20687e53b2b555f9cee39205bc6739252be412f37ea10662f2c2f，Git0a03cc4基准+dirty逐文件冻结。命令/新release/失败v1保留/验证/下一步详见 supplementary_materials/reviews/formal_launch_20260914/REVIEW_ZH.md。此条覆盖下方历史“仅诊断、未提交、待授权”。


> 2026-09-13 20:55只读核对：Thermal4533060仍RUNNING约6天，日志iter483原对偶目标仍相差很大，不支持9–10天必然收尾的预测。修复版与其核心算法主差异为NF2对NF1，1e-4/Cross0/44线程及64CPU/700G资源一致；模型处理仍不同。当前900s/2h包仅早期诊断，全年收敛资格仍未验证。本轮无求解、改参或服务器变更。详情solve_feasibility_vs_thermal_20260913/REVIEW_ZH.md。


> 2026-09-13 用户选定1e-4：当前诊断默认BarConvTol1e-4/Crossover0/SolutionTarget1/44线程，Slurm64CPU/700G/无软限；新包tolerance_1e4_readiness_20260913，未上传/提交。补齐不依赖SolCount的Barrier向量保存和各层QC独立导出，8测试通过。局部水量误差折算合计0.311MWh、跨省反向重叠1.572GWh/额外损耗37.115MWh，严格QC仍未过；高凤山源库容待核实，全国资格未知。900s是早期诊断预算，可能不覆盖历史4155.5s排序。详情同目录REVIEW_ZH.md。


> 2026-09-13 Crossover更正：原定Stage A/Thermal为0/1，入口已恢复Crossover0/SolutionTarget1；44线程/64CPU/700G/无软限不变。新24h无Cross、BarConvTol1e-6及1e-4均OPTIMAL但完整QC HARD_FAIL（水库平衡等），先前Cross2通过不能冒充原定方案资格。撤回上轮可启动结论；1e-6仅为未验收测试值，新包仅归档诊断用途，未上传/提交。下一步本地定位失败行，详见crossover_contract_20260913/REVIEW_ZH.md。


> 2026-09-13 默认资源纠正：下一阶段使用与Thermal相同的Slurm64CPU/700G、Gurobi44线程、无SoftMemLimit。前轮32线程/550GB包已被solver_alignment_thermal_20260913/cloud_gate_20260913_v9_t44_tol1e6.tar.gz替代。诊断BarConvTol=1e-6（同MPS24h配对QC通过，未证明更快），保留NF2/Crossover2及900s优化/2h总限；当前未上传或正式提交。详见同目录REVIEW_ZH.md及CODEX_HANDOFF当前快照。

> 2026-09-13 启动前复查：v9夏季24h冷启动25.740s/严格QC通过、5项启动入口测试通过、全年输入及服务器许可小测试通过。新197文件v9限时包已准备，尚未上传/正式提交；Thermal4533060仍运行且未修改。下一步为单次32线程/700GiB Slurm/550GB Gurobi/900s优化/2h总墙钟的真正8760诊断，不自动链式生产。详情numeric_prelaunch_20260913/REVIEW_ZH.md。

> 2026-09-13 19:26：新序列候选config/optimization_numeric_dac_by_year_v9.json已实现2030 DAC关闭、2040/2050/2060可选。73测试、2040一小时LP构建及四年份dry-run通过；未执行年度优化或服务器操作。v8历史包保留，后续序列应显式使用v9配置；不得因dry-run通过跳过全国8760资格。详情dac_year_schedule_20260913/REVIEW_ZH.md。

> 2026-09-13 double check最终状态：使用config/optimization_2030_numeric_final_v8.json；v7单位变更撤回，v3限时包被v8包替代。本地50测试、620×8760水力QC、冬季168h和夏季24h集成QC通过；全国8760完整LP未验收。本轮未连接/变更服务器，未上传或提交。详情numeric_doublecheck_20260913/REVIEW_ZH.md。

## 2026-09-13 最终v8本地交付与下一步

- Git基线0a03cc452e95d158f36923ceb5210267979b6234，未提交；修改清单、命令、输入哈希和数值范围见CODEX_HANDOFF.md当前快照及numeric_doublecheck_20260913/delivery_manifest.json。
- v8保留v2库容数据，增加1m3/s正弃水上界下限、CF=0.01、10kW微小容量阈值、1CNY/MWh省内正则、2030关闭DAC及beta<1e-4梯级毛刺清理。2030排放限制仍+4000Mt/年；不得把终期-550Mt套到2030。
- 168h最终LP与已冷求解v6字节相同（冷启动597.799s），v8重新基/物理QC通过；24h夏季(start3960)独立冷启动24.843s、QC通过。50项测试及全部620库8760水量重建通过，不能代替全国电力8760验收。
- 本地包numeric_doublecheck_20260913/cloud_gate_20260913_v8.tar.gz，196文件；SHAfe48ac2dd16866034ce9e8c7bb2ff79f24b21826da76da24d1d8a56e0b441e3d。原包与被否决的v7试验全部保留。
- 输入检查命令：python scripts/probe_full_year_numerics.py --config config/optimization_2030_numeric_final_v8.json --output-dir <NEW_DIR> --validate-inputs-only。此模式不构建LP；不得去掉开关后在本地32GiB机器强行构建全年。
- 预设的真正8760诊断仍为32线程/700GiB Slurm/550GB SoftMemLimit/900s求解/2h总限，新release和data_overlay，源数据只读。此前云端范围确认未收到，本轮只把本地包更新到最终v8，不重复发起确认或自行提交。
- 精确下一步：取得云端诊断范围确认后，重新验证服务器/源release环境，再将v8部署到新目录进行限时诊断，检查完整raw/presolve/因子与终态；不得自动链式生产，也不得把TIME_LIMIT或水力子模型通过登记为全国全年通过。下方服务器状态均为历史查询时刻，不代表本轮刷新。



## 2026-09-13 17:30 本地v3完成全年水力及168h压力检查；全国全年仍待验收

- config/optimization_2030_spill_tightened_v3.json新增孤立水库弃水上界收紧；482库、4,222,320界、1,321,812个新零界。源数据沿用v2，单位与发电可行域投影保留。
- 620库×8760h水力组件全部OPTIMAL，物理水量残差最大5.8850e-6m3；全国24/168h保留全年水库界的测试OPTIMAL/完整QC PASS。40项回归测试PASS。
- 全国8760LP未构建/求解；本地32GiB不足以做该验收。限时诊断包已本地准备，192文件哈希通过；计划32线程/700GiB、900s求解/2h总限，尚待云端范围确认，未提交。
- 本轮仅只读查询旧release路径及Thermal4533060（查询时RUNNING/5-20:58:02），没有上传、停止、重启或变更现有作业。
- 证据：supplementary_materials/reviews/numeric_resolution_20260913/。不能把全年水力子模型通过称为全国电力模型全年通过。

## 2026-09-13 水库专项审计完成；修正短窗资格解释

- 水库候选config/optimization_2030_storage_audited_v2.json、data/hydro/repaired_storage_audit_20260913_v2/，在v1上新增白竹洲、克孜尔有来源的库容纠错；三站/29列保留检查通过。
- 620库×8760h输入和旧4139552全年轨迹已本地审计；旧水量最大残差0.03899854m3，水量QC通过。73库共同估算模式、140库超过当前安全年入流水量；后者不能单独确认工程错误或9天NUMERIC唯一成因。
- v2 24h OPTIMAL/完整QC PASS/54.15s；但v1/v2 MPS完全相同，**没有证明库容纠错提高求解速度**。短窗库存界合计24h保留0.54%，全年58.1%，此前直接延长744h的资格解释被替代。
- 39项测试PASS；三处独立8760h水库诊断年度能量上限不变。全国8760 LP尚未构建/预处理/求解。
- 本轮仅SCP只读下载旧reservoir_dispatch.npz，未改变服务器任务/输入，未刷新Thermal运行状态；下方13:40状态只代表当时。
- 证据：supplementary_materials/reviews/reservoir_storage_audit_20260913/。下一步核实高优先级源参数，检查固定8760边界及全模型因子，不能凭短窗通过重启全年。

## 2026-09-13 13:59 本地修复候选通过24h/168h；服务器未部署

- 历史20天Base与失败Base原始数值范围相同；共同75项输入记录SHA相同。旧版Crossover同为0、严格QC曾HARD_FAIL。
- 本地候选config/optimization_2030_numeric_repaired.json已完成水库来源纠错、循环库存范围收紧、CF/流量毛刺清理；
  原表保留，新表data/hydro/repaired_20260913/，使用独立科学基准ID。
- 生产全年CF送出设计24h/168h：OPTIMAL，完整QC PASS，41.536/766.854s，原行最大误差1.7735e-11/8.8088e-7。
  39项单元检查和全8760水文数组审计PASS。早期600s TIME_LIMIT与其他不合格对照保留，未隐去。
- 当前配置8线程/8GB/900s为本地验证预算，不是全年服务器配置；新8760模型尚未build/presolve/solve。
- 本轮没有部署、提交、重启或停止任何云端作业。13:40只读：4479238 FAILED、4533060 RUNNING（5-17:30:45）。
- 详细证据、变更和未决项：supplementary_materials/reviews/numeric_repair_20260913/；Git0a03cc452e95d158f36923ceb5210267979b6234未提交。
- 下一步是固定候选的单一有限预算744h资格验证；当前本地通过不能视为全年资格通过。

## 2026-09-13 Base数值失败终态；无可续接解

- 2026-09-13 Base job4479238终态复核：07:16:40结束，9天13小时52分36秒，Slurm FAILED2:0；
  Gurobi13.0.2 Barrier654轮/status12 NUMERIC，solution_count0、X/BarX不可读；QC NOT_EVALUATED、
  preservation PARTIAL、INCOMPLETE_NO_USABLE_STAGEA。峰值480.48GiB，不支持OOM/超时归因。
  原MPS4142715779 bytes保留（本轮仅stat、未重新下载或验证全部内容），无向量可续接，不能从iter654原地恢复。
  655条日志复算PASS；按项目abs(P-D)/max(1,abs(P),abs(D))诊断式，最小目标差99.6060%，门槛1%；
  iter633→634 Compl6.75e-6→0.0631，恶化9348倍。纠正旧线程仅按残差下降给出的1–2天ETA，不能宣称接近最优。
  系数跨度6.247e9及历史水库大库存/小通量是风险证据，尚未定位本轮唯一病态约束，也未证明不可行。
  Thermal4533060本轮仍RUNNING，最新读取iter454；旧总结iter366 Compl0.292纠正为0.257，随后跃升8.24e11。
  证据/报告/不求解解析器：supplementary_materials/reviews/base_numeric_failure_20260913/；SSH/SCP只读取证。
  Git0a03cc452e95d158f36923ceb5210267979b6234，未提交；仅新增该报告目录并更新三份交接文档，保留原dirty文件。
  未改模型/输入/配置/服务器，无新求解/重启/Stage B/停止Thermal。下一步离线定位尺度来源与等价修复方案；
  新实验需形成有限预算配对门禁，不盲目重跑全年；后续监测同时核对目标差、残差、异常与解可读性。


## 2026-09-07 正式冷热job4533060已提交，无限时

- 2026-09-07 已提交并放行正式冷热作业 **4533060**，观测状态RUNNING，Slurm TimeLimit=UNLIMITED。
  作者明确授权2030年Base＋冷热、44线程及取消所有正式时间限制；未提交EV/联合/下一年/Stage B。
  部署Git `ffd651aded605568bc1e02cc460eae5ecd113b5b`；release=`20260907_thermal_stagea_1e4_t44_ffd651a_v2`。
  case=`2030_case1_thermal_v5_8760_rows8192_t44_m700_tol1e4_ffd651a_v2`；原Base4479238保持运行，未停止或改参。
  307源码文件SHA与V5五文件SHA通过，云Gurobi13.0.2，BarConvTol1e-4，Threads44，Gurobi无TimeLimit/SoftMemLimit，无定时STOP。
  请求TRES cpu64/mem700G/node1/billing64核验通过；held提交后已scontrol release，勿重复提交。
  首次4533016因部署git_commit.txt的CRLF在启动器Git校验处1秒失败，未建模/优化；保留v1，在v2以LF修正后重提。
  20:12:38快照已在m4cm2204运行2:26，实际cpu64/mem700G/billing64；preflight PASS、两份stderr为0，正在建模，尚无MPS/Barrier结果。
  只读状态/提交证据：supplementary_materials/reviews/thermal_launch_20260907/evidence/及output/thermal_launch_20260907/。
  下一步仅跟进该作业分配、preflight、原始模型归档和Barrier启动；保留QC/完整保全，禁止自动停止或启动其他情景。

## 2026-09-07 授权正式冷热案例、无限时启动准备

- 2026-09-07 作者正式授权启动2030 Base＋冷热44线程，并明确取消正式案例的一切时间上限。
  此条覆盖此前仅对该案例的禁止启动/4h测试限制；其他情景、年份和自动Stage B仍未授权。
  BarConvTol落实1e-4；既定A8 64 CPU/700G/billing64，Gurobi Threads44；Slurm无限时、Gurobi无TimeLimit/SoftMemLimit，无定时STOP。
  新显式--authorize-thermal-stage-a-1e4严格限定case1/2030/44/1e-4；QC、保全、跨年接受和未压缩库存链保护不变。
  4项范围测试＋30项不求解回归PASS；31省8760h真实输入在授权路线下建模前PASS，不代表全年数值合格。
  计划独立冻结release和新输出目录；原Base4479238继续运行，不干预。正式提交前核验SHA、版本、预算、billing和preflight。
  详细合同config/THERMAL_STAGE_A_LAUNCH_20260907.md；准备证据output/thermal_launch_20260907/。
  当前里程碑为启动准备，尚无新作业号；准确提交状态由后续追加条目覆盖。

## 2026-09-07 最终自检：参数冻结，异常结果保全，未启动优化

- 2026-09-07 正式运行前最终自检：作者冻结Base＋原三个V5情景，不继续扩模块，仍禁止自行优化。
  实现Git `ba57c79c3cedd3f70b2516cc76ffb29532bf7a5d`；本地修改，未部署，未启动优化/presolve/松弛/Stage B/云作业。
  修复异常跳过保全、损坏QC阻断导出、停止阶段竞态和wrapper恢复状态误判；归档不完整禁止开始求解。
  新显式--allow-recovery-barrier-checkpoint支持未接受checkpoint/raw snapshot同年同LP恢复准备，
  不改变默认科学接受/跨年门槛。Barrier内部迭代不能热续接；无可读有限向量或强杀只能依靠已落盘原模型重建。
  30项禁止求解回归PASS，原三情景参数文件与2省24h矩阵/边界/目标SHA不变；真实V5五文件SHA全部通过。
  31省2030全年输入负荷组件闭合误差1.14e-13GW、EV参考服务8.88e-16GWh；其余年份仅文件覆盖核验。
  Base核心SHA/科学配置一致；17:40前后只读job4479238为RUNNING 4-00:16:14，非此刻状态保证。
  纠正“仍沿用Base宽松”：Base BarConvTol=.01/Threads32，portfolio现有为1e-9/44；其余数值配置一致。
  代入Base宽松参数的8760h建模前检查：EV PASS、冷热与联合BLOCKED；不能把结构PASS当全年求解合格。
  profile/QC/启动保护未改；portfolio现有wrapper仍是2030、≤4h测试入口，非已授权十天正式作业。
  详见supplementary_materials/reviews/portfolio_finalcheck_20260907/REVIEW_CN.md和evidence。
  确切下一步：冻结当前研究参数，待作者明确正式数值配置与启动授权后准备独立release/调度；不得自动绕过资格或覆盖Base。

## 2026-09-06 V5启动前覆盖：本轮禁止优化，资格仍未闭合

- 2026-09-06 V5正式启动前不求解审查覆盖：作者继续要求暂不启动优化。核心修复提交
  `b225ab522a3bd7a38ea5ef1318beb4c161cdd8db`，无优化/presolve/松弛、新云作业或Base干预。
  24项不求解回归PASS；修复压缩冷热状态离线向量映射、无限边界严格JSON、情景ID/配置SHA与科学接受
  续接检查、EV字段单位/维度与V2G同池对流统计。未改物理方程、参数或签约上限。未资格portfolio
  profile及其他profile下8760h入口已本地拦截，preflight/build-only/离线恢复保留；旧云release未覆盖。
  T32冻结供给核心源码SHA与本地一致，解析Base科学配置零差异；76项共同输入74项SHA一致，两项验证
  sidecar差异已解释为JSON格式与数据包清单范围。23:44快照job4479238仍RUNNING，非当前状态保证。
  旧case3全国24h保存向量在新代码中精确LP身份/顺序校验通过、离线容量成本运行导出完成；415条超限
  行均为水库，最大0.0426517793 million m3，整体HARD_FAIL保留，柔性增量最大8.88e-16。
  进一步离线定位为独立子集348→全表475、hour16、HydroCHN_01147；24h来水9776m3、库存约14.8亿m3，
  水量误差42652m3。不能据此放宽容差或擅自固定初始库存，等价坐标处理仅为待验证候选。
  详情：`supplementary_materials/reviews/portfolio_prelaunch_20260905/REVIEW_CN.md`及evidence。
  下一步仅离线审查水库大库存/小通量的等价处理；重新求解需作者解除当前禁令，正式全年资格仍未闭合。

## 2026-09-05 15:51+0800 V5三情景仅代码部署，零新增云端作业

- 2026-09-05 15:51+0800 V5三情景里程碑：作者明确case1=Base+冷热、case2=Base+EV、case3=Base+冷热+EV。
  实现提交`87b534f2cf1f24b9a2bbe084b85f7adc2066f976`（父`860ab84`）新增可选签约/两EV服务池/冷热共享功率，
  保留原始负荷、旧V5及Base供给侧。主比较显式沿用Base峰值容量约束，不给未经事件验证的静态firm credit。
  127项本地回归PASS；三组全国24h basic求解/QC/导出/manifest均PASS；31省8760h独立服务块三组PASS，联合
  2,303,225变量/3,310,291行（含62条诊断份额固定行），最大物理残差1.99e-11。不能当全国全年规划验证。
  无Crossover的全国24h Base/联合均暴露水库行残差；BarHomogeneous1、NumericFocus3、Aggregate0对照仍未通过
  原单位QC。候选全年profile虽已独立注册，正式无Crossover数值资格仍NOT_QUALIFIED，禁止误报可直接正式投产。
  云端仅部署新不可变release`20260905_v5_portfolios_87b534f_v1`，282文件校验、三配置/预算guard/语法检查PASS，
  三个小时V5输入SHA与本地一致；本轮零云端作业，wrapper强制Slurm总wall<=4h（含build/archive）。原T32
  `4479238`继续RUNNING；T44作者在另一任务受控停止，按现有15:23交接保留，未由本轮干预。
  详情及证据：`supplementary_materials/reviews/portfolio_20260905/REVIEW_CN.md`、`delivery_manifest.json`。
  下一步：从本地失败原模型定位水库尺度/近零边界/周期行依赖，做数学等价数值处理门禁；不热改Base，不启动
  新云端全年任务、不自动Stage B，不因部署完成而宣称全年可解性成立。

## 2026-09-05 15:23：Threads44按作者指令受控停止，Threads32继续

- 仅对exact job`4496031`创建`STOP_REQUESTED`，未调用`scancel`。Gurobi在Barrier iter40后status11
  `INTERRUPTED`；Slurm于15:22:53终态`FAILED 2:0`，这是未接受中断解的fail-closed包装器返回，不是OOM。
  elapsed`17:59:20`，batch MaxRSS`658673148K`（628.16GiB），双stderr为0。
- 约5.1G/67文件、原MPS、BarX/BarPi与完整保全输出已落盘；preservation六阶段COMPLETE、errors空。但QC
  HARD_FAIL、checkpoint recovery-only、terminal无可用Stage A，只能用于恢复取证/性能证据。
- job`4479238`保持RUNNING，已到iter116（solver`162003 s`），未改参或创建STOP。作者明确未来A8默认仍为
  `64 CPU/700G + Gurobi Threads44`；此次主动停止不触发默认失效，未来不间断任务仍须通过终态/QC。机器
  合同修正提交为`860ab8424697dfc977e2f086fade4a2c6098e524`，已推送origin/GitHub。

## 2026-09-05 15:09：Threads44记录为未来A8默认

- 作者选择`amd_a8_768 + Slurm 64 CPU/700G + Gurobi Threads44 + automatic Ordering + no SoftMemLimit/time
  limit`为未来全年Stage A默认；机器可读合同为`config/cloud_resource_profiles/a8_8760_stagea_default_v1.json`
  （commit`779dc17`）。未来仍须逐作业核验实际billing64。
- T44 job`4496031`正常至iter39，solver`59834 s`，比T32同iter39的`66750 s`快10.36%；峰值RSS保持
  628.16GiB。T32 job`4479238`正常至iter115。两者双stderr0、无STOP、未被本次记录修改。
- 默认的终态/QC仍pending；若T44自然OOM或验收失败，必须触发重审，不能隐去，v7 Threads32为fallback。

## 2026-09-05 07:12：审查期间只读快照

- `4479238`与`4496031`仍RUNNING，分别iter92/12，对应solver runtime132565/31905s；Slurm峰值RSS约
  480.48/628.16GiB。仍未科学验收；本轮未发信号、改参数、附加计算step或启动任何云端任务。
- 两release的`monolithic.py`、`flexible_load.py`与本地HEAD源码hash一致。详细只读证据及Base/V5审查见
  `supplementary_materials/reviews/review_20260905/REVIEW_CN.md`和同目录`server_readonly_snapshot.txt`。
- 待运行V5不能直接复用当前Base profile：真实本地全年冷热数据触发现有长链guard，且final profiles冻结
  Base原LP身份。报告中的新技术/事件验证建议未实施，不改变下方作业运行边界。

## 2026-09-05 06:55：Threads44已进入Barrier

- job`4496031`正常RUNNING至iter11，Presolve`17453.62 s`、Ordering`4155.50 s`，Factor NZ/Ops
  `3.374e10/1.881e15`；双stderr0、STOP不存在。
- 44线程稳定步时约1029s，较32线程约1234s缩短16.6%；但Ordering慢19.3%，到近似收敛态的累计solver时间
  目前仅快约7.2%。
- T44当前/峰值RSS约396.77/628.16GiB，较T32峰值480.48GiB高147.68GiB，700G边界仍紧。T32 job
  `4479238`正常至iter91；两作业均billing64且不得主动停止。

## 2026-09-04 21:25：A8 Threads44/700G已启动

- 实现`40214fb`只新增v10 Threads44 canonical profile及守卫；相对正式v7仅改变线程数，不改模型、数据、
  Presolve/Ordering、容差、保存/QC或Stage B边界。没有SoftMemLimit或时限。
- release计算节点smoke`4496030`为`COMPLETED 0:0`；job`4496031`在`m4cg1705`正常RUNNING，实际
  `64 CPU/700G/billing64`、cpuset`0-63`、Gurobi Threads44，preflight PASS（67/3/2/0）、双stderr0。
- Threads32 `4479238`继续RUNNING且未受影响。不得主动停止；只读等待44线程的原MPS身份、Presolve、Ordering
  和Barrier证据。历史Ordering候选未证明综合收益，本轮保持自动ordering以保证单因素可比。

## 2026-09-04 20:49：A8 Threads54/700G在Ordering OOM

- job`4488786`在Presolve`17590.56 s`后进入Ordering，心跳到385s时被700G cgroup硬杀；Slurm终态
  `OUT_OF_MEMORY 0:125`，batch MaxRSS约593.97GiB。相较Threads64峰值约677.30GiB有所下降，但仍未存活。
- 原MPS/PRM与冻结LP identity PASS保留；terminal=`INCOMPLETE_NO_USABLE_STAGEA`、rc137，无BarX/BarPi、
  solve report或可用checkpoint。不得作为正式结果或续接来源。
- 当前仅A8 Threads32 `4479238`继续RUNNING，Barrier iter62，当前/峰值RSS约383.34/480.48GiB，双stderr 0。

## 2026-09-04 17:53：M9作业4990379已受控停止

- 按作者明确指令，只在M9 exact case control目录创建`STOP_REQUESTED`，未调用`scancel`。wrapper于
  17:45:30转发SIGTERM，Gurobi于17:46:58在Barrier iter54后以status11 `INTERRUPTED`返回；Slurm最终
  `FAILED 2:0`是受控停止wrapper的预期终态，不是OOM。
- 保全已COMPLETE且errors空：原MPS/LP身份、BarX 331,667,192 bytes、BarPi 407,258,000 bytes、结果目录
  约5.1G均保存，双stderr为0。但QC=`HARD_FAIL`、checkpoint=
  `RECOVERY_ONLY_UNACCEPTED_SOLVER_RESULT`、terminal=`INCOMPLETE_NO_USABLE_STAGEA`，不得当正式解或续接输入。
- M9作业已退出队列；A8 `4479238`与`4488786`继续RUNNING且未受影响。下一步只读监测A8，不恢复M9。

## 2026-09-04 11:17：新License ID 2845749认证失败

- 官方`grbgetkey`13.0.2明确返回`ERROR 203: License 2845749 is inactive`、exit1；未下载或安装新许可。
- 原`/home/zz2/gurobi.lic`保持License ID`2840423`及原SHA256、owner`zz2`、mode600，未被覆盖；临时备份
  核对一致后已删除。
- 固定服务器许可证门禁继续FAIL，不得启动新求解。需要先在Gurobi门户/官方支持侧恢复2845749为active，
  或提供另一有效许可，再重新认证并运行最小LP。

## 2026-09-04 11:07：许可证撤销通知后的双端实测

- 当前Windows设备可正常签出许可证并求解：Gurobi13.0.2 CLI和`RL`环境gurobipy12.0.1均完成一变量
  LP，status2 `OPTIMAL`、objective=1。活动NODE License ID为`2808889`，到期`2027-04-21`。
- 固定服务器SSH、Python3.11.15及gurobipy13.0.2可用，但`gp.Env()`等待150秒仍无法取得许可证；测试已由
  timeout终止且无遗留进程。服务器文件的非秘密元数据为NODE License ID`2840423`、到期
  `2027-07-02`，但文件存在/未到期不等于许可证当前可签出。
- 当前固定服务器许可证门禁为FAIL：不得启动新的正式模型。此现象与撤销通知一致，但尚不能在没有官方
  返回或网络诊断的情况下排除验证服务阻塞。KEY/CKEY及许可证正文不得披露。

## 2026-09-03 15:47：最终v7无SoftMemLimit唯一作业4478922运行中

- 不可变tip`2820fc35f3e9005ce0bf771b0b94444ca1dc85d8`已双推送；release为
  `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260903_8760_stagea_final_2820fc3_v3`。smoke
  `4478920=COMPLETED 0:0`，Gurobi13.0.2/WLS/v7 canonical与`soft_mem_limit_gb=null`通过。
- 唯一正式作业`4478922`于15:44在`m4cg1605`运行：`94 CPU/550G/billing94`、Gurobi Threads32、Slurm与
  Gurobi无时限、无SoftMemLimit、preflight PASS、双stderr 0，当前build。v7保留原模型/验收边界；500GiB
  启动门槛只作用于v7，运行中不按内存阈值自停，550G Slurm硬上限仍可能触发系统OOM。
- 原MPS/PRM在optimize前归档；求解返回后先原子保存完整BarX/BarPi，再做原单位QC并晋级正式候选。
  `4478232`按作者要求在solver前停止，terminal=`INCOMPLETE_NO_USABLE_STAGEA`。下一步只读等待
  `final_stage_a_lp_identity.json=PASS`与`solver_start`；不启动第二作业或Stage B。

## 2026-09-03 15:12：最终v6唯一作业4478232运行中

- 最终不可变tip为`7be4d21e6b79bb243a94072120dd850caad2f5db`，已双推送；云release为
  `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260903_8760_stagea_final_7be4d21_v2`。smoke
  `4478205`为`COMPLETED 0:0`，Gurobi13.0.2/WLS/v6 canonical PASS、stderr 0。
- 唯一正式作业`4478232`于15:11在`m4cg1701`运行：`120 CPU/700G/billing120`、Gurobi Threads32、
  Slurm/Gurobi均无时限、preflight PASS。cgroup raw unlimited哨兵与Slurm申请取小后effective limit为
  `751619276800 bytes`，SoftMemLimit=`638.876385280 decimal GB`；当前双stderr 0，处于build。
- 初次`4478059`因旧wrapper误把cgroup v1 unlimited哨兵当真实上限，已在无solver/无解时于2分39秒止损；
  terminal=`INCOMPLETE_NO_USABLE_STAGEA`。v1根保留。`4478232`将于optimize前自动校验精确raw维度、
  Fingerprint和解压MPS SHA；只读等待，不启动第二作业或Stage B。

## 2026-09-03 14:53：最终单路32线程v6已本地闭合，尚未部署

- 实现提交`af96fb6361af4bb09dd90513c48ad76796f30a7d`固定唯一v6：`BarConvTol=1e-2`、
  `FeasibilityTol=OptimalityTol=1e-6`、`Method2/Threads32/Presolve2/Aggregate1/Crossover0/
  SolutionTarget1/NumericFocus1/ScaleFlag2`、无时限、无自动Stage B。模型边界、行缩放和精确零上界未改。
- primal终解按固定1% gap/primal infeasibility、`1e-5` solver primal质量和全部原单位物理QC验收；dual质量
  只控制影子价格发表。BarX/BarPi先原子落盘，QC/打包失败降为保全待复核；v6 accepted/candidate state保留
  所有有限容量增量。wrapper从Slurm cgroup计算SoftMemLimit并始终生成三态terminal JSON。
- 本地完整回归`310/310 OK`（1 skipped），focused 60项、编译、diff、bash及heredoc解析全部通过。
  14:50固定服务器无CISPO/Gurobi，ParaCloud队列为空；旧`4466067/4466068`保持终态。v6当前未推送、部署、
  构建或启动；下一步仅按新不可变release做Gurobi13/WLS与精确LP身份门禁，再提交唯一32线程作业。

## 2026-09-03 01:29：严格容差线程对照已在Presolve受控停止，等待0.01新profile

- 作业`4466067/4466068`已通过精确`STOP_REQUESTED`受控终止，未用`scancel`；两者均停在Barrier 0步，
  Presolve分别为`4003.76 s/work 24406.37`和`4018.41 s/work 24626.23`。Slurm的`FAILED/2`是无解受控中断
  的runner语义，不是崩溃；双stderr为空，MaxRSS均约97.05 GiB。
- 实际模型同为`50,907,234 rows / 41,458,383 columns / 492,835,195 nonzeros`、Fingerprint
  `0x94cf2e50`；解压MPS流SHA256同为`8216816027025ffc16eb7fb80ce55d6beb822242f03f1a24433102248603713a`。
  original MPS/PRM及build/solve/QC/preservation清单已保全；Barrier尚未开始，故没有可用BarX/BarPi。
- 本次停因是作者否决`BarConvTol=1e-9`导致的潜在超级长尾。下一轮必须恢复`BarConvTol=1e-2`，并把算法
  停止精度与原单位科学QC分开；不能用`1e-9`作为科学性的同义词。当前无活动8760h作业，不自动Stage B。
- 年度VRE/ROR行缩放显著缓和目标行的局部系数，但只影响39,318个非零项（全模型约0.00798%），全局
  Matrix/Objective/Bounds/RHS范围及分解维度未收窄。旧16线程日志显示`1e-2`四项打印指标代理首次同时
  达标约在15.71天，而严格终点20.53天；因此预期低于旧20天，但不能仅据此承诺短于约两周。

## 2026-09-02 23:26：8760h Threads32/64正式科学对照已同步运行（已被上方终态覆盖）

- 云发布根为`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/
  20260902_8760_threads32_64_a142ab5_v1`，不可变代码`a142ab502b5af68e70b088bd5c93bd800083f708`。
  `4466067`在`m4cg1602`运行，`89 CPU/520G/billing=89`、Gurobi Threads32；`4466068`在`m4cm1804`
  同秒运行，`120 CPU/700G/billing=120`、Gurobi Threads64。两者Slurm/Gurobi均无时间上限。
- 两者均为Base2030/8760h、完整原模型、内部Presolve2、Method2/Crossover0/SolutionTarget1、严格
  `1e-9/1e-9/1e-8`容差与KKT/gap门禁、`annual_capacity_link_rows_8192_v1`。preflight双PASS，估计规模
  同为`41,186,823/55,928,698/497,144,574`；去solver-profile行的input manifest SHA256相同。
- 每条在optimize前归档original MPS/PRM，终止后保存能取得的BarX/BarPi及preservation证据；严格通过才
  生成accepted checkpoint、QC、result manifest和planning state。计划内停止用`STOP_REQUESTED`，禁止
  `scancel`截断保全。每4小时heartbeat只读监测，不自动停止、Stage B或任何后续测试。

## 2026-09-02 22:40：三项必要修复本地闭合，云任务尚未启动

- 水库精确零、nonbasic `ConstrResidual/DualResidual/ComplVio/relative gap`硬门禁、physical LP机器可读
  差异白名单已实现；完整本地回归`304/304 OK`（1项跳过），24h physical/scaled双`OPTIMAL`、同目标、
  原单位QC双PASS。相对`b0b8b3a`的24h physical MPS只有5232个经逐水量平衡证明的`1e-12 -> 0`水库
  release上界变化，矩阵/RHS/目标/下界/senses/identity均不变。
- 修复提交`cff905476ed2811a26b16e86f772eb5b91f9357d`已双推送但尚未部署到固定服务器生产checkout或
  ParaCloud；当前没有由本里程碑启动的计费作业。作者提供的云计费规则已
  记录为“申请CPU与内存折算CPU取大者”（例120G即使1线程仍可能按12核计费），提交前仍须以当前分区
  TRES/billing实测复核。
- 单独`Model.presolve()`生成的reduced MPS只能用于诊断，不含uncrush映射，不能作为正式科学求解的
  可续算状态。后续低价准备档可归档原始MPS并校准presolve峰值；正式32/64核对照均须从同一原始MPS、
  内部Presolve=2开始。Stage B不自动执行。

## 2026-09-02 21:08：2160h行缩放资格运行因冻结内存门禁终止

- tag `2030_base_2160h_stagea_capacity_link_rows8192_barrier32_20260902_v1`已为终态
  `FAIL_TERMINATED`；tmux、runner、guard和solver均已退出，未自动重启，也未启动Stage B。
- raw结构精确匹配；presolved为`9,527,358 rows / 8,288,888 columns / 106,864,011 nnz`，其中NNZ通过
  `107,398,350`上限，且无数值警告。但任务只走到ordering约230s，未生成Factor类指标或任何Barrier
  iteration，因此没有iter30速度证据。
- 进程组RSS先越过75GiB资格上限，最终记录`86.382GiB`；整机used达到`99.008%`、available约1.31GB，
  guard发出终止信号。故这是明确的资源/资格门禁失败，不是求解器数值失败，也不能据此评价缩放加速。
- 21:08生产checkout仍detached、clean`ba8e09f`；内存释放后available约94.45GB，实时swap si/so0/0、
  PSI avg10=0。证据见`downloads/stagea_rowscale_2160_fail_memory_20260902_v1`。当前对话已建立每3小时
  heartbeat `3-stage-a`；本机不得换标签原样重跑，后续必须先补齐审计门禁，再从有安全内存余量的较小
  时间窗做单任务验证并按实测峰值逐级扩大。

## 2026-09-02 current override：唯一Stage A行缩放路线，2160h首轮已终止

- 作者已确认唯一继续路线：只对VRE/ROR年度可用量零右端行做
  `annual_capacity_link_rows_8192_v1`精确整行左缩放。族尺度为`s=2^-k`，`k`取不超过13且使缩放后
  最小非零系数仍`>=1e-6`的最大整数；正式2160h/8760h要求VRE/ROR均`k=13`，否则fail closed。
  Wave与省内负荷中心容量行明确排除。变量/目标/边界/支撑/可行域不变；原单位映射为
  `pi_physical=s*pi_solver`、`slack_physical=slack_solver/s`、reduced cost不变。
- 8760h Stage A使用`barrier_checkpoint_full_year_cloud_v4`、`Method=2`、`Threads=32`、`Presolve=2`、
  `Crossover=0`、严格全年容差和`soft_mem_limit_gb=600`；32线程是作者基于既有全年运行作出的选择，
  不以短时域线程测试否决。
  Stage B不是必需步骤，任何launcher/watcher/sequence均不得自动启动；只有作者以后单独授权时才讨论。
- 实现提交`122642f616b7abb2ad137250721a937e83a6f524`及Linux实时swap采样修正
  `ba8e09f97a6526e299f807eb9be8c579a217caeb`已推送并部署。完整本地回归为`290 passed, 1 skipped`；
  服务器精确提交回归`256/256`通过。24h/start2880物理原式和缩放式
  均status2 `OPTIMAL`，目标均`2112716.676624984 million CNY`且原单位QC均`PASS`。这只证明等价性和
  接口正确，不是2160h/8760h速度证据。
- 唯一正确生产checkout是`/home/zz2/National_model_server/repo`，当前核实为detached、clean`ba8e09f`；
  `/data/zz2/National_model/repo`是旧NTFS克隆，禁止部署或启动。本任务为落实作者
  “Stage B非必需、优先解决Stage A”的新决定，已**有意停止**旧Stage B进程组及Case2 watcher；这是
  对下一节18:04在当时信息不足下保留“外部SIGTERM未解析”的后续纠正，历史记录本身保持不变。
- detached `tmux`跨SSH持久性已通过：同PID/start time/cgroup存活，6个heartbeat后自然rc0。真实launcher
  假进程集成已通过normal`0`、guard早退`96`、重复信号`129`、flock拒绝`90`、guard超时`97`且无孤儿。
  探针发现并修正`vmstat`首个since-boot数据行误判；当前只审查之后三个实时`si/so`区间。
- 20:04:49可用内存自然升到`100.304 GiB`，20:05:24启动唯一tag
  `2030_base_2160h_stagea_capacity_link_rows8192_barrier32_20260902_v1`；tmux
  `cispo_stagea_rowscale_2160_v1`、runner PID`384500`、guard PID`384507`。实际CPU affinity为`0-31`，
  32个唯一物理核、NUMA0/1各16核，启动时`MemAvailable=100.292 GiB`。该任务使用
  `host_memory_soft_limit_fraction=0.95`并保留整机95%保护；profile中的`soft_mem_limit_gb=80`仅为
  fallback/provenance，runner必须将有效Gurobi `SoftMemLimit`覆盖为物理内存95%对应的十进制GB。
  raw结构必须精确为
  `12,520,914 rows / 10,398,783 vars / 126,724,678 nnz`；presolved nnz`<=107,398,350`、
  DenseCols`<=38,982`、`AA' NZ<=2.17035e8`、Factor NZ`<=6.28845e9`、Factor Ops`<=2.19345e14`、
  factor memory`<=63 GB`且无数值警告。首个`iteration>=30`记录须满足runtime`<=12,000 s`、
  Work`<=18,961.075`、进程组RSS`<=75 GiB`。该任务21:04在ordering阶段因内存保护终止；没有结构分解或
  iter30结论，不得宣称加速或启动8760h。GPTPro复核要求补齐精确零水库上界、KKT/relative gap硬门禁和
  parent→new physical LP差异白名单，并增加同提交、同32核的physical对照。每3小时heartbeat只推进这条
  路线：先修复和小窗验证，再依据峰值内存按`1488h -> 2160h -> 4320h -> 5880h`逐级单任务扩大；明确
  不执行Stage B，也不自动启动云端8760h。

## 2026-09-02 18:04 Case1 Stage B被SIGTERM中断，Case2未启动

- Stage B于17:41:39返回143；Gurobi `INTERRUPTED`/status11/SolCount0。运行92699.686s、
  8366337 simplex iterations，最后剩1262112 PPushes/PInf1265.5003；无objective/QC/manifest。
- host95保护未触发，非OOM：RSS峰26.954GiB（runner）/28.908GB（2s sampled），host used峰
  77.64%、最低available29.55GB，46818样本/errors0，双stderr空。
- 同秒有SSH session断开记录，但缺少信号发送审计，原因只能标记为外部SIGTERM未解析；不得写成
  算法自然失败或作者主动停止。
- Case2 watcher已退出，最后status仍`WAITING_STAGE_B`；无claim/output/process。Stage B未通过
  rc0+QC+manifest门禁，禁止人工启动Case2或重启Stage B。等待作者决定。

## 2026-09-02 09:59 744h完整Stage A已终态，CF 1e-4未在该尺度晋级

- baseline/candidate均runner rc0、Gurobi `OPTIMAL`并形成完整engineering Barrier checkpoint，
  但Crossover0宽松解均`HARD_FAIL`且原始QC失败，不是科学可用结果。
- 候选相对基线：Barrier 120→134步、solver 2995.079→3070.307s、work units
  2842.982→3006.566、端到端3380.386→3478.729s、process-tree峰20.049→20.402GiB；
  raw NNZ仅减少20976。目标变化371.039 million CNY，因为阈值改变可行域。
- 结论：五步Factor Ops信号未转化为744h完整Stage A收益；`coefficient_zero_tolerance=1e-4`
  不凭该证据晋级744h Stage B或修改生产默认。744h不证明2160h/8760h必慢，后续只可在当前
  Case1/Case2结束后按统一工程线做隔离2160h结构/有限Barrier筛选，不能直接启动8760h。
  证据在`downloads/cf_744_stagea_pair_terminal_20260902_v1`；统一工程分支为
  `codex/numerical-stability-engineering-v2`提交`7fce1ca4`。
- Case1 Stage B同PGID3946395/Python3946400仍在exact-resume Crossover PPushes；09:59剩约
  2.418M、PInf1633.873、solver约64942s，无return code/QC/manifest。当前Python RSS约24.1GiB，
  host used78/123GiB、available44GiB、PSI0，Stage B没有停滞或OOM。
- Case2 watcher881511仍`WAITING_STAGE_B`；只有Stage B rc0+QC PASS+manifest完整、无竞争求解且
  available>=96GiB才启动Threads32 Case2。当前可用内存不足以再启动一对744h，GPU0/1还有
  未归属本任务的计算客户，不触碰。4小时轮询继续。

## 2026-09-01 21:44 两条744h完整Stage A已并发启动

- 五步筛选后，按作者既有授权将1e-4候选晋级为完整744h Stage A匹配A/B；21:44:26启动基线
  PGID1045145与候选PGID1045150，均744h/start2880、Barrier16/Crossover0、BarConvTol1e-2、
  无TimeLimit/SoftMemLimit，唯一差异为CF阈值。两条使用engineering checkpoint模式。
- pair supervisor1045122；分别绑定两个NUMA节点各16CPU。已改用存在且验证过的monitor绝对路径，
  两个2秒遥测进程均存活；pair95%保护保留。启动时available约87GiB、PSI0，Stage B继续PPushes。
- Case2 watcher不会与两条Stage A争用；Stage B若先结束则等待pair释放和available>=96GiB后立即启动。
- 隔离launcher/worklog提交`ba89225a23375f2bc400d510b62f6e1865412239`；生产repo仍clean6065bfb。

## 2026-09-01 21:41 744h因子筛选完成，Stage B从DPush转入PPush

- 两条744h均完成预设5步并返回Gurobi status7/runner rc2，无解/QC是因子诊断的预期终态；pair
  21:18结束且95%保护未触发。候选1e-4相对基线1e-6将Factor NZ降低2.24%、Factor Ops降低6.14%、
  ordering 135.34→117.64s、并发solver 562.91→522.94s；raw/presolved NNZ仅降0.0477%/0.0439%。
  判定`PROMISING_MODEST`，不能据并发5步结果宣称正式加速或直接修改生产阈值。
- per-case telemetry因生产repo缺少`monitor_case_resources.py`失败；pair TSV、runner RSS、solver telemetry
  和time.txt完整。缺失独立资源字段不记为0；不为此重复运行已经完成的筛选。
- Stage B同一PGID3946395于21:41从DPushes转为6755240 PPushes/PInf3224.99，尚无return code、
  solve report、QC或manifest。采样10808/errors0、job RSS峰28.908GB、host峰54.924%；当前available
  约87GiB、PSI0。Case2 watcher仍`WAITING_STAGE_B`，未启动Case2。

## 2026-09-01 21:04 两条744h CF阈值因子筛选运行中，Case2即时队列已部署

- Stage B仍为PGID3946395/Python3946400、2160h/Threads16 deferred Crossover；21:04约剩41621
  DPushes，尚无return code/QC/manifest。RSS约20.5GiB，状态不是32核运行。
- 作者授权利用空余资源并发。21:03:45启动两条`744h/start2880` Barrier16五步筛选：生产CF阈值
  1e-6与候选1e-4，分别绑定偶数/奇数CPU各16个；tag为
  `2030_base_744h_cf1e6_factor5_concurrent_20260901_v1`和
  `2030_base_744h_cf1e4_factor5_concurrent_20260901_v1`。两者无SoftMemLimit/TimeLimit，各有2秒
  遥测；pair supervisor896264保留95%整机保护。21:04 host used25.76%、available约91GiB、PSI0。
- 完整8760h只读误差上界：1e-4相对生产1e-6额外删除VRE64001与ROR261060个系数，wave0；
  容量上界可用电量损失合计约6.1015GWh，既有容量floor损失约0.4151GWh，单小时全国上界
  损失不超过约0.01303GW。它不是等价变换，是否保留必须由求解A/B决定。
- 隔离分支`codex/cf-sparsification-v1`已提交`46f843bc9137bf2112e33dba43e7cc4e584c4bfc`；
  审计py_compile/profile加载与`test_solver_profiles` 10/10 PASS，生产repo仍clean6065bfb。
- Case2 watcher881511当前`WAITING_STAGE_B`；Stage B严格通过且无竞争求解、clean6065bfb、used<90%、
  available>=96GiB和PSI正常时，立即且幂等启动唯一2160h/Threads32 Case2。4小时automation已更新。

## 2026-09-01 18:30 数值候选已隔离准备，生产Stage B不变

- 独立分支`codex/annual-energy-coordinate-v1`提交`4814c2e`，默认关闭、未部署服务器；仅缩放年度
  账户/省内年度流量，CF、径流、水库入流和资源可用量行保持物理坐标。
- 24h门禁候选与原版目标完全相同且QC PASS；raw Matrix上限6250→260.417且最小仍1.026e-6。
  但严格求解178.807s/131 Barrier/370107 simplex，略差于原版174.979s/120/366065，Kappa也更差；
  仅可作为当前Stage B结束后的唯一2160h A/B候选，不能称已加速或直接上8760h。
- heartbeat `2160h-stage-b`已从每小时改为每4小时；活动Stage B、95%保护和服务器2秒遥测均未修改。

## 2026-09-01 17:36 Stage B已进入deferred Crossover

- 同一tag/PGID3946395/Python3946400和clean6065bfb持续；exact resume所需科学输入、Gurobi13.0.2、
  implementation、Fingerprint `0xcf045770`、维度/顺序及向量完整性门禁均通过。
- 日志明确`use start vectors`及`perform crossover with primal and dual start vectors`，未重跑Barrier；
  Presolve1513.67s后进入Crossover。17:36 DPushes 8159992→222988，DInf约9.04，尚未收敛。
- 3462个2秒样本/errors0；RSS峰28.908GB、host可用最低92.465GB、memory PSI0，双stderr空。
- 尚无return code/solve report/QC/result manifest；继续原heartbeat，只读监测，不改参/重启/并发。

## 2026-09-01 15:42 Case1 2160h deferred Stage B已启动

- tag `2030_base_2160h_case1_v3_stage_b_20260901_v1`；source为只读
  `2030_base_2160h_case1_v3_barrier16_stage_a_20260827_v1`。production clean6065bfb。
- 启动前无CISPO solver、MemAvailable113.093GiB、si/so0/0、memory PSI0；checkpoint gate
  eligible=true，BarX/BarPi 10398783/12520914项的size/SHA全部PASS；定向测试13+34 subtests PASS。
- Method2/Threads16/Presolve2/Crossover2/CrossoverBasis1/LPWarmStart2、Feas/Opt1e-6、NF2/Scale2；
  无TimeLimit/SoftMemLimit，95%整机保护和2秒遥测保留。
- launcher3946098、solve PGID3946395/Python3946400；15:42仍在build，双stderr空，尚未生成
  primal_dual_start_input，故exact resume/Crossover尚待确认。heartbeat `2160h-stage-b`后续已改为每4小时只读跟进。

## 2026-09-01 13:59 Case4按作者要求停止，GPU1已释放

- 停止前精确核验标签、PGID1216966/Python1216969、创建时间、完整命令行和GPU1客户；仅对该
  进程组发送SIGTERM，29秒正常退出，未强杀。GPU0其他客户未触碰。
- 终态`INTERRUPTED`/status11/rc143，solver386921.588s（107.478h）、PDHG78474440步、SolCount0；
  末行P/D/Compl=1.32e-4/762/0.388。不是自然收敛、科学接受、OOM、CPU回退或95%保护触发。
- 193911个2秒样本/errors0；RSS峰27.043GiB，GPU1任务显存峰4558MiB、平均利用99.196%。停止后
  求解、wrapper和telemetry均不存在，GPU1本任务显存释放。
- 生产repo仍clean6065bfb，未改模型/数据/参数/其他任务。`case-4-gpu-pdhg`三小时heartbeat已删除，
  不会自动重启。终态证据见`downloads/case4_gpu_pdhg_user_stop_20260901_1359/README.md`。

## 2026-09-01 13:52 Case4运行107h，进入新的长期平台

- 同一Python1216969/PGID1216966、clean6065bfb继续；solver386540s/78397740步，无终态/QC。
- P/D/Compl=1.66e-4/763/0.388，目标相对分离仍78.14%。近24h D残差仅改善1.548%、
  Compl0.257%、目标绝对分离0.232%；P在1.04e-4以上振荡，没有持续下降。
- 近48h目标绝对分离也只改善0.321%，8月29日P残差突破未转化为整体收敛加速。
- GPU1当前100%/job4558MiB、全程平均99.20%，193695样本/errors0；RSS16.59GiB，
  主机可用约96.5GiB、PSI0，两stderr空，无CPU回退/CUDA/OOM，故不是资源瓶颈。
- 按作者无时限要求继续，不停止、重启、改参或改95%保护。证据见
  `downloads/case4_gpu_pdhg_heartbeat_20260901_1352/README.md`。

## 2026-08-29 23:32 Case4原始可行性残差突破旧平台

- 同一Python1216969/PGID1216966、clean6065bfb继续；solver162185s/32634740步，无终态。
- 近3h primal residual `3.93e-3 -> 1.04e-4`（降低97.354%），新水平已持续约1.54h；
  dual residual仅790→789、Compl0.390→0.389，目标绝对分离仅改善0.887%。
- 这是原始可行性方向突破，不是整体收敛；目标相对分离仍约78.19%，不能科学接受或预测终态。
- GPU1仍100%/job4558MiB，81526样本/errors0，RSS16.59GiB、主机可用约86.9GiB、PSI0；
  两stderr空，无CPU回退/CUDA/OOM。未停机、重启、改参或改95%保护。
- 证据见`downloads/case4_gpu_pdhg_heartbeat_20260829_2332/README.md`；继续原三小时巡检。

## 2026-08-29 15:35 8760h原始矩阵审计完成，活动PDHG未干预

- 本地可续传副本和审计均已`COMPLETE`：4142909397bytes、SHA256`344f2ae4...43fe2435d`，
  integrity PASS；规模50907234 rows/41458383 columns/492835195 nnz与预期一致。
- 审计仅解析原始MPS，无build/presolve/optimize；未取得full presolved范围或Kappa，不能称科学接受。
- 主要尺度源为VRE/ROR容量列同时连接小时CF约1e-6和年度FLH约6000，列族跨度约59亿倍；
  年度负荷中心子系统同时产生6250、4380与1e-6目标系数。
- 已形成待验证的等价候选：年度能量/流量内部坐标统一按8192GWh缩放，输出/QC恢复GWh；
  当前未实现、未部署、未改求解参数。详见`downloads/numerical_audit_8760_20260829_v1/REPORT.md`。
- 服务器repo仍clean6065bfb；同2160h Python1216969/PGID1216966继续，未停机、重启或改参。

## 2026-08-29 15:16 2160h GPU-PDHG仍属残差平台

- 同一任务继续，solver36.768h/26552140步，P/D/Compl=0.00393/793/0.390，无异常或终态。
- 近3/6/12/24h：D残差仅改善0.252/0.751/1.491/4.802%，Compl改善0/0/0.256/1.015%，
  P在日志打印精度下无变化；目标绝对分离仍改善1.644/3.140/4.262/6.041%。
- 判断为“残差仍平台、目标差非完全横盘”；目标差在不可行时不是最优性证书，不预测剩余时间。
- GPU1仍100%、job4558MiB，资源记录正常；仅只读分析，不停机/改参。证据见pdhg_plateau_review_20260829_1516。

## 2026-08-28 19:10 核验：8760h GPU0已因主存保护结束

- 当前v2于18:23:22结束rc=-9，原PID702485已退出；不要再将17:22启动快照视为活动状态。
- 建模完成61.06min，规模50907234约束/41458383变量/492835195非零；随后约109s处于预处理，
  触发94%整机保护。未进入GPU-PDHG迭代、没有收敛/QC结果，不是显存OOM或算法收敛失败。
- 建模RSS峰48.183GiB、全程峰77.627GiB；整机峰94.374%，GPU0仅初始化job386MiB/总786MiB。
- 实际TimeLimit/SoftMemLimit=Infinity、Method6/Threads32及容差核实；25/25本地终态证据SHA匹配，
  见downloads/8760_gpu0_terminal_20260828_1910/README.md。clean6065bfb不变。
- 原2160h Python1216969/GPU1继续100%；没有停止/改参/重启。后续需作者另定主存窗口，不能自动重试。
- 与历史8760维度相同但指纹不同，来源待核；本轮不足以评价完整8760的GPU速度或显存容纳性。

## 2026-08-28 17:22 新增完整8760h GPU0运行（作者新授权）

- 17:20:22启动tag `2030_base_8760h_gpu0_pdhg_unlimited_20260828_v2`，PID/PGID702485。
- Base2030/8760h/start0、clean6065bfb、GPU0/Threads32；沿用2160h无限时PDHG所有数值参数。
- 目前建模中，RSS约8.38GiB，host可用78.46GiB，GPU0为786MiB/0%；尚未确认GPU迭代开始。
  参数快照TimeLimit/SoftMemLimit均null，实际Infinity读回在建模完成后自动核实；preflight PASS。
- 新job仅放宽96GiB启动准入，不设Gurobi内存/时间上限。共享主机旧95%保护不动，
  新组94%整机优先退出，0.25秒检查、2秒完整资源采样；OOM优先分值500只施于新进程。
- 原2160h Python1216969/GPU1仍100%/4600MiB；独立审计下载正常推进，未干预。
- v1启动器错误在模型构建前退出125，现场保留，已修正v2；6项单测和静态检查PASS。
- 完整复现/命令/证据见downloads/8760_gpu0_launch_20260828_v2/README.md；不重复启动、
  不自动缩小/StageB，真实峰值、GPU运行及QC待后续证据。既有2160h三小时自动巡检未修改。

## 2026-08-28 17:12 N50R5登录态核验

- 当前平台确已绑定NC-N50R5/scvk386及BSCC-N56R5/scxk805等共五个超算账号；关系图标记在线。
- N50R5网页SSH本次返回connection closed，未获得提示符；队列页仅返回A6/A8，GPU配置/空闲/调度权限未核实。
- 首页可用额度显示约-4973元，须另核合同/信用及计费条件；不能据此认定SSH断连原因。
- 详见downloads/cloud_resource_inventory_20260828_1703/README.md新增段；Chrome关系页已保留。
- 原17:03数据仅为bscc-m8集群快照，不能当作全平台资源清单；本轮无作业提交、账号/许可/运行流程变更。

## 2026-08-28 17:03 超算账号可用资源快照

- 用户有权限的UP分区：amd_m8_768-a（192CPU/768000MB，193节点，80严格idle）、amd_a8_768
  （128CPU/768000MB，61节点，29严格idle）、amd_a8_384（128CPU，384000/768000MB，102节点，0严格idle）。
- 状态时刻17:03:52；当前用户作业数0。关联CPU总配额1280、排队+运行作业上限50；不是无限实际资源。
- 分区节点存在重叠，不相加；当前集群361唯一节点GRES均null，不代表平台其他中心没有GPU。
- 全平台控制台需作者登录后继续，Chrome登录页已保留；详见downloads/cloud_resource_inventory_20260828_1703/README.md。
- 只读查询，无新计费任务、无模型/许可证/运行进程变更。

## 2026-08-28 17:00 PDHG/Barrier16轨迹只读对照

- 同2160/start2880、原LP指纹一致；PDHG快照约16:53，solver14.379h/10111540步，未终态。
- 10—14h目标绝对差Barrier下降88.83%、PDHG下降0.48%；PDHG前期更快接近，但当前平台明显。
  14h PDHG绝对差仍小约10倍，不能将下降速率当作同QC全局性能排名；Barrier23h终态严格质量HARD_FAIL。
- 数据/完整解释见downloads/pdhg_barrier_comparison_20260828_v1/REPORT.md；仅scp日志、本地分析/4项单测，
  没有服务器写操作、改参或停机。16:59独立审计下载222MiB仍继续，不变更既有运行安排。

## 2026-08-28 16:44 云端GPU可部署性核验

- 当前云应用为Gurobi13.0.2 CPU版，许可WLS、文件0600；有效期/并发额度未新建会话核验。
- 当前sinfo -a全部GRES null，未见GPU队列；需要另行开通/切换GPU资源区，而非直接改变原CPU节点。
- 16:42云队列空；本地原Python1216969、GPU1 RTX4090 100%/4600MiB，GPU包13.0.2+cu129。
- 只读查询，未申请GPU/安装/移动许可证/启动或停止求解。详情见downloads/cloud_gpu_license_review_20260828_v1。

## 2026-08-28 16:43 审计恢复流程已启动，PDHG不变

- 作者授权“继续审计”；当前为本机独立local_8760_verified_v3/run_v1，16:41:48 Python49052/
  launcher13448启动，1MiB/2线程可续传；16:42:10已保存3完整块，仍DOWNLOADING。
- 全部下载并校验SHA后自动本地审计；不写固定服务器部分备份，不触碰其45560进程，源端仅stat/dd。
- 32MiB版超时后只停止本次本机31188及SSH客户端，保留v2现场；15:38旧失败现场也保留。
- 16:38固定服务器仍clean6065bfb、原PDHG1216969，GPU1 100%/4600MiB，资源记录无错误。
  未改模型/求解参数、未停止PDHG；本地流程详情与代码SHA见隔离outputs/local_8760_verified_v3/README.md。

## 2026-08-28 16:33 审计已传输失败；PDHG仍运行

- 本机全8760h流式审计15:38:14 FAILED：SSH Connection reset后gzip EOF；审计进程已退出，
  最后104072756/492835195 nnz（21.1%），无audit.json、未完成完整性核验。现场保留，未自动重启。
- 16:32云端/固定服务器SSH均可达；云端原MPS大小4142909397bytes、mtime03:01:57未变，未重做完整SHA。
- 独立完整备份仍有原进程45560，但进度停在14:22:46、1945156460/6606826274bytes（31/104范围），
  无终态PASS。不能使用该部分副本替代完整MPS；本轮未重启或干预备份任务。
- 同一PDHG Python1216969/PGID1216966、clean6065bfb持续；16:31约984万步、solver50470s，
  primal/dual/Compl=0.00393/828/0.393，未收敛。RSS17.002GiB、GPU1 100%/4600MiB，
  25702个2秒样本/errors0，双stderr空、无return_code、未见OOM/CPU回退。保持无时限及原3h巡检。

## 2026-08-28 15:09 历史8760h日志简报完成，无服务器操作

- 3页中文PDF/Markdown及2组PNG/SVG：output/pdf/8760_stage_a_convergence_20260828_v1。
  原始7文件哈希匹配，608个Barrier记录点连续；607步，solver20.5279天，迭代占98.8365%。
- 矩阵范围、原/预求解维度、阶段时间、资源与终态QC均有CSV/JSON来源；6/6解析测试及逐页QA通过。
- 原LP仍HARD_FAIL、恢复QC仍FAIL，不将solver OPTIMAL视为科研验收。本次未运行StageB或任何新求解，
  未干预Case4、独立数值诊断或后台备份；此项是本地分析里程碑，不是新的服务器实时状态快照。

## 2026-08-28 15:07 数值改进在本机隔离执行；PDHG不变

- 14:56复核生产clean6065bfb、原Python1216969/GPU1继续，利用率100%、4600MiB；未改参数/进程。
- 独立worktree `.codex_tmp/numerical_stability_20260828_v1`，候选提交cff89ce；237项回归通过，
  但24h原版/缩放版/零上界修正版均NUMERIC，不能部署或宣称稳定性已修复。详见其NUMERICAL_STABILITY_WORKLOG.md。
- 完整8760h矩阵只读审计已在Windows后台开始，源为云端完整归档，不依赖固定服务器部分备份。
  Python34684/launcher37332/SSH40220（须复核），15:06:29约2409万/49284万nnz、39MB RSS，
  状态RUNNING，完整哈希尚未完成。此任务不占服务器计算或GPU，不改变PDHG的3h巡检/2s采样。
- 接续读取worktree outputs/stream_8760_original_v1/status.json；不得重复启动、把部分统计当全量结论。

## 2026-08-28 14:34 数值尺度只读诊断，不改变当前运行

- 云端8760h及2160h Barrier/PDHG原Matrix极值同为1.000486e-6～6250，约6.247e9倍；
  目标1e-6～3853.189876。两个2160h同指纹0xcf045770，未见原LP数值范围新增恶化。
- 两个Barrier的strict原LP质量均HARD_FAIL；PDHG截至约14:25的快照未收敛但无明确数值告警。
  已有1h归档显示预求解可增大最差行跨度，不能将其当成当前2160h/8760h预求解统计。
- 证据downloads/numerical_review_20260828_v1/REPORT.md及evidence.json。未启动新模型/presolve/optimize，
  未停止/重启/改参，14:31 production仍clean6065bfb；3h巡检与2s采样/95%保护保持。

## 2026-08-28 14:18 Case4改善放缓，继续无时限GPU运行

- 同一无时限tag/PGID1216966/Python1216969仍运行且身份实核一致，production clean6065bfb。
  实际time_limit_seconds/soft_mem_limit_gb均null，未改参/重启。14:18:02已8211040步、solver
  42448.095s含presolve、墙钟约12h03m；stdout primal/dual/Compl由0.00396/847/0.396变为
  0.00393/837/0.394，近3h改善很小，目标差未闭合，无终态/QC，不因此终止。
- RSS17.002GiB/采样峰27.043GiB、GPU1卡级4600MiB/job4558MiB，自上次GPU均值99.9991%；
  host可用86.831GiB，summary21681条/errors0，当前61°C/313.73W，无OOM/回退/监测异常。
- 只读证据review_20260828_1417已备份，约17:17再检查。其他窗口的云端结果备份任务未干预。

## 2026-08-28 14:17 2030结果可视化完成；完整备份仍在传输

- t550独立备份父目录`/home/zz2/National_model_server/backups/2030_8760_stage_a_first_recovered_20260828_v1`。
  复制整个云端`20260828_8760_stagea_recovery_v1`，301文件/6.153GiB；核心结果86manifest文件/5.450GiB。
- Windows后台Python45560（14:14:41）4路分块；SHA匹配复用旧checkpoint4目标，少传1.376GiB。
  14:14:45完整范围计1626281156/6606826274bytes，状态IN_PROGRESS；大MPS等未传完，不能称完整备份成功。
  本机保持开机联网；完成后自动全量SHA256，服务器父目录`backup_status.json`与
  `release_integrity_report.json`分别需COMPLETE/PASS。无需云端计算，不干预Case4。
- 可视化已完成，analysis_v1存PNG/PDF/SVG和CSV/JSON；原数据/QC FAIL不修改。
  本机60绘图输入逐项SHA256通过、4/4校验测试通过；详细说明和续传命令见
  `downloads/2030_stage_a_first_result_visualization_v1/README.md`。
- 14:19复核：后台45560仍运行、stderr空，最近进度1810938732bytes（1.687/6.153GiB）；
  图表12文件服务器SHA256复核全PASS，完整release仍未完成，Case4原进程1216969仍运行。

## 2026-08-28 13:45 云端历史8760h恢复已成功结束

- job4396245于03:18:35 COMPLETED0:0，24核总耗时1:04:39；build38m57s，完整恢复采样峰62.061GiB。
  原LP指纹/维度/完整名称顺序完全匹配，没有实际用到fingerprint豁免，optimize/presolve0。
- 新云端root `20260828_8760_stagea_recovery_v1/recovered_8760`：preservation COMPLETE、86文件约5.45GiB，
  原MPS和完整名称目录均已归档；容量/运行/成本/碳/对偶及86900行candidate state（next2040）生成。
- 运行末尾manifest/candidate读取成功；本次86文件存在/大小及关键结果/state关联hash复核PASS。
  QC仍FAIL（56/58），未通过省际双向流和objective_components；raw LP另2行超1e-5。全部违反项保留，
  科学接受仍false，不自动论文采用/续年。未重新求解，不影响独立Case4。
- 本地只有终态报告备份terminal_review_1342，完整恢复数据仍在云端；待作者决定下载/后续分析。

## 2026-08-28 11:17 Case4已约599万步，primal改善但未收敛

- 同一无时限GPU1任务继续运行，PGID1216966/Python1216969身份已核实，production clean6065bfb。
  实际配置time_limit_seconds/soft_mem_limit_gb均null；solver31569.427s已超过旧21600s仍正常迭代。
- 11:16:44为5992040步，墙钟约9h01m，GPU迭代约8h09m；stdout primal/dual/Compl为
  0.00396/847/0.396，上次为2.54/1020/0.502。primal明显下降，但目标差未闭合，无终态/QC。
- RSS当前17.001GiB/采样峰27.043GiB，host可用87.196GiB；GPU1显存卡级4600MiB/job4558MiB，
  近3h GPU均值99.9998%，温度峰61°C、功耗峰317.6W。资源连续记录，未见OOM/CPU回退/监测错误。
- 本次只读检查、备份及交接；证据review_20260828_1116。继续无时限，约14:16再审查。

## 2026-08-28 08:15 Case4继续GPU运行，较上次巡检残差改善

- 同一无时限tag `2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2`仍运行；
  PGID1216966/Python1216969创建时间/命令行实核一致，生产clean6065bfb，配置无时限未漂移。
- 08:14:36为3763040步，solver20641.640s（含presolve），总墙钟近6h、GPU迭代约5h07m。
  stdout primal/dual/Compl较05:14的9.71/4950/24.2降为2.54/1020/0.502；目标仍明显分离，
  尚无终态/QC，不能推断已收敛、全程单调或比Barrier更快。
- 资源截至08:14:37：RSS17.001GiB/采样峰27.043GiB，host可用87.349GiB；GPU1卡级显存
  4600MiB（18.727%）、job4558MiB，近3h GPU平均99.9998%，当前60°C/314.22W。
  10782个2秒样本/errors0，日志持续更新，无OOM/CPU回退；stderr空，memory PSI为0、无新增swap-out。
- 本轮未操作运行进程或更改参数，已备份证据到review_20260828_0814；保持无时限，约11:14再审查。

## 2026-08-28 05:14 Case4已确认GPU迭代，尚未收敛

- 当前tag `2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2`，pgid1216966/Python1216969
  身份实核一致，production clean6065bfb。自身配置快照TimeLimit/SoftMemLimit对应字段均null，
  无6h限制；未修改模型、数据、参数或启动其他任务。
- 日志确认RTX4090及Start PDHG on GPU。建模913.382s，presolve2184.98s，03:07:07进入GPU迭代。
  05:13:51为1551040步、solver9797.042s（含presolve），没有终态或QC。
- 资源截至05:13:53：job RSS当前17.001GiB/采样峰27.043GiB，整机可用87.330GiB；GPU1显存
  卡级当前/峰4600MiB（18.727%）、本job4558MiB，近1h GPU平均99.999%、温度峰61°C、功耗峰316.91W。
  GPU0无本job显存；GPU1显存控制器100%表示活动率，不是显存容量用满。
- 2秒采样5360条/errors0，stdout/资源文件持续更新，solver及telemetry stderr空，无OOM/CPU回退。
  当前Swap7.419GiB为既有占用，本轮swap-out增量0、swap-in13.508MiB，memory PSI为0。
- stdout在7200s的primal/dual/compl为0.196/2.22e4/193，9795s为9.71/4.95e3/24.2。
  残差非单调、目标仍明显分离，不能认定已收敛或比Barrier快。保持无时限观察，不按长尾提前停止。
- 本地证据 `downloads/case4_unlimited_20260828_v3/review_20260828_0514/`；每3小时继续检查，
  原95%整机保护不变。以下“尚未确认GPU迭代”为早期历史记录。

## 2026-08-28 02:16 无时限Case4已启动；改为每3小时审查

- 作者取消6h限制并将审查频率改为3小时。新tag
  `2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2`于02:15:14启动，pgid1216966、
  Python1216969、telemetry1216967。生产repo仍clean6065bfb，旧恢复现场保持不变。
- 旧screen进程已缓存6h配置、无在线改参入口，因此在进入求解前做一次受控替换；旧tag于02:15:04
  rc143/hostguard0，约10分钟建模需重做，日志与输出全保留，不能算作PDHG算法失败。
- 新profile数值参数仅time_limit_seconds21600→null。实际Gurobi空模型参数检查TimeLimit=Infinity，
  新任务自身配置快照也已确认null；其余模型/2160h/start2880/GPU1/Threads32/容差不变。
- 无新增内存/显存上限，原95%整机保护保留。2秒采样正常，02:15:32为9条/errors0，stderr空；
  尚未确认进入GPU迭代。部署新隔离工具包case4_unlimited_20260828_v3，服务器最终18/18测试PASS。
- heartbeat case-4-gpu-pdhg ACTIVE，每3小时，仅跟进新tag；不再按6小时、长尾或暂时不如Barrier
  提前停止。以下screen运行与10分钟审查记录均为历史状态。

## 2026-08-28 02:15 云端24核恢复job4396245已运行

- 作者授权后已在原云端环境提交，02:13:56 RUNNING于m4cg1702，**24CPU/128G/billing24**，上限4h。
  根 `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260828_8760_stagea_recovery_v1`，
  输出recovered_8760，控制control。02:14:08进入原LP构建，stderr0；尚未恢复完毕。
- 计算节点Python3.10.20及原8个依赖全部匹配，30原始文件/77输入校验PASS，tiny测试6/6。
  原源码只加入导出/恢复补丁，原release/数据/结果不改；未干预固定服务器Case4。
- 新授权策略：指纹差异记录后可继续（显式flag），先保存重建模型；维度/nnz、完整顺序和向量
  哈希/finite继续防错配。QC FAIL不阻断保存，审计异常尝试保留其他结果，科学接受不自动升级。
- 不执行正式模型optimize/presolve、Stage B、续年。progress可用内存是节点值，任务实际配额仅128G。

## 2026-08-28 02:06 Case4已按新授权独立启动，资源采样正常

- 作者明确要求先启动PDHG，不再等待历史恢复成功。Case4于02:05:12启动，tag
  `2030_base_2160h_case4_gpu_pdhg_screen_20260828_v1`，pgid1175169、Python1175172、telemetry1175170。
- Base2030/2160h/start2880、GPU1单4090、Method6/Threads32、最多6h、原PDHG profile不变，
  GPU Python13.0.2+cu129，SoftMemLimit空、95%整机保护保留。生产repo仍clean6065bfb。
- 启动前available104.376GiB、GPU1无计算客户端/free24047MiB；新独立工具包
  `campaign_tools/case4_independent_20260828_v2`，只新增显式失败恢复后独立启动授权，10/10测试PASS。
- 02:05:22监测6样本/errors0、stderr0，GPU1已分配本job显存约386MiB；仍在数据/模型准备，
  尚未见Start PDHG on GPU，不代表已开始GPU迭代。02:05:41资源TSV继续更新、Python存活，无终态。
- heartbeat case-4-gpu-pdhg已ACTIVE，每10分钟仅监测此运行；恢复失败不再阻断本case，不重复启动。
  历史恢复/指纹不匹配现场保留，未重跑或修复；以下暂停记录为旧状态。

## 2026-08-28 02:07 云端原环境仍与历史一致，仅可行性核验

- 原release、checkpoint和数据链接仍在；Python3.10.20及8个已记录依赖版本全部匹配历史，
  原30源码bundle摘要bdf36a79...caf9a8e也匹配。因此可优先考虑云端原环境恢复，但未提交作业。
- 用户队列为空，amd_a8_768 UP；DefMemPerCPU6000、MaxMemPerCPU6144，未来可评估24CPU/128G，
  不照搬原96CPU/700G Barrier申请。实际付费/配额和执行授权仍待确认。
- 先补失败模型归档，再在独立目录只重建/审计/导出，不调用optimize/presolve、不覆盖原结果。
  云端历史构建约39分钟不代表总恢复39分钟，完整导出耗时和指纹匹配尚待实测。

## 2026-08-28 02:04 恢复失败原因进一步核查，未重启

- 已确认是指纹门禁主动抛错，不是内存耗尽或95%保护，原始向量/备份不受损。
- 源Python3.10.20/NumPy2.2.6/SciPy1.15.3/xarray2025.1.2，目标3.11.15/2.4.6/1.17.1/2026.7.0；
  Gurobi同13.0.2。依赖不一致是排查线索，尚未证明是LP指纹差异根因。
- 恢复入口先验证后归档，异常导致本次重建MPS/完整名称目录未保存。这一失败保全路径需修复；
  当前只有build_report、日志及原始checkpoint副本，不能宣称恢复完成。没有放宽门禁或自动重启。
- 生产repo仍clean6065bfb，02:02主机available约104.3GiB。Case4既有暂停状态未变。

## 2026-08-28 00:57 恢复失败，Case4未启动，自动接续PAUSED

- 恢复于00:47:11发生原LP identity mismatch，wrapper于00:48:04退出rc1，host95_guard=0。
  变量/约束/非零元均与历史一致（41458383/50907234/492835195），但fingerprint
  718212258 != -781497218。根因未明，不能跳过验证使用旧向量；尚未完成正式结果恢复。
- build3566.906s，wall1:00:28，采样peak tree RSS47.914GiB；optimize/presolve均0。
  此次不是内存保护终止。原checkpoint、备份和失败现场保留，无模型或输入修改。
- Case4门禁返回BLOCKED_RECOVERY_FAILED；无launch_claim或Case4控制目录，算法未启动。
  heartbeat `case-4-gpu-pdhg`已PAUSED并复核，覆盖下方ACTIVE/WAITING旧状态。
- 00:57主机available约104GiB、恢复进程已退出，生产repo仍clean6065bfb。未因此绕过接续门禁。
  证据在 `downloads/case4_after_recovery_20260828_v1/recovery_failure_0057/`；等待作者下一步决定。

## 2026-08-28 00:46 恢复后Case 4后续任务已设定，当前WAITING_RECOVERY

- 作者已授权恢复结束后自动接续；当前对话heartbeat `case-4-gpu-pdhg` ACTIVE，每10分钟检查一次。
  一次性门禁实调返回WAITING_RECOVERY，**Case 4未启动**；覆盖下方00:32“未排队”的旧状态。
- 预定标签 `2030_base_2160h_case4_gpu_pdhg_screen_20260828_v1`，单GPU1、2160h/start2880，最多6h，
  原profile容差不变，无SoftMemLimit和新增显存上限。恢复失败不抢占/重试，成功后还须通过资源门禁。
- 独立工具已部署 `campaign_tools/case4_after_recovery_20260828_v1`；服务器15/15测试PASS（包含
  不求解的5秒占位job采样集成测试），双GPU单次真实采样无错误。生产repo仍clean6065bfb，恢复未干预。
- 正式启动后每2秒写入本Case控制目录的 `resource_pressure.jsonl` 和 `resource_pressure_summary.json`，
  同时保留resource_monitor.tsv/time.txt：主机内存/Swap/PSI、job RSS/CPU、双卡显存/GPU活跃率/
  显存控制器活跃率/温度/功耗及本job显存。峰值为采样峰值；显存活跃率不是显存容量占用率。
- 定时检查依赖本机Codex运行及SSH可达；启动后的监测在服务器持续运行。完成后汇总并暂停heartbeat。

## 2026-08-28 00:32 Case 4未启动：双GPU空闲但历史恢复占用主机

- SSH正常，双4090 GPU利用率均0%，显存分别395/36MiB。历史8760h恢复PID657364仍在构建原LP，
  RSS约30.96GiB，整机available约71.96GiB，低于2160h既定启动门槛96GiB；不能仅按GPU空闲启动。
- Case 4未启动、未自动排队；恢复进程未干预。生产checkout仍clean6065bfb，未部署本地新修改。
- 本地修复campaign启动器GPU解释器被共享环境覆盖的问题，并增加历史恢复并发门禁；6项隔离
  Bash/初始化测试PASS。Case 4仍为2160h、最多6h、单GPU-PDHG，模型与profile不变、无SoftMemLimit。
- Gurobi13.0.2公开文档未找到受支持的单模型双卡分摊设置，不能宣称双24GB=48GB可用显存。
  下一步等恢复结束并重新核查资源后，单独部署启动器修复，再启动Case 4；本记录不表示已安排自动执行。

## 2026-08-27 23:48 历史8760h离线恢复已启动

- t550已启动云端job4139552的Stage A恢复。根
  `/home/zz2/National_model_server/recovery_8760_20260827_v1`，结果 `recovered_8760`、日志 `control`。
  launcher657349、进程组657359、Python657364；23:47:35启动、23:47:45进入原LP构建，stderr0。
- 使用精确旧release建模代码及显式映射后的历史输入；原30文件/77条输入与配置、实际22536个CF
  文件全payload哈希均通过。现用数据仅复用，不修改；历史output_manifest另存隔离目录。
- 同历史版本1h恢复对照PASS；全年度LP指纹、完整顺序和结果尚待构建后核验，不是恢复已完成。
  禁止optimize/presolve，启动available100.91GiB，90GiB启动门槛，整机95%保护只针对自身进程组。
- 生产checkout仍clean6065bfb；2160h原输出、云端8760h原输出和本地原备份保持不变；Stage B未启动。
  下一步只检查这一个恢复任务及最终manifest，不并发启动其他大模型。详见handoff本时刻条目。

## 2026-08-27 23:34 2160h Case 1 Stage A结束，工程检查点完整但QC未通过

- Case 1于23:27:51退出rc0，未触发95%整机保护，stderr0；242 Barrier iterations，solver82535.468s，
  wrapper wall23:13:57，peak tree RSS69.291GiB，整机最高使用率88.742598%。server clean `6065bfb`。
- OPTIMAL是宽松Stage A终态，strict contract仍为HARD_FAIL。最大原LPconstraint violation0.0384984，
  bound violation0.000263950，dual violation0.00783257；末次primal-dual objective相对差6.286394%。
  工程QC53/58，失败项：power_balance、wave_availability、unidirectional_interprovincial_flow、
  reservoir_transition、captured_co2_reconstruction。没有canonical科学result manifest或planning state。
- `outputs/2030_base_2160h_case1_v3_barrier16_stage_a_20260827_v1/barrier_checkpoint`已实读核验：
  BarX10398783/BarPi12520914 entries，全部finite，SHA256均匹配；engineering checkpoint可续接，
  scientifically_accepted=false。旧进程不具备今天本地实现的新保全逻辑，仍需独立离线补齐完整导出。
- 23:34主机available约101GiB，当前无CISPO solver；Stage B和Case 2--4未启动。本轮仅状态复核和
  本地交接更新，没有部署、调整参数或启动下一任务。

## 2026-08-27 14:18 Stage A 保存/恢复本地验证通过，尚未部署

- 本地实现无验收筛选的Stage A保全、候选容量状态显式读取、默认原模型归档及可选presolved诊断副本。
  运行边界是：保存原模型/raw-order向量、名称/顺序/hash和逐项QC；候选state必须显式选择，且不得因
  文件完整而升级为accepted。原模型/向量保全不等于科学接受或内部Barrier断点恢复。本节为自包含
  历史说明，不依赖当时未提交的独立说明文档。
- Gurobi13.0.2回归222/222 PASS；1h在线/离线45个数据产物、碳和原LP残差一致，恢复端零optimize/
  presolve调用。已显式读入候选构建2040/1h LP，仅build，不求解、不作为正式续年。
- 未部署固定服务器或云端。当前2160h进程仍使用旧逻辑，不能通过本地改文件让它自动获得新保存策略；
  终态后需要独立恢复。历史8760h原始备份不变，未执行全年重建或Stage B。
- 本轮没有刷新服务器实时占用。上轮13:47的只读快照为t550总123.1GiB、可用25.7GiB、2160h进程
  RSS68.3GiB；真正安排恢复前必须再次检查，不能把该数值当作现在空闲资源。

## 2026-08-27 13:39 Stage A 保全政策更新（本地核查，非实时服务器快照）

- 作者要求：Stage A 不论 QC 是否达标，都保存可读取的容量、运行、成本、碳、对偶、QC、结果清单和
  候选跨年容量状态；保留违反项，是否采用留待作者选择。该要求已记录，代码和部署尚未完成。
- job `4139552` 的本地备份已闭合，保存完整 finite `BarX/BarPi`；历史终态为 OPTIMAL，但 strict
  contract HARD_FAIL，不能把备份完整性 PASS 混同于科学接受。原始文件不重标、不覆盖。
- 当前没有可直接供下一年份使用的 candidate state；现有 loader 仍强制 QC PASS/accepted checkpoint。
  同年 Stage B 的 checkpoint 输入资格与跨年状态不同，前者不要求先生成结果表。
- 恢复优先采用 exact-LP 映射核验后的离线数值导出，不以重新启动 Barrier/Crossover 为前提。
  历史模型构建峰值 48.574 GiB，高于本机约 32 GiB；完整恢复仍需资源规划和小样本验证。
- 本轮未实时 SSH、未启动恢复/Stage B/续年、未部署代码、未干预其他任务。下方服务器状态均为其
  各自时间戳的历史快照；当前实时占用需执行前重新核实。详细要求见模型规范 2026-08-27 覆盖节。

## 2026-08-27 00:16 2160h Case 1 active; four-case campaign validated

- Server checkout is clean `6065bfba34b76098e86307081323e8545a4d25ac`. Full server regression with the
  data environment loaded is `217/217 PASS`.
- The review fixes in `88f8877` replace hard-coded transmission loss and VRE/hydro FOM access with the validated
  technology registry and make primary objective inclusion explicit. A matched 1h solve exactly reproduces the
  old `238529/80143/453269`, fingerprint `-146272577`, objective `2127270.3027043818 million CNY`, iterations,
  violations and QC.
- GPU runtime is isolated at `envs/cispo-2030-gurobi-gpu13.0.2-cu129-v1`; wheel SHA256 is
  `10f0a10fed0c0f959d11bc4f60d36d4ef04a13c48ecf649cd557e8b952de0680`. GPU smoke confirms RTX 4090 and
  `Start PDHG on GPU`.
- Active unique solver: tag `2030_base_2160h_case1_v3_barrier16_stage_a_20260827_v1`, started
  `2026-08-27T00:13:53+08:00`, process group `687599`. It is Base 2030 hours 2880--5039, V3 Barrier16 Stage A,
  with no Gurobi time or memory limit. Only the external whole-host 95% guard is active. At 00:15:52 it was still
  building, stderr 0, process RSS about 3.03 GiB, host used 16.02%, memory PSI 0. At 00:28:59 Gurobi started with
  raw dimensions `10398783/12520914/126724678`, fingerprint `0xcf045770`, no TimeLimit/SoftMemLimit, and build
  peak RSS 12.492 GiB; early presolve host use was about 28%.
- Do not deploy into the checkout or start Case 2--4 while Case 1 is active. If 2160h proves impossible due to
  real OOM/95% guard, retry 2016h and only then a smaller horizon. Do not touch the active cloud 8760h run.

## 2026-08-25 17:07 host95 deployed and validated; launch waiting for shared-host memory

- SSH recovered without a client configuration change. The server bare remote, GitHub and clean `t550` checkout
  now contain `60561e57c419131a94539c2258ff108cc725edfd`; functional host95 implementation remains
  `7dfefbbef5acc593d22b82173259931183353b89`.
- Before launch, resource snapshots were hardened to record `comm` rather than full process arguments on this
  shared host, preventing unrelated users' command-line credentials from being persisted. This operational-only
  fix is commit `60561e5`; model equations, data, scenario, numerics and memory thresholds are unchanged.
- Server verification PASS: `bash -n`, py_compile, profile tests `9/9`, guard tests `8/8`, and full pytest
  `215 passed + 63 subtests` in `98.34 s`; MaxRSS `1,186,016 KiB`, swaps `0`, checkout clean.
- Server preflight root `outputs/preflight_host95_2160h_deploy_20260825_v1` PASS: Base 2030 hours
  `2880--5039`, `10,331,823 vars / 13,932,898 rows / 123,010,374 nnz`, numerical compatibility PASS,
  `TEST_ONLY_TRUNCATED_HORIZON`. Physical RAM is `132,145,156,096 bytes`; resolved Gurobi
  `SoftMemLimit=125.537898 decimal GB` (95%), `TimeLimit=null`.
- Run status remains **NOT STARTED**. This is a shared server and other users' active workloads leave only about
  `85--86 GiB` available, below the checked-in `96 GiB` start gate. No foreign process was changed. Wait for
  available memory `>=96 GiB`, then recheck clean/no-solver/roots absent/si-so/PSI before launching the unique
  `2030_base_2160h_host95_20260825_v1` task.

## 2026-08-25 13:05 host95 long-horizon code ready locally; server unreachable

- New test-only profile `barrier_checkpoint_fixed_server_host_memory_95_v1` removes the old 12 h/80 GB
  termination boundary: `TimeLimit=null`; resolved Gurobi `SoftMemLimit=95%` of detected physical host memory.
- New launcher defaults to Base/2160 h/start 2880, requires clean/no-solver/available>=96 GiB, keeps one process
  group and samples whole-host memory every 2 s. It sends SIGTERM only at whole-host used>=95%; natural solver
  terminal remains valid and all evidence is retained in new output/control roots.
- Model/data boundary unchanged. Local py_compile, guard `8/8`, profile `9/9`, full unittest `215/215 PASS`;
  2160 preflight PASS with estimated raw scale `10,331,823/13,932,898/123,010,374`.
- Deployment status: **NOT DEPLOYED / NOT RUNNING**. Both SSH aliases currently time out during banner exchange;
  implementation `7dfefbbef5acc593d22b82173259931183353b89` is on GitHub, while server `origin` push failed.
  Last validated t550 state remains clean `50e2d20`, idle. Do not infer current live state until SSH is restored.

## 2026-08-25 t550 replacement server ready for short debugging gates

- Current SSH/Git: `national-model-server -> zz2@192.168.9.27`（direct source
  `124.16.2.17`）；local `origin=ssh://national-model-server/home/zz2/git/National_model.git`。bare remote、
  deployed clean checkout 和 local branch 均为
  `50e2d2012a76a342eed1d281997c9b2382731a8a`。
- Runtime root `/home/zz2/National_model_server`：Python 3.11.15、Gurobi 13.0.2、完整许可 PASS；
  model-ready/CF/hydro/raw-GRFR/wave 五个根均已 add-only 落位并校验。readiness、release/V5/hydro audits、
  data smoke `142/142`、pytest `212 passed + 59 subtests` 全 PASS。
- 1h Base root `outputs/2030_1h_new_server_smoke_20260825_v1`：`OPTIMAL + QC 58/58 + input/result
  manifests valid`；raw LP `238529/80143/453269`，objective `2127270.302704 million CNY`，solver/wall
  `6.925/33.33 s`，peak tree RSS `0.469 GiB`，swaps/stderr 0。它是
  `TEST_ONLY_TRUNCATED_HORIZON`，不能作为科学规划结果。
- End state: repo clean、无 CISPO/Gurobi、available RAM 约 104 GiB、root disk free 2.6 TiB。
  已挂载文件系统无旧 case；未挂载 `/dev/sdb1` 14.6 TiB NTFS 与 `/dev/sdc4` 222.7 GiB ext4 尚待管理员
  只读挂载授权，因此旧 case 状态仍为 `UNKNOWN_ON_UNMOUNTED_DISKS`。
- Evidence: `/home/zz2/National_model_server/manifests/deployment_evidence_checksums_20260825.sha256`
  （29 records，self SHA256 `4db4ba8a806028df9f1452ffd24a2ae63891728864ef562fa328bd961e686e52`）。

## 2026-08-17 19:29+08:00 parameter-route goal complete / cloud remains active

- 多轮 relaxed 744、V5/744、Base/1488、Base/2160 memory boundary、两批 factor screens、strict deferred
  v3、宏观 A/B、正式 profiles 和 fixed `14/14 + 212/212` 已逐项覆盖原参数筛选目标。
- 批准路线为 future Stage A/B v3，组合相对 strict 744 solver/wall 加速 `7.71×/6.99×`；仍须独立授权
  才能实际提交，截断根不是年度科学结果。
- cloud `4139552` 不因目标闭合而停止或改参，仍按约 2 小时/terminal/anomaly 低频只读；其实际全年
  terminal quality 尚未知。fixed 保持 idle `0363b7b`。

## 2026-08-17 19:26+08:00 full-year v3 profiles server validation PASS

- `0363b7b0183a52184b2f0be7a1381efc76d1615e` 已在 local/origin/GitHub 一致并部署到 fixed；部署前后
  均 clean/idle，无 CISPO/Gurobi。available 约 `113.85 GiB`，si/so 0、memory PSI 0。
- v3 JSON、bash、pycompile PASS；Gurobi focused `14/14 PASS`（wall `0:02.52`、MaxRSS `109,940 KiB`），
  full regression `212/212 PASS`（97.282 s，wall `1:38.40`、MaxRSS `1,118,064 KiB`），均 swaps 0。
- Stage A/B v3 参数现正式 `APPROVED / NOT LAUNCH AUTHORIZED`。没有启动 fixed solver；cloud v2 保持
  不变，下一常规检查约 21:20。

## 2026-08-17 19:20+08:00 cloud round 41 / next check about 21:20

- `4139552` 仍是用户队列唯一任务，RUNNING/Barrier 343；runtime `1,012,057.571 s`，primal/dual/compl
  `0.983025/8.356e-7/0.087008`，recent-20 `51.190 min`。
- wall `1,015,381 s`、allocated `27,076.827 core-hours`、actual CPU `4,235.784 h`、efficiency
  `15.6436%`；MaxRSS `362.913 GiB`，Gurobi current/max `351.054/354.498 GiB`。stderr 0，无
  solve/QC/result/checkpoint。
- iteration 推进后才追加 round 41；ledger `42` records、SHA `69e14220...0f25`。未取消/改参/启
  Stage B；下一常规 cloud 审计不早于约 21:20，terminal/anomaly 除外。

## 2026-08-17 19:18+08:00 approved full-year v3 profiles prepared locally

- 正式 future Stage A/B 文件已建立：`barrier_checkpoint_full_year_cloud_v3` 固定 relaxed winner
  `BCTol=1e-2/FeasOpt=1e-5/NF1/Crossover0`；`deferred_crossover2_full_year_cloud_v3` 固定 exact
  `Crossover2/Basis1/LPWarmStart2/FeasOpt=1e-6/NF2`。两者均为 16 solver threads、Presolve2、Scale2、
  Aggregate1、无 Gurobi TimeLimit、SoftMem600 GiB；不覆盖活动 cloud v2，也不授权启动。
- `solver_profile_version` 保持配置 schema `v1`，`_v3` 只属于 profile identity；首次 config load 已据此
  修正并 PASS。无 Gurobi 依赖的 config load、profile-role guard `5/5`、py_compile、diff check 均 PASS。
  本地默认 Python 缺 gurobipy，`tests.test_solver_profiles` 留给 fixed Gurobi 环境执行。
- fixed 仍 idle、尚未部署本里程碑；下一步只做精确提交/双推送后 no-solver/clean 门禁、targeted 与 full
  server regression，不启动 solver。cloud 继续约 2 小时/事件低频只读。

## 2026-08-17 19:14+08:00 deferred Crossover v3 strict PASS / fixed idle

- 18:44:12 terminal：runner/audit/macro `0/0/0`；`OPTIMAL + solver PASS + QC PASS 58/58 + valid input/result
  manifests + macro PASS`，无 state/basis，stderr 0。744 h 仍为 test-only，不是年度科学结果。
- Barrier 0、simplex `1,266,756`、solver `2,662.606 s`、Crossover `2,458.89 s`；wall `50:52.08`、
  MaxRSS `9,644,004 KiB`、swaps 0。最大 constraint/bound/dual vio 均 `<1e-6`。
- strict 配对 objective rel `1.838e-12`，capacity/carbon/cost/generation/operation L1
  `4.220e-8/1.588e-13/2.209e-9/0.002380/2.109e-6`，全部 PASS。Pi hourly/annual 均完整有限。
- fixed 已无 solver。Stage A+B 合计相对 strict 744 solver/wall 加速 `7.71×/6.99×`；未来 profile
  可正式冻结，但不触发新任务。cloud 保持原 job，约 19:20 检查。

## 2026-08-17 18:26+08:00 deferred Crossover v3 exact resume confirmed

- v3 唯一 solver 存活；Gurobi 明确使用 `LPWarmStart=2` 的 primal/dual vectors 并直接 Crossover，未重跑
  Barrier。Gurobi/Fingerprint/raw identity 为 `13.0.2 / 2120635803 / 4,454,178×3,735,087×40,395,436`；
  scientific manifest 77 rows、SHA `772627bc...9ac3`，仅 RAW_GRFR 0/0 usage 差异。
- presolve `166.67 s`，presolved `3,007,038/2,846,655/31,252,909`；push 于 solver `1,361 s` 完成，
  18:25:41 simplex iteration `1,220,005`、runtime `1,601 s`，尚未终态，未作验收。
- Python RSS `8,758,088 KiB`，Gurobi max `13.944 GiB`；available `105 GiB`、si/so/PSI 0、stderr 0，
  无 numerical trouble 和 solve/QC/result。继续运行；下一 fixed 约 19:10，cloud 约 19:20。

## 2026-08-17 17:54+08:00 deferred Crossover v3 active

- fixed 启动门禁：clean/no solver，available `113 GiB`、vmstat si/so 0、memory PSI 0、v3 roots 不存在；
  已部署 `710aa0259957d03c45821b755562fc1636a60519`。
- server bash/compile PASS、focused `17/17`、full `212/212 PASS`（97.198 s，wall 1:38.40，MaxRSS
  `1,105,756 KiB`，swaps 0）。
- `deferred_crossover2_744_validation_v0817_v3` 于 17:53:13 启动 supervisor/Python
  `1758970/1758995`；5 秒存活、start event 完整、stderr 0。唯一 fixed solver，checkout 冻结。
- 下一检查约 30--45 分钟或 phase/terminal/resource anomaly。cloud 本轮未查询/触碰。

## 2026-08-17 17:48+08:00 deferred Crossover v2 pre-build terminal / repair pushed

- v2 于 17:15:01 terminal，runner/audit/macro `1/41/42`；没有 output 文件、LP、Gurobi、telemetry、
  solve/QC/result/checkpoint，未进入模型构建或求解。
- 唯一错误为 memory gate 使用已删除的 `CLOUD_FULL_YEAR_PROFILE_IDS`。`018607c` 已双推送，改为按
  `cloud_full_year_role` 对所有 Stage A/B 版本实施 640 GiB floor；py_compile、focused `5/5 PASS`，旧引用 0。
- v1/v2 失败根永久保留。下一步先实时复核 fixed no-solver/clean/resource-safe，再部署 `018607c`、跑完整
  server regression，并用全新 v3 roots 启动唯一验证。cloud 本轮未查询/触碰，监控频率不提高。

## 2026-08-17 17:21+08:00 cloud round 40

- `4139552` RUNNING，Barrier 340、runtime `1,002,807.627 s`；primal/dual/compl
  `1.082073/8.926e-7/0.0942553`，recent-20 `51.928 min`。
- wall `1,008,190 s`、allocated `26,885.067 core-hours`、actual CPU `4,205.427 h`、efficiency
  `15.6422%`、MaxRSS `362.913 GiB`；stderr 0，无 terminal/checkpoint。
- ledger 41 records，SHA `5e3a972a...21a4`。未取消/改参/启 Stage B；fixed v2 本轮未查询。

## 2026-08-17 17:15+08:00 deferred Crossover v2 active

- fixed 已部署 exact `acf59f9180483b09c4c0e9380e0576457cc554ac`；`bash`/compile、focused `16/16`、
  full `211/211 PASS`（97.142 s，wall 1:38.26，MaxRSS `1,112,044 KiB`，swaps 0）。
- 全新 `deferred_crossover2_744_validation_v0817_v2` 于 17:14:54 启动 supervisor PID `1710059`；
  available `113.905 GiB`、si/so/PSI 0、初始 stdout/stderr 0。v1 失败根保留。
- checkout 冻结 `acf59f9`，禁止第二 solver/部署 docs tip；下次 fixed 仅 phase/terminal 或 30--45 分钟。
  cloud 本轮尚未查询、未触碰。

## 2026-08-17 17:10+08:00 deferred Crossover v1 failed before optimize / narrow fix local

- v1 于 16:39:46 terminal：runner/audit/macro `1/41/42`，wall `5:31.43`、MaxRSS `4,754,120 KiB`、
  swaps 0；无 Gurobi log/solve/QC/result，未执行 Barrier/Crossover。
- 唯一差异是 source `CISPO_RAW_GRFR_ROOT=null`、target=current raw path。科学 manifests 各自 valid，
  排除 solver 后 77/77 行完全相同、SHA `772627bc...9ac3`，该 root 两端 usage 0；其余 roots 与
  Fingerprint `2120635803` 一致。
- 本地修复仅允许 allowlisted RAW_GRFR 在双方 usage 0 时不同；consumed/non-allowlisted root 仍拒绝，
  audit 落盘。focused `4/4 + 5/5 PASS`、compile/diff PASS；未提交/部署/重启。
- fixed idle clean `b277fce`，available `113 GiB`、si/so/PSI 0。cloud 未查询、未触碰。

## 2026-08-17 16:43+08:00 all-version cloud profile guard prepared locally

- save-first 复核确认：complete `BarStatus=OPTIMAL` engineering checkpoint 可 deferred crossover；至少有
  1 次 Barrier iteration 的 incomplete result 尽力保存 recovery-only，但明确不可续接。
- runner 原只硬编码 cloud v1 profile guard；本地现按 Stage A/B 稳定前缀覆盖 v1/v2/future versions，
  强制 engineering flag/checkpoint input/full-year-only。focused `4/4 PASS`、compile/diff PASS。
- 当前 v2 cloud sbatch 本来已传正确 flag/full_year，job `4139552` 不受影响。此修复未提交/部署；fixed
  活动 checkout 保持 `b277fce`，两端任务均未查询、未触碰。

## 2026-08-17 16:35+08:00 deferred Crossover=2 744 validation active

- `b277fcea4cb42d4bf8634f0baaf794095e00d67f` 已双推送并部署；fixed 启动前 clean/idle，server
  `bash`/JSON/compile PASS、focused `20/20`、full regression `203/203 PASS`（tests `94.966 s`、
  wall `1:36.07`、MaxRSS `1,121,468 KiB`、swaps 0）。
- 全新 output/control 为 `deferred_crossover2_744_validation_v0817_v1`；16:34:12 启动 supervisor
  PID `1656831`、time child PID `1656855`。启动 available RAM `113.918 GiB`、si/so `0/0`、
  memory PSI avg10 0、stderr 0。
- 当前处于 exact LP build/identity gate 的初始窗口；必须先核对 target/source manifests、Gurobi
  `13.0.2`、scientific identity、Fingerprint、dimensions 与完整 Var/Constr order，再以
  `LPWarmStart=2` 直接 Crossover。checkout 冻结 `b277fce`，禁止第二 solver 或部署文档 tip。
- 监管降频：fixed 约 30--45 分钟或 phase/terminal/resource anomaly；cloud 约 2 小时且仅新 Barrier
  iteration/异常落账。云端 `4139552` 保持原 Stage A，未取消、未改参、未启 Stage B。

## 2026-08-17 16:30+08:00 deferred Crossover=2 resume fix prepared locally

- relaxed Base/744 source checkpoint gate PASS：Fingerprint `2120635803`、BarX/BarPi
  `3,735,087/4,454,178` entries 且 size/SHA 完整、source commit `6477f42`、Gurobi `13.0.2`。
- 修复真实 Stage A/B manifest 自相矛盾：只允许 `solver_configuration` 行不同；所有科学 input、Gurobi
  version、identity、Fingerprint、LP 尺寸与变量/约束顺序仍 fail-closed。跨 source bundle 必须显式授权
  且 exact LP 全通过，授权与两端 bundle 落盘。
- 新 744 Stage B profile 为 Crossover2/Basis1/LPWarmStart2、16 threads、Feas/Opt `1e-6`、NF2/Scale2、
  no TimeLimit、SoftMem80；新 runner 禁止 state/basis，要求严格 58/58、manifests 和 exact macro pair。
  本地 JSON/compile/diff、focused `6/6 PASS`；未提交/部署/启动。fixed idle `7551e3f`，cloud 未触碰。

## 2026-08-17 16:16+08:00 second factor batch terminal / no shortlist

- v2 campaign 15:23:11--16:06:11 串行完成；三根 identity valid、status 7、Barrier 5、runner/audit
  `2/0`、stderr/swaps 0、无科学/checkpoint 产物。summary `NO_MATERIAL_COST_IMPROVEMENT`、shortlist 空。
- `PreSparsify2` Factor NZ/Ops/step ratios `0.976002/1.073514/1.107897`；`BarOrder1`
  `1/1/1.107832`；Threads32 `1/1/1.256668`。case wall `17:00.64/12:46.29/13:01.31`，MaxRSS
  `20,371,484/19,783,500/19,759,924 KiB`。
- fixed 无 solver，available 约 `113 GiB`、si/so/PSI 0、checkout clean `7551e3f`。不运行这三根的
  完整 744、不继续参数盲扫；转入已有完整 744/1488/2160/cloud 证据的 8760 决策审计。cloud 未触碰。

## 2026-08-17 15:23+08:00 second factor/throughput batch active

- 实施提交 `7551e3fcc55aa2964dd8eff2bed30e7ab47400f7` 已部署到 clean/idle fixed；`bash -n`、JSON、
  py_compile、focused `16/16` 与 full regression `197/197 PASS`（`93.710 s`，wall `1:34.83`，
  MaxRSS `1,133,084 KiB`，swaps 0）。
- baseline Fingerprint/raw/Factor/observed step metric 为
  `2120635803`、`4,454,178/3,735,087/40,395,436`、`7.334e8/4.761e12`、`12.834849 s/iter`。
  全新 v2 roots；唯一 supervisor PID `1567638`，首根 `presparsify2` 于 15:23:11 启动，stderr 0。
- 启动 available `113.951 GiB`、si/so/PSI `0/0/0`。活动期 checkout 冻结，后两根仅由同一进程
  串行启动；约 30--45 分钟/事件检查。cloud `4139552` 15:19 仍 RUNNING、iteration 338、stderr 0，
  约 2 小时低频检查且未触碰。

## 2026-08-17 15:16+08:00 second factor/throughput batch ready locally

- 第二批仅三根：`PreSparsify=2`、`BarOrder=1`、Threads 32；其余 PreDual/Aggregate/Presolve/AggFill
  已按历史结构/时间证据淘汰。共同保持 Base/744、NF1、Scale2、relaxed tolerance、Crossover 0、5 steps。
- baseline 为第一批同机 `nf1_scaleauto` 5-step；v2 结构降低门槛 `5%`，配对 step-time 降低门槛
  `10%`。summary/runner 对 case tags、profiles、identity、runtime、factor、rc/stderr fail-closed。
- 本地 JSON/compile/diff 与 focused `16/16 PASS`。尚未提交/部署/启动；fixed idle clean `4f195d4`，
  cloud `4139552` 未触碰。

## 2026-08-17 15:10+08:00 factor batch 1 complete / no shortlist / cloud round 39

- 三根 744h×5-step screens 全部 identity valid、status 7、rc 2、audit 0、stderr/swaps 0；无任何
  checkpoint/科学产物。campaign 约 `38:19`，case wall 约 `12:41--12:44`、MaxRSS
  `19.68--20.50M KiB`。
- NF0+Scale2 与 NF0+ScaleAuto 的 Factor NZ/Ops 相对 baseline 为 `1.003545/1.031506`；
  NF1+ScaleAuto 为 `1.0/1.0`。summary `NO_MATERIAL_FACTOR_IMPROVEMENT`，shortlist 空。
- fixed 无 solver，available 约 `114.0 GiB`、si/so/PSI 0、checkout clean `4f195d4`。下一轮只审计/
  短测更直接的 sparsification/fill/order 候选，不运行完整 744。
- cloud round 39：iteration 338、runtime `996,833.092 s`，wall `999,673 s`、allocated
  `26,657.947 core-hours`、actual CPU `4,169.626 h`、efficiency `15.6412%`、recent-20 `52.922 min`；
  ledger 40 records SHA256 `75c7edd5...2108`，stderr 0、无终态/Stage B。

## 2026-08-17 14:26+08:00 serial factor screens active

- exact head `4f195d4353b76ce76c710eb5c7ba3c467a4d494c` 已部署；server bash/profile/compile、focused
  `10/10`、full `194/194 PASS`。baseline Fingerprint/LP/scientific identity 与 Factor 字段全通过。
- 全新 roots `relaxed_factor_screens_v0817_v1`；supervisor PID `1494933`，第一根 `nf0_scale2`
  wrapper/Python `1495063/1495064`，14:25:49 启动。3 根只串行，每根 Base/744、5 Barrier steps、
  Crossover 0，不是 checkpoint/科学结果。
- 启动 available `113.97 GiB`、si/so/PSI 0、磁盘约 `3.96 TB` 可用、stderr 0。活动期间 checkout
  冻结 `4f195d4`；15--20 分钟或事件低频检查。cloud `4139552` 未触碰。

## 2026-08-17 14:20+08:00 factor-screen deployment preflight and data-root freeze

- fixed 已 clean/idle fast-forward `613abe8d...6723`；`bash -n`、profile JSON、`py_compile`、focused
  `10/10 PASS`。显式设置 current data/CF/hydro/raw-GRFR/wave roots 后 full regression
  `194/194 PASS`（`95.60 s`，MaxRSS `1,115,900 KiB`）。缺外部根的两次尝试 fail-fast，无 solver。
- 本地已最小修复 factor-screen runner，使其冻结五个 current 外部数据根并允许显式覆盖；静态 focused
  discovery `10/10 PASS`、diff check PASS。该补丁尚待提交、双推送与 server redeploy，screens 未启动。
- fixed 当前无 solver；cloud `4139552` 未触碰。下一步部署补丁并重跑验证，再启动唯一串行 screens。

## 2026-08-17 14:14+08:00 Base 2160 MEM_LIMIT / fixed idle / cloud round 38

- Base/2160 原始 LP `12,520,914 rows / 10,398,783 cols / 126,724,678 nnz`，build `884.643 s`；
  Presolve `2,214.94 s` 后 `9,527,353 / 8,288,888 / 106,864,030`，Ordering `565.03 s`。
- `SoftMemLimit=80 GiB` 在 Barrier 0 iterations 前触发 `MEM_LIMIT/status 17`；solver `2,800.735 s`、
  wrapper wall `1:01:40`、MaxRSS `72,659,300 KiB`、rc 2、stderr/swaps 0。`solution_count=0`、objective
  null；无 QC/result/checkpoint/BarX/BarPi，只能作为内存与 fill-in 工程证据。
- campaign 14:03:30 complete；fixed 无 CISPO/Gurobi/campaign 进程，checkout clean `902b1672...ff36`。
  available RAM 约 `114.0 GiB`、si/so/PSI 0。下一步不直接抬高 SoftMem 重跑 2160，先部署并执行
  串行 744h lower-factor screens。
- cloud `4139552` iteration 336、runtime `990,741.973 s`；round 38 wall `995,707 s`、allocated
  `26,552.187 core-hours`、actual CPU `4,153.300 h`、efficiency `15.6420%`、MaxRSS `362.913 GiB`、
  recent-20 `53.040 min`。ledger 39 records SHA256 `932b7d8a...bd534`；stderr 0、无 terminal/checkpoint，
  未取消/改参/启 Stage B。

## 2026-08-17 13:09+08:00 Base 1488 complete / Base 2160 active / cloud round 37

- Base/1488 Barrier `OPTIMAL`，143 iterations、solver `25,834.260 s`、wall `7:22:57`、MaxRSS
  `55,460,664 KiB`、rc/stderr/swaps `0/0/0`。checkpoint gate PASS；BarX/BarPi entries
  `7,236,351/8,648,849` 且 size/SHA 完整，LP Fingerprint `893131507`、input manifest 与 order digests
  齐全。身份仅 `ENGINEERING_BARRIER_CHECKPOINT_ONLY`，可 deferred crossover，不是科学结果。
- strict contract `HARD_FAIL`；engineering QC `54/58`，失败 wave `0.850 MW`、strict bidirectionality、
  reservoir `11,280 m3/3.775 m3`。power balance `2.315 kW`，storage overlap 仅 period load `0.0952%`，
  interprov opposing `0.259%`、excess loss `0.00641%`，load-center bidirectional `0.891%`。碳/CCS/DAC、
  备用、惯量、网络容量、储能状态、水文级联与成本闭合；BarPi `46,128/3,366` rows 仅工程使用。
- campaign 13:01:45 串行启动唯一 Base/2160 PID `1387308/1387309`，start hour 2880；13:08 build RSS
  `4.14 GiB`、available 约 `110 GiB`、si/so/PSI 0、stderr 0。checkout clean `902b1672...ff36`。
- cloud `4139552` iteration 335、runtime `987,914.783 s`；round 37 wall `991,984 s`、allocated
  `26,452.907 core-hours`、actual CPU `4,137.397 h`、efficiency `15.6406%`、recent-20 `53.550 min`；
  ledger 38 records SHA256 `c31d779c...e0df`，stderr 0、无 terminal/checkpoint/Stage B。

## 2026-08-17 11:57+08:00 factor shortlist audit ready locally

- 新汇总器按 LP Fingerprint/矩阵/scientific/scenario identity、rc/stderr、5 iterations、numerical trouble
  与完整 Factor 指标 fail-closed；Factor Ops/NZ 至少降低 `5%` 才进入 engineering shortlist。
- runner 在三根 screen 前先审计当前 NF1+Scale2 Base/744 baseline，末尾输出 JSON/CSV；不完整分别
  exit `98/99`。shortlist 不自动成为 winner，完整 744 exact macro A/B 仍强制。
- focused tests `11/11 PASS`、`py_compile` PASS；尚未部署，活动 fixed/cloud 未触碰。

## 2026-08-17 11:52+08:00 cloud round 36 / fixed iteration 120

- fixed Base/1488 iteration 120、runtime `21,739.318 s`，primal/dual/compl
  `0.050274/0.000789619/0.027934`；近 20/10 步 `169.03/169.75 s/step`，12 h 投影 iteration
  `247.0`。RSS `55,459,960 KiB`，available 约 `61.1 GiB`、swap used 约 `984 MiB`，si/so/PSI 0、
  stderr 0、无终态/checkpoint，唯一 solver 正常。
- cloud `4139552` RUNNING，iteration 334、runtime `984,705.405 s`，primal/dual/compl
  `1.213709/9.858e-7/0.104884`；round 36 wall `988,357 s`、allocated `26,356.187 core-hours`、
  actual CPU `4,122.200 h`、efficiency `15.6404%`、MaxRSS `362.913 GiB`、recent-20 `53.255 min`。
  ledger 37 records SHA256 `cbf0311e...33710`；stderr 0、无 terminal/checkpoint、未启 Stage B。
- 下一次 fixed 为 iteration 130/终态，cloud 约一小时；活动 campaign 退出前不部署或并发。

## 2026-08-17 11:05+08:00 phase trajectory audit extended locally

- `collect_solver_run()` 现为每个 solver phase 自动记录 iteration/runtime span、observed seconds per
  iteration、complementarity 及末端 primal/dual objective gap；factor screen 不再依赖人工日志摘录。
- focused tests `8/8 PASS`、`py_compile` PASS、既有 1 h telemetry 实读 PASS。尚未部署，活动
  fixed/cloud 作业完全未触碰；待 campaign idle 后随 lower-factor screens 一并 fast-forward/regression。

## 2026-08-17 10:59+08:00 cloud round 35 / fixed iteration 100

- fixed Base/1488 iteration 100、runtime `18,358.690 s`，primal/dual/compl
  `0.562716/0.00180162/0.402016`；0--100/50--100/75--100/90--100 平均
  `168.69/166.88/168.82/169.06 s/step`，按近期窗口 12 h 约到 iteration `247.2`。残差量级约对应
  strict Base/744 iteration `67/96/122`；raw objective gap `5.432e6`，不跨 horizon 强行比较。
- fixed process RSS `55,452,788 KiB`，available 约 `61.1 GiB`，swap used 约 `984 MiB` 但 si/so 0、
  memory PSI 0；stderr 0、无终态/checkpoint、唯一 solver 安全运行。
- cloud `4139552` RUNNING，iteration 333、runtime `981,713.748 s`，primal/dual/compl
  `1.246258/1.002e-6/0.107341`；round 35 wall `985,280 s`、allocated `26,274.133 core-hours`、
  actual CPU `4,109.163 h`、efficiency `15.6396%`、MaxRSS `362.913 GiB`、recent-20 `53.302 min`。
  resource ledger 36 records SHA256 `64d80b8c...db6e87`；stderr 0、无 terminal/checkpoint、未启 Stage B。
- 继续低频：fixed 每 10 iteration/15--30 min 或事件检查，cloud 约每小时且只在新 iteration 记账；
  正常中途点不再逐次写文档。活动 campaign 退出前不部署或启动 lower-factor screens。

## 2026-08-17 09:57+08:00 cloud round 34 / fixed iteration 79

- cloud `4139552` RUNNING，iteration 332、runtime `978,908.233 s`，primal/dual/compl
  `1.274926/1.023e-6/0.109716`；wall `981,492 s`、allocated `26,173.120 core-hours`、actual CPU
  `4,092.853 h`、efficiency `15.6376%`、MaxRSS `362.913 GiB`，最近 20 步 `53.291 min`。
  audit 35 records SHA256 `29960f1e...aad17`；stderr 0、无 terminal/checkpoint、未启 Stage B。
- fixed Base/1488 iteration 79、runtime `14,822.968 s`，primal/dual/compl
  `10.206400/0.00308381/7.745108`；RSS 稳定、stderr 0，继续唯一 solver 到 100/终态。

## 2026-08-17 09:44+08:00 lower-factor screens prepared locally

- 三个配对 Base/744 profiles：`NF0+Scale2`、`NF1+ScaleAuto`、`NF0+ScaleAuto`；共同
  `BarIterLimit=5`、TimeLimit 2 h、SoftMem 40 GiB，其余保持 relaxed winner 合同。
- 串行 runner 要求 clean/no-solver、available ≥64 GiB、si/so/PSI 0，记录完整 factor/resource
  证据且不导出 checkpoint。配置/配对测试 `1/1 PASS`；server bash/profile/full regression 待 idle。
- 当前 fixed/cloud 未部署或改参；活动 campaign 退出前严禁启动 screens。

## 2026-08-17 09:41+08:00 future campaign checkpoint gate fixed locally

- 旧 1488→2160 编排仅按 manifest 存在性放行；现在本地新增 fail-closed eligibility/vector-integrity
  gate，recovery-only、status 不符、向量缺失/size/SHA256 不符均停止。相关 unittest `4/4 PASS`。
- 尚未部署，活动 fixed checkout、Base/1488 和 cloud `4139552` 均未修改。必须等唯一 solver 与
  campaign 退出后才能 fast-forward，并补 server `bash -n`、focused/full regression。

## 2026-08-17 09:32+08:00 cloud round 33 / fixed iteration 70

- cloud `4139552` 仍为 `RUNNING`，iteration 331、runtime `975,911.936 s`；primal/dual/compl
  `1.336420/1.053e-6/0.113863`。wall `980,022 s`、allocated `26,133.920 core-hours`、actual CPU
  `4,086.896 h`、efficiency `15.6383%`、MaxRSS `362.913 GiB`，最近 20 步 `53.414 min`。
  resource audit 34 records SHA256 `fc88fd29...e48045c`；stderr 0、无终态/checkpoint，未启 Stage B。
- fixed Base/1488 到 iteration 70，runtime `13,316.273 s`，primal/dual/compl
  `19.574527/0.00930446/18.290173`；process RSS 约 `55,451,552 KiB`、stderr 0，仍安全。
- 当前 cloud 严格 profile 不能在运行中改参。近期衰减只支持费用预警：primal 到 relaxed-744
  终点量级约 5 天，objective gap 到 1,000 量级约 8--9 天；不是可靠完成 ETA。保持不取消，
  fixed 继续到 100/终态，下一轮转入 lower-factor 参数 screen。

## 2026-08-17 08:37+08:00 Base 1488 iteration 50

- iteration 50 runtime `10,014.836 s`；primal/dual/compl `229.055/0.172288/262.879`。
  与 Base/744 对齐分别相当于 iteration `48/58/65`，objective gap 相当于 61，综合约领先
  10--15 步；同 iteration gap 小 `157.5x`。
- 当前平均步长推算 12 h 可到 iteration `244--255`。相对 744 的 263 步仍是边界案例；继续到
  100/终态，不取消、不改参。
- RSS `55,428,232 KiB`、available 约 61.0 GiB、swap used 约 984 MiB，si/so 0、memory PSI 0、
  stderr 0；当前安全，下一任务不得并发。

## 2026-08-17 07:40+08:00 cloud round 32 / fixed iteration 30

- cloud `4139552` RUNNING，iteration 329、runtime `969,935.080 s`，primal/dual/compl
  `1.404886/1.110e-6/0.119628`；wall `973,314 s`、allocated `25,955.040 core-hours`、
  actual CPU `4,058.406 h`、efficiency `15.6363%`、MaxRSS `362.913 GiB`，最近 20 步
  `53.686 min`。resource audit 33 records SHA256 `0752c628...e467326d`；stderr 0、无终态/
  checkpoint，未启 Stage B。
- fixed Base/1488 到 iteration 30，runtime `6,588.139 s`，primal/dual/compl
  `2.223e6/702.46/5.926e5`；内存不变、stderr 0，继续到 50。

## 2026-08-17 07:35+08:00 next-candidate factor audit

- 只读历史 24 h 表明 `NumericFocus=0 + ScaleFlag=-1` 相对 NF2/Scale2 将 Factor NZ/Ops
  约降低 `8.3%/7.5%`，Barrier `18.99 s` 对 `57.95 s`；旧严格合同因
  `ConstrVio=0.04788` 拒绝，但 objective 相对差约 `1.54e-7`。
- 下一轮应在 current model / `BarConvTol=1e-2` 下拆分 NF0 与 auto scaling，并先用 744
  短迭代比较 Factor NZ/Ops；`AggFill=0` 历史收益不足 2%，`PreSparsify=2` 虽稀疏却更慢，均非
  首选完整 solve。当前 Base/1488 和 cloud job 未改，活动 campaign 退出前不启动候选。

## 2026-08-17 07:25+08:00 Base 1488 iteration 25

- iteration 25 runtime `5,731.421 s`；0--25 平均 `169.69 s/step`，primal/dual/complementarity
  `2.275e8/1.364e5/5.068e7`。相对 Base/744 同步点，primal 高 32.6% 而 dual/compl 低约
  `30x/533x`；继续到 50，不能按 263 步直接外推。
- solver current/max memory `45.07/58.29 GiB`、process RSS 约 52.8 GiB；host available 约
  61.1 GiB、si/so 0、memory PSI 0、stderr 0。当前安全；2160 仍须退出后重新满足 96 GiB 门禁。

## 2026-08-17 07:03+08:00 Base 1488 validates cloud 8760 per-step scaling

- cloud 8760 Factor NZ/Ops `3.395e10/1.931e15`，fixed 1488 为 `3.866e9/1.060e14`，比值
  `8.78x/18.22x`；dense cols `37,696/36,218`。cloud 最近实际 `3216.5 s/step` 按 Factor Ops
  折算 fixed 为 `176.6 s/step`，与 fixed 0--16 实测 `171.0 s/step` 仅差约 3.2%。
- 结论：1488 是当前 LP 的可信全年单步成本代理；fill-in 决定单步约 50--55 min。放宽容差只可能
  通过减少迭代数降总时间。继续当前 1488 到 25/50/终态实测，不改参、不并发。

## 2026-08-17 07:01+08:00 cloud round 31 / Base 1488 iteration 16

- ParaCloud `4139552` iteration 328、runtime `966,756.149 s`，primal/dual/complementarity
  `1.450925/1.129e-6/0.122696`。round 31 wall `970,967 s`、allocated `25,892.453 core-hours`、
  actual CPU `4,048.863 h`、efficiency `15.6372%`、MaxRSS `362.913 GiB`、最近 20 步
  `53.608 min`；32 records SHA256 `223757e0...e391`。stderr 0、无 terminal/checkpoint，未改任务。
- fixed Base/1488 iteration 16、runtime `4,225.346 s`；0--16 平均约 `171.00 s/step`，solver
  current/max memory `45.07/58.29 GiB`、stderr 0。继续唯一 solver 到 iteration 25 门点。

## 2026-08-17 06:21+08:00 Base 1488 factorization / Barrier start

- Base/1488 raw LP `7,236,351 vars / 8,648,849 rows / 87,364,792 nnz`；build 约 10.4 min，
  presolve `1,080.17 s` 后为 `6,564,794 / 5,761,274 / 73,637,736`，ordering `322.03 s`。
  dense cols 36,218、Factor NZ `3.866e9`（约 36 GB）、Factor Ops `1.060e14`（约 200 s/iter）。
- 相对同 Base/744 NF1 winner，presolved nnz `2.36x`，但 Factor NZ/Ops `5.27x/22.26x`；长时域
  性能瓶颈已定位为 fill-in/dense temporal coupling，不是仅靠容差能消除。
- iteration 0/1/2 runtime `1,489.26/1,595.89/1,855.80 s`；solver current/max memory
  `45.07/58.29 GiB`，stderr 0，主机无 swap I/O/PSI。继续唯一求解，至少 5--10 步后再估 12 h 终点。
- 审计发现 campaign 的 2160 gate 仅检查 checkpoint manifest 存在；若 1488 TIME_LIMIT 后只保存
  `INCOMPLETE_BARRIER_RECOVERY`，也会被误放行。活动脚本不改；本轮结束后应要求 manifest
  `deferred_crossover_eligible=true` 并加测试。

## 2026-08-17 05:47+08:00 cloud round 30 / Base 1488 building

- ParaCloud `4139552` 新落盘 Barrier iteration 326/327；最新 runtime `963,537.897 s`，
  primal/dual/complementarity `1.529887/1.166e-6/0.128042`。round 30 wall `966,523 s`、allocated
  `25,773.947 core-hours`、actual CPU `4,030.069 h`、efficiency `15.6362%`、MaxRSS
  `362.913 GiB`、最近 20 步 `53.232 min`；31 records SHA256 `5ea6005a...840c9`。stderr 0、
  无 terminal/checkpoint，未取消、未改参、未启动 Stage B。
- fixed Base/1488 PID `3899905/3899906` 仍为唯一 solver 链，05:46 尚在 build，stderr 0；继续等待
  Gurobi/presolve/Barrier，不切 checkout、不启动第二 solver。

## 2026-08-17 05:41+08:00 V5 744 terminal / Base 1488 active

- V5/744 于 05:38:39 rc 0：solver `OPTIMAL`，Barrier `305 iterations / 4,520.108 s`，wrapper
  wall `1:21:54`、stderr 0、MaxRSS `21,285,692 KiB`、swaps 0。LP 为 3,894,744 variables、
  4,636,251 constraints、41,327,437 nonzeros；完整 `BarX/BarPi`、LP Fingerprint、ordering digest、
  layered identity 与 hashes 均已保存，checkpoint 可在精确重建 LP 后延期 Crossover。
- 该解是工程检查点，不是科学结果：strict QC `HARD_FAIL`，58 个物理 hard checks 中仅
  `reservoir_transition` 失败，最大残差 `11,917.821 m3`；power balance `2.362e-7 GW`、省间双向流 0、
  storage overlap `1.745e-5 GWh`，其余网络、备用、惯量、碳/CCS 和成本账目通过；没有 scientific
  result manifest/planning state/basis。
- campaign 于 05:38:42 自动串行启动唯一 Base/1488：PID `3899905/3899906`，start hour 3624，
  output `relaxed_barrier_continuation_v0817_v5/base_1488h_bctol1e2_numeric1`，long NF1 winner profile。
  05:41 仍在 build，stderr 0、available RAM 约 111 GiB、si/so 0、memory PSI 0；固定 checkout clean
  `902b1672...ff36`。无第二 solver；仅在 1488 checkpoint 存在时才允许自动进入 Base/2160。
- ParaCloud `4139552` 未取消、未改参、未启动 Stage B；沿用 round 29 证据直到出现新 iteration。

## 2026-08-17 04:18+08:00 exact macro winner / V5 744 start / cloud round 29

- v5 exact A/B 成功：`5e-2/NF2` 与 `1e-2/NF2` 分别因宏观 operation-account L1
  `29.64%/10.04%` 等失败；`1e-2/NF1` 为唯一 `MACRO_PASS`，objective/capacity/generation/
  carbon/operation 差异为 `2.93e-9/1.33e-8/0.001056/8.41e-10/1.92e-6`。winner Barrier
  `4,275.73 s`，较 strict total `53,489.07 s` 快 `92.0%`，较 strict Barrier `7,734.65 s`
  快 `44.7%`。
- 唯一 solver 已于 04:16:42 启动 V5/744 Barrier-only：PID `3569191/3569192`，output
  `relaxed_barrier_continuation_v0817_v5/v5_744h_bctol1e2_numeric1`；profile 为 Method 2、16 threads、
  Presolve 2、Crossover 0、BarConvTol `1e-2`、Feas/Opt `1e-5`、NF1、Scale2、TimeLimit 6h、
  SoftMem 40 GiB。启动时约 113.6 GiB available、无实时 swap I/O/PSI、stderr 0。
- ParaCloud `4139552` 未触碰：iteration 325、runtime `957,363.69 s`；round 29 wall
  `961,177 s`、allocated `25,631.387 core-hours`、actual CPU `4,007.857 h`、efficiency
  `15.6365%`、最近 20 步 `53.129 min`、MaxRSS `362.913 GiB`。30 records SHA256
  `26a9903d...7a61e69`；stderr 0、无 terminal/checkpoint。

## 2026-08-17 04:16+08:00 v4 exact-macro second fail-closed / control-dir fix

- fixed server 已部署 clean `5161dd0`，`bash -n`、focused `6/6` 与完整 `187/187 PASS`
  (`94.975 s`)。v4 正确复用三候选且 import 问题已消失，但复用分支未创建候选 control 子目录，
  shell 在 stdout 重定向前即失败；故仍为 `NO_MACRO_PASS`，无 `macro_comparison.json`、无 solver。
- 最小补丁在每个候选循环入口无条件 `mkdir -p "$CONTROL_ROOT/$tag"`；本地 focused `6/6 PASS`，
  新脚本 SHA256 `21e67deb...ff79b07`。v4 保留为编排失败证据；下一步双推送、server `bash -n`
  后在全新 v5 根第三次执行 exact macro，不重算任何 744 候选。

## 2026-08-17 04:12+08:00 strict 744 accepted / exact-macro orchestration fix

- fixed strict Base/744 reference 正式 `OPTIMAL + QC PASS + 58/58 + current input manifest + valid
  68-file result manifest`。solver `53,489.07 s`：Barrier `7,734.65 s`、Crossover `45,468.01 s`，
  objective `2,361,958.416203 million CNY`；wrapper rc 0、stderr 0、wall `14:57:39`、MaxRSS
  `20,617,928 KiB`、swap 0。`ConstrVio/BoundVio/DualVio` 为
  `9.74e-8/8.50e-8/8.85e-8`，宏观电力、网络、储能、水电、备用、惯量、碳与成本检查均闭合；
  仍仅为 `TEST_ONLY_TRUNCATED_HORIZON`。
- v3 exact-macro campaign fail-closed 且未启动 solver：supervisor symlink 被重复运行逻辑误报为已有输出，
  audit 脚本又因缺少 frozen repo `PYTHONPATH` 报 `ModuleNotFoundError`，故 `NO_MACRO_PASS`。
  已最小修复 campaign：仅复用带完整 engineering contract 的 supervisor symlink，并为独立 audit
  显式注入 repo `PYTHONPATH`；本地 focused `6/6 PASS`，脚本 SHA256
  `95e177ee...5a17132`。下一步双推送、fixed server `bash -n` 后在全新 v4 control/output 根只重跑
  exact macro，再按 winner 串行进入 V5/744 与 Base/1488/2160。

## 2026-08-17 03:01+08:00 cloud round 28 / fixed cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 324、runtime `954,056.89 s`；round 28 为 wall
  `956,593 s`、allocated `25,509.147 core-hours`、actual CPU `3,988.565 h`、CPU efficiency
  `15.6358%`、MaxRSS `362.913 GiB`、iteration 304--324 平均 `53.113 min`。29 records SHA256
  `b9d852b3...31951f87`；stderr 0、无 terminal/checkpoint。最新单步约 `57.12 min`，primal 与
  complementarity 继续下降。
- fixed strict quad cleanup 为 iteration `1,009,728`、runtime `49,698.19 s`、primal 0、dual
  `1.02e3`；wrapper/v3 supervisor 存活、仍只有一个 solver，continuation 输出根 absent。

## 2026-08-17 02:07+08:00 cloud round 27 / fixed cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 323、runtime `950,629.60 s`；round 27 为 wall
  `953,368 s`、allocated `25,423.147 core-hours`、actual CPU `3,975.420 h`、CPU efficiency
  `15.6370%`、MaxRSS `362.913 GiB`、iteration 303--323 平均 `52.990 min`。28 records SHA256
  `1ac421f7...534f0b8`；stderr 0、无 terminal/checkpoint。最新单步约 `53.86 min`，primal 与
  complementarity 继续下降。
- fixed strict quad cleanup 为 iteration `995,574`、runtime `46,496.02 s`、primal 0、dual
  `9.22e2`；wrapper/v3 supervisor 存活、仍只有一个 solver，continuation 输出根 absent。

## 2026-08-17 01:15+08:00 cloud round 26 / fixed cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 322、runtime `947,398.04 s`；round 26 为 wall
  `950,224 s`、allocated `25,339.307 core-hours`、actual CPU `3,962.390 h`、CPU efficiency
  `15.6373%`、MaxRSS `362.913 GiB`、iteration 302--322 平均 `52.831 min`。27 records SHA256
  `ec248a3b...73ee91`；stderr 0、无 terminal/checkpoint。最新单步约 `60.04 min`，primal 与
  complementarity 继续下降。
- fixed strict quad cleanup 为 iteration `980,379`、runtime `43,298.54 s`、primal 0、dual
  `3.23e2`；wrapper/v3 supervisor 存活、仍只有一个 solver，continuation 输出根 absent。

## 2026-08-17 00:14+08:00 cloud round 25 / fixed cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 321、runtime `943,795.68 s`；round 25 为 wall
  `946,575 s`、allocated `25,242.000 core-hours`、actual CPU `3,947.624 h`、CPU efficiency
  `15.6391%`、MaxRSS `362.913 GiB`、iteration 301--321 平均 `52.246 min`。26 records SHA256
  `05a7a568...2f52f7`；stderr 0、无 terminal/checkpoint。最新单步约 `55.02 min`，primal 与
  complementarity 继续下降。
- fixed strict quad cleanup 为 iteration `962,785`、runtime `39,637.75 s`、primal 0、dual
  `2.55e3`；wrapper/v3 supervisor 存活、仍只有一个 solver，continuation 输出根 absent。

## 2026-08-16 23:50+08:00 cloud round 24 / fixed cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 320、runtime `940,494.22 s`；round 24 为 wall
  `945,131 s`、allocated `25,203.493 core-hours`、actual CPU `3,942.270 h`、CPU efficiency
  `15.6418%`、MaxRSS `362.913 GiB`、iteration 300--320 平均 `52.071 min`。25 records SHA256
  `efb6bd58...f51a7`；stderr 0、无 terminal/checkpoint。最新单步约 `68.32 min`，但 primal 与
  complementarity 继续下降，尚无正式停滞或失败证据。
- fixed strict quad cleanup 为 iteration `955,777`、runtime `38,214.01 s`、primal 0、dual
  `1.54e4`；wrapper/v3 supervisor 存活、仍只有一个 solver，终态文件 absent。

## 2026-08-16 23:09+08:00 cloud round 23 / fixed cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 319、runtime `936,395.20 s`；round 23 为 wall
  `942,654 s`、allocated `25,137.440 core-hours`、actual CPU `3,931.546 h`、CPU efficiency
  `15.6402%`、MaxRSS `362.913 GiB`、iteration 299--319 平均 `51.167 min`。24 records SHA256
  `d203d675...fa7b`；stderr 0、无 terminal/checkpoint。
- fixed strict quad cleanup 为 iteration `942,842`、runtime `35,770.00 s`、primal 0、dual
  `1.99e5`；wrapper/v3 supervisor 存活、仍只有一个 solver，终态文件 absent。

## 2026-08-16 21:45+08:00 cloud round 22 / fixed cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 318、runtime `933,326.74 s`；round 22 为 wall
  `937,651 s`、allocated `25,004.027 core-hours`、actual CPU `3,911.908 h`、CPU efficiency
  `15.6451%`、MaxRSS `362.913 GiB`、iteration 298--318 平均 `51.532 min`。23 records SHA256
  `5db4ac89...50a0`；stderr 0、无 terminal/checkpoint。
- fixed strict quad cleanup 为 iteration `917,738`、runtime `30,759.68 s`、primal 0、dual
  `8.19e6`；wrapper/v3 supervisor 存活、仍只有一个 solver，终态文件 absent。

## 2026-08-16 20:23+08:00 cloud round 21 / fixed cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 317、runtime `930,000.70 s`；round 21 为 wall
  `932,693 s`、allocated `24,871.813 core-hours`、actual CPU `3,890.998 h`、CPU efficiency
  `15.6442%`、MaxRSS `362.913 GiB`、iteration 297--317 平均 `51.272 min`。22 records SHA256
  `bf039d69...d7de`；stderr 0、无 terminal/checkpoint。
- fixed strict quad cleanup 为 iteration `892,970`、runtime `25,778 s`、primal 0、dual `2.51e6`；
  wrapper/v3 supervisor 存活、仍只有一个 solver，终态文件 absent。

## 2026-08-16 19:57+08:00 strict runtime 超过旧成功根

- 当前 strict runtime `24,224 s` 且未结束，已超过旧成功根 `24,156.53 s`；iteration `885,507`、
  primal 0、dual `2.89e5`、stderr 0。
- 本次 Barrier 比旧根快约 `3,407.9 s`，但 Barrier 后 Crossover/cleanup 已至少 `16,489.4 s`，
  相对旧完整 Crossover `12,672.69 s` 慢约 `30.1%`，端到端收益已耗尽。比较跨数据版本，仅为
  历史工程参照；继续运行并等待正式 status。云 job 不变。

## 2026-08-16 19:36+08:00 cloud round 20 / fixed low-dual cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 316、runtime `927,093.65 s`；round 20 为 wall
  `929,885 s`、allocated `24,796.933 core-hours`、actual CPU `3,879.081 h`、CPU efficiency
  `15.6434%`、MaxRSS `362.913 GiB`、iteration 296--316 平均 `51.638 min`。21 records SHA256
  `278f0396...e639`；stderr 0、无 terminal/checkpoint。
- fixed strict quad cleanup 为 iteration `879,136`、runtime `22,956 s`、primal 0、dual `4.73e4`；
  wrapper/v3 supervisor 存活、仍只有一个 solver，终态文件 absent。

## 2026-08-16 18:38+08:00 cloud round 19 / fixed dual recovery

- ParaCloud `4139552` 未触碰：Barrier iteration 315、runtime `923,654.91 s`；round 19 为 wall
  `926,381 s`、allocated `24,703.493 core-hours`、actual CPU `3,864.724 h`、CPU efficiency
  `15.6444%`、MaxRSS `362.913 GiB`、iteration 295--315 平均 `51.837 min`。20 records SHA256
  `19273e36...c437`；stderr 0、无 terminal/checkpoint。
- fixed strict quad 已从 `1e10--1e12` dual 段恢复；当前 iteration `859,888`、runtime `19,483 s`、
  primal 0、dual `2.05e6`、stderr 0，wrapper/v3 supervisor 存活、仍只有一个 solver。

## 2026-08-16 18:04+08:00 strict quad 轨迹偏离旧成功根

- 定量纠正：旧成功根 quad 后最大 dual `1.91e8`，仅 2 个采样 `>=1e8`、无 `>=1e9`；当前根
  quad 后最大 `6.63e12`，41/23/17/10 个采样分别 `>=1e8/1e9/1e10/1e11`。两根只有自动
  `drop basis variable + switch to quad` 动作相同，后续数值轨迹明显不同，不能沿用旧根 ETA。
- 当前 iteration `848,783`、runtime `17,444 s`、primal 0、dual `3.96e10`、objective 仍下降；
  wrapper 存活、stderr 0、无正式 failure/终态。按合同不取消、不并发，但提高数值风险等级并等待
  正式 status。云 job 不变。

## 2026-08-16 17:51+08:00 cloud round 18 / fixed quad cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 314、runtime `920,799.47 s`；round 18 为 wall
  `923,578 s`、allocated `24,628.747 core-hours`、actual CPU `3,852.752 h`、CPU efficiency
  `15.6433%`、MaxRSS `362.913 GiB`、iteration 294--314 平均 `51.766 min`。19 records SHA256
  `90fc64d6...0498`；stderr 0、无 terminal/checkpoint。
- fixed strict quad cleanup 为 iteration `844,413`、runtime `16,683 s`、primal 0、dual `2.69e8`；
  wrapper/v3 supervisor 存活、仍只有一个 solver，终态文件 absent。

## 2026-08-16 17:06+08:00 cloud round 17 / fixed quad cleanup

- ParaCloud `4139552` 未修改：Barrier iteration 313、runtime `917,751.15 s`；round 17 为 wall
  `920,881 s`、allocated `24,556.827 core-hours`、actual CPU `3,841.487 h`、CPU efficiency
  `15.6433%`、MaxRSS `362.913 GiB`、最近 20 步平均 `52.099 min`。18 records SHA256
  `a7ab2c58...11ba`；stderr 0、无 terminal/checkpoint。
- fixed strict quad cleanup 为 iteration `828,761`、runtime `13,981 s`、primal 0、dual `2.73e5`；
  wrapper/v3 supervisor 存活，仍只有一个 solver，终态文件 absent。

## 2026-08-16 16:58+08:00 strict cleanup 切换 quad precision

- iteration `823,548`、runtime `13,224 s` 后，Gurobi 自动报告 `1 variables dropped from basis` 和
  `switch to quad precision`；旧成功根存在完全相同保护动作，当前不判失败或取消。
- quad 后约 `7 pivots/s`；iteration `825,303`、runtime `13,464 s` 时 primal 0、dual `1.14e5`、
  objective `2,362,020.1 million CNY`。stderr 0、wrapper 存活、终态文件 absent、只有一个 solver；
  继续等待正式 Crossover status 与强终态审计。云 job 不变。

## 2026-08-16 16:27+08:00 strict cleanup / cloud round 16

- fixed strict simplex 约从 iteration `788,784` 推进到 `792,828`，runtime `11,448→11,630 s`；
  primal infeasibility 保持 0，dual infeasibility 在 `7.47e3--9.29e8` 非单调。旧成功根同一相对
  阶段也曾摆动到 `1.09e9` 后最终 OPTIMAL，当前暂无新增 numerical failure 证据，但仍不能预测
  cleanup 完成时间。
- wrapper/Python 与 v3 supervisor 均存活，stderr 0、终态三文件 absent；fixed 仍只有一个 solver，
  available RAM 约 `100 GiB`、无实时 swap I/O、memory PSI 0。
- ParaCloud `4139552` 未触碰：Barrier iteration 312、runtime `914,959.12 s`；round 16 为 wall
  `918,306 s`、allocated `24,488.16 core-hours`、actual CPU `3,830.451 h`、CPU efficiency
  `15.6421%`、MaxRSS `362.913 GiB`、iteration 292--312 平均 `52.330 min`。17 records SHA256
  `65b3c549...a59c9`；stderr 0、无 terminal/checkpoint。

## 2026-08-16 16:20+08:00 Crossover push complete / simplex cleanup

- strict Crossover basis 约 `255 s`；DPush `841,200→0` 用 `2,565 s`，PPush `274,055→0` 用
  `602 s`。push complete runtime `11,177 s`，PInf/DInf `2.741902/1.751704e8`，已进入 simplex
  cleanup；iteration `782,690` primal infeasibility 已降至 `1.19e-3`，dual cleanup 尚未完成。
- 旧成功根 push complete runtime `13,707 s`，当前仍快 `2,530 s`；但旧 PInf/DInf 仅
  `0.576694/6.499e3`，当前 cleanup 起点更难，不能预测最终净加速。
- stderr 0、terminal files absent；RSS 约 `13.57 GiB`、available RAM 约 `100 GiB`、memory PSI
  0。仍只有一个 fixed solver，v3 supervisor 继续等待 wrapper；ParaCloud 不变。

## 2026-08-16 15:39+08:00 cloud round 15 / fixed DPush

- ParaCloud `4139552` 未触碰：Barrier iteration 311、runtime `911,815.51 s`；resource audit round
  15 为 wall `915,643 s`、allocated `24,417.15 core-hours`、actual CPU `3,819.47 h`、CPU
  efficiency `15.643%`、MaxRSS `362.913 GiB`、iteration 291--311 平均 `52.200 min`。stderr 0、
  无 terminal/checkpoint；16 records SHA256 `41c67c50...a58fe`。
- fixed strict Crossover initial basis 已完成，DPush 从 `841,200` 降至约 `237,580`；DInf 非单调但
  日志无 error。RSS 约 `12.47 GiB`、available RAM 约 `101 GiB`、memory PSI 0，仍只有一个
  solver；v3 PID `46839` 继续等待 wrapper。

## 2026-08-16 15:25+08:00 strict Barrier 完成 / Crossover basis

- strict Base/744 h Barrier 正常报告 `218 iterations / 7,734.65 s / 11,980.50 work units`、
  `Optimal objective 2,361,958.43 million CNY`，已进入 `Building initial crossover basis`。
  最后 telemetry primal/dual/complementarity `0.003445/6.761e-7/1.962e-9`；scaled Gurobi 表为
  `6.11e-4/6.58e-8/1.96e-9`，日志无 warning/error。
- 相对旧同 profile Jan/2030 Barrier `251 / 11,142.54 s`，少 33 轮、runtime 快约 `30.58%`。
  最快 `1e-2/NumericFocus=1` candidate objective 与 strict Barrier 相对差约 `3e-9`，其 runtime
  `4,275.73 s`，Barrier-only 节省约 `44.72%`；仍须 exact macro v2，尚未晋级。
- fixed 仍只有一个 solver；Crossover basis 时 RSS 约 `12.57 GiB`、available RAM 约 `101 GiB`、
  `si/so=0/0`、memory PSI 0，stderr 0、终态三文件 absent。v3 PID `46839` 仍等待 wrapper。
- ParaCloud `4139552` 未触碰，仍为 Barrier iteration 310、resource audit round 14；不取消、不改参、
  不启动 Stage B。

## 2026-08-16 14:20+08:00 strict iteration 120 / cloud audit round 14

- fixed strict Base/744 h 为唯一 solver：Barrier iteration 120、runtime `3,996.41 s`；110--120
  平均 `45.062 s/iteration`，telemetry primal/dual/complementarity 为
  `0.007359/5.61e-4/0.502643`。stderr 0、无数值 warning、终态三文件 absent。
- Python RSS 约 `17.51 GiB`，host available RAM 约 `96 GiB`，swap 实时 `si/so=0/0`、memory
  PSI 0。v3 supervisor PID `46839` 仍等待，预定输出根 absent；fixed checkout clean/frozen
  `d80f5b7`，没有第二 solver。
- 三根 relaxed candidate 的 checkpoint 预检通过：各有完整 BarX `3,735,087` 项与 BarPi
  `4,454,178` 项，只能作为 `ENGINEERING_BARRIER_CHECKPOINT_ONLY`；copied supervisor/campaign
  `bash -n` 与 audit `py_compile` PASS。
- ParaCloud `4139552` 未触碰：iteration 310、runtime `908,489.11 s`、stderr 0、无
  terminal/checkpoint。resource audit round 14 为 wall `910,941 s`、allocated `24,291.76`
  core-hours、actual CPU `3,799.68 h`、CPU efficiency `15.642%`、MaxRSS `362.913 GiB`、最近
  290--310 平均 `51.827 min/iteration`；15 records SHA256 `12ecc84d...e21f`。

## 2026-08-16 13:54+08:00 macro accounting v2 与 supervisor v3

- `a02d4d99b1060a2552e1c1f470817f1d4dbe3ac1` 已双推送：exact macro 新增 carbon/CCS L1
  `<=2%` 与运行账目 L1 `<=5%`；成本分项存在时 L1 `<=2%`，历史缺失时仅 objective `<=1%` 作成本
  门禁并显式报告。容量/发电 `2%`、period generation `0.5%` 不变。采用 normalized L1 而非逐个
  近零项相对误差，符合全国宏观尺度且不放松科学 QC。
- `cost_components.csv` 现在在 load-center strict QC 前写出；不改表达式、数值、accounting scope 或
  QC。py_compile、macro+summary `6/6 PASS`，server isolated cost export PASS；真实旧根 parser v2
  成功但 exact identity 仍 FAIL。活动 checkout 未部署该提交。
- `5af8efe6872b569e4ca068c7c66cc2aefa9e676e` 已双推送并提供 versioned supervisor/campaign audit
  injection。旧 v2 supervisor 只等待且已精确替换，日志保留；v3 PID `46839`、PPID 1，控制/输出根
  为 `relaxed_barrier_continuation_v0816_v3`，绑定 checksummed macro v2。13:54 输出根 absent，无第二
  fixed solve。
- strict Base/744 13:54 Barrier iteration 81、runtime `2,445.64 s`、stderr 0；Python RSS 约
  `17.5 GiB`，memory PSI 0。checkout 继续 frozen `d80f5b7`。ParaCloud `4139552` 未触碰，最近权威
  审计为 round 13、iteration 309、stderr 0、无 terminal/checkpoint。

## 2026-08-16 13:42+08:00 strict reference manifest 门禁与 supervisor v2

- 实现 `f96d9e0443a40f343eaf74b6d97c7abd186e309a` 已双推送：result manifest validator 现在拒绝
  缺失/空 `files`、损坏 JSON、不安全/重复路径、非法 bytes/SHA256，并逐文件复核 size/hash；exact
  macro 审计要求 validator PASS 并记录 failures。py_compile、macro tests `5/5` 与直接 synthetic
  正/反检查通过；服务器 full regression 必须等活动 solve 退出后再做。
- 活动 fixed checkout 继续 clean/frozen `d80f5b7`。旧 supervisor v1 PID `4100799` 与唯一 sleep child
  被精确替换，未触碰 strict wrapper/time/Python `4046161/4046167/4046172` 或 sampler `4059299`；
  v1 日志全部保留。supervisor v2 PID `4179192`、PPID 1、脚本 SHA256 `90e399e9...e17c3b`，使用
  独立 `relaxed_barrier_continuation_v0816_v2` 控制/输出根。
- v2 只有在 reference 同时满足 wrapper rc 0、stderr 0、`OPTIMAL + PASS + 58/58`、非空且逐文件有效
  result manifest、current input manifest valid 后才复用 candidates 并启动串行 continuation；任一失败
  即停止。13:39 新输出根 absent，仍无第二 fixed solve。
- strict reference 13:39 Barrier iteration 51、runtime `1,579.34 s`、stderr 0；RSS 约 `17.5 GiB`、
  available RAM 约 `96.5 GiB`、实时 `si/so=0/0`、memory PSI 0。
- ParaCloud `4139552` 不变，13:42 仍 RUNNING、iteration 309、runtime `905,512.39 s`、stderr 0、无
  terminal/checkpoint。resource audit round 13：wall `908,636 s`、allocated core-hours `24,230.29`、
  actual CPU-hours `3,790.05`、MaxRSS `362.913 GiB`、iteration 289--309 平均 `52.070 min`；14 records
  SHA256 `a649998d...55a1f`。未取消、未改参、未启动 Stage B。

## 2026-08-16 13:30+08:00 Gurobi 参数边界复审

- strict Base/744 h 实际参数为 `BarConvTol=1e-8/FeasOpt=1e-7/NumericFocus=2/ScaleFlag=2/
  Crossover=2/CrossoverBasis=1`；当前矩阵、目标与 RHS 正值跨度分别约 `6.24e9/3.85e9/3.68e11`。
- Gurobi 官方说明支持当前执行边界：BarConvTol 可换取 Barrier 速度但可能转移成本到 Crossover；
  NumericFocus 越高数值保护越强且更慢；Feas/Opt 是绝对容差并非修复数值问题的首选；
  CrossoverBasis=1 更慢但更稳健。
- 因工程候选 `FeasOpt=1e-5` 比最小 `1e-6` 系数还大一个数量级，它们继续严格
  engineering-only。后续速度选择看 exact macro、V5 与长时域，不把 `1e-5` 直接升级 Stage B。
- ParaCloud `4139552` 不变；13:29 已到 iteration 309、stderr 0。fixed strict reference 13:29
  iteration 22、stderr 0、available RAM 约 96 GiB、memory PSI 0；supervisor 仍只等待。

## 2026-08-16 13:28+08:00 relaxed campaign 汇总器完成真实三根验证

- 新增纯读取 `scripts/summarize_relaxed_barrier_campaign.py`，统一输出 JSON/CSV 的 rc、wall、solver
  runtime、Barrier iterations/平均单步、GNU/进程树内存峰值、solution quality、checkpoint、工程 raw QC、
  根目录科学产物隔离、LP identity 与 macro exact A/B。py_compile 与联合测试 `5/5 PASS`。
- 活动 fixed checkout 未部署；脚本经 stdin 读取三根历史 candidate，权威输出位于 continuation 控制根
  `pre_exact_candidate_summary_v2.{json,csv}`，SHA256 为 `f1f95348...82a688`、
  `e15331e5...a6cf50`。三根均 rc 0、OPTIMAL、complete engineering checkpoint，root scientific
  QC/manifest/state/basis 均 absent。
- 观测 Barrier 单步：NumericFocus2 的 `5e-2/1e-2` 为 `31.643/32.573 s`，NumericFocus1 的
  `1e-2` 为 `14.862 s`；对应 solver runtime `4927.57/5289.26/4275.73 s`。因此最快路线的优势来自
  单步因子成本下降，尽管 iterations 为 `263`，高于另外两根的 `144/151`。
- pre-exact macro 列仍来自错误旧 reference，仅用于 parser 验证，禁止选择 winner。13:27 strict
  reference iteration 16、stderr 0；supervisor 继续等待，云端任务未修改。

## 2026-08-16 13:21+08:00 strict 744 h 已进入 Barrier；continuation supervisor 等待

- strict reference LP 为 `3,735,087` variables、`4,454,178` constraints、`40,395,436` nonzeros，
  Gurobi Fingerprint `0x7e66559b`=`2120635803`，与三条 relaxed candidates 相同。Presolve
  `226.12 s` 后为 `3,007,552 × 2,780,968`、`31,165,413` nonzeros；ordering `99.29 s`，
  Barrier iteration 0 于 runtime `363.60 s` 开始。
- 13:20 iteration 3，stderr 0；Gurobi current/max memory `12.61/21.36 GiB`。独立 5 分钟资源采样
  PID `4059299` 已记录 Python RSS `1.90/7.92/17.39 GiB`，host available RAM 当前约 96 GiB，
  swap 累计计数仅有背景级变化、memory PSI 0。
- continuation supervisor PID `4100799` 已 reparent 到 PID 1，只在 `sleep 300` 等待 reference；
  控制根为 `/data/zz2/National_model/run_control/relaxed_barrier_continuation_v0816_v1`，预定新输出根
  尚不存在。门禁为 reference rc 0、stderr 0、`OPTIMAL + QC PASS + result manifest`；失败即停止。
- 门禁通过后仅建立指向三个旧 candidates 的 symlink，不重跑它们；在新控制根重算 exact A/B，随后
  只让最快 exact `MACRO_PASS` 严格串行进入 V5/744、Base/1488、Base/2160（最后一根还要求 1488
  checkpoint 完整）。当前服务器仍只有 strict reference 一个 solver；活动 checkout 不变。
- ParaCloud `4139552` 未修改，继续不取消、不改参、不启动 Stage B。

## 2026-08-16 13:08+08:00 current-identity strict Base/744 h reference 已启动

- local、`origin`、GitHub 与 fixed server 均为 `d80f5b76b7deefd6c82004ee0e17f1fc206f7eff`；
  fixed server clean，Gurobi 13.0.2 完整回归 `184/184 PASS`（`94.693 s`）。启动前无活动
  CISPO/Gurobi，available RAM 约 114 GiB、swap 968 MiB/2 GiB 但 `si/so=0/0`、memory PSI 0。
- strict reference wrapper PID `4046161`，输出根
  `/data/zz2/National_model/outputs/relaxed_barrier_exact_reference_v0816_v1/base_744h_strict_crossover2`，
  控制根为对应 `run_control/`。边界为 2030 Base、hour 0--743、
  `barrier_16_crossover2_stable_basis_long_v1`；即 `Method=2/Threads=16/Presolve=2/Crossover=2/
  CrossoverBasis=1/TimeLimit=86400 s/SoftMemLimit=80 GiB`，未导出 diagnostic state。
- 启动后 wrapper→time→Python 进程树正常，stderr 0；available RAM 约 113 GiB、`si/so=0/0`、
  memory PSI 0。fixed server 内部仍严格单求解，不在 active PID 上部署或改参数。
- ParaCloud `4139552` 未修改：13:07 `RUNNING` 10 天 11:49，iteration 308、solver runtime
  `902,426.19 s`，Gurobi primal/dual/compl `0.901/1.26e-6/0.272`；stderr 0，solve report/QC/result
  manifest/checkpoint 全部不存在。继续不取消、不改参、不启动 Stage B。
- 下一步：strict reference 退出后做完整终态与 LP 身份审计，再对三根 relaxed candidate 另写 exact-LP
  A/B 报告；不得覆盖旧的 invalid-reference 报告。只有 exact `MACRO_PASS` 最快者晋级 V5/744 与更长时域。

## 2026-08-16 13:02+08:00 relaxed 744 h campaign 已完成，但旧宏观 reference 身份无效

- fixed-server campaign `/data/zz2/National_model/outputs/relaxed_barrier_campaign_v0812_v1`
  已严格串行完成 3 根 Base/744 h，均 rc 0、stderr 0、Gurobi `OPTIMAL`、完整工程 BarX/BarPi
  checkpoint，且根目录 scientific QC/manifest/state/basis 保护全部通过。campaign PID `3074785`
  已退出；13:02 fixed server clean `6477f42`、无求解、available RAM 约 114 GiB、swap 968 MiB/2 GiB
  且 `si/so=0/0`、memory PSI 0。
- `BarConvTol=5e-2`：wall `1:28:31`、solver `4,927.57 s`、Barrier 144、MaxRSS
  `19,959,364 KiB`；`1e-2/NumericFocus=2`：`1:34:34`、`5,289.26 s`、151、
  `19,802,092 KiB`；`1e-2/NumericFocus=1`：`1:17:32`、`4,275.73 s`、263、
  `19,486,068 KiB`。三根严格 solver/physical QC 均 HARD_FAIL，但未被误标科学结果。
- 原 `winner.json=NO_MACRO_PASS` 不能解释为参数科学失真：campaign 错用了旧 strict root
  `...744h_jan0_3f123f0_base_v1/2030`。旧根绑定 2026-07-30 数据、Git `3f123f0`、LP Fingerprint
  `-1670477391`；候选绑定 2026-08-05 Power_curve v3_qc 数据、Git `6477f42`、Fingerprint
  `2120635803`。负荷 SHA 与多个 flex/EV 文件也不同，`period_load` 因而相差 `0.2732%`。
  三根的耗时/资源证据仍有效，但既有宏观 A/B 与速度比不是 exact-LP 对照。
- 修补提交 `c53bd78` 现要求同一 baseline/scientific/scenario/formulation identity、同一非 solver
  input manifest、同一 LP variables/constraints/nnz/Fingerprint，并要求 reference
  `OPTIMAL + solution_qc PASS + result_manifest`；solver profile 允许不同。source bundle 是否相同
  单独记录但不作为 LP 门禁，以允许纯审计/导出代码更新。py_compile 与 targeted `4/4 PASS`。
- 精确下一步：双推送并部署 `c53bd78`，server 全回归后在当前 tip/当前数据新建单独 strict
  Base/744 h reference（Crossover=2，不导出 state）；完成后重算已有三根 exact A/B。只有 exact
  winner 才进入 V5/744、Base/1488 与 Base/2160，不再重复无信息的宽松候选。
- ParaCloud `4139552` 未修改：13:02 仍 RUNNING 10 天 11:44，latest Barrier iteration 308、
  runtime `902,426.19 s`、primal/dual/compl `3.376/2.02e-6/0.2725`、stderr 0，无终态/checkpoint。

## 2026-08-12 21:45+08:00 第二次 1 h smoke 定位 master-export QC；分阶段修补已提交

- 新根 `/data/zz2/National_model/outputs/relaxed_barrier_smoke_1h_0d773d5_v2` 的 Python/time 终态为
  rc 0，wall `0:37.84`、MaxRSS `496,276 KiB`、stderr 0；求解结果与首次完全一致：`OPTIMAL`、
  Barrier 49、solver `2.847 s`、checkpoint 完整。外层远端审计命令仅在求解完成后因 `$rc` 转义错误
  以 shell rc 1 退出，并把 `return_code.txt` 误写为字面 `$rc`；`time.txt` 的 `Exit status: 0` 与模型
  文件证明 Python 本体成功。该 wrapper 元数据错误已保留，不重标历史文件。
- 第二次 smoke 证明 load-center 双向流拒绝实际发生在 `export_master_solution()`，早于 operational
  export；因此提交 `cc9293b` 的捕获层级仍不足，未生成 raw-QC file/annual summary/contract。新提交
  `247c3020dc7c667e161d61a331ff81d8b5f616fe` 把 master、operational、summary 拆成独立阶段：仅预期的
  `Load-center/Production solution QC failed` 可被记录并继续，磁盘错误、编程错误等非 QC 异常仍立即
  重新抛出；summary 在严格 QC 失败后继续生成。
- 本地 py_compile 与新增 targeted `3/3 PASS`。一次 Windows 完整回归因错误环境先快速失败；改用 RL
  环境后又异常长时间无终态，已终止且不计入 PASS。下一步双推送，在 clean/idle fixed server 部署，
  以权威环境执行完整 `182` 项回归和第三个全新 1 h smoke；未闭合前不启动 744 h。

## 2026-08-12 21:28+08:00 relaxed Barrier 1 h 真解暴露导出边界；保留宏观证据的修补已提交

- fixed server 的首次 Base/1 h `BarConvTol=5e-2` 烟雾根为
  `/data/zz2/National_model/outputs/relaxed_barrier_smoke_1h_9f5c2ca_v1`。wrapper 正常退出，wall
  `1:44.92`、MaxRSS `497,512 KiB`、stderr 0；Gurobi `OPTIMAL`，Barrier 49 次、solver
  `2.829 s`，完整工程 checkpoint 已先保存：BarX `238,529` 项、BarPi `80,143` 项，均为 finite，
  `scientifically_accepted=false`。
- 该极宽松解没有通过严格解质量：ConstrVio `4.04e-6`、BoundVio `3.78e-9`，但 DualVio
  `0.628`、ComplVio `29.509`，最后一次 telemetry 的 primal--dual relative gap 为 `1.389%`。
  原始物理导出还检测到双向最小流最大 `3.599 GWh`、合计 `76.294 GWh`、640 条活动边，因而按既有
  load-center QC 抛错。根目录仍无 scientific `solution_qc/result_manifest`、planning state 或 basis，
  隔离边界有效；此结果明确不是科学解。
- 修补提交 `cc9293b25ef66ff4642eeb5860fb00b0a938b5ba` 让严格原始 QC 失败时写入
  `engineering_raw_qc_error.json`，同时继续导出未接受的宏观汇总与 analysis contract；宏观审计也能
  在缺少严格 `solution_qc.json` 时保留失败原因。它不改变 LP、solver profile、严格 QC 或晋级阈值。
  本地 py_compile、focused test 与完整 `181/181 PASS`。下一步为双推送、fixed server clean fast-forward、
  server 回归及全新 1 h smoke；复测闭合后立即启动唯一串行 744 h campaign。
- 21:28 fixed server 仍 clean/idle `9f5c2ca`，available RAM 约 `114 GiB`、连续 `si/so=0/0`、memory
  PSI 0、`/data` 余 `3.6 TiB`。ParaCloud job `4139552` 未触碰，仍 `RUNNING` 6 天 20:10；最新
  iteration 202、runtime `587,056.87 s`、MaxRSS `380,541,576 KiB`、stderr 0，无终态或 checkpoint。

## 2026-08-12 12:05+08:00 fixed-server relaxed Barrier campaign 已实现、尚未部署

- 作者授权保持 ParaCloud `4139552` 运行，同时在 fixed server 严格串行测试显著宽松的 744 h
  和更长时域。实时 fixed server 为 clean `3f739fd`，无 CISPO/Gurobi solver，Gurobi 13.0.2，
  available RAM 约 114 GiB、swap 976 MiB/2 GiB 且连续 `si/so=0/0`、memory PSI 0、磁盘余
  3.6 TiB。两个 8 月 5 日遗留 bash/grep 只读审计管道无 Python/Gurobi 子进程，不是第二求解。
- 云 job 未修改：iteration 191 于 12:04:31 落盘，runtime 554,846.21 s；Slurm MaxRSS
  362.913 GiB、stderr 0，`solve_report.json`、`solution_qc.json`、`result_manifest.json` 与
  checkpoint 均不存在。继续禁止人工取消、Stage B 或第二个云任务。
- 实现提交 `9308ac002161a0b7971c28db8e46b5f42e8b91a8` 的新路线只在显式
  `--engineering-barrier-checkpoint-only
  --engineering-relaxed-barrier-analysis` 下工作。3 个 744 h profiles 扫描
  `BarConvTol=5e-2/1e-2` 和 matched `NumericFocus=1`；`FeasibilityTol/OptimalityTol=1e-5`，
  无 Crossover。宽松解的完整 `BarX/BarPi` 与宏观 outputs 分层保存，后者永不生成科学 manifest/
  state/basis。自动 campaign 在 3 个 744 h Base 之后只允许最快 `MACRO_PASS` 进入 V5/744 h、
  Base/1488 h 和最多 Base/2160 h，全程单实例。
- 本地验证为 focused `31/31`、完整 `180/180 PASS`、py_compile/JSON/diff PASS。尚未提交、部署或
  启动任何 fixed-server solve；Linux `bash -n`、server full regression 和 1 h 真解烟雾门禁仍是
  744 h 启动前置条件。

## 2026-08-12 11:50+08:00 Barrier iteration 190，资源审计 round 12

- job `4139552` `RUNNING` 6 天 10:32:11；iteration 190 于 11:18:12 落盘，solver runtime
  552,067.53 s。iteration 158--190 平均 47.571 分钟/步，速度稳定。
- 最新 Gurobi primal/dual residual/complementarity 为 `4.00e1/9.35e-7/2.37e1`；objective 相对
  间距由 iteration 158 的 `3.69` 缓慢降至 `3.21`。仍在推进，但长尾明显且尚未收敛。
- Slurm MaxRSS 362.913 GiB、Gurobi current/max 351.054/354.498 GiB；累计 allocation
  14,835.493 core-hours、actual CPU 2,300.554 h。stderr 0，无 warning/numerical trouble/error。
- 终态报告、QC、result manifest 和 checkpoint 均不存在。资源账本 round 12 共 13 records，SHA256
  `e299d4c7821a0e6e372b44182c3dc239179b58bea5ccfa784a4cc841a77b776d`。继续不取消、不改参，
  不启动 Stage B/第二求解。

## 2026-08-11 10:16+08:00 Barrier iteration 158，资源审计 round 11

- job `4139552` `RUNNING` 5 天 08:58:07；iteration 158 于 09:55:55 落盘，solver runtime
  460,730.61 s。iteration 145--158 平均 47.263 分钟/步，速度稳定。
- 最新 Gurobi primal/dual residual/complementarity 为 `6.97e1/1.92e-6/4.63e1`；objective 相对
  间距由 iteration 145 的 `3.90` 缓慢降至 `3.69`。仍在推进，但已是明显数值长尾，尚未收敛。
- Slurm MaxRSS 362.913 GiB、Gurobi current/max 351.054/354.498 GiB；累计 allocation
  12,380.987 core-hours、actual CPU 1,906.975 h。stderr 0，无 warning/numerical trouble/error。
- 终态报告、QC、result manifest 和 checkpoint 均不存在。资源账本 round 11 共 12 records，SHA256
  `467e4f1bba55a0fac1c9947d444e8f45d3e32fc247b043c0e0dfa76d9c8dc6b4`。继续不取消、不改参，
  不启动 Stage B/第二求解。

## 2026-08-10 23:43+08:00 Barrier iteration 145，资源审计 round 10

- job `4139552` `RUNNING` 4 天 22:25:36；iteration 145 于 23:41:30 刚落盘，solver runtime
  423,865.48 s。iteration 116--145 平均 47.530 分钟/步，计算节奏稳定。
- 相对 iteration 116，telemetry primal/dual infeasibility 与 complementarity 再缩小
  `6.61/4.71/4.81` 倍；最新 Gurobi 三项为 `8.16e1/3.23e-6/5.61e1`。objective 相对间距由
  `8.56` 降至 `3.90`，说明仍有推进，但依然是长尾而非已收敛状态。
- Slurm MaxRSS 362.913 GiB、Gurobi current/max 351.054/354.498 GiB；累计 allocation
  11,368.96 core-hours、actual CPU 1,744.324 h。stderr 0，无 warning/numerical trouble/error。
- 终态报告、QC、result manifest 和 checkpoint 均不存在。资源账本 round 10 共 11 records，SHA256
  `581e3c52d5a087f38368cf35f9396a67c7561e612d91b2059b9f19537db3bba0`。继续不取消、不改参，
  不启动 Stage B/第二求解。

## 2026-08-10 00:47+08:00 Barrier iteration 116，资源审计 round 9

- job `4139552` `RUNNING` 3 天 23:29:30；iteration 116 于 00:43:08 落盘，solver runtime
  341,163.39 s。iteration 77--116 平均 47.499 分钟/步，未发生持续性能退化。
- 相对 iteration 77，telemetry primal/dual infeasibility 与 complementarity 又缩小
  `82.48/36.26/42.62` 倍；最新 Gurobi 三项为 `5.40e2/1.52e-5/2.70e2`。近期收敛已转入较缓长尾，
  primal/dual objective `2.28e9/-1.72e10` 相对间距约 `8.56`，尚不能声明临近完成。
- Slurm MaxRSS 362.909 GiB、Gurobi current/max 351.054/354.498 GiB；累计 allocation
  9,167.2 core-hours、actual CPU 1,391.305 h。stderr 0，无 warning/numerical trouble/error。
- 终态报告、QC、result manifest 和 checkpoint 均不存在。资源账本 round 9 共 10 records，SHA256
  `9aa1f051e406b4bdfd5056f0dec90303e4d5ad3b18a0faf360cd18580bf9052b`。继续不取消、不改参，
  不启动 Stage B/第二求解。

## 2026-08-08 17:51+08:00 Barrier iteration 77，资源审计 round 8

- job `4139552` `RUNNING` 2 天 16:33:41；iteration 77 于 17:50:39 刚落盘，solver runtime
  230,014.78 s。iteration 48--77 平均 46.061 分钟/步，整体节奏稳定。
- 相对 iteration 48，telemetry primal/dual infeasibility 与 complementarity 已分别缩小约
  `82,964/832,887/57,100` 倍；Gurobi 表内最新三项为 `4.45e4/5.22e-5/1.15e4`。这是明显推进，
  但 primal/dual objective `4.98e10/-5.30e11` 尚未闭合，不能声明收敛或给完成百分比。
- Slurm MaxRSS 362.765 GiB、Gurobi current/max 351.054/354.498 GiB；累计 allocation
  6,197.893 core-hours、actual CPU 915.299 h。stderr 0，无 warning/numerical trouble/error。
- 终态报告、QC、result manifest 和 checkpoint 均不存在。资源账本 round 8 共 9 records，SHA256
  `f0c7fdfa03c0ab39c5a1ace6739ea5a337b7dd0b22de7e83d37c4f5bde09ede0`。继续不取消、不改参，
  不启动 Stage B/第二求解。

## 2026-08-07 19:45+08:00 Barrier iteration 48，资源审计 round 7

- job `4139552` `RUNNING` 1 天 18:27:23；iteration 48 于 19:34:53 落盘，solver runtime
  149,868.82 s。iteration 35--48 平均 46.951 分钟/步，计算节奏稳定。
- 相对 iteration 35，telemetry primal/dual infeasibility 与 complementarity 分别下降
  `77.27%/84.52%/77.95%`；目标和残差继续改善，但绝对量级仍不能声明收敛或完成比例。
- Slurm MaxRSS 362.649 GiB、Gurobi current/max 351.054/354.498 GiB；累计 allocation
  4,075.813 core-hours、actual CPU 572.464 h。stderr 0，无 warning/numerical trouble/error。
- 终态报告、QC、result manifest 和 checkpoint 均不存在。资源账本 round 7 共 8 records，SHA256
  `d691d087fec95263c77e62530befa58cac9b0aed6a986a55a9b992535305badc`。继续不取消、不改参，
  不启动 Stage B/第二求解。

## 2026-08-07 09:59+08:00 Barrier iteration 35，资源审计 round 6

- job `4139552` 仍为 `RUNNING`，wall 1 天 08:41:08、96 CPU/700G、`TimeLimit=UNLIMITED`；
  iteration 35 于 09:24:32 落盘，solver runtime 113,247.02 s，正在计算下一轮。
- iteration 23--35 平均 47.032 分钟/步（8--35 平均 47.112）；同期 telemetry primal/dual
  infeasibility 与 complementarity 分别下降 `78.29%/76.82%/77.52%`，dual objective 继续向
  primal 方向回转。绝对残差和目标间距仍很大，不能据 iteration 序号外推完成百分比。
- Slurm MaxRSS 362.540 GiB、Gurobi current/max 351.054/354.498 GiB；累计 allocation
  3,137.813 core-hours、actual CPU 421.861 h。stderr 0，日志无 warning/numerical trouble/error。
- `solve_report.json`、`solution_qc.json`、`result_manifest.json` 与 checkpoint 均不存在。
  resource audit round 6 已追加，共 7 records，SHA256
  `13e567bd1743c5b0079ebb7445123bb18f6cba05a5e7be208f9619592c2c6175`。继续不取消、不改参、
  不启动 Stage B/第二求解。

## 2026-08-07 00:00+08:00 Barrier iteration 23，资源审计 round 5

- job `4139552` `RUNNING` 22:42:29，iteration 23 于 00:00:09 刚完成；solver runtime
  79,383.98 s。iteration 18--23 平均 47.105 分钟/步，iteration 8--23 平均 47.175 分钟/步，
  长时速度稳定。
- 相对 iteration 18，telemetry primal/dual infeasibility 与 complementarity 分别下降
  `42.9%/54.9%/45.6%`；dual objective 持续向 primal 方向回转。仍未接近验收容差，不给完成百分比。
- Slurm MaxRSS 362.344 GiB、Gurobi current/max 351.054/354.498 GiB；累计 allocation
  2,179.973 core-hours、actual CPU 267.629 h。stderr 0、无数值警告，无终态/checkpoint文件。
- resource audit round 5 已追加，共 6 records，SHA256
  `73f3df3998f4313051231658dd35dc8ccaeb1f8c3c23ccec5efa7a0e4c30d967`。继续不取消、不改参、
  不启动 Stage B/第二求解。

## 2026-08-06 20:27+08:00 Barrier iteration 18，资源审计 round 4

- job `4139552` 仍为唯一活动 cloud task：`RUNNING` 19:08:54、96 CPU/700G、无限时长。
  iteration 18 于 20:04:37 落盘，solver runtime 65,252.49 s；iteration 8--18 平均
  47.210 分钟/步，未出现持续变慢。
- 相对 iteration 8，Gurobi 表内 primal residual/dual residual/complementarity 分别下降约
  `74.4%/78.0%/75.1%`；dual objective 在 iteration 14 后开始回转，但仍是早期 Barrier，不能
  换算完成比例或声称接近收敛。日志无 warning/numerical trouble/error，stderr 0。
- 当前 Slurm MaxRSS 362.188 GiB，Gurobi current/max memory 仍为 351.054/354.498 GiB；累计
  allocation 1,838.24 core-hours，实际 CPU 212.941 h。终态三文件和 checkpoint 均不存在。
- `resource_audit_snapshots.jsonl` 已追加 round 4，共 5 records，当前 SHA256
  `fb390f551ef190720673a341037e2bcd8b6ce006905b549268a27c4f0f418c7f`。继续禁止人工取消、
  Stage B、第二求解或重提；资源账本仅在审计时旁路更新，不修改 solver/output。

## 2026-08-06 12:16+08:00 iteration 8 与全程资源审计已固化

- job `4139552` 仍为 `RUNNING`；iteration 8 于 12:12:31 落盘，solver runtime 36,926.33 s，
  该步耗时 2,724.09 s（45.40 分钟）。12:16 Slurm MaxRSS 361.648 GiB、累计实际 CPU
  86.877 h、累计 allocation 约 1,054.24 core-hours，stderr 0。除非作者明确授权，禁止人工取消；
  作业自身终态仍按报告/checkpoint合同审计。
- 当前 control root 新增只读审计产物：`resource_audit_snapshots.jsonl`（4 records，SHA256
  `7ecb6006...5dae10`）记录 launch/iteration 7/iteration 8 的 Slurm 快照与禁止取消策略；
  `historical_8760_comparison.json`（SHA256 `2e77c8ef...fc7f6`）冻结与旧 job `4004585` 的同口径比较。
  每个 Barrier iteration 继续由 `solver_telemetry.jsonl` 自动记录 runtime/work units/residual/memory；
  人工审计追加 Slurm elapsed/CPU/RSS，终态再以 `sacct` 汇总总资源。
- 旧 `4004585` 同样是完整 8760 h LP，只是墙钟限制 24 h，并非 24 h 时域；它最终 `TIMEOUT` 于
  iteration 35、无 accepted result。当前相对旧模型：raw rows/cols/nnz 为 `-25.344%/+1.335%/-4.311%`；
  presolved 为 `-0.734%/-9.194%/+0.848%`；Factor NZ/Ops 为 `-11.772%/-21.119%`，当前 sampled
  MaxRSS 低 `24.145%`。但当前 16 threads 对旧 32 threads，近期单步约慢 50%，且科学模型/数据已变，
  不能直接比较目标与残差大小。

## 2026-08-06 12:06+08:00 2030 Base 8760 h Stage A 已进入 Barrier iteration 7

- ParaCloud job `4139552` 仍为唯一活动任务，`RUNNING` 10:48 于 `m4cm1901`；96 CPU/700G、
  billing 96、`TimeLimit=UNLIMITED`。Slurm stderr 仍为 0 bytes，日志未出现 warning、numerical
  trouble 或 error；58 秒采样中累计 CPU 增加约 15.5 分钟，证明 16 个 Gurobi threads 正在工作。
- model build 于 01:57 完成，耗时 2,336.984 s、build peak RSS 48.574 GiB。实际原始 LP 为
  `41,458,383 vars / 50,907,234 rows / 492,835,195 nnz`，fingerprint `0xd16b4c7e`；presolve
  17,414.51 s 后为 `32,166,850 vars / 37,703,954 rows / 404,259,819 nnz`，ordering 2,912.17 s。
- Barrier 当前最新落盘 iteration 为 7（11:27:07，solver runtime 34,202.25 s）。iteration 3--7
  间隔约 44.6/47.0/48.1/47.7 分钟；12:06 正在计算 iteration 8。表内 primal residual 从
  `6.77e11` 降至 `5.32e11`、complementarity 从 `1.28e11` 降至 `1.02e11`，仍属极早期，不能据此
  判定收敛或失败。Factor NZ `3.395e10`，Gurobi 估算 factor memory 约 300 GB。
- Slurm MaxRSS `379,125,920 KiB`（约 361.6 GiB），Gurobi current/max memory 约
  `351.1/354.5 GiB`；尚未触及 600 GiB soft limit 或 700 GiB allocation。当前无 solve report、
  QC、result manifest 或 checkpoint，继续只读监控，禁止 Stage B/第二求解。

## 2026-08-06 01:19+08:00 2030 Base 8760 h Stage A v2 已稳定进入 model build

- 当前唯一活动 cloud job 为 `4139552`，`RUNNING` 于 `m4cm1901`，开始时间 01:17:53；
  `Req/AllocTRES=cpu=96,mem=700G,billing=96`、`TimeLimit=UNLIMITED`，无依赖任务。Gurobi profile
  仍为 16 threads、Crossover=0、SoftMemLimit=600 GiB；不会自动 Stage B/2040/V5。
- 有效 release：
  `$HOME/National_model_cloud/20260806_8760_stagea_3f739fd_v5`，Git `3f739fd6216b1c7fc356e8d3a1d9a257c666f0c5`，
  Linux archive SHA256 `c49d48da070834b969b13b7a4ea50d0b45c5383276820db0e314d324822ec40e`；
  私有 xarray wheel SHA256 `a7ad6a36...a7f8d6`，共享 conda env 未修改。
- compute data-load gate `4139550` 为 `COMPLETED 0:0`：41.69 s、321,264 KiB、0 swap；31×8760、
  36,686 VRE sites、2,030 hydro stations 与 wave 全载入。主 job 已通过 profile、provenance、input
  manifest、67 PASS/3 WARN/2 INFO/0 HARD_FAIL preflight；full-year scale estimate 为
  `41,186,823 vars / 55,928,698 rows / 497,144,574 nnz`，available 732.26 GiB。
- 01:19 主 job 已越过前三次 fail-fast 点，处于 LP model build；MaxRSS 3,986,620 KiB，Slurm stderr
  0 bytes，尚无 `gurobi.log`/telemetry/build report。继续只读监控，不提交任何第二任务。

## 2026-08-06 01:13+08:00 第三次提交在 wave 数据加载前 fail-fast；补齐私有 xarray overlay

- v4 的低成本 job `4139494` 已证明 profile、代理/WLS 与 Gurobi 13.0.2 小 LP `PASS`。主 job
  `4139496` 完成 provenance/input manifest 后，因 cloud Python 缺 `xarray` 在 wave store 初始化
  前退出；Slurm elapsed 7 秒，无 LP build、`gurobi.log` 或 telemetry。
- cloud 现有环境已含 `netCDF4=1.7.2/cftime=1.6.5/numpy=2.2.6/pandas=2.3.2`，仅缺 xarray。
  fixed server 已有纯 Python wheel `xarray-2025.1.2-py3-none-any.whl`，SHA256
  `a7ad6a36c6e0becd67f8aff6a7808d20e4bdcd344debb5205f0a34b1a4a7f8d6`。
- 不修改共享 cloud conda env；下一 release 使用私有 `python_overlay` + `PYTHONPATH`。先以低资源
  compute job 完整执行 `load_model_data(Base/8760)`，通过依赖/数据加载后才可再提交 96/700G。
  job `4139496` 与 v4 release 不复用。

## 2026-08-06 01:10+08:00 第二次提交在 provenance 前 fail-fast；环境导出已修复

- job `4139479` 先通过 `STAGE_A_PROFILE_PREFLIGHT_PASS`，随后因四个 `CISPO_*_ROOT` 仅被
  shell `source`、未 export 给子 Python 而在 `write_run_provenance` 前退出。Slurm elapsed 5 秒，
  runner wall `1.09 s`、peak RSS `83,900 KiB`、swap 0；没有 LP build、Gurobi log/telemetry 或求解。
- 修复提交 `b5cad0dee02f0f2ac7c8368b778f68dde0796826` 使用 `set -a/source/set +a`，并把该导出
  合同加入 wrapper 静态测试；profile suite 继续 `9/9 PASS`。
- job `4139419/4139479` 与 cloud `_v1/_v2/_v3` 均为只读失败证据，不得重提或补写结果。
  下一步是双推送/deploy `b5cad0d`，以 Linux archive 创建 `_v4`，重复语法/调度预检后只提交
  一个全新 Stage A。

## 2026-08-06 01:06+08:00 首次提交 0 秒失败；未求解，wrapper 已修复

- cloud 无计费 `sbatch --test-only` 接受 `96 CPU/700G`。首次实际 job `4139419` 的
  `ReqTRES/AllocTRES=cpu=96,mem=700G,billing=96`、`TimeLimit=UNLIMITED`，但在 0 秒、
  `TotalCPU=0.007 s/MaxRSS=0` 时 `FAILED 1:0`；Slurm stdout/stderr 均为 0 bytes，未进入 Python、
  模型 build 或 Gurobi，不是数值/模型失败，也没有持续计费。
- 原因是 Slurm 执行 spool copy，旧 wrapper 从 `$0` 推导 release 根会落到 spool 路径。
  修复提交 `d857f8d2a0724bc7d89856aea70042977b2f9b0a` 改用提交时固定的
  `SLURM_SUBMIT_DIR`，并新增静态回归，profile tests `9/9 PASS`。
- Windows tar 导出的 CRLF `_v1` 与上述 job 所在 `_v2` release 均保留为失败证据；二者不复用。
  精确下一步是双推送/deploy `d857f8d`，用 fixed-server Linux archive 建立全新 `_v3` release，
  再次 `bash -n + sbatch --test-only` 后仅重提一个 Stage A。

## 2026-08-06 00:57+08:00 2030 Base 8760 h Stage A v2 已实现，待部署提交

- 实现提交 `6f0b1f7286a5ba479eabff3df2b14c2f8cf6bbb6` 新增
  `barrier_checkpoint_full_year_cloud_v2`：`Method=2/Threads=16/Presolve=2/Crossover=0/
  SolutionTarget=1/BarConvTol=1e-8/FeasibilityTol=OptimalityTol=1e-6/MarkowitzTol=0.01/
  NumericFocus=2/ScaleFlag=2/Aggregate=1/SoftMemLimit=600 GiB`，Gurobi `TimeLimit` 显式为
  `null`，因此保持 solver 默认无限；Slurm wrapper 也不设置 wall time。
- 新 runner 路径保持 Stage A 工程身份：完整 `BarStatus=OPTIMAL` 后先保存 finite `BarX/BarPi`；
  如果外部中断且未完成 Barrier，只在属性仍可读时尽力保存 `RECOVERY_ONLY`，其
  `deferred_crossover_eligible=false`。Stage A 不写 scientific manifest/planning state，也不会
  自动启动 Stage B、2040 或任何情景。
- 本地 py_compile PASS；solver profile `8/8`、checkpoint `5/5`，完整回归 `179/179 PASS`。
  00:49 实时核验 local/origin/GitHub/fixed server 均为前一 clean tip `ad662c8`，fixed server
  idle、available 约 113 GiB、无 swap I/O/PSI；ParaCloud 队列为空。云分区
  `amd_a8_768` 为 `DefaultTime=NONE/MaxTime=UNLIMITED`。
- 已准备单任务 wrapper，申请 `96 CPU/700G` 但 Gurobi 只用 16 threads；相对 128 CPU 请求可将
  计费 TRES 降低 25%（以调度器 `--test-only` 和实际 `sacct` 为准）。此状态点尚未提交付费 job；
  下一步是双推送、clean 部署、建立不可变 cloud release、无计费调度预检后只提交一个 Stage A。

## 2026-08-05 20:35+08:00 Power_curve v3_qc 已部署 fixed server 并同步 ParaCloud

- fixed server clean implementation HEAD `3cb3939197c3915a5a679a15c9a42e651c320534`；新数据根
  `/data/zz2/National_model/data/model_ready_20260805_power_curve_v3_qc_d63a251_v1` 为 78 files、
  127 MiB，tree SHA256 `4e5ba9c5057ff18a2c7267395d69ce292b8f5347453dc57f9dcd892af45886e0`。
  旧生产根与历史 outputs 未改。
- data smoke `142/142 PASS`，完整 unittest `178/178 PASS`，release/readiness/V4/V5 全 PASS。
  首次 v1 smoke 暴露旧精简根缺 16 个当前 QA/support tables，失败记录保留；v2 全闭合。
- 全新四年 Base/V5 1 h 与 24 h 共 16 roots 全部 `ACCEPTED`；两份 A/B audit PASS，无 basis、
  无并发、无 swap，且全部为 `TEST_ONLY_TRUNCATED_HORIZON`。
- ParaCloud 有效 file release 为
  `$HOME/National_model_cloud/20260805_power_curve_v3_qc_3cb3939_v2`，5.5 GiB；code、model-ready、
  CF、hydro、wave 的 archive/tree hashes 全闭合。队列为空、未提交 cloud job。raw GRFR 8.3 GiB
  未复制，故 cloud `--require-raw-grfr` readiness 未执行；无 `_v2` 的 sibling 为无效 clone 尝试。
- 当前无 fixed-server CISPO/Gurobi process；本任务不授权 168/744/8760 h 或付费云求解。

## 2026-08-05 16:05+08:00 本地负荷已切换到 Power_curve_V2 v3_qc；服务器未变

- 本地权威上游现为 `Power_curve_V2/outputs/future_8760_projection_ev_calibrated_v3_qc/tables/
  future_hourly_load_2025_2060_8760.csv.gz`，SHA256
  `8ed727745afda68b7114b08ea65660392cb374b68f203a6633bbbc9a13af791a`。
- 本地 `data/load/hourly_load_2025_2060.csv.gz` 已替换为五模型年转换，SHA256
  `bd94df0fd192c31e553ec9df7e486c90cc51ce2f9cd063cc660e499dce0c9903`；31省×5年×8760 h、
  key/datetime/单位/组件闭合全部通过。EV 年电量较旧本地输入提高 4.219004%，base residual 回算，
  全国总负荷年电量和冷热分量不变。
- `hourly_load_2030_2060.csv.gz`、`annual_load_summary.csv`、V3 envelope、V4/V5 EV 派生输入及
  manifests 已同步重建；V4/V5 sidecar 均直接绑定新负荷主表 SHA256。data smoke `142/142 PASS`，
  相关 unittest `23/23 PASS`。
- 这是 **local-only data milestone**。截至该里程碑时点，固定服务器 checkout、当前版本化数据根、输出和
  ParaCloud 均未改变；此前 accepted roots 继续绑定旧 input manifest，不能
  重标为新负荷结果。部署需另建数据根并重新完成 release/readiness/短门禁。

## 2026-08-05 14:50+08:00 两阶段 8760 h 合同已实现，尚未启动

- implementation `369506010b5bc876676941e456d9574187e0f293` 已双推送并部署到 fixed
  server；server checkout clean/idle，targeted Gurobi 13.0.2 tests `12/12 PASS`。本次只做
  Git fast-forward、py_compile 和 tests，没有 model build/solve。
- Stage A `barrier_checkpoint_full_year_cloud_v1` 强制工程身份：`BarStatus=OPTIMAL` 后优先
  保存 finite raw-order `BarX/BarPi`、完整 LP/order/config/input/Gurobi 身份；即使 solver
  最终为 `OPTIMAL`，该 root 仍是 `scientifically_accepted=false`，无 scientific result
  manifest/planning state。`BarPi` 只可作工程 shadow-price 原始向量。
- Stage B `deferred_crossover2_full_year_cloud_v1` 只接受 exact-LP matched checkpoint；工程源
  需双重显式授权，使用 `PStart/DStart + LPWarmStart=2 + Crossover=2/CrossoverBasis=1`，
  不重复 Barrier。只有 Stage B 的 `OPTIMAL/QC/all checks/input/result manifest/Pi` 全闭合
  才能成为科学结果；planning state 还需单独显式授权。
- 14:50 fixed server available 约 `113 GiB`，Stage A/B profile 内建最低 available
  `640 GiB`，因此 fixed server 会在 build 前 hard-fail。ParaCloud 队列为空；
  `amd_a8_768` 为 128 CPU/750 GiB，`DefMemPerCPU=6000 MB`、`MaxMemPerCPU=6144 MB`。
  建议 job 申请整节点 `128 CPU/700G`，Gurobi 仍为 16 threads；尚未提交作业。

## 2026-08-05 14:09+08:00 744 h 耗时/profile 汇总；无 Barrier-only 744 记录

- 11 个已执行 Phase 2 744 h Base 根全部为 Crossover=2 同一 profile；9 accepted runtime
  `5.20--18.37 h`、平均 `8.89 h`、中位 `7.24 h`，Barrier/Crossover 平均约
  `2.60/6.08 h`；另两根 24 h TIME_LIMIT。峰值 RSS `18.632--21.158 GiB`。
- 服务器全部现存 solve reports 中，744 h 且 Crossover=0 的数量为 0。当前从未真正运行
  744 h Barrier-only；recovery BarX/BarPi 不改变这一事实。

## 2026-08-05 13:52+08:00 当前无已验证 8760 h solver route

- Barrier-only 当前模型 24 h 的 20 个组合均未同时通过严格 primal/dual；它只是历史设计
  目标，不是已验证 production profile。`Crossover=2` 是截断时域已冻结路线，但本轮 744 h
  只完成 9/12 Base，另有两个 Crossover TIME_LIMIT。
- 因此不能把任一路线直接外推到 8760 h，也不能把 recovery-only `BarX/BarPi` 当作
  Barrier-only 可用性证明。正式年度求解继续禁止，先做 recovery 离线审计和新 profile A/B。

## 2026-08-05 13:47+08:00 两个 timeout 根已保存 recovery-only BarX/BarPi

- Jan/2050 与 Jun/2060 均为 Gurobi 13 `BarStatus=OPTIMAL`，wrapper 因而自动保存了完整
  `BarX/BarPi` 向量；两份 checkpoint 均标记
  `RECOVERY_ONLY_UNACCEPTED_SOLVER_RESULT`、`scientifically_accepted=false`、
  `deferred_crossover_eligible=false`。
- 这些文件只证明 Barrier 内点向量仍可读取，不等于 accepted solution：源 solve
  `TIME_LIMIT + SolCount=0`，无 QC/result manifest/planning state，亦不含 presolve、
  factorization 或 basis。不得 resume、续接或用于科学影子价格。
- 大于 744 h 的 inline Crossover 当前默认被 runner 拒绝；8760 h 必须先用严格 accepted
  `Crossover=0` Barrier 主阶段闭合并生成 accepted checkpoint。当前模型尚未通过该门禁。

## 2026-08-05 13:42+08:00 Phase 2 停止：Base 9/12 accepted、2 timeout

- Jan/2050 与 Jun/2060 均在约 `86,400 s` 触发 `TIME_LIMIT`；Crossover 分别耗时
  `79,706.97/78,531.93 s`，日志为 `Crossover changed status from Optimal to Time Limit`。
  两根无 QC/result manifest/planning state；Jan/Jun sequence `HARD_FAIL`，Jan/2060 未运行。
- Oct/2060 严格接受：objective `2,644,370.958385 million CNY`、runtime `18,714.463 s`、
  Barrier/simplex `207/1,846,030`、peak `20.118 GiB`，contract/QC/58 checks/input/result
  manifests/Pi 全部 PASS，counterflow 与 storage/V2G overlap 0。Oct 四年 Base sequence PASS。
- Oct runner 在自动启动 V5 前因 memory PSI avg10 `0.54/0.54` fail-closed 为
  `RESOURCE_GATE_BLOCKED`；三个窗口 V5 均未启动，也不存在 V5 root。当前所有 runner/
  solver 已退出，Base 总计 `9 accepted / 2 TIME_LIMIT / 1 not run`。
- 13:42 available `116,236 MiB`、swap `596/2047 MiB`、实时 `si/so=0/0`、memory/IO PSI 0；
  ParaCloud 空，server clean `3f123f0`。不 resume 或重标失败根；下一步先做新 profile A/B。

## 2026-08-05 00:26+08:00 Base 8/12 accepted；两根 Crossover 数值风险

- Oct Base/2050 新增严格接受：`OPTIMAL + contract/QC PASS + 58/58 + Pi + current input +
  valid result manifest`，objective `2,570,488.097027 million CNY`、runtime `66,128.573 s`、
  Barrier/simplex `238/1,113,083`、peak `19.916 GiB`；counterflow、storage/V2G overlap 0。
- Jan Base/2050 与 Jun Base/2060 仍在 Crossover/simplex，runtime 约 `81,826/64,975 s`；
  中间 primal/dual infeasibility 分别约 `3.79e39/1.18e6` 与 `5.91e40/4.91e7`。Jan 距
  `86,400 s` TimeLimit 约 1.27 h。它们尚无终态，不提前判失败，但风险显著。
- Oct Base/2060 已进入 model build，尚无 Gurobi log；V5 未启动。host available
  `74,239 MiB`、swap `623/2047 MiB`、最新 `si/so=0/0`、memory PSI avg10/60
  `0.02/0.08`、IO PSI `4.70/1.93`、`/data` 余 `3.7 TiB`；control stderr 0，ParaCloud 空。
- server repo 保持 clean `3f123f0`。继续只读监控，不改活动参数、不启动第四条或部署 docs。

## 2026-08-04 13:57+08:00 Base 累计 7/12 accepted；三个下一年度活动

- 新增 Jan/2040、Jun/2050、Oct/2040 三根严格接受，均为 `OPTIMAL + contract/QC PASS +
  58/58 + Pi + current input + valid result manifest`，manifest commit `3f123f0`、72 files，
  counterflow、storage overlap、EV V2G overlap 均为零。
- Jan/2040 objective/runtime/Barrier/simplex/peak 为
  `2,695,375.706199 million CNY / 35,113.316 s / 295 / 775,050 / 19.266 GiB`；Jun/2050 为
  `2,653,537.909967 / 23,990.239 / 208 / 1,065,097 / 19.859 GiB`；Oct/2040 为
  `2,624,367.338789 / 33,408.641 / 204 / 960,431 / 20.706 GiB`。
- 当前 Jan Base/2050、Jun Base/2060、Oct Base/2050 均在 Crossover/simplex；V5 roots 均
  尚不存在。13:57 available `74,374 MiB`、swap `507/2047 MiB`、最新 `si/so=0/0`、
  memory/IO PSI 0、`/data` 余 `3.7 TiB`；全部 control stderr 0，ParaCloud 队列为空。
- server repo 保持 clean `3f123f0`。继续只读监控，不启动第四条/独立 V5，不改参数或部署
  后续 docs tip；活动 Crossover 中间 infeasibility 不作为终态判断。

## 2026-08-04 00:50+08:00 Jun/2040 与 Oct/2030 严格接受；三条 Base 继续

- Jun Base/2040 与 Oct Base/2030 均为 `OPTIMAL + contract/QC PASS + 58/58 + Pi +
  current input + valid result manifest`，manifest commit `3f123f0`、72 files，输入/结果
  validators 均 `(true, [])`；counterflow、storage overlap、EV V2G overlap 均为零。
- Jun/2040 objective `2,678,562.527479 million CNY`、runtime `26,056.710 s`、
  Barrier/simplex `227/850,993`、peak `18.632 GiB`；Oct/2030 objective
  `2,316,701.874843 million CNY`、runtime `34,852.144 s`、`223/1,071,575`、peak
  `21.158 GiB`。年度与控制 stderr 均 0 bytes。
- 当前活动：Jan Base/2040 PID `1152769` 与 Oct Base/2040 PID `2270187` 均在
  Crossover/simplex；Jun Base/2050 PID `2949044` 在 Barrier。三个 runner/sequence 均活动，
  尚无 V5 solve。00:48 available `70,941 MiB`、swap `507/2047 MiB`、实时 `si/so=0/0`、
  memory/IO PSI 0、CPU 约 `65--66% idle`、`/data` 余 `3.7 TiB`；ParaCloud 为空。
- server repo 保持 clean `3f123f0`。继续只读监控，不启动第四条/独立 V5，不改参数或部署
  后续 docs tip；新年度必须重复完整终态审计后才能记为 accepted。

## 2026-08-03 17:25+08:00 Jan/Jun Base 2030 严格接受；2040 活动中

- Jan/Jun Base 2030 均为 `OPTIMAL + contract/QC PASS + 58/58 + Pi + current input + valid
  result manifest`，且 storage/V2G overlap 0、counterflow strict zero。Jan runtime
  `24,157.126 s`、Barrier/simplex `251/751,916`、peak `19.022 GiB`；Jun runtime
  `25,642.054 s`、`218/914,644`、peak `19.366 GiB`。
- 两条已用 accepted planning state 自动进入 Base/2040；17:25 Jan Barrier 128、Jun 107。
  Oct Base/2030 仍在 Crossover，约 1.008m simplex iterations，尚无 solve/QC/result manifests。
- host available 约 `73.2 GiB`，实时 `si/so=0/0`、memory/IO PSI 0、磁盘余 `3.7 TiB`；
  所有 stderr 0，ParaCloud 为空。server checkout 固定 `3f123f0`，不启动第四条、不部署 docs tip。

## 2026-08-03 10:45+08:00 Phase 2 三个季节窗口均已启动

- Jan/Jun 两实例 max solver memory 为 `20.91/21.42 GiB`，历史峰值约 `23.13 GiB`；作者授权
  将第三实例按 24 GiB 规划，并以启动 available `>=56 GiB`、预计后备 `>=32 GiB` 替代此前
  48 GiB 保守 reserve。该变更只影响资源调度，不改 LP、profile 或 strict acceptance。
- Oct PID `4173801`，Base 根 `planning_sequence_2030_2060_744h_oct6552_3f123f0_base_v1`，
  scope `[6552,7296)`；启动 available `62,007,656 KiB`、`si/so=0/0`、PSI 0，stderr 0。
  专用 runner SHA256 `e22f1696445b88458b1927fc1e803ca8ae7ec8c2f00ccf34f2c8feb6111c6be1`。
- 当前 Jan/Jun/Oct 三条均先运行 Base 四年，再由各自 runner 自动接续 V5 四年。不得提前独立
  启动 V5，不得启动第四条；server checkout 固定 `3f123f0`，活动期间只读监控。

## 2026-08-03 08:56+08:00 Phase 2 Jan/Jun-15 两条窗口活动中

- server clean checkout 冻结在 `3f123f0`；模型实现仍为 `b2206d9`。control root
  `/data/zz2/National_model/run_control/phase2_3f123f0_v1`，runner SHA256
  `db8adbfa18821d5dd09875cf8eee7301b557172c9189c9c140e5b93c95fafa1c`。
- Jan PID `3742233`：Base 四年根 `planning_sequence_2030_2060_744h_jan0_3f123f0_base_v1`，
  2030 scope `[0,744)`；Jun-15 PID `3746869`：Base 四年根
  `planning_sequence_2030_2060_744h_jun15_3960_3f123f0_base_v1`，scope `[3960,4704)`。
  两者均为 correct Base/test-only/Crossover=2/no-basis，当前处于 2030 build。
- 08:56 available `117,797,340 KiB`、`si/so=0/0`、memory PSI 0；两个 window stderr 和
  两个 Base stderr 均为 0。当前恰有两个授权槽位，禁止第三条；Oct 等任一窗口完整 Base→V5
  结束并复核资源后才启动。PID 存在时只读监控，不部署后续文档 tip、不切参数。

## 2026-08-03 08:51+08:00 Phase 2 门槛下调；准备立即启动 Jan Base

- 作者已明确撤销 Phase 2 新 sequence 的 `available>=96 GiB` 门槛，并允许资源证据支持时最多
  并发两条。历史实测为 process-tree peak `21.484--21.92 GiB`、solver max memory 约
  `23.13 GiB`，故单实例审计上界按 `24 GiB`，不把“20 GiB”写成硬上界。
- 新单序列启动合同：available `>=64 GiB`、`vmstat si/so=0/0`、memory PSI 0、checkout
  clean/current、目标根不存在、ParaCloud 已核验；运行中 available `<48 GiB` 时不启动下一条。
  第二并发序列还要求首实例实时内存 `<=24 GiB`、预计启动后 available `>=32 GiB`、无 swap
  I/O/PSI；最多两条。
- 08:51 server clean/idle checkout `b2206d9`，available `91,889,284 KiB`（约 `87.63 GiB`）、
  `si/so=0/0`、PSI 0、磁盘余 `3.7 TiB`，ParaCloud 空队列，全部 Phase 2 候选根不存在。
  local/origin/GitHub 为 `2ddf432`；下一步提交本合同、双推送并 fast-forward server，随后立即
  启动 `start-hour=0` Jan Base 四年 744 h sequence。
- 本次只改资源调度合同；`barrier_16_crossover2_stable_basis_long_v1.json`、严格终态验收、
  `TEST_ONLY_TRUNCATED_HORIZON` 标签均不变，仍禁止 Crossover=3、basis/MGA、8760 h 与付费云。

## 2026-08-03 03:17+08:00 Phase 1 完整闭合；Phase 2 等待资源

- `/data/zz2/National_model/run_control/phase1_b2206d9_v1` 已写出 `PHASE1_DONE`；总 stderr
  为 0。1/24/168 h Base/V5 六条四年 sequences 均 rc 0，六个 time wrapper 均 exit 0。
- 三组 A/B audits 全部 `PASS`；`phase1_strict_audit.json` 复核 24/24 年度根均为
  `OPTIMAL + contract/QC PASS + 58/58 + current input/valid result manifests + Pi`，零 failures。
  24 根 storage/V2G overlap 均为零。仅 168 h Base/V5 的 2050 各有 7 个预算内 de-minimis
  counterflow edge-hours；其余 counterflow 为 strict zero。
- 当前无 CISPO/Gurobi/sequence PID。固定服务器 clean checkout
  `b2206d9c899c8008d7b6dabdf15cc50dd286e8b7`；available RAM 约 `87 GiB`、swap
  `449 MiB/2 GiB`、`vmstat si/so=0/0`、memory PSI 0、磁盘余 `3.7 TiB`；ParaCloud 队列为空。
- Phase 2 仍要求新任务前 available `>=96 GiB`。当前只等待外部资源恢复，不降低门槛、不终止
  外部任务。满足后才部署双推送文档 tip，并严格串行执行 `744 h @ start 0/3960/6552`，每个窗口
  Base 四年后 V5 四年；继续禁止并发、basis、Crossover=3、8760 h、付费云和 MGA。

## 2026-08-02 23:16+08:00 Phase 1 已进入 168 h Base

- 1 h Base/V5 与 24 h Base/V5 四条四年 sequences 均 `rc=0`；逐根
  `OPTIMAL/PASS`，result manifests 完整，storage/V2G overlap 与 24 h counterflow 为零。
- 24 h 部分 Barrier 根以 sub-optimal 结束，但 Crossover=2 成功恢复 primal/dual feasible
  optimal；当前不关闭 crossover。
- wrapper PID `1314144` 仍活动，23:16:52 开始 168 h Base。启动 available
  `91,891,228 KiB`、`si/so=0/0`、PSI=0；无第二 CISPO solve，ParaCloud 为空。
- PID 存在期间只读监控。168 h Base/V5 均 accepted 后才执行 Phase 1 总审计；Phase 2
  仍须重新满足 available `>=96 GiB`。

## 2026-08-02 22:55+08:00 全新 Phase 1 活动中

- fixed server clean deployed `b2206d9c899c8008d7b6dabdf15cc50dd286e8b7`；生产环境
  `177/177`、readiness、release、V5 input 和 hydro 380 GW audits 全部 PASS。
- wrapper PID `1314144`，control root
  `/data/zz2/National_model/run_control/phase1_b2206d9_v1`；22:55 正在 1 h Base，后续按
  1 h V5、24 h Base/V5、168 h Base/V5 严格串行。
- 启动 available `91,919,056 KiB`、`si/so=0/0`、memory PSI 0；无第二 CISPO solve，
  ParaCloud 队列为空。PID 存在期间不 fast-forward、不改 checkout、不启动 Phase 2。

## 2026-08-02 22:49+08:00 轻微对冲流 warning 合同已在本地闭合

- 作者决定保持 current full-LP 网络结构，不为截断时域极小系统影响的 AC 对冲流增加
  MILP/方向锁复杂度。2050/168 h storage 与 EV V2G overlap 均为零，唯一异常仍是
  7 个 AC counterflow edge-hours；其 excess-loss/load 与 opposing/gross-flow 分别仅
  `9.7667e-8`、`3.4079e-5`。
- 仅将 test-only 每 168 h 的绝对 warning budgets 调整为
  `8 edge-hours / 1.25 GWh opposing / 0.04 GWh excess loss`；单小时功率、线路占比和两个
  相对系统影响门禁不变，full-year 继续 strict zero。模型与 solver 参数不变。
- 本地方向性 `7/7`、完整回归 `177/177 PASS`。服务器尚未部署本修订，也没有从旧失败根
  resume；部署与新 Phase1 roots 必须等待提交、双推送及实时 server 门禁。

## 2026-08-02 22:19+08:00 Phase 1 在 168 h Base 2050 fail closed

- Phase1 wrapper 与本项目 Python/Gurobi 均已退出。1 h Base/V5、24 h Base/V5 四条四年
  sequence 全部 PASS；逐年复验共 16 个输出均满足 `OPTIMAL + QC PASS + 58/58 + current
  input/result manifests PASS`。
- 168 h Base：2030、2040 strict PASS；2050 的 Gurobi solve/solver acceptance 均 PASS，
  但 `solution_qc=HARD_FAIL`、hard checks `57/58`。因此 runner 未生成 result manifest 或
  accepted state，并正确停止在 2050；2060、168 h V5、Phase 2 都未启动。
- 唯一失败项为 `unidirectional_interprovincial_flow`。吉林—黑龙江
  `CORRIDOR_0153`（AC，`1.646 GW`）在一周内每天 04:00 共 7 次同时双向流，opposing
  energy `1.029728 GWh`、excess loss `0.031052 GWh`，超过 168 h test-only budgets
  `4/0.75/0.025`；最大 opposing flow `0.177690 GW`，远高于 `1e-6 GW` 数值容差。
  对应边际价最低约 `-3412.05 CNY/MWh`，与负价下 lossy-sink 机制一致，不能按数值尾差放行。
- 实时 server checkout clean `fc2c5002d774e80853f4059c506a55d2befc08f0`；available RAM
  约 `87 GiB`、swap `449 MiB/2 GiB`、`si/so=0/0`、memory PSI 0；ParaCloud 队列为空。
  当前状态是“审计阻塞”，不是资源阻塞。保持现场，不 resume、不启动 Phase 2。

## 2026-08-02 19:58+08:00 Phase 1 分级内存门禁生效

- 当前 available RAM 约 `85 GiB`、`si/so=0/0`、PSI=0；外部 wind-power workers 仍在。
- current-tip 168 h 实测 process-tree peak `<=3.651 GiB`，因此仅 Phase 1 的 1/24/168 h
  允许在 `available>=64 GiB` 时启动；运行中低于 48 GiB 或出现 swap I/O/PSI 即停止后续根。
  Phase 2 仍要求 `>=96 GiB`，未放松。

## 2026-08-02 19:53+08:00 168 h V5 调优闭合；等待共享 RAM 恢复

- `d190c23` 在正确生产数据环境下专项 `30/30`、完整回归 `175/175 PASS`。一次漏设 data
  env 的完整回归调用产生 missing-file failures，显式修正五个 roots 后通过。
- 168 h V5 Crossover=2/4 均 strict PASS；solver 分别 `2021.046/2122.079 s`，simplex
  `382,382/383,134`，峰值约 `3.65 GiB`。production winner 为 Crossover=2；4 为 fallback，
  direct dual simplex 为无 Crossover fallback，3 禁止。
- 新 long production profile 为
  `barrier_16_crossover2_stable_basis_long_v1`：16 threads、Presolve=2、Crossover=2、
  CrossoverBasis=1、TimeLimit=86400 s、SoftMemLimit=80 GiB。
- 当前无 CISPO/Gurobi 进程，但 available RAM 约 `93 GiB < 96 GiB`。外部用户多条 wind-power
  worker 正在占用 RAM；swap `449 MiB/2 GiB`、`si/so=0/0`、PSI=0。不得终止外部任务；
  Phase 1 等资源恢复后才启动。

## 2026-08-02 18:35+08:00 24 h 配对通过；168 h Base 通过、V5 被旧 guard 拦截

- 服务器 clean/idle `eb4d5591723d5ed528c8326898731591937ec645`，available RAM
  `113 GiB`、swap `447 MiB/2 GiB`、`si/so=0/0`、memory PSI 0。现行数据根为
  `/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`。
- Crossover 1/2/4 的 24 h Base/V5 六根全部 strict PASS。168 h Base 的 Crossover 2/4
  也 strict PASS，solver runtime 分别 `2044.630/1822.354 s`，Crossover=4 当前总耗时更短。
- 168 h V5 两个候选没有进入 Gurobi optimize：旧代码只把 Crossover=1 识别为 stable
  basic route，均在 prebuild 后约 9.5 s fail closed。正在把允许集合最小扩展为已经 matched
  24 h 验证的 `{1,2,4}`，保留 `CrossoverBasis=1` 并永久拒绝 3。部署后用全新输出根重跑，
  不 resume 两个 prebuild-failed 根。
- Phase 1/2 尚未启动；没有 8760 h、付费云、并发第二求解、basis reuse 或 MGA。

## 2026-08-01 16:53+08:00 Phase 0 完成；Barrier-only 路线被严格门禁拒绝

- 固定服务器已部署 clean `5e7db6835db60170fad7a1a13283e2a4d16792f4`；Phase 0 的
  `175/175` 回归、readiness、显式 data-root release、Base/V5 input、hydropower 380 GW
  和 Base/V5 1 h build audit 全部 PASS。1 h build 的 Base/V5 规模分别为
  `238,529 vars/79,979 rows/452,433 nnz` 和
  `238,978 vars/80,363 rows/453,968 nnz`，process-tree peak 分别约
  `0.429/0.462 GiB`。
- 24 h Base 两轮串行参数诊断已结束，当前无活动 CISPO/Gurobi process。20 个 Barrier-only
  配置均无法同时满足严格 primal/dual contract，故无 accepted `BarPi`、QC 或 result
  manifest。`ScaleFlag=0/1/3`、`NumericFocus=3`、`Aggregate=0`、`Presolve=0/1`、
  `PreDual=1/2`、`PreSparsify=2`、threads `8/32` 和 `BarOrder=1` 均未解除 blocker。
- 同一 24 h Base LP 的 `tuning2_dual_simplex16_v1` 严格通过：solver
  `795.205647945404 s`，`524,890` simplex iterations，process-tree peak
  `0.692 GiB`，`OPTIMAL_BASIC_OR_DEFAULT/PASS`、QC `58/58`、input/result manifest
  validators 均 PASS，dual attribute 为 `Pi`。这证明模型可行，问题局限于当前 Barrier
  数值路径。
- 下一步只串行测试 current-tip matched `Crossover=1/2/4 + CrossoverBasis=1`；不会运行
  `Crossover=3`、8760 h、付费云、并发第二求解、`.bas` reuse 或 MGA。通过 24 h 和 168 h
  配对门禁后才开始 Phase 1/2。

## 2026-08-01 14:18+08:00 0729 统一候选 744 h 历史根复核通过；服务器仍 idle

- 历史根
  `/data/zz2/National_model/outputs/2030_744h_v0729_unified_v4_v1g_cold_v1`
  的 PID 已退出；终态再次确认是 `OPTIMAL + solution_qc=PASS + 52/52 + valid
  result manifest + wrapper exit 0`，不是仍在 Barrier/Crossover、数值失败或异常退出。
  solver `12,984.854 s`、Barrier/simplex `313/832,655`、Crossover
  `3,573.87 s`、wall `3:42:57`、process-tree peak `21.484 GiB`、swaps 0。
- 运行提交/情景/数据身份仍为 clean `7c56622`、
  `flexible_load_comfort_v4_v1g`、744 h January cyclic window、
  `barrier_16_auto_order_v2`、no-basis，以及
  `/data/zz2/National_model/data/model_ready_20260729_unified_7c56622_v4`。
  数据归档 SHA256 复算为
  `f3e6cc0f810d0f4e1ccf8fd10907fb25b8859546be397f21035cd072cdb9d261`。
- `validate_result_manifest=(True, [])`。当前 server checkout 已前进，因此直接运行
  `validate_input_manifest` 对 3 个 repo 配置文件报告 size drift；其余 75/78 输入仍
  通过，且运行提交 `7c56622` 的 3 个 Git blob size/SHA256 与 manifest 完全一致。
  该差异是历史 run identity 与当前 checkout 的正常分离，不是结果损坏；历史验收不变，
  但不得把当前 runtime validator 误报为全绿。
- 实时 local/origin/GitHub tip 均为 `fb7cec37b552f31dcf365b859c93f2734241bb53`；
  固定服务器仍为 branch `codex/cispo-2030-full-lp`、clean `7a1520e`，无真实
  CISPO/Gurobi/planning-sequence 进程。available RAM 约 114 GiB、swap
  447 MiB/2 GiB、连续实时 `si/so=0/0`、memory PSI 0、`/data` available
  3.7 TiB；ParaCloud 队列为空。本轮没有部署或启动任何任务。
- 0729 根仍是 `TEST_ONLY_TRUNCATED_HORIZON`，不得作为年度科学结果或 2040
  state anchor。下一步继续按 `SERVER_RUNBOOK.md` 顶节执行 Barrier-primary Phase 0；
  不自动启动 8760 h、付费云、basis/MGA、并发第二求解或 `Crossover=3`。

## 2026-08-01 13:58+08:00 Barrier 主线续接实现完成；服务器仍 idle、未部署

- 新实现提交为 `53a5873156bfe4e81abfaa258d02b3f3ff664bbd`，父提交
  `19b5754bb0db12818975344e5365777674698c47`。主线现在严格接受并保存
  `Crossover=0` 的 Barrier 最优内点解；planning sequence 在 accepted checkpoint
  闭合后显式导出 nonbasic cohort state 并继续 2030→2060，不再等待 Crossover。
- 后置 Crossover 仅由作者在全部主线完成后选择年份执行。它重建 exact LP，以
  `PStart/DStart + LPWarmStart=2` 构造 basic derivative，不写 `planning_state`、
  不回溯替换序列路径。容量、调度、成本、碳和 `BarPi` dual 不以 Crossover 为门禁；
  `VBasis/CBasis`、`.bas` 和 SA sensitivity 才需要它；连续 LP 的 RC 可从非基解
  读取，但与 dual 一样在退化问题中可能不唯一。
- sequence runner 新增并锁定 `--diagnostic-start-hour`，nonbasic sequence 自动显式
  传递 checkpoint/state flags；state load 会复核 solve/QC/input/result manifests、
  checkpoint 两条向量与 identity，并记录微小 cohort 截断统计。模型方程、数据、
  Base/V5 参数和 58 项（或当前实际总数）科学 QC 均未放松。
- 本地正确 wave root 下完整回归 `175/175 PASS`，真实 Gurobi checkpoint round-trip、
  `py_compile` 和 `git diff --check` 均 PASS。
- 13:58 固定服务器仍为 branch `codex/cispo-2030-full-lp`、clean
  `7a1520eb723db7717b6ce4dd41646916c34bb0cf`，无 CISPO/Gurobi/planning-sequence
  进程；host available 约 `114 GiB`、swap `447 MiB/2 GiB`、连续采样
  `si/so=0/0`、memory PSI 0，`/data` available `3.7 TiB`。ParaCloud 队列为空。
- 本窗口没有部署或启动任何求解。下一窗口先完成四端/资源/数据实时核验和服务器
  regression/readiness/release/input/hydro audits，再按 `SERVER_RUNBOOK.md` 顶节
  严格串行运行小门禁、三季节 Base/V5 四年 744 h sequences 与长时段阶梯；主线
  禁止自动 Crossover、MGA、basis、8760 h、付费云或并发第二求解。

## 2026-08-01 12:20+08:00 Barrier-first 实现已提交；服务器仍 idle、尚未部署

- 新实现提交为 `19b5754bb0db12818975344e5365777674698c47`。它把 `>744 h`
  默认工作流改为先接受严格 `Crossover=0/SolutionTarget=1` 内点解并保存完整
  `BarX/BarPi`，可选 Crossover 在全新根以 `PStart/DStart + LPWarmStart=2`
  独立执行；科学/物理 QC 没有放松，模型约束没有改变。
- 本地正确设置 wave root 后完整回归 `174/174 PASS`，真实 Gurobi checkpoint
  round-trip PASS，`py_compile`/`git diff --check` PASS。新的 long profile 为
  `TimeLimit=86400 s/SoftMemLimit=80 GiB`；diagnostic memory gate 按
  8/32/96 GiB 阶梯向上匹配，避免长 diagnostic 被错误的 8 GiB 门禁放行。
- 12:20 实时固定服务器仍为 branch `codex/cispo-2030-full-lp`、clean
  `7a1520eb723db7717b6ce4dd41646916c34bb0cf`，尚未部署 `19b5754`；只读进程复核
  仅看到审计命令自身，无 CISPO/Gurobi/planning-sequence solver。host 总内存
  `125 GiB`、available 约 `113 GiB`、swap `447 MiB/2 GiB`，最新
  `vmstat si/so=0/0`、memory PSI avg10/60/300 均为 0。ParaCloud 队列为空。
- 本窗口没有启动 Base/V5、744 h、长时域、8760 h 或付费云任务。下一窗口必须先
  等 local/origin/GitHub 文档 tip 一致，再实时核验并 fast-forward 服务器、运行完整
  audits；详细五季节 744 h 配对和长度阶梯见 `SERVER_RUNBOOK.md` 顶节。任何 PID
  存在时只读监控，仍禁止并发第二求解、`Crossover=3`、MGA/basis 和自动 8760 h。

## 2026-08-01 05:52+08:00 reservoir-native Base 744 h 已 TIME_LIMIT；V5 未启动

- 当前 local/origin/GitHub/server 均为
  `7a1520eb723db7717b6ce4dd41646916c34bb0cf`；固定服务器 branch
  `codex/cispo-2030-full-lp`、worktree clean、无 CISPO/Gurobi 进程。
- Base 输出根
  `/data/zz2/National_model/outputs/2030_744h_v0731_reservoir_native_ub_7a1520e_base_stablebasis_v1`
  已结束。`solve_report.json` 为 `TIME_LIMIT/status_code=9`、`SolCount=0`、
  solver `21,601.01 s`；wrapper exit 2、wall `6:05:29`、stderr 0、MaxRSS
  `19,702,352 KiB`、process swaps 0。
- Barrier 为 218 iterations/`6,900.02 s`/objective `2,352,092.16 million CNY`；
  Crossover 重启后 push phase 仍有 `PInf=6.459046`、`DInf=1.0102534e5`，
  cleanup 报告 basis variable drop 与 quad precision，最终 crossover
  `14,528.04 s`、746,438 simplex iterations，并把 Barrier `Optimal` 改为
  `TIME_LIMIT`。
- `input_manifest.csv` 当前且 validator 为 `(True, [])`，SHA256
  `99842464c22371d15e757bcc6db76490060a74bbb944961ed1be6cbdef40d6e4`；无
  `solution_qc.json`，故 58 项 solution hard checks 未执行；无
  `result_manifest.json`，validator 返回 missing。所有解后 physics/accounting
  输出均未形成，不能审计或解释。
- 候选 V5 输出/控制根均不存在，不得启动。Base 自身已复现同类 crossover
  blocker，说明它不是 V5 独有问题。available RAM 约 `114 GiB`、系统 swap
  `447 MiB/2 GiB`、实时 `si/so=0/0`、memory PSI 0，ParaCloud 队列为空。
- 下一步只允许保留失败根并做 shared-core 数值诊断；重新通过匹配
  1 h/24 h/168 h Base/V5 门禁前，不运行新的 744 h。继续禁止 8760 h、付费云、
  并发、basis/MGA 与 `Crossover=3`。

## 2026-07-31 20:41+08:00 summer 744 h 已 TIME_LIMIT；nonbasic 修复待部署

- 旧活动根
  `/data/zz2/National_model/outputs/2030_744h_v0731_summer_offset_a7c6715_v5_v1`
  已终止：`TIME_LIMIT`、`SolCount=0`、solver `21,600.80 s`、Barrier
  `233/7,414.52 s`、Crossover `13,917.15 s`、simplex 1,069,484。
  无 `solution_qc.json`、无 `result_manifest.json`；wrapper exit 2、wall
  `6:05:39`、MaxRSS `22,364,408 KiB`、swaps 0、stderr 0。结论是
  Crossover cleanup 工程失败，不是 Barrier、RAM 或 swap 失败。
- 本地实现提交 `8de7a8e5bf4712bac30472fc4a564f47462fd9cd` 新增 Gurobi 13+
  strict optimal primal-dual nonbasic 诊断路线、`BarPi` dual、未接受解的
  fail-closed 导出合同，以及 annual load-center 每边 0.1 MWh 的显式数值尘埃
  阈值；没有改变冷热/EV/可靠性/成本模型。完整回归 `169/169 PASS`。
- 本地 Gurobi 12 的 1 h Base/V5 可严格闭合，但 24 h Base 返回
  `SUBOPTIMAL/HARD_FAIL`；该 profile 因已知版本风险明确要求 Gurobi 13。
  因而尚未声称该路线适用于 744/8760 h。
- 20:41 服务器仍为 clean `aaf16cc49a5a3d5bb07d214a957a3a4065ac3f07`，
  无 CISPO/Gurobi/National_model 进程；available RAM `114 GiB`、swap
  `447 MiB/2 GiB`、实时 `si/so=0/0`、memory PSI 0；ParaCloud 队列空。
- 下一步：待文档 tip 推送后重新核验，fast-forward 并运行服务器完整回归/
  readiness/release/input audits；随后串行执行 hour 3960 起点的 1 h 与 24 h
  Base/V5 nonbasic 配对。任一失败即淘汰候选并停止；成功后才执行配对 168 h，
  再依次执行 same-window Base/V5 744 h。禁止 8760 h、付费云、并发、basis/
  MGA 与 `Crossover=3`。

## 2026-07-31 16:49+08:00 summer 744 h 正在 Crossover/simplex cleanup（已由上节终态取代）

- Barrier 已在 iteration `233`、runtime `7,414.52 s` 报告 optimal objective
  `2,351,134.66 million CNY`；末行 primal/dual infeasibility 与
  complementarity 为 `2.26e-4/2.27e-8/1.82e-9`，日志无
  `Numerical trouble`。
- crossover basis 构建后 DPush/PPush 于 `9,652 s` 完成；16:48 最新
  simplex iteration `912,630`、runtime `11,752.76 s`、objective
  `2,351,203.328 million CNY`、primal infeasibility 0、dual
  infeasibility `2.014e6`。近期 dual 指标显著振荡，当前未收敛，也尚无正式
  失败状态。
- 唯一 PID 链仍存活；server clean `aaf16cc`，stderr 0。solver current/max
  memory `16.36/23.50 GiB`，host available RAM 约 `100 GiB`，swap
  实时 `si/so=0/0`，memory PSI 0；ParaCloud 空。
- `solve_report.json`、`solution_qc.json`、`result_manifest.json` 均不存在。
  `TimeLimit=21,600 s`；继续只读监控，禁止改 checkout 或启动第二任务。

## 2026-07-31 13:29+08:00 summer 744 h V5 cold gate 正在构建

- 唯一活动输出/控制根均为
  `2030_744h_v0731_summer_offset_a7c6715_v5_v1`；启动提交为 clean
  `aaf16cc49a5a3d5bb07d214a957a3a4065ac3f07`，wrapper/Python PID 初始
  `674143/674145`，启动于 `2026-07-31T13:27:06+08:00`。
- 实时 scope 为 model hour `[3960,4704)`，北京时间 2030-06-15 00:00 至
  07-15 23:00，V5 central、744 h carbon/resource scaling、no-basis、
  `Crossover=1/CrossoverBasis=1` 均正确。
- 13:29 仍处于 build，Python RSS 约 `1.68 GiB`；尚无
  `build_report/solver_telemetry/gurobi.log`，stderr 0。available RAM
  约 `112 GiB`、swap `780 MiB/2 GiB`、实时 `si/so=0/0`、memory PSI 0，
  ParaCloud 队列为空。
- PID 存在时仅监控，不修改服务器 checkout、不启动第二任务。该根仍为
  `TEST_ONLY_TRUNCATED_HORIZON`；终态必须执行完整严格审计。

## 2026-07-31 13:27+08:00 summer 1 h/24 h 小门禁已严格接受

- 固定服务器部署 `11c682076869e30e0ed24db038bf3c12ecdbb1ae` 后完整回归
  `167/167 PASS`。全新 summer 1 h Base v2 与 24 h V5 v2 均达到
  `OPTIMAL + solution_qc=PASS + 58/58 + current input + valid result
  manifest + wrapper exit 0/stderr 0`，失败 v1 未复用。
- 1 h Base v2 solver runtime `4.966 s`、Barrier/simplex `92/1,134`、
  wall `0:34.02`、MaxRSS `498,444 KiB`、swaps 0；`time_index.csv`
  从 model hour 3960、`2030-06-15 00:00` 开始。
- 24 h V5 v2 solver runtime `115.226 s`、Barrier/simplex `243/29,002`、
  wall `2:38.15`、MaxRSS `962,928 KiB`、swaps 0。Barrier 的
  sub-optimal warning 由 crossover 恢复为 `Optimal`，无
  `Numerical trouble`；最大 constraint/bound/dual violation
  `3.242e-8/2.980e-11/2.025e-13`。
- 24 h V5 cooling up/down `2.1335/1.6170 GWh`，storage
  charge/discharge `187.9103/162.4830 GWh` 且无同充同放；EV mobility
  charge `152.998 GWh`、V1G relocated `43.3376 GWh`、本日 V2G export
  为 0。缩放碳上限 `10.958904 MtCO2` binding。全部 58 项 hard QC
  覆盖冷热、EV、wave、水电、PHS/储能、网络、备用、惯量、碳/CCS/BECCS
  和成本 accounting scope。
- 下一步只允许部署包含本记录的文档 tip 后启动一个
  `/data/zz2/National_model/outputs/2030_744h_v0731_summer_offset_a7c6715_v5_v1`
  cold gate；窗口 `[3960,4704)`，profile
  `barrier_16_auto_order_stable_basis_v3.json`，no-basis、
  no-concurrency。仍禁止 8760 h、付费云、basis/MGA 与 `Crossover=3`。

## 2026-07-31 13:18+08:00 首个 summer 1 h build failure 已最小修复

- `985983b` 已部署且 server `166/166` regression、readiness、release、
  V5 input 与 hydro audits 全 PASS；但首次 summer hour 3960 Base 1 h
  在 build 阶段因空 CHP winter 索引触发 Gurobi `AssertionError`。无
  `build_report/solve_report/solution_qc/result_manifest`，不是 solver
  失败或可接受根。
- 失败输出/控制根以 `...summer_offset_985983b_base_v1` 原样保留，wrapper
  exit 1、wall `0:23.75`、MaxRSS `493,580 KiB`、swaps 0。
- 修复提交 `a7c67153d9b90055b60ed2704ef6bba702086ae4` 仅跳过空 winter
  constraint set，并把完整模型测试固定到 hour 3960；本地
  `167/167 PASS`。部署后必须用全新 `v2` 根重跑，禁止复用 v1。

## 2026-07-31 13:10+08:00 summer-offset 744 h 候选待部署

- 实现提交 `077bce0eca16b1025130143122aee0a05559c3e0` 为诊断 runner
  增加一致的非年初连续窗口合同；不改变冷热、V1G、V2G、firm credit、
  年度流量缩放或 solver 科学边界。夏季 744 h 定义为 model hour
  `[3960,4704)`，对应 2030-06-15 00:00 至 2030-07-15 23:00。
- 本地完整回归在正确 wave 根下为 `166/166 PASS`；窗口数据核验 cooling
  为 `147,056.322 GWh`，显著高于年初 744 h 的 `68.469 GWh`。该证据只
  说明测试覆盖更强，不构成结果接受。
- 当前服务器尚未部署该提交，也尚未启动新任务。部署前必须重新核验
  本地/origin/GitHub/server HEAD、server clean/idle、RAM/swap/vmstat/PSI、
  目标根不存在与 ParaCloud 空队列。部署后先串行运行 1 h Base 和 24 h V5
  offset gates；两根严格接受后才允许一个 2030/V5 744 h cold gate。
  长时段 V5 固定使用
  `config/solver_profiles/barrier_16_auto_order_stable_basis_v3.json`，
  no-basis、no-concurrency。744 h 仍为 `TEST_ONLY_TRUNCATED_HORIZON`；
  禁止 8760 h、付费云、basis/MGA 和 `Crossover=3`。

## 2026-07-31 12:45+08:00 当前提交的 24 h/168 h 匹配门禁闭合

- 当前本地、`origin`、GitHub 与固定服务器任务身份均为
  `ae3356391ec55376b041d6a356ea2d1f26be88bc`；服务器 checkout clean。
  本地/服务器完整回归均 `165/165 PASS`，服务器 readiness、release、
  V5 input 与 hydro audits 全部 PASS，水电容量为
  `297.8895 + 82.1105 = 380.0000 GW`。本机 `7.91 GiB < 8 GiB`，未绕过
  内存门槛启动 Windows solver。
- 当前提交的 24 h Base/V5 production-profile 根均为
  `OPTIMAL + PASS + 58/58 + current input + valid result manifest +
  wrapper exit 0/stderr 0`。solver runtime `407.321/420.232 s`，
  wall `7:28.51/7:44.38`，RSS `0.761/0.794 GiB`。
- 168 h Base-v2、Base-v3、V5-v3 三根也全部严格接受。solver runtime
  `907.672/917.121/1024.510 s`，wall
  `16:54.30/17:03.75/18:54.89`，RSS `3.336/3.328/3.508 GiB`，
  Barrier/simplex `213/211003`、`213/185333`、`232/258814`。
  Base 两 profile 的 objective 仅差 `2.9e-7 million CNY`。
- V5 168 h 使用
  `config/solver_profiles/barrier_16_auto_order_stable_basis_v3.json`。
  production-v2 尝试在 optimize 前被既有 guard 正确拒绝，控制根
  `/data/zz2/National_model/run_control/2030_168h_v0731_ae33563_v5_v2prod_v1`
  记录 `exit=1` 与 RuntimeError；无 solve/QC/manifest，不是求解失败根。
- 同 profile V5 相对 Base objective `-298.097 million CNY`，发电容量
  `-2.915 GW`，firm credit `2.891320 GW`，所选窗口 effective peak
  `-1.663365 GW`。adequacy 仍使用完整 8760 h immutable baseline peak，
  未直接使用 effective peak 降容。V5 EV fleet charge/V1G relocated/V2G
  export 为 `756.192/193.242/1.178 GWh`；周期 SOC 与驾驶取能闭合。
- 全部 58 项 hard QC 覆盖冷热/EV、wave、水电/梯级、PHS/储能、网络、
  备用、惯量、碳/CCS/BECCS 与成本。碳限额 `76.712329 MtCO2` binding；
  objective residual `-1.774e-7 million CNY`。截断解释边界仍包括：
  冬季首周无冷热实际移峰却存在全年峰窗 cooling credit；水文 raw clip
  等价量 `974.405 million m3`，需后续科学敏感性。
- 终态服务器无 CISPO/Gurobi，available RAM 约 `114 GiB`，swap
  `780 MiB/2 GiB`、`si/so=0`、memory PSI 0；ParaCloud 队列为空。
  全部结果仍为 `TEST_ONLY_TRUNCATED_HORIZON`。下一步由作者决定四年
  168 h Base/V5 sequence 或单一更长门禁；不自动启动 744/1008/8760 h、
  付费云、basis/MGA、并发第二求解或 `Crossover=3`。

## 2026-07-31 10:15+08:00 固定结果 dashboard 已部署并闭合

- 结果查阅实现提交为 `336116b493cf92eb461d1a2aab490678fd2dbac5`，
  最终解释修正为 `bdb57b2cb4e3f4781cfd53c087c7cc1a780d73a5`。
  dashboard 本身不改变 LP、数据、目标或 solver；冷热、V1G、V2G 与 firm
  credit 的服务模式保持不变。前一数值稳定化中唯一新增的物理约束仍是
  V1G/V2G 共享签约连接功率上限，不应与本轮图表改造混为一谈。
- 本地完整回归 `162/162 PASS`；可用内存 `7.64 GiB < 8 GiB`，没有绕过
  门槛启动本地 solver。服务器在 `336116b` 上完整回归 `162/162 PASS`，
  readiness、release、V5 input、hydro audits 均 PASS，常规水电仍为
  `297.8895 + 82.1105 = 380.0000 GW`；最终 `bdb57b2` 的 dashboard
  聚焦测试 `3/3 PASS`。
- 最终服务器根
  `/data/zz2/National_model/outputs/2030_1h_v0731_dashboard_v5_bdb57b2_server_v1`
  为 `OPTIMAL + solution_qc=PASS + 58/58`，current input/result manifest
  均 `(True, [])`，result manifest 的 Git identity 精确为 `bdb57b2`。
  wrapper exit 0、stderr 0 bytes、wall `0:39.10`、MaxRSS
  `597,624 KiB`、swaps 0；solver runtime `7.352116 s`，Barrier
  96、simplex 1,716，最大 constraint/bound/dual violation
  `0/4.441e-16/0`。
- `result_dashboard_summary.json`、`result_analysis_metrics.csv` 和
  `visualizations/core_result_dashboard.svg` 均存在、进入 output catalog，
  并由最终 result manifest 校验。1 h 的规划/运行成本强度分别为
  `0.2003156/0.3141334 CNY/kWh`；由于时域不同，全年 total 强制为
  `null`，不得相加或表述为 LCOE。objective 重构残差为
  `-9.779e-9 million CNY`。
- 当前服务器 checkout clean，无 CISPO/Gurobi 进程，available RAM 约
  114 GiB、swap 780 MiB/2 GiB、实时 `si/so=0`、memory PSI 0；
  ParaCloud 队列为空。该输出仍是 `TEST_ONLY_TRUNCATED_HORIZON`。
  下一次获准的门禁直接复用固定 dashboard 合同；不自动启动
  744/1008/8760 h、付费云、basis/MGA、并发求解或 `Crossover=3`。

## 2026-07-31 05:14+08:00 V5 168 h 数值稳定化门禁严格通过

- 当前本地/origin/GitHub/固定服务器部署基线均为
  `22e19c154148fcfcb137d5a7e882ff69abd2b7c8`，服务器 checkout clean；
  模型实现提交为 `fead34334153eca32bbf7ec3651f3388038ac04b`。服务器
  `159/159` regression、readiness、release、V5 input、hydro 与 380 GW
  容量审计全部 PASS。
- 新建 Base/V5 1 h 与 24 h 四根均为
  `OPTIMAL + solution_qc=PASS + 58/58 + current input + valid result
  manifest + wrapper exit 0`。24 h Base/V5 solver runtime 为
  `408.850/421.015 s`，两者均有 Barrier `Numerical trouble` 后的严格
  crossover 恢复；V5 的规模/时间增量仅为
  `+5,321 vars / +5,934 rows / +30,045 nz / +3.0% solver time`。
- 唯一 168 h V5 根
  `/data/zz2/National_model/outputs/2030_168h_v0731_v5_numeric_central_22e19c1_server_v1`
  已严格接受：`OPTIMAL + PASS + 58/58`，current input/result manifest
  均 `(True, [])`，wrapper exit 0、wall `18:38.92`、RSS `3.511 GiB`、
  swaps 0。raw/presolved 矩阵为
  `1,209,095/1,060,576/9,755,329` 与
  `737,850/751,223/7,386,987`。Barrier 232 次/819.54 s 后
  `Sub-optimal`，但无 `Numerical trouble`；`CrossoverBasis=1` 用
  176.79 s 改为 `Optimal`，最终 solver 1005.194 s、258,814 simplex，
  最大 constraint/bound/dual violation 为
  `8.339e-8/2.609e-8/6.047e-8`。
- 冷热、EV 共享连接、V1G/V2G nesting/全国上限、firm credit、网络方向、
  水电/梯级、储能、备用、惯量、碳/CCS/BECCS、成本 scope 均无 hard
  failure；诊断碳限额 `76.712329 MtCO2` binding。旧式 V1G daily-energy
  residual 对 V5 的 SOC/驾驶取能服务账户不适用，实际 SOC transition
  residual 为 `2.537e-13 GWh`；需后续修正输出语义，不是本次解的漏约束。
- 当前无 CISPO/Gurobi 进程，约 111 GiB available，swap 约 780 MiB
  但 `vmstat si/so=0`、memory PSI 0；ParaCloud `squeue` 为空。该根仍是
  `TEST_ONLY_TRUNCATED_HORIZON`，`Kappa≈1.62e10`，候选 profile 还不是
  production。下一步只允许同身份匹配 Base 168 h 与只读矩阵缩放审计；
  不自动启动 744/1008/8760 h、付费云、basis/MGA、第二求解或
  `Crossover=3`。

## 2026-07-31 04:21+08:00 V5 数值根因已结构修复，待部署服务器短门禁

- 本地实现提交为 `fead34334153eca32bbf7ec3651f3388038ac04b`；当前
  origin/GitHub 与固定服务器仍为 clean
  `cf265f365c85f8bb9aa8c18880cba04f095fc982`，尚未部署新提交。
- 旧 V5 2030/168 h 终态是 `TIME_LIMIT + Numerical trouble`，不是可接受
  结果：Barrier 210、solver 21,600.187 s、simplex 3,488,935、无解、
  无 QC、无 result manifest；wrapper 峰值 RSS 约 3.47 GiB、swaps 0。
  2040--2060 未启动。
- 最终本地 168 h 矩阵审计：raw
  `1,209,095 rows / 1,060,576 vars / 9,755,331 nz`，presolved
  `737,850 / 751,222 / 7,386,903`；raw/presolved 最大系数同为 6,250，
  presolve amplification `1.0`。旧模型对应放大比为 `51.094`。
  完整回归 `159/159 PASS`，V5 input/release/hydro audits PASS。
- 04:12 实时服务器为 clean `cf265f3`、无真实 CISPO/Gurobi 进程、约
  114 GiB available、swap 780 MiB/2 GiB 且 `vmstat si/so=0`、memory
  PSI 0；ParaCloud `squeue -u a8s001819` 为空。本地 Windows 只有约
  7.9 GiB available，1 h gate 在 `optimize()` 前由 8 GiB 门槛拒绝。
- 下一步：推送后再次实时核验，再 fast-forward 到精确提交；先跑服务器
  `159/159`、readiness/release/V5/hydro，再串行运行全新 Base/V5
  1 h 与 24 h，全部达到 `OPTIMAL + QC PASS + 58/58 + current input +
  valid result manifest` 后，才允许单独启动 2030/V5 168 h。仍禁止
  744 h、8760 h、四年 sequence、付费云、basis/MGA、并发第二求解和
  `Crossover=3`。

## 2026-07-30 21:29+08:00 test-only 对冲流 warning 已实现，待部署

- 实现提交 `9b6e72a` 保持模型与 `1e-6 GW` 检测不变，只把同时满足七项上限的截断时域微小 AC 对冲流标为 `TEST_ONLY_DE_MINIMIS_WARNING`；任一上限超限仍 hard fail，8760 h 始终 strict zero。原 2050 事件对应额外损耗仅 `0.011489 GWh`、占系统负荷 `4.0100e-8`，在新合同内，但不会被写成“严格单向”。
- 本地 `146/146 PASS`，V5 input/release audits PASS。本机约 `7.48 GiB` available，低于 8 GiB solver gate，故没有强行本地求解。
- 服务器尚未部署，仍为 clean `af390fa`；21:28 实时无 CISPO/Gurobi/sequence，约 `114 GiB` available、swap 无进出、PSI 0，ParaCloud 空。代码/文档双端推送后才允许 fast-forward。
- 部署后顺序固定为 server regression/audits → 新 1 h/24 h Base/V5 → 新四年 168 h Base → 新四年 168 h V5。全部接受后启动一个四年 `1008 h` V5 串行门禁；不得跳过短门禁或复用失败 state。仍禁止 8760 h、付费云、basis/MGA、第二求解和 `Crossover=3`。

## 2026-07-30 19:38+08:00 168 h Base 在 2050 网络方向 hard QC 停止

- 当前无 CISPO/Gurobi/planning-sequence 进程。固定服务器保持 clean `af390fad22dc4e3ec4636edadfb56295e4907234`，约 `114 GiB` available RAM，swap `780 MiB/2.0 GiB` 且 `vmstat si/so=0`、memory PSI 0；ParaCloud `squeue -u a8s001819` 为空。本地/origin/GitHub 文档 tip 均为 `134af0f`。
- Base 输出根 `/data/zz2/National_model/outputs/planning_sequence_168h_v0730_flex_v5_base_af390fa_server_v1` 为 `sequence_report=HARD_FAIL`。2030/2040 已 accepted，input/result manifests 均由当前 runtime validator 返回 `(True, [])`；2050 Gurobi 为 `OPTIMAL`，但 `solution_qc=HARD_FAIL`，缺少 `result_manifest.json` 和 planning state，2060 未启动。V5 尚未启动。
- 2050 唯一失败 hard check 为 `unidirectional_interprovincial_flow`。`CORRIDOR_0153`（吉林—黑龙江、AC、`1.646 GW`）在 hour 28/94/95 同时有正反向流：较小方向分别为 `0.083989/0.176374/0.120643 GW`，累计 `0.381006 GWh`。这远高于 `1e-6 GW` QC 容差，不能放宽阈值。
- 机制证据：2050 `168/8760` 缩放后的净碳上限 `-1.917808 MtCO2` 精确 binding，碳 scarcity `3589.731 CNY/tCO2`；违规小时吉林/黑龙江电价约 `-1405/-2338/-3650 CNY/MWh`。少量对冲流通过额外线路损耗消纳 BECCS 驱动的过剩电量，现有 `1.004004 CNY/MWh` 毛流量成本不足以阻止该行为。
- wrapper exit 1、wall `49:20.77`、MaxRSS `3,741,888 KiB`、swaps 0；2030/2040 stderr 为 0 bytes，2050 stderr 明确为 production QC RuntimeError。保留失败根，不续跑、不补写 manifest、不重标。下一步必须先评审 AC 方向性修复；严禁自动启动 V5、744 h、8760 h、付费云、basis/MGA、第二求解或 `Crossover=3`。

## 2026-07-30 16:58+08:00 V5 服务器预门禁与 24 h A/B 已闭合

- 固定服务器 clean checkout 为 `af390fad22dc4e3ec4636edadfb56295e4907234`，数据根为 `/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`。跨 Windows/Linux 的 V5 五表和 manifest 已由 `4f717de` 固定为逐字节一致；`af390fa` 恢复继承权威技术经济 manifest。V5 manifest SHA256 为 `a324430713e0eb3a1671c9b9ba6c127c34c5e0d7c2e21f090cbcd9394f061831`。
- 本地/服务器完整回归均 `141/141 PASS`；服务器 readiness、V5 input、release、水电审计均 PASS。水电容量闭合为 `297.8895 + 82.1105 = 380.0000 GW`。
- 2030/24 h Base/V5 根均为 `OPTIMAL + PASS + 57/57 + current input + valid result manifest + wrapper exit 0`。solver runtime `405.882/434.896 s`，peak RSS `0.759/0.797 GiB`，swaps 0。两者 Barrier 均 numerical trouble 后由 `Crossover=1` 修复，simplex `503,365/519,659`。
- V5 相对 Base 的 objective、firm credit、发电装机变化分别为 `-347.394 million CNY`、`+2.891320 GW`、`-2.891320 GW`；显式 flexibility cost `785.531 million CNY`。领先 24 h 的全国 effective peak 只下降 `2.1692 GW`，不可解释为年度峰值价值，因为 capacity adequacy 使用完整 8760 h 各省 baseline-peak 服务窗口。
- 下一步：服务器 checkout 保持 `af390fa` 冻结，先运行唯一串行四年 168 h Base；严格闭合后再运行 V5。168 h A/B 未全部接受前不启动 744 h；继续禁止 8760 h、付费云、basis/MGA、并发第二求解和 `Crossover=3`。

## 2026-07-30 16:05+08:00 V5 已提交；本地 168 h 被内存门禁阻止，服务器暂不部署

- 集成需求侧灵活性 V5 实现与中英文补充材料提交为 `57ad4c5`。Base 不变；唯一中央反事实联合冷热、付费 V1G、内生付费 V2G 和四小时峰值可交付的折减 firm capacity credit。完整本地回归 `140/140 PASS`，V5 输入/release 审计均 PASS。
- 1 h 当前输出合同 V5 根 `outputs/2030_1h_v0730_flex_v5_central_gate_v3` 为 `OPTIMAL + PASS + 57/57 + current input + valid result manifest`。24 h Base/V5 数学根均 `OPTIMAL + PASS + 57/57 + closed manifests`；V5 的 selected-window peak/firm credit/generation-capacity changes 分别为 `-2.3211/+2.8913/-2.8913 GW`。两根均在 Barrier 数值困难后由 `Crossover=1` 修复，V5 耗时 `727.286 s`。
- 本地 `outputs/planning_sequence_168h_v0730_flex_v5_base_v1` 在求解前因 available RAM `6.07 GiB < 8 GiB` hard fail；没有建模、求解或 state 传递。禁止降低门槛或复用失败根。
- 固定服务器实时 checkout 为 clean `c19e35b87fb5295101d918b29815ea79424e50a5`，无 CISPO/Gurobi solver，available RAM 约 `114 GiB`、swap `780 MiB` 且 `si/so=0`、memory PSI 0；ParaCloud `squeue` 为空。但 2026-07-29 遗留的非 solver release-audit wrapper PID `976320` 与 `grep` 子进程 `976713` 仍存在。按 PID 保护合同，不切换 checkout、不部署 V5、不启动新服务器任务，等待作者明确授权处理该遗留进程。
- 下一步：本地释放至少 2 GiB 后，以全新根重跑当前提交的 24 h Base/V5 和四年 168 h Base/V5；全部闭合后才允许新的服务器 744 h。8760 h、付费云、basis/MGA、并发第二求解和 `Crossover=3` 继续禁止。

## 2026-07-30 11:26+08:00 年度流量缩放已本地闭合，服务器未部署

- 新模型提交 `d3b6f1485d5ef88762e9d8d0ac8ca87db15dc244` 将诊断时域碳上限、DAC throughput、生物质年度燃料和 CO2 年注入能力统一按 `optimization_hours/8760` 缩放；DAC 功率按年化捕集速率计算。8760 h 的比例为 1，不改变全年方程；annualized capacity/fixed cost 不缩放。
- 本地 1 h/24 h 中央 V4 V1G 根 `outputs/2030_{1h,24h}_v0730_annual_flow_scaled_v4_v1g_v1` 均 `OPTIMAL + PASS + 54/54 + current input + valid result manifest`。2030 窗口碳上限分别为 `0.456621/10.958904 MtCO2`，均 binding，DAC capacity violation 为 0；24 h solver runtime `270.653 s`。
- 完整本地回归 `138/139 PASS`；唯一失败是已知的本地 ignored technoeconomic manifest hash 与冻结服务器数据包不一致，本次未改动外置数据或 release contract。
- `scenario_catalog v4` 显式把主分析限制为 `base` 与 `flexible_load_comfort_v4_v1g`。其他 runnable overlay 仍是独立 sensitivity/legacy validation，并未进入本次 1 h/24 h 求解。
- 固定服务器与 ParaCloud 本次未操作。服务器上的旧 744 h 根属于旧的未缩放实现，必须保留原身份；不得原地覆盖或重标。若作者授权新 744 h，须先实时核验 checkout、进程、资源、目标根和队列，再部署新提交并运行全新串行根。

## 2026-07-30 09:18+08:00 四年 744 h sequence 已 PASS，服务器空闲

- `/data/zz2/National_model/outputs/planning_sequence_744h_v0729_identity_hydro_v4_v1g_v1` 于 `09:12:33+08:00` 完成，sequence `PASS`；2030/2040/2050/2060 全部 `ACCEPTED`。
- 四年均 `OPTIMAL + solution_qc=PASS + 53/53 + current input manifest + valid result manifest + hydro reconciliation audit`。objective 依次为 `2,331,204.529 / 2,380,260.669 / 2,564,163.188 / 2,808,392.706 million CNY`；solver runtime 依次为 `12,268.312 / 10,701.027 / 12,557.989 / 14,954.122 s`。
- 顶层 wrapper exit 0、wall `14:27:23`、maximum RSS `21,927,236 KiB`、swaps 0；年度 stderr 全空。当前无 CISPO/Gurobi/planning-sequence PID，available RAM 约 114 GiB，swap 无实时进出，memory PSI 0；ParaCloud 队列空。
- 744 h 仍为 `TEST_ONLY_TRUNCATED_HORIZON`。服务器不得自动启动 8760 h、basis、MGA、付费云或第二求解。

## 2026-07-29 23:21+08:00 2030 已接受，2040 Barrier iteration 107

- sequence 仍为唯一活动任务。2030 已 `ACCEPTED`：`OPTIMAL + PASS + 53/53 + current input + valid result manifest`，solver runtime `12,268.312 s`，objective `2,331,204.529 million CNY`，peak process-tree RSS `20.385 GiB`，年度 stderr 为空。
- 当前 2040 runner PID `1717598`；Barrier iteration `107`、runtime `3,572.896 s`，primal/dual infeasibility `0.008370/0.000821`、complementarity `1.8373`，solver current/max memory `13.174/22.222 GiB`。`solve_report.json`、`solution_qc.json`、`result_manifest.json` 尚不存在，故当前只能判定为 Barrier 进行中。
- 主机 available RAM 约 95 GiB，swap 781 MiB 且无实时进出，memory PSI 0；ParaCloud 队列空。运行 checkout clean `5d31b51`，不追平活动运行期间新增的文档提交。

## 2026-07-29 18:45+08:00 四年 744 h sequence 已启动，当前 2030 构建中

- 唯一任务：`/data/zz2/National_model/outputs/planning_sequence_744h_v0729_identity_hydro_v4_v1g_v1`，控制根同名位于 `run_control`；运行 checkout `5d31b51b350a581287fc8eb13e73216c11fc7543`。
- wrapper/Python/2030 runner 初始 PID `1463763/1463765/1463870`。身份为 `RUNNING + TEST_ONLY_TRUNCATED_HORIZON + 744 h + flexible_load_comfort_v4_v1g`，无 basis；首次快照尚在 build，故 telemetry、Gurobi log 和终态报告均未出现。
- 初始资源为约 113 GiB available RAM、781 MiB/2 GiB swap、`si/so=0`、memory PSI 0；ParaCloud 队列空。PID 存在时只读监控，不切 checkout、不启动任何其他任务。

## 2026-07-29 18:42+08:00 新实现已部署，权威回归与 1 h/24 h 门禁通过

- 固定服务器为 clean `codex/cispo-2030-full-lp` / `03e77ccc8d2ef3813b7cc5c0d727b068d008090d`。部署证据根 `/data/zz2/National_model/run_control/deployment_03e77cc_v1` 中 release contract、readiness、380 GW hydro audit、V4 input validation 全部 PASS；完整回归 `135/135 PASS`。
- 全新中央 V4 V1G 1 h/24 h 根分别为 `/data/zz2/National_model/outputs/2030_1h_v0729_identity_hydro_v4_v1g_server_v1` 和 `/data/zz2/National_model/outputs/2030_24h_v0729_identity_hydro_v4_v1g_server_v1`；均 `OPTIMAL + PASS + 53/53 + current input manifest + valid result manifest + hydro reconciliation audit`。24 h solver runtime `84.230 s`，wrapper wall `2:07.62`，peak RSS `852,644 KiB`，swaps `0`。
- 尚未启动四年 744 h sequence。启动前仍须重新核验唯一进程、RAM/swap/vmstat/PSI、服务器 checkout、目标根不存在和 ParaCloud 队列；禁止项不变。

## 2026-07-29 18:27+08:00 新实现已本地闭合，待推送/部署；服务器仍保持旧 checkout

- 新实现提交 `cea78ae1546b19754f7859982ae82dbf66820fdc` 已完成：8760 runner 常规路径不再调用 `getA()`；双层身份 `baseline_contract + analysis_case`；Base/中央 V4 保持 baseline peak，独立 sensitivity 使用 effective peak；梯级水电使用显式比例转移调和；accepted full-year Base 可 opt-in 输出精选 `.sol/.bas/.prm/fingerprint`。
- 当前固定服务器尚未部署该提交，仍须在部署前实时复核 `/data/zz2/National_model/repo` 的 checkout/dirty state、唯一 CISPO/Gurobi 进程、RAM/swap/vmstat/PSI、旧/新目标根与 ParaCloud。权威数据根仍为 `/data/zz2/National_model/data/model_ready_20260729_unified_7c56622_v4`；其 technoeconomic manifest SHA256 已实时复核为 `397297ec3980ffb38988a0463f934e310f228cbe48268d59ce38c7fa8350ec75`。
- 本地优化后的 24 h baseline/effective A/B：raw nonzeros `1,799,111/1,803,544`（effective 仅 `+0.246%`），runtime `55.253/53.021 s`，发电侧总容量 `3998.172/3785.672 GW`，两根均 `OPTIMAL + PASS + 53/53 + valid manifest`。容量差只能作为截断工程证据，不能作为年度结论。
- 水电全年输入审计保持 `297.8895 + 82.1105 = 380 GW`，并显式记录原始负本地入流 `335,304` node-hours、`158,199.650 million m3` 调和量和 `4.55e-13 m3/s` 最大闭合残差。全新四年 1 h V4 sequence 已 `PASS`。
- 下一步只允许：推送文档 tip后重新只读核验；服务器 fast-forward；权威数据根完整回归 + 1 h/24 h；随后启动唯一串行 2030→2060 744 h V4 V1G diagnostic sequence。禁止 8760 h、付费云、并发第二求解、basis/MGA gate 和 `Crossover=3`。

## 2026-07-29 统一候选已部署；唯一 2030 V4 V1G 744 h cold gate 已严格接受

- 当前固定服务器 checkout 为干净 `codex/cispo-2030-full-lp` / `7c56622c266e673037bd6afaa70c85aa57e6cb13`；终态审计前，本地、固定服务器 bare `origin` 与 GitHub 文档 tip 均为 `5ffee8a79b090dd8493e9b38da78464f3312ec6f`，唯一模型实现基线为 `7aac739e03646edfed14bbf48ac77869ba66cbef`。本次只增加交接文档；无需切换服务器 checkout。最终外置输入根为 `/data/zz2/National_model/data/model_ready_20260729_unified_7c56622_v4`，标准归档 SHA256 `f3e6cc0f810d0f4e1ccf8fd10907fb25b8859546be397f21035cd072cdb9d261`。`model_input_files.json` v10 包含 42 张运行表和 12 个 sidecar，显式覆盖 wave、V3、V4 和其来源 manifest。
- 服务器审计根 `/data/zz2/National_model/outputs/release_contract_v0729_server_7c56622_v5`：readiness PASS、release contract PASS、聚合水电 `297.8895 + 82.1105 = 380 GW` PASS、V4 四规划年 loader PASS、完整 unittest `130/130 PASS`。隔离部署过程中发现并修复 hydro audit NumPy 标量序列化、V4 source/运行表漏包、wave 表漏包、V3 implemented 表漏包与测试写死 `repo/data`；失败的 v1--v3 数据根/审计目录保留作证据，不是当前输入。
- 服务器 V4 小门禁 `2030_{1h,24h}_v0729_unified_v4_v1g_server_v1` 均为 `OPTIMAL + solution_qc=PASS + 52/52 hard checks + valid input/result manifests`。1 h solver 4.136 s、peak RSS 0.485 GiB；24 h solver 82.272 s、peak RSS 0.819 GiB。24 h Barrier 报 numerical trouble，`Crossover=1` 恢复 Optimal；这强化而不是削弱对 `Crossover=3` 的拒绝。
- 技术经济实装已再次复核：正确实施提交 `29bbf90d9edde4e74e3e095b807f2fa1ffaab6a6` 是两端 checkout 的祖先；服务器 `technology/technoeconomic_price_basis_manifest.json` 为 `technoeconomic_2025_cny_v2 / 2025 constant CNY / PASS`，活动 run 的 input/config snapshot 实际记录该 contract。本地迁移审计为 `ALREADY_APPLIED + PASS`、专项测试 `4/4 PASS`。
- 根 `/data/zz2/National_model/outputs/2030_744h_v0729_unified_v4_v1g_cold_v1` 使用 `--planning-year 2030 --horizon one_month`、`flexible_load_comfort_v4_v1g`、`barrier_16_auto_order_v2`，没有 basis。它是单独的 2030 cold gate，未调用 `scripts/run_cispo_planning_sequence.py`。raw 为 `5,238,323/3,942,756/42,266,264`，presolved 为 `3,234,057/2,812,319/31,818,664`，presolve/ordering `177.00/108.70 s`，`AA' NZ=6.236e7`、`Factor NZ=8.124e8`、`Factor Ops=5.567e12`。
- 2026-07-29 16:32+08:00 终态审计：wrapper/Python PID `1004972/1004975` 已退出。Gurobi 为 `OPTIMAL`，objective `2,330,214.449430 million CNY`、solver runtime `12,984.854 s`、Barrier/simplex `313/832,655`、Crossover `3,573.87 s`；最终 primal/dual infeasibility 为零。wrapper exit `0`、wall `3:42:57`、peak process-tree RSS `21.484 GiB`、swaps `0`，stderr 只有 `/usr/bin/time` 统计。
- 严格验收为 `solution_qc=PASS + 52/52 hard checks + validate_input_manifest=(True, []) + validate_result_manifest=(True, [])`。冷热/EV、wave、水电、PHS/储能、网络、备用、惯量、碳/CCS 与成本 accounting scope 已逐表核对；最大 power-balance residual `1.63e-10 GW`、objective component residual `1.79e-6 million CNY`。成本同时含 annualized planning 与截断 operation scope，因此本根仍是 `TEST_ONLY_TRUNCATED_HORIZON`，不是年度科学结果、年度净价值或正式 2040 state anchor。
- 终态刷新时主机约 `114 GiB` available、swap `781 MiB/2.0 GiB`，实时 `vmstat si/so=0`、memory PSI=0；ParaCloud `squeue -u a8s001819` 为空。历史 `4003088=COMPLETED build-only`、`4003172=OUT_OF_MEMORY`、`4004585=TIMEOUT`。另有旧 release-audit SSH/bash/grep 管道，无 Python/Gurobi solver 子进程且不是第二求解，本次未终止。不得启动第二个 CISPO/Gurobi、固定服务器 8760 h、付费云、basis gate 或 `Crossover=3`。

## 2026-07-29 多智能体改动已统一为本地 release candidate；等待精确提交和实时服务器复核

- `b87b3b6` 的干净提交不是可部署版本：它已有省级聚合水电 loader，但漏掉同一功能的配置、LP、导出和测试。统一实现已提交为 `1d04f07565c3039ed467ec4080f276bd0da90786`，并由 `config/release_contract_v0729.json` 把 Base、水电 380 GW、V4、PHS sensitivities、scenario catalog、production solver profile 与 11 个外置数据 SHA256 锁定；detached 精确提交的 release audit PASS、完整回归 `129/129 PASS`。
- 本地当前工作树顺序完成 `outputs/planning_sequence_168h_v0729_{base_current,flexible_load_v4_v1g_current}_local_v1`。2030→2040→2050→2060 八个根均为 `OPTIMAL + solution_qc=PASS + 52/52 hard checks + closed result manifest + current input manifest PASS`，两条序列 resume 后均为四年 `RESUMED_ACCEPTED`；没有 basis 复用、并发求解或远程计算。
- V4 相对 Base 增加 `4.59%` variables、`6.24%` constraints、`3.27%` nonzeros，峰值 RSS 增量不超过约 `0.27 GiB`，未显示工程性能失控。EV 在四年均有实质重排；冷热吞吐为零；波浪能 enabled、候选和上限已加载，但装机/发电为零。上述均是 168 h 机制证据，不是年度价值或年度技术淘汰结论。
- 统一审计修复 aggregate-hydro 备用 QC 重复计数/安全表遗漏、V4 年化成本分类和 gzip 非确定性。完整本地回归 `129/129 PASS`；参数 audit `11,727/26/0/0`（rows/pass/warn/hard-fail）；四个全新 2030 1 h Base/V4/hydro-flex/PHS-central 根均为 `OPTIMAL + QC PASS + manifests valid`。省级水电 up/down 安全表 closure 最大误差为 `1.42e-14/7.11e-15 GW`。
- 作者现已授权代码/数据统一后启动一个固定服务器 744 h 或两个月门禁；当前计划选择标准 744 h V4 V1G cold。它仍须等待精确 commit/push、版本化数据根、服务器实时 Git/进程/RAM/swap/PSI 与 ParaCloud 复核，以及服务器 release/input/readiness + 1 h/24 h 门禁。不得运行 8760 h、付费云、并发第二求解、basis reuse 或 `Crossover=3`。下文 `701b9bc`/RAM/swap 是旧快照，不能直接沿用。

## 2026-07-28 常规水电 380 GW 省级闭合仅在本地；服务器未部署

- 当前本地未提交水电候选已从重复 `COMID` 修复扩展为“297.8895 GW 站点 + 82.1105 GW 固定省级聚合”常规水电表示，并严格闭合国家能源局 2025 年末 380 GW 分项；PHS 下限保持 65.94 GW。聚合层增加 LP 变量和输入文件，旧 duplicate-COMID-only 门禁的矩阵、目标和 basis 均不再代表当前 topology。
- 新的本地 1 h/24 h 根 `outputs/2030_{1h,24h}_v0728_hydro_provincial_closure_base_v2` 均为 `OPTIMAL + solution_qc=PASS + closed manifest`。24 h raw 为 `231,076 rows / 346,736 columns / 1,754,607 nonzeros`，聚合水电 97.768506 GWh 严格等于该窗口可用量、违反量为 0，最大功率平衡残差 `1.12e-12 GW`。这些是 `TEST_ONLY_TRUNCATED_HORIZON`，不能解释为年度发电量或系统成本。
- 本里程碑没有读取、切换或修改固定服务器 checkout，没有传输 `provincial_aggregate_capacity_2025.csv` 或月曲线，没有启动 CISPO/Gurobi，也没有查询或提交 ParaCloud 作业。下文服务器 RAM/swap/进程数值均是旧时间戳快照，未来任何远程动作前必须重新实时核验并取得授权。

## 2026-07-28 冷热/EV V4 数据支撑型本地门禁闭合；没有服务器动作

当前未提交工作树基于 `b87b3b6a76e9b6a3683087105e3251daff22cfad`，已把 `flexible_load_comfort_v4_v1g` 收敛为数据支撑型工程中心情景，并保留独立的 V2G sensitivity。P0 修复覆盖多省周期状态广播、多省目标标量化、禁用 V2G cost 导出类型、V4 smart-charge QC/上界，以及不具物理支撑的负舒适债。冷热现在是非负连续服务库存；EV 是既有 EV 基线的 75% 固定负荷与 25% 可调服务库存，不声称车辆接桩率、行程链、出发 SOC 或物理车队 SOC。Base（wave on、flexible load off）和 V3 均未改动；V4 改变 LP topology，不能与 Base/V3 导入或导出 basis。

五张省-小时输入已由现有负荷/V3 BAIT envelope 生成，中心/低/高参数、来源登记和独立证据计数齐全；四规划年 runtime-loader 审计 PASS。2026-07-29 修复 gzip 时间戳后，连续两次完整 build+validate 的六个输出字节一致，当前 sidecar SHA256 为 `ad46c7610903726a059b92255332056935021763ca11433b0b866b6dd1ac144a`。当前输入身份下的 V1G 1 h/24 h 与 V2G 1 h 新根均为 `OPTIMAL + solution_qc=PASS + closed manifest + current input_manifest PASS`；24 h raw 为 `241,492/353,556/1,799,247`（rows/columns/nonzeros），solver `43.13 s`、峰值 RSS `0.760 GiB`。它们只证明本地截断工程可解性；中心参数仍是 `ENGINEERING_CENTRAL_REQUIRES_LOW_HIGH_SENSITIVITY`，不是论文校准结果。

本里程碑结束时只读复核：固定服务器仍为 clean `codex/cispo-2030-full-lp` / `701b9bc225013a5009dcce3f4e97ee2063dcd00f`，没有真实 CISPO/Gurobi 求解进程，约 `70.9 GiB` available RAM，swap 仍使用约 `19.1/21.5 GiB`；ParaCloud `squeue -u a8s001819` 为空。本轮没有更改固定服务器 checkout、数据、进程或队列。下一步必须先由作者接受当前边界，之后至多运行一个隔离的本地 168 h V1G gate；不得自动进入 basis、744h/8760h 或远程阶段。任何未来远程动作之前仍须重新实时核验 Git、CISPO/Gurobi、RAM/swap/PSI 和 ParaCloud，并取得单独授权。

## 2026-07-28 M2 boundary audit closed locally; no server action

Local implementation commit `379a96a79cf14d7dc08d0a5cfd45b8223f2f4b47` closes M2 Stage A as a read-only decision/parameter audit, not as a solver or deployment milestone. `outputs/m2_model_boundary_audit_20260728_local_v3/` has 11 findings with `9 PASS, 0 OPEN, 0 hard fail`; the parameter audit has `11,717` rows, `26 PASS, 0 WARN, 0 hard fail`, and four retained open risks. It closes scenario-overlay traceability (`M2-PARAM-001`) while leaving Base wave on/flexible load off and leaving all new scientific formulations out of the production LP.

The duplicate-COMID hydrology work currently present in the local worktree is owner-uncommitted and must not be deployed. Its local 1h/24h Base candidate gates are closed (`OPTIMAL + solution_qc=PASS + closed manifest`) and the 24h raw topology remains `231,076/345,992/1,753,119`, but its Barrier log reported numerical trouble before a successful Crossover. This is a review gate, not a server authorization. The last live server check remains the separately time-stamped `701b9bc` / no-CISPO / occupied-swap snapshot below; recheck it live before any future remote action.

## 2026-07-28 swap 不是 cache；保持暂停

- 实时 `/proc` 诊断：`Cached+Buffers` 仅约 `5.6 GiB`，但匿名页约 `49.5 GiB`、inactive anonymous 页约 `34.6 GiB`。swap `19.1/21 GiB` 主要归属仍在运行的 GPU `wind_power` Python（`VmSwap 8.18 GiB`）和两组 MATLAB（`6.01/2.28 GiB`），不是可由 `drop_caches` 清除的文件缓存。
- 5 秒 `vmstat` 的 `si/so=0` 且 memory/IO PSI 均为 0，表明此刻没有持续换页；但这些 swapped pages 仍属于活跃作业。虽有约 `70 GiB` available RAM，`swapoff/swapon` 会进行约 19 GiB 主机级页面回迁并干扰其工作负荷，未取得明确授权前不执行。无 CISPO/Gurobi，但服务器仍暂停部署和求解。

## 2026-07-28 重复 COMID 水量守恒修复仅在本地闭合；服务器未部署

- 本地工作树基于 `ed72ba08ff52025cb372fc5c16583c3e05bd38b5`，将同一 GRFR `COMID` 映射的全部水电站改为按 `capacity_potential_gw` 静态份额共享一次扣除环境流量后的河段径流；梯级节点使用成员站分配流量之和。146 个重复河段、319 条共映射站点记录逐组份额和均为 1。实现尚未提交、推送或部署。
- 完整本地回归 `116/116 PASS`。隔离 1 h/24 h Base 根 `outputs/2030_{1h,24h}_v0728_hydro_comid_flow_share_base_v1` 均为 `OPTIMAL + solution_qc=PASS + closed manifest`；24 h 根为 test-only，不能作为年度水电量或系统成本结论。
- 18:15 后只读服务器核验：checkout 为干净的 `codex/cispo-2030-full-lp` / `701b9bc225013a5009dcce3f4e97ee2063dcd00f`；未发现真实 CISPO/Gurobi 进程，约 `70 GiB` available RAM，swap 仍约 `19/21 GiB`。本里程碑没有传输代码/数据、切换 checkout 或启动求解；既有服务器结果全部早于该水量口径修复。

## 2026-07-28 当前 M1 168h 四根 basis 门禁闭合；不申请 744h

- 本地当前提交顺序完成 2030 cold/warm、2030 diagnostic-state bridge、2040 cold/warm。四根都是 `OPTIMAL + solution_qc=PASS + closed manifest`，同年 objective 完全相同；2030 solver `520.266 → 10.874 s`，2040 `489.268 → 14.257 s`，warm 均为 0 Barrier/0 simplex。2040 只接受标注为 test-only 的 2030 state，basis 只来自 2040 cold；没有跨年 basis。
- 这给出同构 168h 重解的明确加速证据，但不能授权 744h：孤立 744h warm 必须先额外运行同配置 cold 744h 才会有 source basis，当前没有第二个同构 744h 目标，因而无净端到端收益。结论是“不申请、不启动”，而不是将 168h 优势外推为全年表现。
- 本里程碑只写入本地 outputs 和交接记录；随后已实时只读复核固定服务器：干净 `codex/cispo-2030-full-lp` / `701b9bc225013a5009dcce3f4e97ee2063dcd00f`、无 CISPO/Gurobi、约 `70 GiB` available RAM，但 swap 仍约 `19.1/21 GiB` 且有约 `43.0 GiB RSS` 的无关 Python。ParaCloud `squeue -u a8s001819` 为空。按 runbook 继续暂停；任何未来需求仍须重新读取，不能复用本条快照。

## 2026-07-28 M0/M1 仅本地闭合；现有 168h roots 降为历史证据

- 本地实现提交 `a5e34bf5357301c205b246b0aa2149db0dca9c3b` 完成 M0/M1，未推送、未部署。M0 的 `run_identity` 已拆成 `scientific_case`、`lp_topology`、`solver_runtime`、`implementation_bundle`；basis 的唯一硬兼容条件是完整 raw LP topology（变量/约束顺序与方向、维度、NNZ、raw CSR pattern），其余层只作审计。故纯文档提交不会废弃 basis，但活动模型结构变化必定拒绝。
- M1 已闭合 Base 标签/混合气象、VRE `cohort_survival_v1` 与 `fixed_floor_v1` 对照、BECCS 固定结果 lifecycle screening 和仅限可行域不变的 bound tightening。`outputs/2030_24h_v0728_m1_equivalence_cold_local_v1` 为 `OPTIMAL + PASS + closed manifest`，与 M0 cold objective/容量/成本/发电量 zero-diff；完整本地回归为 `114/114 PASS`。
- 因此下节所述 M0/M1 前 168h 根不再是当前 basis 门禁，只保留为历史性能记录。下一步只允许本地当前提交的 2030 cold/warm、2030 diagnostic-state bridge、2040 cold/warm；不跨年导入 basis、不使用 `Crossover=3`，也不启动 744h/8760h 或付费云任务。
- 本条没有重新读取服务器或 ParaCloud。此前 `701b9bc`、swap 压力及空队列只是旧快照；若后续申请远程动作，必须先重新实时核验 Git、CISPO/Gurobi 进程、RAM/swap 与队列。

## 2026-07-28 intra-grid/cohort 本地 168h basis 四根门禁通过；服务器仍因 swap 压力暂停

- 提交 `282c393fd98e25737631493e19110e38bb49ed28` 的本地 168h Base 冷/暖四根已闭合。2030 cold/warm 为 `576.593/11.406 s`，2040 cold/warm 为 `543.965/15.517 s`；四根全部 `OPTIMAL + solution_qc=PASS + manifest true`。warm 均为 0 Barrier/0 simplex，且同年 cold/warm objective、容量 CSV 一致，发电差仅浮点量级。2040 仅用明确 test-only 2030 diagnostic state bridge；每一年只导入本年自身 cold basis，未跨年复用。
- 四根均含新的 site/substation intra-grid CSV，且 2025 VRE 初始共享 trunk proxy 为 `1,069.512666 GW`，相对旧 nameplate `1,309.999999962 GW` 为 -18.36%。这验证 CISPO S4-18 spur 与 S4-19 potential-weighted wind/PV trunk 的本地工程/数值可解性，不是截断时域科学结论，也不证明全年 basis reuse。
- 即时只读服务器核验：checkout 为 `701b9bc225013a5009dcce3f4e97ee2063dcd00f`，无 CISPO/Gurobi 进程，约 70 GiB available RAM；但 swap 已用约 `19/21 GiB`，并有约 45 GiB RSS 的无关长任务。按 runbook 这是内存压力，故没有切换 checkout、安装 cohort 输入或启动服务器 168h。ParaCloud 队列为空。以后服务器状态必须重新读取，不能复用本条快照。
- 下一步只有在该压力消除后才允许：重新核验服务器/队列，add-only 安装 checksummed cohort CSV/manifest，部署精确提交、跑完整回归，再在全新目录运行一个 168h cold Base 根。`Crossover=3`、744h、8760h 和付费云任务均继续禁止。

## 2026-07-28 同格网风光共享并入与既有 VRE cohort：仅本地闭合，禁止据此直接放大

- 本地工作树以 `d73eb3390c970b0da6319a03ca8b1d3c30384040` 为基线完成 CISPO S4-18/S4-19 对齐：spur 继续按 site `max_t(cf) × capacity`，而 wind/PV trunk 在共同 substation 按 potential-weighted equivalent peak 建模。36,686 个 VRE site 行中的 12,603 个多技术 `grid_uid` 全部共享唯一的现有 substation；设计系数使用完整 8760 CF 扫描，但不新增 LP 变量或逐小时约束。
- 新的既有容量 cohort 输入有 15,171 行，2025 年按技术严格闭合为 onwind/offwind/UPV/DPV `593/47/670/530 GW`，SHA256 `e00791ec9597897da80377458d6acefdc481ef1708c0f86d68adb2a5576f92d0`。GEM 可用投运年进入寿命队列；未知/OSM/残差和边界后投运容量显式作为 2025 boundary-censored cohort。退役解除 observed floor，但不删除 technical upper，连接代理独立复用；这允许、但不强迫同址再建。
- 本地隔离 24h Base 根 `outputs/2030_24h_v0728_intra_grid_cohort_smoke_local_v1` 为 `OPTIMAL + solution_qc=PASS + closed result_manifest`，完整回归 `102/102`。站级 VRE 初始 trunk proxy `1,069.513 GW`，相对旧 nameplate `1,310.0 GW` 为 -18.36%；这不是年度科学结果，也不是 744h/8760h 性能外推。
- 本条不写入固定服务器 checkout、数据根、进程、输出或 ParaCloud 队列；本文件先前记录的服务器状态不可作为部署时的实时证明。后续必须先实时核验 `701b9bc` 是否仍为预期 checkout、主机无 CISPO/Gurobi 进程且内存安全、ParaCloud 队列为空，再以 add-only 方式安装 cohort CSV/manifest、fast-forward 至精确已推送提交、运行完整回归。仅通过后才可运行一个新命名的 168h Base 门禁；`Crossover=3`、744h、8760h 和付费云任务均不在本条授权内。

## 2026-07-28 生产运行契约闭合与 Crossover=3 744h 反例

- 固定服务器模型 checkout 已部署 `701b9bc225013a5009dcce3f4e97ee2063dcd00f`；本地与服务器完整回归均为 `98/98`。本次工程改动增加运行根/递进序列原子 claim、不可混用的运行身份、当前输入复验和严格成功终态，不改变 Base 数学边界。
- 服务器数据根以 add-only 方式补齐 `load/flexible_load_envelope_v3.csv.gz` 与 manifest，SHA256 分别为 `b5ebda4344a8f978606c242065159f27a75994a5d976f2cbe06038d66a429a03` 和 `0298256b2c1394f8e5a9e36780d2be279f06b27b291a9eca57daae91dba9a745`；既有文件未覆盖。服务器回归由此从缺少覆盖层输入恢复为 `98/98`。
- 168h 同结构 A/B 中，`Crossover=3` 的 solver/crossover 为 `594.63/117.67 s`，参考 `Crossover=1` 为 `649.17/190.92 s`；`CrossoverBasis=0` 无收益。这个短时域结论没有直接推广到 744h。
- 744h `Crossover=3` 根 `/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_crossover3_v1` 的 raw/presolved/factor 与参考根完全一致，Barrier 从 `7,543.19 s` 降到 `6,981.07 s`，两个 push 阶段也较短；但 primal cleanup 出现 `1e8--1e38` infeasibility 循环。该隔离候选按数值稳定性停止准则优雅中断，终态 `INTERRUPTED`、runtime `10,930.99 s`、crossover `3,947.89 s`、peak RSS `19.828 GiB`、无解/QC/manifest，故明确拒绝为生产 profile。
- 当前无活动 CISPO/Gurobi 进程；接受的 744h 参考仍为 `/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_v2` (`OPTIMAL + PASS + manifest true`，`barrier_16_auto_order_v2`/`Crossover=1`)。比较记录为 `/data/zz2/National_model/outputs/solver_ab_v0728_crossover_744h.{json,csv}`。固定服务器 8760h 与新的付费云任务仍禁止。

## 2026-07-28 2024 Base 744h 已完成并验收

- 根 `/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_v2` 已完成：`OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=(True, [])`；49 项 hard checks 全真。wave 开启、flexible load 关闭、全国碳会计、2024 Beijing-aligned VRE；结果用途为 `TEST_ONLY_TRUNCATED_HORIZON`。
- raw/presolved：`4,915,427/3,711,992/40,836,493` 与 `3,063,498/2,664,976/31,086,440`（rows/columns/nonzeros）。presolve 173.12 s；ordering 114.19 s；`AA' NZ=6.388e7`；`Factor NZ=7.481e8`；`Factor Ops=4.721e12`。
- Barrier 211 次/7,543.19 s；crossover 5,709.46 s；simplex 1,437,196；solver 13,268.90 s；端到端 3:47:18；峰值进程树 RSS 20.049 GiB；无 swap。最大功率平衡残差 `3.43e-12 GW`，最大约束/边界/对偶违例 `9.32e-8/2.75e-8/9.35e-8`。
- 进程已退出，服务器约 70 GiB 可用内存且无活动 CISPO solve。crossover 约占 solver 时间 43%，仍是 8760h 的主要风险。未启动第二个求解、固定服务器 8760h 或付费云任务。

## 2026-07-28 2024 数据已部署；服务器 168h Phase A/B 完成

- 固定服务器实际从干净、空闲的 `78a605d` fast-forward 到双端已推送的 `9a3c5e8`。四个 2024 CF stores 以新增归档安装，归档 SHA256 为 `2f70713d7a93633f8478e554b1924be7fdfe1d05ff5674a385461d3fa3045cfc`，文件数与本地一致；既有数据和归档均未删除/覆盖。服务器完整回归 `89/89`。
- `/data/zz2/National_model/outputs/2030_168h_v0728_2024_dense_reductions_off`：`OPTIMAL + PASS + manifest true`；raw `1,167,956/1,019,192/9,536,283`、presolved `731,124/820,537/7,212,238`，`AA' NZ=2.160e7`、`Factor NZ=1.042e8`、`Factor Ops=8.440e10`，163 Barrier/626.10 s，crossover 72.76 s，229,459 simplex，总 700.50 s，RSS 3.407 GiB。
- `/data/zz2/National_model/outputs/2030_168h_v0728_2024_dense_dualred_v2`：`OPTIMAL + PASS + manifest true`；presolved `704,597/719,155/7,133,417`，`AA' NZ=1.987e7`、`Factor NZ=1.023e8`、`Factor Ops=8.480e10`，Barrier `performed` 124/475.02 s，crossover 190.62 s 后恢复 Optimal，630,993 simplex，总 668.05 s，RSS 3.411 GiB。
- 省级碳分层根也闭合，但其 presolved/factor/迭代/work units/目标与 dense v2 完全一致，故不采用。机器可读比较位于 `/data/zz2/National_model/outputs/solver_audit_v0728_2024_phase_ab/phase_ab_168h.{json,csv}`。
- 当前唯一 744h 候选为 dense + `barrier_16_auto_order_v2`。启动前必须再次确认无进程、可用内存安全和输出根不存在；不得并发或启动 8760h。

## 2026-07-28 2024 气象与 Phase A/B 仅本地闭合；等待服务器放大

- 本地实现提交为 `1449a4571d2881077f926bbc4116d2c9bdc6b5d5`，尚未部署。固定服务器在本轮写入前实时核验为干净 `4e1999d`、无 CISPO/Gurobi 进程、约 70 GiB 可用内存；CF 根有 2023 stores 但缺少全部四个 2024 stores。因此服务器不得直接运行新配置，必须先以追加方式传输 `onshore_wind/offshore_wind/pv/mixed_wind` 的 2024 Zarr 并校验目录、大小和 hash，不覆盖已有数据。
- 新配置的风电/光伏按北京时间 2024 自然年取 8760 小时：2023 UTC 尾部 8 小时 + 2024 UTC 数据，并删除北京时间 2 月 29 日。波浪 reference year 仍为 2023，水文仍为 2019。完整本地回归 `89/89` 通过。
- 新 1h 两根和 24h 六根全部达到 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`。全国排放式与 31 省分层式目标一致；分层式消除了 raw 6,697-NZ 行，但 presolve 后矩阵/factor 完全相同。`DualReductions=1` 降低 24h factor 结构却显著增加 crossover，旧 0/1 参数总时间 39.706 s，而生产候选为 56--62 s；`PreDual=1` 和 `PreSparsify=2` 已在短门禁淘汰。
- 下一步只能顺序执行：推送两远端 → 再次实时核验空闲服务器 → 追加 2024 CF → fast-forward 到精确推送提交 → 完整服务器回归 → 新根 168h 匹配 A/B。全部通过后只选择一个 case 启动新 744h。不得并发、不得覆盖历史根、不得启动固定服务器 8760h 或付费云任务。

## 2026-07-28 当前 Base/MGA 工程代码已部署；1h/24h/168h 与 basis/MGA 诊断通过门禁

- 写入前已实时复核服务器：无 CISPO/Gurobi 进程，可用内存约 69--70 GiB。干净 checkout 在未替换任何活动 checkout 或任务的前提下由 `01ec6f9` fast-forward 至 `56d166d`，并在本轮新代码通过本地完整回归后 fast-forward 至已推送的 `4e1999d`；服务器不再是旧 `c879c99` 模型实现。
- 含波浪 Base 使用附加数据根 `/data/zz2/National_model/data/model_ready_20260723_v0722_city337_wave_20260727` 与 `/data/zz2/National_model/data/wave_energy_20260727`，并沿用既有 CF/水文根。服务器 CISPO 环境缺少 `xarray`；仅从本地下载的 wheel 以 `--no-deps` 加入 `xarray==2025.1.2`，`wave_grid.nc` 已 smoke-open 通过。未读取或记录任何密钥。
- 本地和服务器完整回归均为 `82/82` 通过。服务器新根 `2030_1h_v0728_server_wave_base_basis_source_v1`、`2030_24h_v0728_server_wave_base_phase_audit_v1`、`2030_168h_v0728_server_wave_base_barrier16_v1`、`2030_1h_v0728_server_mga_runner_base` 均为波浪开启、灵活负荷关闭的 Base，且满足 `OPTIMAL`、`solution_qc=PASS`、`scenario_id=base` 和有效科学 result manifest；它们仅是截断时域工程门禁。最后一个 1h 根为 81,061 行、238,467 列、463,697 非零元、83 Barrier、2,674 simplex、10.33 s solver、0.463 GiB RSS，`analysis_mode=BASE_MINIMUM_COST`。
- 168h 终态证据：raw `1,167,958/1,019,192/9,486,177`；presolved `730,782/820,208/7,174,545`；`AA' NZ=2.150e7`；`Factor NZ=1.045e8`；`Factor Ops=8.532e10`；138 次 Barrier/584.20 s；crossover 104.23 s；411,056 次 simplex；总 solver 时间 690.86 s；进程树峰值 RSS 3.359 GiB。168h 的 crossover 具有实质影响，后续审计必须保留。
- 受限 crossover-basis 证据保存在新的隔离 1h 根。完全相同的 2030 LP 从 9.43 s/80 次 Barrier 降至 0.25 s/0 次 Barrier；使用源 2030 diagnostic cohort state 时，2040 冷启动为 9.29 s/77 次 Barrier，而跨年 basis 为 0.52 s/0 次 Barrier 加 1,714 次 simplex，目标和全部 QC 一致。此证据只验证受限的 test-only 路径，不验证全年复用或科学结果。
- 未启动固定服务器 8760h，未触碰历史 744h 文件，未提交或修改 ParaCloud 任务。168h/1h 门禁后服务器空闲。`4e1999d` 的 MGA 只接受闭合的年度 Base 最小成本基线、相同配置/required-input hash，并以硬成本上限加二级目标运行；其输出不得导出递进 state。当前无 accepted 年度 Base，故未运行 MGA。未来 8760h 仍需用户单独确认并满足完整云端协议。

## 2026-07-27 原始 LP 稀疏审计已本地闭合；未部署

- 本地实施提交 `6114157` 新增 `--constraint-family-audit`。它只在 `model.update()` 后读取原始 Gurobi 稀疏矩阵，默认超过 50,000,000 非零元即硬失败；不改变 LP 变量、约束、目标、Base 身份、数据或 solver profile。`constraint_family_audit.json` 记录原始约束/变量族、具体最稠密 25 行/列，并在求解后追加全局 presolve、ordering、factor、Barrier/crossover 指标；该文件被 output catalog 和 SHA256 manifest 正式纳入。Gurobi 不提供 presolved 行到源族的稳定映射，故不得将全局 presolve 缩减归因于某一族。
- 完整本地回归 `75/75` 通过。新的波浪开启、灵活负荷关闭 Base 根 `outputs/2030_{1h,24h}_v0727_constraint_family_audit_base_v3` 均为 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，所有 hard checks 为真。24h raw/presolved 为 `231,074/345,992/1,729,035` 与 `129,335/260,116/1,269,506`（rows/columns/nonzeros）；0.73 s presolve、0.41 s ordering、`AA' NZ=2.200e6`、`Factor NZ=6.284e6`、`Factor Ops=7.399e8`、89 Barrier、57,741 simplex/crossover、29.107 s solver runtime、0.712 GiB 峰值进程树 RSS。
- 精确高连接行是 `annual_emissions_accounting`（6,697）、`capacity_margin_p65/p15`（6,491/5,736）和 31 个 `co2_source_balance_p*`（各 3,246）；最大列为省级 `storage_capacity_gw`（各 194）。这排除了“水电逐站平衡是当前首要矩阵密集源”的假设，但不构成删除任一物理/碳/可靠性约束的授权。下一步仅准备年度排放会计的代数等价候选并做新的匹配 24h A/B；通过后才可考虑 168h。未连接、写入或部署固定服务器，未查询/修改 ParaCloud，也未启动 744h、8760h、第二个求解或付费云任务。

## 2026-07-27 孤立梯级节点等价清理已在本地闭合；未部署

- 本地提交 `9787ba7` 保留 142 个源拓扑节点、124 条源边和全部水电站/GRFR 入流/库容/泄流物理，仅将 8 个“无入边、无出边、单站”的节点从逐小时核心梯级行转入已有的向量化独立水库平衡。该节点的上游项为空、局部入流等于站点 GRFR 可用流量，故约束代数等价；有效核心站点行由 146 降至 138。多站孤立节点触发硬失败，避免未来数据刷新静默改变水文聚合。
- 本地完整回归 `71/71` 通过；含波浪、无灵活负荷的全新 Base 1h/24h 根 `outputs/2030_{1h,24h}_v0727_cascade_isolated_nodes_independent_base` 均为 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，全部 hard checks 为真。24h 与清理前的目标仅差 `9.78e-09 million CNY`，raw/presolved 维度不变；`Factor NZ/Factor Ops` 增至 `6.284e6/7.399e8`，所以它是构建路径清理，不是 Barrier 提速证据。
- 本轮没有连接、写入或部署固定服务器，也没有查询/修改 ParaCloud；不得据此启动 168h、744h、8760h 或云端任务。若以后另行授权部署，先实时复核服务器 checkout、进程、可用内存和数据根，部署精确推送提交后才可在新根运行单一匹配 168h 门禁。

## 2026-07-27 连续 RUC 等价瘦身已在本地闭合；未部署

- 本地实施提交 `3f2255a` 仅删除连续 RUC 中由保留 S4-24、S4-25、S4-29 严格蕴含的四组逐小时上界；容量、备用、惯量、爬坡、最小出力、启停时序、目标函数、Base 技术边界与变量数均未改变。建模前会拒绝不满足 `min_up_h>=1`、`min_down_h>=1`、`pmin_fraction<=pmax_fraction` 或参数缺失的 RUC 表，防止未来参数修改破坏等价性。
- 新的本地含波浪 Base 1h/24h 根 `outputs/2030_{1h,24h}_v0727_ruc_dominated_bounds_removed_base` 均为 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，灵活负荷关闭。24h 原始矩阵由 `345,992/263,810/1,794,507` 变为 `345,992/231,074/1,729,035`（variables/rows/nonzeros），目标完全相同；presolved `129,335/260,116/1,269,506`、`AA' NZ=2.200e6`、`Factor NZ=6.111e6`、`Factor Ops=6.039e8`、95 Barrier 和 67,614 simplex/crossover 均不变。因此它是安全的构建瘦身，并非已证实的 Barrier 加速。
- 8760h 静态预估更新为 `41,186,792` variables、`55,928,636` estimated constraints、`497,144,388` estimated nonzeros、`33.40 GiB`。这不证明 factorization 可行，不能触发固定服务器 8760h 或新付费云端任务。本轮未连接或修改固定服务器/ParaCloud；服务器 checkout、进程、输出和队列状态必须在任何后续部署前重新实时核验。

## 2026-07-27 Base 定义重置为含波浪能；仅本地验证，未部署

- 用户已将 Base 定义为风电（含海风）、光伏和波浪能共同参与的连续 LP。提交 `c992550` 将 `base` 的 `wave_energy=true` 固化，并仅保留一个柔性覆盖层 `flexible_load_comfort_v3_v2g_5pct`：它继承含波浪 Base，再启用 `comfort_envelope_v3`、V1G 和因果日内 5% V2G。旧的 V1、state-v2、单独 wave/comfort 及组合情景 JSON 已删除；历史根和记录保持原样，不能改名为新 Base。
- 本地设置 `CISPO_WAVE_ROOT` 后回归 `66/66` 通过；两个身份的 1h/24h 新根均为 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`，所有 hard checks 为真。24h Base/柔性覆盖层的峰值 RSS 分别为 0.735/0.731 GiB；全年静态 preflight 分别为 36.47/37.63 GiB，均只是模型规模估计。
- 此边界变化尚未部署到固定服务器；先前服务器上的 wave-off Base 168h/744h 结果保留为历史数学、物理 QC 与性能证据，但不是新 Base 的可比求解门禁。此次未写入服务器 checkout、进程、输出，也未修改 ParaCloud 队列或启动新任务。固定服务器 8760h 和新付费云端任务继续禁止。

## 2026-07-27 本地全模块联合敏感性门禁；未部署到服务器或云端

- 新增本地独立情景 `wave_energy_medium_v1_flexible_load_comfort_v3_v2g_5pct`，在同一连续 LP 中启用既有 marine `grid_uid` 波浪能、`comfort_envelope_v3` 冷热状态、EV V1G 和日内因果 5% V2G。它保持 `EVIDENCE_ANCHORED_PARAMETERS_REQUIRE_SENSITIVITY`，不是 Base；Base 默认开关与任何科学边界均未改变。
- 本地 1h、24h、168h 新根均达到 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`，完整回归 `67/67` 通过。联合 168h raw/presolved 为 `1,081,688/1,429,226/10,293,428` 和 `751,365/865,314/7,363,654`，`AA' NZ=2.162e7`、`Factor NZ=1.056e8`、`Factor Ops=8.603e10`，180 Barrier、239,930 simplex/crossover、602.265 s、3.296 GiB 峰值 RSS。详情和局限见 `MODEL_COMBINED_MODULE_SOLVABILITY_AUDIT_20260727.md`。
- 全年 preflight 的 37.63 GiB 是静态构建估计，不能证明 Barrier factorization；因此本工作不授权固定服务器 8760h 或新付费云任务。未对服务器 checkout、运行进程、现有输出或 ParaCloud 队列作任何写入。若以后要上服务器，只能在空闲复核后以新输出根做单一匹配 168h A/B；不得与其他求解并发。

## 2026-07-27 固定服务器 Base 168h manifest 闭合门禁

- 先实时确认固定服务器无 CISPO/Gurobi 进程、约 69 GiB 可用内存、checkout 干净于 `c879c99`，随后仅 fast-forward 到已经推送的 `67482ab`；P0 实施提交为 `7499062`。相对于原服务器模型实现，部署代码的唯一模型邻接差异是通用 runtime 日志排除，不改变 LP、数据、情景、目标函数、约束或时空边界。
- 服务器以三个版本化数据根运行完整 discovery 回归，结果 `67` 项通过、`2` 项可选 xarray 测试跳过。随后单独启动一个 Base 168h 根 `/data/zz2/National_model/outputs/2030_168h_v0727_manifest_runtime_contract_base`，使用 `barrier_16_auto_order_v1`、`Threads=16`、`SoftMemLimit=48`、`Crossover=1` 和 generic `stdout.log`/`stderr.log` wrapper 重定向；无并行求解。
- 终态为 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，灵活负荷/波浪能均关闭，所有 hard checks 为真。原始矩阵 1,393,915 行、1,011,079 列、9,797,949 非零元；presolved 为 729,559/817,723/7,001,232，presolve 22.89 s、ordering 26.08 s，`AA' NZ=2.131e7`、`Factor NZ=1.036e8`、`Factor Ops=8.436e10`。Gurobi 为 161 次 Barrier、226,659 次 simplex/crossover、614.894 s；端到端为 12:24.94、进程树峰值 RSS 3.453 GiB（`/usr/bin/time` 3,641,828 KiB），zero swaps。
- 物理/数值关键值：目标 `2,028,598.8440447072 million CNY`，最大功率平衡残差 `3.91e-12 GW`，最大约束/边界/对偶违例 `4.17e-8/4.11e-12/1.75e-10`。该根标记为 `TEST_ONLY_TRUNCATED_HORIZON`，不得作为全年科学结论。
- P0 直接复核：`result_manifest.json` 的 `excluded_runtime_files` 恰为 `run.pid`、`stderr.log`、`stdout.log`；完成后 stdout/stderr 分别为 18,072/1,006 bytes，科学 manifest 仍零失败。这验证了 finalize 后 wrapper 继续打印的实际运行路径。既有 744h 根完全未写入；没有固定服务器 8760h 或新的 ParaCloud 任务。后续仅按 P2 设计目录外只读审计或按 P3 做匹配 A/B，不得因本日志缺陷立即重跑 744h。

## 2026-07-27 本地 manifest 契约与 Base 短门禁闭合

- 本地实施提交 `7499062` 将通用 `stdout.log`、`stderr.log` 加入 runtime-managed manifest 排除集合。在不改变 LP、数据、场景、目标函数、约束、时空边界或 solver profile 的前提下，修复了已知的通用重定向日志契约缺陷。
- 回归先 finalize 科学 manifest、随后向两类 wrapper 日志追加内容，再确认 `validate_result_manifest()` 仍通过。聚焦测试及完整本地 `unittest discover` 套件通过 `67/67`。
- 新的独立 2030 Base 诊断 `outputs/2030_1h_v0727_manifest_runtime_contract` 与 `outputs/2030_24h_v0727_manifest_runtime_contract` 均为 `OPTIMAL`、`solution_qc=PASS`、`scenario_id=base`、灵活负荷/波浪能关闭和 result manifest 闭合。24h 根记录 342,343 个变量、262,201 条约束、1,771,702 个非零元、41.296 s 求解时间与 0.725 GiB 进程树峰值 RSS；它们是 `TEST_ONLY_TRUNCATED_HORIZON`，不是年度科学结果。
- 未改变固定服务器/云端 checkout、进程、输出或调度状态，既有 744h 输出按字节保全。在任何新的服务器 168h 门禁之前，须推送精确审查提交并重复实时核验服务器空闲、checkout 和内存。固定服务器 8760h 仍禁止。

## 2026-07-27 744h optimal/QC pass; strict manifest closure failed

- 2026-07-27 对话收束时再次实时复核：固定服务器无 CISPO/Gurobi 进程，约 69 GiB 可用内存，checkout 干净停留在实现 `c879c99`；本地文档分支起始 HEAD 为 `3664177`。ParaCloud `squeue -u a8s001819` 为空，历史作业状态仍为 `4003088=COMPLETED build-only`、`4003172=OUT_OF_MEMORY`、`4004585=TIMEOUT`，没有已验收的 8760h 结果。
- ParaCloud job `4004585` is terminal `TIMEOUT` after `1-00:00:25`; its batch step is `CANCELLED` after `1-00:00:32`. It reached Barrier iteration 35 at solver time 82,521 s, with primal residual `1.05e8`, dual residual `2.68`, complementarity `6.03e6`, primal objective `2.0166e11` and dual objective `-1.4513e13`. It was still far from acceptance.
- Sampled MaxRSS remains 499,919,116 KiB = 476.76 GiB. The run did not produce `solve_report.json`, `solution_qc.json` or `result_manifest.json`; it is neither solved nor evidence of infeasibility. Preserve the cloud root unchanged. No cloud job is active.
- The fixed-server implementation remains at `c879c99`; local commits after it are documentation continuity updates and must not be mistaken for a different deployed model. The complete local suite at the implementation milestone passes 67/67 and the server solver-profile tests pass. Both 168h spill formulations are `OPTIMAL + solution_qc=PASS`. Projection takes 641.996 s and explicit spill 654.026 s, but explicit spill has lower presolved rows/nonzeros, `Factor NZ`, `Factor Ops` and telemetry solver memory; it is also materially faster in the paired 24h flexibility case. Explicit spill is therefore retained for the memory-bound full-year target.
- Machine-readable evidence is saved at `/data/zz2/National_model/outputs/solver_comparisons/spill_168h_ab_v0726.{json,csv}`. The two original output roots are preserved.
- Persistent solver telemetry, graceful termination and seven traceable numerics-only solver profiles are validated. The user has authorized one-at-a-time 744h or longer stress tests subject to the memory gate. Do not run concurrent CISPO solves and do not start fixed-server 8760h.
- The 168h dual-simplex result overturns its 24h ranking: after 905.073 s/421,470 pivots it remained infeasible and was gracefully terminated, producing a traceable `INTERRUPTED` report. Peak process-tree RSS was only 2.594 GiB, but runtime already exceeded complete Barrier-32 by 38.4%. Dual simplex is excluded from 744h; Barrier-16 and CPU-PDHG remain pending.
- Barrier-16+AMD is `OPTIMAL + solution_qc=PASS` in 644.636 s with 3.187 GiB peak RSS, modestly better than Barrier-32. Forced AMD nevertheless raises Factor NZ/ops by 5.21%/25.54%. A clean `barrier_16_auto_order_v1` control is added before choosing a 744h profile; CPU-PDHG remains pending.
- Barrier-16 automatic order is the accepted scale-up profile: `OPTIMAL + solution_qc=PASS` in 637.344 s, unchanged reference factor structure, 3.538 GB telemetry solver memory and 3.459 GiB process-tree peak.
- The corrected CPU-PDHG root `/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_pdhg_cpu32_v2` was gracefully stopped after 3,074.134 solver seconds and 496,035 last recorded telemetry iterations. It used only 1.990 GB peak solver memory and 2.503 GiB peak process-tree RSS, but had no feasible solution; the terminal region retained primal residual around `49.5`, about `0.6%` primal-dual objective gap and rising dual residual. PDHG is excluded from the first 744h gate but retained as low-memory research evidence.
- The five-profile machine-readable comparison is `/data/zz2/National_model/outputs/solver_comparisons/solver_profiles_168h_v0726.{json,csv}`.
- The fixed-server 744h Base gate was launched at `/data/zz2/National_model/outputs/2030_744h_v0726_spill_explicit_barrier16_auto_order` from clean HEAD `c879c99` with about 69 GiB available RAM, `barrier_16_auto_order_v1`, `Threads=16`, `Crossover=1` and `SoftMemLimit=48`; Python PID at launch was `663050`.
- Its build phase passed in 341.673 s: 3,686,023 variables, 5,920,701 constraints, 42,360,391 nonzeros and 4.977 GiB build peak RSS. Presolve took 223.80 s and reduced the matrix to 3,088,821 rows, 3,017,979 columns and 30,884,732 nonzeros. Ordering took 115.48 s; `AA' NZ=6.449e7`, `Factor NZ=8.062e8` (about 9.0 GB) and `Factor Ops=6.197e12`. An early Barrier checkpoint at iteration 4 recorded 492.91 solver seconds, 25.087 GB peak solver memory, about 19.1 GiB process RSS and about 50 GiB host-available memory.
- Barrier subsequently completed normally in 244 iterations and 8,917.48 solver seconds with interior objective `2,196,881.94 million CNY`. During crossover, dual pushes fell from 1,044,784 to 464,775 remaining, and telemetry reached 358,606 simplex iterations at 9,996.25 s; solver memory was 13.948 GB, process RSS about 13.8 GiB and host-available memory about 55 GiB. These are retained as intermediate checkpoints; the terminal result is recorded below.
- Terminal state: no CISPO process remains. The 744h run is `OPTIMAL + solution_qc=PASS`, objective `2,196,881.920967378 million CNY`, 13,541.717 solver seconds, 244 Barrier iterations, 1,451,182 simplex iterations, 3:52:03 wall time and 23.121 GiB peak process-tree RSS. All hard QC checks pass; maximum constraint/bound/dual violations are below `1e-7`, maximum power-balance residual is `2.40e-10 GW`, AC bidirectional edge-hours and DC reverse flow are zero, scenario is Base, and flexibility/wave are disabled.
- Strict manifest acceptance fails only on `size:stdout.log`: the result manifest records 63,631 bytes while the completed redirected log is 66,236 bytes. All other 57 manifest entries validate. This is caused by using the generic wrapper name `stdout.log`, which is not in `RUNTIME_MANAGED_FILES`, followed by the program's final report print after manifest generation. Preserve the output unchanged and classify it as mathematical/QC evidence, not a closed reproducibility gate.
- Fixed-server checkout remains clean at `c879c99`; the host has about 69 GiB available memory and no active CISPO solve. Do not start 8760h or another cloud task. Exact next action is a reviewed minimal wrapper/manifest-contract fix with tests and a separately identified closure path.
- 下一阶段门禁顺序：本地修复通用 wrapper log 排除/终结契约并增加 append-after-finalize 回归 → Base 1h/24h `OPTIMAL+QC+manifest` → 空闲服务器新根 168h → 决定既有744h采用独立只读审计还是严格重跑 → 匹配24h/168h/744h求解性A/B。新的云端8760h需要单独付费授权、不可变hash、高内存/线程/时限方案和停止规则；固定服务器仍禁止8760h。

## 2026-07-25 20:30 CST Barrier-32 reached iteration 23

- Job `4004585` remains `RUNNING` on `m4cg1702` after 17:55:54 and has passed the exact stage where the 128-thread run failed.
- Ordering completed in 3,180.53 s. Gurobi reports `AA' NZ=7.425e8`, `Factor NZ=3.848e10`, approximately 340.0 GB factor memory, `Factor Ops=2.448e15` and `Threads=32`.
- Barrier iteration 23 completed at solver time 60,528 s. Primal residual/complementarity improved from `8.98e9/6.57e8` at iteration 0 to `7.71e8/4.47e7`; the run is progressing but is not converged and its primal/dual objectives remain far apart.
- `sstat` reports 499,919,116 KiB MaxRSS = 476.76 GiB and 499,955,580 KiB MaxVMSize. This is below the prior sampled 526.99 GiB peak, but it does not establish a safe lower bound for future runs.
- Slurm has 6:04:06 remaining and ends at `2026-07-26 02:34:26 CST`. Recent iterations require about 30-32 minutes, so completion within the current 24h wall limit is uncertain. The Slurm limit will arrive before Gurobi's configured 86,400-second optimize limit because model construction consumed about 41 minutes.
- `solve_report.json`, `solution_qc.json` and `result_manifest.json` are absent; only `build_report.json` is present. No scheduler parameter was changed during this read-only audit. Do not start 2040 or another job.

## 2026-07-25 02:35 CST authorized Barrier-32 cloud retry running

- ParaCloud job `4004585` started at `2026-07-25 02:34:26 CST` on `m4cg1702`. It uses the unchanged `22fb493` Base/`city_337` release, 700G and 24h, with only Gurobi `Threads` reduced from 128 to 32 relative to failed job `4003172`; `Method=2`, `Presolve=2`, `Crossover=1`, `SoftMemLimit=640` and all scientific settings remain unchanged.
- The additive script is `cloud_cispo_8760_2030_base_barrier32.sbatch`, SHA256 `fc604a1a25d37c9cff8a336c83969809cb5b52ea0ab815183d1ea3a7a96bfbf2`. Output is isolated under `outputs/full_year_2030_base_22fb493_barrier32_700g_v0725`.
- The 50-test gate passed in 11.845 s. Runtime stdout reports `FULL_SOLVE_CPUS 32`, and `optimization_2030_cloud_32threads_640gsoft.json` confirms `threads=32`, `presolve=2`, `method=2`, `crossover=1` and `soft_mem_limit_gb=640`.
- Although the script requests 32 CPUs per task, Slurm allocated 96 CPU/billing units because the 700G request exceeds the partition's per-CPU memory ratio. Cost accounting therefore accrues at 96 allocated core-hours per wall-clock hour, while Gurobi remains capped at 32 threads.
- Failed job `4003172` consumed 2,642,304 allocated CPU-seconds = 733.973 core-hours. Its actual `TotalCPU` was 7:03:11. The scheduler's account report shows 48,355 CPU-minutes = 805.917 core-hours for user `a8s001819` across all jobs in the 2026-07-24 to 2026-07-26 window, but it exposes no paid-credit or remaining-quota balance.
- This is active engineering evidence, not an accepted scientific result. Do not change the release, start 2040 or submit another retry while `4004585` is active.

## 2026-07-25 02:14 CST cloud 2030/8760h solve failed OOM before barrier

- ParaCloud job `4003172` is terminal `OUT_OF_MEMORY` with exit `0:125`; it ran from `2026-07-24 20:24:47` to `2026-07-25 02:08:50` for 5:44:03 on `m4cg1702`, using 128 CPUs and a 700G request.
- The full model build succeeded earlier. Gurobi then spent 17,932.25 s in presolve, reducing 68,189,325 rows/40,912,327 columns/515,040,080 nonzeros to 37,982,903/35,423,761/400,861,556.
- Ordering for barrier factorization ran for at least 140 s, but no barrier statistics or iteration 0 appeared. The Python process was killed by Slurm before an optimization iterate existed.
- Accounting records 526.99 GiB MaxRSS and 527.03 GiB MaxVMSize; CPU efficiency was 0.96%. The node is configured with 750G and rebooted shortly after the OOM event, so the sampled peak does not establish the true instantaneous memory requirement.
- `solve_report.json`, `solution_qc.json` and `result_manifest.json` are absent. Preserve `outputs/full_year_2030_base_22fb493_128cpu_700g` as failed engineering evidence; it is not accepted.
- No ParaCloud CISPO job is now active. Do not rerun the identical barrier configuration, do not start 2040, and do not treat the successful 53.633 GiB build-only result as evidence that barrier factorization fits.

## 2026-07-25 wave module corrected to existing marine grid; combined cases added; not deployed

- This local correction supersedes the spatial mapping and scale figures in the wave note immediately below; no accepted server/cloud release, checkout, data root, process or output changed.
- Raw wave rows are intersected with existing `optimization_points.csv` coordinates within `0.02` degrees and then restricted to `is_land=0`. The resulting contract contains 1,285 unique existing marine `grid_uid` rows (1,284 positive-potential options), 9,798.111 GW retained raw potential and 57 imputed-CF rows. The actual maximum coordinate difference is `4.96e-5` degrees.
- Province, substation and `city_337` load-center identifiers now reuse the exact existing `grid_uid` route. The prior nearest-offshore-wind proxy, including erroneous model-boundary-external matches up to roughly 1,524 km, is removed.
- Explicit combined cases `wave_energy_medium_v1_flexible_load_v1` and `wave_energy_medium_v1_flexible_load_comfort_v3` enable both modules in one LP while Base and single-module cases remain isolated.
- Wave and wave+flex preflight reports have overall `PASS` status with 72 records each (67 `PASS`, 2 `INFO`, 3 pre-existing unrelated `WARN`); the complete local regression passes 62/62. Base/wave/wave+flex-V1/wave+comfort-V3 24h build-only gates are respectively 342,343/345,992/350,456/352,688 variables, 262,201/263,810/264,647/266,879 constraints and 1,771,704/1,794,509/1,825,757/1,830,221 nonzeros. No optimization was started.
- Full-year static estimates are 41,186,792 variables/67,877,276 constraints/532,990,308 nonzeros/36.47 GB for wave, and 42,816,152/68,182,781/533,906,823/36.91 GB for wave+flex V1. These are not solve-memory guarantees.

## 2026-07-25 optional wave-energy module passed local build gates; not deployed

- Local worktree based on `796a6fc` adds `wave_energy_medium_v1` without changing Base `VRE_TECHS`, accepted server/cloud releases, data roots, processes or outputs.
- The source audit finds 4,194 unique grids, 4,187 positive-potential grids, 35,898.123 GW raw potential, ten CF scenarios, 241 imputed-CF grids and no 2060 profile. Capacity potential is identical in every source scenario.
- `data/wave/wave_sites.csv` and `wave_input_manifest.json` are reproducible from `scripts/build_wave_energy_inputs.py`; hourly data stay external and require `CISPO_WAVE_ROOT`.
- Wave preflight passes 68 checks and the complete local regression passes 61/61. Base 24h build-only remains 342,343 variables/262,201 constraints/1,771,704 nonzeros; wave 24h build-only is 351,798/266,712/1,867,703. No optimization was started.
- Full-year static estimate with wave is 41,192,598 variables, 67,880,179 constraints, 558,429,297 nonzeros and 37.23 GB. This is not a solve-memory guarantee.
- Deployment remains blocked pending review of maritime routing, scenario-specific potential, 2060 treatment and China cost sensitivities. Do not stage `wave_grid.nc`, change a live checkout or start any wave solve without a new versioned release and explicit authorization.

## 2026-07-24 local comfort-aware flexibility V3 accepted at 24h; not deployed

- Local worktree based on `796a6fc` adds independent `flexible_load_comfort_v3` and `flexible_load_comfort_v3_v2g_5pct` scenarios. Base, accepted V1/V2 and server/cloud releases are unchanged.
- The generated ignored-data table `data/load/flexible_load_envelope_v3.csv.gz` contains 1,357,800 province-year-hour rows. It reconstructs the `Power_curve_V2` BAIT/balance-point formula with a +/-1 C setpoint envelope, retains the upstream future `thermal_multiplier`, matches the National_model load components, and has SHA256 `b5ebda4344a8f978606c242065159f27a75994a5d976f2cbe06038d66a429a03`.
- Thermal flexibility is a causal daily-reset equivalent state. EV V1G uses a rolling 12h cumulative latest-service constraint. Optional V2G is limited to 5% of province-day baseline EV peak, has a four-hour energy envelope and requires charge before discharge through a daily-zero causal state.
- Costs are explicit objective components: thermal reduction/increase are separate, V1G relocated energy is paid once, and V2G discharged energy is paid once while charging energy/losses remain in normal system operating costs.
- Local regression passes 58/58. The no-V2G 2030 24h gate `outputs/diagnostic_24h_flexible_load_comfort_v3` is `OPTIMAL + solution_qc=PASS` with 349,039 variables, 265,270 constraints, 1,807,414 nonzeros, 33.63 s solver time and 0.739 GiB peak process-tree RSS.
- The final independent 5% V2G gate `outputs/diagnostic_24h_flexible_load_comfort_v3_v2g_5pct_final` is also `OPTIMAL + solution_qc=PASS`, with 351,271 variables, 266,789 constraints, 1,821,550 nonzeros, 38.60 s solver time and 0.718 GiB peak RSS. V1G and V2G share one aggregate grid-charging power ceiling; its violation is zero. All transition/terminal checks pass and simultaneous operations are zero.
- This is local truncated-horizon engineering evidence only. No server/cloud state was changed or refreshed during this milestone. Do not launch fixed-server 168h/744h/8760h or another cloud job without explicit authorization and a new versioned release.

## 2026-07-24 21:17 CST prior cloud checkpoint (superseded by OOM terminal state)

- Job `4003088` completed normally in 40m20s (`COMPLETED`, exit `0:0`). The full Base model has 40,912,327 variables, 68,189,325 constraints and 515,040,080 nonzeros. Build-only peak process-tree RSS is 53.633 GiB.
- The success dependency released job `4003172`, now running on `m4cg1702` with 128 CPU, 700G and a 24h limit. Its full model build completed in about 40m32s with identical statistics and 53.686 GiB build peak.
- Gurobi 13.0.2 accepted the WLS license, `Threads=128` and `SoftMemLimit=640`, and entered `Optimize`. At the audit checkpoint the log had not yet emitted presolve completion or barrier iterations; current stage is presolve/matrix preprocessing.
- Current `sstat` batch MaxRSS is 101,085,156 KiB (96.402 GiB). This remains far below both the 700G allocation and 640G solver soft limit, but presolve/barrier factorization may increase it further.
- `solve_report.json`, `solution_qc.json` and `result_manifest.json` do not yet exist. The task is healthy but not accepted. Continue monitoring without changing the release or starting 2040.

## 2026-07-24 local `flexible_load_state_v2` accepted; not deployed

- Local implementation `271c6dc` adds an independent state-based flexibility scenario. Base and the accepted legacy V1/V2G scenario JSON files are unchanged.
- Heating/cooling use daily-reset equivalent inventories with explicit retention/efficiency and loss accounting. EV V1G uses a causal charging backlog derived from the immutable `Power_curve_V2` uncontrolled charging baseline; `ev_hour_weight` is not treated as plug availability. The new formulation refuses V2G until calibrated availability, battery-energy and departure-service inputs exist.
- Full local regression passes 56/56. Final 2030 24h gate `outputs/2030_24h_v0724_flexible_load_state_v2_final` is `OPTIMAL + solution_qc=PASS`, with 349,039 variables, 265,270 constraints, 1,807,414 nonzeros, 32.84 s solver time, 0.705 GiB peak process-tree RSS, transition residuals at most `8.88e-16 GWh`, zero terminal state/backlog, zero simultaneous up/down and a valid result manifest.
- Four-year 1h diagnostic chain `outputs/planning_sequence_1h_v0724_flexible_load_state_v2` passes all four solve/QC/manifests and immediate `--resume`. It is engineering evidence only.
- Full-year static estimate is 43,356,367 variables, 68,724,249 constraints, 524,283,387 nonzeros and 36.84 GiB model memory. This is not a barrier-memory guarantee and no 8760h job was started.
- No fixed-server or cloud checkout, process, input or output was changed. Retain the existing active cloud release and output roots unchanged. Any deployment of `271c6dc` requires a new versioned identity and fresh authorized 24h/168h gates.

## 2026-07-24 local post-release hardening; not deployed to active cloud run

- Local code based on `4b5bd98` now forbids wind-to-PV CF fallback, hard-fails unresolved wind after same-grid mixed-wind, and requires land-centroid donors for nearest-province PV fallback. Current data have 35 onwind and 10 offwind same-grid mixed-wind rows, zero wind-to-PV mappings, and 141 PV-family nearest-grid fallbacks; the land-donor restriction changes zero current donor assignments.
- Focused tests pass 4/4 and the full local suite passes 54/54. Two live contract documents now describe production `city_337` as a 337-city annual allocation/transmission proxy, not a 337-city hourly nodal dispatch network.
- This hardening is local only. Do not change the staged cloud release, its checkout, inputs or output roots while its authorized jobs are active. Any later deployment requires a new identity and fresh small gates.

## 2026-07-24 ParaCloud 24h/168h accepted; full-year build and authorized single-year solve active

- Cloud 2030 Base 24h job `4003035` (32 CPU, 64G) and 168h job `4003045` (32 CPU, 64G, `m4ci1805`) each pass 50/50 tests, `OPTIMAL`, `solution_qc=PASS` and independent result-manifest validation. Their solver statistics are respectively 342,343 variables/262,201 constraints/1,771,703 nonzeros/26.978 s/0.834 GiB and 1,011,079/1,393,915/9,797,949/377.057 s/3.661 GiB.
- Full-year build-only job `4003088` is running on `m4cm1904` in `amd_a8_768` with 128 CPU and 700G. It constructs but does not optimize the 2030 Base 8760h LP, writing `outputs/full_year_build_only_2030_22fb493_128cpu_700g`.
- The user explicitly authorized one real 2030/8760h Base solve. Job `4003172` is submitted as `afterok:4003088`, requests 128 CPU, 700G and 24h, writes the separate root `outputs/full_year_2030_base_22fb493_128cpu_700g`, and raises only Gurobi `soft_mem_limit_gb` from the fixed-server 80 to 640. Do not start a successor year or a second full-year run while this evidence is pending.

## 2026-07-24 ParaCloud city_337 release staged; 8760h preflight and repaired WLS smoke passed

- New cloud release: `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493`. It carries code archive `22fb493` (SHA256 `2f3564ff9123b292106e51bd5ee943e13e874b6798450e38a96428a48a3b6b7a`) and exactly 11,350 runtime data files whose cloud SHA256 check matches the fixed-server manifest (`662565a090b64523ec353994e6fdb3314a94b88d429f16e85e1665300ffbc85a`). The release is additive and does not modify the fixed server.
- Cloud preflight job `4001137` completed on `m4ci1905.para.bscc`: 175.17 GiB available memory exceeds the full-year 96 GiB gate. For 2030 Base/city_337 it estimates 40,912,327 variables, 67,604,064 constraints, 520,922,832 nonzeros and 36.0 GiB static model memory. This is a data/scale gate only, not a Gurobi build or solve.
- Cloud environment was completed offline with the project numerical stack and `pip check` passes. The user-authorized repair of the three `.bashrc` proxy exports was verified on compute node `m4ci1905` by job `4002980` (`PROXY_EXPORT_COMPUTE_PASS`, HTTP 302 through `172.16.110.3`). WLS job `4002981` then reached `Env.start()` and solved its LP to `OPTIMAL` with `GUROBI_SMOKE_PASS`. Its standalone 10-second curl check timed out, but the authenticated Gurobi solve is the decisive license evidence.
- No cloud 24h/168h, full-year build-only or full-year solve is active. Next cloud action is a new versioned 24h gate, then a 168h gate, with explicit Gurobi thread limits; the full-year build-only gate remains later. Fixed server remains idle and restricted to its accepted 24h/168h roots; do not start fixed-server 744h/8760h.

## 2026-07-23 city_337 fixed-server 168h V2G accepted; server idle

- Four-year 168h V2G root `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v2g_v1` and immediate `--resume` pass. All years are `OPTIMAL + solution_qc=PASS`; runtimes are 792.55/806.12/953.60/1033.25 s, wall time is 1:09:57, peak RSS is 4,087,888 KiB and swaps are zero.
- Every 59-entry SHA256 manifest validates. The V2G model has 1,057,951 variables, 1,404,982 constraints and 10,100,013 nonzeros. All hard checks pass; maximum center/province/intra/power residuals are `5.12e-12/3.64e-12/3.11e-08 GWh` and `1.60e-10 GW`; BECCS closure is zero.
- V2G transition residual is at most `1.90e-13 GWh`, simultaneous charge/discharge is zero, and period charging losses of 7.747/4.509/13.909/42.092 GWh equal both `charge-discharge` and net-load energy change to numerical precision.
- No CISPO/Gurobi process remains. Base, V1 and V2G have all passed 24h/168h city_337 gates. Do not start fixed-server 744h/8760h without separate authorization.

## 2026-07-23 city_337 fixed-server 24h V2G accepted

- Four-year 24h V2G root `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337_flexible_load_v2g_v1` and immediate `--resume` pass. All years are `OPTIMAL + solution_qc=PASS`; runtimes are 44.81/43.45/48.35/45.23 s, wall time is 9:10, peak RSS is 934,340 KiB and swaps are zero.
- Every 59-entry SHA256 manifest validates. V2G is enabled only in this separate scenario; maximum transition residual is `1.83e-12 GWh`, simultaneous charge/discharge is zero, and 2040/2050/2060 charging losses of 0.1563/2.3423/3.4673 GWh close exactly against net-load energy change within floating-point precision.
- Maximum center/province/intra/power residuals are `6.37e-12/5.24e-13/4.61e-10 GWh` and `2.46e-12 GW`; heating/cooling/EV V1G daily conservation, security and BECCS checks also pass.
- The follow-on 168h V2G chain has completed and is accepted in the newer status section above.

## 2026-07-23 city_337 fixed-server 168h V1 accepted

- Four-year 168h V1 root `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v1` and immediate `--resume` pass. Every year is `OPTIMAL + solution_qc=PASS`; runtimes are 714.39/816.08/1007.71/980.09 s, wall is 1:08:59, peak RSS is 4,030,672 KiB and swaps are zero.
- All four 59-entry SHA256 manifests validate. Each year exports 337 center balances, 2,022 center-technology rows, 642 intra edges, 31 province accounts, 31 flexibility accounts and 57 output-catalog data rows. Maximum center/province/intra/power residuals are `5.06e-12/3.64e-12/4.69e-11 GWh` and `1.75e-10 GW`; BECCS closure is zero.
- Maximum heating/cooling/EV V1G daily-energy residuals are `1.17e-12/1.78e-15/4.26e-13 GWh`; simultaneous up/down counts are zero and V2G is disabled. Four `RESUMED_ACCEPTED` records revalidate scenario and strict state-chain identity.
- The V1 matrix has 1,042,327 variables, 1,399,774 constraints and 10,016,685 nonzeros: +3.09%, +0.42% and +2.23% versus Base. Total solver time is nevertheless 8.23% lower; 2050/2060 crossover (265.69/288.77 s) is the remaining performance variability.
- The follow-on 24h V2G chain has completed and is accepted in the newer status section above.

## 2026-07-23 city_337 fixed-server 24h V1 accepted

- Four-year 24h V1 root `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337_flexible_load_v1` and immediate `--resume` pass. Every year is `OPTIMAL + solution_qc=PASS`, has 59 manifest entries and closes the 337-center network; runtimes are 40.84/44.23/43.39/41.95 s.
- The wrapper completed in 9:35 with peak RSS 929,096 KiB, zero swaps and exit status zero. Maximum daily heating/cooling/EV V1G residual is `1.14e-13 GWh`, all simultaneous up/down counts are zero, and V2G is explicitly disabled.
- Capacity margin remains 5%, effective inertia remains 3.5 s, all hard checks pass and BECCS net-carbon closure is zero. These are truncated engineering diagnostics, not scientific planning results.
- The follow-on 168h V1 chain has completed and is accepted in the newer status section above.

## 2026-07-23 city_337 fixed-server 168h Base accepted

- Four-year 168h Base root `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337` is accepted: sequence and `--resume` pass, all years are `OPTIMAL + solution_qc=PASS`, runtimes 733.00/811.58/892.10/1397.12 s, wall 1:13:47, peak RSS 4,085,152 KiB and zero swaps.
- Every year has zero false hard checks, 59 valid manifest entries, 337 center balances, 642 intra-edge outputs and 31 province accounts. Maximum network/power residuals are below `1.78e-10` in their reported units; BECCS closure is numerical zero.
- Relative to the prior 278 Base gate, the 168h city model adds 1,031 variables, 924 constraints and 2,749 nonzeros. Total solver time rises 4.68%; the measurable risk is 2060 Crossover (706.6 s), not model construction or memory.
- The follow-on 24h `flexible_load_v1` chain has completed and is accepted in the newer status section above.

## 2026-07-23 city_337 fixed-server 24h accepted; 168h active

- Fixed-server checkout is clean at `cf39e0a`; active data root is `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`. The city archive SHA256 matches local: `c1451d95c3303f98e53434cd29abc4288f486cba04c99a2c591380b010d470bb`.
- Server regression is 50/50, smoke is 142/142, readiness/full-license and preflight pass. The initial 139-check smoke failure was an obsolete 8-technology row expectation; the production table is correctly 31×5×10=1,550 unique rows and the corrected smoke now validates this explicitly.
- Four-year 24h Base root `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337` and immediate `--resume` are `PASS`. Runtimes are 43.29/48.82/41.17/46.90 s, wall time 7:21, peak RSS 930,204 KiB, and all four 59-file manifests validate. Base flexibility is disabled; 5% capacity margin, 3.5 s inertia, power/network/BECCS checks all pass.
- The new four-year 168h Base chain is active as PID `3321747` under `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337`. Do not change checkout or data root until it exits and is audited. Do not start 744h/8760h.

## 2026-07-23 city_337 local gate and pre-deployment server audit

- Local implementation commit `8e76753` promotes `city_337` to production while retaining `natural_earth_278` as a separate CISPO replication/sensitivity package. The package has 337 centers, 16,609 VRE routes, 2,030 hydropower routes, 642 intra-provincial edges and 203 positive 2025 initial edges.
- Data QA is `PASS`: 31 connected provincial graphs, province demand-share error at most `1.11e-15`, initial network-balance residual at most `7.28e-14 GW`, and exact joint routing is never materially worse than the old nearest-substation-first rule (mean distance reduction 20.21 km).
- Local validation passes 50/50 tests and 61 preflight checks. `outputs/planning_sequence_1h_v0722_city337` passes all four years and `--resume`; each year is `OPTIMAL + solution_qc=PASS`, has 337 load-center rows, a closed 59-file result manifest, Base flexibility disabled, 5% capacity margin and 3.5 s effective inertia.
- Live fixed-server audit before deployment: branch `codex/cispo-2030-full-lp`, clean HEAD `6ed943a`, no active CISPO/Gurobi process, about 35 GiB available memory, 21 GiB swap occupied and 3.8 TiB free on `/data`. The accepted V1 168h root remains `PASS` after its prior four-year resume audit.
- Exact next gate: push/deploy the code plus a SHA256-verified additive `city_337` data root, pass server tests/readiness, then use new 24h and 168h Base output roots. Do not reuse accepted roots and do not launch fixed-server 744h/8760h or paid cloud 8760h.

## 2026-07-22 reviewed reliability parameters (local only)

- Local Git HEAD remains `e28f315`; the working tree now sets Base provincial capacity margin to `5%` and minimum inertia to `3.5 s reference × 1.0 tolerance = 3.5 s effective`.
- Model construction and solution QC use the same effective-threshold resolver. Legacy scenario overrides containing `minimum_system_inertia_seconds` remain accepted and take precedence within that scenario.
- Local regression tests pass 49/49. Local 1h output `outputs/2030_1h_v0722_security_5pct_inertia_3p5s` is `OPTIMAL + solution_qc=PASS`; effective inertia is `3.5 s`, capacity-margin/inertia checks pass and the result manifest validates. No fixed-server checkout change, server process or server output was created.
- Fixed-server checkout and all accepted Base/V1 gates remain at their previously recorded versions and therefore still reflect the old committed security configuration. Do not compare new local results against those outputs without identifying this feasible-set change.
- The next server action, if authorized, is a new versioned 24h gate after committing/pushing/deploying the exact reliability update. Do not reuse accepted output roots and do not start fixed-server 744h/8760h or paid cloud 8760h.

## 2026-07-22 V0722 flexibility deployment and server gates (authoritative)

- Local commit `c62b769` closes the CISPO-equivalent BECCS carbon mass balance without changing the published net factors, objective or feasible set. Local validation is 47/47 tests plus an `OPTIMAL/QC PASS` 1h gate with zero new closure residuals and a valid manifest. This commit is not deployed; the fixed server remains unchanged at `6ed943a`, and no new server job was started.
- Local commit `c91828a` adds a diagnostic sensitivity-suite runner and passes 45/45 tests plus a real 1h Base/V1/V2G suite (12/12 year-scenario cases `OPTIMAL + solution_qc=PASS`, closed manifests, identity-safe `--resume`). This is local interface evidence only: the runner is not deployed, no server job was started, and the fixed-server checkout remains clean and idle at `6ed943a`.
- Commit `6ed943a` implements the optional flexibility/scenario interface and is now the clean fixed-server checkout. It passes 42/42 local and server tests plus local Base 1h, V1 24h and V2G 24h `OPTIMAL/QC PASS` gates.
- The fixed-server Base 168h gate ran from checkout `b6ca42d`, whose model implementation baseline is `0c1eaf2`; this corrects the earlier shorthand that described the checkout itself as `0c1eaf2`. The active data root remains `/data/zz2/National_model/data/model_ready_20260722_v0721_fuel_state`.
- The server four-year 24h sequence and immediate resume audit pass for 2030/2040/2050/2060.
- Four-year 168h Base sequence `/data/zz2/National_model/outputs/planning_sequence_168h_v0721_fuel_state` completed `PASS`: all years are `OPTIMAL + solution_qc=PASS`, every result manifest validates, the resume identity audit passes, wall time is 1:08:40, peak RSS is 4,116,892 KiB and swap is zero.
- Four-year 24h `flexible_load_v1` sequence `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_flexible_load_v1` completed `PASS` and passed resume identity validation. Wall time is 6:32, peak RSS is 946,804 KiB and all daily flexibility residuals are below `6.44e-13 GWh` with no simultaneous up/down.
- Four-year 168h `flexible_load_v1` sequence `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1` completed `PASS` from clean checkout `6ed943a`; PID `1708266` has exited and no CISPO process remains. All four years are `OPTIMAL + solution_qc=PASS`, all hard checks pass, and every 59-file result manifest validates. Solver runtimes are 705.49/672.16/994.41/1181.26 s; wall time is 1:06:54, peak RSS is 4,040,256 KiB and swap is zero. Maximum heating/cooling/EV V1G daily-energy residual is `8.17e-13 GWh`, simultaneous up/down counts are zero, and scenario SHA256 is consistently `7b8f1c920bad35e2e41111f7913cfb456b6e369b85db5b03ae86d43801840532`.
- A fresh 168h `--resume` identity audit at 2026-07-22 16:05 CST completed `PASS` with four `RESUMED_ACCEPTED` years. The accepted capacity-cohort chain remains explicitly `TEST_ONLY_TRUNCATED_HORIZON` and cannot enter production.
- Flexibility is disabled in Base. Local full-year static estimates are 40.91M variables for Base, 42.54M for V1 and 43.36M for V2G; the 96 GiB availability gate remains unchanged.
- No fixed-server 744h/8760h and no cloud 8760h task is running. The V1 168h gate is now accepted, but cloud production remains gated on calibrated sensitivity assumptions, exact code/data/scenario deployment, cloud 24h/168h gates, explicit Slurm thread limits and explicit cost authorization.

## 2026-07-20 V0720 I/O-contract deployment (authoritative)

- Fixed-server checkout is clean at `b40900a`; active model data are `/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds` with the existing versioned hydrology and CF stores.
- Server unit tests pass 34/34 and data-package smoke checks pass 139/139.
- New 24h gate `/data/zz2/National_model/outputs/2030_24h_v0720_io_contract_server` is `OPTIMAL + solution_qc=PASS`: 341,312 variables, 261,280 constraints, 1,768,957 nonzeros, objective `2,024,722.739184 million CNY`, solve time 43.65 s and peak RSS 0.838 GiB.
- All 27 hard checks pass. The SHA256 result manifest is closed with zero mismatches; all NPZ files are pickle-free; the output catalog has 50 files, the field dictionary has 493 rows, and LP dual export contains 744 hourly price rows plus 3,366 annual constraint-shadow rows.
- At launch, about 88 GiB RAM was available. Another user's four Python training processes occupied about 29 GiB RSS and were not changed. This was safe for 24h only and remains below the 96 GiB full-year build gate.
- No 744h or 8760h process is running. The next full-year solve belongs on the cloud platform after compute-node Gurobi licensing, data staging and small gates are verified.
- The old `5a9f4ab` 744h result remains an engineering solvability gate, not a V0720 or scientific-horizon result. Its old manifest has two wrapper-after-hash mismatches (`run.stdout`, `run.time`); see `MODEL_744_SERVER_RUN_AUDIT_20260720.md`.

## 2026-07-19 V0719 deployed server status (authoritative)

- Current server checkout is `bc83663`, including V0719 capacity-bound/DC active-index commit `451b1c0` plus server smoke-test path fixes `c8db9be` and `bc83663`.
- Active V0719 data root is `/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds`. It was created additively; the old `model_ready_20260719_sequential_sparse` root and the completed 744h output were not overwritten.
- Generated V0719 tables are present: `thermal/nuclear_capacity_upper_by_year.csv`, `biomass/capacity_upper_by_province_year.csv` and `storage/battery_capacity_floor_by_province_year.csv`. The root also includes `sets/model_years.csv` and canonical smoke/QC support files that were absent from the old sparse root.
- Server smoke checks passed 139/139, server unit tests passed 32/32 and readiness passed with full Gurobi license plus raw-GRFR SHA256 verification.
- Server 24h V0719 solve `/data/zz2/National_model/outputs/2030_24h_v0719_capacity_bounds_server` reached `OPTIMAL + solution_qc=PASS`: 341,312 variables, 261,280 constraints, 1,768,957 nonzeros, objective `2,024,722.7392 million CNY`, Gurobi runtime 48.96 s and peak process-tree RSS 0.841 GiB. Nuclear floor/upper, biomass+BECCS capacity upper, storage floor, AC bidirectionality and DC reverse-flow hard checks are all zero.
- Requested direct 8760 trial was not launched because the live full-year preflight failed the checked memory gate: `/data/zz2/National_model/outputs/2030_8760_v0719_preflight_memory_check` reported available memory `73.15 GiB` against required `96.0 GiB`. The V0719 full-year estimate is 40,911,296 variables, 67,603,283 constraints and 520,920,489 nonzeros.
- The completed pre-V0719 sparse 744h gate `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` remains valid solver evidence for deployed HEAD `5a9f4ab`, but it is not the V0719 scientific boundary.
- Sections below this heading include older handoff snapshots; use this authoritative section for current deployment and launch decisions.

## 2026-07-19 V0719 local capacity-bound correction

- Local working tree based on Git HEAD `f84143a` / implementation base `5a9f4ab` now implements four reviewed corrections: provincial nuclear upper bounds, shared `bio+bioccs` capacity upper bounds, the CISPO Table S17 2030 battery floor, and active-index AC-only reverse-flow variables.
- New reproducible inputs are generated by `scripts/build_v0719_capacity_bounds.py` from `config/capacity_bounds_v0719.json`; `config/model_input_files.json` contract v2 requires all three new tables.
- Local unit tests passed 32/32; data-package smoke checks passed 139/139. The corrected 24h solve under `outputs/2030_24h_v0719_capacity_bounds_dc_sparse_rerun` reached `OPTIMAL + solution_qc=PASS` with 341,312 variables, 261,280 constraints and 1,768,956 nonzeros. Every nuclear/biomass/storage bound residual and every transmission-direction hard check passed.
- Full-year active-index estimate is now 40,911,296 variables, 67,603,283 constraints and 520,920,489 nonzeros; exact variable reduction is `363×8760=3,179,880`. This is a structural estimate, not barrier-memory proof.
- This local V0719 correction is **not yet committed, deployed or used by the server**. The server remains at `5a9f4ab` and its current versioned data root remains unchanged.
- Server check at 2026-07-19 20:14 Asia/Shanghai: corrected old-code 744h gate `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` has completed. `solve_report.json` reports `OPTIMAL`; `solution_qc.json` reports `PASS`. It used the old versioned data root and did not include the uncommitted V0719 capacity-bound/DC active-index corrections.

## 2026-07-19 synchronized server validation

- Current deployed implementation `5a9f4ab`; readiness/raw-GRFR/full-license gates and 29/29 server tests pass.
- Strict corrected 168h output `/data/zz2/National_model/outputs/2030_168h_sparse_gate_strict`: 1,071,032 variables, 1,392,960 constraints, 10,100,058 nonzeros, `OPTIMAL` in 666.45 s, peak RSS 3.910 GiB and `solution_qc=PASS`. AC bidirectional edge-hours and DC reverse flow are both zero.
- Corrected 744h CPU gate under `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` completed with `OPTIMAL + solution_qc=PASS`: 3,955,064 variables, 5,919,746 constraints, 43,707,940 nonzeros, objective `2,196,413.3453 million CNY`, Gurobi runtime 16,245.79 s, wall time 4:37:02 and peak process-tree RSS 21.979 GiB. Directionality QC passed with zero AC bidirectional edge-hours and zero DC reverse flow.
- Full-year available-memory gate is now checked in as 96 GiB; the unused `NodefileStart`-style config was removed because this is a continuous LP, not branch-and-bound.
- Solvability audit `ab9dfe8` revises the current-code 8760 projection to approximately 44,091,176 variables, 68,188,384 constraints and 515-524 million nonzeros. The prior 853.5 million nonzero preflight is conservative for the raw matrix, but the reported 46.62 GiB is not a barrier peak-memory estimate.
- The rejected 744h barrier formed `8.289e8` factor nonzeros (about 10 GB), then spent 10,969.01 s in barrier and 9,123.64 s in crossover. Linear factor-memory extrapolation is already about 118 GB at 8760h before the model and workspaces are counted; a direct solve on this 125 GiB host is therefore high risk.
- Earlier pre-launch resource snapshot: server HEAD was `f22b9cf`, about 30 GiB available RAM and 21 GiB/21 GiB swap occupied. This snapshot is superseded by the active corrected 744h status recorded above; 8760 was not launched.
- Full-year build-only requires at least 96 GiB available RAM after V0719 server gates, not merely after this old-code 744h. A successful build-only does not authorize solve; inspect peak RSS and factor-risk estimates first.

- Current implementation commit: `1b6da28` (`fix: align interprovincial flows with CISPO`).
- The production sequence is now 2030/2040/2050/2060, with checksummed capacity-cohort transfer between successive full-year solves.
- Local final 24h gate: 349,962 variables, 260,973 constraints, 1,827,245 nonzeros; `OPTIMAL` in 58.79 s; `solution_qc=PASS`; peak RSS 0.698 GiB.
- Local full-year preflight: 44,090,772 variables, 67,603,314 constraints, 853,505,952 estimated nonzeros and 46.62 GiB estimated model memory; local available RAM does not meet the 64 GiB build gate.
- PHS now uses the GHT 2026 province-level 8h-storage floor/project-pipeline upper: 2030 national floor 65.94 GW and upper 249.191 GW; 2040+ upper 514.755 GW.
- Server readiness and raw-GRFR SHA256 verification passed on the 2026-07-19 versioned data roots; server regression tests passed 24/24.
- Server 24h gate: 349,962 variables, 260,973 constraints and 1,827,246 nonzeros; `OPTIMAL` in 60.53 s; `solution_qc=PASS`; peak RSS 0.851 GiB.
- PID `3778049` completed `OPTIMAL`, but the result is rejected: 3,358 material simultaneous AC-direction edge-hours were omitted from the former hard QC. The corrected formulation still needs new server gates.
- Do not start 8760 on the old scientific boundary. The sparse cleanup and corrected 744h gate have passed for deployed HEAD `5a9f4ab`, but V0719 capacity-bound/DC active-index corrections still need commit, deployment to a new versioned data root and fresh 24h/168h/744h gates. Require at least 96 GiB available RAM for build-only; a direct solve remains blocked pending true build/factor-memory review.

## Boundary and architecture

- 2025 is an input boundary only; it is not an optimization year.
- 2030 is the first planning year and represents changes over 2025-2030.
- Production is one continuous LP containing all 8760 chronological hours.
- No Benders decomposition, representative days, sampled hours, or temporal weights are used.
- Optional 744h and 4344h leading-hour horizons are explicitly test-only; 8760h remains the only scientific horizon.

## Implemented

- 31 provinces and 36,686 VRE technology-site rows at 0.25-degree resolution.
- Exact 2023 hourly CF linkage with sparse coefficient construction.
- Continuous capacity-based RUC and cyclic annual commitment/ramp state.
- Battery/PHS SOC and reserve; station-level hydropower and reservoir balance. Commit `b3e6298` adds Stage2 core-mainstem conventional hydropower cascade coupling and is deployed on the server.
- 411 interprovincial corridors, strict hourly power balance, reserve and inertia.
- DAC, annual carbon and biomass accounts, CCS capture and point-level injection.
- Spur/trunk/substation augmentation, memory gate, numerical diagnostics and IIS.
- Production load centers are the 278-node Natural Earth paper replication.
- Annual center energy allocation, provincial export closure and 517-edge intra-province AC500 expansion layer.
- Hydropower station-to-substation/load-center routing and hydro spur/trunk augmentation.

## Verification snapshot

- Current deployed implementation baseline: `827b37f` on 2026-07-19; it contains implementation commit `2a0ee99`. Verify the live HEAD directly because documentation-only synchronization commits follow this baseline.
- Current validated server data paths:
  - `CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260719_sequential_sparse`
  - `CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse`
  - `CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019`
- Raw GRFR transfer completed on 2026-07-06 and was verified on the server:
  - `output_pfaf_03_2019.nc`: 3,380,260,808 bytes, SHA256 `84ff2c882fb17a4b8693bb0773718c2472038021b64618b05f99f8070a506e0f`.
  - `output_pfaf_04_2019.nc`: 5,445,519,752 bytes, SHA256 `e56d5da855ddbdafabdafcb5582981b3f0003054156cf8d912d24a9efd232756`.
- Server readiness with `--require-raw-grfr --verify-raw-grfr-sha256`: `PASS`, zero hard failures.
- Hydropower station input: 2,030 rows, 620 reservoir rows, 1,410 run-of-river rows, 0 potential paper-rule mismatches, no missing required columns. Cascade readiness reported 142 nodes, 124 edges, 4 low-correlation edges, 18 max-bound edges and maximum lag 168 h.
- Server regression test on the synchronized checkout/data: 24/24 tests passed with `unittest` in 19.62 seconds.
- Current one-month preflight: 3,954,660 estimated variables, 5,912,178 constraints, 73,853,760 nonzeros and 4.08 GiB estimated model memory.
- One-month cascade server preflight: 4,761,900 variables, 6,465,714 constraints, 78,282,048 nonzeros; estimated model memory 4.48 GiB; memory gate passed with about 106.65 GiB available.
- Actual one-month cascade model build: 4,808,836 variables, 6,536,681 constraints and 46,092,407 nonzeros.
- Full-year server preflight: 48,164,172 variables, 68,689,554 constraints, 862,195,872 nonzeros.
- Conservative full-year model-memory estimate: 47.98 GiB; configured `SoftMemLimit`: 80 GiB.
- Local 744h build-only test: 3,032,784 variables, 4,760,844 constraints, 39,084,173 nonzeros; completed in about 134 seconds without optimization.
- Local 24h smoke solve: 365,184 variables, 285,309 constraints and 1,812,785 nonzeros; continuous LP solved to optimality in about 8 seconds after presolve. Maximum center-balance and province-export residuals were `1.16e-13` and `1.14e-13` GWh; no edge flowed in both directions, DPV spur augmentation was exactly zero, and no intra-capacity constraint was violated.
- Six-month/full-year local preflight correctly reported that the 32/64 GiB memory gates were not met; no construction was attempted.
- Server: 96 logical CPUs, 125 GiB RAM, 4.3 TiB free under `/data`.
- Server Gurobi Optimizer and `gurobipy`: 13.0.2 installed under `/home/zz2/opt/gurobi1302/linux64` and `/home/zz2/.local/envs/cispo-2030` respectively; 12.0.1 remains available as rollback software.
- Server license: retrieved successfully with Gurobi 13.0.2 on 2026-07-03, stored at `/home/zz2/gurobi.lic`, and valid through 2027-07-02. The server-issued license ID is 2840423.
- Production-license gate passed on 2026-07-06: Gurobi 13.0.2 solved the deterministic 2,501-variable LP to optimality with objective `1.0`, confirming that the bundled size-limited fallback is not active. This gate is also enforced by `scripts/check_server_readiness.py`.

## Cascade server validation status

- Implementation commit `b3e6298` reads Stage2 core cascade files from `D:\codeenv\pycharmproject\National_RL\Gis_process\hydro_power\process_hydro\hydro_model_2019_stage2_classification_cascade_20260630`.
- Generated cascade inputs contain 142 COMID nodes, 124 directed edges and 146 mapped reservoir stations. All mapped stations exist in `data/hydro/hydro_stations.csv`, all are `reservoir_storage`, capacity alignment residual is 0.0 GW and the topology is acyclic.
- Travel lags are estimated from 2019 GRFR hourly discharge by 3h-multiple cross-correlation, range 0-168 h. QA warnings remain for 4 low-correlation edges and 18 edges selecting the 168 h maximum search bound.
- Local checks passed: data-package rebuild with 90 QC checks and zero failures, smoke test 118/118 PASS, unit tests 16/16 PASS, one-month preflight PASS, and custom 24h monolithic build PASS with 146 cascade reservoir rows and 124 cascade edges.
- Server readiness, regression, preflight and full 744h model-build gates passed using the versioned cascade data roots.
- The old 744h solve under `/data/zz2/National_model/outputs/2030_one_month_hydro_cascade` was normally interrupted after `37,576.53 s`. Final status is `INTERRUPTED`, `solution_count=0`, and peak RSS is `22.161 GiB`; the output is preserved as the failed numerical baseline.
- Commit `281f9c7` scales water flow/volume variables without changing physical equations. Server 168h validation under `/data/zz2/National_model/outputs/2030_diagnostic_168h_numerics_scaled` reached `OPTIMAL` in `675.56 s`, used `4.061 GiB` peak RSS and passed every `solution_qc.json` hard check.
- Commit `a8cd150` switches hydropower environmental flow to the 2019 single-year monthly P30 proxy and removes obsolete master boundary variables. Server 24h P30 CPU validation under `/data/zz2/National_model/outputs/2030_diagnostic_24h_p30_cleanup_cpu` reached `OPTIMAL` in `45.06 s`, used `0.879 GiB` peak RSS and passed `solution_qc.json`.
- GPU-enabled Gurobi is available only in `/home/zz2/.local/envs/cispo-gurobi-gpu` (`gurobipy 13.0.2+cu129`). It confirmed `Start PDHG on GPU`, but the same 24h model with GPU-PDHG was still iterating after about 600 s and was interrupted without `solve_report.json`; CPU barrier remains the default route.
- PID `3778049` completed with 3,955,002 variables, 5,919,470 constraints and 44,169,131 nonzeros; build 348.74 s, solve 20,118.58 s and peak RSS 22.141 GiB. Although the old report says `solution_qc=PASS`, post-audit found 3,358 material bidirectional edge-hours, so the output is explicitly rejected and 8760h remains blocked.
- Commit `1b6da28` aligns with CISPO S4-55/S4-56: AC shared bidirectional capacity, DC fixed direction, `0.001 yuan/kWh = 1 yuan/MWh` flow cost, net-exchange load-center closure and hard directionality QC. Local 26/26 tests and corrected 24h `OPTIMAL/QC PASS` succeeded with zero AC bidirectionality and zero DC reverse flow.
- Corrected server validation also passed: 26/26 tests; 24h Gurobi 13.0.2 `OPTIMAL` in 43.88 s; 0 AC bidirectional edge-hours; 0 DC reverse flow across 363 DC edges; all hard QC and scientific manifest hashes PASS. Output: `/data/zz2/National_model/outputs/2030_diagnostic_24h_20260719_cispo_flow_alignment_cpu`.
- Corrected 744h was initially deferred when available RAM was only about 32 GiB and swap was full; it was launched later after memory pressure cleared and completed `OPTIMAL/QC PASS`. Current authoritative status is recorded at the top of this file.

## Explicit unresolved inputs

- CSP site potential and hourly profiles; CSP remains disabled.
- Open-loop and closed-loop PHS hydraulic pairing data remain unavailable; current PHS is province-level 8h storage with GHT 2026 operating floor and year-available project upper.
- Thermal online fuel term `f_on`; fuel is charged on gross generation only.
- Hydropower type labels include low-confidence assigned labels because source data do not provide reliable type labels for all stations; retain them for now and validate later against external station evidence.
- Formal multi-year environmental flow for hydropower; the current cleanup uses the requested 2019 single-year monthly P30 proxy, not a formal 1980-2019 climatological P30. Four low-correlation and eighteen max-bound cascade-lag edges need manual hydrological/topological review.
- Capacity-credit values and spur/trunk proxy costs still need parameter-source review. Base capacity margin and inertia threshold are reviewed locally at `5%` and `3.5 s` but are not yet deployed on the fixed server.
- Intra-center annual capacity uses a 50% design utilization assumption; two western AC500 proxy edges exceed the 1000 km source range.
- Intra-center losses remain zero until their annual energy can be fed back into the provincial hourly balance.

Per-year production entry: `scripts/run_cispo_2030_full_year.py`.
Sequential production entry: `scripts/run_cispo_planning_sequence.py`.


## 2026-09-13 追加更正：无Crossover资格未通过

- 2026-09-13 Crossover约定更正（覆盖上一条直接沿用Cross2启动的结论）：原定Stage A和Thermal均为Crossover0/SolutionTarget1。
  先前本地修复采用Cross2后QC通过，再带入全国候选，不能称为沿用既定方案；用户提醒后诊断入口已恢复0/1，资源仍44线程/64CPU/700G/SoftMemLimit=null。
  本次v9同MPS夏季24h无Crossover冷测试：BarConvTol1e-6/1e-4均OPTIMAL，但原行最大残差1.164401e-3/1.313795e-3，完整QC HARD_FAIL；耗时23.143/21.176s、83/74轮。
  最差行reservoir_independent_hourly_transition[345,0]，另有跨省双向流及城市网络QC失败。此前Cross2的PASS不能作为无Cross全年资格；本轮未测Cross0/1e-8完整QC，不推荐据此启动多年/多日生产。
  1e-6只保留为未验收诊断测试值；源v9和物理模型未改，不自动Crossover/Stage B。5项入口测试、参数实际回读和dry-run通过。
  旧Cross2启动包保留但资格建议撤回，新Cross0诊断归档197文件哈希通过，非科学验收包；新全国任务未上传/提交，Thermal未修改。
  Git0a03cc452e95d158f36923ceb5210267979b6234未提交；修改scripts/probe_full_year_numerics.py、tests/test_full_year_numeric_probe.py及四份交接文档。
  命令/输出/失败记录/前后快照/差异/哈希：supplementary_materials/reviews/crossover_contract_20260913/；精确下一步本地定位该水库行和双向流残差，在固定Cross0下验证修复，再评估全国诊断。


## 2026-09-13 追加：1e-4用户选择和剩余问题

- 2026-09-13 用户明确选定BarConvTol=1e-4：诊断入口和新包均更新为1e-4/Crossover0/SolutionTarget1/Threads44；NF2/Scale2/Presolve2、FeasTol=OptTol1e-6、Slurm64CPU/700G/无SoftMemLimit保持。
  修复诊断遗漏：复用save_numeric_snapshot不依赖SolCount分块查询/保存BarX/X/BarPi/Pi等；城市QC失败后仍独立执行小时水库QC，严格阈值不变，不自动Stage B或接受结果。
  8项启动/保存测试PASS、实际参数回读、dry-run和本地bash -n通过；科学配置身份不变，未新增模型变量/约束或修改输入。未重复求解24h，复用上轮同MPS的Cross0/1e-4真实冷解。
  独立量级复核：最大水量残差1313.795m3在高凤山HydroCHN_01080/库索引471/气象小时3961；折算176.025kWh。620×24h中20站时>1m3，全部绝对残差折算310.895kWh，非实际损失或全年上界。
  跨省反向重叠1.571604GWh/24h，最大42.1258MW、额外损耗37.115MWh；59项小时硬QC中57项PASS，水库平衡/跨省方向失败，城市QC另失败。目标相对Cross2差0.0033988%。不能把这些小样本QC失败等同于旧NUMERIC崩溃，也不能宣布全年已健康。
  高凤山源调节库容3354.936947GL仍为估算来源待核实，duplicate_comid/工程字段需核对；本轮未找到足以直接替换的可靠工程值，未猜测修数据。
  新本地包tolerance_1e4_readiness_20260913/cloud_gate_20260913_v9_t44_cross0_tol1e4.tar.gz，197文件/663247bytes/SHAd47f050c79a6e3c73d4216a80a3cbe0d8f168b62e630343ffdeb4905f9e2a6a2；未上传/提交，未连接或修改服务器/Thermal。
  保留900s optimize/2h总墙钟早期诊断预算；历史44线程排序4155.5s更长，可能未到Barrier即截止，不能用这种TIME_LIMIT判定数值失败。要验证迭代须先安排覆盖排序的有限预算。
  Git0a03cc452e95d158f36923ceb5210267979b6234未提交；改scripts/probe_full_year_numerics.py、tests/test_full_year_numeric_probe.py及四文档。报告/命令/参数/残差表/原始审计引用/快照/差异/哈希在supplementary_materials/reviews/tolerance_1e4_readiness_20260913/。
  下一步固定用户选定1e-4/Cross0，优先核实高凤山异常库容及无Cross残差，在原单位下验证修复；全国8760未验收，不因这次参数更改直接启动多日生产任务。


## 2026-09-13 20:55 参数对照与全年完成时间判断

- 2026-09-13 20:55 9–10天可求解性判断与Thermal参数核对：当前尚无修复版全国8760构建/预处理/Barrier和峰值内存验收，不能承诺9–10天稳定完成。
  实际solver主差异为当前NumericFocus2、Thermal1；两者BarConvTol1e-4/Method2/Crossover0/SolutionTarget1/Threads44/Presolve2/Scale2/FeasTol=OptTol1e-6一致，Slurm均64CPU/700G/无SoftMemLimit。
  当前900s optimize/2h作业是早期诊断设置，不能直接用作多日启动；Thermal无限时，实际Presolve17794.52s约4.94h。本轮未变更预算、模型或参数。
  模型层仍不同：当前去掉年度行8192缩放、采用水库/CF/小容量等修复、城市正则1CNY/MWh及2030DAC关闭；Thermal启用8192、旧输入/0.001CNY/MWh正则、热响应及DAC，不能当同LP速度对照。
  20:54:34只读Slurm：4533060 RUNNING/6-00:44:22，64CPU/700G/billing64。20:55:28读取日志末iter483，P1.59165741e9、D-5.38091980e9、PInf21.5、DInf1.41e-4、Compl89.6，solver518073s。
  项目诊断abs(P-D)/max(1,abs(P),abs(D))当前129.58%、历史最小97.57%；不是MIPGap，不据此预测再3–4天收敛，也未判定作业终态失败。
  当前建议固定1e-4/Cross0/44/NF2，优先核实异常水库输入并在完整8760首12–24h观察收敛/内存；首日检查也不是截止保证。局部0.311MWh残差不应成为无条件收紧容差的理由，但QC记录不篡改。
  本轮只读服务器、写对照报告及更新四文档，无求解/测试重跑，无提交/停止/重启/改参/自动监控。Git0a03cc452e95d158f36923ceb5210267979b6234未提交。
  报告/参数CSV-JSON/服务器有效配置/日志摘要及哈希：supplementary_materials/reviews/solve_feasibility_vs_thermal_20260913/。下一步以实际全年首日数据评估目标，而非给无依据9–10天ETA。


## 2026-10-12 Base2060启动前停止（未提交）

- 2026-10-12 Base2060启动前D2停止：按全部模型new_build/GW资产跨cohort合计<1MW拟删1.136306309440GW>1GW；gasccs删除占2050装机0.7218187%、wave100%，均>0.1%。未删状态/改模型/构建/求解/创建release/提交held作业。三年51小文件源SHA、48manifest成员核验通过，尚未正式验收；旧双向流重叠比例判据按本日AGENTS被额外损耗/负荷替代，历史记录保留。t550转发重试已恢复，可用1.481TB，备份后空间估算36.36%，但D2停止故未备份。详见base_2060_launch_20261012/REVIEW_ZH.md；下一步作者明确清理豁免/阈值与总量口径后重审，不把单独放行当现存Job释放。

- 只读复现及逐文件SHA：supplementary_materials/reviews/base_2060_launch_20261012/REVIEW_ZH.md。held Job不存在；未备份、部署或改写任何冻结release。固定机转发命令：ssh -o BatchMode=yes -o HostName=127.0.0.1 -o BindAddress=127.0.0.1 national-model-server。


## 2026-10-12 T550云端直连准备：待公钥登记

- 2026-10-12 T550云端直连准备：用户本轮明确授权在t550生成专用备份密钥并由其登记平台公钥，覆盖原任务不创建密钥的限制，仅限此用途。t550可解析云端真实域名并收到SSH-2.0-ParaCloud；新专用Ed25519身份及独立ssh_config已创建，私钥留t550/600权限、未读取或复制内容。严格主机验证通过，当前Permission denied(publickey)待用户登记公钥；尚未完成直连认证/文件备份，2060 D2停止不变。入口与公钥指纹见SERVER_RUNBOOK本日新增条目。

- 专用配置：/home/zz2/.ssh/paracloud_backup_20261012/ssh_config；公钥：同目录id_ed25519.pub；指纹SHA256:rfM+Ce+DJQVYFkZkxMAaROxcS1ZSWqvieAAVZkIs2NY。私钥留服务器且权限600，不读取/复制内容。
- 连接命令（在T550执行）：ssh -F /home/zz2/.ssh/paracloud_backup_20261012/ssh_config paracloud-backup hostname。真实域名ssh.cn-zhongwei-1.paracloud.com、用户a8s001819@BSCC-A8、22端口；BatchMode/IdentitiesOnly/严格主机验证已配置。用户登记公钥前认证被拒，不能标记为直连备份已完成。


## 2026-10-12 T550直连备份启动，尚未完成

- 2026-10-12英国16:24 T550直连云端备份已启动：用户登记专用公钥后hostname验证到ln301.para.bscc；单次串行rsync PID4080225，三年262文件/15957710678bytes，T1→T2→T3全部纳入，预计磁盘可用仍36.3589%。目标/home/zz2/National_model_server/cloud_backup/<release>/；启动不等于完成，需各层SHA及最终backup_manifest。2060清理/提交按用户本轮明确要求暂停，未恢复。详见cloud_backup_20261012/REVIEW_ZH.md。

只读状态命令：python supplementary_materials/reviews/cloud_backup_20261012/collect_status.py。三份最终backup_manifest尚待生成，未修改云端输出或启动2060。


## 2026-10-12 Base2060第6b节续办：A/B落地，改造关联下界停止

- 2026-10-12英国16:56 Base2060第6b节重审通过但新构建停止：发电/储能删0.638135708256GW、网络删0.498170601184GW，全部适用比例门禁通过；三年relative_v1离线验收PASS（正式JSON本地完成，T550旁置assessment完成，正式JSON同步待连接恢复）。清理派生状态42971条、34条负new_build置零、94条VRE bound-close；2060 1h build-only发现内蒙古bio/黑龙江coal/海南coal/西藏gas继承下界合计-0.439794MW，原状态无负下界，因删除new_build而保留retrofit_out。已停止，未求解、未部署/创建release/提交held；需作者明确四组共0.801002MW新建cohort的改造关联豁免或成对回退规则。备份未重复启动，最后成功快照15:34UTC三年T1/T2均VERIFIED、2030T3约54%；后续本机→T550握手超时，最新进度未知。详见base_2060_launch_20261012/REVIEW_ZH.md新增第6b节停止记录。

Git基准a4f039762392afdf55acb8476b412ec339100238；本条与代码/证据同次提交。新增relative_acceptance与离线CLI、异常隔离、边界/配置测试、v9_a12与2060 profile、独立6b清理/状态准备/1h审计/只读诊断工具。历史严格QC/status/hard_checks和candidate未被科学晋级，原归档/状态保留；派生状态标记仅作失败门禁证据。完整命令、SHA、原427项及最终回归日志位置见报告。D3完整矩阵审计、D4身份/白名单/24h与E部署提交未完成，不能填PASS。当前精确下一步：作者裁定改造关联规则后重生成新派生状态、重跑门禁；另在连接可用时同步正式验收sidecar、只读核对备份manifest，不重复传输。保留其他SI会话23行handoff及稿件改动，不碰modules或在线LaTeX。


## 2026-10-12 Base2060第6c节：改造关联保护及共享生物质上限停止

- 2026-10-12英国17:36 Base2060第6c节执行后安全网停止：按存在2060存续retrofit_out记录的一般规则保护105个候选删除组，全部new_build共7.311997892MW（2060存续6.873160798MW，含原负下界四组存续0.801002010MW）；发电/储能删0.630823710364GW、网络删0.498170601184GW，6b门禁全PASS。新状态upstream_2050_prepared_6c_v2/共43286cohort，原状态和旧6b派生不变、retrofit记录逐字相同。原四组负下界消除，但上海bio+bioccs共享容量上限超17.202603W（原guard1W）：受保护bio新建17.203W保留、bioccs负尾差-16.996W被6b删除。按6c第3条停止，未optimize/完整D3/D4/部署/held提交；需作者明确共享上限bound-close与关联new_build保护的关系。备份未重启；本机→T550仍banner超时，最新进度未知、正式验收JSON同步PENDING_CONNECTION，旧快照T1/T2均VERIFIED。详见base_2060_launch_20261012/REVIEW_ZH.md新增6c节。

Git基准3ad53ed29c30231d81cd7d5bf954b47fb6e386a1；本条与修改/证据同次提交。改audit_cleanup_6b.py（显式6c开关）、prepare_state_6b.py（新目录及未改CSV字段逐字保留），新增audit_state_6c.py、fetch_2050_identity.py、两项保护规则测试；生产模型/QC/配置SHA与上次429项完整测试相同，新增2项与原relative_v1 10项测试通过。独立字段验证128处变化仅34负值置零+94VRE bound-close，retrofit逐字不变。D1补齐5改造对上界与容量族检查；2050冻结源码/原上游206文件只读SHA已取回，但未完成模型身份比较/24h或创建新release。停止证据revision_6c_v2/capacity_accounting_stop.json、biomass_shared_bound_cohorts.csv与validation_summary.json；cohort SHA1ac6b93cf4792e15100cd054295b45dcea705bfd80f63425240e0d294d87eb72。下一步作者明确仅从非CCS bio新建量扣除共享上界微小超量是否可覆盖6c保护；本轮未执行建议。网络恢复后核验备份并同步验收JSON，不重复传输；其他会话SI改动32行handoff及稿件保持未暂存。


## 2026-10-12 上海授权收口完成；广东PHS极小余量停止

- 2026-10-12 上海共享上限按用户授权完成：仅两条非CCS bio正新建合计17.202602860W扣除，CCS/retrofit及其余字段逐字不变。新状态upstream_2050_prepared_6d/（cohort SHA3c088ed70c463c0b6f03a9ae2f386a495fe810a9731ec2c6ce4982be8510a3af），6b总量/比例PASS。完整2060 1h构建发现广东PHS容量/新建各一条5.488784637kW极小区间，触发任务书D2规则外极小GW容量界停止；未optimize/D4/release/held提交。需作者授权PHS余量收口，建议继承不变、有效上界收至下界、新建上界归零并审计。T550原自主备份COMPLETE：262文件15,957,710,678bytes、9层SHA VERIFIED，三份manifest与计划逐项一致；三年正式验收JSON已同步且远端SHA VERIFIED，未重复传输。详细报告base_2060_launch_20261012/REVIEW_ZH.md及revision_6d/storage_capacity_stop.json。

Git基准fb68d3ddd449f27fc721589973d82b0650effc8a；本条与准备器显式上海开关、只读诊断和小证据同次提交。生产模型/配置无修改，实数据两处字段差异核验与1h完整构建完成；原429项回归记录仍适用。下一步取得PHS授权后在新目录复核D3/D4再执行E的hold提交，不能释放不存在的作业。SI会话32行handoff和稿件保持未暂存。


## 2026-10-12 第6d节容量/RHS清理与D3/D4验收

- 2026-10-12 第6d节实现及D3/D4通过：显式other_capacity_headroom_zero_gw_gwh=1e-5、capacity_cancellation_rhs_zero=1e-12，旧V9关闭。实际广东PHS两UB收口5.489kW、山西gchp退役相消RHS2.22e-16归零；全审计白名单181UB+1RHS通过，矩阵/LB/目标不变。2060 1h80104行238529列452584nnz、与同条件2050增幅0，2050当前/冻结MPS各段SHA相同。24h102轮OPTIMAL/relative_v1 PASS/保全COMPLETE；436测试通过跳过1。准备新20261012_base2060_v9a12_t48_m750_tol1e4_v1，只准hold，尚未宣称提交；备份262文件9层SHA与三份验收JSON同步均完成。详见base_2060_launch_20261012/REVIEW_ZH.md及revision_6d_general/final_gates.json。

Git基准0f58a6ce0219e67fa352560d2f485acf6c193cdb；模型/config/data证据读取/审计白名单/测试及AGENTS作者修订同次提交。命令及输入/状态/测试SHA见上述报告，原始潜力与继承容量不改。下一步冻结已提交源码、云端新overlay补原始退役表、preflight通过后sbatch --hold并核对ReqTRES，停等放行。保留SI会话32行handoff和稿件改动。


## 2026-10-12 Base2060 held提交检查点与验收同步更正

- 2026-10-12英国18:09:31（云端北京时间10月13日01:09:31）Base2060已按授权held提交：Job5124127，PENDING/JobHeldUser/Priority0，ReqTRES cpu64,mem750G,node1,billing64，UNLIMITED/Requeue0，未释放。新release20261012_base2060_v9a12_t48_m750_tol1e4_v1冻结源码680a5c428ac5bd95378dd4eb0b20c8a4f44a01c0，371源码/50输入SHA通过，release清单SHA41a77a156b85afc2fb8dfa167baebb5127ef7fee2098f86960d378c2827331e9；云端合同/preflight_v2 PASS，D3/D4/436测试通过。备份262文件9层SHA完成。验收JSON此前仅LF规范化文本一致（Windows CRLF与服务器LF字节SHA不同），本轮保留原件并另存source_bytes精确副本，三年逐字节SHA现均VERIFIED_BYTES_WITH_CANONICAL_LF；科学内容无差异。停止于held检查点，只有用户明确回复放行后才可release，节点可用内存>=700GiB检查已写batch。

运行命令：deploy_2060.py prepare、preflight、submit、collect。首次preflight因本地部署助手覆盖PYTHONPATH而漏掉既有云端xarray依赖，合同本身PASS；修正为保留环境PYTHONPATH，在新preflight_v2目录通过，无依赖安装/模型改动。冻结batch原本正确保留PYTHONPATH，不改冻结包。held收据/冻结身份/实际求解器参数见revision_6d_general/held_submission.json、cloud_source_repo_sha256.json、continuation_contract_check.json、cloud_preflight.json。release源提交680a5c4；后续提交仅同步收据、操作助手修复和文档，不替换冻结源码。下一步停等作者放行，严禁自动release、Stage B、case3或后台监听。保留其他SI会话32行handoff及稿件。


## 2026-10-12 Base2060获作者放行并启动

- 2026-10-12英国18:17:06（北京10月13日01:17:06）Base2060 Job5124127已按用户“放行，启动这个任务吧”释放并在m4cm2108运行；实际AllocTRES cpu64,mem750G,node1,billing64，UNLIMITED/Requeue0。启动可用内存724.571716GiB>=700，Gurobi13.0.2/节点smoke PASS，7项启动回归PASS。冻结清单SHA41a77a156b85afc2fb8dfa167baebb5127ef7fee2098f86960d378c2827331e9再次全部核验，冻结源码680a5c4不变，未重复提交。17:17:45UTC时全年runner已创建output_8760身份/输入/preflight文件、stderr为空，尚未取得全年结果。备份262文件/9层SHA完成，三年验收JSON source_bytes逐字节同步已核验；未重启传输。证据revision_6d_general/release_job.json及startup_verified.json。后续只读查构建/Barrier进展与终态，禁止原地修改冻结包；无自动监听。

Git操作基准eb7d91202bb4b53ef551d210c4ee25b73001f161；生产冻结源680a5c428ac5bd95378dd4eb0b20c8a4f44a01c0。本次仅新增release_job.json、startup_verified.json和CODEX_HANDOFF.md、MODEL_SERVER_STATUS.md、SERVER_RUNBOOK.md、base_2060_launch_20261012/REVIEW_ZH.md交接记录，不更改模型、数据、运行脚本或参数。释放前scontrol show job -o 5124127验证JobHeldUser/资源/WorkDir/Command，sha256sum --quiet -c release_files.sha256及合同、preflight_v2均通过，再执行一次scontrol release 5124127。远端release_job.json先以排他创建记录attempt，成功回执returncode=0；未再次sbatch。

运行证据：18:17:45英国时间RUNNING/39秒、实际分配符合合同，compute_node_smoke.json记录724.5717163085938GiB；startup_regression.log记录7项/4.287s/OK，含小fixture一次numpy.ndarray size changed RuntimeWarning，测试通过，生产stderr当时为空。stdout当时187bytes，output_8760已生成run_identity/input_manifest/preflight等7文件，无batch_exit.json；这是启动通过，不表示全年构建或科学求解已经完成。后续可用ssh paracloud-bscc-a8只读scontrol和冻结目录日志，具体路径见启动收据。下一步等待云端自主运行，在后续用户查进度时读取构建/Barrier/终态及保全QC，不建立后台轮询。备份与验收JSON沿用已核验完成状态，保留原LF归档及source_bytes副本。另一个SI会话32行handoff及稿件改动保留且不纳入本次提交。


## 2026-10-12英国22:26 Base2060全年构建完成、预处理中

- 2026-10-12英国22:26（北京10月13日05:26）Base2060/5124127 RUNNING/m4cm2108，运行4:09:35。全年构建18:55英国完成（约37分48秒），19:03:55进入求解；50,907,233行/41,458,383列/485,386,301非零元，指纹0x0475f775。当前Presolve约12,185秒，已删14,753,636行/8,362,781列，尚无Barrier迭代；日志每约5秒更新，无求解器Warning/Error，stderr空。sstat RSS87.17GiB、峰103.28GiB；48求解线程，750G分配不变。证据revision_6d_general/progress_20261012T212638Z*.json；无可靠完成百分比/ETA，后续只读观察预处理结束与Barrier启动。

Git基准a3cb6ed7172f9a31d52410ded9e8f90b5a8a9d98；本轮只读scontrol show job -o 5124127、sstat -j 5124127.batch及stdout/stderr、gurobi.log、build_report/solver_telemetry。新增两份进度JSON并更新本交接、MODEL_SERVER_STATUS和SERVER_RUNBOOK；没有更改冻结源码/参数、作业或触发新求解。矩阵范围[3e-5,6250]，最小非零RHS4.9772845e-8。预处理计数在所读尾段保持不变，日志继续更新时间；这不能当作完成比例，也不足以判断卡死。尚无全年解及终态QC；按作者最新第6条，后续任何QC标签均不得阻止完整解数据保全。备份和三年验收JSON同步沿用此前完成记录，未重复传输。下一步用户查询时只读核对预处理/Barrier/终态及保全，禁止原地更新运行包或建立自动监听。保留作者AGENTS修改和另一SI会话全部未提交内容。


## 2026-10-12 夜间 case3 柔性数值实验：P已启动，T550连接阻塞

- 共识以 `RESEARCH_DESIGN_CONSENSUS_20261012.md` 全文及 `AGENTS.md` 本日两节为准；情景Base/A/B/C、R0/R1、relative_v1扩展、证书两用途和比较区间已同步为文档追加更正。所有QC只是标签，任何解/状态/日志一律保全。
- 实现提交 `aef0cb7`，本机P0–P5串行PID44524，P0 OPTIMAL/94轮但M=7.220764389091675GWh；已复现历史失败，不据此改生产。1h smoke v3保全COMPLETE/errors=[]（严格QC HARD_FAIL），候选状态仍完整导出。入口/输出/SHA见 `supplementary_materials/reviews/case3_flex_numerics_20261012/REVIEW_ZH.md`。
- T550资源初查96逻辑核/可用约51.09GiB，其他用户预测训练占主要内存、未见CISPO求解器。89.35MB实验包传输后连接失效，127.0.0.1:22握手/直接地址均超时；无部署和F启动回执，**F未启动**。部分传输保留、不覆盖；排程准备F1/F2/F3/F4、条件F6、最后F5，16线程串行/保留15GiB。制冷/供暖数据选窗8月5088/12月8016。
- 只读squeue确认Base2060/5124127 RUNNING/m4cm2108（运行4:17:44），未控制作业。Base2030–2050正式验收与262文件/15.96GB/9层SHA备份沿用共识和既有核验证据，本轮不接触cloud_backup。
- 待办：恢复T550连接，核验新包与输入SHA并启动F；P/F齐备后按任务书第4节形成三情形结论及H1/H2/H3机制报告。case3全年仍待夜间结论、生产代码和作者确认；本轮无云端提交、release/模型/生产profile修改。Git同步仅明确清单，SI既有未提交内容保留。


## 2026-10-12 T550连接恢复、F队列启动（更正前述阻塞状态）

作者恢复连接后，远端原包89345689bytes与本地SHA `e134e5239a1baaf25493fe8897676185f9645e7f5118decfa81d25c26f20f040` 完全一致；因此未重复传输、不删除或覆盖该包。新根 `/home/zz2/National_model_server/probe_outputs/case3_flex_numerics_20261012_aef0cb7` 安装281文件逐项SHA PASS，冻结求解源码 `aef0cb7ece951154d2c1bbc70f32d2ac5614b7ff`。安装器提交 `2a940e6`；运行Python为 `/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python`，Gurobi13.0.2。旧历史路径 `/home/zz2/.local/envs/cispo-2030/bin/python` 不存在，未改环境或许可证。

flock启动器PID491302，F1求解进程PID491311（已只读实查CPU/RSS），启动可用约60.17GiB；16线程串行，现有 `run_control/numerical_validation_solver.lock` 控制本实验独占求解器。F1/F2/F3/F4，若F1/F2残差失败则插入F6，F5最后单独执行。每次资源门禁与2秒RSS日志保存；105GiB可用条件未满足时F5等待、不挤占其他用户训练。此时只确认F1开始加载/构建，未宣称求解完成。

P0和P1的原模型归档、BarX/BarPi/X/Pi/RC/Slack快照全部COMPLETE，参数回读逐项匹配；P1的完整M=0.0008026169445524904GWh，低于本任务1MWh门槛，旧严格标签仍保留。本机P2继续运行。完整结论待F1/F2/F5及F4时长序列、必要F6齐备。未改变Base2060/备份/生产源码或profile，未提交云端作业。证据 `T550_install_launch.log`、远端 `install_validation.json`/`launch_receipt.json`/`queue_active.json`。


## 2026-10-13英国11:23 Base2060进入Barrier，第33轮

- 2026-10-13英国11:23（北京18:23）Base2060/5124127 RUNNING/m4cm2108，累计17:06:45，已进入Barrier并完成iter33（最新日志英国11:20:29）。Presolve16365.14s、ordering4366.95s；预处理后36,153,597行/33,095,602列/387,670,134nnz。近10轮20.1233分钟/轮，打印PInf1.03e10/DInf44.7/Compl1.23e9，较iter23分别下降74.75%/82.47%/75.55%，仍为早期迭代，不能作完成百分比或外推ETA。Slurm RSS401.18GiB/峰657.34GiB，48线程；无求解器Warning/Error，stderr空，无终态。证据revision_6d_general/progress_20261013T102349Z.json及_summary.json；继续云端自主运行，下一步只读观察收敛/终态与完整保全。

Git基准33fece1b2f324c7bf1b209ff53019223a677e2d7，冻结源码680a5c4和生产profile保持不变。只读命令scontrol show job -o 5124127、sstat -j 5124127.batch，以及gurobi.log/stdout/stderr/solver_telemetry尾段；两份JSON为原始取证和派生统计。打印残差与callback残差定义不同，不当作物理GW/GWh QC；Gurobi内部记录峰值805.854GB，与Slurm采样RSS峰值不是同一统计口径，不能据其中一项判定OOM。没有新警告/错误/退出文件，未宣布可行或最优。近10轮残差持续下降，但不据早期斜率推算结束时间。仅更新交接、SERVER_RUNBOOK、MODEL_SERVER_STATUS和小证据，保留并行SI的32行handoff等工作区内容；未改作业、冻结文件、case3实验或监听设置。后续无论QC标签如何均须保全全部解数据；本次未产生终态解。


## 2026-10-13 11:23 英国时间：夜间P终态、F1–F4终态与第3情形触发

P0–P5全部完成并保全；P5 Status13/SUBOPTIMAL，M=0.08561165888831365GWh，供暖库存下界省31/hour3533，制冷下界0.003340447357447994GWh。P3/P4关闭聚合/预求解的M为1.911544e-10/1.491750e-10，支持H1；收紧容差P2未改善，H3仍受8760/744h差异限制。

T550原实验根case3_flex_numerics_20261012_aef0cb7的F1–F4均OPTIMAL/保全COMPLETE；F1/F2/F4的M为3.8252378095e-5/2.4034940833e-5/1.4707773297e-8GWh。F4→F1增长2600.827倍，按任务书第4节第3情形停止给出全年启动建议、交作者判断，虽绝对值均低于1MWh也不自行改门槛。F5尚未启动：当前资源门禁63.625GiB<105GiB；F6未触发。F5缺失不是数值失败，queue_active的F4 PID为历史遗留。原服务器有限队列仍等待，未发任何进程控制命令；应用内case3续办已暂停，需作者决定后续F5/资源/诊断安排。

79份远端小证据SHA PASS，收集目录 `supplementary_materials/reviews/case3_flex_numerics_20261012/evidence_20261013T1023Z/`；完整10行运行表与残差剖面在同级summary_20261013T1023Z，详细局限见REVIEW_ZH.md。本轮源码基线80090ae，修改只读汇总脚本与追加文档/证据；不改模型/配置/冻结包，不碰云端作业或cloud_backup、不读凭据。下一步作者审阅增长门槛触发和F5资源安排；没有生产启动建议。后续一次SSH握手超时，最新服务器状态以已核验快照时间为准。


## 2026-10-13英国16:42 Base2060第49轮收敛取证

- 2026-10-13英国16:42（北京23:42）Base2060/5124127 RUNNING/m4cm2108、累计22:25:53；最新iter49完成于英国16:40:07，较前次iter33推进16轮。打印PInf1.29e9/DInf3.26/Compl1.55e8，33至49三项逐轮下降，分别降87.48%/92.71%/87.40%；原始-对偶目标差4.737588348e13，降52.01%。近10轮20.03分钟/轮；RSS401.89GiB/峰657.34GiB，无求解器警告/错误、stderr空，无终态。仍远未收敛，无可靠ETA。证据revision_6d_general/progress_20261013T154257Z.json及_summary.json；只读观察后续收敛与终态完整保全。

Git基准c19190ff16b182bf6e40d74efb9419d5c100b044。只读scontrol、sstat、gurobi.log/solver_telemetry及stderr；迭代0至49日志已提取，派生JSON核对33→49降幅及39→49耗时。打印指标与callback定义不同，不把求解器残差当物理GW/GWh验收；近16轮无反弹，最近数轮下降加快，但目标差和残差仍大，不预测完成时间。仅新增两份证据并更新交接/服务器状态/runbook，冻结源680a5c4和运行参数不动；不改并行case3实验或SI内容。下一步按用户查询只读取证；终态无论QC标签均完整保全解与归档。


## 2026-10-13 16:44 F5内存门槛复核（只读，未降门槛）

105GiB是aef0cb7排程脚本写死常数；扣除15GiB保留意味着90GiB工作预算，但原记录没有90的计算公式或F5实测支持。本次纠正“门槛即已证实需求”的潜在误读。F1/F4全流程RSS峰20.144886/3.775208GiB；F5按小时线性、两点RSS幂律、Factor NZ增长代理三种外推分别54.586/61.847/64.603GiB，加15GiB保留为69.586/76.847/79.603GiB。这些是情形估算，不是置信区间或安全上界。

最新三次MemAvailable82.11–82.46GiB，较早63.625GiB改善；但相对64.603+15只有约2.51GiB缓冲。历史F3的MemAvailable+本实验RSS代理波动约24.43GiB；现有optimize回调保护不覆盖构建/归档/导出、SoftMemLimit=Infinity，不能据此证明原脚本降门槛后即可安全完成。结论是静态容量有可能，但尚未证明安全；建议作者决定后在新独立诊断目录做完整保护下的2016h规模/分解预检。本轮未改105GiB门槛、排程、冻结代码或参数，F5未启动。

证据与可复算公式：`supplementary_materials/reviews/case3_flex_numerics_20261012/memory_review_20261013T1542Z/MEMORY_REVIEW_ZH.md`及同目录两份JSON。只读远端原实验目录的内存日志、系统资源统计与queue_gate；未查询或操作云端作业/备份、未读取凭据。Git基准c19190f；本次仅追加文档和小证据。


## 2026-10-13 16:52 作者授权直接启动F5

作者在内存复核后明确要求“直接启动”。已逐项核对原协调器491304的完整命令、用户身份、F5门禁和无子求解器状态，短暂挂起后二次确认无F5/子进程，再终止这个等待进程并释放原flock锁，避免稍后重复启动；没有停止任何在求解的模型或其他用户任务。旧运行记录全部保留，原冻结源码和105GiB常数未改写。

新独立目录 `/home/zz2/National_model_server/probe_outputs/case3_flex_F5_direct_20261013_3e4a2fe`；一次性控制器源码提交3e4a2fe，SHA6639a8ba05ff8be81c7f82324b9bc212f002dff2096266e7e216a47c9cacce20。复用原aef0cb7求解源码与数据bundle，281文件逐项SHA PASS。F5命令参数hours2016/start5088/threads16/case3_thermal_ev_v5/Aggregate1/Presolve2/reserve15，V9及其余数值与F1相同。本次仅按作者授权绕过105GiB排程门槛，启动可用约83.94GiB，不宣称这是安全上界。

flock2312130、控制器2312131、求解进程2312139，16:53只读核验求解进程CPU98.4%、RSS约0.77GiB，处于加载/构建；日志持续写入，没有终态。所有输出进入新根F5，F5_memory.jsonl逐2秒记录全流程RSS。保留原optimize回调的15GiB检查；它不是构建/归档/导出阶段的硬内存上限，未隐瞒此前已说明的局限。

接管、启动回执与确切命令在本地 `F5_direct_launch_20261013/`；原F1–F4目录不变。应用内case3有限续办已恢复并改为仅跟进这一新F5，状态不变保持安静。下一步等F5终态后补齐运行表、残差剖面与全部时长增长比；已记录的第3情形不自行放宽，也不阻止作者授权的补充诊断。没有云端操作、生产配置修改、凭据读取或结果删除。


## 2026-10-13 17:17 英国时间：第5b节追加F7/F8等待F5（独立诊断）

F5原PID2312139继续运行，16:16:24 UTC仍在预求解、RSS21.38GiB，未干预。依据作者新授权，在同根 `/home/zz2/National_model_server/probe_outputs/case3_flex_F5_direct_20261013_3e4a2fe` 排好F7/F8有限串行队列；控制器PID2340523，16:12:23 UTC启动，诊断源码f053057放入新子目录extension_source_f053057，原281文件SHA通过、仅三个诊断脚本叠加，F5在用冻结源不变。

F7 Aggregate0/F8 AggFill0，均F1同窗744h/start5088/16线程/V9/case3 2030。队列等待F5_terminal及原求解锁释放；逐项可用内存≥60GiB（45+15工程预算，并非内存上界）、无其他识别到的求解器才启动。全流程RSS采样、原15GiB仅optimize期间回调保护；准入最多24小时，资源中止后停队列，不停止其他用户。extension_gate/started/dispatch及源码清单四份证据SHA逐字核验保存在本地extension_5b_20261013/server_evidence/。F7/F8尚未运行，不能把排定误报为完成。

判定更正于F5终态前17:09:42英国时间登记并提交d83be1e：F4→F1增长不再否决；外推仅F5 M≤1e-3且F5/F1<3。旧判断保留。追加本机P6/P7/P5a/P5b/P5c/P8串行PID16312，最终按5b(a)(b)(c)选择首个合格production/AggFill0/Aggregate0供作者确认。既有应用内有限回查更新继续。本条未核验或操作Base2060/云端/备份，不修改其既有记录。详见case3_flex_numerics_20261012/REVIEW_ZH.md本日追加节。


## 2026-10-13 17:21 本机P6补充结果

P6（2040隔离块）已保全：Status13、68轮、422.040秒，完整M=0.05617986345229854GWh（供暖库存下界），P7自动继续。两份保全manifest均COMPLETE，11行汇总summary_5b_P6_20261013。T550 F5及F7/F8排程未作任何变更；本条不代表新增服务器终态。


## 2026-10-13 17:54 英国时间：F5进入Barrier，P系列补救项取得终态

只读核验F5 PID2312139仍运行，16:54:18UTC已打印iter1；presolved9370703行/8612547列/97391084nnz、FactorNZ5.632e9。全流程RSS采样峰64.951183GiB、最低MemAvailable18.046539GiB；当前RSS约46.09GiB/可用36.24GiB，无F5_terminal。F7/F8控制器2340523仍等待原F5终态与锁，60GiB准入和15GiB回调不变，未干预任何求解。

本机新增P7 Status13/M0.07102013187681203GWh；P5a Aggregate0和P5b AggFill0均Status2，M分别1.6950964778421167e-9/2.7500133394919857e-6GWh，均完整保全。P5c运行，P8排队。Aggregate0已通过隔离块条件(a)，全模型(b)(c)仍待F7；AggFill0待P8/F8。阶段证据progress_5b_20261013T1653Z及14行summary_5b_20261013T1653Z，报告只追加，不作生产配置建议。此条未操作或核验云端/备份，其他既有记录不变。


## 2026-10-13 18:25 英国时间：本机P追加队列完成，T550继续F5

本机追加六项全部结束、两类保全manifest及参数核验全通过。P5c/P8均OPTIMAL，M分别1.430724e-9/1.115778e-7GWh；AggFill0与Aggregate0均通过5b(a)，仍待全模型(b)(c)。16行汇总summary_P_complete_20261013T1724Z。17:25:03UTC只读确认F5仍运行、iter5、无终态，峰RSS64.951183GiB/最低可用16.080601GiB、当时可用16.676289GiB；15GiB回调和F7/F8的60GiB准入保持不变，追加协调器仍等待F5终态/锁。未干预任何求解，未触碰云端/备份/凭据。证据P_complete_20261013T1724Z/server_observation.json。


## 2026-10-13 19:25 英国时间：F5资源中断，F7接续运行

F5原控制器/求解进程已退出：Status11/SolCount0/10轮/Runtime6250.024秒、全流程7690.954秒。既有15GiB回调在MemAvailable14.806969GiB时触发resource_stop；不是人工干预或数值失败，不能提供F5外推M。模型archive、数值snapshot、语义preservation均COMPLETE/errors=[]，六种可用向量和候选状态等全部保全；17份小证据逐字SHA核验至F5_interrupted_20261013T1825Z，10个大文件存在/长度与manifest一致（本轮未重算全部大文件SHA）。QC HARD_FAIL仅标签，数据未删。

F7已由既有队列于18:01:07UTC自动接续，PID2507652/控制器2340523；准入76.273GiB、无其他识别求解器、F5终态与锁均满足，仍为60GiB准入/15GiB回调。744h/start5088/16线程/Aggregate0/独立f053057源；18:24:41UTCiter11，FactorNZ8.294e8比F1增3.804756%，终态残差/轮数/耗时待定。F8继续排队，本轮无新启动命令或参数调整。不自动重跑F5，不触碰生产/冻结源/云端/备份/凭据；有限跟进继续已授权F7/F8，最终如需F5补验交作者决定。


## 2026-10-13 21:54 英国时间：F7完成，F8自动接续

F7于20:39:40UTC完成并全保全，Status2/SolCount1、150轮、Runtime8946.851秒、全流程9512.473秒、峰RSS20.057224GiB；M1.0928808209537816e-8GWh，FactorNZ8.294e8。相较F1轮数不变、耗时+27.775654%、FactorNZ+3.804756%，结合P3/P5a满足5b(a)(b)(c)。目标相对差1.07677e-5超过一般Cross0等价性1e-5，单独披露但不改5b判据，不宣称目标等价验收通过。20小证据SHA通过、archive/snapshot/preservation均COMPLETE，证据F7_complete_20261013T2054Z及18行summary_F7_complete_20261013T2054Z。

F8由原队列同刻接续，PID2791611/控制器2340523，同窗744h/start5088/16线程/Aggregate1/AggFill0；准入可用62.464191GiB>=60、无其他识别求解器，原15GiB回调不变。20:54:10UTC仍在运行，需等F8决定是否按温和优先选择AggFill0。F5保持资源中断/M未定，无重跑或降保护。未对云端/备份/凭据/生产或冻结源码作任何操作。


## 2026-10-13 22:22 英国时间：F5_retry2g 独立串行等待

作者最新授权将F5内存保护由15GiB改为2GiB。原F5已资源中断并完整归档，保留不动；在新根 `/home/zz2/National_model_server/probe_outputs/case3_flex_F5_retry2g_20261013_ed90ebc` 安排从头重跑，源码ed90ebc、冻结source_ed90ebc/repo，协调器PID2858146于21:20:40UTC启动。新源清单212项，SHA256为02ba21ea01fbdc14c25c792a6606347d0510e8d2d607054cb835430a11347a93；原281项输入/源与F7/F8的211项冻结源已核验，旧源未修改。

21:21:02UTC队列状态等待；F8 PID2791611/协调器2340523仍运行、iter48，可用约42.76GiB。F8完成并释放锁后，确认无其他识别求解器且可用≥67GiB（原F5采样峰64.951183+2向上取整）才启动2016h/start5088/16线程/Aggregate1/Presolve2，optimize回调阈值2GiB。67GiB不是峰值保证，回调不覆盖建模/归档/导出。F8原15GiB保护不变、不并跑、不终止其他用户进程。新队列读取retry_gate/active/terminal及F5_retry2g_terminal，截止2026-10-14T16:09:42Z停止等待；不重复启动，既有Base与备份记录不修改。

证据：supplementary_materials/reviews/case3_flex_numerics_20261012/F5_retry2g_20261013。下一步等待F8完整终态及新F5准入/终态，保留两次F5结果并明确区分资源中断与数值判定。


## 2026-10-13 23:00 英国时间：F8终态与F5_retry2g自动接续

原独立根case3_flex_F5_direct_20261013_3e4a2fe中的F8于22:43:52UTC完成，Status2/OPTIMAL、138轮、Runtime6883.456638秒、M1.2101824602468741e-4GWh、全流程峰RSS20.554878GiB；所有保全报告COMPLETE，原PID2791611和协调器2340523退出。FactorNZ7.964e8，较F1-0.325407%，耗时-1.692994%；AggFill0满足5b(a)(b)(c)，生产未改。

新根case3_flex_F5_retry2g_20261013_ed90ebc的唯一协调器2858146于22:44:21UTC取得锁、通过71.379GiB可用≥67GiB与无其他识别求解器门禁，自动启动F5_retry2g PID2998218。源码ed90ebc冻结，2016h/start5088/16线程/Aggregate1/Presolve2、2GiB optimize回调；22:55UTC仍运行、RSS8.043877GiB、可用64.886593GiB。未干预原F5/F8，不操作其他用户任务。

24份小证据逐字SHA核验于F8_complete_20261013T2254Z；新19行结果summary_F8_identity_corrected_20261013T2254Z，P5输入年份由旧缺失元数据的默认2030更正为原报告2060、电价2030，数值不变。下一步只读等待新F5终态与完整保全，历史结果不删除，Base和备份既有记录不改。


## 2026-10-14英国13:37 Base2060第114轮进度

- 2026-10-14英国13:37（北京20:37）Base2060/5124127 RUNNING/m4cm2108、累计1天19:20:40，最新iter114（英国13:35:36），较前次49推进65轮。打印PInf5090/DInf1.49e-5/Compl550，近10轮三项逐轮下降32.94%/37.66%/35.45%，目标差2.677767251e10下降32.25%；每轮19.65分钟。第101轮DInf曾回升13.28%，102至114已连续下降至更低值；不宣称全程单调。Slurm RSS403.20GiB/峰657.34GiB，48线程、750G不变；无求解器警告/错误、stderr空，无终态。仍未收敛，残差/目标差不能作为物理QC或完成比例。证据revision_6d_general/progress_20261014T123742Z.json及_summary.json；后续只读观察收敛与完整保全。

Git基准a6cdc1714fd71f2c3413b3352718c1bd05a917ef，冻结源码680a5c4和运行profile未改。只读scontrol、sstat、gurobi.log/solver_telemetry和stderr，提取0至114轮；最新callback时间与打印日志一致。相比第49轮，三项打印指标分别降低约25.34万倍/21.88万倍/28.18万倍，但仍无OPTIMAL或科学QC结论；不把早期大幅下降外推为结束时间。保留打印与callback两种残差定义；本轮只更新交接、MODEL_SERVER_STATUS、SERVER_RUNBOOK和两份小证据。未触碰作业、case3、SI或后台设置。下一步用户查询时读取收敛/终态，任何QC标签均完整保全所有解数据。


## 2026-10-14英国21:18 Base2060第137轮及对偶反弹

- 2026-10-14英国21:18（北京10月15日04:18）Base2060/5124127 RUNNING/m4cm2108，累计2天3:01:38，最新iter137（英国21:15:06）。PInf1320/DInf9.35e-5/Compl133，目标差7.54571972e9；较114原始/互补/目标差降74.07%/75.82%/71.82%，但对偶升至6.275倍。133–136对偶连续反弹，137回落4.00%，仍为132的18.30倍，恢复未确认。最近10轮原始/互补/目标差降43.83%/43.16%/39.25%，较前10轮48.80%/52.73%/49.16%放缓，约20.01分钟/轮。RSS403.34GiB/峰657.34GiB，无显式Warning/Error、stderr空，无终态；不得表述成全部指标持续下降。证据revision_6d_general/progress_20261014T201840Z.json及_summary.json；下一步只读观察对偶恢复与整体收敛。

Git基准92ec229d4ab2ccfbfaeb7e63efe96f267f140ae0；只读scontrol、sstat、gurobi.log、solver_telemetry和stderr。保存完整迭代行0–137、所读日志字节SHA及最新callback；逐区间104–114、114–137、117–127、127–137、132–137、117–137计算降幅/每轮耗时。最近5轮原始/互补/目标差仅降12.58%/15.82%/15.39%，对偶上升18.30倍；其余指标未同步反弹，尚不足以判定整体发散。打印残差为求解器口径，与callback和物理GW/GWh QC不同；无OPTIMAL/完整解结论，不外推结束时间。仅两份证据及交接/服务器状态/runbook入本次提交；保留作者AGENTS/研究共识和并行SI未提交内容，冻结源码680a5c4与生产配置不变。下一步只读关注对偶回落是否持续、其他残差有无同步恶化及终态完整保全，不修改运行作业。


## 2026-10-14 Base2030–2060历史收敛轨迹比较

- 2026-10-14 Base2060跨年收敛比较完成：云端四份原始gurobi.log逐字节SHA与连续迭代行核验，2030/2040/2050终轮348/605/716，solver耗时约5.224/9.765/11.532天。2060最新137轮；原始/互补水平约对应2030第85–87轮、2040第130–131轮，当前对偶明显差于这两年对应阶段。2050第116→117轮原始3720→4.40e11、互补416→5.15e11发生同步大跳，2060未见同类事件；因此同137轮2060显著优于2050当时，但不能据此保证更早结束。比较证据revision_6d_general/historical_comparison_20261014{,_summary}.json；2040为44线程、其余48，2060有v9_a12清理，不做严格同LP性能归因。

Git基准8641609c47972f373fca484bec56324eddd7a593。经现有SSH只读2030 20260914_base_v9_t48_m750_tol1e4_v3、2040 20260919_base2040_v9_t44_m750_tol1e4_v1、2050 20260930_base2050_v9_t48_m750_tol1e4_v1及2060冻结release的output_8760/gurobi.log。四年全日志SHA、选定统计与完整连续迭代行见JSON，最近一次读取2060仍137。相同轮次137的PInf/DInf/Compl：2030=48.7/1.14e-8/5.53，2040=594/1.9e-6/86.2，2050=7.32e10/3890/7.24e10，2060=1320/9.35e-5/133。相近PInf/Compl阶段2030第86轮的前10轮降83.79%/78.58%，2040第130轮降53.01%/51.16%，2060当前降43.83%/43.16%；2060近期残差下降较两者对应窗口慢。每轮约20.01分钟，与2040对应窗口20.42分钟相近；2030约18.40分钟。2040对应阶段累计solver约2.20天，2060约2.09天，因2040预处理更长，不能仅凭迭代数推断墙钟时间落后。2050的双指标最近邻是跳升前116轮，不代表跳升后恢复阶段；跳升后PInf首次达到2060当前值在219轮，Compl在265轮，不能把不同指标拼成唯一进度。跨年数值仅作求解器工程轨迹比较，不当物理QC、科学效果或完成百分比；历史总时长不作为2060倒计时。没有修改作业/冻结源码/参数/数据，无新求解。保留其他作者AGENTS/共识及SI改动。下一步只读确认2060对偶反弹是否持续恢复，终态保全不受QC标签影响。

## 2026-10-14 case3 2030 L1–L4 核准与 held 部署准备

作者最新确认所有含柔性情景仅把 Base 数值设置的 Aggregate 改为 0，旧 AggFill0 候选结论仅保留历史。新增筛选生产 profile/入口与参数核准脚本，V5 实际输入 SHA 溯源补齐，所有 QC 标签均独立保全。L2 76 项 PASS；Base 1h 全段 SHA 同冻结 2030；零签约 24h 目标相对差 1.1409671441444699e-14、柔性决策严格零；筛选只改 BOUNDS_VRE_NEW，剔除 20,272 列。case3/nocredit 24h 均 OPTIMAL，M=1.1204230761761597e-8 / 1.1769423379675084e-8，保全 COMPLETE、relative_v1 记录齐全；完整回归 440 项通过、1 项跳过。

Git 基准 2aa17ef，源码与证据随本条明确清单提交；部署后的源提交、release SHA 和 held 作业号另追加。命令/输入/输出/历史失败及修复见 `supplementary_materials/reviews/case3_2030_launch_20261014/REVIEW_ZH.md` 与 `final_gates.json`。全部原始门禁模型/向量/日志保留本地，不提交大数据；其他 SI 改动不纳入。

下一步仅冻结两个独立 2030 release，64CPU/750G/48线程、启动可用内存≥700GiB，完成云端 preflight 后 --hold 提交，汇报并等待作者“放行”。P1–P5 待运行期间继续；C2050 同样 held 后汇报。F5 不干预、不追加 F9；本轮未操作 Job5124127、旧冻结源码、T550 cloud_backup 或凭据，无后台监听/自动提交。

## 2026-10-14 英国21:52：case3 与 nocredit 2030 已 held，等待作者放行

L1–L4 PASS，冻结源码 `62bba5928f9db3c6d947e33350d5e08bd9bec01d`，两个新 release 分别为 `20261014_case3_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1`、`20261014_case3nocredit_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1`，均在 `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/` 下。385 源码/55 输入 SHA、两份云端 preflight_v2、9 项 CF/3 项水文身份核对均通过。共享源码清单 SHA `ec8fa5906eff941c60cee0b9cb905adb18500641a24e493d39e00c2003d09e7c`；release 清单 SHA 分别 `90e4f9f89cc798d1c4eebc576ea24de97dc70481eb9ed838f503e49ceae0166c`、`d7bfbe0db90fc48de9086a029cff24ee0b991711ab3d2334c5d22669c4dade1c`。

Job5153878 / Job5153901 均 PENDING/JobHeldUser；ReqTRES cpu64/mem750G/node1/billing64，UNLIMITED/Requeue0，AllocTRES=null，未 release。求解 48 线程，Base 数值仅 Aggregate=0，margin0.2；启动可用内存至少700GiB。历史峰680.804GiB，余量有限。证据 `supplementary_materials/reviews/case3_2030_launch_20261014/both_held_verified.json` 及两个 `deployment_*/`；完整核准见同目录 REVIEW_ZH.md。部署工具 preflight 参数修复与回执单独提交，冻结源保持62bba59。

下一动作：等待作者“放行”后 release 并核对实际分配与内存；运行期间完成P1–P5，C2050另经门禁后held。此轮未操作Base2060、旧冻结源码或T550诊断/备份，不恢复定时回查、不追加F9。所有运行数据完整保全。

## 2026-10-14 英国22:27：case3单独放行，nocredit继续held

用户只授权5153878。21:10:20UTC执行release，21:12:07UTC在m4cg1604启动；实际AllocTRES cpu64/mem750G/node1/billing64、UNLIMITED/Requeue0，启动可用723.2404518127441GiB>=700，Gurobi13.0.2 smoke及7项启动回归PASS，取证时生产stderr空、全年构建中。5153901仍PENDING/JobHeldUser，未获放行。冻结源62bba59保持不变，回执和核验见case3_2030_launch_20261014/release_case3_5153878.json与startup_verified.json。

本地P工具：relative_v1离线GW/GWh扩展通过；R1复现既有2050→2060 cohort SHA3c088ed7与汇总SHAf455533f；C2050的R1上游state已准备，16,446cohort，SHA1b7b068d6ed00653e2ffb23f853e98b8bfdf8c2426b8d44b2a838d396b47b246。P1两份24h定价与独立点积核验通过，但Base2030全尺寸自检仍待下载；P4脚本通过小测试，Base2040/2050清单尚未生成，C2050还未做完整门禁/held提交。450项回归PASS跳过1、补充21项针对性PASS；详见REVIEW_ZH.md与P_progress_20261014T2127Z.json。一次性Base2030归档下载正在进行，不是后台监听，不做自动提交。

本次Git基准4bcce51；仅本地离线工具/测试/报告和启动小证据提交，运行源码不变。下一步全档SHA/定价自检→2040/2050筛选→C2050门禁→held汇报；nocredit需新的作者授权。无定时回查、不触碰Base2060/F5/备份；任何QC标签均完整保全。

2026-10-14英国22:31补充：Base2030有限取证PID33028；Base2040→2050有限顺序取证当前PID45068。下载后以download_identity.json和SHA为准，禁止重复启动/覆盖partial。未建立监听、无自动提交；后续全档解析先核验本机可用内存。最终源SHA与分项状态见case3_2030_launch_20261014/P_progress_final_before_commit.json。


## 2026-10-15英国10:53 Base2060第178轮及对偶恢复

- 2026-10-15英国10:53（北京17:53）Base2060/5124127 RUNNING/m4cm2108，累计2天16:36:47，最新iter178（英国10:44:57），较137推进41轮。PInf359/DInf6.20e-6/Compl25.2；较137三项降72.80%/93.37%/81.05%，目标差降79.12%。对偶较136峰回落93.63%，163曾小反弹、164至178连续15轮下降，仍为132反弹前1.213倍，不能称完全恢复旧低点。近10轮约19.82分钟/轮，原始/对偶/互补降28.06%/40.38%/35.22%。RSS403.47GiB/峰657.34GiB，stderr空、无显式警告/错误/终态；仍未收敛。证据revision_6d_general/progress_20261015T095350Z.json及_summary.json。

Git基准ea07c31aa09498aab23af7a7f1eae4e3ac796966。只读scontrol、sstat、gurobi.log/solver_telemetry及stderr，日志0–178连续、源字节SHA已保存，打印行与最新callback轮次一致。对偶反弹大部分已消退但尚高于132旧低点；最近10轮三项持续下降，不据此预测结束时间。原始残差与互补性仍大，没有可行/最优或物理QC结论，打印与callback口径分开。仅更新交接、服务器状态、runbook及两份小证据；冻结源680a5c4、48线程生产profile和作业不改，其他case3/SI会话内容保留。下一步用户查进度时只读核对收敛与终态；任何QC标签均完整保全全部解数据。


## 2026-10-15英国21:40 Base2060第210轮与新对偶回升

- 2026-10-15英国21:40（北京10月16日04:40）Base2060/5124127 RUNNING/m4cm2108，累计3天3:23:15，最新iter210（英国21:28:19），较178推进32轮。PInf137/DInf5.42e-6/Compl6.86；较178降61.84%/12.58%/72.78%，目标差4.60943322e8降70.75%。对偶先至194轮3.40e-6，195–210连续16轮回升59.41%，不能沿用三项连续下降；原始/互补/目标差继续下降。近10轮原始/互补/目标差降27.89%/36.48%/34.69%，约20.34分钟/轮。RSS403.53GiB/峰657.34GiB，stderr空，无显式警告/错误/终态；仍未收敛。证据revision_6d_general/progress_20261015T204018Z.json及_summary.json。

Git基准e58925f8ceb48d036f72d723e13f5abb04f82cd0，只读scontrol、sstat、gurobi.log/solver_telemetry及stderr；0–210连续迭代行与原始日志SHA保存，最新callback轮次和打印一致。原始/互补/目标差近10轮下降速度较190–200轮略快，但对偶仍回升；没有多项同步恶化或求解器错误，不推断整体发散，也不保证完成时间。打印与callback残差定义不同，不当作物理GW/GWh验收。仅更新交接、MODEL_SERVER_STATUS、SERVER_RUNBOOK与两份小证据；冻结源680a5c4和运行配置不变，未改其他会话/作业/监听。下一步只读关注对偶是否止升、原始与互补改善是否持续，终态完整保全不受QC标签影响。


## 2026-10-15 P4本机完成、P5暂停（Git基准 91345ed）

仅从已完成Base2040/2050原release只读取证，未访问T550 cloud_backup或操作Job5124127。2050采用四路有限字节段传输，全部部分文件/分块保留，最终MPS/BarPi的字节数和原manifest SHA核验通过；本机串行解析，两年筛选清单margin0.2通过，按Base余量固定新建列12,505/6,195，保留可扩建21,473/29,171。证据case3_2030_launch_20261014/P4_completion_20261015.json及REVIEW；原件/完整表本地保全，小清单随Git，不更新任何冻结release。

本轮作者暂停P5；C2050与nocredit2030等待case32030系列成功收敛及后续确认。2026-10-15T21:19:26Z左右只读squeue确认5153878 RUNNING/m4cg1604、5153901 PENDING/JobHeldUser，精确取证时刻见P4_job_state_20261015.json。无提交/release/cancel，无新增C2050门禁或打包，无后台监听/自动提交服务。既有C2050派生状态保留。


## 2026-10-16英国13:18 Base2060第256轮及对偶回落

- 2026-10-16英国13:18（北京20:18）Base2060/5124127 RUNNING/m4cm2108，累计3天19:01:12，最新iter256（英国13:08:32），较210推进46轮。PInf24.7/DInf2.88e-6/Compl0.885，较210降81.97%/46.86%/87.10%，目标差6.40395073e7下降86.11%。对偶227轮峰1.08e-5后回落，250有22.08%小反弹，251–256连续下降；当前低于194回升前3.40e-6。近10轮原始/对偶/互补降31.39%/21.31%/34.44%，目标差降33.53%，约20.49分钟/轮；原始与互补速度和前10轮接近。RSS403.57GiB/峰657.34GiB，stderr空，无显式警告/错误/终态，仍未收敛。证据revision_6d_general/progress_20261016T121812Z.json及_summary.json。

Git基准b1b5565ee56376524b3914bf3bdbdcaf09bafaff；只读scontrol、sstat、gurobi.log/solver_telemetry及stderr。0–256连续迭代核验，原始日志字节SHA和打印/callback两种口径保留。对偶已低于此前194低点但250存在新小反弹，不称227后全程单调；目标差和原始残差仍明显，互补性低于1不等于最优。没有可靠完成百分比或ETA。仅两份证据和交接、MODEL_SERVER_STATUS、SERVER_RUNBOOK更新；冻结源码680a5c4/生产参数/运行作业及其他会话不改。下一步用户查询时只读观察是否持续收敛及终态，任何QC标签均完整保全解与归档。


## 2026-10-16英国23:30 新增Case3联合进度汇报约定

- 2026-10-16英国23:30联合查进度：云端2个RUNNING（Base2060/5124127、Case3 2030/5153878），nocredit5153901另为PENDING/JobHeldUser，不计运行数。用户明确后续询问进度时同时检查所有运行项目，先报RUNNING项目数，再逐项报轮次/收敛/资源，保持无定时检查。Base2060 iter286、累计4天5:13，PInf7.08/DInf6.86e-7/Compl0.237；Case3 iter193、累计2天1:18，PInf31.8/DInf7.54e-7/Compl1.01。两者stderr空、无显式警告/错误/终态。联合证据cloud_joint_progress_20261016/status_20261016T223008Z{,_summary}.json。

Git基准4d98a1e27bf5244df1e0ab084336b06cf5cb3a52。作者本轮要求同步关注Case3，并在澄清中明确“询问时一并检查（保持现有方式）”；此为后续汇报范围和顺序约定，不建立自动化。只读squeue -u当前账户取得完整队列，scontrol/sstat核对三项身份与状态，再读取两RUNNING作业output_8760/gurobi.log和solver_telemetry、stderr。Base2060源码680a5c4和Case3源码62bba59冻结不变；nocredit继续held，不操作C2050或新求解。两份证据记录日志SHA、完整连续迭代行和派生最近10轮指标。Case3第191轮对偶小反弹，192–193回落至此前190水平以下；两项仍未收敛。Slurm RSS/峰值与Gurobi内部内存统计不同，不混用。仅更新交接、MODEL_SERVER_STATUS、SERVER_RUNBOOK及本次证据；其他会话未提交内容保留。下一步用户查询时重新枚举实际队列后逐项取证，区分RUNNING、held、终态；所有解数据保全与QC标签独立。

## 2026-10-19 Case3 2030完成及Base2060第480轮

- 2026-10-19英国22:19（北京10月20日05:19）联合查进度：云端仅1个RUNNING，Base2060/5124127到iter480、累计7天4:02，打印PInf0.0155/DInf1.01e-8/Compl3.75e-4；尚无终态。Case3 2030/5153878已于10月18日英国14:38:11完成（COMPLETED/0:0，3天16:26:04），Barrier353轮OPTIMAL，保全COMPLETE/errors=[]，relative_v1=PASS，严格口径HARD_FAIL仍记录；scientifically_accepted=false，作者采纳和筛选定价证书后续另行处理。nocredit5153901仍JobHeldUser，不自动释放。证据cloud_joint_progress_20261016/status_20261019T211913Z{,_summary}.json及case3_completion_details_20261019.json。

Git基准bbb0222d47750f68584d6da8044c724a18bce73b。只读squeue/scontrol/sstat/sacct与冻结release日志、solve_report、QC、保全和归档manifest；Case3已退出队列，使用sacct确认正常终态。Base近470–480轮原始/对偶/互补分别下降41.73%/70.38%/43.61%，约22.41分钟/轮；对偶中途有反弹，不称全程单调。Base当前RSS406.72GiB、Slurm峰657.34GiB，stderr空；仍不能给可靠ETA。Case3最终打印PInf8.57e-4/DInf7.67e-7/Compl1.52e-5，目标4188026.777763238 million CNY；全部保全阶段完成，原模型归档COMPLETE，BarPi导出可用。严格检查的双向流和目标分项标签未通过，relative_v1通过；水库项按作者规则暂缓。冷热库存上下界违反均0 GWh。此处是读取报告状态，未对多GB归档重新计算全量SHA，也未完成筛选定价证书或作者最终验收。仅更新三份交接文档及三份小JSON；无模型改动，不重复跑求解测试。运行源码680a5c4/62bba59、参数、held和其他会话工作保持原状，无自动监听。下一步仅在作者询问时核对队列与Base收敛；Case3后续证书/采用及任何新排程须按任务合同和作者安排，P5/C2050继续暂停。

### 2026-10-19：case3 2030比较与2040续接预检（证书前版本）

2026-10-19 case3 2030与Base初步比较及2040预检：54份小证据远端/本地SHA核验，现有解目标点差47.520584亿元/年（0.113339%）；证书B待定，成本节省区间为[44.456953,60.836946+B/100]亿元（B单位million CNY）。扩展relative_v1两侧PASS；case3冷热库存M4.01009e-8GWh；R1只读清理预检PASS（发电/储能0.110375GW、网络0.100047GW），没有改状态或代作者采纳。2040尚无正式R1状态、1h/24h门禁、release或held作业，不能直接放行。nocredit5153901仍held，C2050/P5暂停。详情case3_2030_launch_20261014/comparison_20261019/REVIEW_ZH.md。

Git基准2a0f6c3；新增明确清单的小证据采集/比较脚本、comparison_20261019报告/CSV/JSON，四路下载助手增加显式release参数（旧year入口保留）。运行collect_comparison_20261019.py（含--r1-supplement）、assess_relative_v1.py两侧、analyze_comparison_20261019.py；所有已采集文件SHA及manifest已列项复核通过。原严格QC、candidate状态和全部远端结果不变。R1通用审计的固定文案“storage is zero”对本次不适用，实际storage小量0.004324262GW已计入总量，报告披露，未改算法。没有操作Base2060、提交/放行任何作业或建立监听。

唯一有限传输会话：本机fetch_pricing_archive_ranges.py --release 20261014_case3_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1 --output supplementary_materials/reviews/case3_2030_launch_20261014/P1_case3_archive_20261019，原MPS4142788418字节和raw BarPi等待完整SHA；保留每块及部分文件，不重启重复传输。下一步先核验download_identity.json，再补candidate_selection/result_manifest小文件并离线price_screened_candidates.py（新输出目录）；B>418.802677776 million CNY触发一次2030重解。P1 Base2030全年自检仍未执行。作者采纳与完整R1/2040门禁后才能held汇报；无自动release。保留其他会话SI未提交条目及稿件。

## 2026-10-19 晚：nocredit 与 C2050 放行，case3 2040 云端门禁阻塞

- 授权依据：AGENTS.md 2026-10-19 晚及 PROMPT_release_nocredit_case3_2040_C2050_20261019.md；源码提交 681627f，C2050 打包工具及门禁提交 f6372ff。报告：supplementary_materials/reviews/case3_2040_C2050_launch_20261019/REVIEW_ZH.md。
- Claude 证书原件 SHA 交叉核验通过；B=347.7820678689325 million CNY、B/obj=8.304198762899926e-5，ACCEPT/INTERVAL_WITH_B，3 个负价列，无需重解。本轮未重复计算；节省区间[44.46,64.32]亿元/年。作者已采纳 case3 2030 筛选解候选状态作为2040上游。
- 两个续接年 R1、参数核准、筛选/不筛选1h MPS仅BOUNDS_VRE_NEW不同、容量微小余量0列、24h门禁均PASS；M分别1.0428117347416332e-7与1.969660003986462e-7 GWh，信用越界0，relative_v1 PASS，保全COMPLETE。17项本机回归PASS。短窗不作规划结论。
- Job5153901 nocredit：RUNNING/m4cg1604，AllocTRES cpu64/mem750G/billing64，UNLIMITED/no-requeue，启动可用722.5721397399902GiB，smoke及7项计算节点回归PASS。
- C2050 Job5201262：RUNNING/m4cg1606，同资源分配，启动可用723.3704795837402GiB，smoke及7项回归PASS。新release为20261020_lateentry_2050_v9a12_screen0p2_agg0_t48_m750_tol1e4_v1，源码f6372ff，58项数据SHA核验，云端preflight PASS后提交release。
- case3 2040：没有Job ID、未提交。20261020_case3_2040_v9a12_screen0p2_agg0_t48_m750_tol1e4_v1（源码681627f）本机门禁通过，但云端preflight缺thermal/retirement_schedule.csv。按任务书第6节停止该作业放行；冻结包与失败输出原样保留，不原地补文件。C2050在冻结前补齐并核对3项续接输入，不受影响。
- 最新只读核验时间2026-10-20T06:46:02.396615+08:00；小文件传输SHA校验通过，final_job_status.json含状态、计算节点smoke及回归尾部。未查询/操作Job5124127，未访问cloud_backup、未修改既有冻结源码、未读复制凭据，无后台监听/自动提交。
- 后续：等待作者审查2040打包阻塞；任何修复须新release并通过完整输入与云端preflight，当前失败包不得放行。两个已运行作业仅在作者要求时再做只读查询。所有原始/失败/部分输出继续完整保全。

## 2026-10-20：case3 2040 v2 打包修复并放行

- 作者明确授权补齐v1遗漏、原源码681627f不变、preflight通过即release；文档起点a66cd15。未修改生产代码、profile、batch、筛选清单或R1状态；原本机门禁继续有效。
- 对照C2050已核验58项数据：v1漏列thermal/existing_capacity_2025.csv、thermal/retirement_schedule.csv、hydro/grfr_monthly_p30_single_year_proxy_2019.nc；其中existing_capacity实体存在且SHA正确，后两项实体缺失，无其他SHA不一致。三项均从C2050已核验目录复制到v2自有additional_data并显式纳入清单。
- 395源码文件与681627f git archive逐字节一致；源码/状态/batch/门禁共409项保持原字节。58项数据与本地核验通过，云端实际74项必需逻辑输入与原24h门禁manifest SHA一致。水文逻辑别名核对仅只读已有manifest，无重复preflight。
- 新release：20261020_case3_2040_v9a12_screen0p2_agg0_t48_m750_tol1e4_v2；release manifest SHA b1a07cb8bb062943dfc543e788eef830667a157e093a2016d1c3605508829283；source manifest SHA c8ea0394405ed8492ab58ca300da9de0e179b600aa6f293f31fce3f5b3b27b37。
- 云端preflight一次PASS，sbatch --test-only/held请求核验/冻结文件核验后release Job5201318。2026-10-20T07:01:20.005150+08:00 核验RUNNING/m4cm1803，AllocTRES cpu64/mem750G/billing64，UNLIMITED/no-requeue，启动725.0457878112793GiB，smoke及7项回归PASS，stderr空。
- 新增报告与小证据：case3_2040_C2050_launch_20261019/REVIEW_ZH.md追加修复节，deployment_case3_2040_v2下input_comparison/local_manifest_check/source_identity_check/frozen_release/cloud_preflight/cloud_manifest_check/released/startup_status.json；原始操作命令与日志本地保留。
- v1及失败输出424个文件SHA/mtime在建立前后、启动后均不变；不读复制凭据、不操作其他三个Job、不访问cloud_backup、不建监听。后续只按作者请求查询；所有运行与失败包完整保全。

## 2026-10-20 四项目进度：Base2060完成、C2050内存终止

- **2026-10-20英国12:12（北京19:12）四项目核验：实际2个RUNNING。** Base2060/5124127已于英国09:23:29正常结束，511轮OPTIMAL，Slurm COMPLETED/0:0，总7天15:06:23，保全COMPLETE/errors=[]，relative_v1 PASS、严格HARD_FAIL并存。C2050/5201262于英国04:08:53因OUT_OF_MEMORY终止（4:23:41，batch exit137），日志停在ordering2005s，无Barrier迭代；原模型归档COMPLETE，未生成完整解/保全报告，失败现场保留，未重启。nocredit5153901第43轮、12:42:17；case3 2040/5201318第23轮、12:12:04；两者日志无显式警告、stderr空。证据cloud_joint_progress_20261016/status_20261020T111242Z{,_summary}.json；完整终态报告terminal_details_20261020.json本地留存、SHA记入summary。

Git基准e7d5d4ac4eb253b56458df88f7c8230f6e7c8d71。按作者本次查询，只读squeue/scontrol/sstat/sacct、gurobi.log、batch_exit及终态solve/QC/preservation/archive报告；不修改冻结包或作业。Base最终打印PInf2.81e-3/DInf1.29e-8/Compl6.25e-5，目标5789097.634735345 million CNY，求解655761.754s，全部保全阶段完成；完整归档未重新全量SHA校验，科学采纳待作者决定。C2050 Slurm明确1次oom_kill，MaxRSS719.855GiB；该采样值不能代替瞬时cgroup峰值或据此确定重跑内存。无迭代解，不能解释成数学不可行或收敛失败。nocredit第33至43轮PInf/DInf/Compl分别降66.24%/67.05%/65.94%，14.49分钟/轮，RSS372.11GiB/峰704.59GiB；2040第13至23轮分别降73.65%/76.67%/74.01%，17.67分钟/轮，RSS396.30GiB/峰712.44GiB。两者均为早期迭代，残差绝对量大，不能预估完成率/ETA。变更仅3份交接文档及2份小证据JSON，JSON解析和暂存diff检查；没有源码变更，无需求解测试。下一步：作者查询时继续观察两RUNNING；C2050须先独立诊断排序阶段内存和提出新release资源方案再安排重跑，现包与部分输出保全；本轮不自动重启、无后台监听，不动SI其他会话。

## 2026-10-20：C2050 40线程新作业启动许可失败

**2026-10-20 C2050 40线程已提交放行但许可阻塞：** 作者授权40线程新release，源码f75a330；1h/24h门禁及13项回归PASS，MPS分段与原模型一致、58项数据/79项必需输入核验通过。Job5206992在m4cm1607获cpu64/mem750G/billing64、UNLIMITED，启动≥700GiB检查通过后gp.Env.start报License expired，4秒FAILED/1:0，尚未构建全年模型。没有40线程峰值结果；两次失败包均完整保留。详见case3_2040_C2050_launch_20261019/REVIEW_ZH.md本日40线程节与deployment_C2050_t40/。下一步等待作者恢复云端许可；不重复提交、不建监听、不影响其他作业。

实际运行2026-10-20北京时间19:47:31–19:47:35；新release为20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1。Slurm FAILED/ExitCode1:0；尚无output_8760及有效解，完整保留已有日志和包。未修改原冻结release；原case3 2040与nocredit未受本轮操作影响。完整smoke未通过，需恢复许可后另行核验；不自动重启。

## 2026-10-20：新WLS通过，C2050 40线程v2运行

**2026-10-20新WLS恢复C2050运行（取代上一条许可阻塞）：** 作者提供D:/gurobi1许可，独立受限路径迁移，未覆盖旧许可/未公开内容；本机、云端及计算节点2501变量测试通过。新t40_v2 release源码d385fa7，396项repo文件与40线程v1相同，R1/筛选/Aggregate0不变，preflight PASS。Job5207165 RUNNING/m4cm1607，北京20:24:47启动，实配cpu64/mem750G/billing64、UNLIMITED，启动可用722.968513GiB，7项节点回归通过，全年流程已开始。证据deployment_C2050_t40_wls_v2/startup_verified.json，详细报告REVIEW本日新WLS节。两次失败包保留，无后台监听；下一步按作者要求核验排序峰值，尚无全年40线程峰值/收敛结论。

旧5206992因旧许可过期4秒失败、新5207165使用独立WLS路径；原许可证文件未覆盖，其他作业未干预。门禁与启动证据见本轮REVIEW与deployment_C2050_t40_wls_v2/。

## 2026-10-20北京21:01：许可影响只读核验

**2026-10-20北京21:01许可影响核验：** 3项RUNNING。nocredit5153901/m4cg1604到51轮（20:54），case3 2040/5201318/m4cm1803到30轮（20:57），均较此前43/23轮继续推进；stdout/Gurobi日志未见许可错误，stderr/Slurm stderr空。新C2050 5207165/m4cm1607运行37分09秒、尚无Barrier行，无许可错误。旧许可明确阻断的是5206992的新Env，当前未观察到其他既有求解受影响。证据cloud_joint_progress_20261016/license_impact_20261020T130159Z.json；本轮只读，不换运行任务许可/不重启/不建立监听。

## 2026-10-20英国16:49 三项运行联合进度

- **2026-10-20英国16:49／北京23:49联合进度：3项RUNNING。** nocredit5153901第66轮、17:18:56，PInf1.92e7/DInf0.0278/Compl4.51e5；case3 2040/5201318第39轮、16:48:43，PInf9.70e9/DInf34.4/Compl2.23e8。C2050 t40新WLS/5207165运行3:24:31，仍在presolve（日志9315s），无Barrier行，尚未实测排序峰值。三者未见显式警告、许可错误，stderr与Slurm stderr均0字节。证据cloud_joint_progress_20261016/status_20261020T154922Z{,_summary}.json。

Git基准bb93d25dfd1a368d2d3af50226442fb6ad58dd3a。按作者查询，只读squeue完整队列、scontrol/sstat及各release的gurobi.log和stderr；记录原始日志SHA，未修改作业/源码/许可或启动后台监听。nocredit较本会话上次43轮前进23轮，最近56–66轮PInf/DInf/Compl降72.01%/75.83%/73.31%，11.30分钟/轮；对偶63/65轮有小反弹，不称全程单调。2040较上次23轮前进16轮，最近29–39轮三项降71.55%/71.57%/70.96%，17.38分钟/轮。当前RSS/Slurm峰分别369.48/704.59、396.63/712.44、84.66/93.24GiB；C2050处预求解，低内存不能外推排序/因子分解峰值，40线程能否避免OOM仍待实测。此前Base2060完成511轮OPTIMAL/保全COMPLETE/relative_v1 PASS的终态沿用已核验证据；本轮没有重读其大归档。仅3份交接文档和2份小JSON更新，JSON解析、敏感字面量与diff检查；无代码变化，不重复运行求解测试。下一步仅按作者请求继续核对三项进度，重点确认C2050是否通过排序并进入Barrier；旧失败包和所有输出保留，不动SI会话内容。

## 2026-10-20 已解结果补备份与结束后必做流程

- **2026-10-20 T550补备份已启动及长期规则：** 作者要求每次确认云端生产求解结束均执行备份，无需重复授权；保持无定时监听。旧Base2030/2040/2050三套manifest与原262项path/bytes/SHA一致，不重复传输。新增Base2060和Case3 2030共184文件/10,828,735,197bytes，T550 PID2833275单次自主拉取，完成后预计余量34.4127%；当前两套T1均VERIFIED（176文件/1,112,217,190bytes），Base2060 T2传输中，完整备份尚未完成。Case3证书与扩展验收九文件/6,223,488bytes旁置同步SHA VERIFIED。规则见AGENTS、台账CLOUD_BACKUP_REGISTER_ZH.md，证据cloud_backup_20261020/。

Git基准559f633f4481d4ea9a5d589fd9bc6ece5b69631b。先读取既有backup_on_t550/collect_status与历史完成manifest，核对T550空间、无旧活跃备份和云端五套已解生产输出；前三套历史备份已完，新补两套。scripts/backup_completed_cloud.py复用原分层rsync/SHA实现，新增显式配置、活跃作业/终态门禁、全局flock与不静默省略MPS的空间检查；7项针对性单测PASS（tests/test_completed_cloud_backup.py）。远端实际plan、启动、T1验证通过；部署工具原字节SHA cd261143d85b91664b26d8b8582468f7171a64155f5d443ca535b579a2f47658。操作目录/home/zz2/National_model_server/cloud_backup/_operations/20261020_base2060_case3_2030，工具目录backup_tools/completed_20261020；只读查询python supplementary_materials/reviews/cloud_backup_20261020/collect_status.py。新状态/manifest本地留证，不触碰云端源码、运行三作业、凭据、旧备份或SI会话。完整结果传输未结束，不能将启动或T1通过写为最终COMPLETE；下次检查status六层VERIFIED与两最终manifest，异常则原操作核对后续传。C2050两旧失败release不是完整解备份，现存输出云端保留并在台账单列。任何新生产终态均按新规则核对和补备份，仍不建立后台监听。

## 2026-10-20 两套已解结果技术验收与本地取回

- **2026-10-20 Base2060与Case32030验收/本地包已完成：** 两套T550离线复评均relative_v1_author_20261014_extended PASS，严格HARD_FAIL保留，水库按作者规则暂缓并完整披露。云端61原始小文件/26,736,488bytes已取回，59项与原manifest一致、两份manifest自身另核源SHA；T550按原调度重算、省级与水库残差核验。两正式验收JSON旁置同步原字节SHA一致。本地packages/base2060_acceptance_20261020.zip为4,279,063bytes/49成员，case3_2030包7,449,859bytes/58成员，均逐项SHA校验。新增两套T550备份亦已COMPLETE：184文件/10,828,735,197bytes，六层VERIFIED、源未变。证据与报告completed_acceptance_20261020/，台账已更新；不改变原候选状态，不新增求解。

Git基准f04bf22a05b40b3ce8dbe8fae4237a1ada266960。本轮复用旧collect_evidence和独立relative_acceptance/assess_relative_v1 CLI，仅新增本轮collect/assess/finalize编排；评估器源码未改，14项回归PASS。新目录supplementary_materials/reviews/completed_acceptance_20261020/：collection_manifest、assessment_byte_verification、两套assessments、backup_completion_verification、acceptance_sync_verification、package_summary、validation_summary及REVIEW。原始小文件和ZIP仅本地保留，Git只同步编排/报告/小JSON；全部ZIP CRC/成员bytes/SHA验证通过。Base2060最大功率残差3.683015590e-6GW、成本闭合1.988788200e-11、双向额外损耗占比1.199859818e-5；Case3相应2.703891084e-7/3.087821615e-12/3.574347760e-6。水库最大713.857706641m³（HydroCHN_00136）及0.282365064m³（HydroCHN_00473）与原NPZ重算一致，活动库容/小时均披露；扩展GW/GWh及其余保留检查无失败。Case3证书身份与本次MPS/BarPi清单一致，B/obj8.3042e-5，沿用作者10月19日采纳，无重算/重解。Base本次仅技术质量验收，不自动晋级源candidate。T550原备份完成于2026-10-20T16:26:47.750542+00:00，最终manifest与计划完全一致，旁置正式JSON精确字节同步（不重复旧CRLF误判）。截图中的未备份/仍求解旧状态以本条更正；其他会话SI模块、稿件不动。下一步可用本地验收包开展结果分析；水库逐站复核仍按作者暂缓，无新增求解/监听/运行包变更。

## 2026-10-20英国23:22 三项运行及C2050通过排序

- **2026-10-20英国23:22／10月21日北京06:22联合进度：3项RUNNING。** nocredit5153901到98轮（23:52:04），PInf1.22e4/DInf3.93e-5/Compl478；case3 2040/5201318到62轮（23:21:51），PInf1.86e9/DInf0.394/Compl4.04e7。C2050 t40/5207165已通过此前OOM的排序阶段并到11轮（9:57:39），PInf1.82e11/DInf1340/Compl4.52e9，当前RSS413.41GiB、采样峰621.18GiB，未再出现OOM；不能据此保证后续峰值。三项stderr空、未见显式警告或许可错误。证据cloud_joint_progress_20261016/status_20261020T222226Z{,_summary}.json。

Git基准70a7756888c3cb0f1953e57dcc63d7a70c4134ca。只读squeue完整队列、scontrol/sstat、gurobi.log与stderr，日志SHA已留证。相较上次66/39轮，nocredit和case3 2040分别前进32/23轮；最近10轮PInf/DInf/Compl分别下降96.64%/94.30%/94.98%与63.10%/95.53%/62.24%，13.68与18.07分钟/轮。当前RSS/Slurm采样峰分别370.38/704.59、394.50/712.44GiB。C2050实测40线程，已进入Barrier并完成11轮，最近1–11轮三项下降56.56%/46.40%/54.80%，24.26分钟/轮；初始对偶残差有上升，不能描述为全程单调，旧48线程排序OOM原包仍保留。三者均未收敛，不估算完成率/ETA；本轮没有新终态，无须启动新备份。此前Base2060和Case3 2030技术验收relative_v1 PASS、本地验收ZIP及T550完整备份已完成，沿用completed_acceptance_20261020已核验证据，不重复传输。修改仅3份交接文档与2份小JSON；JSON解析、暂存差异和敏感字面量检查，无源码变更、不重复求解测试。不修改冻结包/许可/作业，不建监听、不动SI。下一步仅在作者查询时继续核对收敛和内存；发现生产终态按AGENTS执行T550备份收尾。

## 2026-10-21英国11:19 三项运行联合进度

- **2026-10-21英国11:19／北京18:19联合进度：3项RUNNING。** nocredit5153901到144轮（1天11:49:06），PInf246/DInf1.99e-6/Compl13.9；case3 2040/5201318到109轮（1天11:18:53），PInf4.26e7/DInf6.47e-7/Compl1.05e6；C2050 t40/5207165到41轮（21:54:41），PInf5.04e9/DInf19.9/Compl1.14e8。三项未见显式警告或许可错误，stderr空。C2050当前RSS415.33GiB，采样峰621.18GiB未增加。证据cloud_joint_progress_20261016/status_20261021T101930Z{,_summary}.json。

Git基准2fcacc5c0151e8add79e6feada41dbba2f815d5a。只读squeue完整队列、scontrol/sstat、gurobi.log与stderr，日志SHA留证；无新终态。相较上次98/62/11轮分别前进46/47/30轮。nocredit最近134–144轮原始残差降34.05%、互补性降43.03%，对偶残差从1.88e-6升至1.99e-6（137轮反弹后回落），不能称三项单调改善；17.25分钟/轮，比上次13.68分钟/轮慢。Case3 2040最近99–109轮三项下降82.82%/99.42%/82.90%，15.36分钟/轮；C2050最近31–41轮下降71.03%/78.23%/71.92%，24.38分钟/轮。当前RSS/Slurm采样峰依次374.62/704.59、399.18/712.44、415.33/621.18GiB；C2050未再OOM，不承诺后续峰值。三者尚未收敛，对偶残差小不代表原始可行或接近结束，不估算完成率/ETA。Base2060与Case3 2030已完成验收、本地包与T550全备份，沿用completed_acceptance_20261020证据，不重复传输。仅3份交接文档及2份小JSON变化，解析/敏感字面量/暂存差异检查；无代码修改，无需求解测试。保持运行release、参数、许可、其他会话SI不变，无监听。下一步仅在作者询问时核对三项收敛，遇新生产终态按AGENTS完成T550备份收尾。

## 2026-10-21英国19:54 三项运行联合进度

- **2026-10-21英国19:54／10月22日北京02:54联合进度：3项RUNNING。** nocredit5153901到172轮（1天20:24:29），PInf55.8/DInf2.29e-6/Compl3.19；case3 2040/5201318到138轮（1天19:54:16），PInf57900/DInf2.79e-7/Compl1350；C2050 t40/5207165到63轮（1天6:30:05），PInf2.58e9/DInf5.42/Compl5.48e7。三项未见显式警告或许可错误，stderr空，采样内存峰值未增加。证据cloud_joint_progress_20261016/status_20261021T185453Z{,_summary}.json。

Git基准3ba8a0f591dfeadd695a5469324c18bb82ca7691。只读squeue完整队列、scontrol/sstat、gurobi.log与stderr，记录日志SHA；无新终态。较上次144/109/41轮分别前进28/29/22轮。nocredit最近162–172轮PInf/DInf/Compl下降35.34%/31.85%/32.70%，18.35分钟/轮；对偶较上次查询1.99e-6仍略高，不称全程单调。Case3 2040最近128–138轮下降67.29%/75.95%/69.73%，18.57分钟/轮，互补性较上次查询1.05e6降至1350（约778倍），原始残差仍未收敛。C2050最近53–63轮下降17.83%/29.88%/18.69%，23.22分钟/轮，残差下降幅度较上一窗口减小、未停滞。RSS/Slurm采样峰依次371.02/704.59、398.88/712.44、416.00/621.18GiB；未再OOM，不承诺后续峰值或结束时间。Base2060和Case3 2030技术验收/本地包/T550完整备份沿用已完成证据，不重复传输。本轮仅3份交接文档与2份JSON，解析、敏感字面量与暂存差异检查，无代码变化、不重复求解测试。不改冻结包、参数、许可或其他SI会话，无监听。下一步按作者询问核对收敛及内存，发现新生产终态即按AGENTS补齐T550备份。

## 2026-10-21英国22:49 三项运行联合进度

- **2026-10-21英国22:49／10月22日北京05:49联合进度：3项RUNNING。** nocredit5153901到182轮（1天23:19:08），PInf37.1/DInf1.59e-6/Compl2.19；case3 2040/5201318到148轮（1天22:48:55），PInf14400/DInf1.12e-6/Compl304；C2050 t40/5207165到70轮（1天9:24:43），PInf1.95e9/DInf2.62/Compl4.04e7。三项stderr空、未见显式警告或许可错误，采样内存峰不变。证据cloud_joint_progress_20261016/status_20261021T214931Z{,_summary}.json。

Git基准090e802f1bf1bdb17040b6630a4f1eadcc11611e。只读squeue、scontrol/sstat、gurobi.log及stderr，日志SHA留证，无新终态。较上次172/138/63轮前进10/10/7轮。nocredit最近172–182轮PInf/DInf/Compl下降33.51%/30.57%/31.35%，18.14分钟/轮。Case3 2040最近138–148轮PInf和Compl下降75.13%/77.48%，DInf从2.79e-7升至1.12e-6（约4.01倍），19.04分钟/轮，不称三项单调收敛。C2050最近60–70轮下降28.57%/55.97%/30.46%，23.36分钟/轮；相较上一53–63窗口互补性下降18.69%，本窗口降幅改善，但窗口重叠且绝对残差仍大，不能据此预测结束时间。RSS/Slurm峰依次371.05/704.59、395.82/712.44、416.17/621.18GiB，未再OOM。Base2060和Case3 2030的验收包与T550完整备份沿用已完成证据，不重复传输。本轮仅更新3份交接文档与2份小JSON，解析/敏感字面量/暂存diff检查；无代码变更，不重复求解测试。不动冻结包、参数、许可、SI或排程，无监听。下一步按作者询问核对进度，发现新生产终态按AGENTS补齐T550备份。

## 2026-10-22英国13:13 三项运行联合进度

- **2026-10-22英国13:13／北京20:13联合进度：3项RUNNING。** nocredit5153901到231轮（2天13:43:15），PInf3.19/DInf2.54e-5/Compl0.187；case3 2040/5201318到192轮（2天13:13:02），PInf571/DInf1.59e-5/Compl9.59；C2050 t40/5207165到107轮（1天23:48:50），PInf1.74e8/DInf0.00843/Compl3.61e6。三项stderr空、未见显式警告或许可错误，采样内存峰不变。证据cloud_joint_progress_20261016/status_20261022T121339Z{,_summary}.json。

Git基准1f332a57ddb99e722dd906b2e96dd0f41865df2c。只读squeue、scontrol/sstat、gurobi.log及stderr，日志SHA留证，无新终态。较上次182/148/70轮前进49/44/37轮。nocredit最近221–231轮PInf/Compl下降36.96%/38.08%，DInf从4.01e-6升至2.54e-5（6.33倍），16.67分钟/轮；互补性小于1不等于已经收敛。Case3 2040最近182–192轮PInf/Compl下降44.02%/51.81%，DInf从4.38e-7升至1.59e-5（36.30倍），187轮跳升后回落，20.96分钟/轮；不称三项单调改善。C2050最近97–107轮PInf/DInf/Compl下降63.83%/89.48%/63.05%，22.57分钟/轮，较此前60–70轮互补性下降30.46%改善，但仍有较大原始残差，不外推ETA。RSS/Slurm峰依次374.23/704.59、395.95/712.44、416.57/621.18GiB，未再OOM。Base2060及Case3 2030验收包与T550完整备份沿用已完成证据，不重复传输。本轮仅更新3份交接文档与2份小JSON，解析/敏感字面量/暂存diff检查，无代码变化，无需求解测试。不改冻结包、参数、许可、排程或SI，无监听。下一步按作者询问核对进度，尤其两项对偶残差变化；发现新生产终态按AGENTS补齐T550备份。

## 2026-10-22英国22:10 三项运行联合进度

- **2026-10-22英国22:10／10月23日北京05:10联合进度：3项RUNNING。** nocredit5153901到263轮（2天22:39:54），PInf0.959/DInf1.12e-5/Compl0.0552；case3 2040/5201318到214轮（2天22:09:41），PInf256/DInf1.68e-5/Compl3.56；C2050 t40/5207165到133轮（2天8:45:29），PInf2.30e6/DInf0.00032/Compl55000。三项stderr空、未见显式警告或许可错误，采样内存峰不变。证据cloud_joint_progress_20261016/status_20261022T211018Z{,_summary}.json。

Git基准8723da2c5d344d6606f349ef3463b0f16bcc34e2。只读squeue、scontrol/sstat、gurobi.log和stderr，记录日志SHA，无新终态。较上次231/192/107轮前进32/22/26轮。nocredit最近253–263轮PInf/DInf/Compl下降34.32%/35.63%/34.52%，16.50分钟/轮，原始残差低于1但尚未收敛。Case3 2040最近204–214轮下降27.07%/39.78%/33.71%，24.00分钟/轮，较上次20.96分钟/轮变慢；对偶较上次查询1.59e-5仍略高。C2050最近123–133轮下降93.39%/54.02%/92.43%，20.61分钟/轮；124轮对偶反弹后回落，不能称全程单调；互补性较上次3.61e6降至55000约65.6倍，本阶段改善但不外推ETA。RSS/Slurm峰依次374.87/704.59、399.68/712.44、416.72/621.18GiB，未再OOM。Base2060及Case3 2030验收包与T550全备份沿用已完成证据，不重复传输。本轮仅3份交接文档及2份JSON，解析/敏感字面量/暂存diff检查；无代码变更，不重复求解测试。不改冻结包、参数、许可、排程或其他SI会话，无监听。下一步按作者询问核对三项残差及终态；发现新生产终态按AGENTS补齐T550备份。

## 2026-10-23英国13:57 三项运行联合进度

- **2026-10-23英国13:57／北京20:57联合进度：3项RUNNING。** nocredit5153901到321轮（3天14:27:36），PInf0.0745/DInf2.03e-6/Compl0.00369；case3 2040/5201318到250轮（3天13:57:23），PInf56.1/DInf0.000321/Compl0.613；C2050 t40/5207165到172轮（3天0:33:11），PInf19000/DInf1.36e-6/Compl358。三项stderr空、未见显式警告或许可错误，采样内存峰不变。证据cloud_joint_progress_20261016/status_20261023T125757Z{,_summary}.json，观测时间以JSON内云端UTC为准。

Git基准0e9701f0e3b164e3ae5204c5d78779ae60c13e6f。只读squeue、scontrol/sstat、gurobi.log与stderr，日志SHA留证，无新终态。较上次263/214/133轮前进58/36/39轮。nocredit最近311–321轮PInf/DInf/Compl下降43.13%/24.54%/45.17%，15.80分钟/轮，对偶局部反弹仍存在。Case3 2040最近240–250轮三项下降35.59%/39.09%/37.39%，25.10分钟/轮；237轮DInf由6.93e-6升至2.35e-4、238轮达6.59e-4，随后降至3.21e-4，仍比上次查询1.68e-5高约19倍，须披露而非称全程单调。互补性小于1不是求解终态。C2050互补性较上次55000降至358约154倍，但最近162–172轮三项仅降14.80%/32.34%/25.73%，24.60分钟/轮，较上一窗口互补性下降92.43%明显放缓，仍在改善，不外推ETA。RSS/Slurm峰依次374.89/704.59、399.72/712.44、416.85/621.18GiB，未再OOM。Base2060及Case3 2030验收包/T550全备份沿用已完成证据，不重复传输。本轮仅3份交接文档与2份小JSON，解析/敏感字面量/暂存diff检查，无源码变化，不重复求解测试。不改冻结包、参数、许可、排程或其他SI会话，无监听。下一步按作者询问核对三项进度，重点关注2040对偶回落与C2050残差下降；新生产终态按AGENTS补齐T550备份。


## 2026-10-24 nocredit2030完成与两项目进度

**2026-10-24英国10:45／北京17:45：当前2项RUNNING，nocredit2030刚完成。** Job5153901于北京17:43:45 COMPLETED/0:0，总4天11:13:23，Barrier404轮OPTIMAL，目标4189002.976254521 million CNY；保全COMPLETE/errors=[]，81个output_8760文件共5,502,966,799bytes。冻结报告relative_v1_author_20261012=PASS，严格HARD_FAIL仍保留；这不是最新扩展口径的独立正式验收。其T550备份未启动：127.0.0.1:22转发拒绝连接、192.168.9.27:22超时，旧manifest/空间/活跃传输尚不可核验。已准备新配置，恢复连接后先防重复核验再自主拉取。Case3 2040/5201318到302轮，PInf7.68/DInf6.76e-5/Compl0.0837；C2050 t40/5207165到221轮，PInf734/DInf5.16e-8/Compl11.2；两项仍求解中。

Git基准8ed5beb6ebd2ddc2e5f038f36ce27e1ee2ebdcf3。09:43UTC第一快照三项RUNNING；09:45UTC再次squeue/sacct确认nocredit正常退出，不把两时点混作同时观测。其求解382362秒、终轮打印PInf8.46e-5/DInf1.98e-7/Compl3.14e-6；最终保全与result_manifest、batch_exit已生成。Case3近292–302轮三项残差降20.91%/20.84%/21.04%，约20.08分钟/轮；C2050近211–221轮降34.46%/45.11%/41.67%，约25.05分钟/轮。当前RSS分别396.02/416.91GiB，Slurm峰712.44/621.18GiB未变，stderr均空，无新警告/OOM。不能据此给可靠ETA。

证据：supplementary_materials/reviews/cloud_joint_progress_20261016/status_20261024T094319Z{,_summary}.json、nocredit_completion_20261024.json；备份配置与阻塞记录cloud_backup_20261024/。现有五套已完成备份的历史结论保留，本轮不能实时复核T550。下一步恢复既有转发后核对manifest/活跃进程/锁/磁盘余量，使用scripts/backup_completed_cloud.py对新release plan/run，全量bytes/SHA和源身份校验完成才称备份完成。无后台监听、不改变活跃作业/冻结包/科学参数；其他SI会话改动保留。仅记录和JSON更新，JSON解析及暂存diff检查，无需重复模型测试。


## 2026-10-25 两项目继续收敛与T550连接阻塞

**2026-10-25英国13:23 GMT／北京21:23：云端2项RUNNING。** Case3 2040/5201318到388轮（5天14:23:02），PInf0.568/DInf4.77e-6/Compl0.006；较昨日302推进86轮，近378–388轮三项下降27.18%/28.49%/28.14%，19.73分钟/轮。C2050 t40/5207165到279轮（5天00:58:50），PInf104/DInf2.71e-6/Compl0.965；较昨日221推进58轮，互补性首次低于1。近269–279轮原始/互补下降26.76%/31.56%，对偶反增122.13%，31.21分钟/轮；268和273轮对偶反弹，273峰3.71e-6后连续回落至2.71e-6，仍高于反弹前267轮2.71e-8，不能称三项持续单调改善。两项stderr空、无显式警告/错误/终态，RSS396.04/416.91GiB、Slurm峰712.44/621.18GiB未增；不承诺ETA。nocredit5153901再次sacct确认COMPLETED/0:0；T550 127.0.0.1:22转发仍Connection refused，无法核验manifest/空间/旧进程，备份本轮未启动。

Git基准45dc64751cc555768f277c47a6b0daadbba209ae；仅只读squeue/scontrol/sstat/sacct和日志、保存小证据与更新交接。证据supplementary_materials/reviews/cloud_joint_progress_20261016/status_20261025T132337Z{,_summary}.json、t550_backup_check_20261025.json。未改科学代码、冻结包、运行作业、其他SI会话或建立监听。验证为JSON解析、暂存范围/凭据模式/diff检查；无模型改动不重跑求解。下一步用户询问时检查收敛/终态；恢复T550既有转发后先核对旧备份、活跃传输与30%磁盘余量，再按cloud_backup_20261024/backup_config.json执行单次自主拉取和全量SHA校验，未完成前不标COMPLETE。


## 2026-10-25 T550恢复并启动nocredit2030完整备份

**2026-10-25英国13:25 GMT／北京21:25，T550连接恢复，取代本日上一条备份阻塞状态。** 作者开启转发后已核验hostname=t550；既有五套备份manifest均COMPLETE，两旧操作COMPLETE且未发现活跃备份进程。nocredit2030新计划93文件/5,510,708,567bytes（全部output_8760及启动身份元数据，T1/T2/T3全部包含），预计余量36.2871%满足30%门槛。单次自主传输PID700378于13:25:24UTC启动，13:25:38核验进程存在、状态RUNNING/T1 TRANSFERRING（89文件/584,009,478bytes），尚无完整目标SHA验证和最终manifest，不称备份完成。

Git基准6ee7f8a4241ed9a572aa2e0d6b9b8aa540ef18f9。复用已测试scripts/backup_completed_cloud.py，工具原字节SHA cd261143d85b91664b26d8b8582468f7171a64155f5d443ca535b579a2f47658，新配置和操作目录20261025_nocredit2030；工具部署backup_tools/completed_20261025。T550直连云端盘点正常，plan终态/保全/空间/目标不重复门禁通过，独立会话运行，具有全局与操作锁。证据supplementary_materials/reviews/cloud_backup_20261025/{backup_config,plan_execution,transfer_launch,startup_status}.json。目标/home/zz2/National_model_server/cloud_backup/20261014_case3nocredit_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1。旧备份只核manifest状态，不重复传输/全量哈希，不改源结果；未启动定时监听。新JSON解析、暂存diff/凭据检查通过；无源码变更，复用既有7项单测证据。下一步读取操作transfer_status，全部三层VERIFIED、目标逐文件bytes/SHA匹配和源身份不变后生成backup_manifest才可报告COMPLETE。异常时先核旧进程/锁再原操作续传。


## 2026-10-25深夜 两项目进度与nocredit备份完成

**2026-10-25英国23:40 GMT／10月26日北京07:40：云端2项RUNNING，nocredit备份已COMPLETE。** Case3 2040/5201318到417轮（6天00:40:06），PInf0.226/DInf3.09e-6/Compl0.00234，较上次388推进29轮；近407–417原始/互补降30.89%/31.58%，对偶升1.64%，22.85分钟/轮。C2050 t40/5207165到298轮（5天11:15:54），PInf50.9/DInf1.07e-4/Compl0.426，较279推进19轮；近288–298原始/互补降29.79%/31.62%，对偶增至原值8.70倍（增加769.92%），30.86分钟/轮。298轮对偶从8.40e-6跃至1.07e-4（12.74倍），尚无后续回落证据；其他两项仍降，无显式警告或错误，不能将互补改善等同于全指标稳定收敛。

Git基准b9ab0698a34f84fc12697486f296e138769ee2b8。只读squeue/scontrol/sstat/sacct及日志，stderr均0，Slurm峰712.44/621.18GiB未变；当前RSS约396.04/420.62GiB。仍无OPTIMAL，不给ETA、不改参数/作业。证据supplementary_materials/reviews/cloud_joint_progress_20261016/status_20261025T234041Z{,_summary}.json。

nocredit备份在2026-10-25T13:34:16.290807Z（北京21:34）完成，T1/T2/T3全部VERIFIED，93文件/5,510,708,567bytes，无延期文件，source_unchanged=true。最终backup_manifest文件清单与原plan逐项相等，源result_manifest SHA一致；本次取回完成证据cloud_backup_20261025/check_20261025T2340Z.json。目标/home/zz2/National_model_server/cloud_backup/20261014_case3nocredit_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1，磁盘仍约36.29%可用。完整逐文件bytes/SHA核验由单次备份进程完成，本次复核最终报告及清单，不重复传输。备份完成不代表最新扩展科学验收完成；原QC/作者待定标签不改。台账、交接、服务器记录同步追加；JSON解析/暂存diff与凭据检查，无源码变更不重跑求解。下一步询问时重点观察C2050对偶反弹是否恢复及两项终态，任何新终态按既定流程完整备份，无后台监听。


## 2026-10-26 两项目收敛及C2050对偶回落

**2026-10-26英国12:48 GMT／北京20:48：云端2项RUNNING。** Case3 2040/5201318到456轮（6天13:47:25），PInf0.0402/DInf5.57e-7/Compl3.75e-4，较417推进39轮；近446–456三项下降40.88%/50.27%/41.77%，19.07分钟/轮，448对偶有小幅波动，不能称全程单调。C2050 t40/5207165到324轮（6天00:23:13），PInf18.6/DInf1.27e-4/Compl0.155，较298推进26轮；近314–324三项下降31.62%/30.60%/32.02%，30.275分钟/轮。对偶305轮峰2.51e-4，当前较峰回落49.40%，仍高于上次298的1.07e-4及297反弹前8.40e-6；不能称已完全恢复。

Git基准fa2ccce7d8fb6f5a8443cebc20671c575bcc4852。只读squeue/scontrol/sstat/sacct、Gurobi日志及stderr，当前RSS396.05/420.62GiB、Slurm峰712.44/621.18GiB未增加；stderr空，无显式警告/错误/终态。nocredit5153901仍COMPLETED/0:0；其93文件/5,510,708,567bytes完整T550备份的上次最终验证结论保留，本轮不重复传输/全量SHA复核。证据supplementary_materials/reviews/cloud_joint_progress_20261016/status_20261026T124800Z{,_summary}.json，备份证据沿用cloud_backup_20261025/check_20261025T2340Z.json。

仅两小JSON和CODEX_HANDOFF/MODEL_SERVER_STATUS/SERVER_RUNBOOK更新，其他SI会话工作保留。JSON解析、暂存范围/凭据/diff检查通过，无源码变更无需模型测试；不改冻结包、作业或求解参数，不建监听，不给ETA。下一步用户询问时继续核验对偶恢复/终态，确认新生产终态后按已授权流程完整保全备份；nocredit最新扩展正式验收仍待执行。


## 2026-10-26 nocredit2030收尾、T550定价与case3 2050预置

Git起点0cbad432fb61cb555e92db42923339cffe79d63d。按作者新增授权，仅增加case3 2050 40线程profile及限定入口、同情景门禁选项，P4审计允许显式2060来源；不改物理模型/输入/约束。nocredit73小文件逐项SHA取回，备份93文件COMPLETE身份复核；定价B/obj8.1423511193e-5、扩展PASS，证书只在T550，原严格标签/输出不改。三方目标与原对偶差见case3_2030_launch_20261014/nocredit_results_20261026/REVIEW_ZH.md；旧case3上界64.32与高精度重算64.314766差异已明确披露。

准备入口case3_2050_preparation_20261026/{remote_work,prepare_package,collect_live}.py；云端独立目录/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/_preparations/20261026_case3_2050_t40_v1，11,220,392bytes包SHA b1d8f8b15f31efd72a4e34bd7afc95b66d9499a0e61cb95f0364e97bd6be0fd9，58数据SHA及bash语法PASS。未来最终源码须从本轮审查提交冻结，不能仅将新profile套到旧源码。

验证：定价5测试PASS；relative13项本地PASS、1项因缺gurobipy在T550补验PASS；新旧profile7项T550 PASS（含新增3项），新profile本地3项PASS。语法、逐键diff及数据清单核验通过；不以此代替未来真实R1/1h/24h/参数/preflight。2050中央值任务书位于../claude_workspace/tasks/PROMPT_release_nocredit_case3_2040_C2050_20261019.md。

下一步：等待正在进行的T550 Base2060离线清单计算后做P4同口径审计；case3 2040终态后按NEXT_ACTIONS_ZH.md备份/证书/扩展评估，B/obj≤1e-2才采纳并R1、门禁、最终preflight、提交release。C2050终态只收尾，C2060/C′等作者决定。不建后台监听，不读凭据，不干预5201318/5207165。保留既有其他会话32行handoff和稿件改动，Git仅明确审查清单。


## 2026-10-26 Base2060清单完成与最终交付

功能源码提交3c11ed7已推送github工作分支；本次只补清单/证据和交接。T550原scripts/build_vre_screen_list.py读取完整MPS/BarPi并核身份；audit_screen_2060.py复用P4：36686项、正余量33773、筛除8025、保留25748、无余量2913，原/反序apply_vre_screen均PASS。旧P4 2040/2050复放CSV逐字节一致，筛除仍12505/6195。新生产CSV SHA 831514fdb19da9ffa0a4ccca40def435a3972f37db00284524916c1d8b6c9fc3；MPS SHA c37a99082d8a9ab29ddb9c6580b25c399320546571aa2386738e42966fb8f29e；BarPi SHA 052b8623a580a53acd54dbbcded9e44f7369985898d68ef5d75a3d3b828d077d。

输出：supplementary_materials/reviews/base_2060_screen_20261026/ready/；总报告case3_2050_preparation_20261026/REVIEW_ZH.md；三方P/D与区间见case3_2030_launch_20261014/nocredit_results_20261026/REVIEW_ZH.md。命令remote_work.py screen、audit_screen_2060.py、finalize_reports.py、collect_live.py。大原件与nocredit完整证书留T550；Base2060全量CSV本地/T550保留，Git发生产清单和小证据。准备包source_commit只是当时基准，正式release须重新从已审查commit冻结。

14:05:46GMT：5201318 RUNNING/m4cm1803，第460轮PInf0.0314/DInf4.21e-7/Compl2.85e-4；5207165 RUNNING/m4cm1607，第327轮PInf16.9/DInf1.16e-4/Compl0.141。均cpu64/mem750G/billing64、UNLIMITED、Restarts0、stderr空，无终态报告。未干预运行任务。精确下一步：2040终态后完整T550备份、T550证书、扩展评估，B/obj≤1e-2才采纳，完成R1/1h/24h/2050实际参数/最终preflight后直接提交release；门禁失败停止报告。C2050终态只收尾，C2060/C′待作者。两份备份配置预置但未执行，无后台监听。其他32行SI交接与作者稿件保留未发布。

补充：Base2060三列生产清单向T550 ready/的额外旁置同步遇SSH255，随后只读核对在127.0.0.1:22 banner阶段超时，目标状态未确认。核心T550全量清单/identity与本地生产清单已经核验，不受影响；下一次连接恢复先核ready/已有文件与SHA，再按缺项续补。详见ready_t550_sync_status.json，不把这次额外同步标为完成。


## 2026-10-26 16:29 GMT T550恢复核验与遗漏同步补齐

Git起点1921b62efed0a71d3da18ee3b24cece86574fe36。T550 hostname已确认；先只读检查发现Base2060 screen_margin0p2_20261026/ready不存在，随后仅新建旁置目录并用exclusive-create写入缺失三文件，读回bytes/SHA与本地逐项一致。生产CSV 1,315,109bytes，SHA 831514fdb19da9ffa0a4ccca40def435a3972f37db00284524916c1d8b6c9fc3；另外两文件身份见base_2060_screen_20261026/ready_t550_recovery_20261026.json。此前ready_t550_sync_status.json连接失败证据原样保留；本条取代其中待恢复状态，不修改原输出。T550原全量CSV及nocredit完整证书SHA亦复核一致，未取回完整证书、未重新定价或求解。

16:29:05 UTC只读collect_live.py：5201318仍RUNNING，第467轮PInf0.0197/DInf2.43e-7/Compl1.74e-4；5207165仍RUNNING，第332轮PInf14.1/DInf1.00e-4/Compl0.120。两者AllocTRES=cpu64/mem750G/node1/billing64，UNLIMITED、Restarts0，stderr均0bytes，尚无solve_report。证据case3_2050_preparation_20261026/live_20261026T162906Z.json。未干预运行作业、未启动终态备份或监听。

原任务1–3及本次恢复补项已完成；4–5仍等待上游终态。下一步按NEXT_ACTIONS_ZH.md：2040终态后完整备份、T550证书及扩展评估，B/obj≤1e-2才采纳，再R1/1h/24h/2050参数/冻结/preflight，门禁全通过直接提交release；C2050终态只收尾，C2060/C′等待作者。验证为SSH身份、远端读回SHA、JSON解析、Git明确清单与diff检查；无源码变更，不重复模型测试。仅更新两份报告、恢复/作业JSON及四份交接台账；其他作者稿件和32行SI交接保留未暂存。

## 2026-10-26 框架 B Base-frozen 候选实现与门禁停止

- 源码/证据提交：`ba7a23fdfe76a367ca72eb393daeddc334a9dc13`；明确 56 文件清单见 `supplementary_materials/reviews/base_frozen_B_20261026/ba7a23fdfe76a367ca72eb393daeddc334a9dc13_PATHS.txt`。新增冻结与补表模块、生产候选 profile、runner opt-in、身份/保全分支和 13 个定向测试。原始 Base 表/模型/向量未改。
- 运行位置：T550 `/home/zz2/National_model_server/base_frozen_B_validation_20261026/repo/supplementary_materials/reviews/base_frozen_B_20261026`。独立验证包与私有输入覆盖；没有云端生产部署。
- 命令：`run_gate.py` 的 old-default/default/frozen 1h 与 base-control/zero 24h；`compare_identity_gate.py`；`crosscheck_saved_solutions.py`（只评估保存解、不 optimize）；`python -m unittest discover -s tests -q` 最终 477 tests/159.655s/OK，无跳过。源码 SHA 对齐见 `final_validation.json`，历史失败日志保留。
- 结果：默认关闭 MPS 字节一致；86745 个投资列的 MPS FX 值等于审计；GW clip 合计 2.6415681231e-10，单列最大 2.6414467271e-10。两个对照都 OPTIMAL/保全 COMPLETE，容量误差 ≤2.84e-14，目标相对差 8.67e-16；逐时 VRE 差 8.57 GW、正向潮流差 2.81 GW，任务书身份门禁 1 未通过。双向交叉约束最大违反 3.7169e-11、界违反 4.8743e-12、等成本，支持退化解释；没有替代原门禁。
- 未解决：Cross2/basic 的 relative_v1 为 ERROR（缺 barrier_primal_dual_metrics）。开放柔性 B24h 门禁 2、参数核准、生产冻结/preflight/提交/release 全部未做；无全年性能或验收结论。后续 2040–2060 上游恢复尚须实际包核验，线程等待作者。
- 下一动作：作者决定是否改用目标相等+双向交叉可行性、逐时差异披露的门禁；未明确修订前不推进放行。之后修复 Cross2 QC 兼容性、重新门禁、通过才按原授权提交 2030。保护作业 5201318/5207165 和 case3 2050 未触碰，无凭据读取或后台监听。

## 2026-10-26 框架 B 作者修订后本地门禁全部通过

- **2026-10-26 GMT：作者修订后 B2030 本地全部门禁 PASS，准备生产冻结。** 门禁1按保存 X 补成本分项，最大相对差1.64e-13；变化列 reduced cost≤2.29e-15，原目标差/双向交叉可行通过。Cross2 relative_v1 已修复，basic 语义导出选 X/Pi、Cross0不变；开放柔性24h门禁2容量差≤2.84e-14、relative_v1 PASS、保全 COMPLETE。2030中央参数及“仅投资界变化”原MPS对比 PASS；全套480 tests OK。以 `base_frozen_B_20261026/FINAL_GATES_PASSED.json` 为本地放行依据，下一步独立 B2030 48线程冻结/preflight/held资源核验后直接release；后续年份仍等作者线程确认。

源码起点88bd36f；本次变更 relative_acceptance.py、solution_preservation.py、两测试及 B 验证/部署工具。原CSV来自BarX，已按保存X重算旁置，不改原件；成本和边际成本、参数桥接、完整回归证据均在 B review 第7节。最终480 tests/161.365s/OK；368源码LF SHA对齐。命令 run_t550_checks.py costs / frozen --suffix _basic_v2 / regression --suffix _basic_v2 / parameters。生产包预计 `20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v1`，本条时尚未提交；实际source_commit及资源/Job在部署回执另记。未碰5201318/5207165或case3 2050，无后台监听。

## 2026-10-26 19:43 GMT B2030提交与许可启动失败收尾

- **2026-10-26 19:43 GMT：B2030 Job5276670已提交/release但启动许可失败，停止重提。** 最终源码9f0a042、v2冻结/preflight和481回归/两道身份/参数门禁PASS；m4cg1603实配64CPU/750G/billing64、UNLIMITED。19:39:55–19:39:59 gp.Env.start报旧License2847107过期，尚未构建模型/无output_8760，无全年RSS/轮数指标。部署误沿用旧默认许可；记录已有10-20独立WLS路径，未读凭据，未自动重试。23文件/92,477,291bytes启动失败记录已T550逐项SHA备份COMPLETE，余36.2379%；不是完整解备份。下一步引用已登记WLS路径验证许可并新建v3；保留v1/v2、不重启旧Job、不碰保护作业。详见B review第9节。

- 执行源码：`9f0a042`（修复只读preflight与保全参数互斥），此前实现e2bb4fd、ba7a23f。最终测试481/159.093s/OK；Cross0路径不变，保存X成本项最大相对差1.64e-13、两方向交叉可行≤1e-8、开放柔性24h容量误差2.84e-14、relative_v1 BASIC_CROSSOVER PASS、2030参数与仅投资界改变核验PASS。
- 命令：`deploy_pilot.py prepare`、`preflight`、`submit-release`；405源码与58输入SHA校验，v2 release manifest SHA153d78c95caff43b72ea2a164e7068ca81565c8c4be12d54e4c2420640b7e1b0。held ReqTRES及实际AllocTRES均通过；作业5276670 FAILED/1:0，runtime4秒，no-requeue。≥700GiB检查分支通过但精确内存值未落盘；不将sacct batch MaxRSS=0解释为模型峰值。
- 失败原因：旧默认许可2847107已过期；本轮执行未引用2026-10-20登记的独立WLS，是部署疏漏。已有路径 `/publicfs01/fs1-a8/home/a8s001819/.config/gurobi/licenses/author_wls_20261020_f5e565f5/gurobi.lic`，本轮未读取内容/未再次验证。停止新增提交，不要求作者重新提供凭据，也不把旧许可失败推广为所有许可失效。
- T550：`/home/zz2/National_model_server/cloud_backup/20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v2`，backup_scope=STARTUP_FAILURE_NO_MODEL_OR_SOLUTION；23文件/92,477,291bytes，全部目标bytes/SHA与源前后身份一致。独立operation、全局/本地flock、rsync partial、空间门禁≥30%，完成后余36.2378568%。无output_8760，无有效解/扩展验收，不称完整环境镜像。
- 精确证据/提交清单：`supplementary_materials/reviews/base_frozen_B_20261026/deployment_v2/`、`startup_failure_backup.json`、`COMMIT_PATHS_launch_receipt.txt`；v1 preflight失败及v2许可失败均保留。其他作者未审稿件、32行SI交接仍不暂存。
- 下一动作：按任务失败停止规则回报；新v3应显式绑定现有WLS路径并先过许可门禁，启动资源元数据先于许可检查落盘。不得修改v1/v2/重启5276670。后续年份仍待作者线程决定，5201318/5207165与case3 2050未干预，无后台监听。


## 2026-10-26晚 三项目联合进度

**2026-10-26英国21:44 GMT／10月27日北京05:44：云端3项RUNNING。** Case3 2040/5201318到484轮（6天22:43:20），PInf0.00543/DInf6.62e-8/Compl4.74e-5，较456推进28轮，近474–484三项下降56.56%/55.87%/56.51%，19.43分钟/轮。C2050 t40/5207165到344轮（6天09:19:08），PInf9.72/DInf7.01e-5/Compl0.0826，较324推进20轮，近334–344三项下降28.53%/25.74%/27.54%，26.73分钟/轮；对偶已低于298轮1.07e-4，仍高于297反弹前8.40e-6。新增Base-frozen2030/5276703运行1:42:27，48线程，ordering1343.89s已完成、Barrier第4轮，PInf7.09e11/DInf664/Compl4.07e9，属早期迭代。

Git基准04687e8afa5e070bd46a922bda22647ddc6b8ac3；先枚举完整squeue发现新B2030，再补scontrol/sstat/日志核验，没有遗漏新增项目。Case3/C2050仍未OPTIMAL，三项stderr空、无显式警告/许可错误。前两项Slurm峰712.44/621.18GiB未增加；B2030采样RSS约239.84GiB、峰557.64GiB，不把排序通过当后续峰值保证。证据supplementary_materials/reviews/cloud_joint_progress_20261016/status_20261026T214355Z{,_summary}.json及B2030_status_20261026T2144Z.json。nocredit完整备份沿用10-25最终校验，本次未重复传输/全量校验。

仅更新小证据和三份交接记录，保留其他会话32行handoff及SI改动；未改冻结作业/参数、未建监听或给ETA。JSON解析、明确暂存清单/凭据/diff核验。下一步用户询问时核验三项；Case3 2040终态后按作者10-26新授权进行完整备份、优先T550证书、扩展验收，B/obj≤1e-2时采纳为2050上游，并按R1/v9_a12/Base2050 margin0.2/Aggregate0/40线程/1h与24h及参数门禁全部通过后提交release，同时准备Base2060 margin0.2清单；本轮2040未终态，未启动这些依赖步骤。


## 2026-10-27 三项目联合进度

**2026-10-27英国00:45 GMT／北京08:45：云端3项RUNNING。** Case3 2040/5201318到494轮（7天01:44:30），PInf0.00235/DInf2.47e-8/Compl1.98e-5，较484推进10轮，近10轮三项下降56.72%/62.69%/58.23%，18.68分钟/轮。C2050 t40/5207165到351轮（6天12:20:18），PInf7.93/DInf5.71e-5/Compl0.0672，较344推进7轮，近341–351三项下降27.91%/26.61%/27.51%，26.73分钟/轮；对偶继续回落，仍高于297轮反弹前8.40e-6。Base-frozen2030/5276703到50轮（4:43:23），PInf1150/DInf1.30e-6/Compl116，较4推进46轮；近40–50三项下降92.18%/99.69%/87.90%，3.375分钟/轮，属早期迭代，不据此推全年耗时。

Git基准92432f7fbfb0064074f4453eeaf04c284fe9ca1c；枚举完整squeue并逐项scontrol/sstat/sacct/日志取证。三项均无OPTIMAL/终态、stderr空、无显式警告/错误；Slurm峰依次712.44/621.18/557.64GiB未增加。nocredit完整备份沿用10-25最终校验，本次未重复传输。证据supplementary_materials/reviews/cloud_joint_progress_20261016/status_20261027T004505Z{,_summary}.json。仅两小JSON及CODEX_HANDOFF/MODEL_SERVER_STATUS/SERVER_RUNBOOK追加，其他SI会话内容保留，JSON解析/暂存范围/凭据/diff检查通过，无源码改动不重跑模型测试。未干预在跑作业/冻结包，无后台监听/ETA。下一步询问时检查三项终态；Case3 2040完成后按10-26授权先备份、T550证书及扩展验收，再按门禁推进40线程2050与Base2060筛选清单；本轮未触发终态依赖步骤。


## 2026-10-27上午 Case3 2040及B2030完成，备份连接阻塞

**2026-10-27英国09:48 GMT／北京17:48：仅1项RUNNING，两项新完成。** C2050/5207165到370轮（6天21:23:58），PInf4.24/DInf3.27e-5/Compl0.0369，近360–370三项下降28.86%/27.65%/28.76%，28.24分钟/轮，无新警告/错误。Case3 2040/5201318已于英国02:22:05（北京10:22:05）COMPLETED/0:0，总7天03:21:30，499轮OPTIMAL，目标5057005.849455288 million CNY；Base-frozen2030/5276703于英国06:54:59（北京14:54:59）COMPLETED/0:0，总10:53:17，116轮OPTIMAL，目标4189733.4068938484 million CNY。两者保全COMPLETE/errors=[]。

Git基准e9241075ee896980e35b41236786f173045c27ed（前次GitHub推送网络中断，本轮重试同步）。只读squeue/scontrol/sstat/sacct与终态报告，scontrol/sstat不再返回已退出作业信息属正常，终态以sacct与报告交叉确认。Case3最终打印PInf0.00171/DInf7.58e-8/Compl1.34e-5；B2030为9.65e-5/1.57e-6/1.77e-5。冻结扩展relative_v1：Case3 HARD_FAIL，唯一剩余失败co2_source，最大残差1.0819820274173217e-5 Mt（约10.82t，现行1e-5 Mt约10t阈值）；B2030 PASS，两者原严格HARD_FAIL保留。未修改判据/原报告，不因标签弃用或停止保全，独立验收和筛选证书未完成，未自动晋级2040状态。

证据cloud_joint_progress_20261016/status_20261027T094845Z{,_summary}.json及completed_details_20261027.json（包含每份终态报告bytes/SHA和内容）。T550当前127.0.0.1:22转发拒绝连接、192.168.9.27:22超时；既有备份/活跃传输/磁盘无法核验，因此未创建远端plan或重复启动。新本地配置cloud_backup_20261027/backup_config.json覆盖两新完成release，blocked记录并列；原nocredit等已完成备份不重复操作。

下一步恢复转发后先核manifest/进程/锁/至少30%空间，执行两release单次完整备份、全量bytes/SHA与源身份校验。Case3按10-26预授权优先T550备份上算证书、独立扩展验收并披露CO2项；B/obj≤1e-2时按作者规则采纳后完成2050 R1/v9_a12/Base2050 margin0.2/Aggregate0/40线程及1h/24h/参数门禁，全部通过才提交release，并生成Base2060筛选清单。连接阻塞前不跳过备份身份核验，不改运行C2050，不启后台监听。仅记录/小JSON更新，JSON解析和暂存diff/凭据检查；其他会话内容保留。


## 2026-10-27 T550恢复及两项完成结果备份启动

**2026-10-27英国09:56 GMT／北京17:56：T550转发已恢复，两项终态结果的完整备份已自主启动。** Case3 2040/5201318：93文件5,508,208,350bytes；Base-frozen2030/5276703：97文件5,517,592,632bytes；合计11,025,800,982bytes。Case3 T1（578,199,570bytes）已逐文件bytes/SHA VERIFIED；B2030 T1正在传输，T2/T3及最后源身份复核尚待完成，当前不得称完整备份完成。

Git基准a71a3fcd010eb9383894a211d635ecd932288aae。复用未修改的scripts/backup_completed_cloud.py（SHA cd261143d85b91664b26d8b8582468f7171a64155f5d443ca535b579a2f47658），以新显式config执行plan后run。新操作`/home/zz2/National_model_server/cloud_backup/_operations/20261027_case3_2040_B2030`，独立工具目录`/home/zz2/National_model_server/backup_tools/completed_20261027`。主机t550，原三项完整备份操作均COMPLETE，无活跃同类传输，两新目标不存在；云端inventory复核终态标记、保全COMPLETE和result_manifest。容量门禁通过：原free 1,459,538,599,936bytes，全量后预计35.9467%空闲，高于30%。run PID33104，09:54:54 UTC独立session启动，进程存活，约10MB/s实测传输。单次任务持全局/操作锁，断开本机连接不影响T550到云端自主传输；不是定时监听，不会自动启动求解。

证据：`supplementary_materials/reviews/cloud_backup_20261027/transfer_launch.json`、`progress_latest.json`、`progress_initial.json`、`plan_remote.log`；原blocked记录保留，由本次成功恢复记录纠正。目标为cloud_backup下上述两个release目录，包含全output_8760、BarX/BarPi、原MPS与显式启动身份元数据，无凭据/输入环境镜像。未更改科学阈值、运行C2050或SI模块；Case3 2040原CO2 QC标签保留。

下一步核对transfer_status和两个backup_manifest，全部T1/T2/T3 VERIFIED且source_unchanged才记COMPLETE；连接恢复后先查旧PID/状态，不重用此前未执行的单独2040备份config以免重复传输。之后在完整T550备份上算2040证书、独立扩展验收并同步小JSON；满足10-26预授权条件后执行Case3 2050门禁。Base2060 margin0.2清单实际上已于10-26完成且ready旁置同步已核验（见base_2060_screen_20261026/ready_t550_recovery_20261026.json），此前“生成清单”待办纠正为复核复用。当前未启动证书/验收或2050新求解。无模型源码改动，不重复运行模型测试；本次检查JSON解析、明确暂存范围和diff。


## 2026-10-27 Mt验收修订、结果取回与后续门禁（阶段1）

**2026-10-27作者新增验收/排程阶段1：** Mt采用化石未减排分母，Case3 2040本地/T550重评PASS，验收JSON同步；两项全备份190文件/11.03GB已COMPLETE。Case3/B2030小文件73/78个已取回。B2030最终峰559.893GiB、116轮、相邻轮均288.655s，B三年选48线程。Case3 2050 R1与1h/24h门禁PASS，T550证书计算中；B三年上游三方核验PASS，补表/年度门禁进行中。新生产尚未提交。

Git基准c48630750d3a4e2b36c45513818df9a3fc80b608；修改relative_acceptance/solution_export/frozen_capacity、相关测试与门禁/部署助手，作者AGENTS新增条款同步。全套489 tests OK（Windows跳过Linux /proc一项），Mt相关22项与冻结源10项通过；新模型数值或物理设置未改。详细命令、环境失败保留、身份及精确指标见supplementary_materials/reviews/completed_results_20261027/REVIEW_ZH.md。后续Case3证书合格后冻结40线程release；B2040/50/60各年1h/24h与参数/身份门禁全通过后48线程同时提交放行。最新成功B2030v3为sbatch源，WLS路径字符串核对。5207165只读，不建监听。

## 2026-10-27 阶段2：Case3 2050 已放行；B组门禁停止

源码提交7253a4b（Mt验收与旧状态恢复）、3244f4f（SHA验证云端输入独立复制）已推送GitHub。Case3 2040全年证书B=0、B/obj=0、ACCEPT；作者采纳证书补充记录及原采纳JSON已旁置同步T550，原R1引用不变。B2030新Mt口径复核PASS。Base2060 ready三文件T550 SHA与本地相同，复用旧文件未重复传输。

Case3 2050最终release `20261027_case3_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2`：源码3244f4f，484个冻结文件，release manifest SHA 914f06273382c654e286ef452576d1dad584a4b95826f40952f5f184a3b4e620。58项输入从既有准备目录验证bytes/SHA后复制成独立文件，再次验证；没有指向可变准备层的symlink。原v1上传低速且未完成，主动停止单一scp进程，完整本地payload与云端部分文件保留，v1没有提交。v2云端preflight PASS，held资源核验PASS后按预授权release Job5294579；2026-10-27T13:31:06Z开始RUNNING，Gurobi13.0.2计算节点smoke PASS，cpu64/mem750G/billing64、40线程、UNLIMITED/no-requeue，启动可用内存721.5803GiB。证据在case3_2050_launch_20261027/deployment_v2，入口deploy_authorized.py A2050 prepare|preflight|submit|release|status --version 2。启动通过不等于全年求解通过。

B2040和B2050的1h容量冻结/原Base容量一致性/年度参数均PASS，但24h Base对照均在预求解判INFEASIBLE，原MPS、IIS、所有导出保留。对原MPS只读代入容量会计等式，分别识别12/13项静态矛盾；最大为trunk_capacity_4734的0.002489823815498171GW与trunk_capacity_2349的0.00017961942022282074GW。诊断见base_frozen_followups_20261027/<year>/fixed_capacity_conflicts.json，脚本diagnose_fixed_capacity_conflicts.py；并非修改模型后的求解。B三年按同时提交要求均未提交，不能擅自增加网络容量、扣减冻结发电容量或放松容差。B2060补表正在T550提取，随后核验门禁并补充停止报告。5207165未修改；无后台监听。

## 2026-10-27 阶段3：B三年停止报告及本轮交付

T550三年hydro spur提取COMPLETE，全部补表bytes/SHA和36686个VRE交叉值通过。B2060在1h中发现43项固定容量静态矛盾，最大trunk_capacity_4326为0.00008743143463796343GW，停止在24h之前。B2040/2050为12/13项，最大2.489823815498171/0.17961942022282074MW；两年24h Base对照INFEASIBLE。三年未提交或release。停止报告base_frozen_followups_20261027/STOP_REPORT_ZH.md、STOP_20261027.json、fixed_capacity_conflicts_all_years.csv；各年原模型、IIS及导出保留，INFEASIBLE/IIS工作向量不作为解。下一步由作者决定是否允许固定网络/共享容量的最小闭合；不得自行改冻结定义或门禁，批准后必须新目录重跑全部门禁。

Case3 2050 Job5294579已放行，冻结源码3244f4f、40线程启动检查PASS。Case3 2040已按化石未减排Mt分母重评PASS，全年证书B=0；B2030亦在T550重评PASS。两项完整备份190文件11,025,800,982bytes已逐文件校验且source_unchanged；本地取回Case3 73小文件106,961,807bytes与B2030 78小文件121,288,714bytes。新增验收JSON已从T550回传，作者采纳+证书引用已旁置T550；Base2060 ready三文件同步已核验。B2030峰RSS559.893GiB，116轮，相邻轮均4.8109分钟/中位4.58325分钟，因此B后续48线程选择仍有效，只是科学门禁阻塞。主报告completed_results_20261027/REVIEW_ZH.md；489回归测试OK（1项平台跳过），运行模型源码无后续变更。5207165未修改，无后台监听；其他SI改动未混入提交。

## 2026-10-27 B 最小静态闭合完成；2040/2050 短窗碳门禁停止

Git 基准 eb161d8cb3dd558796884683f79af1365261ed79。按作者本次明确授权追加 AGENTS，新增 cispo_model/frozen_closure.py 与 tests/test_frozen_closure.py，runner 增加显式 --frozen-capacity-closure，容量来源核验分别计入原 clipping 和新闭合；门禁助手增加闭合参数与未压缩 MPS 读取，默认科学配置不变。

新目录 supplementary_materials/reviews/base_frozen_closure_20261027：三年 1h 静态冲突 12/13/43 项全部精确闭合。网络增量 2.799987596/0.181143989/0.154655181 MW，非 CCS bio 减少 9.162058/2.293526/5.957564 W，年度固定成本增加 61596.505660/3954.901821/3543.065116 CNY。逐列仅授权投资界改变，原 Base/冻结审计 SHA 均不变，目标/系数/RHS 分段未变。

B2060 attempt_2 的 1h、3 组 24h、目标/双向交叉可行/成本分项、年度参数和冻结来源全部 PASS。B2040/2050 的 24h Base 对照 INFEASIBLE；IIS 碳排放下界 6.234302872/0.353699641 Mt，高于短窗上限 3.561643836/-0.273972603 Mt。对偶界证明每条 spur/trunk 上界增加 1 MW 后仍不可能闭合碳缺口，不属获授权的逐时网络残差回退。三年均未提交或 release，不单独放行 2060。

命令：prepare_closures.py；run_year_gates.py 2040、2050、2060 --attempt 2；diagnose_iis.py <run> --output <newdir>；audit_derived_models.py；python -m unittest discover -s tests -q。使用 RL Python + Gurobi13 overlay，波浪数据原路径，BLAS 1 线程。19 项冻结测试及 492 项全套串行回归 PASS（1 项平台跳过）；初次并发遇 8 GiB 内存保护失败保留，不降低保护，新目录串行完成。模型测试 SHA 与最终源码一致。

详细 STOP_REPORT_ZH.md、EXECUTION_STATUS.json、closure_summary.csv、derived_integrity.json、各年 derived_static 及 iis_diagnosis_v2、2060/attempt_2/FINAL_GATES_PASSED.json。完整 MPS/IIS/向量本地保留，Git 只同步源码与小证据。只读 squeue 确认 5207165、5294579 仍 RUNNING；未修改二者，不建监听，未重复启动备份。上一阶段 Case3 2040/B2030 的完整备份和验收/证书同步结论沿用，本轮未复核 T550。

下一步：作者与决策层决定短窗年度碳预算门禁处理规则；在新目录按新授权重做受影响门禁，三年全过后才按 48 线程同时提交/release。不得自行放松碳约束或容差。其他会话 SI 修改保留且不混入本轮提交。


## 2026-10-27 第二批 B 独立放行、生产映射修正与失败保全

**2026-10-27 第二批 B 放行：** 云端快照 2026-10-27T21:21:33.430034+00:00 为 5 RUNNING、0 PENDING。B2040/5297384、B2050/5297390 已 release 且启动 smoke PASS；B2060 v2/5297410 已 release 且启动 smoke PASS。三年云端一致映射 1h/3×24h、目标/双向交叉可行/成本门禁 PASS，年度碳上限不变。首次 B2060/5295127 构建闭合核验 FAILED，已完整保全现存文件并 T550 SHA 备份；不是解。

源码80b5c3c→3019462→d14206c→cdd8333；核心模型源码沿用已测版本，本轮修改review助手、作者AGENTS、审计/部署/交接。Windows与生产25个PV最近邻平局选择不同；T550与云端一致，按云端重生成8/12/40行最小闭合，净增成本20.5763/47.0188/243.7888 CNY/yr。三年窗口碳门禁与年度身份通过，生产仅用年度上限。完整命令、环境版本、SHA、测试及未解决项见 supplementary_materials/reviews/base_frozen_batch2_20261027/REVIEW_ZH.md、QUALIFIED_GATES_SUMMARY.json、各年cloud_identity_v2_t550及deployment。

首次5295127失败包T550已备份14,503,317bytes，source unchanged、SHA全过；不是完整解备份。后续新B终态按备份→扩展验收→小文件取回执行，入口backup_B_completed.py/postprocess_B.py，各年config已准备，当前没有新B全年验收。无后台监听、无保护作业/SI修改。


## 2026-10-27 T550恢复、补充回归确认

**2026-10-27 21:25 GMT T550恢复核验：** 云端5项RUNNING；C2050/5207165第396轮，Case3 2050/5294579第7轮，B2040/5297384、B2050/5297390、B2060 v2/5297410仍构建且启动检查PASS。T550遗留筛选CSV已完整到达（7,470,093bytes，SHA fe5d87a2adc6f5d6b8ad21606c571979312c1f632780fcdc9ea7500b7f0f2368），未重复传输；设置与全套回归相同数据环境后，tests.test_production_screen 6项全部PASS，解决上一轮唯一缺夹具报错。

Git基准dd5f382，本轮仅补充证据/交接，无模型源码修改。完整全套第二轮492项中的唯一错误为缺CSV，定向模块6项已通过；保留2项原跳过和全部失败日志，不冒称重新执行整套全绿。首次定向命令遗漏数据环境报provenance输入缺失，补齐既有路径后通过，证据production_screen_recovery_receipt.log与production_screen_recovery_env_receipt.log。失败B2060备份manifest仍COMPLETE，新增备份/后处理入口及三年config已同步T550并SHA核验（t550_recovery_20261027.json），没有启动传输或后台监听。

v2指B2060运行包第二版，模型配置仍v9_a12。首版5295127因Windows与云端25个PV等距离nearest fallback选择不同导致静态闭合来源核验失败，未进入Barrier；按云端一致T550映射重审后在新包5297410运行，不修改最近邻规则、科学容差或年度碳上限。原包完整保全。下一步在用户查询时检查现有作业；遇终态按完整备份→扩展验收→小文件取回执行，无自动监听。


## 2026-10-28 云端五项只读进度核验

**2026-10-28 11:14 GMT（北京19:14）：云端5项RUNNING，无新终态。** B2040/5297384第132轮（PInf0.00532/DInf6.01e-6/Compl1.08e-4），B2050/5297390第145轮（2.72e-4/4.91e-6/5.89e-5），B2060 v2/5297410第159轮（9.33e-4/7.17e-6/6.74e-5）；三者近10轮全部指标改善，均已通过构建/排序进入Barrier，仍未结束。Case3 2050/5294579第43轮（2.58e10/1.48e5/1.18e8），近10轮三项下降54.71%/58.08%/55.03%，23.12分钟/轮。C2050/5207165第427轮（2.37/2.86e-5/0.00367），近10轮三项下降33.95%/10.08%/36.30%，26.90分钟/轮。五项stderr无错误；不据此预估结束时间。

基准提交dbcf010；执行collect_cloud_status.py、sacct与sstat只读查询，无模型/配置/作业修改。证据：supplementary_materials/reviews/base_frozen_batch2_20261027/cloud_status_20261028T111453Z.json、progress_summary_20261028T1114Z.json。B2040/2050/2060近期每轮6.89/6.86/4.82分钟；Slurm batch峰值分别562.80/557.49/547.71GiB（运行中累计值），Case3/C峰值617.82/621.18GiB。无新终态，未启动备份；下一次查询继续核对，终态后按已有授权执行完整保全、T550备份、验收及小文件回传，不建监听。


## 2026-10-28 B三年终态与T550自主备份

**2026-10-28 16:46 GMT（北京10月29日00:46）：云端2项RUNNING，B三年完成。** C2050/5207165第439轮（PInf1.4375/DInf1.91e-5/Compl0.002149），Case3 2050/5294579第58轮（1.8736e10/5.49e4/8.2191e7）。B2040/5297384、B2050/5297390、B2060 v2/5297410均COMPLETED/0:0、OPTIMAL，162/160/178轮，作业耗时17:43:38/15:48:52/15:49:52，保全COMPLETE且errors=[]。T550恢复后16:49UTC已启动三年完整自主备份，PID2538534/PPID1/SID2538534，330文件16,566,391,148bytes，预计余35.4185%；当前RUNNING/T1 TRANSFERRING，不称备份完成。本机可关机，不影响T550直连云端。

Git基准7499490；未修改模型或运行中的5207165/5294579。只读sacct、solve_report、preservation_report、resource_usage与telemetry核对；B三年模型内部峰RSS562.859/562.848/551.809GiB。原始solution_qc仍HARD_FAIL标签，原结果完整保留；尚未完成独立扩展relative_v1验收及小文件回传，不能把OPTIMAL称为验收PASS。

备份复用backup_B_completed.py与backup_completed_cloud.py，全output_8760含原MPS/BarX/BarPi/调度/状态/QC及显式闭合、映射、启动身份元数据。启动前核对无活跃rsync/同类进程、无同名目标或operation；30%空间门禁PASS。独立session、stdin DEVNULL、stdout/stderr写操作日志，持全局锁，逐层rsync/SHA及最终源身份复核；不删源、不复制凭据、不建监听。operation=/home/zz2/National_model_server/cloud_backup/_operations/20261028_B2040_B2050_B2060_completed。

证据：本review目录B_completed_20261028.json、B_all_completed_backup_config_20261028.json、B_backup_launch_20261028.json、B_backup_running_20261028.json、cloud_status_20261028T164644Z.json。最初转发拒绝连接，作者恢复后成功启动；未重复备份旧失败v1。下一次连接先看旧PID、transfer_status、三份backup_manifest；全部COMPLETE且source unchanged才报告完成。随后对三年执行postprocess_B.py B2040|B2050|B2060 assess及collect，回传nocredit同清单≤32MiB文件，验收JSON按来源SHA旁置同步。不要重复plan/start，也不因自动QC标签放弃任何保全。

## 2026-10-28 B三年验收、T550初步分析与本机归档入口

**2026-10-28 收尾：B2040/2050/2060 完整备份及扩展验收完成，初步分析在 T550。** 三年330文件16,566,391,148bytes备份于17:26:52 UTC完成，九层VERIFIED且source_unchanged；独立relative_v1（10-27 Mt口径）均PASS，三套验收JSON已同步本机/T550，原QC保留。18:48GMT只读云端2项RUNNING：C2050/5207165第444轮（PInf1.1663/DInf1.53e-5/Compl0.001693），Case3 2050/5294579第63轮（1.65e10/4.02e4/7.12e7）。T550汇总11个已解案例；仅取回606,996bytes压缩包，101载荷文件2,991,005bytes，包和逐文件SHA通过。本机case_results统一索引15个案例版本，原件未移动/删除。

- Git基准099e5ae；本记录所在提交新增两项整理工具、case_results索引/解读/验证、B三套验收证据与T550清单，未改模型或生产release。最终提交号由包含本条的Git提交追溯。
- 执行：`postprocess_B.py B2040 assess`、B2050/B2060同式，在T550完成；`build_t550_compact_analysis.py --backup-root /home/zz2/National_model_server/cloud_backup --output /home/zz2/National_model_server/cloud_backup/_analysis/20261028_compact_case_results_v1`；本机`organize_local_case_results.py`只建索引。上述工具在supplementary_materials/reviews/base_frozen_batch2_20261027/。
- 备份复核先查既有operation/manifest/传输，确认COMPLETE且无活跃任务，未重复启动。T550剩余1,427,141,468,160bytes（约35.4%）。完整output_8760与显式启动元数据保全，不宣称含全部输入环境镜像。
- 本轮用户要求取回文件小、初步分析在T550，替代此前本轮收尾默认nocredit全清单收集：采用显式≤1MiB文件白名单，不取逐时数组/BarX/BarPi/MPS。原大文件仍在T550，未省略完整备份。压缩包SHA ebfc296ee5ed6eba70c6fc6b824d3c803134290de51eef78bbb6f1dbf829ed79。
- 证据：本review下T550_inventory_20261028.json、compact_analysis_execution_v1.log、B2040/B2050/B2060/assessment及assess_receipt.json；case_results/delivery_receipt_20261028.json、organization_validation_20261028.json；云端cloud_status_20261028T184833Z.json。
- 初步B成本区间与柔性物理量见case_results/PRELIMINARY_FINDINGS_ZH.md。B未筛选，使用作者Barrier工程区间，不作为统计区间或严格嵌套可行域证明；各年科学采纳仍由作者决定。其他历史PASS按各自验收日期/口径保留，不称全部新口径重评。
- Git仅保存工具/索引/小审计；压缩包与完整小交付载荷保存在本机/T550，不随Git上传。原reviews路径不动，15卡包括11已解、2运行、2已备份失败；未列旧诊断仍在原目录。其他会话SI修改不纳入本提交。
- 验证：101载荷SHA、15卡、全部显式本地Markdown链接、三年验收JSON双份一致、两工具AST及Git差异检查。无模型修改，未重跑大型模型测试。
- 下一步：作者查看统一索引和初步分析；下次询问只读查看两在跑任务，新终态按10-20规则备份/扩展验收，并优先T550分析后取回小结果。不新建监听、不干预5207165/5294579、不动SI/在线LaTeX。

## 2026-10-29 10:30 GMT 云端只读进度

**2026-10-29 10:30 GMT（北京18:30）：云端2项RUNNING，无新终态。** C2050/5207165第482轮，运行8天22:05:17，PInf0.08179/DInf4.91e-6/Compl1.0438e-4；472→482三项下降58.02%/48.55%/58.83%，约25.41分钟/轮。Case3 2050/5294579第105轮，运行1天20:58:58，PInf3.65e9/DInf1467.65/Compl1.516e7；95→105下降36.09%/68.58%/36.58%，约23.00分钟/轮。两者stderr为空，仍未完成；不由互补性数值推断终止或ETA。B三年仍COMPLETED，既有完整备份与扩展PASS记录不变，未重复传输。

基准16c3d30；复用collect_cloud_status.py和sacct只读核验，无源码/模型/作业修改。证据supplementary_materials/reviews/base_frozen_batch2_20261027/cloud_status_20261029T103003Z.json；比上次18:48快照分别推进38/42轮。无新终态，未触发新备份。下一次询问继续只读核对，终态后按长期授权保全、T550备份验收及小文件回传；不建后台监听。

## 2026-10-29 C2050终态与备份待恢复

**2026-10-29 19:09 GMT（北京10月30日03:09）：云端1项RUNNING，C2050已完成。** C2050/5207165于16:28:53GMT（北京10月30日00:28:53）COMPLETED/0:0，总9天04:04:06，496轮OPTIMAL，目标5700892.181056213 million CNY，峰值RSS623.282GiB；保全COMPLETE/errors=[]，原模型已归档。最终PInf0.02918/DInf2.17e-6/Compl3.34e-5，旧10-14 relative_v1 HARD_FAIL（co2_source及solver原始残差>0.01）；10-27独立复评/筛选证书尚未执行，不自动采纳或放行2060。Case3 2050/5294579第129轮，运行2天05:38:15，PInf3.319e8/DInf4.760/Compl1.410e6，近10轮下降67.99%/89.88%/68.21%，22.12分钟/轮，stderr空。T550转发连接拒绝，备份配置已准备，尚未计划或启动传输，已请作者恢复。

Git基准bf72d8e；只读squeue/sacct及solve/preservation/QC/result_manifest核验。证据C2050_completed_20261029/terminal_evidence.json、qc_failed_checks.json、backup_config.json；队列证据base_frozen_batch2_20261027/cloud_status_20261029T190921Z.json。结果manifest为46e39579d1d5ef4bcef80d722e4586a0c92b10019920db2a2ae5a051fbbf035c，80条5,509,265,018bytes；这只是结果manifest合计，完整备份还需启动元数据，未冒称最终计划规模。无模型/运行作业变更，不因QC标签放弃保全。

下一步：T550恢复后先查既有manifest/operation/锁/进程及30%余量；复用scripts/backup_completed_cloud.py，操作20261029_C2050_completed，仅一次自主拉取全部output_8760与明确启动元数据，分层SHA及源身份核验完成后再称完整备份。随后复用postprocess.py的assess/price，对C2050独立Mt验收及筛选证书在T550计算，只回传小JSON/汇总，不跑旧collect全清单。原始PInf门槛仍为0.01，不能仅以Mt更新推断PASS。不得自动启动C2060、不得触碰Case3在跑包；无后台监听。

## 2026-10-29 T550恢复后的连接复核

**2026-10-29 作者恢复T550后复核：** 本机127.0.0.1:22已由GameViewer监听，但三次SSH握手前均Connection reset；内网192.168.9.27:22超时，尚未登录T550。C2050备份plan/run及验收/证书均未执行，不宣称传输启动。已请作者重连T550会话或端口映射。

基准a370afe；证据C2050_completed_20261029/t550_reconnect_check_20261029.json。新增postprocess_C.py复用已有T550独立评估器，仅允许C2050 assess|price并要求完整备份manifest；已过AST语法检查，远端尚未执行。连接恢复后先查旧manifest/operation/活动传输与锁，复用backup_config.json安排一次自主全备份，校验后运行postprocess_C.py C2050 assess及price；本机只收小JSON，禁止旧collect全清单。未改变模型、源归档或在跑Case3；无后台监听。

## 2026-10-29 C2050收尾暂停与后续排程核对

**2026-10-29 作者暂缓C2050备份：** 本次明确要求后续确认后再备份；不再因T550连接恢复自动plan/run。此暂停仅针对本次C2050待执行备份，长期终态保全规则不变。框架C的2050→2060总体路线已有共识，R1/40线程/Base2060 margin0.2清单规则已有；当前未发现C2060独立启动任务书或直接release预授权。

核对依据：AGENTS.md 2026-10-12晚/10-19/10-26节，RESEARCH_DESIGN_CONSENSUS_20261012.md第1节，claude_workspace/tasks/TASK_case3_launch_contract_20261010.md第4–5节及PROMPT_release_nocredit_case3_2040_C2050_20261019.md第4节（该release授权仅C2050）。Base2060筛选就绪记录base_2060_screen_20261026/ready_t550_recovery_20261026.json为VERIFIED_COMPLETE。

下一步顺序：等待作者确认备份→T550完整备份及SHA→最新Mt口径独立验收与C2050自身对偶筛选证书→作者采纳2050上游→明确C2060启动合同/授权→C2050状态经R1续接2060、v9_a12/Aggregate0/40线程、1h/24h/参数与身份门禁→冻结、preflight和held检查点；未获C2060明确直接release授权前不自动放行。C2050的旧QC HARD_FAIL并不自动要求重跑，也不自动允许采纳；PInf0.02918>0.01仍需如实披露。待A2050完成后比较A/C2050，C′是否追加按作者10-19分步设计决定，不自动新增。

本轮仅查文档并记录最新用户暂停，备份配置增加execution_gate说明字段（既有备份脚本不自动执行该字段，操作者必须遵守），无SSH重试、无传输、无构建或提交。基准fab9811；变更为交接/状态与备份配置。

## 2026-10-29 C2050自主备份启动

**2026-10-29 19:26 GMT C2050备份已自主启动。** 作者“再次尝试t550备份”解除本次等待确认；连接恢复后已确认无同名目标/operation、无活跃传输、全局锁可用。新计划105文件5,511,013,265bytes，完整T1/T2/T3含原MPS及显式启动元数据，30%余量门禁PASS，预计余35.2781%。PID351788/SID351788独立session、stdin DEVNULL，当前RUNNING/T1 TRANSFERRING，尚未完成校验；本机断线不影响T550直连云端任务。

基准037faa2；新增backup_C_completed.py复用既有全局锁/可续传/逐文件SHA/最终源身份核验引擎，仅扩展明确启动文件清单并检查用户授权标记。旧待确认backup_config.json保留为历史，新执行配置backup_config_authorized_20261029.json。工具部署独立/home/zz2/National_model_server/C2050_completed_20261029_tools，未覆盖旧工具或原输出；新操作cloud_backup/_operations/20261029_C2050_completed。

证据：本review目录backup_plan_execution_20261029.log、backup_launch_20261029.json；已核result_manifest SHA46e39579d1d5ef4bcef80d722e4586a0c92b10019920db2a2ae5a051fbbf035c。脚本AST通过，执行工具逐文件SHA留档。完整源不含输入环境镜像，不复制凭据。无模型/在跑作业变更、无后台监听。下一次查询先核现有PID/transfer_status/backup_manifest，禁止重复plan/start；三层全部VERIFIED且源身份未变才称完成，再在T550做assess/price，仅回传小JSON。本轮没有启动C2060。
