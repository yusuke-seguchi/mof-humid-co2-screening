"""Stage 2 本番: 混合GCMC（CO₂:N₂=15:85, 1 bar, 298 K）を投入リスト全件に実行。

サイクルはパイロットの半分（init 2500 + prod 5000）。パイロットのブロック誤差が
十分小さかったこと、および Widom 5k/20k 検証（誤差1%）を根拠とする。
結果は data/processed/gcmc_results.csv に追記（再実行時は完了分をスキップ）。

    python -u -m src.gcmc_batch
"""

from __future__ import annotations

import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src.simulate import install_forcefield, run_gcmc

N_WORKERS = 6
PROD_CYCLES = 5000
INIT_CYCLES = 2500


def main() -> None:
    install_forcefield()
    targets_df = pd.read_csv(config.DATA_PROCESSED / "stage2_targets.csv")
    # Henry係数の高い順（=有望順）に処理し、途中中断でも上位から埋まるようにする
    targets = targets_df.sort_values("kh_co2_mol_kg_pa", ascending=False)[
        "structure_id"].tolist()

    done_csv = config.DATA_PROCESSED / "gcmc_results.csv"
    done = set()
    if done_csv.exists():
        done = set(pd.read_csv(done_csv)["structure_id"])
    targets = [t for t in targets if t not in done]
    print(f"gcmc targets: {len(targets)} (skipped done: {len(done)})")

    results: list[dict] = []

    def flush() -> None:
        if not results:
            return
        pd.DataFrame(results).to_csv(done_csv, mode="a",
                                     header=not done_csv.exists(), index=False)
        results.clear()

    def one(sid: str) -> dict:
        try:
            r = run_gcmc(sid, prod_cycles=PROD_CYCLES, init_cycles=INIT_CYCLES,
                         label="stage2")
            return {"structure_id": sid, "status": "ok", **r}
        except Exception as e:  # noqa: BLE001
            return {"structure_id": sid, "status": f"error: {e}",
                    "trace": traceback.format_exc()[-200:]}

    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futures = {ex.submit(one, s): s for s in targets}
        for i, fut in enumerate(as_completed(futures), 1):
            r = fut.result()
            results.append(r)
            print(f"[{i}/{len(targets)}] {r['structure_id']}: {r['status']} "
                  f"co2={r.get('co2_mol_kg', float('nan')):.3f} "
                  f"wall={r.get('wall_s', float('nan')):.0f}s", flush=True)
            if len(results) >= 5:
                flush()
    flush()
    print("done ->", done_csv)


if __name__ == "__main__":
    main()
