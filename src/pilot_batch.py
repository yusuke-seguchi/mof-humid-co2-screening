"""Phase 3.2: パイロットバッチ — 層化20構造で実行時間とML予測乖離を実測する。

選定: CIF入手済み(CoRE SI)かつ Stage 1 選抜のうち、Tier と予測吸着量の
分位で層化サンプリング。6並列で混合GCMCを実行し、結果を CSV に集約する。

    python -m src.pilot_batch          # 実行（~1-2時間想定）
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
PROD_CYCLES = 10000
INIT_CYCLES = 5000


def select_pilot(n: int = 20) -> pd.DataFrame:
    pool = pd.read_parquet(config.DATA_PROCESSED / "stage1_ranking.parquet")
    cand = pool[(pool["source"] == "coremof2024_si") & pool["stage1_selected"]].copy()
    picked = []
    for tier, quota in (("A", 6), ("B", 8), ("C", 6)):
        sub = cand[cand["tier"] == tier].sort_values(
            "pred_co2_binary_uptake_0p15bar_298K"
        )
        if len(sub) == 0:
            continue
        # 予測吸着量の分位で均等サンプリング（低い側〜高い側まで網羅）
        idx = [int(round(i * (len(sub) - 1) / max(quota - 1, 1))) for i in range(quota)]
        picked.append(sub.iloc[sorted(set(idx))])
    out = pd.concat(picked).drop_duplicates("structure_id").head(n)
    return out


def run_one(structure_id: str) -> dict:
    try:
        res = run_gcmc(structure_id, prod_cycles=PROD_CYCLES,
                       init_cycles=INIT_CYCLES, label="pilot_batch")
        return {"structure_id": structure_id, "status": "ok", **res}
    except Exception as e:  # noqa: BLE001 — バッチは1件の失敗で止めない
        return {"structure_id": structure_id, "status": f"error: {e}",
                "trace": traceback.format_exc()[-300:]}


def main() -> None:
    install_forcefield()
    pilot = select_pilot()
    print(f"pilot set: {len(pilot)} structures")
    results = []
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futures = {ex.submit(run_one, s): s for s in pilot["structure_id"]}
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            print(f"[{len(results)}/{len(pilot)}] {r['structure_id']}: "
                  f"{r['status']} "
                  f"co2={r.get('co2_mol_kg', float('nan')):.3f} "
                  f"wall={r.get('wall_s', float('nan')):.0f}s")

    res = pd.DataFrame(results).merge(
        pilot[["structure_id", "tier", "pld", "lcd", "has_oms",
               "pred_co2_binary_uptake_0p15bar_298K", "pred_co2_n2_selectivity"]],
        on="structure_id", how="left",
    )
    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    res.to_csv(config.DATA_PROCESSED / "pilot_batch_results.csv", index=False)
    print("saved to data/processed/pilot_batch_results.csv")


if __name__ == "__main__":
    main()
