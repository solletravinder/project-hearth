"""OCR using TrOCR base-printed model."""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TROCRService:
    """OCR service using TrOCR. Falls back to mock if unavailable."""

    def __init__(self):
        self._model = None
        self._processor = None

    async def load(self):
        try:
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel  # type: ignore
            self._processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-printed")
            self._model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-printed")
            logger.info("TrOCR model loaded successfully")
        except ImportError:
            logger.warning("transformers not installed; using mock OCR")
        except Exception as e:
            logger.warning(f"Failed to load TrOCR: {e}; using mock OCR")

    async def ocr(self, image_path: str) -> str:
        if self._model is None:
            await self.load()
        if self._model is not None:
            try:
                from PIL import Image  # type: ignore
                image = Image.open(image_path).convert("RGB")
                pixel_values = self._processor(images=image, return_tensors="pt").pixel_values
                generated_ids = self._model.generate(pixel_values)
                text = self._processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                return text
            except Exception as e:
                logger.error(f"OCR failed: {e}; falling back to mock")
        return f"[Mock OCR output for {Path(image_path).name}]"


trocr_service = TROCRService()
