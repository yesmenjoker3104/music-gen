# AGENTS.md

このリポジトリは、ACE-Step と HTTP で連携する音楽生成デスクトップ UI（Gradio）向けローカル Python MVP を扱います。

## コアスタック

- `requirements.txt` で管理する Python アプリケーション
- Gradio UI のエントリポイント: `python app.py`
- アプリ本体パッケージ: `src/music_gen_app/`
- 音楽生成バックエンド: 別プロセスで起動した ACE-Step サーバーへの HTTP 連携（`gradio_client` 経由）

## エージェント向け作業ルール

- ACE-Step の HTTP クライアントは `src/music_gen_app/acestep_client.py`、UI の制御は `src/music_gen_app/ui.py` に分離して保つこと。
- 接続先 ACE-Step サーバーの URL と API エンドポイント名は `config.py` の `AppSettings` で管理し、環境変数 `ACESTEP_ENDPOINT` / `ACESTEP_API_NAME` で上書き可能にすること。
- ちょっとした編集や構文確認でモデルのダウンロードや ACE-Step の起動が走らないよう、`gradio_client.Client()` の呼び出しは `generate()` と `check_connection()` のみに限定すること。
- 編集後の検証はまず最小範囲で行うこと。このリポジトリのコード変更では `python -m compileall app.py src` が最初の軽量チェック。

## アーキテクチャ

```
[music-gen Gradio UI :7860]
        │
        ├── gradio_client (HTTP) ──▶ [ACE-Step サーバー :7861]  → 音楽生成 (WAV)
        └── gradio_client (HTTP) ──▶ [AudioGen サーバー :7862]  → 効果音生成 (WAV)
```

music-gen は各サーバーの起動・停止を管理しない。それぞれ別プロセスで起動しておく。

## 環境構築

### 前提

- Python 3.10 以上（3.12 推奨）
- GPU を持つマシンで ACE-Step を実行すること（Intel 内蔵グラフィックスでは実用速度が出ない）
- music-gen UI 自体は軽量なので CPU マシンでも動く

### music-gen UI のセットアップ（軽量側）

```powershell
py -3.12 -m venv C:\venvs\musicgen-ui
C:\venvs\musicgen-ui\Scripts\python.exe -m pip install --upgrade pip
C:\venvs\musicgen-ui\Scripts\python.exe -m pip install -r requirements.txt
```

### ACE-Step サーバーのセットアップ（GPU マシン側）

GPU 環境（NVIDIA GPU 搭載マシン / クラウド GPU）で実行：

```powershell
# Python 3.10-3.12 の venv を作成
py -3.12 -m venv C:\venvs\acestep
C:\venvs\acestep\Scripts\python.exe -m pip install --upgrade pip

# PyTorch（CUDA 版）をインストール
C:\venvs\acestep\Scripts\python.exe -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# triton（Windows GPU 最適化）
C:\venvs\acestep\Scripts\python.exe -m pip install triton-windows

# ACE-Step をインストール（PyPI の acestep 0.1.0 は sdist が壊れているため GitHub から）
$env:PYTHONUTF8='1'
C:\venvs\acestep\Scripts\python.exe -m pip install "git+https://github.com/ace-step/ACE-Step.git"

# ACE-Step は Gradio 5.x が必要
C:\venvs\acestep\Scripts\python.exe -m pip install "gradio==5.23.3"
```

### ACE-Step サーバーの起動

```powershell
$env:PYTHONUTF8='1'
C:\venvs\acestep\Scripts\acestep.exe --port 7861 --server_name 127.0.0.1 --cpu_offload true --overlapped_decode true --torch_compile false --bf16 true
```

Turing 世代（GTX 16 / 20 系）では `--bf16 false` と `$env:ACE_PIPELINE_DTYPE='float32'` を指定する（`float16` は出力が壊れるため不可）。Windows の初回モデル取得・torchcodec の注意点は README のトラブルシューティングを参照。

### AudioGen サーバーのセットアップ（GPU マシン側）

```powershell
py -3.11 -m venv C:\venvs\audiogen
C:\venvs\audiogen\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
C:\venvs\audiogen\Scripts\python.exe -m pip install --only-binary=:all: "av==18.1.0"
C:\venvs\audiogen\Scripts\python.exe -m pip install "torch==2.1.0" "torchaudio==2.1.0" --index-url https://download.pytorch.org/whl/cu121
C:\venvs\audiogen\Scripts\python.exe -m pip install "gradio>=5.38,<6.0" "numpy<2"
C:\venvs\audiogen\Scripts\python.exe -m pip install --no-deps --force-reinstall "audiocraft==1.3.0"
```

### AudioGen サーバーの起動

```powershell
C:\venvs\audiogen\Scripts\python.exe audiogen_server.py --port 7862
```

初回はモデルのダウンロードが走る（audiogen-medium で約 2 GB）。

### music-gen UI の起動

```powershell
cd D:\dev\music-gen
C:\venvs\musicgen-ui\Scripts\python.exe app.py
```

ブラウザで `http://127.0.0.1:7860` にアクセス。

## ACE-Step API エンドポイントの確認方法

デフォルトの `ACESTEP_API_NAME` は `/__call__`（ACE-Step 0.2.0 の text2music 関数）。実際の名前が異なる場合は：

1. `http://127.0.0.1:7861/info` にアクセスしてエンドポイント一覧を確認
2. または `gradio_client` を使って確認：
   ```python
   from gradio_client import Client
   c = Client("http://127.0.0.1:7861")
   c.view_api()
   ```
3. 環境変数で上書き: `ACESTEP_API_NAME=/実際の名前`

## 環境変数

| 変数名 | 既定値 | 説明 |
|---|---|---|
| `ACESTEP_ENDPOINT` | `http://127.0.0.1:7861` | ACE-Step サーバーの URL |
| `ACESTEP_API_NAME` | `/__call__` | ACE-Step Gradio の API 関数名 |
| `AUDIOGEN_ENDPOINT` | `http://127.0.0.1:7862` | AudioGen サーバーの URL |
| `AUDIOGEN_API_NAME` | `/generate_sound` | AudioGen Gradio の API 関数名 |
| `OUTPUT_DIR` | `generated` | 生成ファイルの保存先 |
| `APP_HOST` | `127.0.0.1` | music-gen UI のバインドアドレス |
| `APP_PORT` | `7860` | music-gen UI のポート |
| `APP_SHARE` | `false` | Gradio 共有リンクの有効化 |

## メンテナンス

- ACE-Step の API パラメータや出力形式が変わったら `acestep_client.py` を更新すること。
- AudioGen の API パラメータや出力形式が変わったら `audiogen_client.py` と `audiogen_server.py` を更新すること。
- サーバーのエンドポイント確認手順やデフォルト値が変わったらこのファイルを更新すること。
