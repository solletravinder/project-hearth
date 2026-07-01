"""Speech-to-text using faster-whisper."""

import logging
from pathlib import Path

try:
    from faster_whisper import WhisperModel

    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False

from app.config import settings

logger = logging.getLogger(__name__)


class WhisperService:
    """Transcription service using faster-whisper. Falls back to mock if unavailable."""

    def __init__(self):
        self._model = None

    async def load(self):
        if not HAS_WHISPER:
            logger.warning("faster-whisper not installed; using mock transcription")
            return
        try:
            self._model = WhisperModel(
                settings.whisper_model,
                device=settings.device,
                compute_type="int8",
            )
            logger.info(
                "Whisper model loaded: %s (device=%s)",
                settings.whisper_model,
                settings.device,
            )
        except Exception as e:
            logger.warning("Failed to load Whisper model: %s; using mock transcription", e)

    async def transcribe(self, audio_path: str) -> str:
        if self._model is None:
            await self.load()
        if self._model is not None:
            try:
                segments, _ = self._model.transcribe(audio_path, beam_size=5)
                return " ".join([seg.text for seg in segments])
            except Exception as e:
                logger.error("Transcription failed: %s; falling back to mock", e)
        return f"[Mock transcription of {Path(audio_path).name}]"


whisper_service = WhisperService()
