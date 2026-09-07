import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src import loaders
from src.pool import assign_tier, water_stability_evidence


# ---------------------------------------------------------------------------
# 金属パース
# ---------------------------------------------------------------------------

def test_parse_metals_handles_slash_and_comma():
    assert loaders.parse_metals("V/Ni") == {"V", "Ni"}
    assert loaders.parse_metals("Cu, Zn") == {"Cu", "Zn"}
    assert loaders.parse_metals("Zr") == {"Zr"}
    assert loaders.parse_metals(None) == frozenset()
    assert loaders.parse_metals(float("nan")) == frozenset()


def test_extract_refcode():
    assert loaders.extract_refcode("ABAVIJ_ASR_pacman") == "ABAVIJ"
    assert loaders.extract_refcode("RUBTAK01_clean") == "RUBTAK01"
    assert loaders.extract_refcode("IHEYOM_full") == "IHEYOM"
    assert loaders.extract_refcode(None) is None


# ---------------------------------------------------------------------------
# Tier 判定
# ---------------------------------------------------------------------------

def test_tier_a_is_strict_high_valence():
    assert assign_tier(frozenset({"Zr"})) == "A"
    assert assign_tier(frozenset({"Al", "Cr"})) == "A"


def test_tier_b_allows_fe():
    assert assign_tier(frozenset({"Fe"})) == "B"
    assert assign_tier(frozenset({"Zr", "Fe"})) == "B"


def test_tier_c_lanthanides():
    assert assign_tier(frozenset({"Eu"})) == "C"


def test_low_valence_and_toxic_metals_rejected():
    assert assign_tier(frozenset({"Zn"})) is None
    assert assign_tier(frozenset({"Zr", "Cu"})) is None  # 混合でも低価数が入れば除外
    assert assign_tier(frozenset({"Zr", "Cd"})) is None  # 毒性金属
    assert assign_tier(frozenset()) is None


# ---------------------------------------------------------------------------
# 水安定性の根拠の優先順位
# ---------------------------------------------------------------------------

def _row(**kw):
    base = {"ws24_burtch_label": float("nan"), "water_stability_prob": float("nan"), "tier": "C"}
    base.update(kw)
    return pd.Series(base)


def test_ws24_label_takes_priority():
    ev, ok = water_stability_evidence(_row(ws24_burtch_label=4, water_stability_prob=0.1))
    assert ev == "ws24_experimental" and ok


def test_ws24_unstable_label_fails_even_tier_a():
    ev, ok = water_stability_evidence(_row(ws24_burtch_label=1, tier="A"))
    assert ev == "ws24_experimental" and not ok


def test_coreml_prob_used_when_no_label():
    ev, ok = water_stability_evidence(_row(water_stability_prob=0.7))
    assert ev == "coremof_ml" and ok
    ev, ok = water_stability_evidence(_row(water_stability_prob=0.3))
    assert ev == "coremof_ml" and not ok


def test_tier_c_without_evidence_fails():
    ev, ok = water_stability_evidence(_row(tier="C"))
    assert ev == "none" and not ok


def test_tier_a_heuristic_passes_without_labels():
    ev, ok = water_stability_evidence(_row(tier="A"))
    assert ev == "metal_heuristic" and ok


# ---------------------------------------------------------------------------
# 実データの統合テスト（data/raw が無い環境ではスキップ）
# ---------------------------------------------------------------------------

needs_data = pytest.mark.skipif(
    not (config.DATA_RAW / "mosaec_db.csv").exists(), reason="raw data not downloaded"
)


@needs_data
def test_load_mosaec_schema():
    df = loaders.load_mosaec()
    assert len(df) > 100_000
    assert df["refcode"].notna().mean() > 0.99
    assert df["has_chemisorption_fg"].dtype == bool


@needs_data
def test_load_ws24_labels():
    df = loaders.load_ws24()
    assert 500 < len(df) < 1500
    assert set(df["ws24_burtch_label"].unique()) <= {1.0, 2.0, 3.0, 4.0}
