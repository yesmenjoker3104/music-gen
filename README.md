# ACE-Step Music Gen

ACE-Step HTTP サーバーと連携する、チャット形式の音楽生成デスクトップ UI です。スタイルタグと歌詞（構造タグ付き）から音楽を生成します。

## ディレクトリ構成

```text
music-gen/
├─ app.py
├─ requirements.txt
├─ README.md
├─ AGENTS.md
└─ src/
   └─ music_gen_app/
      ├─ __init__.py
      ├─ config.py
      ├─ acestep_client.py
      └─ ui.py
```

## 前提

- Windows 11 / PowerShell 想定
- Python 3.10 以上（3.12 推奨）
- **GPU を持つ別マシンまたはクラウド GPU** で ACE-Step サーバーを起動しておく必要があります
  - Intel 内蔵グラフィックス（UHD 620 等）では ACE-Step の実用速度が出ません
  - music-gen UI 自体は軽量なので CPU マシンで動かせます

## セットアップ

### 1. ACE-Step サーバーの準備（GPU マシン）

NVIDIA GPU を持つマシンで ACE-Step をセットアップします：

```powershell
py -3.12 -m venv C:\venvs\acestep
C:\venvs\acestep\Scripts\python.exe -m pip install --upgrade pip
C:\venvs\acestep\Scripts\python.exe -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
C:\venvs\acestep\Scripts\python.exe -m pip install triton-windows
# PyPI の acestep 0.1.0 はsdist が壊れているため GitHub から入れる（cp932 環境では PYTHONUTF8=1 が必要）
$env:PYTHONUTF8='1'
C:\venvs\acestep\Scripts\python.exe -m pip install "git+https://github.com/ace-step/ACE-Step.git"
# ACE-Step は Gradio 5.x が必要（6.x では起動時に失敗する）
C:\venvs\acestep\Scripts\python.exe -m pip install "gradio==5.23.3"
```

ACE-Step サーバーの起動（初回はモデルのダウンロードが走ります）：

```powershell
$env:PYTHONUTF8='1'
C:\venvs\acestep\Scripts\acestep.exe --port 7861 --server_name 127.0.0.1 --cpu_offload true --overlapped_decode true --torch_compile false --bf16 true
```

GTX 16 / 20 系（Turing）の GPU では bf16 の畳み込みが動かないため、`--bf16 false` と `$env:ACE_PIPELINE_DTYPE='float32'` を指定してください。`float16` にすると出力が全サンプル同じ値に張り付き、ノイズのような音になるため使わないでください。

### 2. music-gen UI のセットアップ

```powershell
py -3.12 -m venv C:\venvs\musicgen-ui
C:\venvs\musicgen-ui\Scripts\python.exe -m pip install --upgrade pip
C:\venvs\musicgen-ui\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. music-gen UI の起動

```powershell
cd D:\dev\music-gen
C:\venvs\musicgen-ui\Scripts\python.exe app.py
```

ブラウザで `http://127.0.0.1:7860` にアクセス。

## 使い方

1. ACE-Step サーバーが起動していることを確認（UI 上部に ✅ が表示される）
2. **スタイルタグ** を入力する（例: `pop, piano, female vocal, upbeat`）
3. **歌詞** を入力する（省略可）。`[verse]`、`[chorus]`、`[outro]` などの構造タグを使うと精度が上がります
4. **長さ** を選ぶ（「自動」で ACE-Step に任せる）
5. `Generate` を押す
6. 生成結果をその場で再生し、ファイルとして保存する

## 歌詞の構造タグ例

```
[verse]
Hello, the world is bright today
Every step along the way

[chorus]
La la la, music fills the air
Melodies beyond compare

[outro]
Slowly fade away...
```

## 環境変数

| 変数名 | 既定値 | 説明 |
|---|---|---|
| `ACESTEP_ENDPOINT` | `http://127.0.0.1:7861` | ACE-Step サーバーの URL |
| `ACESTEP_API_NAME` | `/__call__` | ACE-Step Gradio の API 関数名 |
| `OUTPUT_DIR` | `generated` | 生成ファイルの保存先 |
| `APP_HOST` | `127.0.0.1` | UI のバインドアドレス |
| `APP_PORT` | `7860` | UI のポート |
| `APP_SHARE` | `false` | Gradio 共有リンクの有効化 |

## トラブルシューティング

### UI 上部に ❌ が表示される

ACE-Step サーバーが起動していないか、接続できない状態です：
- ACE-Step サーバーが起動しているか確認する
- `ACESTEP_ENDPOINT` が正しいか確認する（リモート GPU の場合は IP アドレスを変更）
- ファイアウォールでポート 7861 が開いているか確認する

### `API名 '/__call__' が正しいか確認してください` エラー

ACE-Step 側の処理で失敗した場合も同じメッセージが出ます。まず ACE-Step のコンソールログを確認してください。

ACE-Step のバージョンによってエンドポイント名が異なる場合があります：

```python
from gradio_client import Client
c = Client("http://127.0.0.1:7861")
c.view_api()  # 利用可能な API 名が表示される
```

確認した名前を `ACESTEP_API_NAME` 環境変数で指定してください。

### Windows での ACE-Step 初回起動の注意

- **`[WinError 1314]`（シンボリックリンク権限がない）**: Hugging Face キャッシュがシンボリックリンクを作ろうとして失敗します。Windows の開発者モードを有効にするか、`huggingface_hub.snapshot_download(..., local_dir=...)` でモデルを取得し、`acestep` に `--checkpoint_path <そのフォルダ>` を渡してください。
- **`Could not load libtorchcodec`**: WAV 保存に使う torchcodec が FFmpeg の共有 DLL（`avutil-*.dll` など）を必要とします。`ffmpeg.exe` だけの静的ビルドでは足りないため、共有ビルドの `bin` を PATH に通してください。

### `gradio-client が未インストールです`

```powershell
C:\venvs\musicgen-ui\Scripts\python.exe -m pip install gradio-client
```
