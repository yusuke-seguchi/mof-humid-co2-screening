# 技術報告の図版と根拠

作成日：2026-09-05。報告書：docs/mof_screening_report.md。

## 文献図

| ローカル画像 | 出典 | 図番号 | 利用条件・変更 |
|---|---|---|---|
| moosavi2020_fig2.png | Moosavi et al., Nature Communications 11, 4068 (2020), https://doi.org/10.1038/s41467-020-17755-8 | Fig. 2 | CC BY 4.0。全図転載。表示サイズのみ変更 |
| prisma2024_fig1.png | Charalambous et al., Nature 632, 89–94 (2024), https://doi.org/10.1038/s41586-024-07683-8 | Fig. 1 | CC BY 4.0。全図転載。表示サイズのみ変更 |
| moosavi2020_fig3.png | Moosavi et al., Nature Communications 11, 4068 (2020), https://doi.org/10.1038/s41467-020-17755-8 | Fig. 3 | CC BY 4.0。全図転載。表示サイズのみ変更 |
| prisma2024_fig2.png | Charalambous et al., Nature 632, 89–94 (2024), https://doi.org/10.1038/s41586-024-07683-8 | Fig. 2 | CC BY 4.0。全図転載。表示サイズのみ変更 |
| prisma2024_fig3.png | Charalambous et al., Nature 632, 89–94 (2024), https://doi.org/10.1038/s41586-024-07683-8 | Fig. 3 | CC BY 4.0。全図転載。表示サイズのみ変更 |

本文・見出しはユーザー指定のMeiryo。ローカルPowerPoint付属のmeiryo.ttc/meiryob.ttcを変換コンテナへ読み取り専用でマウントし、フォント本体を成果物には再配布しない。文献図と既存計算図に含まれる文字は画像内の元フォントを維持する。

ライセンス：https://creativecommons.org/licenses/by/4.0/
両論文のRights and permissionsおよび図キャプションを確認。著者への帰属とDOIを各スライドにも表示。

原画像：
- https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41467-020-17755-8/MediaObjects/41467_2020_17755_Fig2_HTML.png
- https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41586-024-07683-8/MediaObjects/41586_2024_7683_Fig1_HTML.png

## 計算図

| 図 | 元データ | 生成コード |
|---|---|---|
| pilot_parity.png | data/processed/pilot_batch_results.csv（図用pilot_plot_data.csvも保存） | docs/report_assets/build_report_figures.py |
| discussion.png | data/processed/pilot_batch_enriched.csv（図用discussion_plot_data.csvも保存。点は各構造、黒横線は平均） | docs/report_assets/build_report_figures.py |
| initialization_trace.png | simulations/pilot_batch/*/Output/System_0/*.data（図用initialization_plot_data.csvも保存。本計算を含む） | docs/report_assets/build_report_figures.py |
| fig13_snapshot.png | simulations/movie/2014[Eu][esg]3[ASR]1/Movies/System_0/ のPDBと対応CIF | src/report_process.py |
| fig16_density.png | simulations/density/2014[Eu][esg]3[ASR]1/VTK/System_0/DensityProfile_CO2.vtk | src/report_density.py |

## 本資料での解釈の修正

- GCMCは計算であり実測ではない。警告ゼロと物理的妥当性・収束を同一視しない。
- n=20の層化サンプルの相関から、全母集団やML一般について断定しない。
- 初期ローダの欠損・特徴量不足・計算条件差もML誤差の候補原因。
- 元素Tierは耐水性保証ではない。アミン/OMSフラグは化学吸着の確定診断ではない。
- KH classのnone/unknownを親水性の証拠として使用しない。
- 密度図は相対投影。濃淡だけからサイトの原子種・機構・骨格占有を決めない。
- 並列ジョブのwall_s合計をCPU時間と呼ばない。
- Widomは途中結果。完了・最終候補選定を主張しない。

大学アカウントの有無だけではデータ利用条件は確定しない。構造データの再配布・用途は各配布元の条件を確認する。本報告にはCIFデータ一式を埋め込んでいない。
