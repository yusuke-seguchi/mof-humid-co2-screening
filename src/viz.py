"""matplotlib 用の共通スタイル（dataviz スキルの検証済みライトパレット準拠）。"""

from __future__ import annotations

import matplotlib as mpl

# 検証済みカテゴリカルパレット（light）: 固定順で割り当て、循環させない
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"


def add_source(fig, *sources: str, script: str | None = None) -> None:
    """図の左下に元データファイルと生成スクリプトを明記する（再現性のため）。"""
    txt = "データ: " + " , ".join(sources)
    if script:
        txt += f"  |  生成: {script}"
    fig.text(0.01, 0.006, txt, fontsize=6.5, color=MUTED, ha="left")


def apply_style() -> None:
    mpl.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "text.color": INK,
            "axes.labelcolor": INK2,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "axes.edgecolor": AXIS,
            "axes.linewidth": 0.8,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "axes.axisbelow": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            # 日本語フォント: macOS → Linux/WSL2 → Windows の順にフォールバック
            "font.family": ["Hiragino Sans", "Noto Sans CJK JP", "IPAexGothic",
                            "Yu Gothic", "Meiryo", "sans-serif"],
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "figure.dpi": 150,
            "lines.linewidth": 2.0,
        }
    )
