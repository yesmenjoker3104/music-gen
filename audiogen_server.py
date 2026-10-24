r"""
AudioGen Gradio server — run this on the GPU machine.

Setup (audiocraft environment):
    py -3.11 -m venv C:\venvs\audiogen
    C:\venvs\audiogen\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
    C:\venvs\audiogen\Scripts\python.exe -m pip install --only-binary=:all: "av==18.1.0"
    C:\venvs\audiogen\Scripts\python.exe -m pip install "torch==2.1.0" "torchaudio==2.1.0" --index-url https://download.pytorch.org/whl/cu121
    C:\venvs\audiogen\Scripts\python.exe -m pip install "gradio>=5.38,<6.0" "numpy<2"
    C:\venvs\audiogen\Scripts\python.exe -m pip install --no-deps --force-reinstall "audiocraft==1.3.0"

Start:
    C:\venvs\audiogen\Scripts\python.exe audiogen_server.py --port 7862
"""

import argparse
import tempfile
from pathlib import Path

import gradio as gr

_model = None
_model_id: str | None = None


def _load_model(model_id: str):
    global _model, _model_id
    if _model is not None and _model_id == model_id:
        return _model
    from audiocraft.models import AudioGen
    _model = AudioGen.get_pretrained(model_id)
    _model_id = model_id
    return _model


def generate_sound(description: str, duration: float, model_id: str) -> str:
    import torchaudio

    description = description.strip()
    if not description:
        raise ValueError("説明を入力してください（例: rain on a rooftop）。")

    model = _load_model(model_id)
    model.set_generation_params(duration=float(duration))
    wav = model.generate([description], progress=False)
    waveform = wav[0].detach().cpu()

    peak = waveform.abs().max().item()
    if peak > 1.0:
        waveform = waveform / peak

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    torchaudio.save(tmp.name, waveform, model.sample_rate)
    return tmp.name


def build_app() -> gr.Blocks:
    with gr.Blocks(title="AudioGen Server") as app:
        gr.Markdown("# AudioGen Server\nテキスト説明から効果音・環境音を生成します。")
        with gr.Row():
            description = gr.Textbox(
                label="説明",
                placeholder="例: rain on a rooftop, thunder in the distance",
                lines=2,
            )
        with gr.Row():
            duration = gr.Slider(1.0, 30.0, value=5.0, step=0.5, label="Duration (seconds)")
            model_id = gr.Dropdown(
                choices=[
                    ("audiogen-medium (推奨)", "facebook/audiogen-medium"),
                    ("audiogen-large", "facebook/audiogen-large"),
                ],
                value="facebook/audiogen-medium",
                label="Model",
            )
        generate_btn = gr.Button("Generate", variant="primary")
        audio_out = gr.Audio(label="Output", type="filepath", interactive=False)

        generate_btn.click(
            fn=generate_sound,
            inputs=[description, duration, model_id],
            outputs=audio_out,
            api_name="generate_sound",
        )

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7862)
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()

    app = build_app()
    app.queue(default_concurrency_limit=1).launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
    )
