"""各データソースを共通スキーマに正規化して読み込む。

共通の結合キーは CSD refcode（6文字英字＋任意の2桁数字）。同一refcodeの
活性化バリアント（_ASR, _clean 等）はサフィックスを剥がして refcode 列に揃える。
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config

_METAL_SPLIT = re.compile(r"[,;/]")
_REFCODE = re.compile(r"^([A-Za-z]{6}\d{0,2})")


def parse_metals(value: object) -> frozenset[str]:
    """'V/Ni' や 'Cu, Zn' 形式の金属リストを分解する。"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return frozenset()
    parts = (p.strip() for p in _METAL_SPLIT.split(str(value)))
    return frozenset(p for p in parts if p and p.lower() != "nan")


def extract_refcode(name: object) -> str | None:
    """'ABAVIJ_ASR_pacman' 'RUBTAK01_clean' 等から CSD refcode を取り出す。"""
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return None
    m = _REFCODE.match(str(name).strip())
    return m.group(1).upper() if m else None


# ---------------------------------------------------------------------------
# MOSAEC-DB
# ---------------------------------------------------------------------------

# 化学吸着性（Track 2 分離）の判定に使う官能基フラグ
CHEMISORPTION_GROUPS = ["primary amine", "secondary amine"]


def load_mosaec(path: Path | None = None) -> pd.DataFrame:
    path = path or config.DATA_RAW / "mosaec_db.csv"
    df = pd.read_csv(path, low_memory=False)
    out = pd.DataFrame(
        {
            "structure_id": df["cif"].astype(str),
            "refcode": df["refcode"].map(extract_refcode),
            "metals": df["metal_id"].map(parse_metals),
            "pld": pd.to_numeric(df["pld_ang_H2"], errors="coerce"),
            "lcd": pd.to_numeric(df["lcd_ang_H2"], errors="coerce"),
            "density": pd.to_numeric(df["density_g/cm3"], errors="coerce"),
            "asa_m2_g": pd.to_numeric(df["asa_m2/g_H2"], errors="coerce"),
            "void_fraction": pd.to_numeric(df["void_fraction_H2"], errors="coerce"),
            "pore_volume_cm3_g": pd.to_numeric(df["av_cm3/g_H2"], errors="coerce"),
            "is_unique": df["unique"].astype(str).str.lower().eq("true"),
            "has_oms": df["open_metal_site"].astype(str).str.lower().eq("true"),
            "solvent_removed": df["solvent_removed"].astype(str),
            "charge_label": df["charge_label"].astype(str),
            "source": "mosaec",
        }
    )
    for col in CHEMISORPTION_GROUPS:
        out[f"fg_{col.replace(' ', '_')}"] = (
            df[col].astype(str).str.lower().eq("true") if col in df else False
        )
    out["has_chemisorption_fg"] = out[
        [f"fg_{c.replace(' ', '_')}" for c in CHEMISORPTION_GROUPS]
    ].any(axis=1)
    return out


# ---------------------------------------------------------------------------
# CoRE MOF 2024（SI サブセットのプロパティ表: 水安定性・KHクラス込み）
# ---------------------------------------------------------------------------

def load_coremof2024_asr(path: Path | None = None, source: str = "coremof2024_si") -> pd.DataFrame:
    path = path or config.DATA_RAW / "coremof2024_asr.csv"
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    thermal_col = next(c for c in df.columns if c.startswith("Thermal_stability"))
    out = pd.DataFrame(
        {
            "structure_id": df["coreid"].astype(str),
            "refcode": df["refcode"].map(extract_refcode),
            "metals": df["Metal Types"].map(parse_metals),
            "pld": pd.to_numeric(df["PLD (Å)"], errors="coerce"),
            "lcd": pd.to_numeric(df["LCD (Å)"], errors="coerce"),
            "density": pd.to_numeric(df["Density (g/cm3)"], errors="coerce"),
            "asa_m2_g": pd.to_numeric(df["ASA (m2/g)"], errors="coerce"),
            "void_fraction": pd.to_numeric(df["VF"], errors="coerce"),
            "pore_volume_cm3_g": pd.to_numeric(df["PV (cm3/g)"], errors="coerce"),
            "has_oms": df["Has OMS"].astype(str).str.strip().str.lower().eq("yes"),
            "water_stability_prob": pd.to_numeric(df["Water_stability"], errors="coerce"),
            "thermal_stability_C": pd.to_numeric(df[thermal_col], errors="coerce"),
            "kh_class": df["KH_Classes"].astype(str).str.strip(),
            "source": source,
        }
    )
    return out


