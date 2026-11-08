"""Build a Base-2060 map atlas from identified local solved outputs.

No optimization, remote access, or changes to inputs/formal supplement modules.
The output folders and figure titles in the filesystem are Chinese.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection
import numpy as np
import pandas as pd

from china_map import (ChinaMap, ROOT, BLUE, RED, TEAL, PALETTES, colorbar,
                       export, figure_grid, linear_norm, sha256, write_json)

MODEL=ROOT.parents[1]
PROJECT=MODEL.parent
ARCHIVE=MODEL/"supplementary_materials/reviews/base_frozen_followups_20261027/source_base/20261012_base2060_v9a12_t48_m750_tol1e4_v1/output_8760"
RETURN=PROJECT/"claude_workspace/analysis/base_dual_diagnosis_20261020/02_server_returns/base2060"
SYSTEM=MODEL/"supplementary_materials/reviews/flex_mechanism_exploration_20261106/runs/system_base2060_v1"
OUT=ROOT/"Base2060全要素图集"
TECHS=[("onwind","Onshore wind","blue"),("offwind","Offshore wind","blue"),("upv","Utility PV","red"),("dpv","Distributed PV","teal")]


class Inputs:
    def __init__(self):
        self.records={};self.checks=[]
        self.original=json.loads((ARCHIVE/"result_manifest.json").read_text())
        self.original_index={x["path"]:x for x in self.original["files"]}
        self.system=json.loads((SYSTEM/"manifest.json").read_text())
        self.input_index=pd.read_csv(ARCHIVE/"input_manifest.csv").set_index("logical_path")
        for p in [ARCHIVE/"result_manifest.json",ARCHIVE/"input_manifest.csv",ARCHIVE/"run_scope.json",ARCHIVE/"run_identity.json",SYSTEM/"manifest.json",SYSTEM/"source_identity.json"]:self.record(p)
        scope=json.loads((ARCHIVE/"run_scope.json").read_text())
        assert (scope["planning_year"],scope["scenario_id"],scope["optimization_hours"])==(2060,"base",8760)
        identity=json.loads((SYSTEM/"source_identity.json").read_text())
        assert identity["case"]=="base2060"
        assert sha256(ARCHIVE/"result_manifest.json")==identity["source_inputs"]["result_manifest.json"]["sha256"]
        self.checks.append({"check":"Base2060_8760_identity_and_system_source_manifest","status":"PASS"})

    def record(self,p):
        p=Path(p);d={"bytes":p.stat().st_size,"sha256":sha256(p)}
        self.records[str(p.resolve())]=d;return d

    def read(self,p,kind="result"):
        p=Path(p);actual=self.record(p)
        if kind=="result":
            expected=self.original_index[p.name]
            assert actual["sha256"]==expected["sha256"],p
        elif kind=="derived":assert actual["sha256"]==self.system[p.name]["sha256"],p
        elif kind=="input":
            rel=p.relative_to(MODEL/"data").as_posix()
            assert actual["sha256"]==self.input_index.loc[rel,"sha256"],p
        return pd.read_csv(p)

    def close(self):
        prior=OUT/"核验记录/输入文件与身份.json"
        if prior.exists():
            existing=json.loads(prior.read_text(encoding="utf-8"));existing.update(self.records);self.records=existing
        assert all(sha256(p)==v["sha256"] for p,v in self.records.items())
        write_json(OUT/"核验记录/输入文件与身份.json",self.records)
        check_path=OUT/"核验记录/数据一致性检查.json"
        existing=json.loads(check_path.read_text(encoding="utf-8")) if check_path.exists() else []
        merged={r["check"]:r for r in existing};merged.update({r["check"]:r for r in self.checks})
        write_json(check_path,list(merged.values()))


def equal_check(inp,name,a,b,atol=1e-6,rtol=1e-9):
    a,b=np.asarray(a,float),np.asarray(b,float)
    err=float(np.max(np.abs(a-b)))
    ok=bool(np.allclose(a,b,atol=atol,rtol=rtol))
    inp.checks.append({"check":name,"max_abs_difference":err,"atol":atol,"rtol":rtol,"status":"PASS" if ok else "FAIL"})
    if not ok:raise ValueError((name,err))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only",default="all",help="all or comma-separated theme numbers 1..12")
    args=parser.parse_args();selected=set(range(1,13)) if args.only=="all" else set(map(int,args.only.split(',')))
    OUT.mkdir(parents=True,exist_ok=True);inp=Inputs();m=ChinaMap();contracts=[]
    cap=inp.read(RETURN/"annual_capacity_by_province_technology.csv")
    gen=inp.read(RETURN/"annual_generation_by_province_technology.csv")
    vre=inp.read(RETURN/"vre_capacity.csv")
    points=inp.read(MODEL/"data/vre/optimization_points.csv","input")
    centers=inp.read(MODEL/"data/load_center_network/city_337/load_centers.csv","input")
    routes=inp.read(MODEL/"data/load_center_network/city_337/vre_routes.csv","input")
    provinces=inp.read(MODEL/"data/sets/provinces.csv","input")
    storage=inp.read(RETURN/"storage_capacity.csv")
    hydro=inp.read(ARCHIVE/"hydro_capacity.csv")
    hydro["technology"]=hydro.operation_type_model.map({"reservoir_storage":"reservoir","run_of_river":"ror"})
    assert hydro.technology.notna().all()
    wave=inp.read(ARCHIVE/"wave_capacity.csv")
    tx=inp.read(RETURN/"transmission_capacity.csv")
    intra=inp.read(ARCHIVE/"load_center_intra_transmission.csv")
    trunk=inp.read(ARCHIVE/"intra_grid_substation_design.csv")
    spur=inp.read(ARCHIVE/"intra_grid_vre_site_design.csv")
    carbon=inp.read(RETURN/"annual_resource_accounting_by_province.csv")
    adequacy=inp.read(RETURN/"annual_adequacy_by_province.csv")
    dac=inp.read(ARCHIVE/"dac_capacity_capture.csv")
    corr=inp.read(SYSTEM/"corridor_stats.csv","derived")
    mh=inp.read(SYSTEM/"province_month_hour.csv","derived")
    external=inp.read(SYSTEM/"province_external_accounts.csv","derived")
    site=inp.read(SYSTEM/"site_capacity_attributes.csv","derived")
    assert points.grid_uid.is_unique and len(points)==16609 and len(provinces)==31
    assert not vre.duplicated(["grid_uid","technology"]).any()
    assert len(vre)==36686
    joined=vre.merge(points[["grid_uid","lon","lat"]],on="grid_uid",how="left",validate="many_to_one")
    assert joined[["lon","lat"]].notna().all().all()
    for tech,_,_ in TECHS:
        for field,target in [("capacity_gw","capacity"),("new_capacity_gw","new_capacity")]:
            actual=joined[joined.technology.eq(tech)].groupby("province_code")[field].sum().reindex(provinces.province_code,fill_value=0)
            expected=cap[cap.technology.eq(tech)].set_index("province_code")[target].reindex(provinces.province_code)
            equal_check(inp,f"VRE_{tech}_{field}_31_provinces",actual,expected)
    sv=site.sort_values(["grid_uid","technology"]);vv=joined.sort_values(["grid_uid","technology"])
    assert list(zip(sv.grid_uid,sv.technology))==list(zip(vv.grid_uid,vv.technology))
    equal_check(inp,"derived_site_vs_original_capacity",sv.capacity_gw,vv.capacity_gw)
    equal_check(inp,"derived_site_coordinates",sv[["lon","lat"]],vv[["lon","lat"]])
    equal_check(inp,"derived_corridor_vs_original",corr.set_index("line_id").loc[tx.line_id,"capacity_gw"],tx.capacity_gw)
    assert mh.case.eq("base2060").all() and not mh.duplicated(["province_code","month","hour"]).any()
    assert (mh.groupby("province_code").n_hours.sum()==8760).all()
    mh["load_gwh"]=mh.baseline_load_mean_gw*mh.n_hours
    mh["energy_value_hours"]=mh.energy_price_mean_cny_per_mwh*mh.n_hours
    mh["composite_value_hours"]=mh.full_price_mean_cny_per_mwh*mh.n_hours
    regional=provinces[["province_code","province_name_en"]].copy()
    regional=regional.merge(mh.groupby("province_code")[["load_gwh","energy_value_hours","composite_value_hours"]].sum(),on="province_code",validate="one_to_one")
    regional["mean_energy_value"]=regional.energy_value_hours/8760
    regional["mean_composite_value"]=regional.composite_value_hours/8760
    regional["load_twh"]=regional.load_gwh/1000
    regional=regional.merge(gen.groupby("province_code").generation_gwh.sum().rename("generation_gwh"),on="province_code",validate="one_to_one")
    regional["generation_twh"]=regional.generation_gwh/1000
    vre_gen=gen[gen.technology.isin([t[0] for t in TECHS])].groupby("province_code").generation_gwh.sum()
    regional["vre_generation_share_pct"]=regional.province_code.map(vre_gen)/regional.generation_gwh*100
    regional=regional.merge(external[["province_code","annual_external_net_import_gwh"]],on="province_code",validate="one_to_one")
    regional["net_import_twh"]=regional.annual_external_net_import_gwh/1000
    regional=regional.merge(adequacy[["province_code","peak_load_gw","capacity_margin_gw"]],on="province_code",validate="one_to_one")
    summary_path=RETURN/"annual_summary.json";inp.record(summary_path)
    assert sha256(summary_path)==inp.original_index[summary_path.name]["sha256"]
    summary=json.loads(summary_path.read_text())
    equal_check(inp,"annual_load_from_month_hour_means",regional.load_gwh.sum(),summary["annual_load_gwh"])
    equal_check(inp,"annual_generation",regional.generation_gwh.sum(),summary["annual_generation_gwh"])
    gen_cap=cap[cap.asset_group.eq("generation")].groupby("technology").capacity.sum().to_dict()
    for tech in ["reservoir","ror"]:
        equal_check(inp,"hydro_"+tech,hydro.loc[hydro.technology.eq(tech),"capacity_gw"].sum(),gen_cap[tech])
    equal_check(inp,"wave_total",wave.capacity_gw.sum(),gen_cap["wave"])
    # Store source data exactly; absent grid/technology records remain absent, never invented zeros.
    geo_by_tech={t:m.cells(joined[joined.technology.eq(t)].copy()) for t,_,_ in TECHS}
    hc=m.points(hydro);wc=m.points(wave);cg=m.points(centers)

    def save(fig,folder,stem,caption,tables):
        target=OUT/folder;target.mkdir(parents=True,exist_ok=True)
        for name,table in tables.items():table.to_csv(target/(name+".csv"),index=False,encoding="utf-8-sig")
        report=export(fig,target/stem)
        (target/(stem+"_图注.md")).write_text("# "+stem+"\n\n"+caption+"\n\n统一口径：Base 2060、8760小时；同一已解release，未重新求解。图内英文、线性色标、色条单位为准。背景无数据地区不解释为零。\n",encoding="utf-8")
        contracts.append({"folder":folder,"stem":stem,"caption":caption,"maps":len(report["map_panels"]),"pdf":str((target/(stem+'.pdf')).relative_to(OUT))})
        registry=OUT/"核验记录/图件登记.json"
        existing=json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else []
        merged={r["stem"]:r for r in existing};merged[stem]=contracts[-1]
        write_json(registry,list(merged.values()))
        print("DONE",folder,stem,flush=True)

    def prov_panels(title,specs):
        fig,axs=figure_grid(title,rows=1 if len(specs)==2 else 2)
        for ax,(d,col,label,unit,pal,signed) in zip(axs,specs):
            m.frame(ax,label);norm=m.province(ax,d,col,pal,signed)
            colorbar(fig,ax,norm,pal,unit)
        return fig

    if 1 in selected:
        for field,folder,stem,label in [("capacity_gw","01_风光装机","风光总装机_四技术","Installed capacity"),("new_capacity_gw","02_风光新增","风光当期新增_四技术","Current-period new build")]:
            fig,axs=figure_grid("Base 2060 | "+label)
            for i,(ax,(tech,name,pal)) in enumerate(zip(axs,TECHS)):
                geo=geo_by_tech[tech];total=geo[field].sum()
                m.frame(ax,f"{'abcd'[i]}  {name} | {total:,.2f} GW")
                norm=m.grid(ax,geo,field,pal);colorbar(fig,ax,norm,pal,"Capacity (GW / 0.25° cell)")
            save(fig,folder,stem,"四类风光分别显示；按grid_uid连接生产点表，重建0.25°格网。所有导出候选记录保留，不设1MW显示阈值。各技术独立全范围线性色标；本图新增量直接取new_capacity_gw，不是跨年容量差。图中格网是决策单元，不是单个实测电厂。",{"风光作图数据":joined})
    # Same native units and shared scale for power panels and energy panels.
    if 2 in selected:
        fig,axs=figure_grid("Base 2060 | Storage power and energy")
        for i,(ax,(tech,col,pal,title,unit)) in enumerate(zip(axs,[
            ("battery","capacity_gw","blue","Battery power","GW"),("phs","capacity_gw","teal","Pumped-hydro power","GW"),
            ("battery","energy_capacity_gwh","blue","Battery energy","GWh"),("phs","energy_capacity_gwh","teal","Pumped-hydro energy","GWh")])):
            d=storage[storage.technology.eq(tech)]
            norm=linear_norm(storage[col]);m.frame(ax,f"{'abcd'[i]}  {title}");m.province(ax,d,col,pal,norm=norm);colorbar(fig,ax,norm,pal,unit)
        save(fig,"06_储能配置","储能功率与能量","省级储能结果，不提供站点坐标。同一行两种储能使用共同范围；上行为GW，下行为GWh，不能相加。能量／功率比受模型时长设置约束，不解释为自由优化时长。",{"储能作图数据":storage})
    if 3 in selected:
        d=corr.copy();d["lo"]=d[["from_province_code","to_province_code"]].min(axis=1);d["hi"]=d[["from_province_code","to_province_code"]].max(axis=1)
        d["oriented_net_twh"]=d.annual_net_gwh/1000*np.where(d.from_province_code.eq(d.lo),1,-1)
        pairs=d.groupby(["lo","hi"],as_index=False)[["capacity_gw","new_capacity_gw","oriented_net_twh"]].sum().rename(columns={"lo":"from_province_code","hi":"to_province_code"})
        segments=m.province_segments(pairs);fig,axs=figure_grid("Base 2060 | Interprovincial transmission")
        for ax,col,title,pal,unit,arrows in [(axs[0],"capacity_gw","a  Corridor capacity","blue","GW",False),(axs[1],"new_capacity_gw","b  New corridor capacity","red","GW",False),(axs[2],"oriented_net_twh","c  Annual net transfer","teal","|Net transfer| (TWh / year)",True)]:
            m.frame(ax,title);norm=m.lines(ax,segments,pairs[col],pal,arrows);colorbar(fig,ax,norm,pal,unit)
        m.frame(axs[3],"d  Provincial net imports");norm=m.province(axs[3],regional,"net_import_twh","diverging",True);colorbar(fig,axs[3],norm,"diverging","Net imports (TWh / year)")
        save(fig,"03_省际输电","省际容量与年度净交换","411条模型线路按无向省对聚合容量；净流先统一方向再相加，箭头表示年度净交换方向。线宽有可见性下限且按值线性增加，颜色为全范围线性。端点为省级代表点，连线不是实际线路走向；不存在电气相角/阻抗的潮流解释。省级净进口来自负荷中心年度外送/接收核算，接收侧计损耗，因此全国净进口合计不要求为零。",{"省对聚合":pairs,"原线路统计":corr,"省级核算":regional})
    if 4 in selected:
        cxy=cg.set_index("load_center_id").geometry
        segments=np.array([[[cxy.loc[a].x,cxy.loc[a].y],[cxy.loc[b].x,cxy.loc[b].y]] for a,b in zip(intra.from_load_center_id,intra.to_load_center_id)])
        intra["net_twh"]=(intra.annual_flow_forward_gwh-intra.annual_flow_reverse_gwh)/1000
        fig,axs=figure_grid("Base 2060 | City-level network proxies",rows=1)
        for ax,col,pal,title,unit in [(axs[0],"capacity_gw","blue","a  Intra-provincial capacity","GW"),(axs[1],"net_twh","teal","b  Annual net transfers","|Net transfer| (TWh / year)")]:
            m.frame(ax,title);norm=m.lines(ax,segments,intra[col],pal,arrows=col=="net_twh",linewidth=(.08,1.5));colorbar(fig,ax,norm,pal,unit)
            ax.scatter(cg.geometry.x,cg.geometry.y,s=1.9,c="#334C5C",linewidths=0,zorder=7)
        save(fig,"04_省内网络与接入","城市负荷中心与省内网络","337个城市负荷代理中心、642条省内边。点位按生产输入，边为端点连接的规划代理；省内流是年度量，不是逐时潮流。所有边和中心保留，无top-N筛选。",{"城市中心":centers,"省内网络":intra})
        subcoords=routes[["substation_id","substation_lon","substation_lat"]].drop_duplicates()
        assert subcoords.substation_id.is_unique
        sub=trunk.merge(subcoords,on="substation_id",how="left",validate="one_to_one")
        missing=sub.substation_lon.isna()
        # Sites without VRE routing can be recovered from the full public-input substation table.
        subinput=inp.read(MODEL/"data/grid/substations_osm_220kv_plus.csv",kind="context")
        ref=subinput.set_index("substation_id")
        sub.loc[missing,"substation_lon"]=sub.loc[missing,"substation_id"].map(ref.lon)
        sub.loc[missing,"substation_lat"]=sub.loc[missing,"substation_id"].map(ref.lat)
        sub=sub.rename(columns={"substation_lon":"lon","substation_lat":"lat"})
        assert sub[["lon","lat"]].notna().all().all()
        sg=m.points(sub)
        agg=site.groupby(["grid_uid","lon","lat"],as_index=False)[["spur_capacity_gw","spur_augmentation_gw"]].sum()
        grid=m.cells(agg);fig,axs=figure_grid("Base 2060 | Grid connection infrastructure")
        for ax,col,title,pal in [(axs[0],"spur_capacity_gw","a  Site connection capacity","blue"),(axs[1],"spur_augmentation_gw","b  New site connections","red")]:
            m.frame(ax,title);norm=m.grid(ax,grid,col,pal);colorbar(fig,ax,norm,pal,"GW / 0.25° cell")
        for ax,col,title,pal in [(axs[2],"trunk_capacity_gw","c  Substation trunk capacity","teal"),(axs[3],"trunk_augmentation_gw","d  New trunk capacity","red")]:
            signed=bool((sg[col]<0).any())
            if signed:pal="diverging"
            norm=linear_norm(sg[col],signed=signed)
            m.frame(ax,title);m.point_values(ax,sg,col,pal,norm=norm,size=4);colorbar(fig,ax,norm,pal,"GW / substation")
        negative_trunk=sub[sub.trunk_augmentation_gw<0]
        inp.checks.append({"check":"negative_trunk_values_retained", "count":len(negative_trunk),"min_gw":float(sub.trunk_augmentation_gw.min()),"status":"DISCLOSED_NOT_CLIPPED"})
        equal_check(inp,"spur_derived_vs_original_sum",site.spur_capacity_gw.sum(),spur.spur_capacity_gw.sum())
        save(fig,"04_省内网络与接入","格网接入与变电站汇集","上两图将各技术接入容量在格网内求和，下两图显示变电站汇集容量。接入/汇集容量不是发电容量，也不与省际通道直接相加。6294变电站均保留；站址沿用生产route，未出现在route中的站址从本地OSM输入补齐并记录来源。原结果5个trunk新增值为微小负数，最小-5.162407e-7 GW；原值保留，新增图用零中心发散色标，不在绘图中清零或解释为拆除。",{"格网接入":agg,"变电站汇集":sub})
    if 5 in selected:
        specs=[(regional,"load_twh","a  Electricity demand","TWh / year","blue",False),
               (regional,"generation_twh","b  Electricity generation","TWh / year","teal",False),
               (regional,"vre_generation_share_pct","c  Wind and solar generation share","% of provincial generation","red",False),
               (regional,"net_import_twh","d  Annual net imports","TWh / year","diverging",True)]
        fig=prov_panels("Base 2060 | Regional supply and demand",specs)
        save(fig,"05_地区供需差异","省级负荷发电与净交换","负荷按month×hour代表组均值乘实际n_hours还原，31省各8760h，全年合计核对原始annual_summary。发电不含储能放电；风光占比的分母为本省发电量，不能解释为本省消费中可再生比例。净交换为年度外送/接收核算量。",{"省级供需作图数据":regional})
    if 6 in selected:
        families={"Coal family":["coal","coalccs","cchp","cchpccs"],"Gas family":["gas","gasccs","gchp","gchpccs"],"Bioenergy":["bio","bioccs"],"Nuclear":["nuclear"]}
        allrows=[];specs=[]
        for i,(name,techs) in enumerate(families.items()):
            d=cap[cap.technology.isin(techs)].groupby("province_code",as_index=False).capacity.sum();d["family"]=name;allrows.append(d)
            specs.append((d,"capacity",f"{'abcd'[i]}  {name}","Installed capacity (GW)",["blue","red","teal","blue"][i],False))
        fig=prov_panels("Base 2060 | Thermal and nuclear capacity",specs)
        save(fig,"07_常规电源","火电生物质与核电装机","按省展示容量，煤/气系列分别包含CHP和CCS变体，生物质包含有/无CCS。省级色块不虚构电厂坐标；各技术独立全范围色标。",{"常规电源作图数据":pd.concat(allrows,ignore_index=True)})
    if 7 in selected:
        fig,axs=figure_grid("Base 2060 | Hydropower and wave energy")
        for ax,kind,title in [(axs[0],"reservoir","a  Reservoir hydropower"),(axs[1],"ror","b  Run-of-river hydropower")]:
            d=hc[hc.technology.eq(kind)];m.frame(ax,title);norm=m.point_values(ax,d,"capacity_gw","blue" if kind=="reservoir" else "teal",size=8);colorbar(fig,ax,norm,"blue" if kind=="reservoir" else "teal","Capacity (GW / station)")
        d=cap[cap.technology.eq("hydro_aggregate")];m.frame(axs[2],"c  Provincial aggregate hydropower");norm=m.province(axs[2],d,"capacity","teal");colorbar(fig,axs[2],norm,"teal","Capacity (GW / province)")
        wc["capacity_mw"]=wc.capacity_gw*1000;m.frame(axs[3],"d  Wave energy");norm=m.point_values(axs[3],wc,"capacity_mw","blue",size=5);colorbar(fig,axs[3],norm,"blue","Capacity (MW / site)")
        save(fig,"08_水电与波浪能","水电分层与波浪能装机","水库式与径流式用原结果站点，未识别省级聚合水电用省级色块。波浪能单位单独采用MW，不能与GW色条混读；候选记录全保留，浅色不表示大规模开发。既有水电挂接与来水质量问题仍适用，图只展示该生产解，不重新认可其物理输入。",{"水电站点":hydro,"省级聚合水电":cap[cap.technology.eq("hydro_aggregate")],"波浪能站点":wave})
    if 8 in selected:
        specs=[(carbon,"co2_captured_for_storage_mtco2","a  CO2 captured for storage","Mt CO2 / year","blue",False),
               (carbon,"beccs_net_removal_mtco2","b  BECCS net removal","Mt CO2 / year","teal",False),
               (carbon,"dac_removed_mtco2","c  Direct air capture removal","Mt CO2 / year","red",False),
               (carbon,"net_emissions_after_dac_mtco2","d  Net emissions after DAC","Mt CO2 / year","diverging",True)]
        fig=prov_panels("Base 2060 | Carbon capture and net emissions",specs)
        save(fig,"09_碳捕集与封存","省级碳捕集与净排放","展示省级源端碳核算，不把捕集省当成实际封存落点；净排放负值可来自BECCS及DAC抵扣。当前本机已核验包未包含Base2060完整CO2源汇流表，未借用其他情景或24h门禁源汇表。",{"省级碳核算":carbon,"DAC容量及捕集":dac})
        ccs=points[["grid_uid","lon","lat","ccs_pot_mt","ccs_inj_rec_mtpa"]].copy();geo=m.cells(ccs)
        fig,axs=figure_grid("Base 2060 inputs | Geological storage resources",rows=1)
        for ax,col,title,unit,pal in [(axs[0],"ccs_pot_mt","a  Geological storage potential","Mt CO2 / cell","blue"),(axs[1],"ccs_inj_rec_mtpa","b  Recommended injection limit","Mt CO2 / year / cell","teal")]:
            m.frame(ax,title);norm=m.grid(ax,geo,col,pal);colorbar(fig,ax,norm,pal,unit)
        save(fig,"09_碳捕集与封存","地质封存资源输入","此页明确为Base2060匹配的模型输入，不是优化后实际封存布局。储量与年度推荐注入上限分别显示；不以储量代替年流量，不声称全部潜力已建。",{"封存资源输入":ccs})
    if 9 in selected:
        specs=[(regional,"mean_energy_value","a  Mean energy marginal value","CNY / MWh","blue",False),
               (regional,"mean_composite_value","b  Mean composite marginal value","CNY / MWh","red",False),
               (regional,"peak_load_gw","c  Provincial peak load","GW","teal",False),
               (regional,"capacity_margin_gw","d  Capacity adequacy surplus","GW","blue",False)]
        fig=prov_panels("Base 2060 | Regional planning signals",specs)
        save(fig,"10_区域边际信号","省级边际价值与容量充裕性","边际价值为按n_hours加权还原的8760h算术均值，不是负荷加权均价。能量项含年度需求行对偶偏移，复合项另含备用/惯量边际分量；来源source_identity内配对证据PASS。BARRIER_DUAL_ENGINEERING_GRADE，BarConvTol=1e-4；规划指标，不是市场结算价或可兑现收入。",{"省级规划信号":regional})
    if 10 in selected:
        # A quantitative total replaces categorical overpainting of tiny interior-point capacities.
        fig,axs=figure_grid("Base 2060 | Spatial system overview",rows=1,cols=1)
        fig.subplots_adjust(bottom=.25,top=.87)
        ax=axs[0];m.frame(ax,"")
        overview=joined.groupby(["grid_uid","lon","lat"],as_index=False).capacity_gw.sum()
        norm=m.grid(ax,m.cells(overview),"capacity_gw","blue")
        colorbar(fig,ax,norm,"blue","Total wind and solar capacity (GW / 0.25° cell)")
        segments=m.province_segments(tx);width=.02+1.8*tx.capacity_gw/tx.capacity_gw.max()
        ax.add_collection(LineCollection(segments,colors="#354B60",linewidths=width,alpha=.5,zorder=5))
        ax.scatter(hc.geometry.x,hc.geometry.y,s=1.2+9*hc.capacity_gw/hc.capacity_gw.max(),c=TEAL,edgecolors="white",linewidths=.1,zorder=6,rasterized=True)
        ax.scatter(cg.geometry.x,cg.geometry.y,s=6,marker="o",facecolors="white",edgecolors="#263E51",linewidths=.35,zorder=7)
        handles=[Line2D([],[],color='#354B60',lw=1.1,label="Interprovincial corridors"),Line2D([],[],marker='o',color=TEAL,lw=0,label="Hydropower stations",markersize=4),Line2D([],[],marker='o',mfc='white',mec='#263E51',color='none',label="City load centers",markersize=4)]
        fig.legend(handles=handles,loc="lower center",bbox_to_anchor=(.5,.035),ncol=3,frameon=False,columnspacing=1.4,handlelength=1.5,fontsize=7)
        save(fig,"11_全要素总览","电力系统空间总览","底层色块为格网内四技术容量求和（非取最大值），全范围线性色标，无1MW显示阈值。叠加输电容量线宽、水电容量点面积及城市负荷中心定位；各层详细定量图例和分技术分布见专题图。省级火电、核电、储能、碳核算在对应专题图展示，不将其虚构为站点挤在总图。",{"总风光容量格网":overview})
    if 11 in selected:
        totals=cap[cap.asset_group.eq("generation")].groupby("province_code").capacity.sum()
        vre_totals=joined.groupby("province_code").capacity_gw.sum()
        dd=regional[["province_code","province_name_en"]].copy()
        dd["generation_capacity_gw"]=dd.province_code.map(totals)
        dd["vre_capacity_share_pct"]=dd.province_code.map(vre_totals)/dd.generation_capacity_gw*100
        dd["annual_generation_per_gw_gwh"]=regional.generation_gwh/dd.generation_capacity_gw
        dd["generation_demand_ratio"]=regional.generation_gwh/regional.load_gwh
        fig=prov_panels("Base 2060 | Regional portfolio differences",[
            (dd,"generation_capacity_gw","a  Generation capacity","GW","blue",False),
            (dd,"vre_capacity_share_pct","b  Wind and solar capacity share","% of generation capacity","red",False),
            (dd,"annual_generation_per_gw_gwh","c  Fleet equivalent full-load hours","h / year","teal",False),
            (dd,"generation_demand_ratio","d  Generation-to-demand ratio","Ratio","blue",False)])
        save(fig,"05_地区供需差异","地区电源组合与利用差异","发电容量不含储能，风光份额按容量而非电量。全电源等效小时=总发电GWh/发电容量GW，反映技术组合和运行的共同作用，不能当作某项技术的利用小时；供需比不扣除储能损耗及网络损耗，不等同自给率。",{"地区电源组合":dd})
    if 12 in selected:
        # Add a station-level geographic context panel, not an all-technologies maximum merge.
        fig,axs=figure_grid("Base 2060 | Renewable siting and connection distance")
        for i,(ax,(tech,name,pal)) in enumerate(zip(axs,TECHS)):
            d=site[site.technology.eq(tech)].copy();geo=m.cells(d)
            m.frame(ax,f"{'abcd'[i]}  {name}");norm=m.grid(ax,geo,"connection_distance_km",pal);colorbar(fig,ax,norm,pal,"Site-to-connection distance (km)")
        save(fig,"04_省内网络与接入","四技术接入距离","显示已导出的四技术候选记录对应生产接入距离，全部记录保留，未按正新增筛选。该距离是技术专属接入距离，不是地理直线替代值，也不是总trunk距离；图本身不是已建线路长度图。",{"接入距离作图数据":site})
    # Required evidence and local, human-readable index.
    inp.close();write_json(OUT/"核验记录/底图与投影.json",m.audit())
    write_json(OUT/"核验记录/全国合计.json",{"generation_capacity_gw":gen_cap,"annual_load_twh":regional.load_twh.sum(),"annual_generation_twh":regional.generation_twh.sum(),"storage_gw":storage.groupby("technology").capacity_gw.sum().to_dict(),"transmission_gw":tx.capacity_gw.sum(),"figures_this_run":len(contracts)})
    contract_path=OUT/"核验记录/图件登记.json"
    old=json.loads(contract_path.read_text(encoding="utf-8")) if args.only!="all" and contract_path.exists() else []
    merged={r["stem"]:r for r in old};merged.update({r["stem"]:r for r in contracts})
    write_json(contract_path,list(merged.values()))
    print("COMPLETE",len(contracts),flush=True)


if __name__=="__main__":main()
