"""母集団とデータベースの分布可視化。

生成物 (docs/figures/):
    fig1_funnel.png        — Stage 0 ファネル
    fig2_descriptors.png   — 記述子分布: MOSAEC全体 vs Stage 0 通過母集団
    fig3_composition.png   — 母集団の金属・Tier・OMS構成
    fig4_domain_shift.png  — ML教師データ(BW-DB) vs 母集団の分布比較
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src import loaders, viz

FIG_DIR = config.PROJECT_ROOT / "docs" / "figures"

DESCRIPTORS = [
    ("pld", "PLD [Å]", (0, 25)),
    ("lcd", "LCD [Å]", (0, 30)),
    ("asa_m2_g", "重量比表面積 [m²/g]", (0, 4000)),
    ("void_fraction", "空隙率 [-]", (0, 1)),
    ("density", "密度 [g/cm³]", (0, 3)),
    ("pore_volume_cm3_g", "細孔容積 [cm³/g]", (0, 1.5)),
]


def _hist_pair(ax, a, b, label_a, label_b, xlabel, xlim):
    bins = np.linspace(*xlim, 40)
    ax.hist(a.dropna().clip(*xlim), bins=bins, density=True, alpha=0.85,
            color=viz.SERIES[0], label=label_a, edgecolor=viz.SURFACE, linewidth=0.4)
    ax.hist(b.dropna().clip(*xlim), bins=bins, density=True, histtype="step",
            linewidth=2.0, color=viz.SERIES[1], label=label_b)
    ax.set_xlabel(xlabel)
    ax.set_yticks([])
    ax.grid(axis="x", visible=False)


def main() -> None:
    viz.apply_style()
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    pool = pd.read_parquet(config.DATA_PROCESSED / "pool.parquet")
    track2 = pd.read_parquet(config.DATA_PROCESSED / "track2.parquet")
    mosaec = loaders.load_mosaec()
    mos_u = mosaec[mosaec["is_unique"]]

    # ---- fig1: ファネル（pool_stats.json から読む） -----------------------
    import json
    stats = json.load(open(config.DATA_PROCESSED / "pool_stats.json"))
    stages = [
        ("入力（MOSAECユニーク＋CoRE）", stats["input_structures"]),
        ("高価数金属（毒性除外込み）", stats["gate_metal_pass"]),
        ("＋ PLD > 3.3 Å", stats["gate_metal_and_pld_pass"]),
        ("＋ 水安定性", stats["stage0_pass"]),
        ("Track 1（物理吸着・GCMC対象）", stats["track1_physisorption"]),
    ]
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    names = [s for s, _ in stages][::-1]
    vals = [v for _, v in stages][::-1]
    bars = ax.barh(names, vals, color=viz.SERIES[0], height=0.62)
    bars[1].set_color(viz.SERIES[1])  # Track1 を強調(下から2番目=Track1)
    bars[0].set_color(viz.SERIES[1])
    for y, v in enumerate(vals):
        ax.text(v * 1.15, y, f"{v:,}", va="center", color=viz.INK2, fontsize=9)
    ax.set_xscale("log")
    ax.set_xlim(500, 3e5)
    ax.set_xlabel("構造数（対数軸）")
    ax.set_title("Stage 0 スクリーニングファネル")
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig1_funnel.png")
    plt.close(fig)

    # ---- fig2: 記述子分布 ----------------------------------------------
    fig, axes = plt.subplots(2, 3, figsize=(11, 5.6))
    for ax, (col, xlabel, xlim) in zip(axes.ravel(), DESCRIPTORS):
        _hist_pair(ax, mos_u[col], pool[col],
                   "MOSAEC-DB 全体（ユニーク）", "Stage 0 通過母集団", xlabel, xlim)
    axes[0, 0].legend(loc="upper right", fontsize=8, frameon=False)
    fig.suptitle("MOF記述子の分布 — データベース全体 vs スクリーニング母集団", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig2_descriptors.png")
    plt.close(fig)

    # ---- fig3: 母集団の構成 ---------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))

    metal_counts = Counter()
    for m in pool["metals"]:
        for x in str(m).split(","):
            if x:
                metal_counts[x] += 1
    top = metal_counts.most_common(12)[::-1]
    axes[0].barh([k for k, _ in top], [v for _, v in top], color=viz.SERIES[0], height=0.62)
    axes[0].set_title("金属元素の出現数（上位12）")
    axes[0].grid(axis="y", visible=False)

    tier_order = ["A", "B", "C"]
    tier_counts = pool["tier"].value_counts().reindex(tier_order).fillna(0)
    axes[1].bar(tier_order, tier_counts.values, color=viz.SERIES[0], width=0.55)
    for x, v in zip(tier_order, tier_counts.values):
        axes[1].text(x, v + 12, f"{int(v):,}", ha="center", color=viz.INK2, fontsize=9)
    axes[1].set_title("水安定性Tier構成")
    axes[1].set_xlabel("Tier（A: Zr/Hf/Ti/Al/Cr純系）")
    axes[1].grid(axis="x", visible=False)

    ev = pool["water_evidence"].value_counts()
    labels = {"metal_heuristic": "金属ヒューリスティクス", "coremof_ml": "CoRE MLモデル",
              "ws24_experimental": "WS24 実験ラベル"}
    names = [labels.get(k, k) for k in ev.index][::-1]
    axes[2].barh(names, ev.values[::-1], color=viz.SERIES[0], height=0.55)
    for y, v in enumerate(ev.values[::-1]):
        axes[2].text(v + 15, y, f"{v:,}", va="center", color=viz.INK2, fontsize=9)
    axes[2].set_title("水安定性の判定根拠")
    axes[2].grid(axis="y", visible=False)

    fig.suptitle(
        f"Stage 0 通過母集団の構成（Track 1: {len(pool):,}件 / Track 2 化学吸着候補: {len(track2):,}件）",
        fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig3_composition.png")
    plt.close(fig)

    # ---- fig4: ドメインシフト（教師 vs 適用先） --------------------------
    bwdb = loaders.load_bwdb()
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    for ax, (col, xlabel, xlim) in zip(
        axes, [DESCRIPTORS[0], DESCRIPTORS[3], DESCRIPTORS[2]]
    ):
        _hist_pair(ax, bwdb[col], pool[col],
                   "BW-DB（ML教師・仮想MOF）", "母集団（実験MOF）", xlabel, xlim)
    axes[0].legend(loc="upper right", fontsize=8, frameon=False)
    fig.suptitle("ドメインシフトの確認 — ML教師データと適用先母集団の記述子分布", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig4_domain_shift.png")
    plt.close(fig)

    print("figures saved to", FIG_DIR)


if __name__ == "__main__":
    main()
