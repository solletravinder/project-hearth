"""PII detection using spaCy NER."""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

PII_PATTERNS = [
    ("EMAIL", r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    ("PHONE", r"\+?1?\d{10,15}"),
    ("SSN", r"\d{3}-\d{2}-\d{4}"),
]


class NERService:
    """PII detection service using spaCy. Falls back to regex-only if unavailable."""

    def __init__(self):
        self._nlp = None

    async def load(self):
        try:
            import spacy  # type: ignore
            self._nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy NER model loaded successfully")
        except ImportError:
            logger.warning("spaCy not installed; using regex-only PII detection")
        except Exception as e:
            logger.warning(f"Failed to load spaCy model: {e}; using regex-only detection")

    async def detect(self, text: str) -> list[dict]:
        """Detect PII in text. Returns list of {type, start, end, text} dicts."""
        results = []
        # Regex patterns first
        for pii_type, pattern in PII_PATTERNS:
            for match in re.finditer(pattern, text):
                results.append({
                    "type": pii_type,
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(),
                })
        # NER-based detection
        if self._nlp is None:
            await self.load()
        if self._nlp is not None:
            try:
                doc = self._nlp(text)
                for ent in doc.ents:
                    if ent.label_ in ("PERSON", "ORG", "GPE", "EMAIL", "PHONE", "SSN"):
                        results.append({
                            "type": ent.label_,
                            "start": ent.start_char,
                            "end": ent.end_char,
                            "text": ent.text,
                        })
            except Exception as e:
                logger.error(f"NER detection failed: {e}")
        return results


ner_service = NERService()
