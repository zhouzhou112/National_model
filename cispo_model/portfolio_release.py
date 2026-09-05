"""Immutable case identity for V5 portfolios; never reuse the frozen Base LP."""
from __future__ import annotations
import gzip
import hashlib
import json
import re
from pathlib import Path


def require_qualified_portfolio_stage_a() -> None:
    """Fail closed until the unresolved original-unit residual gate is reviewed.

    No runtime flag promotes this candidate profile to production. This guard
    must be revised with reproducible qualification evidence before launch.
    Build-only, preflight and offline recovery remain available in the runner.
    """
    raise ValueError(
        'PORTFOLIO_STAGE_A_NOT_QUALIFIED: full-system nonbasic water residuals '
        'have not passed original-unit QC; optimization launch is blocked. '
        'Use preflight/build-only or offline recovery without optimization.'
    )


def validate_cloud_budget(time_limit: str) -> int:
    """Reject missing/unlimited/>4h Slurm wall limits, including build time."""
    match = re.fullmatch(r'(?:(\d+)-)?(\d+):(\d{2}):(\d{2})', time_limit.strip())
    if not match:
        raise ValueError('Portfolio cloud tests require a finite Slurm wall limit <=04:00:00')
    days, hours, minutes, seconds = (int(value or 0) for value in match.groups())
    total = ((days*24+hours)*60+minutes)*60+seconds
    if minutes >= 60 or seconds >= 60 or not 0 < total <= 14400:
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
