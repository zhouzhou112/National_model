"""Read preserved P/F runs into a new report directory; never change raw runs.

Usage: python scripts/summarize_flex_numerics.py --p-root PATH --f-root PATH
         --output NEW_DIRECTORY
One deterministic run per setting, Seed=0; no smoothing or statistical inference.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd


def read(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--p-root", required=True, type=Path)
    p.add_argument("--f-root", type=Path)
    p.add_argument("--output", required=True, type=Path)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=False)
    rows=[]; metrics=[]; frames=[]; decisions={}; storage_decisions={}; source=[]
    roots=[a.p_root]+([a.f_root] if a.f_root else [])
    for root in roots:
        if not root.exists(): continue
        for d in sorted(root.iterdir()):
            if not d.is_dir() or not d.name.startswith(("P","F")): continue
            s=read(d/"solver_result.json"); diag=read(d/"service_diagnostics.json")
            scope=read(d/"scope.json"); report=read(d/"report.json")
            if not s: continue
            params=read(d/"solver_parameters.json")
            mem=read(root/(d.name+"_terminal.json"))
            queue=read(root/"queue_status.json")
            if isinstance(queue,list): mem=next((x for x in queue if x["name"]==d.name),{})
            row=dict(run=d.name, state="COMPLETE" if (d/"service_diagnostics.json").exists() or scope.get("case")=="base" else "EXPORT_PENDING_OR_UNAVAILABLE",
                year=report.get("year",2030), hours=scope.get("hours",8760), start=scope.get("start",0),
                status=s.get("Status"), barrier_iterations=s.get("BarIterCount"), runtime_s=s.get("Runtime"),
                wall_s=mem.get("wall_seconds"), peak_rss_gib=mem.get("peak_rss_bytes",np.nan)/2**30,
                gurobi_max_memory_gb=s.get("MaxMemUsed"), objective_million_cny=s.get("ObjVal"),
                ConstrVio=s.get("ConstrVio"), BoundVio=s.get("BoundVio"),
                M_gw_gwh=diag.get("maximum_service_residual_gw_gwh"), parallel=False, **params)
            for key,val in diag.get("physical_qc",{}).items():
                row[key]=val
                metrics.append(dict(run=d.name,family=key,value=val,unit="GWh" if key.endswith("_gwh") else "GW" if key.endswith("_gw") else "dimensionless"))
            for component, worst in diag.get("thermal_worst",{}).items():
                row[component+"_worst"]=json.dumps(worst,sort_keys=True)
            decision=d/"service_decisions.csv"
            if decision.exists():
                table=pd.read_csv(decision); decisions[d.name]=table
                for col in table.columns:
                    if col.endswith("_contract_gw"): row[col]=table[col].sum()
                for col in ("alpha","beta"): row[col+"_by_province"]=json.dumps(table.set_index("province_code")[col].to_dict())
            storage=d/"storage_capacity.csv"
            if storage.exists():
                table=pd.read_csv(storage)
                storage_decisions[d.name]=table
                row["storage_new_gw"]=table.new_capacity_gw.sum(); row["storage_new_gwh"]=table.new_energy_capacity_gwh.sum()
            qc=read(d/"solution_qc.json")
            row["power_balance_gw"]=qc.get("maximum_power_balance_residual_gw")
            profile=d/"thermal_residual_profile.csv.gz"
            if profile.exists():
                frame=pd.read_csv(profile); frame["run"]=d.name; frames.append(frame)
            rows.append(row)
            for name in ("solver_result.json","solver_parameters.json","service_diagnostics.json","service_decisions.csv","storage_capacity.csv","scope.json","effective_config.json","thermal_residual_profile.csv.gz","report.json","solution_qc.json","model_archive/archive_manifest.json","solution_snapshot/snapshot_manifest.json"):
                file=d/name
                if file.exists(): source.append(dict(run=d.name,path=str(file),sha256=hashlib.sha256(file.read_bytes()).hexdigest(),bytes=file.stat().st_size))
    runs=pd.DataFrame(rows); runs.to_csv(a.output/"runs.csv",index=False)
    pd.DataFrame(metrics).to_csv(a.output/"residual_families.csv",index=False)
    (a.output/"source_sha256.json").write_text(json.dumps(source,indent=2),encoding="utf-8")
    differences=[]
    for name,table in decisions.items():
        base="P1" if name in ("P0","P2","P3","P4") else "F1" if name.startswith("F6_F1") else "F2" if name.startswith("F6_F2") else None
        if base not in decisions: continue
        for col in table.columns:
            if col=="province_code":continue
            left=decisions[base].set_index("province_code")[col]; right=table.set_index("province_code")[col]
            for province in left.index:
                relative=abs(right[province]-left[province])/max(abs(left[province]),1e-12)
                if relative>0.01: differences.append(dict(reference=base,run=name,province_code=province,decision=col,reference_value=left[province],value=right[province],absolute_change=abs(right[province]-left[province]),relative_change=relative,denominator_floor=1e-12))
    for name,table in storage_decisions.items():
        base="F1" if name.startswith("F6_F1") else "F2" if name.startswith("F6_F2") else None
        if base not in storage_decisions: continue
        left=storage_decisions[base].set_index(["province_code","technology"])
        right=table.set_index(["province_code","technology"])
        for key in left.index:
            for col in ("new_capacity_gw","new_energy_capacity_gwh"):
                reference=float(left.loc[key,col]); value=float(right.loc[key,col])
                relative=abs(value-reference)/max(abs(reference),1e-12)
                if relative>0.01: differences.append(dict(reference=base,run=name,province_code=key[0],technology=key[1],decision=col,reference_value=reference,value=value,absolute_change=abs(value-reference),relative_change=relative,denominator_floor=1e-12))
    pd.DataFrame(differences,columns=["reference","run","province_code","technology","decision","reference_value","value","absolute_change","relative_change","denominator_floor"]).to_csv(a.output/"decision_changes_above_1pct.csv",index=False)
    conclusion=dict(state="PENDING_F_SERIES",rule=None)
    if not runs.empty:
        r=runs.set_index("run"); m=r.M_gw_gwh
        valid={n for n in ("F1","F2","F4","F5") if n in r.index and pd.notna(m[n]) and r.loc[n,"status"] == 2}
        ratios={f"{x}_to_{y}":float(m[y]/m[x]) if m[x]>0 else (1.0 if m[y]==0 else float("inf")) for x,y in (("F4","F1"),("F1","F5"),("F4","F5")) if x in valid and y in valid}
        if ratios and max(ratios.values())>=3:
            # An observed growth violation is sufficient for the registered
            # stop recommendation; a missing F5 is disclosed, not a failure.
            conclusion=dict(state="STOP_RECOMMENDATION_AWAIT_AUTHOR",rule=3,growth_ratios=ratios,
                            missing_or_nonoptimal_runs=sorted(set(("F1","F2","F4","F5"))-valid))
        elif len(valid)==4:
            conclusion=dict(state="AWAIT_AUTHOR_REVIEW",growth_ratios=ratios,rule=1 if all(m[n]<=1e-3 for n in ("F1","F2","F5")) and max(ratios.values())<3 else None)
            # Rule 2 requires human review of all failed windows, paired timing,
            # iteration overhead and missing/no-solution cases; never auto-promote.
    (a.output/"preregistered_rule_evidence.json").write_text(json.dumps(conclusion,indent=2),encoding="utf-8")
    if frames:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Arial","DejaVu Sans"],"font.size":8,"pdf.fonttype":42,"svg.fonttype":"none","axes.spines.top":False,"axes.spines.right":False})
        full=pd.concat(frames,ignore_index=True)
        # Figure contract: locate postsolve failures in each cyclic decay chain.
        # Quantitative grid, paired heating/cooling panels, full hourly data;
        # all provinces faint, per-hour max bold. No downsampling or smoothing.
        for name,run in full.groupby("run",sort=False):
            fig,axes=plt.subplots(2,1,figsize=(7.2,4.2),layout="constrained",sharex=True)
            plot=[]
            for ax,component,color in zip(axes,("heating","cooling"),("#B26545","#326B95")):
                sub=run[run.component==component].copy(); sub["absolute_residual_gwh"]=sub.signed_residual_gwh.abs()
                for _,prov in sub.groupby("province_code"):
                    ax.plot(prov.hour_position,prov.absolute_residual_gwh,lw=.35,alpha=.25,color=color)
                maximum=sub.groupby("hour_position",as_index=False).absolute_residual_gwh.max()
                ax.plot(maximum.hour_position,maximum.absolute_residual_gwh,color=color,lw=.8)
                ax.axhline(1e-3,color="#444444",ls="--",lw=.7,label="1 MWh threshold")
                ax.set_yscale("symlog",linthresh=1e-10)
                upper=max(float(maximum.absolute_residual_gwh.max()),1e-3)*1.5
                ax.set_ylim(0,upper)
                ax.set_yticks([v for v in (0,1e-9,1e-6,1e-3,1e-1,1,10) if v<=upper])
                ax.set_ylabel("Absolute residual (GWh)")
                ax.set_title(name+" | "+component,loc="left",fontsize=9);ax.legend(loc="upper right",fontsize=7,frameon=False)
                maximum["component"]=component;plot.append(maximum)
            axes[-1].set_xlabel("Hour position within cyclic diagnostic window")
            for suffix in ("png","pdf","svg"):fig.savefig(a.output/(name+"_thermal_residuals."+suffix),dpi=300)
            plt.close(fig)
            pd.concat(plot).to_csv(a.output/(name+"_hourly_max_source.csv"),index=False)
    print(json.dumps(dict(runs=len(rows),conclusion=conclusion)))


if __name__=="__main__":main()
