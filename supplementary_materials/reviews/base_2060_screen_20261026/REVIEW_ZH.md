# Base 2060 筛选清单（2026-10-26）

在 T550 完整备份上运行原 `scripts/build_vre_screen_list.py --margin 0.2`，来源 `20261012_base2060_v9a12_t48_m750_tol1e4_v1`。原 MPS SHA `c37a99082d8a9ab29ddb9c6580b25c399320546571aa2386738e42966fb8f29e`，BarPi SHA `052b8623a580a53acd54dbbcded9e44f7369985898d68ef5d75a3d3b828d077d`。MPS、BarPi、checkpoint指纹和语义表身份均已核验；完整文件保留T550。

与 P4 2040/2050 使用相同的配对约化成本、费用分母、正余量与 margin0.2 判据。复用 `audit_p4_screens.py`，仅增加2060年份与显式来源参数；算术、唯一稳定键、源身份、原顺序及反序调用实际 `apply_vre_screen` 均 PASS。无模型构建或优化。

- 全部站点×技术：36686；有正扩展余量：33773；无余量：2913。
- 按 Base2060 原余量筛掉：8025；保留可扩展：25748。
- 全量定价表：`source_screen.csv`，SHA `53f9bfc05c1a986cff0f4151f557df21f2a9c9beae607fc1b027ecf64a1d3dfb`。
- 生产三列清单：`ready/source_screen.csv`，SHA `831514fdb19da9ffa0a4ccca40def435a3972f37db00284524916c1d8b6c9fc3`；生产profile片段：`ready/candidate_screen_fragment.json`。

这些计数只描述 Base2060 的原余量，不代表尚未构建的 case3/C2060 最终候选数；应用时仍须逐一按 grid_uid×technology 对齐并使用未来模型实际新增上界。清单生成不授权case3/C2060求解，也不改已完成Base2060的全候选模型。

全量CSV与来源小证据留本机/T550，Git发布生产清单、身份与审查。`source_evidence/download_identity.json` 是远端核验描述文件，明确大型原件仅在T550，不能解读为已下载本机。复现命令与返回SHA见 `screen_receipt.json`，原manifest/工具身份见 `screen_identity.json`。

生产三列清单已在本地核验并随Git交付；额外复制到T550的ready/旁置目录时连接中断，后续只读检查也在SSH banner阶段超时，目标状态未确认。原始全量清单/identity已在T550完成并核验，不受影响；恢复连接后先检查ready/，逐字节相同则复用，不盲目覆盖。
