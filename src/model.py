"""Stage 1: BW-DB で学習した LightGBM アンサンブルによる ML 粗選別。

設計方針（docs/literature_survey_ml_mof_screening.md §3 の知見を反映）:
- 特徴量は転移に強い幾何記述子のみ。金属種 one-hot は使わない。
- リーク対策: 構成ブロック（金属ノード＋リンカー）でグループ化した GroupKFold。
  同一組成のトポロジー違い・官能基違いが train/test に跨らないようにする。
- 不確実性: fold アンサンブルの分散。高不確実性構造は選抜から落とさない。
- 選抜: 予測吸着量 × 予測選択性の Pareto シェル上位（スカラー合成しない）。

出力: data/processed/stage1_ranking.parquet, stage1_metrics.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src import loaders

FEATURES = ["pld", "lcd", "asa_m2_g", "void_fraction", "pore_volume_cm3_g", "density"]
TARGETS = {
    "co2_binary_uptake_0p15bar_298K": {"log": False},
    "co2_n2_selectivity": {"log": True},
    "qst_co2_kcal_mol": {"log": False},
}
N_FOLDS = 5
LGB_PARAMS = dict(
    objective="regression",
    n_estimators=500,
    learning_rate=0.06,
    num_leaves=63,
    min_child_samples=40,
    subsample=0.8,
    subsample_freq=1,
    colsample_bytree=0.9,
    random_state=17,
    n_jobs=-1,
    verbose=-1,
)


def prepare_training() -> tuple[pd.DataFrame, pd.Series]:
    df = loaders.load_bwdb()
    df = df.dropna(subset=FEATURES)
    groups = (
        df["metal_linker"].astype(str)
        + "|" + df["organic_linker1"].astype(str)
        + "|" + df["organic_linker2"].astype(str)
    )
    return df, groups


def train_target(df: pd.DataFrame, groups: pd.Series, target: str, log: bool):
    """GroupKFold で fold モデル群と OOF 予測を返す。"""
    mask = df[target].notna() & np.isfinite(df[target])
    if log:
        mask &= df[target] > 0
    d = df[mask]
    g = groups[mask]
    x = d[FEATURES].to_numpy()
    y = np.log10(d[target].to_numpy()) if log else d[target].to_numpy()

    oof = np.full(len(d), np.nan)
    models = []
    for tr, te in GroupKFold(n_splits=N_FOLDS).split(x, y, g):
        m = lgb.LGBMRegressor(**LGB_PARAMS)
        m.fit(x[tr], y[tr])
        oof[te] = m.predict(x[te])
        models.append(m)
    r2_grouped = r2_score(y, oof)
    return models, r2_grouped, d, y, oof


def ensemble_predict(models, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    preds = np.stack([m.predict(x) for m in models])
    return preds.mean(axis=0), preds.std(axis=0)


def pareto_shells(obj1: np.ndarray, obj2: np.ndarray) -> np.ndarray:
    """2目的（両方最大化）の非劣ソート。shell 0 が最良フロント。"""
    n = len(obj1)
    shell = np.full(n, -1)
    remaining = np.arange(n)
    level = 0
    while len(remaining):
        o1, o2 = obj1[remaining], obj2[remaining]
        is_dominated = np.zeros(len(remaining), dtype=bool)
        order = np.argsort(-o1)  # o1 降順に走査し o2 の最大値で支配判定
        best2 = -np.inf
        for idx in order:
            if o2[idx] < best2:
                is_dominated[idx] = True
            else:
                best2 = max(best2, o2[idx])
        # 同率o1で並ぶ場合の厳密支配は近似（粗選別用途では十分）
        shell[remaining[~is_dominated]] = level
        remaining = remaining[is_dominated]
        level += 1
    return shell


def main() -> None:
    df, groups = prepare_training()
    pool = pd.read_parquet(config.DATA_PROCESSED / "pool.parquet")
    pool_x = pool[FEATURES].fillna(pool[FEATURES].median()).to_numpy()

    metrics: dict = {"n_train": int(len(df)), "features": FEATURES}
    oof_frames = {}

    for target, spec in TARGETS.items():
        models, r2_grouped, d, y, oof = train_target(df, groups, target, spec["log"])
        mu, sd = ensemble_predict(models, pool_x)
        if spec["log"]:
            pool[f"pred_{target}"] = 10 ** mu
            pool[f"pred_{target}_log10_sd"] = sd
        else:
            pool[f"pred_{target}"] = mu
            pool[f"pred_{target}_sd"] = sd
        metrics[target] = {"r2_grouped_oof": round(float(r2_grouped), 4)}
        oof_frames[target] = pd.DataFrame({"y": y, "oof": oof})
        # 特徴量重要度（gain）
        imp = np.mean([m.feature_importances_ for m in models], axis=0)
        metrics[target]["feature_importance"] = {
            f: round(float(v), 1) for f, v in zip(FEATURES, imp)
        }

    # --- Qst ソフト窓フラグ（kcal/mol -> kJ/mol） ---
    qst_kj = pool["pred_qst_co2_kcal_mol"].abs() * 4.184
    lo, hi = config.QST_SOFT_WINDOW_KJMOL
    pool["qst_in_window"] = (qst_kj >= lo) & (qst_kj <= hi)

    # --- Keskin 実験構造での順位相関（ドメインシフトの定量化） ---
    keskin = loaders.load_keskin()
    cal = pool.merge(keskin, on="refcode", how="inner").dropna(
        subset=["pred_co2_n2_selectivity", "s_co2n2_1bar"]
    )
    rho = spearmanr(cal["pred_co2_n2_selectivity"], cal["s_co2n2_1bar"])
    metrics["keskin_calibration"] = {
        "n_overlap": int(len(cal)),
        "spearman_rho": round(float(rho.statistic), 3),
    }

    # --- Pareto バンド選抜 ---
    up = pool["pred_co2_binary_uptake_0p15bar_298K"].to_numpy()
    sel = np.log10(pool["pred_co2_n2_selectivity"].to_numpy())
    pool["pareto_shell"] = pareto_shells(up, sel)

    target_n = max(300, int(0.25 * len(pool)))
    shells_sorted = np.sort(pool["pareto_shell"].unique())
    keep = np.zeros(len(pool), dtype=bool)
    for s in shells_sorted:
        keep |= (pool["pareto_shell"] == s).to_numpy()
        if keep.sum() >= target_n:
            break
    # 高不確実性は落とさない（アンサンブル分散の上位10%）
    unc = pool["pred_co2_binary_uptake_0p15bar_298K_sd"].to_numpy()
    keep |= unc >= np.quantile(unc, 0.90)
    pool["selected_by_pareto"] = keep
    # Tier A（水安定性の本命）は ML 予測に依らず全件 Stage 2 へ
    keep = keep | (pool["tier"] == "A").to_numpy()
    pool["stage1_selected"] = keep

    metrics["stage1_selected"] = int(keep.sum())
    metrics["stage1_selected_by_tier"] = (
        pool.loc[pool["stage1_selected"], "tier"].value_counts().to_dict()
    )

    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    pool.to_parquet(config.DATA_PROCESSED / "stage1_ranking.parquet", index=False)
    for t, f in oof_frames.items():
        f.to_parquet(config.DATA_PROCESSED / f"oof_{t}.parquet", index=False)
    with open(config.DATA_PROCESSED / "stage1_metrics.json", "w") as fp:
        json.dump(metrics, fp, indent=2, ensure_ascii=False)
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
