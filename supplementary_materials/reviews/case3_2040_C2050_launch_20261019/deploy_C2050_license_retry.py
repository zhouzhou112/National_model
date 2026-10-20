"""Resume the authorized 40-thread deployment with the author's replacement WLS.

Uses the same prepare/preflight/submit/release/status CLI as the first retry.
Only nonsecret license path/SHA metadata is included in the new release.
"""
import json
import deploy_C2050_threads40 as deployment

prior = deployment.EVIDENCE
metadata = json.loads((prior / "license_transfer.json").read_text())
assert metadata["status"] == "TRANSFER_VERIFIED"
assert metadata["directory_mode"] == "0o700" and metadata["file_mode"] == "0o600"
assert json.loads((prior / "license_cloud_smoke.json").read_text())["status"] == "PASS"
deployment.NAME = "20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2"
deployment.ROOT = deployment.BASE + "/" + deployment.NAME
deployment.EVIDENCE = deployment.HERE / "deployment_C2050_t40_wls_v2"
deployment.BATCH_FILE = "C2050_threads40_wls.sbatch"
deployment.EXTRA_LAUNCH = dict(
    previous_failed_job="5206992",
    previous_failed_release=deployment.BASE + "/20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1",
    authorization="Author 2026-10-20: 40-thread C2050; use replacement WLS provided in D:/gurobi1",
    license_path=metadata["license_path"],
    license_sha256=metadata["sha256"],
)

if __name__ == "__main__":
    deployment.main()
