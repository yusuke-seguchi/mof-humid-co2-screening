"""Stage 2（混合GCMC本番）の投入リスト確定。

優先順位の設計（docs/metrics_survey §6 に準拠、MLでなくWidom物理値ベース）:
- ランキング: CO₂ Henry係数（低圧吸着性能の物理的代理指標）
- ゲートは緩く: 極端な親水（KHクラス superweak/none かつ 高water_stability無し）でも
  落とさずフラグのみ（湿潤判定はStage 2→3で行う）
- Tier A は全件投入（水安定性の本命）
- 非物理的に巨大な Henry 係数（> 1 mol/kg/Pa）は「擬化学吸着フラグ」を付け、
  古典力場の適用限界として別枠レビューに回す（Track 1.5）

出力: data/processed/stage2_targets.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config

KH_QUASI_CHEMISORPTION = 1.0  # mol/kg/Pa。これ以上は古典力場の信頼域外とみなす
N_GCMC_TARGET = 300


def main() -> pd.DataFrame:
    w = pd.read_csv(config.DATA_PROCESSED / "widom_results.csv")
    w = w[w["status"].str.startswith("ok") & (w["n_warnings"] == 0)]
    pool = pd.read_parquet(config.DATA_PROCESSED / "stage1_ranking.parquet")
    d = w.merge(pool, on="structure_id", how="left")
    d["s_henry"] = d["kh_co2_mol_kg_pa"] / d["kh_n2_mol_kg_pa"]
    d["quasi_chemisorption"] = d["kh_co2_mol_kg_pa"] > KH_QUASI_CHEMISORPTION

    # 優先度: Henry係数の降順（擬化学吸着は除いた通常域で）
    normal = d[~d["quasi_chemisorption"]].sort_values(
        "kh_co2_mol_kg_pa", ascending=False)
    take = set(normal.head(N_GCMC_TARGET)["structure_id"])
    take |= set(d.loc[d["tier"] == "A", "structure_id"])          # Tier A 全件
    take |= set(d.loc[d["quasi_chemisorption"], "structure_id"])  # 別枠レビュー分も計算はする
    d["stage2_selected"] = d["structure_id"].isin(take)

    out = d[d["stage2_selected"]].sort_values("kh_co2_mol_kg_pa", ascending=False)
    cols = ["structure_id", "refcode", "tier", "kh_co2_mol_kg_pa", "s_henry",
            "quasi_chemisorption", "has_oms", "kh_class", "pld", "lcd", "density",
            "water_evidence"]
    out[cols].to_csv(config.DATA_PROCESSED / "stage2_targets.csv", index=False)

    print(f"widom ok: {len(d)} | stage2 selected: {len(out)}")
    print("  by tier:", out["tier"].value_counts().to_dict())
    print("  quasi-chemisorption flagged:", int(out["quasi_chemisorption"].sum()))
    return out


if __name__ == "__main__":
    main()
