from typing import Any

import gradio as gr

from .config import AppSettings
from .acestep_client import ACEStepClient, GenerationRequest
from .audiogen_client import AudioGenClient, SoundRequest

DURATION_CHOICES = [
    ("自動 (-1)", -1.0),
    ("30秒", 30.0),
    ("1分", 60.0),
    ("1分30秒", 90.0),
    ("2分", 120.0),
    ("3分", 180.0),
    ("4分", 240.0),
    ("5分", 300.0),
]

AUDIOGEN_MODEL_CHOICES = [
    ("audiogen-medium (推奨)", "facebook/audiogen-medium"),
    ("audiogen-large", "facebook/audiogen-large"),
]


def build_demo(settings: AppSettings) -> gr.Blocks:
    music_client = ACEStepClient(settings)
    sound_client = AudioGenClient(settings)

    with gr.Blocks(title="Music & Sound Gen") as demo:
        gr.Markdown("# Music & Sound Gen\nACE-Step（音楽）と AudioGen（効果音）を HTTP で呼び出します。")

        with gr.Tabs():

            # ── Tab 1: 音楽生成 (ACE-Step) ──────────────────────────────────
            with gr.Tab("🎵 音楽生成 (ACE-Step)"):
                music_history = gr.State([])

                conn_ok, conn_msg = music_client.check_connection()
                music_conn = gr.Markdown(f"{'✅' if conn_ok else '❌'} {conn_msg}")

                music_chatbot = gr.Chatbot(label="Session", type="messages", height=300)

                with gr.Row():
                    with gr.Column(scale=3):
                        tags = gr.Textbox(
                            label="スタイルタグ",
                            placeholder="例: pop, piano, female vocal, upbeat, bright",
                            lines=2,
                        )
                        lyrics = gr.Textbox(
                            label="歌詞（構造タグ付き）",
                            placeholder=(
                                "[verse]\nHello, the world is bright today\n\n"
                                "[chorus]\nLa la la, music fills the air\n\n"
                                "[outro]\nFade away..."
                            ),
                            lines=7,
                        )
                    with gr.Column(scale=2):
                        music_duration = gr.Dropdown(
                            choices=DURATION_CHOICES,
                            value=-1.0,
                            label="長さ",
                        )
                        with gr.Accordion("詳細設定", open=False):
                            steps = gr.Slider(20, 150, value=60, step=1, label="ステップ数 (infer_step)")
                            guidance_scale = gr.Slider(1.0, 15.0, value=7.0, step=0.5, label="Guidance Scale")
                            omega_scale = gr.Slider(0.0, 20.0, value=10.0, step=0.5, label="Omega Scale (APG)")
                            seed = gr.Number(value=-1, label="シード (-1 でランダム)", precision=0)

                with gr.Row():
                    music_gen_btn = gr.Button("Generate", variant="primary")
                    music_clear_btn = gr.Button("Clear")
                    music_check_btn = gr.Button("接続確認")

                with gr.Row():
                    music_audio = gr.Audio(label="生成された音楽", interactive=False)
                    music_dl = gr.File(label="ダウンロード")

                music_status = gr.Markdown(f"Ready. 出力先: **{settings.output_dir}**")

                def do_music_generate(history, tags_v, lyrics_v, dur_v, steps_v, guidance_v, omega_v, seed_v):
                    return _music_reply(
                        client=music_client,
                        history=history,
                        tags=tags_v,
                        lyrics=lyrics_v,
                        duration=float(dur_v),
                        steps=int(steps_v),
                        guidance_scale=float(guidance_v),
                        omega_scale=float(omega_v),
                        seed=int(seed_v),
                    )

                def do_music_check():
                    ok, msg = music_client.check_connection()
                    return f"{'✅' if ok else '❌'} {msg}"

                music_gen_btn.click(
                    fn=do_music_generate,
                    inputs=[music_history, tags, lyrics, music_duration, steps, guidance_scale, omega_scale, seed],
                    outputs=[music_history, music_chatbot, music_audio, music_dl, music_status],
                )
                music_clear_btn.click(
                    fn=lambda: ([], [], None, None, "会話をクリアしました。"),
                    outputs=[music_history, music_chatbot, music_audio, music_dl, music_status],
                )
                music_check_btn.click(fn=do_music_check, outputs=music_conn)

            # ── Tab 2: 効果音生成 (AudioGen) ─────────────────────────────────
            with gr.Tab("🔊 効果音生成 (AudioGen)"):
                sound_history = gr.State([])

                sconn_ok, sconn_msg = sound_client.check_connection()
                sound_conn = gr.Markdown(f"{'✅' if sconn_ok else '❌'} {sconn_msg}")

                sound_chatbot = gr.Chatbot(label="Session", type="messages", height=300)

                with gr.Row():
                    with gr.Column(scale=3):
                        sound_desc = gr.Textbox(
                            label="説明",
                            placeholder="例: rain on a rooftop, distant thunder, crowd cheering",
                            lines=3,
                        )
                    with gr.Column(scale=2):
                        sound_duration = gr.Slider(1.0, 30.0, value=5.0, step=0.5, label="Duration (seconds)")
                        sound_model = gr.Dropdown(
                            choices=AUDIOGEN_MODEL_CHOICES,
                            value="facebook/audiogen-medium",
                            label="Model",
                        )

                with gr.Row():
                    sound_gen_btn = gr.Button("Generate", variant="primary")
                    sound_clear_btn = gr.Button("Clear")
                    sound_check_btn = gr.Button("接続確認")

                with gr.Row():
                    sound_audio = gr.Audio(label="生成された効果音", interactive=False)
                    sound_dl = gr.File(label="ダウンロード")

                sound_status = gr.Markdown(f"Ready. 出力先: **{settings.output_dir}**")

                def do_sound_generate(history, desc_v, dur_v, model_v):
                    return _sound_reply(
                        client=sound_client,
                        history=history,
                        description=desc_v,
                        duration=float(dur_v),
                        model_id=model_v,
                    )

                def do_sound_check():
                    ok, msg = sound_client.check_connection()
                    return f"{'✅' if ok else '❌'} {msg}"

                sound_gen_btn.click(
                    fn=do_sound_generate,
                    inputs=[sound_history, sound_desc, sound_duration, sound_model],
                    outputs=[sound_history, sound_chatbot, sound_audio, sound_dl, sound_status],
                )
                sound_clear_btn.click(
                    fn=lambda: ([], [], None, None, "会話をクリアしました。"),
                    outputs=[sound_history, sound_chatbot, sound_audio, sound_dl, sound_status],
                )
                sound_check_btn.click(fn=do_sound_check, outputs=sound_conn)

    return demo


