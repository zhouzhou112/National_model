param(
    [string]$ArchiveRoot = "E:\数据拷贝\National_model基准情景数据_20260825_v1",
    [string]$Python = "C:\Users\ZZ\.conda\envs\RL\python.exe"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if (Test-Path -LiteralPath $ArchiveRoot) {
    throw "归档目录已存在，拒绝覆盖：$ArchiveRoot"
}

$NationalRoot = "D:\codeenv\pycharmproject\National_RL"
$ModelRoot = Join-Path $NationalRoot "National_model"
$SuitableRoot = Join-Path $NationalRoot "Gis_process\suitable_area"
$PowerCurveRoot = Join-Path $NationalRoot "Power_curve_V2"
$InstalledRoot = Join-Path $SuitableRoot "installed_capacity_2026_landuse_grid_assessment"

function New-ArchiveItem {
    param(
        [string]$Source,
        [string]$Destination,
        [string]$VersionRole
    )
    [PSCustomObject]@{
        Source = $Source
        Destination = $Destination
        VersionRole = $VersionRole
    }
}

$Items = @(
    New-ArchiveItem (Join-Path $SuitableRoot "intermediate\run_current_v3\rasters\master") "01_风光适宜性与潜力_土地利用精细栅格\01_主土地利用栅格" "current project_config.py master"
    New-ArchiveItem (Join-Path $SuitableRoot "intermediate\run_current_v3\rasters\cell_area_km2.crf") "01_风光适宜性与潜力_土地利用精细栅格\02_像元面积\cell_area_km2.crf" "current pixel-area raster"
    New-ArchiveItem (Join-Path $SuitableRoot "intermediate\run_current_v3\rasters\factor_rasters_v2") "01_风光适宜性与潜力_土地利用精细栅格\03_土地利用因子_v2" "current project_config.py factor directory"
    New-ArchiveItem (Join-Path $SuitableRoot "intermediate\run_current_v3\rasters\natural_masks_v2") "01_风光适宜性与潜力_土地利用精细栅格\04_自然条件掩膜_v2" "current project_config.py natural masks"
    New-ArchiveItem (Join-Path $SuitableRoot "intermediate\run_current_v3\rasters\protection_masks") "01_风光适宜性与潜力_土地利用精细栅格\05_保护区与生态掩膜" "current project_config.py protection masks"
    New-ArchiveItem (Join-Path $SuitableRoot "intermediate\run_current_v3\rasters\access_masks_v3") "01_风光适宜性与潜力_土地利用精细栅格\06_基础设施可达性掩膜_v3" "current project_config.py access masks"
    New-ArchiveItem (Join-Path $SuitableRoot "intermediate\run_current_v3\rasters\offshore_masks") "01_风光适宜性与潜力_土地利用精细栅格\07_海上风电掩膜" "current project_config.py offshore masks"
    New-ArchiveItem (Join-Path $SuitableRoot "intermediate\run_current_v3\rasters\area_rasters_v3") "01_风光适宜性与潜力_土地利用精细栅格\08_最终适宜面积栅格_v3" "current project_config.py area rasters"
    New-ArchiveItem (Join-Path $SuitableRoot "outputs\final_rasters_v4") "01_风光适宜性与潜力_土地利用精细栅格\09_最终面积与容量栅格_v4" "final raster export v4"
    New-ArchiveItem (Join-Path $SuitableRoot "scripts") "01_风光适宜性与潜力_土地利用精细栅格\10_复现脚本" "current suitability scripts"
    New-ArchiveItem (Join-Path $SuitableRoot "logs") "01_风光适宜性与潜力_土地利用精细栅格\11_运行日志与QA" "current suitability logs"
    New-ArchiveItem (Join-Path $SuitableRoot "outputs\final_grid_suitability_v4.gdb") "02_风光潜力与已有装机_0.25度网格\01_适宜性潜力\final_grid_suitability_v4.gdb" "final 0.25-degree geodatabase v4"
    New-ArchiveItem (Join-Path $SuitableRoot "outputs\final_grid_suitability.csv") "02_风光潜力与已有装机_0.25度网格\01_适宜性潜力\final_grid_suitability.csv" "final 16,739-grid table"
    New-ArchiveItem (Join-Path $SuitableRoot "outputs\summary_by_province.csv") "02_风光潜力与已有装机_0.25度网格\01_适宜性潜力\summary_by_province.csv" "final provincial summary"
    New-ArchiveItem (Join-Path $SuitableRoot "outputs\resource_thresholds_v4.csv") "02_风光潜力与已有装机_0.25度网格\01_适宜性潜力\resource_thresholds_v4.csv" "final resource thresholds v4"
    New-ArchiveItem (Join-Path $SuitableRoot "outputs\zonal_grid_area.csv") "02_风光潜力与已有装机_0.25度网格\01_适宜性潜力\zonal_grid_area.csv" "direct zonal upstream"
    New-ArchiveItem (Join-Path $SuitableRoot "outputs\execution_report_zh.md") "02_风光潜力与已有装机_0.25度网格\01_适宜性潜力\execution_report_zh.md" "processing report"
    New-ArchiveItem (Join-Path $SuitableRoot "distributed_pv_025deg_grid_simplified_20260603") "02_风光潜力与已有装机_0.25度网格\02_分布式光伏_最终简化版" "final DPV input to final_pointV2"
    New-ArchiveItem (Join-Path $SuitableRoot "distributed_pv_025deg_grid_enhancement_20260603") "02_风光潜力与已有装机_0.25度网格\03_分布式光伏_增强版过程证据" "upstream DPV QA evidence"
    New-ArchiveItem (Join-Path $InstalledRoot "osm_geometry_value_added_capacity_v3_offwind47") "02_风光潜力与已有装机_0.25度网格\04_已有风光装机_v3_海风47GW_最终版" "authoritative National_model existing VRE version"
    New-ArchiveItem (Join-Path $InstalledRoot "osm_geometry_value_added_capacity_v2") "02_风光潜力与已有装机_0.25度网格\05_上游版本_仅供复现v3_非最终成果" "v3 upstream only; not final"
    New-ArchiveItem (Join-Path $InstalledRoot "data_processed") "02_风光潜力与已有装机_0.25度网格\06_已有装机处理输入" "processed GEM/NEA inputs"
    New-ArchiveItem (Join-Path $InstalledRoot "data_raw") "02_风光潜力与已有装机_0.25度网格\07_已有装机原始下载快照" "raw GEM/NEA source snapshot"
    New-ArchiveItem (Join-Path $InstalledRoot "scripts") "02_风光潜力与已有装机_0.25度网格\08_已有装机复现脚本" "scripts 01-12; final correction is 11-12"
    New-ArchiveItem (Join-Path $SuitableRoot "final") "02_风光潜力与已有装机_0.25度网格\09_剩余容量_SO2_CCS上游" "SO2/CCS ancillary source for final_pointV2"
    New-ArchiveItem (Join-Path $SuitableRoot "final_pointV2") "02_风光潜力与已有装机_0.25度网格\10_最终优化点_final_pointV2" "authoritative National_model 0.25-degree point input"
    New-ArchiveItem "D:\National_model\Data\OSM_national\national_power_facilities.gdb" "02_风光潜力与已有装机_0.25度网格\11_OSM电力设施源数据库\national_power_facilities.gdb" "OSM point/polygon source"
    New-ArchiveItem (Join-Path $PowerCurveRoot "outputs\future_8760_projection_ev_calibrated_v3_qc") "03_基准电力负荷_不含采暖制冷电动车\01_当前未来负荷完整来源_v3_QC" "current source; overall_status PASS"
    New-ArchiveItem (Join-Path $PowerCurveRoot "outputs\run_20260617_122125\tables") "03_基准电力负荷_不含采暖制冷电动车\02_历史负荷分解最终表" "historical decomposition evidence"
    New-ArchiveItem (Join-Path $PowerCurveRoot "2015_2024各省负荷_论文") "03_基准电力负荷_不含采暖制冷电动车\03_已发表省级逐时总负荷源数据" "published historical source snapshot"
    New-ArchiveItem (Join-Path $PowerCurveRoot "scripts") "03_基准电力负荷_不含采暖制冷电动车\04_复现脚本" "current Power_curve_V2 scripts"
    New-ArchiveItem (Join-Path $PowerCurveRoot "config") "03_基准电力负荷_不含采暖制冷电动车\05_运行配置" "current Power_curve_V2 config"
    New-ArchiveItem (Join-Path $PowerCurveRoot "预测基础数据外推\电力负荷2020-2060\provincial_electricity_demand_template.csv") "03_基准电力负荷_不含采暖制冷电动车\06_情景输入\provincial_electricity_demand_template.csv" "future annual demand targets"
    New-ArchiveItem (Join-Path $PowerCurveRoot "预测基础数据外推\空调参数外推\ac_ownership_2015_2024_projection_2025_2060.xlsx") "03_基准电力负荷_不含采暖制冷电动车\06_情景输入\ac_ownership_2015_2024_projection_2025_2060.xlsx" "thermal subtraction/scaling evidence"
    New-ArchiveItem (Join-Path $PowerCurveRoot "预测基础数据外推\电动汽车保有量推测\中国汽车与新能源汽车保有量_补充材料版_Logistic情景推算表.xlsx") "03_基准电力负荷_不含采暖制冷电动车\06_情景输入\中国汽车与新能源汽车保有量_补充材料版_Logistic情景推算表.xlsx" "EV subtraction/scaling evidence"
    New-ArchiveItem (Join-Path $ModelRoot "data\load") "03_基准电力负荷_不含采暖制冷电动车\07_National_model当前负荷输入" "current model-ready load tables"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\biomass\data\raw") "04_生物质资源与模型输入\01_原始数据快照" "final workflow source data"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\biomass\output\results_arcgis_final") "04_生物质资源与模型输入\02_空间评估最终成果" "results_arcgis_final only"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\biomass\scripts") "04_生物质资源与模型输入\03_复现脚本" "current biomass script"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\biomass\READEME.md") "04_生物质资源与模型输入\04_工程说明\READEME.md" "project source description"
    New-ArchiveItem (Join-Path $ModelRoot "data\biomass") "04_生物质资源与模型输入\05_National_model省级输入" "current model-ready biomass tables"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\transmission_line\data") "05_现存省际输电线路\01_最终表格与来源" "use *_with_500kv and candidate options as documented"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\transmission_line\outputs\shp_2025_with_500kv") "05_现存省际输电线路\02_最终矢量_SHP_含500kV补充" "final GIS export with 500 kV supplement"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\transmission_line\outputs\province_transmission_model_edges_2025_with_500kv.geojson") "05_现存省际输电线路\03_最终矢量_GeoJSON\province_transmission_model_edges_2025_with_500kv.geojson" "final GIS export with 500 kV supplement"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\transmission_line\outputs\province_pair_new_corridor_matrices_2025.xlsx") "05_现存省际输电线路\04_候选走廊矩阵\province_pair_new_corridor_matrices_2025.xlsx" "candidate corridor workbook"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\transmission_line\scripts") "05_现存省际输电线路\05_复现脚本" "current transmission scripts"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\transmission_line\工程说明_2025省际输电容量数据.md") "05_现存省际输电线路\06_工程说明\工程说明_2025省际输电容量数据.md" "existing-grid documentation"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\transmission_line\工程说明_省际距离与候选线路矩阵.md") "05_现存省际输电线路\06_工程说明\工程说明_省际距离与候选线路矩阵.md" "candidate-grid documentation"
    New-ArchiveItem "D:\National_model\Data\OSM_national\national_power_line_complete.gdb" "05_现存省际输电线路\07_OSM完整电力线路源数据库\national_power_line_complete.gdb" "500 kV supplement and suitability access source"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\thermal_power\data\raw") "06_火电核电厂点位与退役边界\01_GEM原始下载快照" "official GEM tracker snapshots"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\thermal_power\outputs\thermal_retirement_20260612_official_gem_neacheck") "06_火电核电厂点位与退役边界\02_火电最终版_official_gem_neacheck" "authoritative thermal output"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\thermal_power\outputs\nuclear_capacity_milestones_expanded_20260612") "06_火电核电厂点位与退役边界\03_核电扩展里程碑最终版" "current nuclear pipeline source"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\thermal_power\scripts") "06_火电核电厂点位与退役边界\04_复现脚本" "current thermal/nuclear scripts"
    New-ArchiveItem "D:\National_model\Data\Gis\Hourly_cf\mixed_wind\cf_hourly_mixed_wind_2023.zarr" "07_基准气象年风光容量因子_2023\mixed_wind\cf_hourly_mixed_wind_2023.zarr" "default weather year 2023"
    New-ArchiveItem "D:\National_model\Data\Gis\Hourly_cf\onshore_wind\cf_hourly_onshore_wind_2023.zarr" "07_基准气象年风光容量因子_2023\onshore_wind\cf_hourly_onshore_wind_2023.zarr" "default weather year 2023"
    New-ArchiveItem "D:\National_model\Data\Gis\Hourly_cf\offshore_wind\cf_hourly_offshore_wind_2023.zarr" "07_基准气象年风光容量因子_2023\offshore_wind\cf_hourly_offshore_wind_2023.zarr" "default weather year 2023"
    New-ArchiveItem "D:\National_model\Data\Gis\Hourly_cf\pv\cf_hourly_pv_2023.zarr" "07_基准气象年风光容量因子_2023\pv\cf_hourly_pv_2023.zarr" "default weather year 2023"
    New-ArchiveItem "D:\National_model\Data\Gis\Hourly_cf\summary\cf_annual_summary_2023.csv" "07_基准气象年风光容量因子_2023\summary\cf_annual_summary_2023.csv" "2023 annual CF summary"
    New-ArchiveItem (Join-Path $ModelRoot "supplementary_materials\modules\02_hourly_vre_capacity_factors") "07_基准气象年风光容量因子_2023\方法与QA归档" "hourly VRE technical archive"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\hydro_power\process_hydro\hydro_model_2019_stage2_classification_cascade_20260630\model_inputs\hydro_station_operation_type_stage2.csv") "08_水电抽蓄与其他基准空间输入\01_水电站点\hydro_station_operation_type_stage2.csv" "current hydro station classification"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\hydro_power\process_hydro\hydro_model_2019_stage2_classification_cascade_20260630\figure_data") "08_水电抽蓄与其他基准空间输入\02_梯级拓扑" "current cascade nodes and edges"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\hydro_power\process_hydro\hydro_model_2019_stage1_20260629\model_inputs") "08_水电抽蓄与其他基准空间输入\03_水文时序" "current station-level hydrology inputs"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\hydro_power\process_hydro\hydro_phs_module\data_output\hydrochn_ght2026_updated.csv") "08_水电抽蓄与其他基准空间输入\04_水电更新清单\hydrochn_ght2026_updated.csv" "existing hydro inventory"
    New-ArchiveItem (Join-Path $NationalRoot "Gis_process\hydro_power\process_hydro\hydrochn_clean_v1_outputs\phs_ght2026_8h_clean.csv") "08_水电抽蓄与其他基准空间输入\05_抽蓄清单\phs_ght2026_8h_clean.csv" "current PHS inventory"
    New-ArchiveItem (Join-Path $ModelRoot "data\hydro") "08_水电抽蓄与其他基准空间输入\06_National_model水电输入" "current model-ready hydro tables"
    New-ArchiveItem (Join-Path $ModelRoot "data\storage") "08_水电抽蓄与其他基准空间输入\07_National_model储能边界" "current model-ready storage tables"
    New-ArchiveItem (Join-Path $ModelRoot "data\sets") "09_National_model直接输入包\data\sets" "current model-ready data"
    New-ArchiveItem (Join-Path $ModelRoot "data\vre") "09_National_model直接输入包\data\vre" "current model-ready data"
    New-ArchiveItem (Join-Path $ModelRoot "data\load") "09_National_model直接输入包\data\load" "current model-ready data"
    New-ArchiveItem (Join-Path $ModelRoot "data\flexibility") "09_National_model直接输入包\data\flexibility" "current model-ready data"
    New-ArchiveItem (Join-Path $ModelRoot "data\thermal") "09_National_model直接输入包\data\thermal" "current model-ready data"
    New-ArchiveItem (Join-Path $ModelRoot "data\hydro") "09_National_model直接输入包\data\hydro" "current model-ready data"
    New-ArchiveItem (Join-Path $ModelRoot "data\biomass") "09_National_model直接输入包\data\biomass" "current model-ready data"
    New-ArchiveItem (Join-Path $ModelRoot "data\transmission") "09_National_model直接输入包\data\transmission" "current model-ready data"
    New-ArchiveItem (Join-Path $ModelRoot "data\carbon") "09_National_model直接输入包\data\carbon" "current model-ready data"
    New-ArchiveItem (Join-Path $ModelRoot "data\technology") "09_National_model直接输入包\data\technology" "current model-ready data"
    New-ArchiveItem (Join-Path $ModelRoot "data\storage") "09_National_model直接输入包\data\storage" "current model-ready data"
    New-ArchiveItem (Join-Path $ModelRoot "data\wave") "09_National_model直接输入包\data\wave" "current model-ready data"
    New-ArchiveItem (Join-Path $ModelRoot "data\grid") "09_National_model直接输入包\data\grid" "current model-ready data"
    New-ArchiveItem (Join-Path $ModelRoot "data\load_center_network") "09_National_model直接输入包\data\load_center_network" "current city_337 network"
    New-ArchiveItem (Join-Path $ModelRoot "data\load_centers_1km") "09_National_model直接输入包\data\load_centers_1km" "load-center construction evidence"
    New-ArchiveItem (Join-Path $ModelRoot "data\README.md") "09_National_model直接输入包\data\README.md" "data package documentation"
    New-ArchiveItem (Join-Path $ModelRoot "data\model_defaults.json") "09_National_model直接输入包\data\model_defaults.json" "data package defaults"
    New-ArchiveItem (Join-Path $ModelRoot "data\source_manifest.csv") "09_National_model直接输入包\data\source_manifest.csv" "source hashes"
    New-ArchiveItem (Join-Path $ModelRoot "data\output_manifest.csv") "09_National_model直接输入包\data\output_manifest.csv" "output hashes"
    New-ArchiveItem (Join-Path $ModelRoot "data\qc_summary.csv") "09_National_model直接输入包\data\qc_summary.csv" "build QA"
    New-ArchiveItem (Join-Path $ModelRoot "data\smoke_test_report.json") "09_National_model直接输入包\data\smoke_test_report.json" "smoke QA"
    New-ArchiveItem (Join-Path $ModelRoot "config") "09_National_model直接输入包\config" "current configuration snapshot"
    New-ArchiveItem (Join-Path $ModelRoot "cispo_model") "09_National_model直接输入包\cispo_model" "current loader/model code snapshot"
    New-ArchiveItem (Join-Path $ModelRoot "scripts") "09_National_model直接输入包\scripts" "current build/run scripts"
    New-ArchiveItem (Join-Path $ModelRoot "tests") "09_National_model直接输入包\tests" "current regression tests"
    New-ArchiveItem (Join-Path $ModelRoot "env") "09_National_model直接输入包\env" "environment definition"
    New-ArchiveItem (Join-Path $ModelRoot "README.md") "09_National_model直接输入包\README.md" "model overview"
    New-ArchiveItem (Join-Path $ModelRoot "MODEL_IO_CONTRACT.md") "09_National_model直接输入包\MODEL_IO_CONTRACT.md" "model I/O contract"
    New-ArchiveItem (Join-Path $ModelRoot "cispo_full_lp_model_spec.md") "09_National_model直接输入包\cispo_full_lp_model_spec.md" "model specification"
    New-ArchiveItem (Join-Path $ModelRoot "requirements-data.txt") "09_National_model直接输入包\requirements-data.txt" "data environment"
    New-ArchiveItem (Join-Path $ModelRoot "requirements-server.txt") "09_National_model直接输入包\requirements-server.txt" "server environment"
    New-ArchiveItem (Join-Path $ModelRoot "requirements-test.txt") "09_National_model直接输入包\requirements-test.txt" "test environment"
)

