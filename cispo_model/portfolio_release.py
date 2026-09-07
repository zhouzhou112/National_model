"""Immutable case identity for V5 portfolios; never reuse the frozen Base LP."""
from __future__ import annotations
import gzip
import hashlib
import json
import re
from pathlib import Path


def require_qualified_portfolio_stage_a(config=None, *, author_authorized=False) -> None:
    """Default blocked; author-approved 2030 thermal 1e-4 launch is QC-pending.

    The 2026-09-07 authorization permits execution, never scientific acceptance.
    Other scenarios, years and numerical settings retain the previous block.
    """
    if author_authorized and config is not None:
        raw = config.raw
        expected = dict(method=2, crossover=0, solution_target=1, threads=44,
                        barrier_convergence_tolerance=1e-4, feasibility_tolerance=1e-6,
                        optimality_tolerance=1e-6, aggregate=1, scale_flag=2, numeric_focus=1)
        if (config.planning_year == 2030
                and raw['scenario']['id'] == 'case1_thermal_v5'
                and raw.get('solver_profile', {}).get('id') == 'barrier_stagea_portfolio_v1_threads44'
                and raw['flexible_load'].get('portfolio_contract') == 'optional_service_pools_v1'
                and raw['formulation'].get('annual_capacity_link_row_scaling') == 'binary_power2_safe_8192_v1'
                and all(raw['numerics'].get(key) == value for key, value in expected.items())):
            return
        raise ValueError('AUTHOR_THERMAL_SCOPE_MISMATCH: authorization is only 2030 case1, Threads44, BarConvTol1e-4')
    raise ValueError(
        'PORTFOLIO_STAGE_A_NOT_QUALIFIED: full-system nonbasic water residuals '
        'have not passed original-unit QC; optimization launch is blocked. '
        'Use preflight/build-only or offline recovery without optimization.'
    )


def validate_cloud_budget(time_limit: str, *, authorized_seconds: int = 14400) -> int:
    """Default tests <=4h; explicit zero budget denotes author-approved unlimited run."""
    if authorized_seconds == 0:
        if time_limit.strip().upper() == 'UNLIMITED':
            return 0
        raise ValueError('Author requested an unlimited formal run; finite Slurm wall limit is forbidden')
    match = re.fullmatch(r'(?:(\d+)-)?(\d+):(\d{2}):(\d{2})', time_limit.strip())
    if not match:
        raise ValueError('Portfolio cloud tests require a finite Slurm wall limit <=04:00:00')
    days, hours, minutes, seconds = (int(value or 0) for value in match.groups())
    total = ((days*24+hours)*60+minutes)*60+seconds
    if minutes >= 60 or seconds >= 60 or not 0 < total <= int(authorized_seconds):
        raise ValueError('Portfolio cloud test wall limit exceeds the authorized 4h budget')
    return total


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(8*1024*1024):
            digest.update(chunk)
    return digest.hexdigest()


def archive_portfolio_lp_identity(model, config, output_dir) -> dict:
    """Freeze each newly built original LP and source/input provenance.

    This establishes identity, not scientific acceptance or an independent
    prequalified full-year fingerprint. Resume still requires exact-LP checks.
    """
    root = Path(output_dir)
    archive = root/'model_archive'
    source = archive/'original.mps.gz'
    if not source.is_file():
        source = archive/'original.mps'
    opener = gzip.open if source.suffix == '.gz' else open
    digest = hashlib.sha256()
    with opener(source, 'rb') as stream:
        while chunk := stream.read(8*1024*1024):
            digest.update(chunk)
    model.update()
    payload = dict(schema_version='cispo_portfolio_lp_identity_v1',
        status='ORIGINAL_MODEL_ARCHIVED_NOT_PREQUALIFIED',
        scientific_acceptance=False, scenario_id=config.raw['scenario']['id'],
        planning_year=config.planning_year,
        constraints=int(model.NumConstrs), variables=int(model.NumVars), nonzeros=int(model.NumNZs),
        gurobi_fingerprint_unsigned_hex=f'0x{int(model.Fingerprint)&0xffffffff:08x}',
        uncompressed_mps_sha256=digest.hexdigest(),
        config_files={str(p):file_sha256(Path(p)) for p in (
            config.path,config.scenario_path,config.solver_path,config.formulation_path) if p},
        interpretation='A distinct portfolio LP; the reviewed Base fingerprint is inapplicable. Original-unit QC and solver acceptance are mandatory after optimization.')
    target = root/'portfolio_lp_identity.json'
    if target.exists():
        raise FileExistsError(f'Refusing to overwrite portfolio LP identity: {target}')
    target.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return payload
