"""データソースの取得。すべて2026-09に到達確認済みのURL。

使い方:
    python -m src.download            # 未取得のファイルのみダウンロード
    python -m src.download --force    # 全て再取得
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config

# name -> (URL, 保存ファイル名)
SOURCES: dict[str, tuple[str, str]] = {
    # CoRE MOF 2024 (Zenodo 15055758): SI構造のプロパティ表（水安定性・KHクラス込み）
    "coremof2024_asr": (
        "https://zenodo.org/api/records/15055758/files/ASR_data_SI_20250204.csv/content",
        "coremof2024_asr.csv",
    ),
    "coremof2024_screening_list": (
        "https://zenodo.org/api/records/15055758/files/12089-recommended-screening-list.csv/content",
        "coremof2024_screening_list.csv",
    ),
    # 構造ごとの水吸着等温線 (.aif)
    "coremof2024_water": (
        "https://zenodo.org/api/records/15055758/files/water.zip/content",
        "coremof2024_water.zip",
    ),
    # CoRE MOF 2025 (Zenodo 15621349): 推奨スクリーニングリスト
    "coremof2025_screening8806": (
        "https://zenodo.org/api/records/15621349/files/8806-recommended-screening-list.txt/content",
        "coremof2025_screening8806.txt",
    ),
    # MOSAEC-DB (Zenodo 15808197): 全124k構造のマスタープロパティ表
    "mosaec_db": (
        "https://zenodo.org/api/records/15808197/files/mosaec-db.csv/content",
        "mosaec_db.csv",
    ),
    # BW-DB / Boyd 2019 (Materials Cloud): GCMC結果 324,426構造
    "bwdb_screening": (
        "https://archive.materialscloud.org/api/records/nsp7v-2dk91/files/screening_data.tar.gz/content",
        "bwdb_screening_data.tar.gz",
    ),
    # Keskin 2018 (Europe PMC): CoRE実験構造のCO2/N2・CO2/CH4選択性
    "keskin2018": (
        "https://europepmc.org/api/fulltextRepo?pprId=PMC5968432&type=FILE"
        "&fileName=am8b04600_si_002.xlsx"
        "&mimeType=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "keskin2018_co2n2_selectivity.xlsx",
    ),
    # WS24 (Zenodo 12110918): 水安定性の実験ラベル
    "ws24_datasets": (
        "https://zenodo.org/api/records/12110918/files/data_sets.zip/content",
        "ws24_data_sets.zip",
    ),
}


def fetch(name: str, force: bool = False) -> Path:
    url, filename = SOURCES[name]
    dest = config.DATA_RAW / filename
    if dest.exists() and not force:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    print(f"downloading {name} -> {dest}")
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    return dest


def fetch_all(force: bool = False) -> None:
    for name in SOURCES:
        fetch(name, force=force)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    fetch_all(force=args.force)