function Get-SourceBytes {
    param([string]$Path)
    $Item = Get-Item -LiteralPath $Path
    if (-not $Item.PSIsContainer) {
        return [int64]$Item.Length
    }
    $Measure = Get-ChildItem -LiteralPath $Path -File -Recurse | Measure-Object -Property Length -Sum
    return [int64]$Measure.Sum
}

$Inventory = @()
foreach ($Item in $Items) {
    if (-not (Test-Path -LiteralPath $Item.Source)) {
        throw "缺少归档源：$($Item.Source)"
    }
    $SourceItem = Get-Item -LiteralPath $Item.Source
    $Inventory += [PSCustomObject]@{
        source_path = $SourceItem.FullName
        archive_relative_path = $Item.Destination
        version_role = $Item.VersionRole
        source_type = if ($SourceItem.PSIsContainer) { "directory" } else { "file" }
        source_bytes = Get-SourceBytes $Item.Source
        source_last_write_time = $SourceItem.LastWriteTime.ToString("o")
    }
}

$EstimatedBytes = [int64](($Inventory | Measure-Object -Property source_bytes -Sum).Sum)
$DriveName = ([System.IO.Path]::GetPathRoot($ArchiveRoot)).TrimEnd("\").TrimEnd(":")
$Drive = Get-PSDrive -Name $DriveName
$RequiredFreeBytes = $EstimatedBytes + 1GB
if ($Drive.Free -lt $RequiredFreeBytes) {
    throw "空间不足：预计复制 $([math]::Round($EstimatedBytes/1GB,3)) GiB，要求额外保留 1 GiB；当前仅 $([math]::Round($Drive.Free/1GB,3)) GiB。"
}

New-Item -ItemType Directory -Path $ArchiveRoot | Out-Null
$ArchiveInfoDir = Join-Path $ArchiveRoot "00_归档说明与校验"
New-Item -ItemType Directory -Path $ArchiveInfoDir | Out-Null
$Inventory | Export-Csv -LiteralPath (Join-Path $ArchiveRoot "00_归档说明与校验\复制源映射.csv") -NoTypeInformation -Encoding utf8BOM -Force

foreach ($Item in $Items) {
    $Destination = Join-Path $ArchiveRoot $Item.Destination
    $SourceItem = Get-Item -LiteralPath $Item.Source
    if ($SourceItem.PSIsContainer) {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
        & robocopy $SourceItem.FullName $Destination /E /COPY:DAT /DCOPY:DAT /R:2 /W:1 /XJ /NFL /NDL /NJH /NJS /NP
        if ($LASTEXITCODE -ge 8) {
            throw "robocopy 失败（exit=$LASTEXITCODE）：$($SourceItem.FullName) -> $Destination"
        }
    }
    else {
        $Parent = Split-Path -Parent $Destination
        New-Item -ItemType Directory -Path $Parent -Force | Out-Null
        Copy-Item -LiteralPath $SourceItem.FullName -Destination $Destination
    }
}

$BaseLoadDir = Join-Path $ArchiveRoot "03_基准电力负荷_不含采暖制冷电动车\08_仅基准残余负荷_最终导出"
& $Python (Join-Path $ModelRoot "scripts\extract_base_residual_load.py") `
    --input (Join-Path $ModelRoot "data\load\hourly_load_2025_2060.csv.gz") `
    --output (Join-Path $BaseLoadDir "基准残余负荷_不含采暖制冷电动车_2025_2060.csv.gz") `
    --qa-output (Join-Path $BaseLoadDir "基准残余负荷_QA.json") `
    --annual-output (Join-Path $BaseLoadDir "基准残余负荷_分省年度汇总.csv")
if ($LASTEXITCODE -ne 0) {
    throw "基准残余负荷导出失败（exit=$LASTEXITCODE）"
}

$GitState = @()
$GitState += "archive_created=$(Get-Date -Format o)"
$GitState += "archive_root=$ArchiveRoot"
$GitState += "estimated_source_bytes=$EstimatedBytes"
$GitState += "git_head=$(& git -C $ModelRoot rev-parse HEAD)"
$GitState += "git_branch=$(& git -C $ModelRoot branch --show-current)"
$GitState += "git_status_begin"
$GitState += (& git -C $ModelRoot status --short)
$GitState += "git_status_end"
$GitState | Set-Content -LiteralPath (Join-Path $ArchiveRoot "00_归档说明与校验\归档运行状态.txt") -Encoding utf8BOM

Write-Output "ARCHIVE_ROOT=$ArchiveRoot"
Write-Output "ESTIMATED_SOURCE_GIB=$([math]::Round($EstimatedBytes/1GB,3))"
