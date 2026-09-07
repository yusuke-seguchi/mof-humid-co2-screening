"""Stage 0: スクリーニング母集団の構築。

MOSAEC-DB（金属・幾何・官能基）を土台に、CoRE MOF 2024 SI（ML水安定性・KHクラス）
と WS24（実験ラベル）を refcode で突合し、金属Tier付与とゲートを適用する。

出力:
    data/processed/pool.parquet    — Stage 0 通過構造（Track 1: 物理吸着）
    data/processed/track2.parquet  — 化学吸着候補（アミン官能基持ち; 別枠評価）
    data/processed/pool_stats.json — 集計サマリ
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src import loaders


def assign_tier(metals: frozenset[str]) -> str | None:
    """金属集合から水安定性Tierを返す。高価数でなければ None。"""
    if not metals:
        return None
    if metals & config.EXCLUDED_METALS:
        return None
    if metals <= config.TIER_A_METALS:
        return "A"
    if metals <= config.TIER_B_METALS:
        return "B"
    if metals <= config.TIER_C_METALS:
        return "C"
    return None


def water_stability_evidence(row: pd.Series) -> tuple[str, bool]:
    """水安定性の根拠と合否を返す。

    優先順位: WS24実験ラベル > CoRE ML確率 > 金属Tierヒューリスティクス。
    Tier C はラベル裏付けが無い場合に不合格（保守的運用）。
    """
    label = row.get("ws24_burtch_label")
    if pd.notna(label):
        return "ws24_experimental", label >= config.WS24_STABLE_MIN_LABEL
    prob = row.get("water_stability_prob")
    if pd.notna(prob):
        return "coremof_ml", prob >= config.WATER_STABILITY_PROB_MIN
    if row["tier"] in ("A", "B"):
        return "metal_heuristic", True
    return "none", False


def build_pool(save: bool = True) -> dict:
    mosaec = loaders.load_mosaec()
    core = loaders.load_coremof2024_asr()
    try:
        csd_mod = loaders.load_coremof2024_csd_modified()
        core = pd.concat([core, csd_mod], ignore_index=True)
    except FileNotFoundError:
        pass  # CCDC登録前はSI分のみで構築
    ws24 = loaders.load_ws24()

    # --- 土台: MOSAEC のユニーク構造 + CoRE SI にしかない構造を追加 ---
    base = mosaec[mosaec["is_unique"]].copy()
    core_extra = core[~core["refcode"].isin(set(base["refcode"].dropna()))].copy()
    # refcode が判明している行のみ重複排除（refcode欠損の新規構造は全て残す）
    has_ref = core_extra["refcode"].notna()
    core_extra = pd.concat(
        [core_extra[has_ref].drop_duplicates("refcode"), core_extra[~has_ref]],
        ignore_index=True,
    )
    core_extra["is_unique"] = True
    pool = pd.concat([base, core_extra], ignore_index=True)

    # --- CoRE SI の安定性情報を refcode で付与（MOSAEC行に対して） ---
    core_props = (
        core.dropna(subset=["refcode"])
        .groupby("refcode", as_index=False)
        .agg(
            water_stability_prob=("water_stability_prob", "mean"),
            thermal_stability_C=("thermal_stability_C", "mean"),
            kh_class=("kh_class", "first"),
        )
    )
    pool = pool.merge(
        core_props, on="refcode", how="left", suffixes=("", "_core")
    )
    # CoRE由来の行は自分の値を優先
    for col in ("water_stability_prob", "thermal_stability_C", "kh_class"):
        col_core = f"{col}_core"
        if col_core in pool.columns:
            pool[col] = pool[col].combine_first(pool[col_core])
            pool = pool.drop(columns=[col_core])

    pool = pool.merge(ws24, on="refcode", how="left")

    # --- Tier とゲート ---
    pool["tier"] = pool["metals"].map(assign_tier)
    evidence = pool.apply(water_stability_evidence, axis=1)
    pool["water_evidence"] = [e for e, _ in evidence]
    pool["water_pass"] = [p for _, p in evidence]

    gates = {
        "gate_metal": pool["tier"].notna(),
        "gate_pld": pool["pld"] > config.PLD_MIN_ANG,
        "gate_water": pool["water_pass"],
    }
    for name, mask in gates.items():
        pool[name] = mask
    pool["stage0_pass"] = pd.concat(gates.values(), axis=1).all(axis=1)

    # --- Track 分離 ---
    passed = pool[pool["stage0_pass"]].copy()
    track2 = passed[passed["has_chemisorption_fg"] == True].copy()  # noqa: E712
    track1 = passed[passed["has_chemisorption_fg"] != True].copy()  # noqa: E712

    stats = {
        "input_structures": int(len(pool)),
        "gate_metal_pass": int(gates["gate_metal"].sum()),
        "gate_metal_and_pld_pass": int((gates["gate_metal"] & gates["gate_pld"]).sum()),
        "stage0_pass": int(len(passed)),
        "track1_physisorption": int(len(track1)),
        "track2_chemisorption": int(len(track2)),
        "tier_counts": track1["tier"].value_counts().to_dict(),
        "water_evidence_counts": track1["water_evidence"].value_counts().to_dict(),
        "oms_fraction_track1": float(track1["has_oms"].mean()) if len(track1) else None,
        "with_kh_class": int(track1["kh_class"].notna().sum()),
    }

    if save:
        config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        # frozenset は parquet 非対応なのでソート済み文字列に変換して保存
        for frame, name in ((track1, "pool"), (track2, "track2")):
            out = frame.copy()
            out["metals"] = out["metals"].map(lambda s: ",".join(sorted(s)))
            out.to_parquet(config.DATA_PROCESSED / f"{name}.parquet", index=False)
        with open(config.DATA_PROCESSED / "pool_stats.json", "w") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

    return stats


if __name__ == "__main__":
    stats = build_pool()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
