"""Optional Google Gemini Interactions adapter, no model tools or automatic retries."""
from __future__ import annotations
import os
from typing import Callable
from .gateway import (ACTION_SCHEMA, REFLECTION_SCHEMA, GatewayError, Reply,
                      action_menu_schema, benchmark_action_schema, normalized_usage,
                      parse_answer, parse_benchmark_answer, parse_reflection)

DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
FREE_GEMINI_MODELS = frozenset({
    "gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash-lite",
})


def check_gemini_model(model: str) -> dict:
    if model == "gemini-3.7-flash":
        raise ValueError("gemini-3.7-flash is deprecated and routed to gemini-3.8-flash")
    if model not in FREE_GEMINI_MODELS:
        raise ValueError("model not in reviewed Gemini API free-tier allow-list")
    return {
        "model": model,
        "free_tier_listed": True,
        "account_billing_verified": False,
        "warning": "Google free-tier model does not guarantee this key uses free billing; verify in AI Studio",
    }


def _schema(mode: str, allowed_masks: list[int] | None,
            benchmark_items: int | None) -> dict:
    if mode == "benchmark":
        if benchmark_items is None or allowed_masks is not None:
            raise ValueError("benchmark requires item count and no menu")
        original = benchmark_action_schema(benchmark_items)
    elif mode == "reflection":
        if benchmark_items is not None or allowed_masks is not None:
            raise ValueError("reflection accepts no action constraints")
        original = REFLECTION_SCHEMA
    elif mode == "action":
        if benchmark_items is not None:
            raise ValueError("item count requires benchmark mode")
        original = action_menu_schema(allowed_masks) if allowed_masks is not None else ACTION_SCHEMA
    else:
        raise ValueError("invalid consultation mode")
    raw = original["json_schema"]["schema"]
    return {
        "type": "object",
        "properties": {
            key: {p: v for p, v in value.items()
                  if p in ("type", "enum", "minimum", "maximum", "description")}
            for key, value in raw["properties"].items()
        },
        "required": raw["required"],
    }


def _prompt(messages: list[dict]) -> str:
    if not isinstance(messages, list) or not 1 <= len(messages) <= 15:
        raise ValueError("messages must be a short nonempty list")
    chunks = []
    for msg in messages:
        if (not isinstance(msg, dict)
                or msg.get("role") not in ("system", "developer", "user", "assistant")
                or not isinstance(msg.get("content"), str)):
            raise ValueError("malformed prompt message")
        chunks.append(msg["role"].upper() + ":\n" + msg["content"])
    combined = "\n\n".join(chunks)
    if len(combined) > 18000:
        raise ValueError("prompt too large")
    return combined


def _usage(interaction) -> dict:
    raw = getattr(interaction, "usage", None)
    getter = raw.get if isinstance(raw, dict) else lambda k: getattr(raw, k, None)
    return normalized_usage({
        "prompt_tokens": getter("total_input_tokens"),
        "completion_tokens": getter("total_output_tokens"),
        "total_tokens": getter("total_tokens"),
    }) or {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}


def _reason(exc: Exception) -> str:
    code = getattr(exc, "code", None)
    if code is None:
        code = getattr(exc, "status_code", None)
    if type(code) is int and 400 <= code <= 599:
        return "http_" + str(code)
    if isinstance(code, str) and code.isdigit() and 400 <= int(code) <= 599:
        return "http_" + code
    return "google_provider_failure"


class GeminiGateway:
    def __init__(self, model: str = DEFAULT_GEMINI_MODEL,
                 max_requests: int = 6, max_output_tokens: int = 512,
                 reasoning: str = "off", transport: Callable | None = None):
        check_gemini_model(model)
        if type(max_requests) is not int or max_requests < 1:
            raise ValueError("max_requests must be positive")
        if type(max_output_tokens) is not int or not 16 <= max_output_tokens <= 1024:
            raise ValueError("max_output_tokens must be 16..1024")
        if reasoning not in ("off", "low", "auto"):
            raise ValueError("reasoning must be off, low or auto")
        if transport is None:
            try:
                from google import genai  # noqa: F401 - optional SDK preflight
            except ImportError:
                raise ValueError(
                    "Google provider requires python -m pip install -e '.[gemini]'"
                ) from None
        self.model, self.limit, self.calls = model, max_requests, 0
        self.max_output_tokens, self.reasoning = max_output_tokens, reasoning
        self.transport = transport or self._sdk_call

    @property
    def remaining(self):
        return max(0, self.limit - self.calls)

    @staticmethod
    def _sdk_call(*, api_key: str, **kwargs):
        try:
            from google import genai
        except ImportError:
            raise GatewayError("install google-genai optional dependency", "missing_google_sdk") from None
        client = genai.Client(api_key=api_key)
        try:
            return client.interactions.create(**kwargs)
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                close()

    def ask(self, messages: list[dict], *, mode: str = "action",
            allowed_masks: list[int] | None = None,
            benchmark_items: int | None = None) -> Reply:
        schema = _schema(mode, allowed_masks, benchmark_items)
        prompt = _prompt(messages)
        if not self.remaining:
            raise GatewayError("model request budget exhausted", "request_cap")
        key = os.environ.get("GOOGLE_API_KEY", "").strip()
        if not key:
            raise GatewayError("GOOGLE_API_KEY missing", "missing_google_api_key")
        self.calls += 1  # debit before send; no automatic retry
        try:
            interaction = self.transport(
                api_key=key, model=self.model, input=prompt, store=False,
                response_format={"type": "text", "mime_type": "application/json",
                                 "schema": schema},
                generation_config={
                    "max_output_tokens": self.max_output_tokens,
                    "thinking_level": "low" if self.reasoning in ("off", "low") else "medium",
                },
            )
        except GatewayError:
            raise
        except Exception as exc:
            raise GatewayError("Google provider call failed", _reason(exc)) from None
        served = getattr(interaction, "model", None) or self.model
        usage = _usage(interaction)
        if served != self.model:
            err = GatewayError("Gemini served unexpected model", "routed_model_mismatch")
            err.model, err.usage = str(served)[:160], usage
            raise err
        if getattr(interaction, "status", "completed") not in ("completed", None):
            err = GatewayError("Gemini interaction incomplete", "incomplete_interaction")
            err.model, err.usage = self.model, usage
            raise err
        content = getattr(interaction, "output_text", None)
        try:
            if mode == "benchmark":
                return parse_benchmark_answer(content, self.model, usage, benchmark_items)
            if mode == "reflection":
                return parse_reflection(content, self.model, usage)
            return parse_answer(content, self.model, usage)
        except GatewayError as exc:
            exc.model, exc.usage = self.model, usage
            raise
