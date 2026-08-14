from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import torch
import torchaudio

from .config import AppSettings

try:
    from audiocraft.models import MusicGen
except ImportError:  # pragma: no cover - handled at runtime
    MusicGen = None


MELODY_CAPABLE_MODELS = {
    "facebook/musicgen-melody",
    "facebook/musicgen-stereo-melody",
    "facebook/musicgen-melody-large",
}


@dataclass(slots=True)
class GenerationRequest:
    prompt: str
    model_id: str
    duration: int
    temperature: float
    top_k: int
    top_p: float
    cfg_coef: float
    reference_audio_path: Optional[str] = None


@dataclass(slots=True)
class GenerationResult:
    output_path: Path
    sample_rate: int
    model_id: str
    used_reference_audio: bool


class MusicGenService:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self._model = None
        self._model_id: Optional[str] = None
        self._device = self._detect_device()

    @property
    def device(self) -> str:
        return self._device

    def generate(self, request: GenerationRequest) -> GenerationResult:
        prompt = request.prompt.strip()
        if not prompt and request.reference_audio_path:
            prompt = "instrumental arrangement that follows the uploaded melody"
        if not prompt:
            raise ValueError("テキストプロンプトを入力してください。")

        self._ensure_model(request.model_id)
        self._configure_generation(request)

        if request.reference_audio_path:
            self._assert_melody_support(request.model_id)
            melody, sample_rate = torchaudio.load(request.reference_audio_path)
            generated = self._model.generate_with_chroma(
                descriptions=[prompt],
                melody_wavs=melody,
                melody_sample_rate=sample_rate,
                progress=False,
            )
        else:
            generated = self._model.generate([prompt], progress=False)

        waveform = generated[0].detach().cpu()
        output_path = self._save_waveform(waveform, self._model.sample_rate)
        return GenerationResult(
            output_path=output_path,
            sample_rate=self._model.sample_rate,
            model_id=request.model_id,
            used_reference_audio=bool(request.reference_audio_path),
        )

    def _ensure_model(self, model_id: str) -> None:
        if MusicGen is None:
            raise RuntimeError(
                "audiocraft が見つかりません。"
                "Python 3.12 では AudioCraft の依存制約で導入できない場合があります。"
                "MusicGen を使う場合は README の手順で Python 3.11 環境を作成してください。"
            )
        if self._model is not None and self._model_id == model_id:
            return
        self._model = MusicGen.get_pretrained(model_id, device=self.device)
        self._model_id = model_id

    def _configure_generation(self, request: GenerationRequest) -> None:
        self._model.set_generation_params(
            use_sampling=True,
            top_k=request.top_k,
            top_p=request.top_p,
            temperature=request.temperature,
            duration=request.duration,
            cfg_coef=request.cfg_coef,
        )

    def _save_waveform(self, waveform: torch.Tensor, sample_rate: int) -> Path:
        output_path = self.settings.output_dir / self._build_filename()
        normalized = self._normalize_waveform(waveform)
        torchaudio.save(str(output_path), normalized, sample_rate)
        return output_path

    def _build_filename(self) -> str:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"musicgen-{stamp}.wav"

    def _normalize_waveform(self, waveform: torch.Tensor) -> torch.Tensor:
        peak = waveform.abs().max().item()
        if peak > 1.0:
            waveform = waveform / peak
        return waveform.clamp(-1.0, 1.0)

    def _assert_melody_support(self, model_id: str) -> None:
        if model_id not in MELODY_CAPABLE_MODELS:
            raise ValueError(
                "参照音声付き生成には melody 系モデルが必要です。facebook/musicgen-melody を選択してください。"
            )

    def _detect_device(self) -> str:
        return "cuda" if torch.cuda.is_available() else "cpu"
