"""fig17: 採用データセットの中身の分布（社内展開資料用）。

(a) MOSAEC-DB全体の金属元素分布（高価数をハイライト）
(b) PLD分布の比較: MOSAEC全体 / CoRE MOF 2024(CR) / BW-DB(ML教師・仮想)
(c) 密度分布の同比較
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


def main() -> None:
    viz.apply_style()
    mosaec = loaders.load_mosaec()
    core = pd.concat(
        [loaders.load_coremof2024_asr(), loaders.load_coremof2024_csd_modified()],
        ignore_index=True,
    )
    bwdb = loaders.load_bwdb()

    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.0))

    # (a) 金属分布（MOSAEC全体）
    c = Counter()
    for s in mosaec["metals"]:
        for m in s:
            c[m] += 1
    top = c.most_common(15)[::-1]
    hv = config.TIER_C_METALS
    colors = [viz.SERIES[1] if k in hv else viz.SERIES[0] for k, _ in top]
    axes[0].barh([k for k, _ in top], [v for _, v in top], color=colors, height=0.65)
    axes[0].set_title("金属元素の出現数（MOSAEC-DB全体 124k）\n橙=高価数（本プロジェクトの対象）")
    axes[0].grid(axis="y", visible=False)
    axes[0].set_xlabel("構造数")

    # (b)(c) PLD・密度の分布比較
    series = [
        ("MOSAEC-DB（実験, 124k）", mosaec, viz.SERIES[0]),
        ("CoRE MOF 2024 CR（実験, 11k）", core, viz.SERIES[1]),
        ("BW-DB（仮想・ML教師, 325k）", bwdb, viz.SERIES[2]),
    ]
    for ax, (col, xlabel, xlim) in zip(
        axes[1:], [("pld", "PLD [Å]", (0, 20)), ("density", "結晶密度 [g/cm³]", (0, 3))]
    ):
        bins = np.linspace(*xlim, 45)
        for label, df, color in series:
            vals = pd.to_numeric(df[col], errors="coerce").dropna().clip(*xlim)
            ax.hist(vals, bins=bins, density=True, histtype="step",
                    linewidth=2.0, color=color, label=label)
        ax.set_xlabel(xlabel)
        ax.set_yticks([])
        ax.grid(axis="x", visible=False)
    axes[1].legend(fontsize=7.5, frameon=False)
    axes[1].set_title("細孔径（PLD）の分布")
    axes[2].set_title("結晶密度の分布")

    fig.suptitle("採用データセットの中身 — 金属種と構造記述子の分布", fontweight="bold")
    viz.add_source(fig, "data/raw/mosaec_db.csv", "data/raw/coremof2024_asr.csv",
                   "data/raw/csd_modified/.../CR_data_*.csv",
                   "data/raw/bwdb_all_MOFs_screening_data.csv",
                   script="src/report_datasets.py")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIG_DIR / "fig17_datasets.png")
    plt.close(fig)
    print("fig17 saved")


if __name__ == "__main__":
    main()
