"""スクリーニング全体の設定値。閾値には出典を付す（docs/metrics_survey_mof_screening.md 参照）。"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# ---------------------------------------------------------------------------
# 金属Tier（水安定性の化学ヒューリスティクス）
# Tier A: 高価数の代表格。カルボキシレート系で加水分解耐性の実験実績が最も厚い
# Tier B: +Fe/Sc/In/Ga（Fe は Fe2+/Fe3+ を元素記号で区別できない点に注意）
# Tier C: +Y/V/ランタノイド（3+だがイオン半径が大きく電荷密度が低い → 要ラベル裏付け）
# ---------------------------------------------------------------------------
TIER_A_METALS = frozenset({"Zr", "Hf", "Ti", "Al", "Cr"})
TIER_B_METALS = TIER_A_METALS | frozenset({"Fe", "Sc", "In", "Ga"})
LANTHANIDES = frozenset(
    {"La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"}
)
TIER_C_METALS = TIER_B_METALS | LANTHANIDES | frozenset({"Y", "V"})

# 毒性・規制面で除外する金属（Danaci 2020: 実用性ゲート）
EXCLUDED_METALS = frozenset({"Cd", "Pb", "Hg", "As", "U", "Th", "Tl", "Be"})

# ---------------------------------------------------------------------------
# Stage 0 ゲート
# ---------------------------------------------------------------------------
PLD_MIN_ANG = 3.3  # CO2 動的直径 3.3 Å（Kancharlapalli & Snurr 2023 ほか）
WATER_STABILITY_PROB_MIN = 0.5  # CoRE MOF DB のML水安定性確率。緩め（recall重視, ES&T 2025）
WS24_STABLE_MIN_LABEL = 3  # Burtch段階: 3=high kinetic, 4=thermodynamic を「安定」扱い

# ---------------------------------------------------------------------------
# Stage 1（ML/Widom）: ソフト適用の窓。ゲートではなくフラグ
# ---------------------------------------------------------------------------
QST_SOFT_WINDOW_KJMOL = (30.0, 55.0)  # CCST 2026: 硬い閾値は非線形域の勝者を落とす

# ---------------------------------------------------------------------------
# Stage 2（GCMC）条件
# ---------------------------------------------------------------------------
FLUE_GAS = {
    "T_K": 313.0,
    "P_total_bar": 1.0,
    "y_CO2": 0.15,
    "y_N2": 0.85,
}
DESORPTION_VSA = {"T_K": 313.0, "P_total_bar": 0.1}
REGENERABILITY_MIN = 0.70  # Bae & Snurr 2011（補助診断）
HUMID_RETENTION_MIN = 0.80  # Kwon 2025 は0.9。境界例を残すため緩め
HUMID_CO2_H2O_RATIO_MIN = 1.0  # Kwon 2025

# BW-DB 教師ラベルの条件（Boyd 2019 と一致させる）
BWDB_TRAIN_CONDITION = {"T_K": 298.0, "p_CO2_bar": 0.15}
