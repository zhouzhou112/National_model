"""Identity tests for the single author-authorized missing-table recovery."""
import csv
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from scripts.extract_frozen_hydro_spur import extract, sha256


class FrozenHydroExtractionTests(unittest.TestCase):
    def fixture(self, root, *, saved_x=False, mismatch=False):
        source = root / 'output_8760'
        archive = source / 'model_archive'
        checkpoint = source / 'barrier_checkpoint'
        archive.mkdir(parents=True)
        checkpoint.mkdir()
        names = ['vre_new_gw[0]', 'vre_new_gw[1]', 'hydro_spur_augmentation_gw[0]']
        digest = hashlib.sha256(b'cispo_raw_lp_variable_order_v1\0' + (3).to_bytes(8, 'big'))
        for i, name in enumerate(names):
            encoded = name.encode()
            digest.update(i.to_bytes(8, 'big') + len(encoded).to_bytes(8, 'big') + encoded + b'\0')
        with gzip.open(archive / 'original.mps.gz', 'wt') as f:
            f.write('NAME test\nROWS\n N OBJ\nCOLUMNS\n')
            for name in names:
                f.write(f'    {name} OBJ 1\n    {name} c1 1\n')
            f.write('RHS\n    RHS1 c1 1\nBOUNDS\nENDATA\n')
        vector = np.array([.1, .2, .3], dtype=np.float64)
        np.save(checkpoint / 'primal_barx.npy', vector)
        def record(p, relative):
            return dict(path=Path(relative).as_posix(), bytes=p.stat().st_size, sha256=sha256(p))
        ordering = dict(variables=3, gurobi_fingerprint=17, variable_order_digest=dict(sha256=digest.hexdigest()))
        cp = dict(lp_ordering=ordering, vectors={'primal':dict(record(checkpoint/'primal_barx.npy','primal_barx.npy'),attribute='BarX')})
        (checkpoint/'barrier_checkpoint_manifest.json').write_text(json.dumps(cp))
        (archive/'archive_manifest.json').write_text(json.dumps(dict(gurobi_fingerprint=17,files=[record(archive/'original.mps.gz','original.mps.gz')])))
        (source/'vre_capacity.csv').write_text('grid_uid,technology,new_capacity_gw\na,wind,0.1\nb,pv,'+('0.25' if mismatch else '0.2')+'\n')
        (source/'hydro_capacity.csv').write_text('hydrochn_row_id\n7\n')
        if saved_x:
            snap = source/'solution_snapshot'
            snap.mkdir()
            np.save(snap/'X.npy', np.array([.1,.2,.7]))
            (snap/'snapshot_manifest.json').write_text(json.dumps(dict(gurobi_fingerprint=17,variable_order_digest=ordering['variable_order_digest'],attributes={'X':record(snap/'X.npy','X.npy')})))
        files = [record(p,p.relative_to(source)) for p in source.rglob('*') if p.is_file()]
        (source/'result_manifest.json').write_text(json.dumps(dict(files=files)))
        return source

    def test_prefers_saved_x_and_validates_vre_same_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=self.fixture(root,saved_x=True)
            result=extract(source,root/'supplement')
            self.assertEqual(result['vector_attribute'],'X')
            self.assertTrue(result['vre_crosscheck']['passed'])
            with (root/'supplement/hydro_spur_capacity.csv').open() as f:
                row=next(csv.DictReader(f))
            self.assertEqual(float(row['hydro_spur_augmentation_gw']),.7)

    def test_falls_back_to_barx_when_x_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=self.fixture(root)
            result=extract(source,root/'supplement')
            self.assertEqual(result['vector_attribute'],'BarX')
            self.assertEqual(result['fallback_reason'],'X not preserved')

    def test_vre_mismatch_retains_failure_but_no_usable_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=self.fixture(root,mismatch=True)
            with self.assertRaisesRegex(ValueError,'VRE vector/table'):
                extract(source,root/'supplement')
            self.assertFalse((root/'supplement/hydro_spur_capacity.csv').exists())
            report=json.loads((root/'supplement/supplement_manifest.json').read_text())
            self.assertEqual(report['status'],'FAIL')

    def test_modified_vector_rejected_before_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=self.fixture(root)
            np.save(source/'barrier_checkpoint/primal_barx.npy',np.array([.2,.1,.3]))
            with self.assertRaisesRegex(ValueError,'identity mismatch'):
                extract(source,root/'supplement')

    def test_unmanifested_x_cannot_silently_fall_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=self.fixture(root)
            (source/'solution_snapshot').mkdir()
            np.save(source/'solution_snapshot/X.npy',np.array([.1,.2,.3]))
            with self.assertRaisesRegex(ValueError,'Unmanifested X'):
                extract(source,root/'supplement')

    def test_never_write_inside_or_reuse_source_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=self.fixture(root)
            with self.assertRaisesRegex(ValueError,'outside immutable'):
                extract(source,source/'supplement')
            (root/'supplement').mkdir()
            with self.assertRaises(FileExistsError):
                extract(source,root/'supplement')


if __name__ == '__main__':
    unittest.main()
