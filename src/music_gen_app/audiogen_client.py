from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import shutil

from .config import AppSettings


@dataclass(slots=True)
class SoundRequest:
    description: str
    duration: float
    model_id: str = "facebook/audiogen-medium"


@dataclass(slots=True)
class SoundResult:
    output_path: Path
    description: str
    duration: float


class AudioGenClient:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def check_connection(self) -> tuple[bool, str]:
        try:
            from gradio_client import Client  # type: ignore[import]
        except ImportError:
            return False, "gradio-client が未インストールです。pip install gradio-client を実行してください。"
        try:
            Client(self.settings.audiogen_endpoint, verbose=False)
            return True, f"接続OK: {self.settings.audiogen_endpoint}"
        except Exception as exc:
            return False, (
                f"AudioGen サーバーに接続できません ({self.settings.audiogen_endpoint}): {exc}"
            )

    def generate(self, request: SoundRequest) -> SoundResult:
        try:
            from gradio_client import Client  # type: ignore[import]
        except ImportError:
            raise RuntimeError(
                "gradio-client が未インストールです。pip install gradio-client を実行してください。"
            )

        description = request.description.strip()
        if not description:
            raise ValueError("説明を入力してください（例: rain on a rooftop）。")

        try:
            client = Client(self.settings.audiogen_endpoint, verbose=False)
        except Exception as exc:
            raise RuntimeError(
                f"AudioGen サーバーに接続できません。\n"
                f"endpoint: {self.settings.audiogen_endpoint}\n\n"
                f"audiogen_server.py が起動しているか確認してください。\n{exc}"
            ) from exc

        try:
            result = client.predict(
                description=description,
                duration=request.duration,
                model_id=request.model_id,
                api_name=self.settings.audiogen_api_name,
            )
        except Exception as exc:
            raise RuntimeError(
                f"AudioGen の生成に失敗しました。\n\n"
                f"API名 '{self.settings.audiogen_api_name}' が正しいか確認してください。\n"
                f"AudioGen サーバーの /info でエンドポイント一覧を確認できます。\n\n{exc}"
            ) from exc

        output_path = self._save_result(result)
        return SoundResult(
            output_path=output_path,
            description=description,
            duration=request.duration,
        )

    def _save_result(self, gradio_result) -> Path:
        dest = self.settings.output_dir / self._build_filename()

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
            f"AudioGen から予期しない出力形式を受け取りました: {type(gradio_result)}\n"
            f"AUDIOGEN_API_NAME ({self.settings.audiogen_api_name}) が正しいか確認してください。"
        )

    def _build_filename(self) -> str:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"audiogen-{stamp}.wav"
