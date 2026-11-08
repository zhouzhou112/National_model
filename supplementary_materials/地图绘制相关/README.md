# 地图绘制资源与成图约定

核验日期：2026-11-08，英国时间。用途：给后续 Codex 地图任务提供本机资源、运行入口和成图标准。本目录是技术交接，不是论文正文，也不表示已有图件已获作者最终审美验收。

**推荐：使用本机 RL Python，以 Module 03 的 `china_layers()` / `finish_map()` 为地图底层参考，按 `midterm_base_v3` 的最新线性、英文、无说明脚注风格编写新脚本。输出放到新任务目录。** CRF 和 FileGDB 的读取核验交给 ArcGIS Pro Python。不要直接重跑会覆盖既有图件的整包脚本。

## 阅读入口

| 文件 | 内容 |
|---|---|
| [01_地图绘制原则与成图标准.md](01_地图绘制原则与成图标准.md) | 已确定规范、精确地图范围、色标与尺寸、数据表达边界、交付检查 |
| [02_本机资源与运行环境.md](02_本机资源与运行环境.md) | 完整本机路径、数据版本、参考脚本、解释器及可运行检查命令 |
| [03_Codex地图任务交接模板.md](03_Codex地图任务交接模板.md) | 可直接复制给后续 Codex 的任务要求 |
| [resource_inventory.csv](resource_inventory.csv) | 资源绝对路径、存在性、用途、部分文件 bytes/SHA256 |
| [scripts/audit_local_resources.py](scripts/audit_local_resources.py) | 可重跑的本机只读资源核验；仅写本目录的清单和 evidence |
| [evidence](evidence) | 环境导入、坐标系、几何、表结构、网格集合与 ArcGIS 读取证据 |

## 已核验结论

- 资源清单中的路径全部存在；清单目录存在不等于其中每个大型栅格均完成读取或校验。对 GDB 两个要素类和一个代表性 CRF，已用 ArcPy 额外读取。
- 标准投影为 Albers 等积圆锥投影（Albers Equal Area Conic），`Asia_North_Albers_Equal_Area_Conic`；两处历史 `.prj` 路径均存在，坐标参考系（Coordinate Reference System, CRS）等价。
- 上游综合点 `final_pointV2` 为 **16,739 行、37 列**；模型 `optimization_points.csv` 为 **16,609 行**；`out_of_scope_points.csv` 的 **130 行**恰好等于二者集合差，主键均唯一。
- 标准省界包含 **34 个要素**，模型为 **31 省**；二者不能通过行号对应。城市负荷中心 **337 个**、省内代理边 **642 条**；这些是当前本地输入计数，不代表电气母线或完整实际线路。
- 已有风光装机当前上游版本为 `osm_geometry_value_added_capacity_v3_offwind47`；旧技能中的 v2 路由已经落后于本机 Module 01 脚本及 `final_pointV2` 报告。陆风约 593 GW、海风约 47 GW、集中式光伏约 670 GW、分布式光伏约 530 GW；精确求和在 `evidence/table_checks.json`。
- RL 环境可导入 matplotlib、GeoPandas、pyproj、Rasterio、pyogrio、LERC、Pillow、pypdf；缺 Fiona 和 PyMuPDF，不妨碍此次已验证的 pyogrio 省界读取及常规绘图。旧 `package_atlas.py` 的完整运行依赖尚未验证。

## 需保留的差异和限制

1. **最新风格决定优先。** `midterm_base_v3/README_ZH.md` 明确记载作者要求不再用 Nature 系列绘图技能，参考 `journal_codex_v2`，英文图内文字、尽量线性、无说明性小字。旧技能和 `journal_codex_v2` 代码仍保留非线性色标、脚注等历史实现，不能原样当成最新规范。
2. **南海插图在右下。** 2026-07-11 模板及现有函数已取代早期“左下角插图”计划；左下用于比例尺。
3. **省界几何和名称需注意。** 默认读取发现一个环自相交：`gb=156230000`，行索引22，位置约 `(133.865512, 46.509559)`；默认中文名称含替换字符。尝试 GBK 可辨认该项为黑龙江省，但其他名称仍有编码警告，不能简单全局改编码即宣称修好。按 `gb` 映射模型省码；需要叠置运算时只在派生副本处理无效几何并核验修复影响，不覆盖原始 shapefile。
4. **“九段线”是文件名，不是读取行数约束。** 当前源文件有10个要素，应完整保留，不按名称擅自删成9行。其源CRS为 Beijing 1954 / China Lambert Conformal Conic，不能误标为WGS84；重投影已成功，未验证测绘级大地基准转换精度。
5. 此次没有新画科学图、没有重新求解、没有刷新云端状态、没有更改模型数据或正式模块。所列历史图与脚本是参考，不是当前全部情景结果的自动科学验收。

## 依据与状态

事实依据优先采用本地脚本、最终数据报告及本次核验。主要规范来源：`SUPPLEMENT_WORKFLOW_GUIDE_ZH.md` 第8节、Module 03 地图函数、全局 `supplementary-materials/references/china-map-template.md`、`midterm_base_v3/README_ZH.md`。它们的完整路径及适用边界见资源说明。

本次只新增此目录。项目已有其他未提交文件及 `CODEX_HANDOFF.md` 改动未纳入本目录交付。本机资源文档不会使引用的本地 GIS 大文件随 Git 自动发布；换机器需按清单另行准备数据。
