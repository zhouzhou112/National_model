"""Base2030 ROWS extraction only; its existing T2 is reused after SHA checks."""
import argparse
from pathlib import Path
import numpy as np
from dual_extensions import verify_inputs, RowsObserver
import gzip

p = argparse.ArgumentParser()
p.add_argument("--root", required=True)
p.add_argument("--out", required=True)
a = p.parse_args()
identity = verify_inputs(a.root, a.out)
root = Path(a.root) / "output_8760"
pi = np.load(root / "barrier_checkpoint/dual_barpi.npy", mmap_mode="r")
observer = RowsObserver(a.root, a.out, pi, identity)
rows = False
with gzip.open(root / "model_archive/original.mps.gz", "rt", encoding="ascii") as stream:
    for line in stream:
        if line.startswith("ROWS"):
            rows = True
        elif line.startswith("COLUMNS"):
            observer.finish()
            break
        elif rows:
            parts = line.split()
            if parts and parts[0] != "N":
                observer.consume(parts[0], parts[1])
    else:
        raise RuntimeError("MPS COLUMNS boundary not found")
