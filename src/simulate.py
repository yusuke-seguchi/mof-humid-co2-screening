"""RASPA ジョブの入力生成・実行・結果回収。

使い方（パイロット1構造）:
    python -m src.simulate pilot "2016[Fe][hcb]2[ASR]1" --cycles 10000
"""

from __future__ import annotations

import argparse
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src.forcefield import write_forcefield

RASPA_DIR = Path.home() / "micromamba" / "envs" / "raspa"
CIF_DIRS = [
    config.DATA_RAW / "coremof_si_cifs" / "SI" / "CR" / "ASR",
    config.DATA_RAW / "csd_modified" / "CSD-modified" / "cifs" / "CR" / "ASR",
    config.DATA_RAW / "matched_cifs",  # MOSAEC行 structure_id 名で複製したCoRE CIF
]
SIM_ROOT = config.PROJECT_ROOT / "simulations"
CUTOFF = 12.0

GCMC_TEMPLATE = """SimulationType                MonteCarlo
NumberOfCycles                {prod_cycles}
NumberOfInitializationCycles  {init_cycles}
PrintEvery                    {print_every}
RestartFile                   no

Forcefield                    UFFPool
RemoveAtomNumberCodeFromLabel yes
UseChargesFromCIFFile         yes
CutOff                        {cutoff}
ChargeMethod                  Ewald
EwaldPrecision                1e-6

Framework 0
FrameworkName {name}
UnitCells {na} {nb} {nc}
HeliumVoidFraction {void_fraction}
ExternalTemperature {temperature}
ExternalPressure {pressure}

Component 0 MoleculeName             CO2
            MoleculeDefinition       ExampleDefinitions
            MolFraction              {y_co2}
            TranslationProbability   0.5
            RotationProbability      0.5
            ReinsertionProbability   0.5
            IdentityChangeProbability 1.0
              NumberOfIdentityChanges 2
              IdentityChangesList     0 1
            SwapProbability          1.0
            CreateNumberOfMolecules  0

Component 1 MoleculeName             N2
            MoleculeDefinition       ExampleDefinitions
            MolFraction              {y_n2}
            TranslationProbability   0.5
            RotationProbability      0.5
            ReinsertionProbability   0.5
            IdentityChangeProbability 1.0
              NumberOfIdentityChanges 2
              IdentityChangesList     0 1
            SwapProbability          1.0
            CreateNumberOfMolecules  0
"""


def find_cif(structure_id: str) -> Path:
    for d in CIF_DIRS:
        p = d / f"{structure_id}.cif"
        if p.exists():
            return p
    raise FileNotFoundError(structure_id)


def cell_from_cif(cif: Path) -> dict:
    text = cif.read_text()
    def grab(key):
        m = re.search(rf"{key}\s+([0-9.]+)", text)
        return float(m.group(1))
    return {
        "a": grab("_cell_length_a"), "b": grab("_cell_length_b"),
        "c": grab("_cell_length_c"), "alpha": grab("_cell_angle_alpha"),
        "beta": grab("_cell_angle_beta"), "gamma": grab("_cell_angle_gamma"),
    }


def replication(cell: dict, cutoff: float = CUTOFF) -> tuple[int, int, int]:
    """垂直幅が 2*cutoff 以上になる最小のスーパーセルを返す。"""
    a, b, c = cell["a"], cell["b"], cell["c"]
    al, be, ga = (math.radians(cell[k]) for k in ("alpha", "beta", "gamma"))
    # 格子ベクトル
    va = (a, 0.0, 0.0)
    vb = (b * math.cos(ga), b * math.sin(ga), 0.0)
    cx = c * math.cos(be)
    cy = c * (math.cos(al) - math.cos(be) * math.cos(ga)) / math.sin(ga)
    cz = math.sqrt(max(c * c - cx * cx - cy * cy, 1e-12))
    vc = (cx, cy, cz)

    def cross(u, v):
        return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0])

    def norm(u):
        return math.sqrt(sum(x * x for x in u))

    vol = abs(sum(va[i] * cross(vb, vc)[i] for i in range(3)))
    widths = (vol / norm(cross(vb, vc)), vol / norm(cross(vc, va)),
              vol / norm(cross(va, vb)))
    return tuple(max(1, math.ceil(2 * cutoff / w)) for w in widths)


def install_forcefield() -> None:
    """生成した力場を RASPA の探索パスに配置する。"""
    src = write_forcefield()
    dest = RASPA_DIR / "share" / "raspa" / "forcefield" / "UFFPool"
    dest.mkdir(parents=True, exist_ok=True)
    for f in src.iterdir():
        (dest / f.name).write_text(f.read_text())


def run_gcmc(
    structure_id: str,
    prod_cycles: int = 10000,
    init_cycles: int = 5000,
    temperature: float = 298.0,
    pressure: float = 1.0e5,
    y_co2: float = 0.15,
    label: str = "pilot",
) -> dict:
    cif = find_cif(structure_id)
    cell = cell_from_cif(cif)
    na, nb, nc = replication(cell)

    job = SIM_ROOT / label / structure_id
    job.mkdir(parents=True, exist_ok=True)
    (job / f"{structure_id}.cif").write_text(cif.read_text())
    (job / "simulation.input").write_text(
        GCMC_TEMPLATE.format(
            prod_cycles=prod_cycles, init_cycles=init_cycles,
            print_every=max(1000, prod_cycles // 5), cutoff=CUTOFF,
            name=structure_id, na=na, nb=nb, nc=nc, void_fraction=0.0,
            temperature=temperature, pressure=pressure,
            y_co2=y_co2, y_n2=1.0 - y_co2,
        )
    )
    env = dict(os.environ, RASPA_DIR=str(RASPA_DIR))
    t0 = time.time()
    subprocess.run([str(RASPA_DIR / "bin" / "simulate"), "simulation.input"],
                   cwd=job, env=env, check=True, capture_output=True)
    wall = time.time() - t0
    return parse_output(job) | {"wall_s": round(wall, 1), "cells": (na, nb, nc)}


def parse_output(job: Path) -> dict:
    data = next((job / "Output" / "System_0").glob("*.data")).read_text()
    res: dict = {}
    # 最終結果の "Number of molecules:" セクション以降だけを対象にする
    tail = data.split("Number of molecules:")[-1]
    for m in re.finditer(
        r"Component \d \[(\w+)\].*?"
        r"Average loading absolute \[mol/kg framework\]\s+([-\d.]+) \+/-\s+([-\d.]+)",
        tail, re.S,
    ):
        name = m.group(1).lower()
        res[f"{name}_mol_kg"] = float(m.group(2))
        res[f"{name}_err"] = float(m.group(3))
    m = re.search(r"Total enthalpy of adsorption\s*\n\s*-+\s*\n.*?"
                  r"([-\d.]+)\s+\+/-\s+([-\d.]+)\s+\[KJ/MOL\]", data, re.S)
    if m:
        res["h_ads_kj_mol"] = float(m.group(1))
    res["n_warnings"] = len(re.findall(r"WARNING", data))
    return res


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["pilot"])
    p.add_argument("structure_id")
    p.add_argument("--cycles", type=int, default=10000)
    p.add_argument("--temperature", type=float, default=298.0)
    args = p.parse_args()

    install_forcefield()
    out = run_gcmc(args.structure_id, prod_cycles=args.cycles,
                   init_cycles=args.cycles // 2, temperature=args.temperature)
    print(out)
