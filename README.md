# 湿潤排ガスCO₂回収向け MOFスクリーニング

公開データベース（12万構造超）から、水安定かつ湿度環境下でCO₂を吸着できるMOF候補を
計算スクリーニングで選定するプロジェクト。

- **全体像・結果**: `docs/mof_screening_internal.md`（社内展開資料）/ `docs/mof_screening_report.md`（技術報告）
- **判断の経緯**: `docs/dev_log.md` ｜ **図↔データ対応**: `docs/figures/README.md`
- 文献サーベイ: `docs/literature_survey_ml_mof_screening.md` / `docs/metrics_survey_mof_screening.md`

## 再現手順

### 1. Python環境

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. データ取得（~700MB。リポジトリにはデータを含まない）

```bash
python -m src.download            # Zenodo / Materials Cloud / Europe PMC から自動取得
```

追加で必要なもの（手動）:

- **CoRE MOF CSD-modified CIFs**: [CCDCダウンロードページ](https://www.ccdc.cam.ac.uk/support-and-resources/downloads/)
  から無料登録後に取得し、`CSD-modified.zip` をリポジトリ直下に配置 → `data/raw/csd_modified/` に展開
  （ライセンス **CC BY-NC-SA 4.0** — 非商用。利用条件は各自確認のこと）
- CoRE MOF SI構造CIF: Zenodo record 15055758 の `CoREMOF2024DB_SI_20250204.zip`
  → `data/raw/coremof_si_cifs/` に展開

### 3. RASPA環境（GCMC/Widom計算）

```bash
brew install micromamba
micromamba create -n raspa -c conda-forge raspa2 zeopp-lsmo
```

### 4. パイプライン実行（順番に）

```bash
python -m src.pool            # Stage 0: 母集団構築 → data/processed/pool.parquet
python -m src.model           # (参考) ML粗選別。本番ではWidomが粗選別を担う
python -m src.widom_batch     # Stage 1: Henry係数計算（~5分/件、6並列）
python -m src.stage2_plan     # Stage 2 投入リスト確定
python -m src.gcmc_batch      # Stage 2: 混合GCMC本番（1-10時間/件）
```

可視化（`docs/figures/` に出力。全図の元データは figures/README.md 参照）:

```bash
python -m src.report_pool     # 母集団の分布
python -m src.report_stage1   # ML検証
python -m src.report_pilot    # パイロットGCMC分析
python -m src.report_process  # 収束・構造・スナップショット
python -m src.report_insight  # 上位要因分析
python -m src.report_density "<構造ID>"   # 吸着密度マップ
python -m src.viewer3d "<構造ID>"          # 対話的3DビューHTML
```

テスト: `python -m pytest tests/`

**Windowsでの再現**: `docs/setup_windows.md` 参照（GCMC部分はWSL2必須）

### 5. 資料のpptx変換（任意）

```bash
cd docs && docker run --rm --init -v "$PWD":/home/marp/app/ marpteam/marp-cli:latest \
  mof_screening_internal.md --pptx --allow-local-files -o mof_screening_internal.pptx
```

## 設計の要点

- 母集団は高価数金属（加水分解耐性）に限定。金属Tier: A=Zr/Hf/Ti/Al/Cr、B=+Fe/Sc/In/Ga、C=+ランタノイド
- **ML粗選別は実験構造で無相関（ρ=0.16）と実測判明 → Widom挿入（ρ=0.87）に転換済み**
- 閾値・条件は `config.py` に一元管理（文献根拠コメント付き）
- 化学吸着系（アミン等）と擬化学吸着域（Henry>1 mol/kg/Pa）は定量予測から分離

## データライセンスの注意

- Zenodo系（CoRE SI・MOSAEC記述子・WS24）とMaterials Cloud（BW-DB）: CC BY 4.0
- CoRE CSD-modified CIF: **CC BY-NC-SA 4.0（非商用）** — リポジトリに同梱しない
- 本リポジトリはデータ本体を含まない（`data/`, `simulations/` はgitignore）
