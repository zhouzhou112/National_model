"""Final one-shot verification and navigation publication, without touching originals."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE=Path('/home/zz2/National_model_server')
LIB=BASE/'case_library_v2_20261123'
TOOLS=BASE/'case_library_tools_20261123'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    catalog=json.loads((LIB/'catalog.json').read_text())['cases'];count=0;links=0
    lines=['# T550 全量案例导航','', '按情景、年份和 release 查找。每案 core 是统一小文件，full_backup 是原完整备份导航，analysis_links 是已有分析导航。所有原件保持原位。', '', '| 情景 | 年份 | 类型 | 验收 | 有序入口 |', '|---|---:|---|---|---|']
    for c in catalog:
        p=LIB/c['relative_directory'];manifest=json.loads((p/'core_manifest.json').read_text())
        for name,info in manifest['files'].items():
            assert sha(p/name)==info['sha256'];count+=1
        assert (p/'full_backup').is_symlink() and (p/'full_backup').resolve()==Path(c['source_backup'])
        assert sha(Path(c['source_backup'])/'backup_manifest.json')==manifest['source_backup_manifest_sha256'];links+=1
        for f in (p/'analysis_links').iterdir():
            assert f.is_symlink() and f.resolve().is_dir();links+=1
        lines.append(f'| {c["case"]} | {c["year"]} | {c["kind"]} | {c["acceptance"]} | [{c["release"]}]({c["relative_directory"]}/README.md) |')
    (LIB/'INDEX_ZH.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    synced={name:sha(TOOLS/name) for name in ('REPORT_ZH.md','local_library_verification.json','navigation_verification.json')}
    report=dict(status='PASS',as_of_utc=datetime.now(timezone.utc).isoformat(),cases=len(catalog),
        files_sha_verified=count,navigation_links_verified=links,reports_sha256=synced,
        organized_directory=str(LIB),source_backup_manifests_unchanged=True)
    (TOOLS/'remote_closeout_verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
