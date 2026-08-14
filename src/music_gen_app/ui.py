from pathlib import Path
from typing import Any

import gradio as gr

from .config import AppSettings
from .musicgen_service import GenerationRequest, MusicGenService


MODEL_CHOICES = [
    ("facebook/musicgen-melody", "facebook/musicgen-melody"),
    ("facebook/musicgen-small", "facebook/musicgen-small"),
    ("facebook/musicgen-medium", "facebook/musicgen-medium"),
]


def build_demo(settings: AppSettings) -> gr.Blocks:
    service = MusicGenService(settings)

    with gr.Blocks(title="MusicGen Chat MVP") as demo:
        history_state = gr.State([])

        gr.Markdown(
            "# MusicGen Chat MVP\n"
            "テキストのみの生成と、参照音声を使ったメロディー条件付け生成を試せます。"
        )

        chatbot = gr.Chatbot(label="Session", type="messages", height=480)

        with gr.Row():
            with gr.Column(scale=3):
                prompt = gr.Textbox(
                    label="Prompt",
                    placeholder="例: cinematic piano with warm strings and gentle percussion",
                    lines=4,
                )
                reference_audio = gr.Audio(
                    sources=["upload"],
                    type="filepath",
                    label="Reference audio (optional)",
                )
            with gr.Column(scale=2):
                model_id = gr.Dropdown(
                    choices=MODEL_CHOICES,
                    value=settings.default_model,
                    label="Model",
                )
                duration = gr.Slider(4, 600, value=12, step=1, label="Duration (seconds)")
                temperature = gr.Slider(0.1, 2.0, value=1.0, step=0.1, label="Temperature")
                top_k = gr.Slider(0, 500, value=250, step=1, label="Top-k")
                top_p = gr.Slider(0.0, 1.0, value=0.0, step=0.05, label="Top-p")
                cfg_coef = gr.Slider(1.0, 6.0, value=3.0, step=0.1, label="CFG")

        with gr.Row():
            generate_button = gr.Button("Generate", variant="primary")
            clear_button = gr.Button("Clear")

        with gr.Row():
            generated_audio = gr.Audio(label="Generated audio", interactive=False)
            download_file = gr.File(label="Download")

        status = gr.Markdown(
            f"Ready. Device: **{service.device}**. Output directory: **{settings.output_dir}**"
        )

        generate_button.click(
            fn=lambda history, text, audio_path, chosen_model, seconds, temp, chosen_top_k, chosen_top_p, chosen_cfg: _generate_reply(
                service=service,
                history=history,
                prompt=text,
                reference_audio_path=audio_path,
                model_id=chosen_model,
                duration=seconds,
                temperature=temp,
                top_k=chosen_top_k,
                top_p=chosen_top_p,
                cfg_coef=chosen_cfg,
            ),
            inputs=[
                history_state,
                prompt,
                reference_audio,
                model_id,
                duration,
                temperature,
                top_k,
                top_p,
                cfg_coef,
            ],
            outputs=[history_state, chatbot, generated_audio, download_file, status],
        )

        clear_button.click(
            fn=lambda: ([], [], None, None, "会話をクリアしました。"),
            outputs=[history_state, chatbot, generated_audio, download_file, status],
        )

    return demo


def _generate_reply(
    service: MusicGenService,
    history: list[dict[str, Any]],
    prompt: str,
    reference_audio_path: str | None,
    model_id: str,
    duration: int,
    temperature: float,
    top_k: int,
    top_p: float,
    cfg_coef: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str | None, str | None, str]:
    session = list(history or [])
    user_prompt = prompt.strip()
    if not user_prompt and reference_audio_path:
        user_prompt = "instrumental arrangement that follows the uploaded melody"

    user_message = user_prompt or "No prompt"
    if reference_audio_path:
        user_message += f"\n\nAttached audio: {Path(reference_audio_path).name}"
    session.append({"role": "user", "content": user_message})

    try:
        result = service.generate(
            GenerationRequest(
                prompt=user_prompt,
                model_id=model_id,
                duration=int(duration),
                temperature=float(temperature),
                top_k=int(top_k),
                top_p=float(top_p),
                cfg_coef=float(cfg_coef),
                reference_audio_path=reference_audio_path,
            )
        )
        assistant_message = (
            "生成が完了しました。\n\n"
            f"- model: {result.model_id}\n"
            f"- mode: {'text+melody' if result.used_reference_audio else 'text-only'}\n"
            f"- saved: {result.output_path.name}"
        )
        session.append({"role": "assistant", "content": assistant_message})
        status = f"Saved to {result.output_path}"
        output_path = str(result.output_path)
        return session, session, output_path, output_path, status
    except Exception as exc:  # pragma: no cover - depends on local runtime
        session.append({"role": "assistant", "content": f"生成に失敗しました。\n\n{exc}"})
        return session, session, None, None, f"Error: {exc}"
