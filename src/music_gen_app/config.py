from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(slots=True)
class AppSettings:
    acestep_endpoint: str
    acestep_api_name: str
    audiogen_endpoint: str
    audiogen_api_name: str
    output_dir: Path
    host: str
    port: int
    share: bool

    @classmethod
    def from_env(cls) -> "AppSettings":
        output_dir = Path(os.getenv("OUTPUT_DIR", "generated")).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        port_str = os.getenv("APP_PORT") or os.getenv("GRADIO_SERVER_PORT") or "7860"
        return cls(
            acestep_endpoint=os.getenv("ACESTEP_ENDPOINT", "http://127.0.0.1:7861"),
            acestep_api_name=os.getenv("ACESTEP_API_NAME", "/__call__"),
            audiogen_endpoint=os.getenv("AUDIOGEN_ENDPOINT", "http://127.0.0.1:7862"),
            audiogen_api_name=os.getenv("AUDIOGEN_API_NAME", "/generate_sound"),
            output_dir=output_dir,
            host=os.getenv("APP_HOST", "127.0.0.1"),
            port=int(port_str),
            share=os.getenv("APP_SHARE", "false").lower() in {"1", "true", "yes"},
        )
