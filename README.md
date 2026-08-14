# MusicGen Desktop MVP

ローカル環境の Python で動く、チャット形式の音楽生成デスクトップアプリです。MusicGen をバックエンドに使い、テキスト生成と参照音声付きのメロディー条件付け生成を 1 つの UI から試せます。

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
      ├─ musicgen_service.py
      └─ ui.py
```

## 前提

- Windows 11 / PowerShell 想定
- **Python 3.11 必須**（AudioCraft 1.3.0 は Python 3.12 では動作しません）
- GPU 推奨。CPU でも動く可能性はありますが、実用速度はかなり厳しいです
- MP3 を参照音声に使う場合は ffmpeg が必要です。WAV ならトラブルが少なめです

## セットアップ

### 重要: Windows 環境での注意事項

AudioCraft の依存関係である `av` パッケージは、Windows でソースからビルドしようとすると失敗します。以下の手順に従って、**必ず順番通りに**インストールしてください。

### 推奨手順

1. **Python 3.11 の仮想環境を作成**

OneDrive などの同期フォルダを避け、ローカルパスに作成することを推奨：

```powershell
# 例: Astral CPython 3.11.15 を使用
py -V:Astral/CPython3.11.15 -m venv C:\venvs\musicgen311

# または標準の Python 3.11
py -3.11 -m venv C:\venvs\musicgen311

# ビルドツールをアップグレード
C:\venvs\musicgen311\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
```

2. **av パッケージをバイナリでインストール（最優先）**

これを最初に行わないと、後続のインストールでビルドエラーが発生します：

```powershell
C:\venvs\musicgen311\Scripts\python.exe -m pip install --only-binary=:all: "av==18.1.0"
```

3. **PyTorch スタックをインストール**

CPU 版の場合:

```powershell
C:\venvs\musicgen311\Scripts\python.exe -m pip install "torch==2.1.0" "torchaudio==2.1.0" "torchvision==0.16.0" "torchtext==0.16.0" "xformers==0.0.22.post7"
```

CUDA 12.1 の場合:

```powershell
C:\venvs\musicgen311\Scripts\python.exe -m pip install "torch==2.1.0" "torchaudio==2.1.0" "torchvision==0.16.0" "torchtext==0.16.0" --index-url https://download.pytorch.org/whl/cu121
C:\venvs\musicgen311\Scripts\python.exe -m pip install "xformers==0.0.22.post7"
```

4. **アプリ依存関係をインストール**

```powershell
C:\venvs\musicgen311\Scripts\python.exe -m pip install "gradio>=5.38,<6.0" "soundfile>=0.12,<1.0" "hydra-core>=1.1" "hydra_colorlog" "einops" "flashy>=0.0.1" "julius" "num2words" "sentencepiece" "transformers>=4.31.0" "demucs" "librosa" "torchmetrics" "encodec" "protobuf" "spacy>=3.6.1"
```

5. **AudioCraft を依存関係なしでインストール**

古い av 依存を回避するため、`--no-deps` フラグが必須：

```powershell
C:\venvs\musicgen311\Scripts\python.exe -m pip install --no-deps --force-reinstall "audiocraft==1.3.0"
```

6. **NumPy をダウングレード**

PyTorch 2.1.0 は NumPy 2.x と互換性がないため：

```powershell
C:\venvs\musicgen311\Scripts\python.exe -m pip install "numpy<2"
```

7. **動作確認**

```powershell
C:\venvs\musicgen311\Scripts\python.exe -c "from audiocraft.models import MusicGen; print('Setup OK!')"
```

8. **（オプション）ffmpeg のインストール**

MP3 を使いたい場合：

```powershell
winget install Gyan.FFmpeg
```

### 簡易セットアップ（トラブルが発生した場合は推奨手順を使用）

プロジェクトフォルダ内に venv を作成する場合:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install --only-binary=:all: "av==18.1.0"
python -m pip install "torch==2.1.0" "torchaudio==2.1.0" --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
python -m pip install --no-deps --force-reinstall "audiocraft==1.3.0"
python -m pip install "numpy<2"
```

### Python 3.12 について

Python 3.12 を使用すると、`requirements.txt` の環境マーカーにより `audiocraft` がスキップされ、実行時にインポートエラーが発生します。**必ず Python 3.11 を使用してください。**

## 起動

venv をプロジェクト外に作成した場合:

```powershell
cd C:\Users\<username>\Documents\workspace\music-gen
C:\venvs\musicgen311\Scripts\python.exe app.py
```

venv をプロジェクト内に作成した場合:

```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

ブラウザで `http://127.0.0.1:7860` を開くと UI が表示されます。

## トラブルシューティング

### `avformat.lib not found` エラー

av パッケージがソースからビルドされようとしています。セットアップ手順の 2 番（`--only-binary=:all:` フラグ付きインストール）を最優先で実行してください。

### NumPy 互換性エラー

```
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x...
```

PyTorch 2.1.0 は NumPy 1.x を要求します。`python -m pip install "numpy<2"` で解決します。

### AudioCraft がインポートできない

Python 3.12 を使用している可能性があります。`python --version` で確認し、必ず Python 3.11 環境を使用してください。

## 使い方

1. プロンプトを入力する
2. 必要なら参照音声を 1 つアップロードする
3. モデルを選ぶ
4. `Generate` を押す
5. 生成結果をその場で再生し、ファイルとして保存する

## 環境変数

- `MUSICGEN_MODEL`: 既定モデル。既定値は `facebook/musicgen-small`
- `MUSICGEN_OUTPUT_DIR`: 生成ファイルの保存先。既定値は `generated`
- `MUSICGEN_HOST`: Gradio の bind 先。既定値は `127.0.0.1`
- `MUSICGEN_PORT`: Gradio のポート。既定値は `7860`
- `MUSICGEN_SHARE`: `true` で Gradio の共有リンクを有効化

## 注意

- `facebook/musicgen-small` と `facebook/musicgen-medium` はテキスト専用です。参照音声付き生成には `facebook/musicgen-melody` を使ってください。
- 初回起動では Hugging Face からモデルがダウンロードされるため、時間とディスク容量が必要です。既定の `facebook/musicgen-small` は比較的軽く、起動と生成が早めです。
- モデル重みの利用条件は Meta / Hugging Face 側のライセンスに従ってください。
