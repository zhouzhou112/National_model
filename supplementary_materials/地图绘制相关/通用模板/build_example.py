"""Make the four-technology existing-capacity example, without altering inputs."""
from pathlib import Path
import pandas as pd
from china_map import ChinaMap, ROOT, figure_grid, colorbar, export, sha256, write_json


def main():
    source=ROOT.parents[2]/"Gis_process/suitable_area/final_pointV2/tables/final_025deg_points_for_optimization.csv"
    data=pd.read_csv(source)
    assert len(data)==16739 and data.grid_uid.is_unique
    m=ChinaMap();geo=m.cells(data)
    fig,axes=figure_grid("Existing wind and solar capacity | 2025")
    contracts=[]
    for ax,(field,title,palette) in zip(axes,[
        ("existing_onwind_mw","a  Onshore wind","blue"),
        ("existing_offwind_mw","b  Offshore wind","blue"),
        ("existing_cpv_mw","c  Utility PV","red"),
        ("existing_dpv_mw","d  Distributed PV","teal")]):
        total=float(data[field].sum()/1000)
        m.frame(ax,f"{title} | {total:,.0f} GW")
        norm=m.grid(ax,geo,field,palette)
        colorbar(fig,ax,norm,palette,"Capacity (MW / 0.25° cell)")
        contracts.append({"field":field,"total_gw":total,"vmax_mw":norm.vmax,"all_16739_cells_retained":True})
    out=ROOT/"示例图_现有风光装机"
    export(fig,out/"现有风光装机_四技术示例",data[["grid_uid","lon","lat","existing_onwind_mw","existing_offwind_mw","existing_cpv_mw","existing_dpv_mw"]])
    write_json(out/"数据与底图核验.json",{"source":str(source),"sha256":sha256(source),"panels":contracts,"cartography":m.audit()})
    print(out)


if __name__=="__main__":main()
