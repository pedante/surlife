"""Constrained OpenRouter free-tier model gateway (no extra SDK required).

Only the host calls the endpoint. Never serialize the API key to events or souls.
Transport is injectable, so tests exercise this code without live network calls.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openrouter/free"


class GatewayError(Exception):
    """Public, scrubbed failure class; never includes API keys or request headers."""


@dataclass(frozen=True)
class Reply:
    mask: int | None
    soul_update: str
    model: str
    usage: dict[str, int | None]
    status: str = "ok"


def require_free_model(model: str) -> None:
    if model != DEFAULT_MODEL and not model.endswith(":free"):
        raise ValueError("M1 only accepts openrouter/free or a pinned :free model; paid models disabled")
    if any(c.isspace() for c in model) or len(model) > 140:
        raise ValueError("invalid model identifier")


def parse_answer(content: str, actual_model: str, usage: dict) -> Reply:
    """Extract a tiny data-only answer; never execute model output."""
    if not isinstance(content, str) or len(content) > 4096:
        raise GatewayError("non-text or oversized model response")
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0].strip()
    try:
        data = json.loads(text)
    except (ValueError, TypeError) as e:
        raise GatewayError("model did not produce a JSON object") from e
    if not isinstance(data, dict) or "mask" not in data:
        raise GatewayError("model response missing mask")
    mask = data["mask"]
    if mask is not None and (type(mask) is not int or not 0 <= mask < 32):
        raise GatewayError("mask must be null or an integer from 0 through 31")
    update = data.get("soul_update", "")
    if not isinstance(update, str):
        update = ""
    update = update.strip().replace("\n", " ")[:120]
    metric = {}
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        v = usage.get(key) if isinstance(usage, dict) else None
        metric[key] = v if type(v) is int and v >= 0 else None
    return Reply(mask=mask, soul_update=update, model=actual_model[:160], usage=metric)


class OpenRouterGateway:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        max_requests: int = 6,
        max_output_tokens: int = 128,
        transport: Callable[[dict, str, int], dict] | None = None,
    ):
        require_free_model(model)
        if type(max_requests) is not int or max_requests < 1:
            raise ValueError("max_requests must be positive")
        if type(max_output_tokens) is not int or not 16 <= max_output_tokens <= 512:
            raise ValueError("max_output_tokens must be between 16 and 512")
        self.model, self.limit, self.calls = model, max_requests, 0
        self.max_output_tokens = max_output_tokens
        self.transport = transport or self._http

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.calls)

    def _http(self, payload: dict, api_key: str, timeout: int) -> dict:
        raw = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(ENDPOINT, data=raw, method="POST", headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            "X-Title": "Surlife M1 experiment",
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status != 200:
                    raise GatewayError(f"unexpected provider status {response.status}")
                data = response.read(150_000)
        except urllib.error.HTTPError as e:
            raise GatewayError(f"OpenRouter returned HTTP {e.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise GatewayError("OpenRouter request failed or timed out") from None
        try:
            return json.loads(data)
        except (ValueError, TypeError) as e:
            raise GatewayError("invalid provider JSON") from e

    def ask(self, messages: list[dict]) -> Reply:
        if not self.remaining:
            raise GatewayError("per-run request cap reached")
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise GatewayError("OPENROUTER_API_KEY is not set")
        self.calls += 1  # debit before send; never silently retry
        payload = {
            "model": self.model, "messages": messages, "temperature": 0,
            "max_completion_tokens": self.max_output_tokens, "stream": False,
        }
        try:
            raw = self.transport(payload, api_key, 30)
            choice = raw["choices"][0]["message"]["content"]
            return parse_answer(choice, str(raw.get("model", self.model)), raw.get("usage") or {})
        except (KeyError, TypeError, IndexError) as e:
            raise GatewayError("missing or malformed provider response") from e


class FakeGateway(OpenRouterGateway):
    """Deterministic test double: fixed first-fit policy, not learning."""

    def __init__(self, max_requests: int = 6):
        super().__init__(max_requests=max_requests)

    def ask(self, messages: list[dict]) -> Reply:
        if not self.remaining:
            raise GatewayError("per-run request cap reached")
        self.calls += 1
        payload = json.loads(messages[-1]["content"])
        items, capacity = payload["task"]["items"], payload["task"]["capacity"]
        mask = 0
        for i, (cost, _) in enumerate(items):
            if cost <= capacity:
                mask |= 1 << i
                capacity -= cost
        # Fake revisions exercise the persistence protocol, not cognitive gains.
        return Reply(mask=mask, soul_update="Check task capacity carefully." if payload["tick"] == 1 else "",
                     model="surlife/fake-model", usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
