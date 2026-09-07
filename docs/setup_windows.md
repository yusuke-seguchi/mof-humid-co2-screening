# Windows環境での再現手順

作成: 2026-09-07。対象: Windows 10 (21H2以降) / Windows 11。

## 結論: WSL2（Windows上のUbuntu）を使う

GCMC/Widom計算に使う **RASPA2 と Zeo++ には Windowsネイティブ版（conda-forge win-64）が
存在しない**ことを確認済み（2026-09時点）。そのため:

| 部分 | Windowsネイティブ | WSL2 (Ubuntu) |
|---|---|---|
| データ取得・母集団構築・ML・可視化（Python） | ⭕ 動く | ⭕ 動く |
| Widom / GCMC（RASPA2） | ❌ 不可 | ⭕ 動く |
| pptx変換（Docker + Marp） | ⭕ 動く | ⭕ 動く |

**推奨: 全工程をWSL2側で統一する**（パスの混在トラブルを避けるため）。

---

## 1. WSL2のセットアップ（初回のみ、~10分）

管理者PowerShellで:

```powershell
wsl --install -d Ubuntu-24.04
```

再起動後、Ubuntuのユーザー名/パスワードを設定。以降の作業はすべて**Ubuntuターミナル内**で行う。

メモリ割当を増やす場合（GCMC 6並列なら8GB以上推奨）、Windows側の `%UserProfile%\.wslconfig` に:

```ini
[wsl2]
memory=12GB
processors=8
```

## 2. 必要パッケージ（Ubuntu内）

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git curl unzip fonts-noto-cjk
```

`fonts-noto-cjk` は**図の日本語表示に必須**（入れないと文字化けする。
インストール後 `rm -rf ~/.cache/matplotlib` でフォントキャッシュを再構築）。

## 3. リポジトリとPython環境

```bash
git clone https://github.com/yusuke-seguchi/mof-humid-co2-screening.git
cd mof-humid-co2-screening
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**注意: リポジトリは必ずWSL2側のファイルシステム（`~/` 以下）に置く。**
`/mnt/c/...`（Windows側ドライブ）に置くとファイルI/Oが数倍〜数十倍遅くなり、
GCMCバッチの実行時間に直結する。

## 4. RASPA環境（micromamba経由）

```bash
curl -L micro.mamba.pm/install.sh | bash   # micromambaインストール（プロンプトに従う）
source ~/.bashrc
micromamba create -n raspa -c conda-forge raspa2 zeopp-lsmo
```

`src/simulate.py` は `~/micromamba/envs/raspa` を自動参照する（`RASPA_DIR` 定数）。
micromambaのルートを変えた場合はこの定数を修正すること。

動作確認:

```bash
~/micromamba/envs/raspa/bin/simulate -v   # "RASPA 2.0.x" が出ればOK
```

## 5. データ取得

```bash
python -m src.download
```

手動取得分（CCDC無料登録が必要）は README.md の手順どおり。Windowsブラウザで
ダウンロードした場合、WSL2からは `/mnt/c/Users/<名前>/Downloads/CSD-modified.zip`
に見えるので、`cp` でリポジトリ直下へコピーして展開する。

## 6. パイプライン実行

README.md の「4. パイプライン実行」と同一（WSL2内はLinuxなので差分なし）。

```bash
python -m src.pool && python -m src.widom_batch   # 以降READMEどおり
```

- 並列数はCPUコア数に合わせ `src/*_batch.py` の `N_WORKERS` を調整
  （WSL2は `.wslconfig` の `processors` が上限になる）
- 長時間バッチ中にWindowsをスリープさせない（設定 > 電源）。
  WSL2はホストがスリープすると計算も止まる

## 7. pptx変換（任意）

Docker Desktop for Windows をインストールし、Settings > Resources > **WSL integration で
Ubuntu-24.04 を有効化**。あとはREADMEのmarpコマンドがそのまま動く。

## トラブルシューティング

| 症状 | 対処 |
|---|---|
| 図の日本語が「□□□」になる | `sudo apt install fonts-noto-cjk` → `rm -rf ~/.cache/matplotlib` |
| GCMCが異常に遅い | リポジトリが `/mnt/c` 下にないか確認（→ `~/` へ移動） |
| `git push` が "remote end hung up" | 大きいpushで発生しやすい。`git config http.postBuffer 157286400` の上でコミットを分割してpush |
| micromambaコマンドが見つからない | `source ~/.bashrc` または新しいターミナルを開く |
| WSL2のメモリ不足でバッチが落ちる | `.wslconfig` で `memory=` を増やしWindows再起動 |

## ネイティブWindowsで動く範囲（参考）

RASPA不要の工程（`src/download.py` / `src/pool.py` / `src/model.py` / 可視化系）は
ネイティブPython（3.11+）でも動作する。ただし本プロジェクトの検証はmacOS/Linuxのみで
実施しているため、フル再現はWSL2を推奨する。
