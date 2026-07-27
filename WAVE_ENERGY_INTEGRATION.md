# 波浪能 Base 集成

更新时间：2026-07-27

## 1. 当前模型边界

波浪能已纳入 `base`，与陆上风、海上风和光伏同为默认供给侧技术；它不再通过单独
scenario 启用。`flexible_load_comfort_v3_v2g_5pct` 仅在这个波浪整合 Base 上附加需求
柔性。运行任一情景均必须设置：

```powershell
$env:CISPO_WAVE_ROOT = 'D:\codeenv\pycharmproject\National_RL\wave_energy'
```

波浪仍不进入 `VRE_TECHS`，也不建立第二套空间网格。它只在
`data/vre/optimization_points.csv` 已有且 `is_land == 0` 的 marine `grid_uid` 上创建
连续容量扩建选项；省份、变电站和 `city_337` 负荷中心路由均精确复用同一 `grid_uid`。

## 2. 数据合同

原始 CF 文件为：

```text
D:\codeenv\pycharmproject\National_RL\wave_energy\wave_grid.nc
```

该数据包含 2023 年完整 8,760 小时、4,194 个原始格点及 10 套情景 CF。经过最大
`0.02 degree` 坐标交集和现有 marine-grid 限制后，运行合同保留 1,285 个既有
`grid_uid`、其中 1,284 个有正潜力，原始潜力合计 9,798.111 GW；57 个保留格点的 CF
带插补标记。禁止以最近海上风电格点代替原始波浪格点。

运行时输入为 `data/wave/wave_sites.csv`，由
`scripts/build_wave_energy_inputs.py` 生成；小时 NetCDF 保持外部，绝不复制到输出根。

## 3. 数学与可靠性处理

对海洋格点 `i`：

\[
K_i^{wave}=K_{i,inherited}^{wave}+K_{i,new}^{wave},\qquad
0\le K_i^{wave}\le f_{potential}K_{i,raw}^{wave}.
\]

省级逐时出力满足：

\[
0\le g_{p,t}^{wave}\le\sum_{i\in p}CF_{i,t}^{wave}K_i^{wave},
\]

并直接进入严格省级小时平衡。波浪不提供容量信用、备用或同步惯量；其实际出力按
`reserve_requirement_fraction=0.05` 增加上下备用需求。项目成本采用基准 CAPEX 加水深与
离岸距离加成，且不共享海上风电 spur/trunk，以避免未建模的共用送出决策。

## 4. 年份与证据限制

2030/2040/2050 使用 medium profile/cost；2060 明确沿用 2050。`potential_fraction`、
插补 CF、水深/离岸距离筛选、汇率和成本本地化仍是待校准假设。波浪进入 Base 是用户
确定的模型边界，不表示上述参数已经获得独立科学验证。

旧的波浪单模块/组合 scenario 及其短时结果已从 catalog 删除；既有输出保留为历史
工程证据，不能与新 Base 直接比较。新 Base 的 24h/168h/8760h 必须使用新输出根重新
验收；静态 preflight 不是 Barrier 内存可行性证明。
