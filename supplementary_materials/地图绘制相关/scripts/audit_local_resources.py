"""Read local map resources; write evidence only under this delivery folder.

Run with the existing RL Python. --arcpy probes ArcGIS instead of general GIS.
No plotting, solver, network access, package installation or upstream writes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
NM = HERE.parents[1]
PROJECT = NM.parent
SUIT = PROJECT / "Gis_process/suitable_area"
EXIST = SUIT / "installed_capacity_2026_landuse_grid_assessment/osm_geometry_value_added_capacity_v3_offwind47"
JOURNAL = PROJECT / "claude_workspace/analysis/base_dual_diagnosis_20261020/04_figures/journal_codex_v2"
PROVINCES = Path(r"D:\gisproject\gis地图数据\2024最新权威全国行政区数据0512\2024最新权威全国行政区数据0512\中国标准行政区划数据GS（2024）0650号\中国_省_市_县shp格式\中国_省.shp")
PRJ = Path(r"D:\Work\联合国地球大数据报告申报\12月书稿\制图指南及模板-2025--供参考\制图指南及模板-2025--供参考\投影文件\中国底图投影.prj")
OLD_PRJ = Path(r"D:\Work\联合国地球大数据报告申报\制图指南及模板\制图指南及模板\投影文件\中国底图投影.prj")
NINE = Path(r"D:\gisproject\九段线\11\九段线.shp")


def resources():
    rows = [
        ("province_boundary", "basemap", PROVINCES, "标准省界；行政展示范围不等于31省模型样本"),
        ("target_projection", "basemap", PRJ, "现有模块01/03/05实际使用"),
        ("legacy_projection", "legacy", OLD_PRJ, "旧技能路径；比较存在性与CRS后判断"),
        ("nine_dash", "basemap", NINE, "主图裁切；右下插图完整显示"),
        ("river_r1", "context", Path(r"D:\gisproject\中国地图要素\R1\R1\hyd1_4l.shp"), "一级河流背景"),
        ("river_r2", "context", Path(r"D:\gisproject\中国地图要素\R3\R3\hyd2_4l.shp"), "二级河流实际存于R3目录"),
        ("river_r5", "context", Path(r"D:\gisproject\中国地图要素\R5\R5\River5_polyline.shp"), "更细河流背景"),
        ("dpv_raw_cells", "context", Path(r"D:\National_model\分布式光伏\outputs_90city\gis_v4\fn_cells_all.shp"), "DPV原始空间单元；勿称全覆盖实测"),
        ("osm_gdb", "container", Path(r"D:\National_model\Data\OSM_national\national_power_facilities.gdb"), "OSM设施原始库；不把OSM完整性视为官方完整性"),
        ("suitability_grid", "data", SUIT / "outputs/final_grid_suitability.csv", "适宜性与潜力原始最终网格"),
        ("grid_polygon_gdb", "container", SUIT / "intermediate/run_current_v3/suitability_work.gdb", "要素类grid_025_polygon_master_prj；用ArcPy确认"),
        ("area_rasters", "container", SUIT / "intermediate/run_current_v3/rasters/area_rasters_v3", "像元适宜面积CRF"),
        ("dpv_grid", "data", SUIT / "distributed_pv_025deg_grid_simplified_20260603/tables/grid_points_with_dpv_mw_simplified.csv", "DPV潜力及C/B/O字段"),
        ("final_point_v2", "data", SUIT / "final_pointV2/tables/final_025deg_points_for_optimization.csv", "当前上游综合点；不是模型筛选后点集"),
        ("point_field_dictionary", "dictionary", SUIT / "final_pointV2/tables/field_dictionary_final_025deg_points.csv", "字段定义与单位"),
        ("point_qa", "evidence", SUIT / "final_pointV2/tables/qa_summary.csv", "上游原QA；此次不重新认定全部科学方法"),
        ("point_source_manifest", "evidence", SUIT / "final_pointV2/tables/source_manifest.csv", "来源清单"),
        ("point_report", "reference", SUIT / "final_pointV2/docs/WORKFLOW_AND_FINAL_ARCHIVE.md", "47GW修正和最终版本边界"),
        ("point_gdb", "container", SUIT / "final_pointV2/vector/final_025deg_optimization_points.gdb", "要素类final_025deg_points_for_optimization"),
        ("existing_v3_grid", "data", EXIST / "tables/grid_025_osm_geometry_value_added_key_fields.csv", "当前已有装机拆分"),
        ("existing_v3_report", "reference", EXIST / "TECHNICAL_ARCHIVE_REPORT.md", "已有装机来源及残差分配解释"),
        ("existing_v3_025_manifest", "evidence", EXIST / "tables/raster_manifest_025deg.csv", "0.25度栅格入口"),
        ("existing_v3_pixel_manifest", "evidence", EXIST / "tables/landuse_capacity_raster_manifest_final.csv", "像元栅格入口"),
        ("existing_v3_025_rasters", "container", EXIST / "rasters_025deg", "0.25度CRF"),
        ("existing_v3_pixel_rasters", "container", EXIST / "landuse_cap_rasters", "像元已有装机CRF"),
        ("legacy_v2", "legacy", SUIT / "installed_capacity_2026_landuse_grid_assessment/osm_geometry_value_added_capacity_v2", "历史版本保留，不作为最新海陆风拆分"),
        ("hydro_paths", "data", PROJECT / "Gis_process/hydro_power/process_hydro/hydro_model_2019_stage2_classification_cascade_20260630/figure_data/cascade_topology_path_reaches_stage2.geojson", "已识别梯级沿河路径"),
        ("interprovincial_geometry", "data", PROJECT / "Gis_process/transmission_line/outputs/province_transmission_model_edges_2025_with_500kv.geojson", "省际模型边空间展示；不自动等于全线路实测走向"),
        ("uhv_geometry", "data", PROJECT / "Gis_process/transmission_line/outputs/uhv_lines_2025_crossprov.geojson", "跨省UHV线路参考；正式图前核对来源与geometry定义"),
        ("journal_readme", "reference", JOURNAL / "README_ZH.md", "内部探索版，非论文最终审美验收"),
        ("journal_data", "container", JOURNAL / "figure_data", "历史图集数据；不能替代新案例结果"),
        ("journal_runtime", "evidence", JOURNAL / "qa/runtime_versions.json", "历史环境快照"),
        ("journal_prepare", "script", JOURNAL / "scripts/prepare_data.py", "历史结果整理；先检查固定输出目录"),
        ("journal_plot", "script", JOURNAL / "scripts/plot_atlas.py", "参考布局，不整段照搬非线性色标/脚注"),
        ("journal_package", "script", JOURNAL / "scripts/package_atlas.py", "PDF/HTML打包参考"),
        ("latest_style_readme", "reference", JOURNAL.parent / "midterm_base_v3/README_ZH.md", "作者后续风格决定：英文、线性、无说明脚注"),
        ("latest_linear_maps", "script", JOURNAL.parent / "midterm_base_v3/scripts/build.py", "线性色标与显示阈值审计参考"),
        ("rl_python", "runtime", Path(r"C:\Users\ZZ\.conda\envs\RL\python.exe"), "推荐地图环境"),
        ("arcgis_python", "runtime", Path(r"D:\Program Files\ArcGISPro\bin\Python\envs\arcgispro-py3\python.exe"), "CRF/FileGDB核验"),
        ("shell_default_python", "runtime", Path(r"D:\anaconda\python.exe"), "本次PATH默认；勿假定等于RL"),
        ("arial_font", "runtime", Path(r"C:\Windows\Fonts\arial.ttf"), "现有英文字体"),
    ]
    for rel, note in [
        ("vre/optimization_points.csv", "模型风光点；绘模型结果优先按其键连接"),
        ("vre/out_of_scope_points.csv", "范围外点审计"),
        ("sets/provinces.csv", "省份索引"),
        ("thermal/existing_capacity_2025.csv", "省级火电存量，不是电厂坐标表"),
        ("thermal/nuclear_capacity_floor_by_year.csv", "省级核电下界，不是逐站优化结果"),
        ("grid/substations_osm_220kv_plus.csv", "220kV及以上OSM变电站"),
        ("load_center_network/city_337/load_centers.csv", "337城市负荷代理中心"),
        ("load_center_network/city_337/intra_edges.csv", "省内代理网络边"),
        ("load_center_network/city_337/vre_routes.csv", "风光接入路线"),
        ("load_center_network/city_337/hydro_routes.csv", "水电接入路线"),
        ("transmission/existing_lines.csv", "既有线路输入"),
        ("transmission/candidate_corridors.csv", "候选省际通道"),
        ("hydro/hydro_stations.csv", "站级水电；具体坐标来源和匹配质量见诊断"),
        ("hydro/cascade_topology_nodes.csv", "梯级节点"),
        ("hydro/cascade_topology_edges.csv", "梯级拓扑边"),
        ("hydro/provincial_aggregate_capacity_2025.csv", "省级聚合水电，不虚构站址"),
        ("wave/wave_sites.csv", "波浪能候选点"),
    ]:
        rows.append((rel.replace("/", "_"), "model_input", NM / "data" / rel, note))
    for rel, note in [
        ("01_wind_solar_suitability/scripts/generate_module_outputs.py", "多情景格网/像元图、CRF解码；固定输出到旧模块"),
        ("01_wind_solar_suitability/scripts/qa_arcpy_crf.py", "ArcPy核对CRF参考；原脚本会写旧模块表"),
        ("03_load_reconstruction_and_centers/scripts/generate_module_outputs.py", "china_layers和finish_map可复用；仅导入不会执行main"),
        ("03_load_reconstruction_and_centers/scripts/generate_city337_initialized_network.py", "负荷中心、接入、代理网络"),
        ("05_hydropower_and_pumped_storage/scripts/plot_hydro_capacity_spatial_contract.py", "站级/梯级/省级水电区分"),
        ("09_model_formulation/scripts/draw_network_generation_maps.py", "电网与发电分布参考，先审查边界与路径"),
    ]:
        rows.append((rel.replace("/", "_"), "script", NM / "supplementary_materials/modules" / rel, note))
    for rid, path in [("province_boundary", PROVINCES), ("nine_dash", NINE)]:
        for suffix in [".shx", ".dbf", ".prj", ".cpg"]:
            rows.append((rid + suffix, "sidecar", path.with_suffix(suffix), "shapefile配套文件；与shp一起保留"))
    return rows


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arcpy", action="store_true")
    args = parser.parse_args()
    out = HERE / "evidence"
    out.mkdir(exist_ok=True)
    runtime = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "executable": sys.executable,
               "python": platform.python_version(), "platform": platform.platform(), "packages": {}}
    if args.arcpy:
        import arcpy
        runtime["arcgis_install"] = arcpy.GetInstallInfo()
        checks = {}
        paths = [SUIT / "intermediate/run_current_v3/suitability_work.gdb/grid_025_polygon_master_prj",
                 SUIT / "final_pointV2/vector/final_025deg_optimization_points.gdb/final_025deg_points_for_optimization",
                 SUIT / "intermediate/run_current_v3/rasters/area_rasters_v3/area_onwind_B_infra_km2.crf"]
        for p in paths:
            item = {"exists": bool(arcpy.Exists(str(p)))}
            if item["exists"]:
                d = arcpy.Describe(str(p))
                item.update(data_type=d.dataType, crs=d.spatialReference.name)
                if d.dataType == "FeatureClass":
                    item["count"] = int(arcpy.management.GetCount(str(p))[0])
                else:
                    item.update(cell_x=d.meanCellWidth, cell_y=d.meanCellHeight)
            checks[str(p)] = item
        runtime["resource_checks"] = checks
        dump(out / "arcgis_runtime.json", runtime)
        print(json.dumps(runtime, ensure_ascii=False))
        return
    for name in ["numpy", "pandas", "matplotlib", "geopandas", "pyproj", "shapely", "rasterio", "fiona", "pyogrio", "lerc", "PIL", "fitz", "pypdf"]:
        try:
            m = importlib.import_module(name)
            runtime["packages"][name] = {"import_ok": True, "version": str(getattr(m, "__version__", getattr(m, "VersionBind", "not_exposed")))}
        except Exception as exc:
            runtime["packages"][name] = {"import_ok": False, "error": f"{type(exc).__name__}: {exc}"}
    dump(out / "rl_runtime.json", runtime)
    records = []
    for rid, category, path, note in resources():
        row = dict(id=rid, category=category, path=str(path), exists=path.exists(), kind="directory" if path.is_dir() else "file", bytes="", sha256="", note=note)
        if path.is_file():
            row["bytes"] = path.stat().st_size
            if path.suffix.lower() in {".csv", ".md", ".py", ".json", ".prj", ".shp", ".shx", ".dbf"} and row["bytes"] < 32 * 1024**2:
                row["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        records.append(row)
    with (HERE / "resource_inventory.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=records[0].keys()); w.writeheader(); w.writerows(records)
    import geopandas as gpd
    import pandas as pd
    from pyproj import CRS, Transformer
    target = CRS.from_wkt(PRJ.read_text(encoding="utf-8"))
    geo = {"target_crs_name": target.name, "target_wkt": target.to_wkt(), "target_proj4": target.to_dict(), "axis_units": [a.unit_name for a in target.axis_info], "layers": {}}
    geo["legacy_prj_exists"] = OLD_PRJ.exists()
    if OLD_PRJ.exists():
        geo["legacy_crs_equivalent"] = target.equals(CRS.from_wkt(OLD_PRJ.read_text(encoding="utf-8")))
    for rid, p in [("provinces", PROVINCES), ("nine_dash", NINE)]:
        d = gpd.read_file(p)
        pr = d.to_crs(target)
        from shapely.validation import explain_validity
        invalid = [{"index": str(i), "gb": str(row.get("gb", "")), "name_read_default": str(row.get("name", "")), "reason": explain_validity(row.geometry)} for i, row in d.loc[~d.is_valid].iterrows()]
        geo["layers"][rid] = {"count": len(d), "source_crs": str(d.crs), "projected_bounds": pr.total_bounds.tolist(), "all_valid": bool(d.is_valid.all()), "invalid_geometries": invalid, "fields": list(d.columns), "sidecars": {s: p.with_suffix(s).exists() for s in [".shp", ".shx", ".dbf", ".prj", ".cpg"]}}
        if rid == "provinces":
            xmin, _, xmax, ymax = pr.total_bounds
            width = xmax - xmin
            _, cut = Transformer.from_crs("EPSG:4326", target, always_xy=True).transform(105, 15.5)
            ext = [xmin - .03 * width, xmax + .30 * width, cut, ymax + .06 * width]
            geo["main_extent"] = ext
            geo["box_aspect"] = (ext[3]-ext[2])/(ext[1]-ext[0])
    dump(out / "geospatial_checks.json", geo)
    tables = {}
    for row in records:
        p = Path(row["path"])
        if row["exists"] and p.suffix == ".csv" and row["category"] in {"data", "model_input", "dictionary"}:
            frame = pd.read_csv(p)
            item = {"rows": len(frame), "columns": list(frame.columns)}
            for key in ["grid_uid", "point_id", "load_center_id", "intra_edge_id"]:
                if key in frame:
                    item[key + "_unique"] = bool(frame[key].is_unique)
            if row["id"] == "final_point_v2":
                item["existing_capacity_sums_mw"] = {c: float(frame[c].sum()) for c in frame if c.startswith("existing_") and c.endswith("_mw")}
            tables[row["id"]] = item
    dump(out / "table_checks.json", tables)
    upstream = pd.read_csv(SUIT / "final_pointV2/tables/final_025deg_points_for_optimization.csv")
    model = pd.read_csv(NM / "data/vre/optimization_points.csv")
    excluded = pd.read_csv(NM / "data/vre/out_of_scope_points.csv")
    dump(out / "grid_scope_checks.json", {
        "upstream_rows": len(upstream), "upstream_columns": len(upstream.columns),
        "model_rows": len(model), "excluded_rows": len(excluded),
        "model_subset_of_upstream": set(model.grid_uid) <= set(upstream.grid_uid),
        "excluded_equals_upstream_minus_model": set(excluded.grid_uid) == set(upstream.grid_uid) - set(model.grid_uid),
        "model_and_excluded_disjoint": not bool(set(model.grid_uid) & set(excluded.grid_uid))})
    print(json.dumps({"resources": len(records), "missing": [r["id"] for r in records if not r["exists"]], "runtime": runtime, "crs": geo["target_crs_name"], "box_aspect": geo["box_aspect"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
