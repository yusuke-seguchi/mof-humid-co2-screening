---
marp: false
---

# ML-Based MOF Screening & Selection for CO2 Capture — Literature Survey

対象パイプライン: 高価数金属の実験MOF母集団 → 仮想MOF GCMCデータ（BW-DB / hMOF）で学習したMLによる粗ランキング → 最終候補への自前GCMC → 湿潤排ガスCO₂回収。
調査日: 2026-09-03（Web照合済み。DOI未確認のものは出版社URLを記載）

---

## 1. 基礎: ML+GCMC スクリーニングファネル（「MLで粗選別→シミュレーションで確定」の系譜）

- **Wilmer, Leaf, Lee, Farha, Hauser, Hupp, Snurr — *Nat. Chem.* 2012** — 組合せ生成＋GCMCで仮想MOF 137k（hMOF）を構築。後のML事前スクリーニングのデータ基盤。 — [10.1038/nchem.1192](https://doi.org/10.1038/nchem.1192)
- **Fernandez, Boyd, Daff, Aghaji, Woo — *J. Phys. Chem. Lett.* 2014** — AP-RDF記述子によるQSPR/ML分類器で、DBの一部評価のみでCO₂回収トップ1000のうち~945を回収。「ML事前選別→GCMC」パターンを確立した論文。 — [10.1021/jz501331m](https://doi.org/10.1021/jz501331m)
- **Chung, Gómez-Gualdrón, Li, Leperi, Deria, Snurr et al. — *Sci. Adv.* 2016** — 遺伝的アルゴリズムで~55k MOFから燃焼前CO₂回収候補を探索、トップ候補を実験検証。 — [10.1126/sciadv.1600909](https://doi.org/10.1126/sciadv.1600909)
- **Bucior, Bobbitt, Islamoglu, Goswami, Gopalan, Farha, Snurr et al. — *Mol. Syst. Des. Eng.* 2019** — エネルギーヒストグラム記述子＋LASSO/NNをGCMCの安価な代理モデルとして定式化。 — [10.1039/C8ME00050F](https://doi.org/10.1039/C8ME00050F)
- **Boyd, Chidambaram, García-Díez, Ireland, Daff, Bounds, Woo, Smit et al. — *Nature* 2019** — BW-DB（~325k）構築、寄生エネルギーで湿潤排ガス向けGCMCスクリーニング、アドソルバフォア抽出、Al-PMOF合成・実証。データ駆動設計→実験の旗艦例。 — [10.1038/s41586-019-1798-7](https://doi.org/10.1038/s41586-019-1798-7)
- **Dureckova, Krykunov, Aghaji, Woo — *J. Phys. Chem. C* 2019** — BW-DBでGBM QSPR、CO₂作業容量・CO₂/H₂選択性を予測（R²≈0.94）。 — [10.1021/acs.jpcc.8b10644](https://doi.org/10.1021/acs.jpcc.8b10644)
- **Burner, Schwiedrzik, Krykunov, Luo, Boyd, Woo — *J. Phys. Chem. C* 2020** — BW-DBで低圧（0.15 bar）CO₂作業容量・CO₂/N₂選択性の深層学習回帰（R²≈0.95-0.96）。 — [ACS](https://pubs.acs.org/jpccck/article-abstract/124/51/27996/1437837/High-Performing-Deep-Learning-Regression-Models)
- **Kancharlapalli, Snurr — *ACS Appl. Mater. Interfaces* 2023** — CoRE-MOF-2019を湿潤排ガス向けに多段選別: 幾何フィルタ→ML→力場相互作用エネルギー→DFT→2・3成分GCMC（CO₂/N₂/H₂O）。本パイプラインに最も近い公開テンプレート。 — [10.1021/acsami.3c04079](https://doi.org/10.1021/acsami.3c04079)
- **Kwon, Gibaldi, Pai, Rajendran, Woo — *ACS Cent. Sci.* 2025** — 実験MOF ~56kを湿潤排ガス向けにPVSAプロセスシミュレーションまで通して選定。 — [ACS](https://pubs.acs.org/acscii/article/11/8/1438/3758023/Identification-of-Metal-Organic-Frameworks-for)

## 2. CO₂吸着予測のMLモデル

**記述子ベース（RF/GBM）:**
- Fernandez 2014 / Dureckova 2019 / Burner 2020（上記）がCO₂の定番（AP-RDF＋幾何＋化学モチーフ特徴量）。
- **Yuan, Suvarna, Lourenço, Pérez-Ramírez et al. — *Commun. Chem.* 2023** — 幾何記述子が効かない低分圧域（DAC域）向けの新記述子。 — [10.1038/s42004-023-01009-x](https://www.nature.com/articles/s42004-023-01009-x)

**深層学習 / Transformer / GNN:**
- **Xie, Grossman — *Phys. Rev. Lett.* 2018** — CGCNN。MOF系GNNの親アーキテクチャ。 — [10.1103/PhysRevLett.120.145301](https://doi.org/10.1103/PhysRevLett.120.145301)
- **Choudhary et al. — *Comput. Mater. Sci.* 2022** — hMOFでの構造直入力GNN（ALIGNN系）CO₂吸着予測。 — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S092702562200163X)
- **Cao, Magar, Wang, Barati Farimani — *JACS* 2023 (MOFormer)** — MOFid文字列の自己教師ありTransformer。結晶構造不要の物性予測。 — [10.1021/jacs.2c11420](https://doi.org/10.1021/jacs.2c11420)
- **Park, Kang, Kim — *Nat. Mach. Intell.* 2023 (MOFTransformer)** — 原子グラフ＋エネルギーグリッドのマルチモーダル事前学習。MOF物性の汎用転移学習。 — [10.1038/s42256-023-00628-2](https://doi.org/10.1038/s42256-023-00628-2) / [GitHub](https://github.com/hspark1212/MOFTransformer)
- **Park, Kim — *ACS Appl. Mater. Interfaces* 2023 (PMTransformer)** — 190万多孔質材料で事前学習、材料クラス横断のfew-shot学習。 — [ACS](https://pubs.acs.org/aamick/article-abstract/15/48/56375/309043/Enhancing-Structure-Property-Relationships-in)
- **Wang et al. — *Nat. Commun.* 2024 (Uni-MOF)** — ガス種・温度・圧力を入力に取る3D事前学習Transformer。多ガス等温線を横断予測。 — [10.1038/s41467-024-46276-x](https://doi.org/10.1038/s41467-024-46276-x)
- **Sriram et al. (Meta FAIR/Georgia Tech) — *ACS Cent. Sci.* 2024 (ODAC23)** — 8,400 MOFでのCO₂/H₂O DFT計算38M点＋DFT精度に迫るMLP。古典力場を超えるラベル源。アミン化学吸着も明示的にカバー。 — [10.1021/acscentsci.3c01629](https://doi.org/10.1021/acscentsci.3c01629)
- **Lim, Park, Walsh, Kim — *Matter* 2025** — 汎用MLFFをCO₂/H₂O吸着にファインチューニング（GoldDAC＋DAC-SIM）。8,000+ MOFを走査し古典力場が見逃した100件超を発見。 — [Cell/Matter](https://www.cell.com/matter/abstract/S2590-2385(25)00246-2)
- **MOFSimBench — arXiv 2025** — 汎用機械学習ポテンシャル（MACE, CHGNet, EquiformerV2等）のMOFモデリング性能ベンチマーク。uMLIP採用前に必読。 — [arXiv:2507.11806](https://arxiv.org/abs/2507.11806)
- **MOFGPT — arXiv 2025** — LLM/生成基盤モデル路線の代表（RL調整の生成言語モデル）。 — [arXiv:2506.00198](https://arxiv.org/pdf/2506.00198)

## 3. データベース間の転移性・ドメインシフト（本プロジェクトの核心的懸念）

- **Moosavi, Nandy, Jablonka, Ongari, Janet, Boyd, Lee, Smit, Kulik — *Nat. Commun.* 2020** — 各MOF DBの化学的多様性を定量化。仮想DB（hMOF, BW-DB, ToBaCCo）はCoREと部分的に重ならない偏った化学空間を占めることを実証。hMOF学習モデルが実験MOFで劣化する根拠。 — [10.1038/s41467-020-17755-8](https://doi.org/10.1038/s41467-020-17755-8)
- **Majumdar, Moosavi, Jablonka, Ongari, Smit — *ACS Appl. Mater. Interfaces* 2021** — 学習DBを多様化して汎化性能を上げる方法論。 — [10.1021/acsami.1c16220](https://pubs.acs.org/doi/10.1021/acsami.1c16220)
- **Ma, Colón et al. — *ACS Appl. Mater. Interfaces* 2020** — ガス種・条件を跨ぐ転移学習の初期研究。事前学習NN特徴量はゼロから学習より転移に強い。 — [10.1021/acsami.0c06858](https://pubs.acs.org/doi/abs/10.1021/acsami.0c06858)
- **Park, Kim — *ACS Appl. Mater. Interfaces* 2023** — 仮想DB事前学習Transformerを実験（CoRE）構造数百件でファインチューニングすると精度回復。hMOF→実験構造シフトへの実践的レシピ。 — [ACS](https://pubs.acs.org/aamick/article-abstract/15/48/56375/309043/Enhancing-Structure-Property-Relationships-in)
- **教師なしドメイン適応（仮想→実験、CH₄吸着） — *Sep. Purif. Technol.* 2024** — hMOF→実験データのドメイン適応問題を明示的に研究。 — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1383586623021998)
- **Jablonka, Rosen, Krishnapriyan, Smit — *ACS Cent. Sci.* 2023 (mofdscribe)** — DB間の重複構造によるデータリーケージとテスト指標の水増しを実証。リーク安全なsplitとベンチマークを提供。ML精度報告前の必読方法論。 — [10.1021/acscentsci.2c01177](https://doi.org/10.1021/acscentsci.2c01177)
- **Jin, Moubarak, Li, Jablonka, Smit et al. — *Digital Discovery* 2025 (MOFChecker)** — 重複検出・エラー検証。CoRE-2014の~38%に重大エラーと報告。 — [RSC](https://pubs.rsc.org/dd/article/4/6/1560/889033/MOFChecker-a-package-for-validating-and-correcting)
- **Zhao, Chung et al. — *Matter* 2025 (CoRE MOF DB)** — ML物性付きの再整備実験MOF DB。現時点で最もクリーンな実験構造源。 — [Cell/Matter](https://www.cell.com/matter/abstract/S2590-2385(25)00183-3)
- **Sarikas et al. — *J. Chem. Inf. Model.* 2026 (RetNeXt)** — hMOF 320万吸着点で事前学習したマルチタスクCNNをUO/ToBaCCoに転移。エネルギーボクセル入力はDB間転移に強く、幾何・点群入力はドメインシフトに弱いことを示す。ラベル必要量を最大100分の1に削減。 — [10.1021/acs.jcim.5c02698](https://doi.org/10.1021/acs.jcim.5c02698)
- **Generalizable and Transferable ML for gas separations — *Environ. Sci. Technol.* 2026** — 実運用でのDB横断評価。 — [ACS](https://pubs.acs.org/esthag/article-abstract/60/27/19347/5177933/Generalizable-and-Transferable-Machine-Learning)
- **物理吸着ラベルの限界（化学吸着）:** ODAC23（上記）はアミン含有MOFの化学吸着が古典力場GCMCで表現不能なことを記録。**Kumar et al. — *ACS Nano* 2023**はMg-MOF-74のOMSでのCO₂化学吸着に量子情報MLFFを構築（[10.1021/acsnano.2c11102](https://pubs.acs.org/doi/10.1021/acsnano.2c11102)）、**ReaxFF/メタダイナミクス（アミンMOF） — *J. Phys. Chem. C* 2024**（[10.1021/acs.jpcc.3c07183](https://pubs.acs.org/doi/10.1021/acs.jpcc.3c07183)）はGCMCが見逃す部分を明示。実務的含意: hMOF/BW-DBラベルは物理吸着限定。OMS/アミン系化学吸着体はMLランキングから除外するか、DFT/MLPレベルで別途扱うこと。

## 4. 水安定性・湿潤CO₂スクリーニングの先行研究

- **Li, Chung, Snurr — *Langmuir* 2016** — 水共存下CO₂回収の初期階層GCMCスクリーニング。H₂O競合がほとんどの物理吸着体を無力化することを示す。 — [10.1021/acs.langmuir.6b02803](https://pubs.acs.org/doi/10.1021/acs.langmuir.6b02803)
- **Nandy, Duan, Kulik — *JACS* 2021** — 文献マイニング→水/熱安定性ML分類器。 — [10.1021/jacs.1c07217](https://doi.org/10.1021/jacs.1c07217)
- **Nandy et al. — *Sci. Data* 2022 (MOFSimplify)** — ~3,000 MOFの安定性データセット＋Webツール公開。 — [10.1038/s41597-022-01181-0](https://doi.org/10.1038/s41597-022-01181-0)
- **Terrones, Huang, Rivera, Kulik et al. — *JACS* 2024 (WS24)** — 実験ラベル+911件（>400%増）。水・酸安定性ROC-AUC >0.8。 — [10.1021/jacs.4c05879](https://doi.org/10.1021/jacs.4c05879)
- **Zhang, Palakkal, Wu, Jiang, Jiang — *Environ. Sci. Technol.* 2025** — ML安定性モデル（水/熱/活性化）＋GCMCでARC-MOF ~28万構造から超安定湿潤CO₂回収MOFを選定。「耐水性×CO₂性能」複合ランキングの最直接の先例。 — [10.1021/acs.est.5c00768](https://pubs.acs.org/doi/10.1021/acs.est.5c00768)
- **Hydrostable fluorinated MOFs, multiscale screening — *Chem & Bio Engineering* 2024** — 加水分解耐性化学に絞った湿潤排ガススクリーニング。 — [10.1021/cbe.4c00111](https://pubs.acs.org/doi/10.1021/cbe.4c00111)

## 5. レビュー・展望（最初に読む用）

- **Jablonka, Ongari, Moosavi, Smit — *Chem. Rev.* 2020** — 「Big-Data Science in Porous Materials」。手法・記述子・落とし穴の決定版レビュー。 — [10.1021/acs.chemrev.0c00004](https://doi.org/10.1021/acs.chemrev.0c00004)
- **Chong, Lee, Kim — *Coord. Chem. Rev.* 2020** — MOFへのML応用。入門に好適。 — [10.1016/j.ccr.2020.213487](https://doi.org/10.1016/j.ccr.2020.213487)
- **Recent advances in computational modeling of MOFs — *Coord. Chem. Rev.* 2023** — GCMC/DFT実務とML代理モデルの橋渡し。 — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0010854523001017)
- **Kang, Park, Kim et al. — *JACS Au* 2024** — 「From Data to Discovery」。Transformer・基盤モデル・生成設計の最新概観。 — [10.1021/jacsau.4c00618](https://pubs.acs.org/doi/10.1021/jacsau.4c00618)
- **Sung et al. — *Ind. Eng. Chem. Res.* 2025** — ガス吸着の予測記述子に特化した実務的レビュー。特徴量設計に直接有用。 — [10.1021/acs.iecr.4c03500](https://pubs.acs.org/doi/10.1021/acs.iecr.4c03500)
- **日本語文献の注記:** ML×MOF吸着スクリーニングに特化した査読付き日本語レビューは見当たらず（実質的に英語文献のみ）。日本語で読める周辺資料: 旭化成ARCレポート（MOF実用化動向、[PDF](https://arc.asahi-kasei.co.jp/report/arc_report/pdf/RS-1057.pdf)）、岩崎悠真『マテリアルズ・インフォマティクス』（[日刊工業新聞社](https://www.kinokuniya.co.jp/f/dsg-01-9784526079863)）。

## 6. 実験検証まで到達した成功例

- **Boyd et al. — *Nature* 2019** — **Al-PMOF**（＋Al-PyrMOF）: BW-DBからアドソルバフォア解析で選定→合成→湿潤下でもCO₂容量維持を実証。今も基準となる完結ループ。 — [10.1038/s41586-019-1798-7](https://doi.org/10.1038/s41586-019-1798-7)
- **Chung et al. — *Sci. Adv.* 2016** — GA選定トップMOF（NOTT-101/OEt）を合成・測定し予測と一致。 — [10.1126/sciadv.1600909](https://doi.org/10.1126/sciadv.1600909)
- **Moosavi, Chidambaram, Talirz, Smit et al. — *Nat. Commun.* 2019** — MLによる合成条件最適化（HKUST-1）。合成側のデータ駆動検証。 — [10.1038/s41467-019-08483-9](https://doi.org/10.1038/s41467-019-08483-9)
- **Lin et al. — *Science* 2021 (CALF-20)** — シミュレーション支援で発見された耐水・産業スケール排ガスCO₂吸着材。ML選定ではないが、湿潤排ガス候補リストが超えるべき現実のベンチマーク。 — [10.1126/science.abi7281](https://doi.org/10.1126/science.abi7281)
- **Yan, Foster et al. (Argonne) — *Commun. Chem.* 2024 (GHP-MOFassemble)** — 拡散モデル＋CGCNN＋GCMCで12万新規MOFを生成、6千件を上位5%CO₂性能と予測（in-silico検証まで）。 — [arXiv:2306.08695](https://arxiv.org/abs/2306.08695) / [Argonne](https://www.anl.gov/article/argonne-scientists-use-ai-to-identify-new-materials-for-carbon-capture)
- **Zheng, Yaghi et al. — *JACS* 2023** — GPT支援の合成条件テキストマイニング→予測MOFの合成検証。合成ループを閉じる際に関連。 — [10.1021/jacs.3c05819](https://doi.org/10.1021/jacs.3c05819)
- **正直な注記:** 2019年以降、「MLランキング→合成→湿潤CO₂実測」のフルループ例は依然少ない。2023-26年の「検証」の多くはホールドアウト等温線やプロセスモデルに対するもの。自前GCMC＋実験ステージを持つ本パイプラインの設計はこの現状に沿っている。

---

## 推奨リーディング順（最初の5本）

1. **Boyd et al., *Nature* 2019** — 教師データBW-DBの出典・ファネル設計・湿潤排ガス指標・実験検証の姿。
2. **Kancharlapalli & Snurr, *ACS AMI* 2023** — 「実験MOF＋ML＋DFT＋CO₂/N₂/H₂O GCMC」の設計図。
3. **Moosavi et al., *Nat. Commun.* 2020** — 仮想DB学習モデルを実験高価数MOFに使う前に、化学空間バイアスの所在を理解する。
4. **Jablonka et al., *ACS Cent. Sci.* 2023** — リーク安全なtrain/testプロトコル（hMOF/BW-DB/CoRE間の重複対策）。
5. **Burner et al., *JPCC* 2020**（＋Dureckova 2019） — これから作るモデルの実働例（BW-DB学習、低圧CO₂＋CO₂/N₂選択性）。

その後: **WS24 (JACS 2024)**（水安定性ゲート）→ **Kwon et al. (ACS Cent. Sci. 2025)**（プロセスレベル指標）→ **ODAC23 + Lim et al. (Matter 2025)**（物理吸着力場を超える必要が出たとき）。
