import asyncio
import edge_tts
from typing import Optional

VOICE_MAP = {
    "Spanish": ("es-ES", "es-ES-ElviraNeural"),
    "French": ("fr-FR", "fr-FR-DeniseNeural"),
    "Japanese": ("ja-JP", "ja-JP-NanamiNeural"),
    "Mandarin Chinese": ("zh-CN", "zh-CN-XiaoxiaoNeural"),
    "German": ("de-DE", "de-DE-KatjaNeural"),
    "Italian": ("it-IT", "it-IT-ElisabettaNeural"),
    "English": ("en-US", "en-US-AriaNeural"),
}

async def _synthesize_async(voice: str, text: str, output_path: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path

def synthesize_text(target_language: str, text: str, output_path: str = "assistant_output.mp3") -> Optional[str]:
    if not text.strip():
        return None
    lang_code_voice = VOICE_MAP.get(target_language)
    if not lang_code_voice:
        lang_code_voice = VOICE_MAP.get("English")
    voice = lang_code_voice[1]
    try:
        asyncio.run(_synthesize_async(voice, text, output_path))
        return output_path
    except Exception:
        return None
