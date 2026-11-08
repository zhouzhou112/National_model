# 可复用全国地图模板

推荐使用 `china_map.py`，无需导入模型或旧论文模块。它直接读取已确定的省界、投影及九段线，支持格网、点、分省填色和连线；输出固定尺寸 PDF 与450 dpi PNG，保留字体、作图数据和检查记录。

按作者2026-11-08本轮纠正，地图构件以已审核的模块01、模块03为直接模板。具体函数、参考成图与沿用参数见上级目录的 `已审核模块样式对照.md`。不以未通过作者审核的新样式替换现成模板。

## 入口与目录

| 脚本 | 作用 |
|---|---|
| `china_map.py` | 独立命令行单图和可导入的 `ChinaMap` 类 |
| `build_example.py` | 现有风光装机四技术示例；16,739个上游网格 |
| `build_base2060_atlas.py` | 已核验Base2060结果的15张专题图；只读本机原始／派生结果 |
| `review_outputs.py` | PDF实际渲染、页面文字边界检查、PDF/PNG对照、15页合并地图册和中文浏览页 |

图件目录均为中文：`地图绘制相关\示例图_现有风光装机` 和 `地图绘制相关\Base2060全要素图集`，后者按11个中文主题子目录组织。源码、操作指南可随Git复用；大图、作图数据和研究性解读仅保留本地，不自动公开发布。

## 一条命令绘制单图

已实际运行下列命令，可直接重现单图示例：

```powershell
& 'C:\Users\ZZ\.conda\envs\RL\python.exe' 'D:\codeenv\pycharmproject\National_RL\National_model\supplementary_materials\地图绘制相关\通用模板\china_map.py' --csv 'D:\codeenv\pycharmproject\National_RL\National_model\supplementary_materials\地图绘制相关\示例图_现有风光装机\现有风光装机_四技术示例_作图数据.csv' --value existing_onwind_mw --kind grid --title 'Existing onshore wind | 2025' --unit 'Capacity (MW / 0.25 degree cell)' --output 'D:\codeenv\pycharmproject\National_RL\National_model\supplementary_materials\地图绘制相关\示例图_现有风光装机\单图模板示例\陆上风电_单图'
```

`--output`为不带扩展名的文件前缀。自有数据可替换CSV、字段、图题、单位和输出位置。必要列：

- `--kind grid`：`grid_uid, lon, lat, <value>`，每格一行、主键唯一，格心必须满足本项目0.25°网格定义；不把不同技术重复格点直接传入。
- `--kind point`：`lon, lat, <value>`；按真实坐标绘制点，勿把省级量伪装成站点。
- `--kind province`：`province_code, <value>`，省码唯一。缺数据地区显示灰色斜线背景，不能自动填零。
- `--palette blue/red/teal`：非负顺序数据；`--palette diverging`：有正负意义的差值，零中心对称色标。
- 可用 `--provinces`、`--nine-dash`、`--projection`覆盖路径，换机器时保持同一文件版本并核验SHA。

命令不会自动换算MW/GW，也不猜测字段含义。默认保留全部值，不做1MW过滤、异常值截尾或对数变换。带负数而未显式使用有符号色标时停止；全零数据使用单一0刻度平色色条，不生成虚假数值跨度。

## Python多面板接口

以下是可运行的双面板例子。它读取已生成示例CSV，输出到新的中文目录：

```python
from pathlib import Path
import sys
import pandas as pd

root = Path(r"D:\codeenv\pycharmproject\National_RL\National_model\supplementary_materials\地图绘制相关")
sys.path.insert(0, str(root / "通用模板"))
from china_map import ChinaMap, figure_grid, colorbar, export

data = pd.read_csv(root / "示例图_现有风光装机/现有风光装机_四技术示例_作图数据.csv")
maps = ChinaMap()
cells = maps.cells(data)
fig, axes = figure_grid("Existing capacity | 2025", rows=1, cols=2)
for ax, field, title, palette in [
    (axes[0], "existing_onwind_mw", "a  Onshore wind", "blue"),
    (axes[1], "existing_cpv_mw", "b  Utility PV", "red"),
]:
    maps.frame(ax, title)
    norm = maps.grid(ax, cells, field, palette)
    colorbar(fig, ax, norm, palette, "Capacity (MW / cell)")
export(fig, root / "自定义示例/陆风与集中式光伏", data)
```

其他接口：

