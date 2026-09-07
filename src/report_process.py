"""シミュレーション過程とMOF構造の可視化。

生成物 (docs/figures/):
    fig11_convergence.png — パイロットGCMCの吸着量収束トレース
    fig12_structures.png  — 代表MOF構造のギャラリー（ASE描画）
    fig13_snapshot.png    — 吸着CO₂分子のスナップショット（動画ジョブ完了後）
    fig10_widom.png       — Widom Henry係数の途中経過（10件以上たまり次第）
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src import viz
from src.simulate import find_cif

FIG_DIR = config.PROJECT_ROOT / "docs" / "figures"
PILOT_DIR = config.PROJECT_ROOT / "simulations" / "pilot_batch"

SHOWCASE = [
    ("2022[Tb][umc]3[ASR]1", "Tb系 / 6.88 mmol/g"),
    ("2020[Sc][nan]3[ASR]1", "Sc系 / 5.81 mmol/g"),
    ("2014[Eu][esg]3[ASR]1", "Eu系 / 4.87 mmol/g"),
    ("2019[Zr][scu]3[ASR]4", "Zr系(Tier A) / 3.48 mmol/g"),
]


def parse_trace(structure_id: str) -> pd.DataFrame:
    """RASPA出力から (cycle, CO2 mol/kg) の収束トレースを抽出する。"""
    data = next((PILOT_DIR / structure_id / "Output" / "System_0").glob("*.data")).read_text()
    rows = []
    # 初期化フェーズと本計算フェーズの両方を拾う
    pattern = re.compile(
        r"(\[Init\] )?Current cycle: (\d+) out of (\d+).*?"
        r"absolute adsorption:.*?([\d.]+) \[mol/kg\]",
        re.S,
    )
    init_total = None
    for m in pattern.finditer(data):
        is_init = m.group(1) is not None
        cyc = int(m.group(2))
        if is_init:
            init_total = int(m.group(3))
            rows.append((cyc, float(m.group(4)), "init"))
        else:
            rows.append((cyc + (init_total or 0), float(m.group(4)), "prod"))
    return pd.DataFrame(rows, columns=["cycle", "co2_mol_kg", "phase"])


def fig_convergence() -> None:
    fig, ax = plt.subplots(figsize=(8, 4.4))
    for i, (sid, label) in enumerate(SHOWCASE):
        try:
            tr = parse_trace(sid)
        except (StopIteration, FileNotFoundError):
            continue
        ax.plot(tr["cycle"], tr["co2_mol_kg"], color=viz.SERIES[i],
                label=f"{sid}（{label}）", linewidth=1.8)
    init_end = 5000
    ax.axvline(init_end, color=viz.AXIS, linewidth=1.0, linestyle="--")
    ax.text(init_end, ax.get_ylim()[1] * 0.97, " 初期化ここまで", fontsize=8,
            color=viz.INK2, va="top")
    ax.set_xlabel("MCサイクル")
    ax.set_ylabel("CO₂吸着量 [mol/kg]")
    ax.set_title("GCMCの収束過程 — 吸着量がプラトーに達してから統計を取る")
    ax.legend(fontsize=7.5, frameon=False, loc="center right")
    viz.add_source(fig, "simulations/pilot_batch/<構造ID>/Output/System_0/*.data",
                   script="src/report_process.py")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(FIG_DIR / "fig11_convergence.png")
    plt.close(fig)


def fig_structures() -> None:
    from ase.io import read
    from ase.visualize.plot import plot_atoms

    fig, axes = plt.subplots(1, 4, figsize=(12.5, 3.6))
    for ax, (sid, label) in zip(axes, SHOWCASE):
        atoms = read(find_cif(sid))
        plot_atoms(atoms, ax, radii=0.45, rotation="8x,12y,0z")
        ax.set_axis_off()
        ax.set_title(f"{sid}\n{label}", fontsize=8.5)
    fig.suptitle("パイロット上位構造（単位胞、GCMC乾燥条件の吸着量を併記）", fontweight="bold")
    viz.add_source(fig, "data/raw/coremof_si_cifs/SI/CR/ASR/<構造ID>.cif",
                   script="src/report_process.py")
    fig.tight_layout(rect=(0, 0.03, 1, 0.99))
    fig.savefig(FIG_DIR / "fig12_structures.png", dpi=170)
    plt.close(fig)


def fig_snapshot() -> None:
    """RASPAの動画出力（PDB）から最終フレームの吸着CO₂を骨格に重ねて描く。"""
    from ase import Atoms
    from ase.io import read
    from ase.visualize.plot import plot_atoms

    sid = "2014[Eu][esg]3[ASR]1"
    movie_dir = config.PROJECT_ROOT / "simulations" / "movie" / sid / "Movies" / "System_0"
    pdbs = sorted(movie_dir.glob("Movie_*_CO2_*.pdb")) if movie_dir.exists() else []
    if not pdbs:
        print("snapshot: movie output not ready, skipping")
        return
    text = pdbs[0].read_text()
    last_model = text.split("MODEL")[-1]
    co2_pos, co2_sym = [], []
    for line in last_model.splitlines():
        if line.startswith(("ATOM", "HETATM")):
            x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
            sym = "C" if line[12:16].strip().startswith("C") else "O"
            co2_pos.append((x, y, z))
            co2_sym.append(sym)
    framework = read(find_cif(sid)) * (2, 2, 2)
    # CO2座標を周期境界でスーパーセル内に折り返す（RASPAはunwrapped座標を出力する）
    # 骨格に存在しない元素記号(P/S)で描き分け、1オブジェクトに結合して座標系を揃える
    vis_sym = ["P" if s == "C" else "S" for s in co2_sym]
    gas = Atoms(symbols=vis_sym, positions=co2_pos, cell=framework.cell, pbc=True)
    gas.wrap()
    combined = framework + gas
    fig, ax = plt.subplots(figsize=(6.4, 5.6))
    plot_atoms(combined, ax, radii=0.3, rotation="0x,0y,0z")
    ax.set_axis_off()
    ax.set_title(f"吸着CO₂のスナップショット — {sid}\n"
                 f"(混合GCMC 0.15/0.85 bar, 298 K, 最終フレーム, "
                 f"橙/黄の3原子分子=CO₂, {len(co2_sym)//3}分子)",
                 fontsize=9.5)
    viz.add_source(fig, f"simulations/movie/{sid}/Movies/System_0/*.pdb",
                   f"data/raw/coremof_si_cifs/SI/CR/ASR/{sid}.cif",
                   script="src/report_process.py")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIG_DIR / "fig13_snapshot.png", dpi=170)
    plt.close(fig)


def fig_widom_progress() -> None:
    path = config.DATA_PROCESSED / "widom_results.csv"
    if not path.exists():
        print("widom: no results yet")
        return
    df = pd.read_csv(path)
    df = df[df["status"] == "ok"].dropna(subset=["kh_co2_mol_kg_pa", "kh_n2_mol_kg_pa"])
    if len(df) < 10:
        print("widom: <10 results, skipping")
        return
    pool = pd.read_parquet(config.DATA_PROCESSED / "stage1_ranking.parquet")
    df = df.merge(pool[["structure_id", "tier"]], on="structure_id", how="left")
    df["s_henry"] = df["kh_co2_mol_kg_pa"] / df["kh_n2_mol_kg_pa"]
    fig, ax = plt.subplots(figsize=(7.6, 5))
    colors = {"A": viz.SERIES[0], "B": viz.SERIES[1], "C": viz.SERIES[2]}
    for t in ("A", "B", "C"):
        m = df["tier"] == t
        ax.scatter(df.loc[m, "kh_co2_mol_kg_pa"], df.loc[m, "s_henry"], s=26,
                   color=colors[t], label=f"Tier {t}（{int(m.sum())}件）",
                   alpha=0.85, edgecolors=viz.SURFACE, linewidths=0.4)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("CO₂ Henry係数 [mol/kg/Pa]（大きいほど低圧吸着に有利）")
    ax.set_ylabel("Henry選択性 CO₂/N₂")
    ax.set_title(f"Widom挿入の途中経過 — {len(df)}/547 件完了")
    ax.legend(fontsize=8, frameon=False)
    viz.add_source(fig, "data/processed/widom_results.csv",
                   "data/processed/stage1_ranking.parquet",
                   script="src/report_process.py")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(FIG_DIR / "fig10_widom.png")
    plt.close(fig)


if __name__ == "__main__":
    viz.apply_style()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig_convergence()
    fig_structures()
    fig_snapshot()
    fig_widom_progress()
    print("done")
