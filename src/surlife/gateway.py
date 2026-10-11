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
DEFAULT_MODEL = "dots-studio/dots-3-note-preview:free"

# Use an endpoint that can return the organism's tiny JSON action. The
# free router may otherwise select moderation, embedding or reranking models.
ACTION_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "surlife_action",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "mask": {
                    "type": ["integer", "null"],
                    "description": "Item selection bitmask 0 to 31, or null to wait",
                },
                "soul_update": {
                    "type": "string",
                    "description": "A short optional personal strategy note, empty if none",
                },
            },
            "required": ["mask", "soul_update"],
            "additionalProperties": False,
        },
    },
}


REFLECTION_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "surlife_reflection",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "soul_update": {
                    "type": "string",
                    "description": "One reusable decision heuristic, 1-120 characters; empty if no lesson",
                },
            },
            "required": ["soul_update"],
            "additionalProperties": False,
        },
    },
}


def parse_reflection(content: str, actual_model: str, usage: dict) -> Reply:
    """Parse a data-only reflection with no task action or executable output."""
    if not isinstance(content, str) or len(content) > 4096:
        raise GatewayError("non-text or oversized reflection", "invalid_content")
    data_text = content.strip()
    if data_text.startswith("```"):
        data_text = data_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    start = data_text.find("{")
    if start < 0:
        raise GatewayError("reflection returned no JSON", "invalid_json")
    try:
        data, _ = json.JSONDecoder().raw_decode(data_text[start:])
    except (ValueError, TypeError):
        raise GatewayError("reflection returned invalid JSON", "invalid_json") from None
    if not isinstance(data, dict) or not isinstance(data.get("soul_update"), str):
        raise GatewayError("reflection missing soul_update", "missing_reflection")
    return Reply(mask=None, soul_update=data["soul_update"][:120],
                 model=actual_model[:160], usage=normalized_usage(usage) or normalized_usage({}))


class GatewayError(Exception):
    """Structured safe diagnostics. Never include provider body, prompt or API key."""

    def __init__(self, message: str, reason: str = "gateway_error") -> None:
        super().__init__(message)
        self.reason = reason
        self.model: str | None = None
        self.usage: dict[str, int | None] | None = None


@dataclass(frozen=True)
class Reply:
    mask: int | None
    soul_update: str
    model: str
    usage: dict[str, int | None]
    status: str = "ok"


def require_free_model(model: str) -> None:
    if model != "openrouter/free" and not model.endswith(":free"):
        raise ValueError("M1 only accepts openrouter/free or a pinned :free model; paid models disabled")
    if any(c.isspace() for c in model) or len(model) > 140:
        raise ValueError("invalid model identifier")


def normalized_usage(usage: object) -> dict[str, int | None] | None:
    if not isinstance(usage, dict):
        return None
    result = {}
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        v = usage.get(key)
        result[key] = v if type(v) is int and v >= 0 else None
    return result


def parse_answer(content: str, actual_model: str, usage: dict) -> Reply:
    """Decode one bounded JSON action, even when a free model surrounds it with prose."""
    if not isinstance(content, str) or len(content) > 4096:
        raise GatewayError("non-text or oversized model response", "invalid_content")
    text = content.strip()
    if not text:
        raise GatewayError("model returned empty content", "empty_content")
    # Many chat models add a Markdown fence or a one-line preamble despite instructions.
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0].strip()
    first = text.find("{")
    if first < 0:
        raise GatewayError("model returned no JSON object", "invalid_json")
    try:
        data, _end = json.JSONDecoder().raw_decode(text[first:])
    except (ValueError, TypeError) as e:
        raise GatewayError("model returned invalid JSON", "invalid_json") from e
    if not isinstance(data, dict) or "mask" not in data:
        raise GatewayError("model response missing mask", "missing_mask")
    mask = data["mask"]
    if mask is not None and (type(mask) is not int or not 0 <= mask < 32):
        raise GatewayError("mask must be null or an integer from 0 through 31", "invalid_mask")
    update = data.get("soul_update", "")
    if not isinstance(update, str):
        update = ""
    update = update.strip().replace("\n", " ")[:120]
    return Reply(mask=mask, soul_update=update, model=actual_model[:160],
                 usage=normalized_usage(usage) or normalized_usage({}))


def provider_error_reason(error: object, prefix: str) -> str:
    """Report only a numeric code from a provider envelope; never untrusted prose."""
    if not isinstance(error, dict):
        return prefix
    code = error.get("code")
    if type(code) is int and 100 <= code <= 599:
        return f"{prefix}_{code}"
    if isinstance(code, str) and len(code) == 3 and code.isascii() and code.isdigit():
        return f"{prefix}_{code}"
    return prefix


