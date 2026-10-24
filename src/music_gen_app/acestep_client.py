from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import shutil

from .config import AppSettings


@dataclass(slots=True)
class GenerationRequest:
    tags: str
    lyrics: str
    duration: float  # seconds; -1 = auto/random
    steps: int = 60
    guidance_scale: float = 7.0
    omega_scale: float = 10.0
    seed: int = -1


@dataclass(slots=True)
class GenerationResult:
    output_path: Path
    tags: str
    duration_requested: float


class ACEStepClient:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def check_connection(self) -> tuple[bool, str]:
        try:
            from gradio_client import Client  # type: ignore[import]
        except ImportError:
            return False, "gradio-client が未インストールです。pip install gradio-client を実行してください。"
        try:
            Client(self.settings.acestep_endpoint, verbose=False)
            return True, f"接続OK: {self.settings.acestep_endpoint}"
        except Exception as exc:
            return False, (
                f"ACE-Step サーバーに接続できません ({self.settings.acestep_endpoint}): {exc}"
            )

    def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            from gradio_client import Client  # type: ignore[import]
        except ImportError:
            raise RuntimeError(
                "gradio-client が未インストールです。pip install gradio-client を実行してください。"
            )

        tags = request.tags.strip()
        if not tags:
            raise ValueError("スタイルタグを入力してください（例: pop, guitar, upbeat）。")

        try:
            client = Client(self.settings.acestep_endpoint, verbose=False)
        except Exception as exc:
            raise RuntimeError(
                f"ACE-Step サーバーに接続できません。\n"
                f"endpoint: {self.settings.acestep_endpoint}\n\n"
                f"ACE-Step が起動しているか確認してください。\n{exc}"
            ) from exc

        seeds = [request.seed] if request.seed >= 0 else []
        try:
            result = client.predict(
                audio_duration=request.duration,
                prompt=tags,
                lyrics=request.lyrics,
                infer_step=request.steps,
                guidance_scale=request.guidance_scale,
                scheduler_type="euler",
                cfg_type="apg",
                omega_scale=request.omega_scale,
                actual_seeds=seeds,
                api_name=self.settings.acestep_api_name,
            )
        except Exception as exc:
            raise RuntimeError(
                f"ACE-Step の生成に失敗しました。\n\n"
                f"API名 '{self.settings.acestep_api_name}' が正しいか確認してください。\n"
                f"ACE-Step サーバーの /info でエンドポイント一覧を確認できます。\n\n{exc}"
            ) from exc

        output_path = self._save_result(result)
        return GenerationResult(
            output_path=output_path,
            tags=tags,
            duration_requested=request.duration,
        )

    def _save_result(self, gradio_result) -> Path:
        dest = self.settings.output_dir / self._build_filename()

        # gradio_client audio return types:
        # - str/Path: filepath (most common with Gradio 5 + gradio_client 1.x)
        # - dict {"name": "..."}: older gradio_client format
        # - tuple (sample_rate, np.ndarray): numpy audio mode

        if isinstance(gradio_result, (str, Path)):
            src = Path(str(gradio_result))
            if src.exists():
                shutil.copy2(src, dest)
                return dest

        if isinstance(gradio_result, dict) and "name" in gradio_result:
            src = Path(gradio_result["name"])
            if src.exists():
                shutil.copy2(src, dest)
                return dest

        if isinstance(gradio_result, tuple) and len(gradio_result) == 2:
            sample_rate, audio_data = gradio_result
            try:
                import numpy as np  # type: ignore[import]
                import soundfile as sf  # type: ignore[import]
                audio = np.array(audio_data, dtype=np.float32)
                if audio.ndim == 2:
                    audio = audio.T
                sf.write(str(dest), audio, int(sample_rate))
                return dest
            except ImportError:
                pass

        raise RuntimeError(
            f"ACE-Step から予期しない出力形式を受け取りました: {type(gradio_result)}\n"
            f"ACESTEP_API_NAME ({self.settings.acestep_api_name}) が正しいか確認してください。"
        )

    def _build_filename(self) -> str:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"acestep-{stamp}.wav"