# ── helper functions ─────────────────────────────────────────────────────────

def _music_reply(
    client: ACEStepClient,
    history: list[dict[str, Any]],
    tags: str,
    lyrics: str,
    duration: float,
    steps: int,
    guidance_scale: float,
    omega_scale: float,
    seed: int,
) -> tuple[list, list, str | None, str | None, str]:
    session = list(history or [])
    user_message = tags.strip() or "(タグなし)"
    if lyrics.strip():
        truncated = lyrics.strip()[:200]
        user_message += f"\n\n歌詞:\n{truncated}{'...' if len(lyrics.strip()) > 200 else ''}"
    session.append({"role": "user", "content": user_message})

    try:
        result = client.generate(
            GenerationRequest(
                tags=tags,
                lyrics=lyrics,
                duration=duration,
                steps=steps,
                guidance_scale=guidance_scale,
                omega_scale=omega_scale,
                seed=seed,
            )
        )
        dur_label = "自動" if result.duration_requested < 0 else f"{result.duration_requested:.0f}秒"
        session.append({"role": "assistant", "content": (
            "生成が完了しました。\n\n"
            f"- tags: {result.tags}\n"
            f"- duration: {dur_label}\n"
            f"- saved: {result.output_path.name}"
        )})
        p = str(result.output_path)
        return session, session, p, p, f"Saved to {result.output_path}"
    except Exception as exc:
        session.append({"role": "assistant", "content": f"生成に失敗しました。\n\n{exc}"})
        return session, session, None, None, f"Error: {exc}"


def _sound_reply(
    client: AudioGenClient,
    history: list[dict[str, Any]],
    description: str,
    duration: float,
    model_id: str,
) -> tuple[list, list, str | None, str | None, str]:
    session = list(history or [])
    session.append({"role": "user", "content": description.strip() or "(説明なし)"})

    try:
        result = client.generate(
            SoundRequest(
                description=description,
                duration=duration,
                model_id=model_id,
            )
        )
        session.append({"role": "assistant", "content": (
            "生成が完了しました。\n\n"
            f"- description: {result.description}\n"
            f"- duration: {result.duration:.1f}秒\n"
            f"- saved: {result.output_path.name}"
        )})
        p = str(result.output_path)
        return session, session, p, p, f"Saved to {result.output_path}"
    except Exception as exc:
        session.append({"role": "assistant", "content": f"生成に失敗しました。\n\n{exc}"})
        return session, session, None, None, f"Error: {exc}"
