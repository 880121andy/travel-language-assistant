from typing import Optional, Dict
from faster_whisper import WhisperModel
import os

class WhisperTranscriber:
    def __init__(self, model_size: str = "small", device: Optional[str] = None, compute_type: str = "int8"):
        # device auto-selection
        self.model_size = model_size
        self.device = device or ("cuda" if os.environ.get("CUDA_PATH") else "cpu")
        self.compute_type = compute_type
        self._model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)

    def transcribe(self, audio_path: str, language_hint: Optional[str] = None) -> Dict[str, str]:
        segments, info = self._model.transcribe(audio_path, language=language_hint, beam_size=5)
        text = " ".join([seg.text.strip() for seg in segments]).strip()
        return {
            "text": text,
            "language": info.language,
            "language_probability": info.language_probability,
        }
