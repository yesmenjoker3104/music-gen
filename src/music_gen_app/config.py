from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(slots=True)
class AppSettings:
    default_model: str
    output_dir: Path
    host: str
    port: int
    share: bool

    @classmethod
    def from_env(cls) -> "AppSettings":
        project_root = Path(__file__).resolve().parents[2]
        hf_cache_dir = (project_root / ".hf_cache").resolve()
        hf_cache_dir.mkdir(parents=True, exist_ok=True)

        os.environ.setdefault("HF_HOME", str(hf_cache_dir))
        os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(hf_cache_dir / "hub"))
        os.environ.setdefault("HF_HUB_CACHE", str(hf_cache_dir / "hub"))
        os.environ.setdefault("TRANSFORMERS_CACHE", str(hf_cache_dir / "transformers"))

        output_dir = Path(os.getenv("MUSICGEN_OUTPUT_DIR", "generated")).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        port = os.getenv("MUSICGEN_PORT") or os.getenv("GRADIO_SERVER_PORT") or "7860"
        return cls(
            default_model=os.getenv("MUSICGEN_MODEL", "facebook/musicgen-small"),
            output_dir=output_dir,
            host=os.getenv("MUSICGEN_HOST", "127.0.0.1"),
            port=int(port),
            share=os.getenv("MUSICGEN_SHARE", "false").lower() in {"1", "true", "yes"},
        )
