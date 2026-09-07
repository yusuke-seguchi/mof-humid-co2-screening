"""fig0: スクリーニング全体のフロー図（社内展開資料の冒頭用）。"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src import viz

FIG_DIR = config.PROJECT_ROOT / "docs" / "figures"


def box(ax, x, y, w, h, title, lines, fc, ec, title_color=None, lw=1.4):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012",
                                facecolor=fc, edgecolor=ec, linewidth=lw))
    ax.text(x + w / 2, y + h - 0.09, title, ha="center", va="top",
            fontsize=10.5, fontweight="bold", color=title_color or viz.INK)
    ax.text(x + w / 2, y + h - 0.44, "\n".join(lines), ha="center", va="top",
            fontsize=8.6, color=viz.INK2, linespacing=1.5)


def arrow(ax, x1, y1, x2, y2, color, style="-|>", lw=2.0, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                 mutation_scale=16, color=color, linewidth=lw,
                                 linestyle=ls, shrinkA=2, shrinkB=2))


def main() -> None:
    viz.apply_style()
    fig, ax = plt.subplots(figsize=(12.8, 5.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")

    blue_bg, blue = "#e8f1fc", viz.SERIES[0]
    orange_bg, orange = "#fdece4", viz.SERIES[1]
    aqua_bg, aqua = "#e4f5ee", viz.SERIES[2]
    gray_bg = "#f0efec"

    # ---- メインフロー（下段） ----
    y, h, w = 0.55, 1.25, 1.72
    xs = [0.15, 2.15, 4.15, 6.15, 8.15]
    box(ax, xs[0], y, w, h, "公開データベース",
        ["実験MOF 117,275構造", "(MOSAEC + CoRE)", "費用ゼロ"], gray_bg, viz.AXIS)
    box(ax, xs[1], y, w, h, "Stage 0: 記述子ゲート",
        ["高価数金属・毒性除外", "細孔径 > 3.3 Å・水安定性", "→ 2,475件  (~0秒/件)"],
        blue_bg, blue)
    box(ax, xs[2], y, w, h, "Stage 1: Widom粗選別",
        ["Henry係数で順位付け", "806件計算 → 471件選抜", "(~5分/件)"], blue_bg, blue)
    box(ax, xs[3], y, w, h, "Stage 2: 混合GCMC",
        ["CO₂:N₂=15:85, 1bar, 298K", "吸着量・選択性の精密値", "(1-10時間/件) 実行中"],
        orange_bg, orange)
    box(ax, xs[4], y, w, h, "Stage 3: 最終選別",
        ["湿潤チェック(水との競合)", "実験DB(NIST)との整合確認", "→ 最終候補 ~50件"],
        aqua_bg, aqua)
    for i in range(4):
        arrow(ax, xs[i] + w, y + h / 2, xs[i + 1], y + h / 2, viz.INK2)

    # ---- 上段: ML転換の物語 ----
    box(ax, 3.0, 2.6, 2.0, 1.0, "当初計画: ML粗選別",
        ["32万件で学習するも", "実測と無相関 ρ=0.16 ✗"], gray_bg, viz.AXIS)
    box(ax, 5.7, 2.6, 2.2, 1.0, "検証パイロット (GCMC 20件)",
        ["小さく検証して発見", "→ 物理計算へ1日で転換"], aqua_bg, aqua)
    arrow(ax, 5.0, 3.1, 5.7, 3.1, viz.INK2)
    arrow(ax, 5.0, 2.6, 5.0, y + h, orange, ls=(0, (4, 3)))
    ax.text(5.08, 2.28, "転換後 ρ=0.87 ✓", fontsize=9, color=orange, fontweight="bold")

    # ---- 分離枠の注記（下） ----
    ax.text(0.15, 0.18, "分離枠: 化学吸着候補144件（Track 2）／擬化学吸着フラグ15件 — "
                        "古典力場で予測できないものは別枠で明示", fontsize=8.6, color=viz.INK2)

    ax.set_title("スクリーニング全体フロー — 安い計算で絞り、高い計算は有望株だけに",
                 fontsize=13, fontweight="bold", pad=14)
    viz.add_source(fig, "docs/dev_log.md（経緯）", "data/processed/pool_stats.json",
                   script="src/report_flow.py")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(FIG_DIR / "fig0_flow.png", dpi=170)
    print("fig0 saved")


if __name__ == "__main__":
    main()
