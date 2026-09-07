"""「なぜ上位MOFは良いのか」の記述子分析。

fig14_why_top.png       — パイロット20件: 性能を分ける記述子の予備分析
fig15_widom_insight.png — Widom全数: 上位10% vs 残りの記述子分布（完了後に実行）
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


def load_pilot() -> pd.DataFrame:
    df = pd.read_csv(config.DATA_PROCESSED / "pilot_batch_enriched.csv")
    return df


def fig_why_top() -> None:
    df = load_pilot()
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.0))

    # (1) OMS の効果
    ax = axes[0]
    for i, (flag, label) in enumerate([(False, "OMSなし"), (True, "OMSあり")]):
        vals = df.loc[df["has_oms"] == flag, "co2_mol_kg"]
        x = np.full(len(vals), i) + np.random.default_rng(1).uniform(-0.08, 0.08, len(vals))
        ax.scatter(x, vals, s=42, color=viz.SERIES[i], alpha=0.85,
                   edgecolors=viz.SURFACE, linewidths=0.5)
        ax.hlines(vals.mean(), i - 0.2, i + 0.2, color=viz.INK, linewidth=2)
        ax.text(i, vals.mean() + 0.25, f"平均 {vals.mean():.1f}", ha="center",
                fontsize=9, color=viz.INK2)
    ax.set_xticks([0, 1], ["OMSなし\n(n=%d)" % (~df["has_oms"]).sum(),
                           "OMSあり\n(n=%d)" % df["has_oms"].sum()])
    ax.set_ylabel("GCMC CO₂吸着量 [mmol/g]")
    ax.set_title("① 吸着量はOMSの有無で3.6倍差\n（幾何記述子はどれも無相関 |ρ|<0.1）")
    ax.grid(axis="x", visible=False)

    # (2) 選択性は「密で狭い」構造ほど高い
    ax = axes[1]
    for t, c in zip(("A", "B", "C"), viz.SERIES[:3]):
        m = df["tier"] == t
        ax.scatter(df.loc[m, "density"], df.loc[m, "s_gcmc"], s=42, color=c,
                   label=f"Tier {t}", edgecolors=viz.SURFACE, linewidths=0.5)
    rho = spearmanr(df["density"], df["s_gcmc"], nan_policy="omit").statistic
    ax.set_yscale("log")
    ax.set_xlabel("結晶密度 [g/cm³]")
    ax.set_ylabel("GCMC CO₂/N₂選択性")
    ax.set_title(f"② 選択性は密度と正相関（ρ={rho:+.2f}）\n空隙率とは負相関（ρ=-0.59）")
    ax.legend(fontsize=8, frameon=False, loc="lower right")

    # (3) 疎水性クラスとの関係（湿潤リスクの示唆）
    ax = axes[2]
    order = ["none", "weak", "strong", "superstrong_high_loading"]
    labels = {"none": "分類なし\n(親水寄り)", "weak": "弱疎水", "strong": "強疎水",
              "superstrong_high_loading": "超強疎水"}
    med = df.groupby("kh_class")["co2_mol_kg"].median().reindex(order)
    ns = df.groupby("kh_class").size().reindex(order).fillna(0)
    ax.bar([labels[k] for k in order], med.values, color=viz.SERIES[0], width=0.6)
    for i, (v, n) in enumerate(zip(med.values, ns.values)):
        if not np.isnan(v):
            ax.text(i, v + 0.1, f"{v:.1f}\n(n={int(n)})", ha="center", fontsize=8,
                    color=viz.INK2)
    ax.set_ylabel("CO₂吸着量の中央値 [mmol/g]")
    ax.set_title("③ 乾燥条件の勝者は親水寄りに偏る\n→ 湿潤チェックで逆転リスク")
    ax.grid(axis="x", visible=False)

    fig.suptitle("なぜ上位MOFは強いのか — パイロット20件の予備分析（n小のため傾向値）",
                 fontweight="bold")
    viz.add_source(fig, "data/processed/pilot_batch_enriched.csv",
                   script="src/report_insight.py")
    fig.tight_layout(rect=(0, 0.025, 1, 1))
    fig.savefig(FIG_DIR / "fig14_why_top.png")
    plt.close(fig)


def fig_widom_insight(top_frac: float = 0.1) -> None:
    """Widom全数完了後: CO₂ Henry上位10% vs 残りの記述子分布（Uni-MOF Fig6e方式）。"""
    path = config.DATA_PROCESSED / "widom_results.csv"
    if not path.exists():
        print("widom results not ready")
        return
    w = pd.read_csv(path)
    w = w[(w["status"] == "ok") & (w.get("n_warnings", 0) == 0)]
    if len(w) < 100:
        print(f"widom rows={len(w)} <100, skipping")
        return
    pool = pd.read_parquet(config.DATA_PROCESSED / "stage1_ranking.parquet")
    d = w.merge(pool, on="structure_id", how="left")
    d["s_henry"] = d["kh_co2_mol_kg_pa"] / d["kh_n2_mol_kg_pa"]
    thr = d["kh_co2_mol_kg_pa"].quantile(1 - top_frac)
    d["is_top"] = d["kh_co2_mol_kg_pa"] >= thr

    cols = [("pld", "PLD [Å]", (2, 12)), ("lcd", "LCD [Å]", (2, 16)),
            ("density", "密度 [g/cm³]", (0.5, 3)), ("void_fraction", "空隙率", (0, 0.8))]
    fig, axes = plt.subplots(1, 4, figsize=(12.5, 3.4))
    for ax, (col, label, xlim) in zip(axes, cols):
        bins = np.linspace(*xlim, 30)
        ax.hist(d.loc[~d["is_top"], col].dropna().clip(*xlim), bins=bins, density=True,
                alpha=0.85, color=viz.SERIES[0], label="残り90%",
                edgecolor=viz.SURFACE, linewidth=0.3)
        ax.hist(d.loc[d["is_top"], col].dropna().clip(*xlim), bins=bins, density=True,
                histtype="step", linewidth=2.0, color=viz.SERIES[1],
                label="CO₂ Henry上位10%")
        ax.set_xlabel(label)
        ax.set_yticks([])
    axes[0].legend(fontsize=8, frameon=False)
    oms_top = d.loc[d["is_top"], "has_oms"].mean()
    oms_rest = d.loc[~d["is_top"], "has_oms"].mean()
    fig.suptitle(
        f"CO₂ Henry係数 上位10%の共通記述子（n={len(d)}; OMS率 上位{oms_top:.0%} vs 残り{oms_rest:.0%}）",
        fontweight="bold")
    viz.add_source(fig, "data/processed/widom_results.csv",
                   "data/processed/stage1_ranking.parquet", script="src/report_insight.py")
    fig.tight_layout(rect=(0, 0.03, 1, 0.99))
    fig.savefig(FIG_DIR / "fig15_widom_insight.png")
    plt.close(fig)
    print("fig15 saved")


if __name__ == "__main__":
    viz.apply_style()
    fig_why_top()
    fig_widom_insight()
