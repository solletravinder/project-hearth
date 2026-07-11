import json
import uuid
from datetime import UTC, datetime
from typing import Any


def _new_id() -> str:
    return uuid.uuid4().hex


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _row_to_dict(row) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def _deserialize_metadata(result: dict[str, Any] | None) -> dict[str, Any] | None:
    if result and result.get("metadata"):
        result["metadata"] = json.loads(result["metadata"])
    return result