class OpenRouterGateway:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        max_requests: int = 6,
        max_output_tokens: int = 512,
        transport: Callable[[dict, str, int], dict] | None = None,
        reasoning: str = "off",
    ):
        require_free_model(model)
        if type(max_requests) is not int or max_requests < 1:
            raise ValueError("max_requests must be positive")
        if type(max_output_tokens) is not int or not 16 <= max_output_tokens <= 1024:
            raise ValueError("max_output_tokens must be between 16 and 1024")
        if reasoning not in ("off", "low", "auto"):
            raise ValueError("reasoning must be off, low or auto")
        self.reasoning = reasoning
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
                    raise GatewayError(f"unexpected provider HTTP status {response.status}", f"http_{response.status}")
                data = response.read(150_000)
        except urllib.error.HTTPError as e:
            raise GatewayError(f"OpenRouter returned HTTP {e.code}", f"http_{e.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise GatewayError("OpenRouter request failed or timed out", "network_failure") from None
        try:
            return json.loads(data)
        except (ValueError, TypeError) as e:
            raise GatewayError("invalid provider response JSON", "invalid_provider_json") from e

    def ask(self, messages: list[dict], *, mode: str = "action") -> Reply:
        if mode not in ("action", "reflection"):
            raise ValueError("invalid model consultation mode")
        if not self.remaining:
            raise GatewayError("per-run request cap reached")
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise GatewayError("OPENROUTER_API_KEY is not set")
        self.calls += 1  # debit before send; never silently retry
        payload = {
            "model": self.model, "messages": messages, "temperature": 0,
            "max_tokens": self.max_output_tokens, "stream": False,
        }
        # Prefer a concise answer over spending the entire completion budget
        # on hidden reasoning. Availability/behavior varies by free model.
        payload["response_format"] = ACTION_SCHEMA if mode == "action" else REFLECTION_SCHEMA
        payload["provider"] = {"require_parameters": True}
        if self.reasoning == "off":
            payload["reasoning"] = {"enabled": False}
        elif self.reasoning == "low":
            payload["reasoning"] = {"effort": "low"}
        raw = None
        try:
            raw = self.transport(payload, api_key, 30)
            if not isinstance(raw, dict):
                raise GatewayError("unexpected OpenRouter response shape", "invalid_response")
            if raw.get("error"):
                reason = provider_error_reason(raw["error"], "provider_error")
                raise GatewayError("OpenRouter reported a provider error", reason)
            choices = raw.get("choices")
            if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
                raise GatewayError("OpenRouter returned no completion choice", "missing_choice")
            choice = choices[0]
            # A router may still send a request to a model unsuitable for
            # general instruction following. Reject the action as unsupported.
            served = str(raw.get("model") or self.model).lower()
            if any(token in served for token in ("content-safety", "rerank", "embedding", "/embed-")):
                raise GatewayError("routed endpoint is not a chat action model", "unsuitable_model")
            if choice.get("finish_reason") == "error" or choice.get("error"):
                reason = provider_error_reason(choice.get("error"), "completion_error")
                raise GatewayError("OpenRouter reported an interrupted completion", reason)
            if choice.get("finish_reason") == "length":
                raise GatewayError(
                    "model output hit max completion tokens; increase --max-output-tokens",
                    "completion_truncated",
                )
            message = choice.get("message")
            if not isinstance(message, dict):
                raise GatewayError("OpenRouter response missing assistant message", "missing_message")
            content = message.get("content")
            if isinstance(content, list):
                content = "\n".join(
                    part["text"] for part in content if isinstance(part, dict)
                    and part.get("type") == "text" and isinstance(part.get("text"), str)
                )
            actual_model = str(raw.get("model") or self.model)[:160]
            try:
                parser = parse_answer if mode == "action" else parse_reflection
                return parser(content, actual_model, raw.get("usage") or {})
            except GatewayError as exc:
                # The provider may have charged tokens even when its text was unusable.
                exc.model = actual_model
                exc.usage = normalized_usage(raw.get("usage"))
                raise
        except GatewayError as exc:
            # Even a completion rejected as truncated may include a model ID
            # and usage. Neither is trusted authority and no raw text is logged.
            if isinstance(raw, dict):
                if exc.model is None:
                    model = raw.get("model")
                    if isinstance(model, str):
                        exc.model = model[:160]
                if exc.usage is None:
                    exc.usage = normalized_usage(raw.get("usage"))
            raise
        except (KeyError, TypeError, IndexError) as e:
            raise GatewayError("missing or malformed provider response", "invalid_response") from e


class FakeGateway(OpenRouterGateway):
    """Deterministic test double: fixed first-fit policy, not learning."""

    def __init__(self, max_requests: int = 6):
        super().__init__(max_requests=max_requests)

    def ask(self, messages: list[dict]) -> Reply:
        if not self.remaining:
            raise GatewayError("per-run request cap reached")
        self.calls += 1
        payload = json.loads(messages[-1]["content"])
        if mode == "reflection":
            return Reply(mask=None,
                         soul_update="Check selected costs against capacity before submitting any subset.",
                         model="surlife/fake-model",
                         usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        items, capacity = payload["task"]["items"], payload["task"]["capacity"]
        mask = 0
        for i, (cost, _) in enumerate(items):
            if cost <= capacity:
                mask |= 1 << i
                capacity -= cost
        # Fake revisions exercise the persistence protocol, not cognitive gains.
        return Reply(mask=mask, soul_update="Check task capacity carefully." if payload["tick"] == 1 else "",
                     model="surlife/fake-model", usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
