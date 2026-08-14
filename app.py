from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from music_gen_app.config import AppSettings
from music_gen_app.ui import build_demo


def main() -> None:
    settings = AppSettings.from_env()
    demo = build_demo(settings)
    demo.queue(default_concurrency_limit=1).launch(
        server_name=settings.host,
        server_port=settings.port,
        share=settings.share,
    )


if __name__ == "__main__":
    main()