def load_coremof2024_csd_modified(path: Path | None = None) -> pd.DataFrame:
    """CCDC配布の CSD-modified CR メタデータ（要無料登録で取得済みの前提）。"""
    path = path or (
        config.DATA_RAW / "csd_modified" / "CSD-modified"
        / "CR_data_CSD_modified_20250227.csv"
    )
    return load_coremof2024_asr(path, source="coremof2024_csd_modified")


# ---------------------------------------------------------------------------
# BW-DB（ML教師データ）
# ---------------------------------------------------------------------------

BWDB_TARGETS = {
    "CO2_uptake_P0.15bar_T298K [mmol/g]": "co2_uptake_0p15bar_298K",
    "CO2_binary_uptake_P0.15bar_T298K [mmol/g]": "co2_binary_uptake_0p15bar_298K",
    "heat_adsorption_CO2_P0.15bar_T298K [kcal/mol]": "qst_co2_kcal_mol",
    "CO2/N2_selectivity": "co2_n2_selectivity",
    "working_capacity_vacuum_swing [mmol/g]": "wc_vsa_mmol_g",
    "working_capacity_temperature_swing [mmol/g]": "wc_tsa_mmol_g",
}

BWDB_FEATURES = {
    "surface_area [m^2/g]": "asa_m2_g",
    "void_fraction": "void_fraction",
    "void_volume [cm^3/g]": "pore_volume_cm3_g",
    "largest_free_sphere_diameter [A]": "pld",
    "largest_included_sphere_diameter [A]": "lcd",
    "volume [A^3]": "cell_volume_A3",
    "weight [u]": "cell_weight_u",
}


def load_bwdb(path: Path | None = None) -> pd.DataFrame:
    path = path or config.DATA_RAW / "bwdb_all_MOFs_screening_data.csv"
    usecols = ["MOFname", "functional_groups", "metal_linker", "organic_linker1",
               "organic_linker2", "topology", *BWDB_TARGETS, *BWDB_FEATURES]
    df = pd.read_csv(path, usecols=usecols, low_memory=False)
    df = df.rename(columns={**BWDB_TARGETS, **BWDB_FEATURES})
    # 密度 [g/cm3] = (質量[u] * 1.66054e-24 g) / (体積[Å^3] * 1e-24 cm3)
    df["density"] = 1.66054 * df["cell_weight_u"] / df["cell_volume_A3"]
    return df


# ---------------------------------------------------------------------------
# Keskin 2018（実験構造の選択性: 校正用）
# ---------------------------------------------------------------------------

def load_keskin(path: Path | None = None) -> pd.DataFrame:
    path = path or config.DATA_RAW / "keskin2018_co2n2_selectivity.xlsx"
    df = pd.ExcelFile(path).parse("Binary", skiprows=1)
    df.columns = ["refcode", "s_co2n2_1bar", "s_co2ch4_1bar"]
    df = df.dropna(subset=["refcode"])
    df["refcode"] = df["refcode"].map(extract_refcode)
    df["s_co2n2_1bar"] = pd.to_numeric(df["s_co2n2_1bar"], errors="coerce")
    df["s_co2ch4_1bar"] = pd.to_numeric(df["s_co2ch4_1bar"], errors="coerce")
    return df.dropna(subset=["refcode"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# WS24（水安定性の実験ラベル）
# ---------------------------------------------------------------------------

def load_ws24(raw_dir: Path | None = None) -> pd.DataFrame:
    """WS24s labels.csv を読む。zip 展開済みディレクトリ or zip 本体のどちらでも可。"""
    raw_dir = raw_dir or config.DATA_RAW
    labels_path = raw_dir / "ws24" / "data_sets" / "WS24s" / "labels.csv"
    if not labels_path.exists():
        zip_path = raw_dir / "ws24_data_sets.zip"
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(raw_dir / "ws24")
    df = pd.read_csv(labels_path, encoding="utf-8-sig")
    burtch_col = next(c for c in df.columns if c.startswith("Burtch label"))
    out = pd.DataFrame(
        {
            "refcode": df["refcode"].map(extract_refcode),
            "ws24_burtch_label": pd.to_numeric(df[burtch_col], errors="coerce"),
        }
    )
    out = out.dropna(subset=["refcode", "ws24_burtch_label"])
    # 同一refcodeに複数報告がある場合は保守側（最小=最も不安定な報告）を採る
    return (
        out.groupby("refcode", as_index=False)["ws24_burtch_label"].min()
    )
