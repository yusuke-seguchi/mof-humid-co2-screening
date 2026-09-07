"""Stage 1 の結果解釈図。

生成物 (docs/figures/):
    fig5_parity.png       — OOF parity（モデルがどこまで信頼できるか）
    fig6_calibration.png  — 特徴量重要度 + Keskin実験構造での順位校正
    fig7_pareto.png       — 母集団の予測性能マップと Stage 1 選抜
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src import loaders, viz

FIG_DIR = config.PROJECT_ROOT / "docs" / "figures"
CMAP = LinearSegmentedColormap.from_list("seq_blue", [viz.SURFACE] + viz.SEQ_BLUE)

PARITY = [
    ("co2_binary_uptake_0p15bar_298K", "CO₂混合吸着量 @0.15 bar [mmol/g]", False),
    ("co2_n2_selectivity", "CO₂/N₂選択性 [log₁₀]", True),
    ("qst_co2_kcal_mol", "CO₂吸着熱 [kcal/mol]", False),
]


def main() -> None:
    viz.apply_style()
    metrics = json.load(open(config.DATA_PROCESSED / "stage1_metrics.json"))
    pool = pd.read_parquet(config.DATA_PROCESSED / "stage1_ranking.parquet")

    # ---- fig5: OOF parity ------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.7))
    for ax, (target, label, _) in zip(axes, PARITY):
        oof = pd.read_parquet(config.DATA_PROCESSED / f"oof_{target}.parquet")
        lim = (min(oof["y"].min(), oof["oof"].min()), max(oof["y"].max(), oof["oof"].max()))
        ax.hexbin(oof["y"], oof["oof"], gridsize=60, cmap=CMAP, bins="log",
                  extent=(*lim, *lim), linewidths=0)
        ax.plot(lim, lim, color=viz.INK2, linewidth=1.0, linestyle="--")
        r2 = metrics[target]["r2_grouped_oof"]
        ax.text(0.05, 0.92, f"R² = {r2:.2f}\n(グループ分割OOF)", transform=ax.transAxes,
                fontsize=9, color=viz.INK2, va="top")
        ax.set_xlabel(f"GCMC値: {label}")
        ax.set_ylabel("ML予測（学習時未見）")
        ax.set_aspect("equal")
    fig.suptitle("ML予測の信頼性 — BW-DB 32万構造でのリーク対策済みホールドアウト性能",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig5_parity.png")
    plt.close(fig)

    # ---- fig6: 特徴量重要度 + Keskin校正 ---------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    imp = metrics["co2_binary_uptake_0p15bar_298K"]["feature_importance"]
    jp = {"pld": "PLD", "lcd": "LCD", "asa_m2_g": "比表面積",
          "void_fraction": "空隙率", "pore_volume_cm3_g": "細孔容積", "density": "密度"}
    items = sorted(imp.items(), key=lambda kv: kv[1])
    axes[0].barh([jp[k] for k, _ in items], [v for _, v in items],
                 color=viz.SERIES[0], height=0.6)
    axes[0].set_title("特徴量重要度（CO₂吸着量モデル, gain）")
    axes[0].grid(axis="y", visible=False)

    keskin = loaders.load_keskin()
    cal = pool.merge(keskin, on="refcode", how="inner").dropna(
        subset=["pred_co2_n2_selectivity", "s_co2n2_1bar"])
    axes[1].scatter(cal["s_co2n2_1bar"], cal["pred_co2_n2_selectivity"], s=22,
                    color=viz.SERIES[0], alpha=0.75, edgecolors=viz.SURFACE, linewidths=0.5)
    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    kc = metrics["keskin_calibration"]
    axes[1].text(0.05, 0.90,
                 f"順位相関 ρ = {kc['spearman_rho']:.2f}（n={kc['n_overlap']}）",
                 transform=axes[1].transAxes, fontsize=9, color=viz.INK2)
    axes[1].set_xlabel("Keskin 2018 GCMC選択性（実験構造, 1 bar）")
    axes[1].set_ylabel("ML予測選択性（0.15 bar）")
    axes[1].set_title("実験構造での校正チェック（仮想→実験のずれ）")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig6_calibration.png")
    plt.close(fig)

    # ---- fig7: Pareto マップ ---------------------------------------------
    fig, ax = plt.subplots(figsize=(8.2, 5.4))
    tiers = ["A", "B", "C"]
    colors = {t: viz.SERIES[i] for i, t in enumerate(tiers)}
    x = pool["pred_co2_n2_selectivity"]
    y = pool["pred_co2_binary_uptake_0p15bar_298K"]
    unselected = ~pool["stage1_selected"]
    ax.scatter(x[unselected], y[unselected], s=14, color=viz.GRID, alpha=0.8,
               label="非選抜", edgecolors="none")
    for t in tiers:
        m = pool["stage1_selected"] & (pool["tier"] == t)
        ax.scatter(x[m], y[m], s=26, color=colors[t], alpha=0.9,
                   edgecolors=viz.SURFACE, linewidths=0.4,
                   label=f"Tier {t}（選抜 {int(m.sum())}件）")
    front = pool["pareto_shell"] == 0
    fx = x[front].sort_values()
    ax.plot(fx, y[front].loc[fx.index], color=viz.INK2, linewidth=1.0,
            linestyle=":", label="第1Paretoフロント")
    ax.set_xscale("log")
    ax.set_xlabel("ML予測 CO₂/N₂選択性（0.15/0.85 bar, 298 K）")
    ax.set_ylabel("ML予測 CO₂混合吸着量 [mmol/g]")
    ax.set_title(f"Stage 1 選抜マップ — 母集団{len(pool):,}件 → Stage 2へ{int(pool['stage1_selected'].sum()):,}件")
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig7_pareto.png")
    plt.close(fig)

    print("figures saved")


if __name__ == "__main__":
    main()
