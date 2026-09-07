"""パイロットバッチの解釈図。

    fig8_ml_vs_gcmc.png — ML予測とGCMC実測の乖離（Stage 1の信頼性検証）
    fig9_timing.png     — 実行時間の構造依存性と716件への外挿
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src import viz

FIG_DIR = config.PROJECT_ROOT / "docs" / "figures"


def main() -> None:
    viz.apply_style()
    df = pd.read_csv(config.DATA_PROCESSED / "pilot_batch_results.csv")
    df["s_gcmc"] = (df["co2_mol_kg"] / df["n2_mol_kg"]) / (0.15 / 0.85)
    df["wall_h"] = df["wall_s"] / 3600
    colors = {"A": viz.SERIES[0], "B": viz.SERIES[1], "C": viz.SERIES[2]}

    # ---- fig8: ML vs GCMC ------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4))
    specs = [
        ("pred_co2_binary_uptake_0p15bar_298K", "co2_mol_kg",
         "CO₂吸着量 [mmol/g]", axes[0], False),
        ("pred_co2_n2_selectivity", "s_gcmc", "CO₂/N₂選択性", axes[1], True),
    ]
    for pred_col, gcmc_col, label, ax, logscale in specs:
        for t in ("A", "B", "C"):
            m = df["tier"] == t
            oms = m & df["has_oms"]
            ax.scatter(df.loc[m & ~df["has_oms"], pred_col],
                       df.loc[m & ~df["has_oms"], gcmc_col],
                       s=48, color=colors[t], label=f"Tier {t}",
                       edgecolors=viz.SURFACE, linewidths=0.6)
            ax.scatter(df.loc[oms, pred_col], df.loc[oms, gcmc_col],
                       s=48, color=colors[t], marker="^",
                       edgecolors=viz.INK2, linewidths=0.8)
        lims = (min(df[pred_col].min(), df[gcmc_col].min()) * 0.8,
                max(df[pred_col].max(), df[gcmc_col].max()) * 1.25)
        ax.plot(lims, lims, linestyle="--", color=viz.INK2, linewidth=1.0)
        if logscale:
            ax.set_xscale("log")
            ax.set_yscale("log")
        rho = spearmanr(df[pred_col], df[gcmc_col]).statistic
        ax.text(0.05, 0.92, f"順位相関 ρ = {rho:.2f}", transform=ax.transAxes,
                fontsize=10, color=viz.INK2)
        ax.set_xlabel(f"ML予測 {label}")
        ax.set_ylabel(f"GCMC実測 {label}")
    axes[0].legend(loc="lower right", fontsize=8, frameon=False,
                   title="▲ = OMSあり", title_fontsize=8)
    fig.suptitle("パイロット20構造: ML予測はこの母集団でほぼ無相関 → 物理計算主導へ切替",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig8_ml_vs_gcmc.png")
    plt.close(fig)

    # ---- fig9: 実行時間 ---------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    for t in ("A", "B", "C"):
        m = df["tier"] == t
        axes[0].scatter(df.loc[m, "co2_mol_kg"], df.loc[m, "wall_h"],
                        s=48, color=colors[t], label=f"Tier {t}",
                        edgecolors=viz.SURFACE, linewidths=0.6)
    axes[0].set_xlabel("GCMC CO₂吸着量 [mmol/g]")
    axes[0].set_ylabel("実行時間 [h]（15,000サイクル）")
    axes[0].set_title("計算コストは吸着量にほぼ比例")
    axes[0].legend(fontsize=8, frameon=False)

    med, mean = df["wall_h"].median(), df["wall_h"].mean()
    scenarios = [
        ("全716件・現サイクル", 716 * mean / 6 / 24),
        ("全716件・サイクル半減", 716 * mean / 2 / 6 / 24),
        ("上位300件・サイクル半減", 300 * mean / 2 / 6 / 24),
        ("上位200件・サイクル半減", 200 * mean / 2 / 6 / 24),
    ]
    names = [s for s, _ in scenarios][::-1]
    vals = [v for _, v in scenarios][::-1]
    bars = axes[1].barh(names, vals, color=viz.SERIES[0], height=0.6)
    bars[0].set_color(viz.SERIES[2])
    bars[1].set_color(viz.SERIES[2])
    for y, v in enumerate(vals):
        axes[1].text(v + 0.25, y, f"{v:.1f}日", va="center", color=viz.INK2, fontsize=9)
    axes[1].set_xlabel("M3ローカル6並列での所要日数")
    axes[1].set_title(f"716件への外挿（平均 {mean:.1f} h/件, 中央値 {med:.1f} h）")
    axes[1].grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig9_timing.png")
    plt.close(fig)
    print("saved fig8, fig9")


if __name__ == "__main__":
    main()
