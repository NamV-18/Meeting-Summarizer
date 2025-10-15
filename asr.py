import pathlib
from typing import Optional
from openai import OpenAI
from ..config import settings


class ASRService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        # Prefer explicit key; otherwise let SDK resolve from env (OPENAI_API_KEY)
        key = api_key or settings.openai_api_key
        self.client = OpenAI(api_key=key) if key else OpenAI()
        self.model = model or settings.asr_model

    def transcribe_file(self, file_path: str) -> str:
        path = pathlib.Path(file_path)
        # If configured to use local faster-whisper
        if (settings.asr_provider or "openai").lower() == "faster-whisper":
            return self._transcribe_local(path)

        # Default: try OpenAI first, then fallback on quota errors
        try:
            with path.open("rb") as f:
                transcript = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=f,
                    response_format="text",
                )
            return str(transcript)
        except Exception as e:
            # Fallback only on insufficient quota or explicit provider error
            if "insufficient_quota" in str(e) or "You exceeded your current quota" in str(e):
                try:
                    return self._transcribe_local(path)
                except Exception:
                    pass
            raise

    def _transcribe_local(self, path: pathlib.Path) -> str:
        # Lazy import to avoid dependency if not needed
        from faster_whisper import WhisperModel  # type: ignore

        # Use a lightweight model to reduce download/compute
        model = WhisperModel("small", device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(path), beam_size=1)
        text_parts = [seg.text for seg in segments]
        return " ".join(part.strip() for part in text_parts if part)


