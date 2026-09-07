"""Widom挿入バッチ: CIF入手済みの全母集団構造に CO2/N2 Henry係数を計算する。

物理ベースの Stage 1 優先順位付け（ML粗選別の代替）。
    python -m src.widom_batch
"""

from __future__ import annotations

import re
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src.simulate import (RASPA_DIR, SIM_ROOT, cell_from_cif, find_cif,
                          install_forcefield, replication, CUTOFF)
import os
import subprocess
import time

N_WORKERS = 6
WIDOM_CYCLES = 5000

WIDOM_TEMPLATE = """SimulationType                MonteCarlo
NumberOfCycles                {cycles}
NumberOfInitializationCycles  0
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
ExternalTemperature {temperature}

Component 0 MoleculeName             CO2
            MoleculeDefinition       ExampleDefinitions
            WidomProbability         1.0
            CreateNumberOfMolecules  0

Component 1 MoleculeName             N2
            MoleculeDefinition       ExampleDefinitions
            WidomProbability         1.0
            CreateNumberOfMolecules  0
"""


def run_widom(structure_id: str, temperature: float = 298.0) -> dict:
    cif = find_cif(structure_id)
    na, nb, nc = replication(cell_from_cif(cif))
    job = SIM_ROOT / "widom" / structure_id
    job.mkdir(parents=True, exist_ok=True)
    (job / f"{structure_id}.cif").write_text(cif.read_text())
    (job / "simulation.input").write_text(WIDOM_TEMPLATE.format(
        cycles=WIDOM_CYCLES, print_every=WIDOM_CYCLES // 4, cutoff=CUTOFF,
        name=structure_id, na=na, nb=nb, nc=nc, temperature=temperature))
    env = dict(os.environ, RASPA_DIR=str(RASPA_DIR))
    t0 = time.time()
    subprocess.run([str(RASPA_DIR / "bin" / "simulate"), "simulation.input"],
                   cwd=job, env=env, check=True, capture_output=True)
    res = parse_widom(job)
    res["wall_s"] = round(time.time() - t0, 1)
    return res


def parse_widom(job: Path) -> dict:
    data = next((job / "Output" / "System_0").glob("*.data")).read_text()
    res: dict = {"n_warnings": len(re.findall(r"WARNING", data))}
    for m in re.finditer(
        r"\[(\w+)\] Average Henry coefficient:\s+([-\d.eE+]+) \+/-\s+([-\d.eE+]+)",
        data,
    ):
        res[f"kh_{m.group(1).lower()}_mol_kg_pa"] = float(m.group(2))
    return res


def main() -> None:
    install_forcefield()
    pool = pd.read_parquet(config.DATA_PROCESSED / "stage1_ranking.parquet")

    def has_cif(sid: str) -> bool:
        try:
            find_cif(sid)
            return True
        except FileNotFoundError:
            return False

    targets = [s for s in pool["structure_id"] if has_cif(s)]
    done_csv = config.DATA_PROCESSED / "widom_results.csv"
    done = set()
    if done_csv.exists():
        done = set(pd.read_csv(done_csv)["structure_id"])
    targets = [t for t in targets if t not in done]
    print(f"widom targets: {len(targets)} (skipped done: {len(done)})")

    results = []

    def flush():
        if not results:
            return
        df = pd.DataFrame(results)
        header = not done_csv.exists()
        df.to_csv(done_csv, mode="a", header=header, index=False)
        results.clear()

    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futures = {ex.submit(_safe, s): s for s in targets}
        for i, fut in enumerate(as_completed(futures), 1):
            r = fut.result()
            results.append(r)
            print(f"[{i}/{len(targets)}] {r['structure_id']}: {r['status']} "
                  f"kh_co2={r.get('kh_co2_mol_kg_pa', float('nan')):.3e} "
                  f"wall={r.get('wall_s', float('nan')):.0f}s", flush=True)
            if len(results) >= 10:
                flush()
    flush()
    print("done ->", done_csv)


def _safe(structure_id: str) -> dict:
    try:
        return {"structure_id": structure_id, "status": "ok", **run_widom(structure_id)}
    except Exception as e:  # noqa: BLE001
        return {"structure_id": structure_id, "status": f"error: {e}",
                "trace": traceback.format_exc()[-200:]}


if __name__ == "__main__":
    main()
