"""対話的3Dビュー（単一HTML）の生成。

骨格（CIF由来スーパーセル）＋吸着CO₂スナップショット（RASPA動画PDBの最終フレーム）を
3Dmol.js で表示する自己完結HTMLを docs/ に書き出す。ブラウザで開くだけで回せる。

    python -m src.viewer3d "2014[Eu][esg]3[ASR]1"
"""

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src.report_process import FIG_DIR  # noqa: F401  (docsパス確認用)
from src.simulate import find_cif

TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>{sid} — 3D viewer</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.1.0/3Dmol-min.js"></script>
<style>
  body {{ margin: 0; font-family: system-ui, sans-serif; background: #fcfcfb; }}
  #hdr {{ padding: 8px 14px; font-size: 14px; color: #0b0b0b; }}
  #hdr .sub {{ color: #52514e; font-size: 12px; }}
  #view {{ width: 100vw; height: 86vh; position: relative; }}
  .chip {{ display: inline-block; padding: 1px 8px; border-radius: 9px;
          font-size: 11px; margin-left: 6px; color: #fff; }}
</style>
</head>
<body>
<div id="hdr">
  <b>{sid}</b> — 混合GCMC (CO₂:N₂=15:85, 1 bar, 298 K) 最終フレーム
  <span class="chip" style="background:#eb6834">CO₂ ({n_co2}分子)</span>
  <span class="sub">｜ドラッグ=回転 / ホイール=ズーム / 右ドラッグ=平行移動｜
  データ: simulations/movie/{sid}/Movies/System_0/*.pdb ＋ 同名CIF</span>
</div>
<div id="view"></div>
<script>
const viewer = $3Dmol.createViewer("view", {{ backgroundColor: "#fcfcfb" }});
const framework = `{framework_pdb}`;
const co2 = `{co2_pdb}`;
viewer.addModel(framework, "pdb");
viewer.setStyle({{model: 0}}, {{stick: {{radius: 0.10, colorscheme: "Jmol"}},
                               sphere: {{scale: 0.16, colorscheme: "Jmol"}}}});
viewer.addModel(co2, "pdb");
viewer.setStyle({{model: 1}}, {{sphere: {{scale: 0.38, color: "#eb6834"}}}});
viewer.zoomTo();
viewer.render();
</script>
</body>
</html>
"""


def atoms_to_pdb(atoms) -> str:
    from ase.io import write
    buf = StringIO()
    write(buf, atoms, format="proteindatabank")
    return buf.getvalue()


def build(sid: str) -> Path:
    from ase import Atoms
    from ase.io import read

    framework = read(find_cif(sid)) * (2, 2, 2)

    movie_dir = config.PROJECT_ROOT / "simulations" / "movie" / sid / "Movies" / "System_0"
    pdbs = sorted(movie_dir.glob("Movie_*_CO2_*.pdb"))
    co2_pos, co2_sym = [], []
    if pdbs:
        last = pdbs[0].read_text().split("MODEL")[-1]
        for line in last.splitlines():
            if line.startswith(("ATOM", "HETATM")):
                co2_pos.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
                co2_sym.append("C" if line[12:16].strip().startswith("C") else "O")
    gas = Atoms(symbols=co2_sym, positions=co2_pos, cell=framework.cell, pbc=True)
    gas.wrap()

    html = TEMPLATE.format(
        sid=sid, n_co2=len(co2_sym) // 3,
        framework_pdb=atoms_to_pdb(framework).replace("`", ""),
        co2_pdb=atoms_to_pdb(gas).replace("`", ""),
    )
    out = config.PROJECT_ROOT / "docs" / f"viewer_{sid}.html"
    out.write_text(html)
    return out


if __name__ == "__main__":
    print("written:", build(sys.argv[1]))