| 接口 | 输入／用途 |
|---|---|
| `maps.points(df)` | WGS84经纬度转目标投影 |
| `maps.cells(df)` | 以格心±0.125°重建真实地理格网后投影 |
| `maps.province(ax, df, column, palette, signed=False, norm=None)` | 以省码连接，不使用乱码中文名称 |
| `maps.point_values(ax, geo, column, palette, norm=None, size=9)` | 固定点大小、颜色表达数值 |
| `maps.province_segments(df)` | 以省级内部代表点构造代理通道，非实际线路走向 |
| `maps.lines(ax, segments, values, palette, arrows=False)` | `segments`形状为`(n,2,2)`的目标投影坐标；线宽与颜色线性编码绝对值，正负控制箭头方向 |
| `linear_norm(values, signed=False, limits=None)` | 创建线性色标；显式范围不得截掉值，跨面板可传同一个norm |
| `maps.audit()` | 源文件SHA、投影、插图范围、几何修复记录 |
| `export(fig, stem, data=None)` | 输出PDF/PNG和检查JSON，可附作图CSV |

`figure_grid`固定宽7英寸：1×2为3.5英寸高，2×2为6.3英寸高，3×2为8.6英寸高，单图为6.2英寸高。单栏85mm或其他排版可自行建Figure，但仍调用`frame/colorbar/export`并通过尺寸及视觉检查。每指标需要共同色标时由调用方传统一norm；模板不会将不同指标自动混到一个范围。

## 本次模板落实的地图检查

- 省界、九段线和数据全部转换到原 `.prj` 的Albers等积圆锥投影，`always_xy=True`，输出检查实际x/y比例一致。
- 主图按既定海南以南截断、横向紧凑范围，南海插图固定右下；完整保留线文件10个几何要素，并纳入相关岛屿背景范围，不在插图叠加定量数据。
- 指北针、比例尺、南海插图及蓝红青色阶沿用模块01/03。比例尺为水平“0—500 km”，长度500000投影米；箭头沿投影北直立。二者是既有模块的制图约定，不声称全国各位置均为精确真北或无距离变形。
- 构件在数据图层完成后统一添加；固定主图范围和等投影比例，逐面板检查标尺水平、指北针直立及二者都在画框内，避免后续图层改变布局。
- 省界无效几何只在内存中 `make_valid`，不改源文件；前后面积与省码写入底图审计。
- 默认无解释性图内脚注；图题、变量标签和数值／单位正常保留。方法和限制放在每张图旁的中文图注。
- `export`检查可见文字在画布内、投影等比例、PDF MediaBox、PNG像素、字体嵌入；PDF实际渲染还需运行`review_outputs.py`并人工看图。

## 重现整套成果

```powershell
& 'C:\Users\ZZ\.conda\envs\RL\python.exe' 'D:\codeenv\pycharmproject\National_RL\National_model\supplementary_materials\地图绘制相关\通用模板\build_example.py'
& 'C:\Users\ZZ\.conda\envs\RL\python.exe' 'D:\codeenv\pycharmproject\National_RL\National_model\supplementary_materials\地图绘制相关\通用模板\build_base2060_atlas.py'
```

Base图集脚本的`--only 1,3`可单独重画选定主题。主题编号：1风光两页，2储能，3省际输电，4省内网络与接入两页，5地区供需，6常规电源，7水电波浪，8碳核算和CCS输入两页，9区域信号，10总览，11地区组合，12接入距离。编号是脚本参数，不等于图件文件夹排序。

这些命令只重写本模板生成的输出，不会覆盖原生产数据或旧模块。科学结果路径固定为本次核验的Base2060 release及对应只读回传，不能只改标题变成别的情景。新情景应先扩展路径配置、验证身份和字段，再生成新目录。

PDF检查使用带 `pymupdf`、NumPy、Pillow 的Python。本机RL缺PyMuPDF；本次使用Codex bundled Python，实际路径由 `load_workspace_dependencies`工具给出。不要把某次bundle绝对版本路径当永久运行依赖，不需为此改RL环境。先找到可导入`pymupdf`的Python，再运行 `review_outputs.py`；它仅写本目录。

## 交付边界

图件QA通过表示文件、地理构成和本次数据连接／合计检查通过，不等同于作者审美采纳或全部科学假设已验证。Base2060的水电输入问题、工程对偶口径和原解数值残差仍须随图注保留。新增场景必须继续检查，而不能复用这次PASS标签。
