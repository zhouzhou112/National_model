from pathlib import Path
import hashlib,json,subprocess,sys,tempfile,unittest
import numpy as np

MPS='''NAME tiny
ROWS
 N OBJ
 E vre_capacity_accounting[0]
 G spur_capacity_non_dpv[0]
COLUMNS
 vre_capacity_gw[0] OBJ 2 vre_capacity_accounting[0] 1
 vre_capacity_gw[0] spur_capacity_non_dpv[0] -0.5
 vre_new_gw[0] OBJ 3 vre_capacity_accounting[0] -1
 spur_augmentation_gw[0] OBJ 4 spur_capacity_non_dpv[0] 1
RHS
 rhs vre_capacity_accounting[0] 1 spur_capacity_non_dpv[0] -0.4
BOUNDS
 LO bounds vre_capacity_gw[0] 1
 UP bounds vre_capacity_gw[0] 3
 UP bounds vre_new_gw[0] 2
ENDATA
'''

class DirectionalCLITest(unittest.TestCase):
    def fixture(self,parent):
        root=parent/'source';root.mkdir();(root/'model_archive').mkdir();(root/'barrier_checkpoint').mkdir()
        m=root/'model_archive/original.mps';m.write_text(MPS);pi=root/'barrier_checkpoint/dual_barpi.npy';np.save(pi,[17.,20.]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        (root/'model_archive/archive_manifest.json').write_text(json.dumps(dict(gurobi_fingerprint=42,files=[dict(path=m.name,sha256=sha(m))])))
        (root/'barrier_checkpoint/barrier_checkpoint_manifest.json').write_text(json.dumps(dict(gurobi_fingerprint=42,source=dict(optimization_hours=24),vectors=dict(dual=dict(path=pi.name,sha256=sha(pi))))))
        (root/'vre_capacity.csv').write_text('grid_uid,technology,province_code,capacity_floor_gw,capacity_upper_gw,new_capacity_gw\nG1,onwind,13,1,3,0\n')
        (root/'model_config_snapshot.json').write_text(json.dumps(dict(resolved_configuration=dict(planning_year=2050,numerics=dict(capacity_headroom_zero_gw=1e-5)))))
        (root/'solve_report.json').write_text(json.dumps(dict(status='OPTIMAL',objective_value_million_cny=1000)))
        (root/'result_manifest.json').write_text(json.dumps(dict(files=[dict(path=p.name,sha256=sha(p)) for p in root.iterdir() if p.is_file()])))
        selection=parent/'selection.json';selection.write_text(json.dumps(dict(schema_version='capacity_bound_selection_v1',planning_year=2050,mode='vre_boundary_states',source_references={},columns=[dict(grid_uid='G1',technology='onwind',state='lower')])))
        return root,selection

    def run_cli(self,root,selection,out,cache=None):
        script=Path(__file__).resolve().parents[1]/'scripts/price_capacity_bound_selection.py'
        cmd=[sys.executable,str(script),'--run-dir',str(root),'--selection-json',str(selection),'--output',str(out),'--reference-only']
        if cache:cmd+=['--parse-cache',str(cache)]
        return subprocess.run(cmd,capture_output=True,text=True)

    def test_cached_and_uncached_scientific_outputs_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);root,s=self.fixture(p);before={x:x.read_bytes() for x in root.rglob('*') if x.is_file()}
            a=self.run_cli(root,s,p/'first');self.assertEqual(a.returncode,0,a.stderr)
            b=self.run_cli(root,s,p/'cached',p/'first');self.assertEqual(b.returncode,0,b.stderr)
            for n in ['boundary_directional_prices.csv','proposed_selection.json','directional_pricing_report.json']:
                self.assertEqual((p/'first'/n).read_bytes(),(p/'cached'/n).read_bytes())
            self.assertEqual(before,{x:x.read_bytes() for x in before})

    def test_wrong_cache_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);root,s=self.fixture(p);a=self.run_cli(root,s,p/'first');self.assertEqual(a.returncode,0,a.stderr)
            f=p/'first/parse_cache_manifest.json';r=json.loads(f.read_text());r['barpi_sha256']='wrong';f.write_text(json.dumps(r))
            b=self.run_cli(root,s,p/'wrong',p/'first');self.assertNotEqual(b.returncode,0);self.assertIn('identity mismatch',b.stderr)

if __name__=='__main__':unittest.main()
