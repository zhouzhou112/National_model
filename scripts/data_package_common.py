"""Shared mappings and helpers for the CISPO model input package."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


PROVINCES = [
    (11, "Beijing", "北京"),
    (12, "Tianjin", "天津"),
    (13, "Hebei", "河北"),
    (14, "Shanxi", "山西"),
    (15, "Inner Mongolia", "内蒙古"),
    (21, "Liaoning", "辽宁"),
    (22, "Jilin", "吉林"),
    (23, "Heilongjiang", "黑龙江"),
    (31, "Shanghai", "上海"),
    (32, "Jiangsu", "江苏"),
    (33, "Zhejiang", "浙江"),
    (34, "Anhui", "安徽"),
    (35, "Fujian", "福建"),
    (36, "Jiangxi", "江西"),
    (37, "Shandong", "山东"),
    (41, "Henan", "河南"),
    (42, "Hubei", "湖北"),
    (43, "Hunan", "湖南"),
    (44, "Guangdong", "广东"),
    (45, "Guangxi", "广西"),
    (46, "Hainan", "海南"),
    (50, "Chongqing", "重庆"),
    (51, "Sichuan", "四川"),
    (52, "Guizhou", "贵州"),
    (53, "Yunnan", "云南"),
    (54, "Tibet", "西藏"),
    (61, "Shaanxi", "陕西"),
    (62, "Gansu", "甘肃"),
    (63, "Qinghai", "青海"),
    (64, "Ningxia", "宁夏"),
    (65, "Xinjiang", "新疆"),
]

PROVINCE_DF = pd.DataFrame(
    PROVINCES, columns=["province_code", "province_name_en", "province_name_zh"]
)
CODE_TO_EN = dict(zip(PROVINCE_DF.province_code, PROVINCE_DF.province_name_en))
CODE_TO_ZH = dict(zip(PROVINCE_DF.province_code, PROVINCE_DF.province_name_zh))
EN_TO_CODE = dict(zip(PROVINCE_DF.province_name_en, PROVINCE_DF.province_code))
ZH_TO_CODE = dict(zip(PROVINCE_DF.province_name_zh, PROVINCE_DF.province_code))


def normalize_zh_province(value: object) -> str:
    """Normalize common Chinese province suffixes to the package labels."""
    text = str(value).strip()
    replacements = {
        "内蒙古自治区": "内蒙古",
        "广西壮族自治区": "广西",
        "西藏自治区": "西藏",
        "宁夏回族自治区": "宁夏",
        "新疆维吾尔自治区": "新疆",
    }
    if text in replacements:
        return replacements[text]
    for suffix in ("省", "市"):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
    return text


def add_province_fields(
    frame: pd.DataFrame,
    *,
    source_col: str,
    source_kind: str,
) -> pd.DataFrame:
    """Add standardized 31-province code and names to a table."""
    out = frame.copy()
    if source_kind == "code":
        code = pd.to_numeric(out[source_col], errors="coerce").astype("Int64")
    elif source_kind == "en":
        code = out[source_col].astype(str).str.strip().map(EN_TO_CODE).astype("Int64")
    elif source_kind == "zh":
        code = out[source_col].map(normalize_zh_province).map(ZH_TO_CODE).astype("Int64")
    else:
        raise ValueError(f"Unsupported source_kind={source_kind}")
    if code.isna().any():
        missing = sorted(out.loc[code.isna(), source_col].astype(str).unique())
        raise ValueError(f"Unmapped province values in {source_col}: {missing}")
    out["province_code"] = code.astype(int)
    out["province_name_en"] = out.province_code.map(CODE_TO_EN)
    out["province_name_zh"] = out.province_code.map(CODE_TO_ZH)
    return out


def sha256_file(path: Path, chunk_bytes: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(chunk_bytes):
            digest.update(block)
    return digest.hexdigest()


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig", lineterminator="\n")


def write_output_manifest(data_root: Path) -> None:
    """Refresh hashes for every generated data file except the manifest itself."""
    outputs = []
    for path in sorted(data_root.rglob("*")):
        if path.is_file() and path.name != "output_manifest.csv":
            outputs.append(
                {
                    "relative_path": path.relative_to(data_root).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    write_csv(pd.DataFrame(outputs), data_root / "output_manifest.csv")
