"""Speech-to-text using faster-whisper."""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class WhisperService:
    """Transcription service using faster-whisper. Falls back to mock if unavailable."""

    def __init__(self):
        self._model = None

    async def load(self):
        try:
            from faster_whisper import WhisperModel  # type: ignore
            self._model = WhisperModel("base", device="cpu", compute_type="int8")
            logger.info("Whisper model loaded successfully")
        except ImportError:
            logger.warning("faster-whisper not installed; using mock transcription")
        except Exception as e:
            logger.warning(f"Failed to load Whisper model: {e}; using mock transcription")

    async def transcribe(self, audio_path: str) -> str:
        if self._model is None:
            await self.load()
        if self._model is not None:
            try:
                segments, _ = self._model.transcribe(audio_path, beam_size=5)
                return " ".join(seg.text for seg in segments)
            except Exception as e:
                logger.error(f"Transcription failed: {e}; falling back to mock")
        return f"[Mock transcription of {Path(audio_path).name}]"


whisper_service = WhisperService()
