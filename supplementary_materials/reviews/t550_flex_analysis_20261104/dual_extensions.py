"""Output-only additions and fail-closed identity checks. No solver imports."""
import csv
import gzip
import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path
import numpy as np


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def table(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def csv_out(path, rows, fields=None):
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def verify_inputs(root, out):
    """Hash every consumed scientific input before opening it for computation."""
    started = time.time()
    root, out = Path(root), Path(out)
    assert root.parent == Path("/home/zz2/National_model_server/cloud_backup")
    assert out.parent == Path("/home/zz2/National_model_server/analysis_tools_20261020")
    backup = json.loads((root / "backup_manifest.json").read_text())
    manifest_path = root / "output_8760/result_manifest.json"
    assert sha(manifest_path) == backup["source_result_manifest_sha256"], "result manifest SHA"
    manifest = json.loads(manifest_path.read_text())
    index = {x["path"]: x for x in manifest["files"]}
    bindex = {x["path"]: x for x in backup["files"]}
    names = ["barrier_checkpoint/barrier_checkpoint_manifest.json",
             "model_archive/archive_manifest.json", "model_archive/original.mps.gz",
             "barrier_checkpoint/dual_barpi.npy", "vre_capacity.csv",
             "transmission_capacity.csv", "load_center_annual_balance.csv",
             "load_center_intra_transmission.csv", "province_annual_load_center_accounts.csv",
             "hourly_marginal_prices.csv.gz"]
    verified = {}
    for name in names:
        p = root / "output_8760" / name
        expected = index.get(name, bindex.get("output_8760/" + name))
        assert expected, "Unanchored input " + name
        h = sha(p)
        assert h == expected["sha256"], "Input SHA mismatch: " + name
        verified[name] = dict(sha256=h, bytes=p.stat().st_size, source=str(p))
        print("SHA PASS", name, flush=True)
    checkpoint = json.loads((root / "output_8760" / names[0]).read_text())
    ordering = checkpoint["lp_ordering"]
    assert ordering["constraint_vector"] == "raw_original_model_linear_constraint_index_order"
    assert checkpoint["vectors"]["dual"]["sha256"] == verified["barrier_checkpoint/dual_barpi.npy"]["sha256"]
    archive = json.loads((root / "output_8760" / names[1]).read_text())
    assert next(x for x in archive["files"] if x["path"] == "original.mps.gz")["sha256"] == verified["model_archive/original.mps.gz"]["sha256"]
    result = dict(status="PASS", release=str(root), inputs=verified, ordering=ordering,
                  checkpoint_source=checkpoint["source"], seconds=time.time()-started)
    write_json(out / "input_identity.json", result)
    (out / "inputs_sha256.txt").write_text(
        "".join(x["sha256"] + "  " + x["source"] + "\n" for x in verified.values()), encoding="utf-8")
    return result


class RowsObserver:
    """Stream MPS ROWS; emit T3/T4 only after exact ordering digest matches."""
    def __init__(self, root, out, pi, identity):
        self.root, self.out, self.pi = Path(root) / "output_8760", Path(out), pi
        self.ordering = identity["ordering"]
        self.expected = self.ordering["constraints"]
        assert len(pi) == self.expected and np.isfinite(pi).all()
        self.digest = hashlib.sha256(b"cispo_raw_lp_constraint_order_v1\0")
        self.digest.update(self.expected.to_bytes(8, "big"))
        self.index = 0
        self.families, self.examples, self.senses = Counter(), {}, {}
        self.lines = table(self.root / "transmission_capacity.csv")
        self.centers = table(self.root / "load_center_annual_balance.csv")
        self.intra = table(self.root / "load_center_intra_transmission.csv")
        assert len(self.lines) == 411 and len(self.centers) == 337 and len(self.intra) == 642
        self.ac = [i for i, r in enumerate(self.lines) if r["preset_technology"].upper() == "AC"]
        self.dc = [i for i, r in enumerate(self.lines) if r["preset_technology"].upper() == "DC"]
        assert len(self.ac) + len(self.dc) == len(self.lines)
        self.hourly = np.full((len(self.lines), 8760), np.nan)
        self.annual = []
        self.selected_counts = Counter()
        self.started = time.time()

    def consume(self, sense, name):
        i = self.index
        encoded = name.encode("utf-8")
        self.digest.update(i.to_bytes(8, "big"))
        self.digest.update(len(encoded).to_bytes(8, "big"))
        self.digest.update(encoded)
        self.digest.update({"E": "=", "L": "<", "G": ">"}[sense].encode())
        self.digest.update(b"\0")
        self.index += 1
        # Numeric suffixes in scalar names and numeric bracket indices are
        # catalogued as index placeholders, with actual first/last examples.
        family = re.sub(r"\d+", "#", name.split("[", 1)[0])
        self.families[family] += 1
        self.examples.setdefault(family, [name, name])[1] = name
        self.senses.setdefault(family, Counter())[sense] += 1
        if name.startswith(("ac_line_shared_capacity_hourly[", "dc_line_forward_capacity_hourly[")):
            fam, indices = name.split("[")
            subset, hour = map(int, indices.rstrip("]").split(","))
            line = (self.ac if fam.startswith("ac_") else self.dc)[subset]
            assert sense == "L" and np.isnan(self.hourly[line, hour]), name
            self.hourly[line, hour] = self.pi[i]
            self.selected_counts[fam] += 1
        elif name.startswith("load_center_annual_energy_balance_"):
            city = int(name.rsplit("_", 1)[-1])
            r = self.centers[city]
            self.add_annual(name, "load_center_annual_energy_balance", i, sense, city, r["province_code"], city, r["load_center_id"])
        elif name.startswith("intra_load_center_annual_capacity["):
            edge = int(name.split("[")[1].rstrip("]"))
            r = self.intra[edge]
            self.add_annual(name, "intra_load_center_annual_capacity", i, sense, edge, r["province_code"], "", r["intra_edge_id"])
        elif name.startswith("province_annual_") and re.search(r"_p\d+$", name):
            fam, province = name.rsplit("_p", 1)
            self.add_annual(name, fam, i, sense, province, province, "", "")

    def add_annual(self, name, family, row_index, sense, index, province, city, key):
        self.selected_counts[family] += 1
        self.annual.append(dict(row_family=family, row_name=name, index=index,
                               province_code=province, city_index=city,
                               pi_million_cny_per_gwh=float(self.pi[row_index]),
                               original_row_index=row_index, row_sense=sense,
                               entity_id=key, unit="million CNY/GWh"))

    def finish(self):
        inventory = [dict(row_family=f, count=c, senses=json.dumps(self.senses[f]),
                          first_row=self.examples[f][0], last_row=self.examples[f][1])
                     for f, c in sorted(self.families.items())]
        csv_out(self.out / "row_family_inventory.csv", inventory)
        valid = self.index == self.expected and self.digest.hexdigest() == self.ordering["constraint_order_digest"]["sha256"]
        write_json(self.out / "row_order_verification.json", dict(
            status="PASS" if valid else "FAIL", mps_rows=self.index, barpi_entries=len(self.pi),
            expected_rows=self.expected, actual_digest=self.digest.hexdigest(),
            expected_digest=self.ordering["constraint_order_digest"]["sha256"],
            constraint_vector=self.ordering["constraint_vector"], seconds=time.time()-self.started))
        assert valid, "STOP: MPS row count/order differs from raw BarPi"
        assert self.selected_counts["load_center_annual_energy_balance"] == 337
        assert self.selected_counts["intra_load_center_annual_capacity"] == 642
        assert np.isfinite(self.hourly).all(), "STOP: corridor family incomplete/ambiguous"
        # Inventory written first. Actual families are confirmed against MPS
        # names, senses, complete index coverage, and 411 transmission records.
        csv_out(self.out / "annual_row_duals.csv", self.annual)
        months = {}
        with gzip.open(self.root / "hourly_marginal_prices.csv.gz", "rt", encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                hour = int(row["hour_index"])
                month = int(row["datetime_bj"][5:7])
                if hour in months:
                    assert months[hour] == month
                months[hour] = month
                if len(months) == 8760:
                    break
        assert set(months) == set(range(8760))
        monthly, corridor = [], []
        for line, meta in enumerate(self.lines):
            values = self.hourly[line]
            signed = float(values.sum())
            capacity = float(meta["capacity_gw"])
            common = dict(line_index=line, line_id=meta["line_id"],
                          from_province=meta["from_province_code"], to_province=meta["to_province_code"],
                          voltage_class="", ac_or_dc=meta["preset_technology"],
                          capacity_gw=capacity, new_capacity_gw=meta["new_capacity_gw"])
            corridor.append(dict(common,
                rent_million_cny_per_year=signed, rent_per_gw=signed/capacity if capacity else "",
                hours_binding=int((np.abs(values)>1e-6).sum()),
                pi_max=float(values.max()), pi_p99=float(np.quantile(values,.99)), pi_median=float(np.median(values)),
                hours_binding_forward=int((np.abs(values)>1e-6).sum()) if line in self.dc else "",
                hours_binding_reverse="", pi_sum_million_cny_per_gw=signed,
                marginal_capacity_value_million_cny_per_gw=-signed,
                capacity_rent_million_cny_per_year=-signed*capacity,
                raw_pi_unit="million CNY/GW", capacity_row_sense="L",
                direction_note="shared_forward_reverse" if line in self.ac else "forward_only"))
            for month in range(1,13):
                selected = values[[h for h,m in months.items() if m==month]]
                total = float(selected.sum())
                monthly.append(dict(line_index=line, month=month, pi_sum_million_cny_per_gw=total,
                                    hours_binding=int((np.abs(selected)>1e-6).sum()),
                                    marginal_capacity_value_million_cny_per_gw=-total,
                                    capacity_rent_million_cny=-total*capacity))
        csv_out(self.out / "corridor_duals.csv", corridor)
        csv_out(self.out / "corridor_duals_monthly.csv", monthly)
        write_json(self.out / "row_extraction_summary.json", dict(status="PASS",
            result_label="初步结果", dual_grade="BARRIER_DUAL_ENGINEERING_GRADE",
            T3_corridors=len(corridor), T3_monthly_rows=len(monthly), T4_rows=len(self.annual),
            selected_families=dict(self.selected_counts), seconds=time.time()-self.started,
            no_province_offset_correction=True, no_clipping=True,
            signs="Min LP, capacity rows L: raw pi normally <=0. Raw signed pi retained; capacity value = -sum(pi).",
            units_note="Task legacy rent_million_cny_per_year stores requested sum(pi), whose actual unit is million CNY/GW, NOT cash/year. Legacy rent_per_gw=sum(pi)/capacity has unit million CNY/GW^2. Use explicitly unit-named columns. capacity_rent=-sum(pi)*capacity is million CNY.",
            binding_note="hours_binding is abs(pi)>1e-6 as requested; dual-active proxy, not primal slack verification. AC uses shared bidirectional row; no identifiable separate direction counts. DC has no reverse row.",
            voltage_note="voltage_class absent in archived transmission_capacity.csv; left empty, not inferred.",
            annual_capacity_units="intra_load_center_annual_capacity constrains annual GWh flows by design_hours*capacity_GW; raw pi unit million CNY/GWh." ))
        print("ROWS_VERIFIED_T3_T4_COMPLETE", dict(self.selected_counts), flush=True)


def capacity_output(out, names, obj, rc, nnz, split_name, families):
    rows = []
    for column, name in names.items():
        family, index = split_name(name)
        if family in families:
            rows.append(dict(column_index=column, column_name=name, family=family, index=index,
                             obj=float(obj[column]), rc=float(rc[column]), nnz=int(nnz[column])))
    csv_out(Path(out) / "capacity_column_reduced_costs.csv", rows)
