"""吸着密度マップ (fig16): RASPAの3D密度グリッド(VTK)を投影図にする。

    python -m src.report_density "2014[Eu][esg]3[ASR]1"
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src import viz
from matplotlib.colors import LinearSegmentedColormap

FIG_DIR = config.PROJECT_ROOT / "docs" / "figures"
CMAP = LinearSegmentedColormap.from_list("seq_blue", [viz.SURFACE] + viz.SEQ_BLUE)


def read_vtk_grid(path: Path) -> np.ndarray:
    """RASPAのSTRUCTURED_POINTS形式VTKを読み、(nx,ny,nz)配列で返す。"""
    text = path.read_text()
    dims = re.search(r"DIMENSIONS\s+(\d+)\s+(\d+)\s+(\d+)", text)
    nx, ny, nz = (int(dims.group(i)) for i in (1, 2, 3))
    body = text.split("LOOKUP_TABLE default", 1)[1]
    vals = np.fromstring(body, sep=" ")[: nx * ny * nz]
    # VTKはx が最速で回る → (nz,ny,nx) に reshape して転置
    return vals.reshape((nz, ny, nx)).transpose(2, 1, 0)


def main(sid: str) -> None:
    viz.apply_style()
    vtk_dir = config.PROJECT_ROOT / "simulations" / "density" / sid / "VTK" / "System_0"
    cands = sorted(vtk_dir.glob("DensityProfile*CO2*.vtk")) or sorted(
        vtk_dir.glob("DensityProfile*.vtk"))
    if not cands:
        print("no density vtk found in", vtk_dir)
        return
    grid = read_vtk_grid(cands[0])
    print("grid:", grid.shape, "max:", grid.max())

    axes_def = [(2, "a–b面（c軸方向に平均）"), (1, "a–c面（b軸方向に平均）"),
                (0, "b–c面（a軸方向に平均）")]
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.0))
    for ax, (axis, label) in zip(axes, axes_def):
        proj = grid.mean(axis=axis).T
        im = ax.imshow(proj, origin="lower", cmap=CMAP, aspect="auto")
        ax.set_title(label, fontsize=9.5)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.colorbar(im, ax=axes, shrink=0.8, label="CO₂存在密度（時間平均, a.u.）")
    fig.suptitle(f"CO₂吸着密度マップ — {sid}（混合GCMC 0.15/0.85 bar, 298 K）",
                 fontweight="bold")
    viz.add_source(fig, f"simulations/density/{sid}/VTK/System_0/{cands[0].name}",
                   script="src/report_density.py")
    fig.savefig(FIG_DIR / "fig16_density.png", bbox_inches="tight")
    plt.close(fig)
    print("fig16 saved")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2014[Eu][esg]3[ASR]1")
