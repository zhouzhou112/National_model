"""Tests for the explicit, author-scoped Late-entry source identity bridge."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from scripts.run_cispo_2030_full_year import validate_late_entry_base_state

class LateEntryBridgeTests(unittest.TestCase):
    def test_valid_capsule_and_fail_closed_mutations(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent=Path(tmp);root=parent/'planning_state_candidate';root.mkdir()
            hashes={}
            for name in ('solve_report.json','solution_qc.json','run_identity.json'):
                raw=json.dumps({'source':'base','file':name}).encode();(parent/name).write_bytes(raw);hashes[name]=hashlib.sha256(raw).hexdigest()
            accept=dict(author_decision='ACCEPTED_RELATIVE_V1_20261012',planning_year=2040,scenario_id='base',source_evidence=dict(source_sha256=hashes))
            raw=json.dumps(accept).encode();(parent/'acceptance_relative_v1.json').write_bytes(raw)
            meta=dict(acceptance_relative_v1_sha256=hashlib.sha256(raw).hexdigest(),source_capacity_state_policy='AUTHOR_R1_CLEANED_BOUND_CLOSED_DERIVATIVE',continuation_cleanup=dict(status='PASS',applied=True,source_year=2040,planning_year=2050))
            (root/'state_metadata.json').write_text(json.dumps(meta))
            config=SimpleNamespace(planning_year=2050,boundary_year=2040,raw={'scenario':{'id':'case3_thermal_ev_v5'}})
            self.assertEqual(validate_late_entry_base_state(config,root,allow_candidate=True),'base')
            with self.assertRaises(ValueError):validate_late_entry_base_state(config,root,allow_candidate=False)
            config.planning_year=2040
            with self.assertRaises(ValueError):validate_late_entry_base_state(config,root,allow_candidate=True)
            config.planning_year=2050
            (parent/'solve_report.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'provenance'):validate_late_entry_base_state(config,root,allow_candidate=True)
            (parent/'acceptance_relative_v1.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'SHA'):validate_late_entry_base_state(config,root,allow_candidate=True)

if __name__=='__main__':unittest.main()
