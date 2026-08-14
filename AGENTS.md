# AGENTS.md

このリポジトリは、AudioCraft 経由で Meta MusicGen を利用する、チャット形式の音楽生成デスクトップ UI（Gradio）向けローカル Python MVP を扱います。

## コアスタック

- `requirements.txt` で管理する Python アプリケーション
- Gradio UI のエントリポイント: `python app.py`
- アプリ本体パッケージ: `src/music_gen_app/`
- 音楽生成バックエンド: `audiocraft.models.MusicGen`

## エージェント向け作業ルール

- MusicGen のラッパー処理は `src/music_gen_app/musicgen_service.py`、UI の制御は `src/music_gen_app/ui.py` に分離して保つこと。
- テキストのみ生成とメロディー条件付け生成の両方を維持すること。メロディー入力には `musicgen-melody` 系モデルが必要。
- ちょっとした編集や構文確認でモデル重みのダウンロードが走らないよう、遅延ロードを優先すること。
- 編集後の検証はまず最小範囲で行うこと。このリポジトリのコード変更では `python -m compileall app.py src` が最初の軽量チェック。

## 環境構築（重要）

### Python バージョン要件

**Python 3.11 が必須です。** Python 3.12 では `requirements.txt` の `audiocraft>=1.3,<2.0; python_version < "3.12"` マーカーにより audiocraft がスキップされ、実行時にインポートエラーが発生します。

### 推奨セットアップ手順（Windows）

#### 1. Python 3.11 環境の作成

OneDrive などの同期フォルダ配下だと Windows App Control でブロックされる可能性があるため、ローカルパス推奨：

```powershell
# Astral CPython 3.11.15 を使用する例
py -V:Astral/CPython3.11.15 -m venv C:\venvs\musicgen311clean

# 環境変数として設定
$venv = "C:\venvs\musicgen311clean\Scripts\python.exe"

# ビルドツールのアップグレード
& $venv -m pip install --upgrade pip setuptools wheel
```

#### 2. av パッケージのバイナリインストール（最優先）

AudioCraft 1.3.0 は古い `av==11.0.0` を要求しますが、これは Windows でソースビルド時に `avformat.lib not found` エラーで失敗します。先にバイナリ版の新しい av をインストールすることで回避：

```powershell
& $venv -m pip install --only-binary=:all: "av==18.1.0"
```

#### 3. PyTorch スタックのインストール

AudioCraft が要求する PyTorch 2.1.0 系をインストール：

```powershell
# CPU版の例
& $venv -m pip install "torch==2.1.0" "torchaudio==2.1.0" "torchvision==0.16.0" "torchtext==0.16.0" "xformers==0.0.22.post7"

# CUDA版を使う場合は --index-url オプションを追加
# & $venv -m pip install "torch==2.1.0" "torchaudio==2.1.0" --index-url https://download.pytorch.org/whl/cu121
```

#### 4. アプリ依存関係のインストール

```powershell
& $venv -m pip install "gradio>=5.38,<6.0" "soundfile>=0.12,<1.0" "hydra-core>=1.1" "hydra_colorlog" "einops" "flashy>=0.0.1" "julius" "num2words" "sentencepiece" "transformers>=4.31.0" "demucs" "librosa" "torchmetrics" "encodec" "protobuf" "spacy>=3.6.1"
```

#### 5. AudioCraft のインストール（依存関係スキップ）

古い av 依存を回避するため、`--no-deps` フラグ必須：

```powershell
& $venv -m pip install --no-deps --force-reinstall "audiocraft==1.3.0"
```

#### 6. NumPy のダウングレード

PyTorch 2.1.0 は NumPy 2.x と互換性がないため、1.x にダウングレード：

```powershell
& $venv -m pip install "numpy<2"
```

#### 7. 動作確認

```powershell
& $venv -c "from audiocraft.models import MusicGen; print('OK')"
```

### 起動コマンド

```powershell
cd C:\Users\<username>\Documents\workspace\music-gen
& C:\venvs\musicgen311clean\Scripts\python.exe app.py
```

ブラウザで `http://127.0.0.1:7860` にアクセス。

## トラブルシューティング

### `avformat.lib not found` エラー

av パッケージがソースからビルドされようとしている場合に発生。手順 2 の `--only-binary=:all:` フラグ付きインストールを最優先で実行すること。

### `numpy 2.x` 互換性エラー

PyTorch 2.1.0 は NumPy 1.x を要求。`pip install "numpy<2"` で解決。

### `audiocraft` がインポートできない

Python 3.12 を使用している可能性。`python --version` で確認し、必ず Python 3.11 環境を使うこと。

## 環境メモ

- ユーザー環境は Windows + PowerShell 前提。
- 同期フォルダ配下の仮想環境が実行ポリシーや App Control でブロックされる場合は、`C:\venvs\` など非同期パスに作成すること。
- `audiocraft` は重量級で、実用的な推論には通常 GPU が必要。構造確認のための CPU 実行は可だが、遅さは明示すること。
- MP3 取り扱いにはシステム `ffmpeg` が必要な場合がある。Windows では WAV が最も安全な検証入力。

## メンテナンス

- パッケージ構成、起動コマンド、モデル選択肢が変わったらこのファイルを更新すること。