"""Reusable, exact-size China maps; no model/solver imports or upstream writes.

Python 3.10+, matplotlib, geopandas/pyogrio, pyproj, shapely, numpy, pandas,
Pillow and pypdf. See README.md for API and command-line examples.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, Normalize, TwoSlopeNorm
from matplotlib.ticker import FuncFormatter, MaxNLocator
import numpy as np
import pandas as pd
from PIL import Image
from pypdf import PdfReader
from pyproj import CRS, Transformer
from shapely import make_valid
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
PROVINCES = Path(r"D:\gisproject\gis地图数据\2024最新权威全国行政区数据0512\2024最新权威全国行政区数据0512\中国标准行政区划数据GS（2024）0650号\中国_省_市_县shp格式\中国_省.shp")
NINE = Path(r"D:\gisproject\九段线\11\九段线.shp")
PROJECTION = Path(r"D:\Work\联合国地球大数据报告申报\12月书稿\制图指南及模板-2025--供参考\制图指南及模板-2025--供参考\投影文件\中国底图投影.prj")
# Adopt Module 01's approved palette and Module 01/03 cartographic layout.
BLUE, RED, TEAL = "#0F4D92", "#B64342", "#42949E"
PALETTES = {
    "blue": LinearSegmentedColormap.from_list("map_blue", ["#E6EEF5", "#BBD5EC", BLUE]),
    "red": LinearSegmentedColormap.from_list("map_red", ["#F8E9E7", "#F1C7C2", RED]),
    "teal": LinearSegmentedColormap.from_list("map_teal", ["#E7F2F1", "#B8E1DD", TEAL]),
    "diverging": LinearSegmentedColormap.from_list("map_signed", [BLUE, "#FAF8F5", RED]),
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def style():
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 7.5, "axes.titlesize": 8.5, "axes.titleweight": "bold", "axes.labelsize": 7.5,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.5, "pdf.fonttype": 42,
        "axes.linewidth": .45, "figure.facecolor": "white", "savefig.facecolor": "white",
        "axes.unicode_minus": True, "savefig.bbox": None})


def figure_grid(title, rows=2, cols=2):
    """7 inches wide; 2x2=6.3, 1x2=3.5, 3x2=8.6 inches high."""
    style()
    height = {1: 3.5, 2: 6.3, 3: 8.6}[rows] if cols == 2 else 6.2
    fig, axes = plt.subplots(rows, cols, figsize=(7, height), squeeze=False)
    fig.subplots_adjust(left=.025, right=.985, bottom=.22 if rows == 1 else .105,
                        top=.85 if rows == 1 else .91, wspace=.09, hspace=.46)
    if cols == 1:fig.subplots_adjust(bottom=.22,top=.90)
    fig.suptitle(title, x=.035, y=.978, ha="left", va="top", fontsize=11, fontweight="bold", color="#233B49")
    return fig, axes.ravel()


def linear_norm(values, signed=False, limits=None):
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if not len(finite):
        raise ValueError("No finite data for colour normalization")
    if signed:
        limit = max(float(np.max(np.abs(finite))), 1e-12) if limits is None else max(abs(limits[0]), abs(limits[1]))
        return TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit)
    if finite.min() < -1e-10:
        raise ValueError("Negative values require an explicitly signed colour scale")
    if limits is None and float(finite.max()) == 0:
        norm = Normalize(0, 1)
        norm._constant_zero = True
        return norm
    lo, hi = (0., max(float(finite.max()), 1e-12)) if limits is None else limits
    if finite.min() < lo-1e-9 or finite.max() > hi+1e-9:
        raise ValueError("Requested scale would clip data")
    return Normalize(lo, hi)


def colorbar(fig, ax, norm, palette, label):
    cax = ax.inset_axes([.13, -.155, .74, .045], transform=ax.transAxes)
    cmap = PALETTES[palette]
    constant_zero = getattr(norm, "_constant_zero", False)
    display_norm = Normalize(-.5, .5) if constant_zero else norm
    display_cmap = ListedColormap([cmap(0)]) if constant_zero else cmap
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=display_norm, cmap=display_cmap), cax=cax, orientation="horizontal")
    ticks=MaxNLocator(nbins=4,steps=[1,2,2.5,5,10]).tick_values(norm.vmin,norm.vmax)
    ticks=ticks[(ticks>=norm.vmin)&(ticks<=norm.vmax)]
    cb.set_ticks([0] if constant_zero else ticks)
    def format_tick(x, _):
        if x == 0: return "0"
        if abs(x) >= 100: return f"{x:,.0f}"
        if abs(x) >= 10: return f"{x:.1f}".rstrip("0").rstrip(".")
        if abs(x) >= .1: return f"{x:.2f}".rstrip("0").rstrip(".")
        return f"{x:.3g}"
    cb.ax.xaxis.set_major_formatter(FuncFormatter(format_tick))
    cb.ax.minorticks_off(); cb.ax.tick_params(length=2, width=.4, pad=1.5, labelsize=6.5)
    cb.outline.set_edgecolor("#9BA5A9"); cb.outline.set_linewidth(.4)
    cb.set_label(label, fontsize=7, labelpad=2)
    fig._map_colorbars = getattr(fig, "_map_colorbars", []) + [{"norm": type(norm).__name__, "vmin": float(norm.vmin), "vmax": 0.0 if constant_zero else float(norm.vmax), "constant_zero": constant_zero, "unit_label": label, "palette": palette,"ticks":cb.get_ticks().tolist()}]
    return cb


class ChinaMap:
    def __init__(self, provinces=PROVINCES, nine=NINE, projection=PROJECTION):
        self.paths = [Path(provinces), Path(nine), Path(projection)]
        self.crs = CRS.from_wkt(Path(projection).read_text(encoding="utf-8"))
        self.forward = Transformer.from_crs(4326, self.crs, always_xy=True)
        raw = gpd.read_file(provinces)
        self.repair = []
        for i in raw.index[~raw.is_valid]:
            before = raw.loc[i, "geometry"]
            after = make_valid(before)
            self.repair.append({"gb": str(raw.loc[i, "gb"]), "operation": "make_valid_in_memory_only",
                                "before_area_degree2": before.area, "after_area_degree2": after.area,
                                "relative_area_change": abs(after.area-before.area)/max(before.area, 1e-30)})
            raw.loc[i, "geometry"] = after
        self.provinces = raw.to_crs(self.crs)
        self.provinces["province_code"] = pd.to_numeric(self.provinces.gb).astype(int)//10000 % 100
        assert self.provinces.province_code.is_unique and self.provinces.is_valid.all()
        self.nine = gpd.read_file(nine).to_crs(self.crs)
        xmin, _, xmax, ymax = self.provinces.total_bounds
        width = xmax-xmin
        _, cut = self.forward.transform(105, 15.5)
        self.extent = (xmin-.03*width, xmax+.30*width, cut, ymax+.06*width)
        self.aspect = (self.extent[3]-self.extent[2])/(self.extent[1]-self.extent[0])
        # Exact Module 01/03 inset extent: complete line bounds + 10% padding.
        ix0, iy0, ix1, iy1 = self.nine.total_bounds
        px, py = .10*(ix1-ix0), .10*(iy1-iy0)
        self.inset_extent = (ix0-px, ix1+px, iy0-py, iy1+py)
        self.centers = self.provinces.set_index("province_code").geometry.representative_point()

    def points(self, df):
        if df[["lon", "lat"]].isna().any().any():
            raise ValueError("Missing coordinates")
        return gpd.GeoDataFrame(df.copy(), geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326).to_crs(self.crs)

    def cells(self, df):
        if not df.grid_uid.is_unique:
            raise ValueError("One row per grid cell is required")
        if not np.allclose(df.lon*4, np.round(df.lon*4), atol=1e-7) or not np.allclose(df.lat*4, np.round(df.lat*4), atol=1e-7):
            raise ValueError("Expected quarter-degree grid centers")
        return gpd.GeoDataFrame(df.copy(), geometry=[box(x-.125,y-.125,x+.125,y+.125) for x,y in zip(df.lon,df.lat)], crs=4326).to_crs(self.crs)

    def frame(self, ax, title):
        """Set the base; export adds approved decorations after all data layers."""
        self.provinces.plot(ax=ax, facecolor="#F5F7F8", edgecolor="#9B9B9B", linewidth=.35, zorder=0)
        ax.set_title(title, loc="left", pad=5)
        ax._china_map = {"owner": self, "decorated": False}
        self._set_extent(ax)
        return ax

    def _set_extent(self, ax):
        x0,x1,y0,y1 = self.extent
        ax.set(xlim=(x0,x1), ylim=(y0,y1))
        ax.set_box_aspect(self.aspect)
        ax.set_aspect("equal", adjustable="box")
        ax.set_autoscale_on(False)
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values(): spine.set_visible(False)

    def finish(self, ax):
        """Module 01/03 horizontal scale, upright grid north and sea inset.

        The nominal 500 km is 500,000 projected metres, as in the approved
        source. It is not a claim of globally exact geodesic distance.
        """
        if ax._china_map["decorated"]:
            self._set_extent(ax)
            return
        x0,x1,y0,y1 = self.extent; xs=x1-x0; ys=y1-y0
        self.provinces.boundary.plot(ax=ax,color="#767676",linewidth=.28,zorder=8)
        self.nine.plot(ax=ax,color="#4C4C4C",linewidth=.42,linestyle=(0,(4,3)),zorder=9)
        self._set_extent(ax)
        nx,tip,tail=x1-.055*xs,y1-.10*ys,y1-.19*ys
        ax.annotate("",xy=(nx,tip),xytext=(nx,tail),arrowprops={"arrowstyle":"-|>","lw":.72,"color":"#1E3B3F"},zorder=20,clip_on=False)
        ax.text(nx,tip+.015*ys,"N",ha="center",va="bottom",fontsize=6.2,color="#1E3B3F",zorder=20)
        sx,sy,length=x0+.12*xs,y0+.10*ys,500000.
        scale_line,=ax.plot([sx,sx+length],[sy,sy],color="#555555",lw=.55,zorder=20)
        for px,label in [(sx,"0"),(sx+length,"500 km")]:
            ax.plot([px,px],[sy-.008*ys,sy+.008*ys],color="#555555",lw=.55,zorder=20)
            ax.text(px,sy-.024*ys,label,ha="center",va="top",fontsize=5,color="#555555",zorder=20)
        inset=ax.inset_axes([.785,.055,.180,.340],zorder=30)
        inset.set_facecolor("white")
        self.provinces.boundary.plot(ax=inset,color="#B4B4B4",linewidth=.24,zorder=1)
        self.nine.plot(ax=inset,color="#3B3B3B",linewidth=.60,linestyle=(0,(4,3)),zorder=2)
        a,b,c,d=self.inset_extent;inset.set(xlim=(a,b),ylim=(c,d));inset.set_aspect("equal")
        inset.set_xticks([]);inset.set_yticks([])
        for spine in inset.spines.values():spine.set_visible(True);spine.set_color("#777777");spine.set_linewidth(.45)
        ax._china_map.update({"inset":inset,"scale_line":scale_line,"north_points":[[nx,tail],[nx,tip]],"decorated":True})

    def borders(self, ax):
        self.provinces.boundary.plot(ax=ax,color="#8C999F",linewidth=.24,zorder=8)

    def grid(self, ax, geo, column, palette="blue", norm=None):
        norm=norm or linear_norm(geo[column]);geo.plot(ax=ax,column=column,cmap=PALETTES[palette],norm=norm,edgecolor="none",zorder=3,rasterized=True)
        self.borders(ax)
        return norm

    def province(self, ax, df, column, palette="blue", signed=False, norm=None):
        if not df.province_code.is_unique: raise ValueError("Duplicate province codes")
        geo=self.provinces.merge(df[["province_code",column]],on="province_code",how="left",validate="one_to_one")
        norm=norm or linear_norm(df[column], signed)
        geo.plot(ax=ax,column=column,cmap=PALETTES[palette],norm=norm,edgecolor="#97A3A9",linewidth=.28,zorder=3,
                 missing_kwds={"color":"#EEEEEE","hatch":"////","edgecolor":"#BCC2C5"})
        return norm

    def point_values(self, ax, geo, column, palette="blue", norm=None, size=9):
        norm=norm or linear_norm(geo[column]);order=geo.sort_values(column)
        ax.scatter(order.geometry.x,order.geometry.y,c=order[column],s=size,cmap=PALETTES[palette],norm=norm,linewidths=.15,edgecolors="#FFFFFF",zorder=4,rasterized=True)
        return norm

    def lines(self, ax, segments, values, palette="blue", arrows=False, linewidth=(.12,2.2)):
        vals=np.asarray(values,float);ab=np.abs(vals);norm=linear_norm(ab)
        order=np.argsort(ab);segments=np.asarray(segments)[order];vals=vals[order];ab=ab[order]
        widths=linewidth[0]+(linewidth[1]-linewidth[0])*ab/max(ab.max(),1e-30)
        lc=LineCollection(segments,cmap=PALETTES[palette],norm=norm,linewidths=widths,zorder=4,alpha=.9)
        lc.set_array(ab);ax.add_collection(lc)
        if arrows:
            for seg,value,width in zip(segments,vals,widths):
                if value == 0:continue
                start,end=(seg[0],seg[1]) if value>0 else (seg[1],seg[0])
                delta=end-start
                ax.annotate("",xy=start+.60*delta,xytext=start+.44*delta,
                            arrowprops={"arrowstyle":"-|>","color":PALETTES[palette](norm(abs(value))),"lw":max(.22,width*.65),"mutation_scale":3.0+width},zorder=6)
        return norm

    def province_segments(self, df, first="from_province_code", second="to_province_code"):
        return np.array([[[self.centers.loc[a].x,self.centers.loc[a].y],[self.centers.loc[b].x,self.centers.loc[b].y]] for a,b in zip(df[first],df[second])])

    def audit(self):
        hashes={}
        for p in self.paths:
            for q in ([p.with_suffix(s) for s in [".shp",".shx",".dbf",".prj",".cpg"]] if p.suffix==".shp" else [p]):
                if q.exists():hashes[str(q)]={"bytes":q.stat().st_size,"sha256":sha256(q)}
        ix0,ix1,iy0,iy1=self.inset_extent; bounds=self.nine.total_bounds
        return {"target_crs_wkt":self.crs.to_wkt(),"main_extent":self.extent,"box_aspect":self.aspect,
                "inset_extent":self.inset_extent,"nine_dash_features":len(self.nine),
                "all_nine_dash_within_inset":bool(ix0<bounds[0]<bounds[2]<ix1 and iy0<bounds[1]<bounds[3]<iy1),
                "source_files":hashes,"geometry_repairs":self.repair,
                "style_source":"modules/01_wind_solar_suitability/scripts/generate_module_outputs.py; modules/03_load_reconstruction_and_centers/scripts/generate_module_outputs.py",
                "north_arrow":"upright projected grid north, approved module convention", "scale_bar":"horizontal 0-500 km; 500000 projected metres, approved module convention"}


def export(fig, stem, data=None):
    """Exact dimensions, font embedding, scale and projection checks per figure."""
    stem=Path(stem);stem.parent.mkdir(parents=True,exist_ok=True)
    for ax in fig.axes:
        if hasattr(ax,"_china_map"):ax._china_map["owner"].finish(ax)
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    outside=[]
    from matplotlib.text import Text
    for text in fig.findobj(Text):
        if not text.get_visible() or not text.get_text():continue
        bb=text.get_window_extent(renderer)
        if bb.x0 < -.5 or bb.y0 < -.5 or bb.x1 > fig.bbox.width+.5 or bb.y1 > fig.bbox.height+.5:
            outside.append(text.get_text())
    if outside:raise ValueError("Text outside canvas: "+repr(outside))
    map_checks=[]
    for ax in fig.axes:
        if not hasattr(ax,"_china_map"):continue
        origin=ax.transData.transform((0,0));dx=np.linalg.norm(ax.transData.transform((1000,0))-origin);dy=np.linalg.norm(ax.transData.transform((0,1000))-origin)
        assert np.isclose(dx,dy,rtol=1e-8),"Geographic stretching"
        inset=ax._china_map["inset"]
        scale=ax.transData.transform(ax._china_map["scale_line"].get_xydata())
        north=ax.transData.transform(ax._china_map["north_points"])
        assert np.isclose(scale[0,1],scale[1,1],atol=1e-8),"Tilted scale bar"
        assert np.isclose(north[0,0],north[1,0],atol=1e-8),"Tilted module north arrow"
        assert ax.bbox.contains(*scale[0]) and ax.bbox.contains(*scale[1])
        assert ax.bbox.contains(*north[0]) and ax.bbox.contains(*north[1])
        map_checks.append({"title":ax.get_title(loc="left"),"equal_projected_scale":True,"pixel_per_km":float(dx),
                           "main_xlim":list(ax.get_xlim()),"main_ylim":list(ax.get_ylim()),
                           "inset_xlim":list(inset.get_xlim()),"inset_ylim":list(inset.get_ylim()),
                           "scale_projected_m":500000,"scale_horizontal":True,"scale_display_dy_px":float(scale[1,1]-scale[0,1]),
                           "north_upright":True,"inset_visible":bool(inset.get_visible()),"cartography_source":"approved Module 01/03"})
    for ext in ["pdf","png"]:fig.savefig(stem.with_suffix("."+ext),dpi=450,bbox_inches=None)
    inch=fig.get_size_inches().tolist();plt.close(fig)
    with Image.open(stem.with_suffix(".png")) as im:
        pixels=im.size;dpi=im.info.get("dpi");assert pixels==tuple(round(x*450) for x in inch)
    page=PdfReader(stem.with_suffix(".pdf")).pages[0]
    pdf_size=[float(page.mediabox.width),float(page.mediabox.height)]
    assert np.allclose(pdf_size,np.array(inch)*72,atol=1e-6)
    fonts={}
    for k,v in page["/Resources"]["/Font"].items():
        font=v.get_object(); descendants=font.get("/DescendantFonts",[])
        desc=(descendants[0].get_object().get("/FontDescriptor") if descendants else font.get("/FontDescriptor"))
        descriptor=desc.get_object() if desc else {}
        fonts[k]={"font":str(font.get("/BaseFont")),"embedded":any(n in descriptor for n in ["/FontFile","/FontFile2","/FontFile3"])}
    assert fonts and all(f["embedded"] for f in fonts.values())
    report={"width_height_in":inch,"pdf_mediabox_pt":pdf_size,"png_pixels":pixels,"png_dpi":dpi,
            "fonts":fonts,"map_panels":map_checks,"colour_scales":getattr(fig,"_map_colorbars",[]),
            "text_outside_canvas":outside,"visual_review":"PENDING","files":{ext:{"sha256":sha256(stem.with_suffix('.'+ext)),"bytes":stem.with_suffix('.'+ext).stat().st_size} for ext in ["pdf","png"]}}
    if data is not None:data.to_csv(stem.parent/(stem.name+"_作图数据.csv"),index=False,encoding="utf-8-sig")
    write_json(stem.parent/(stem.name+"_检查.json"),report)
    return report


def main():
    p=argparse.ArgumentParser(description="Render a single full-range linear grid, point or province map.")
    p.add_argument("--csv",type=Path,required=True);p.add_argument("--value",required=True)
    p.add_argument("--kind",choices=["grid","point","province"],default="grid")
    p.add_argument("--title",required=True);p.add_argument("--unit",required=True)
    p.add_argument("--palette",choices=list(PALETTES),default="blue")
    p.add_argument("--output",type=Path,required=True,help="Output stem, without suffix")
    p.add_argument("--provinces",type=Path,default=PROVINCES);p.add_argument("--nine-dash",type=Path,default=NINE);p.add_argument("--projection",type=Path,default=PROJECTION)
    a=p.parse_args();d=pd.read_csv(a.csv);m=ChinaMap(a.provinces,a.nine_dash,a.projection)
    fig,axs=figure_grid(a.title,1,1);ax=axs[0];m.frame(ax,"")
    norm=linear_norm(d[a.value],signed=a.palette=="diverging")
    if a.kind=="province":m.province(ax,d,a.value,a.palette,norm=norm)
    elif a.kind=="grid":m.grid(ax,m.cells(d),a.value,a.palette,norm)
    else:m.point_values(ax,m.points(d),a.value,a.palette,norm)
    colorbar(fig,ax,norm,a.palette,a.unit);export(fig,a.output,d)
    write_json(a.output.parent/(a.output.name+"_底图检查.json"),m.audit())


if __name__=="__main__":main()
