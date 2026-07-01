"""OCR using TrOCR."""

import logging
from pathlib import Path

try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel

    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    from PIL import Image

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from app.config import settings

logger = logging.getLogger(__name__)


class TROCRService:
    """OCR service using TrOCR. Falls back to mock if unavailable."""

    def __init__(self):
        self._model = None
        self._processor = None

    async def load(self):
        if not HAS_TRANSFORMERS:
            logger.warning("transformers not installed; using mock OCR")
            return
        try:
            model_name = settings.trocr_model
            self._processor = TrOCRProcessor.from_pretrained(model_name)
            self._model = VisionEncoderDecoderModel.from_pretrained(model_name)
            logger.info("TrOCR model loaded: %s", model_name)
        except Exception as e:
            logger.warning("Failed to load TrOCR: %s; using mock OCR", e)

    async def ocr(self, image_path: str) -> str:
        if self._model is None:
            await self.load()
        if self._model is not None and self._processor is not None and HAS_PIL:
            try:
                image = Image.open(image_path).convert("RGB")
                pixel_values = self._processor(images=image, return_tensors="pt").pixel_values
                generated_ids = self._model.generate(pixel_values)
                text = self._processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                return text
            except Exception as e:
                logger.error("OCR failed: %s; falling back to mock", e)
        return f"[Mock OCR output for {Path(image_path).name}]"


trocr_service = TROCRService()
