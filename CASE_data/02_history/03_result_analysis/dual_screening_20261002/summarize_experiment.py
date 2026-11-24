"""Reproduce paired performance/QC table and MPS structural identity checks."""
from pathlib import Path
import csv
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent


def mps_identity(path):
    parts={};bounds={}; section=None
    with path.open(encoding="ascii") as f:
        for line in f:
            if not line.strip() or line.startswith("*"):continue
            if line[0] not in " \t":
                section=line.split()[0];parts.setdefault(section,hashlib.sha256())
            if section=="BOUNDS" and line[0] in " \t":
                t=line.split(); bounds.setdefault(t[2],[]).append([t[0],float(t[3]) if len(t)>3 else None])
            else:parts[section].update(line.encode("ascii"))
    return {k:v.hexdigest() for k,v in parts.items() if k!="BOUNDS"},bounds


def main():
    rows=[]
    for p in sorted(HERE.glob("local_*/result.json")):
        d=json.loads(p.read_text())
        for r in d["rounds"]:
            rd=p.parent/f"round_{r['round']:02d}"
            log=(rd/"gurobi.log").read_text(encoding="utf-8",errors="replace")
            stat={}
            for label in ["Dense cols","Factor NZ","Factor Ops"]:
                m=re.search(re.escape(label)+r"\s*:\s*([\d.eE+\-]+)",log)
                stat[label.lower().replace(" ","_")]=float(m[1]) if m else None
            m=re.search(r"Presolved: ([\d,]+) rows, ([\d,]+) columns, ([\d,]+) nonzeros",log)
            if m:
                stat.update(dict(zip(["presolved_rows","presolved_columns","presolved_nnz"],[int(x.replace(',','')) for x in m.groups()])))
            it=[json.loads(s) for s in (rd/"barrier.jsonl").read_text().splitlines() if s.strip()]
            deltas=[it[i]["runtime"]-it[i-1]["runtime"] for i in range(1,len(it)) if it[i]["iteration"]>=2]
            rows.append(dict(case=p.parent.name,mode=d["mode"],hours=d["hours"],round=r["round"],
                status=r["status"],objective=r.get("objective"),runtime_seconds=r["runtime"],work=r["work"],
                iterations=r["barrier_iterations"],retained_expandable=r["retained_expandable"],excluded=r["excluded"],
                reenter=r.get("reenter_count"),min_excluded_rc=r.get("min_excluded_rc"),
                physical_qc=r.get("physical_qc_status"),pricing_gate=r.get("numerical_pricing_gate"),
                mean_iter_seconds_after_1=sum(deltas)/len(deltas) if deltas else None,**stat))
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with (HERE/"paired_results.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    full=HERE/"local_case3_24_full"
    screen=HERE/"local_case3_24_screen"
    audit={}
    if (screen/"result.json").exists():
        f=json.loads((full/"result.json").read_text());s=json.loads((screen/"result.json").read_text())
        fm,fb=mps_identity(full/"round_00/model.mps")
        sm,sb=mps_identity(screen/"round_00/model.mps")
        changed=sorted(k for k in set(fb)|set(sb) if fb.get(k)!=sb.get(k))
        if fm!=sm:raise AssertionError("A/RHS/rows/objective changed between paired models")
        if not all(k.startswith("vre_new_gw[") for k in changed):raise AssertionError("Non-VRE-new bound changed")
        # Confirm exact restricted UB=0 for every altered variable, never a
        # change to an inherited floor or to another source of flexibility.
        if not all(sb[k] in ([["FX",0.0]],[["UP",0.0]]) for k in changed):
            raise AssertionError("Unexpected restricted bound")
        lf=f["rounds"][-1];ls=s["rounds"][-1]
        audit=dict(matrix_rhs_objective_sections_identical=True,section_sha256=fm,
            changed_bound_columns=len(changed),changed_family="vre_new_gw only",restricted_bound_gw=0,
            absolute_objective_difference_million_cny=abs(lf["objective"]-ls["objective"]),
            relative_objective_difference=abs(lf["objective"]-ls["objective"])/max(1,abs(lf["objective"])),
            full_solver_seconds=sum(x["runtime"] for x in f["rounds"]),
            screen_all_rounds_solver_seconds=sum(x["runtime"] for x in s["rounds"]),
            screen_reentered_sites=s["screen_reentry_added"],final_pricing_gate=ls["numerical_pricing_gate"],
            final_physical_qc=ls["physical_qc_status"])
        for case in [full,screen]:
            checks=json.loads((case/"round_00/pricing_identity_checks.json").read_text())
            audit[case.name+"_max_rc_identity_error"]=max(x["error"] for x in checks)
        audit["warning"]="24h zero VRE investment and zero flex enrollment; mechanism validation, not annual speed or scientific evidence"
        (HERE/"paired_identity_audit.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(rows=rows,audit=audit),indent=2))


if __name__=="__main__":main()
