from __future__ import annotations

import re
from typing import List, Optional, Tuple


def redact_patterns(text: str) -> Tuple[str, List[dict]]:
    """Redact common PII patterns (email, phone, SSN) using regex.

    Returns (redacted_text, detections) where detections is a list of
    dicts with keys: pattern_type, original, start, end.
    """
    detections: List[dict] = []

    patterns = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    }

    redacted = text

    for pattern_type, pattern in patterns.items():
        for match in re.finditer(pattern, redacted):
            detections.append(
                {
                    "pattern_type": pattern_type,
                    "original": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                }
            )
        redacted = re.sub(pattern, f"[REDACTED_{pattern_type.upper()}]", redacted)

    return redacted, detections


def redact_with_ner(
    text: str, ner_model=None
) -> Tuple[str, List[dict]]:
    """Redact PII using an NER model (spaCy or similar).

    If no model is provided, falls back to pattern-based redaction.
    Returns (redacted_text, detections).
    """
    if ner_model is None:
        return redact_patterns(text)

    detections: List[dict] = []
    doc = ner_model(text)
    redacted = text

    for ent in doc.ents:
        if ent.label_ in {"PERSON", "ORG", "EMAIL", "PHONE", "SSN", "GPE", "DATE"}:
            detections.append(
                {
                    "pattern_type": ent.label_.lower(),
                    "original": ent.text,
                    "start": ent.start_char,
                    "end": ent.end_char,
                }
            )
            redacted = redacted.replace(ent.text, f"[REDACTED_{ent.label_}]")

    return redacted, detections
