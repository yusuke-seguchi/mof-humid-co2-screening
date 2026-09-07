# 図と元データの対応表

すべての図は再現可能。各行の「元データ」を pandas 等で読めば自分で再可視化できます。
新しい図には左下に元データパスを直接記載しています（古い図も再生成時に順次記載）。

| 図 | 内容 | 元データ | 生成スクリプト |
|---|---|---|---|
| fig1_funnel.png | Stage 0 ファネル | `data/processed/pool_stats.json` | `src/report_pool.py` |
| fig2_descriptors.png | 記述子分布（DB全体 vs 母集団） | `data/raw/mosaec_db.csv`, `data/processed/pool.parquet` | `src/report_pool.py` |
| fig3_composition.png | 母集団の金属/Tier/水安定性根拠 | `data/processed/pool.parquet` | `src/report_pool.py` |
| fig4_domain_shift.png | 教師(BW-DB) vs 母集団の分布 | `data/raw/bwdb_all_MOFs_screening_data.csv`, `data/processed/pool.parquet` | `src/report_pool.py` |
| fig5_parity.png | ML OOF parity（3ターゲット） | `data/processed/oof_*.parquet`, `data/processed/stage1_metrics.json` | `src/report_stage1.py` |
| fig6_calibration.png | 特徴量重要度＋Keskin校正 | `data/processed/stage1_metrics.json`, `stage1_ranking.parquet`, `data/raw/keskin2018_co2n2_selectivity.xlsx` | `src/report_stage1.py` |
| fig7_pareto.png | Stage 1 選抜マップ | `data/processed/stage1_ranking.parquet` | `src/report_stage1.py` |
| fig8_ml_vs_gcmc.png | パイロット: ML vs GCMC | `data/processed/pilot_batch_results.csv` | `src/report_pilot.py` |
| fig9_timing.png | パイロット: 実行時間と外挿 | `data/processed/pilot_batch_results.csv` | `src/report_pilot.py` |
| fig10_widom.png | Widom Henry係数（途中経過） | `data/processed/widom_results.csv`, `stage1_ranking.parquet` | `src/report_process.py` |
| fig11_convergence.png | GCMC収束トレース | `simulations/pilot_batch/<構造ID>/Output/System_0/*.data` | `src/report_process.py` |
| fig12_structures.png | 代表構造ギャラリー | `data/raw/coremof_si_cifs/SI/CR/ASR/<構造ID>.cif` | `src/report_process.py` |
| fig13_snapshot.png | 吸着CO₂スナップショット | `simulations/movie/<構造ID>/Movies/System_0/*.pdb` ＋ 同CIF | `src/report_process.py` |
| fig14_why_top.png | 上位MOFの要因分析（予備） | `data/processed/pilot_batch_enriched.csv` | `src/report_insight.py` |
| fig15_widom_insight.png | Henry上位10%の共通記述子 | `data/processed/widom_results.csv` | `src/report_insight.py` |
| fig16_density.png | CO₂吸着密度マップ | `simulations/density/<構造ID>/VTK/System_0/DensityProfile*.vtk` | `src/report_density.py` |
| viewer_<構造ID>.html | 対話的3Dビュー（ブラウザ用） | 同上のCIF＋動画PDB | `src/viewer3d.py` |

## 主要データファイルのスキーマ要点

- `data/processed/pool.parquet` — Track 1 母集団（1行=1構造）。`metals` はカンマ区切り文字列、`tier` A/B/C、`water_evidence` は判定根拠（ws24_experimental / coremof_ml / metal_heuristic）
- `data/processed/stage1_ranking.parquet` — 上記＋ML予測列（`pred_*`）、`pareto_shell`、`stage1_selected`
- `data/processed/pilot_batch_results.csv` — GCMC実測（`co2_mol_kg`, `n2_mol_kg`, `wall_s`, `n_warnings`）＋対応するML予測列
- `data/processed/widom_results.csv` — Henry係数（`kh_co2_mol_kg_pa`, `kh_n2_mol_kg_pa`）。選択性は比を取る
- RASPA生出力はすべて `simulations/<バッチ名>/<構造ID>/Output/System_0/*.data`（テキスト、grep可能）
