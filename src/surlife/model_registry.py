"""Preflight OpenRouter model IDs using its current public API catalog.

A model's marketing page does not establish that its API slug is currently
available. Perform this check *before* creating a run or sending a billed call.
Only a local no-credential GET is used; no organism gets registry authority.
"""
from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Callable
import urllib.error
import urllib.request

from .gateway import require_free_model

CATALOG_URL = "https://openrouter.ai/api/v1/models"
MAX_CATALOG_BYTES = 10_000_000
DISALLOWED_ID_MARKERS = ("content-safety", "safety-classifier", "rerank", "embedding", "/embed-")


def fetch_catalog() -> dict:
    req = urllib.request.Request(
        CATALOG_URL, headers={"Accept": "application/json", "User-Agent": "Surlife/0.1"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status != 200:
                raise ValueError(f"OpenRouter model catalog returned HTTP {response.status}")
            payload = response.read(MAX_CATALOG_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise ValueError(f"OpenRouter model catalog returned HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ValueError("OpenRouter model catalog is unreachable; refusing to place model calls") from None
    if len(payload) > MAX_CATALOG_BYTES:
        raise ValueError("OpenRouter model catalog response exceeds maximum size")
    try:
        result = json.loads(payload)
    except (ValueError, UnicodeError):
        raise ValueError("OpenRouter model catalog is invalid JSON") from None
    if not isinstance(result, dict) or not isinstance(result.get("data"), list):
        raise ValueError("OpenRouter model catalog has an unexpected format")
    return result


def check_model(model: str, loader: Callable[[], dict] | None = None) -> dict:
    """Only permit listed, zero-priced text-output models with structured JSON.

    This is an availability/compatibility check, not a guarantee that an API
    inference request will be served successfully by any provider.
    """
    require_free_model(model)
    result = (loader or fetch_catalog)()
    if not isinstance(result, dict) or not isinstance(result.get("data"), list):
        raise ValueError("OpenRouter catalog has an unexpected format")
    entry = next(
        (item for item in result["data"] if isinstance(item, dict) and item.get("id") == model),
        None,
    )
    if entry is None:
        raise ValueError(
            f"Model '{model}' is not listed in OpenRouter's live API catalog. "
            "Choose a listed :free model with structured-output support."
        )
    if any(marker in model.lower() for marker in DISALLOWED_ID_MARKERS):
        raise ValueError(f"Model '{model}' is not a supported chat action model")
    pricing = entry.get("pricing")
    if not isinstance(pricing, dict):
        raise ValueError(f"Model '{model}' has no verifiable free price")
    try:
        free = Decimal(str(pricing["prompt"])) == 0 and Decimal(str(pricing["completion"])) == 0
    except (KeyError, InvalidOperation, ValueError, TypeError):
        free = False
    if not free:
        raise ValueError(f"Model '{model}' is not zero-priced for input and output tokens")
    params = entry.get("supported_parameters")
    if not isinstance(params, list) or not {"response_format", "structured_outputs"}.issubset(params):
        raise ValueError(f"Model '{model}' does not advertise structured JSON support")
    architecture = entry.get("architecture")
    if not isinstance(architecture, dict) or "text" not in architecture.get("output_modalities", []):
        raise ValueError(f"Model '{model}' does not advertise text output")
    return {"model": model, "available": True, "free": True, "structured_json": True,
            "source": CATALOG_URL}
