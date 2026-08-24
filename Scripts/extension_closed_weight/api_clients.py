"""
Thin HTTP wrappers for OpenAI, Gemini, and Anthropic Claude chat completions.

All call_*() functions return the model's plain text completion (a string) on
success and None on failure. They retry on transient errors (429, 500-class).
No decoding parameters are overridden — provider defaults are used so the
closed-weight runs are as comparable to the open-weight Ollama-default runs
as the protocol allows.

Reads:
  OPENAI_API_KEY     required for OpenAI calls
  GEMINI_API_KEY     required for Gemini calls
  ANTHROPIC_API_KEY  required for Claude calls
"""

from __future__ import annotations

import os
import time

import requests

OPENAI_URL    = "https://api.openai.com/v1/chat/completions"
GEMINI_URL    = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

# Anthropic API requires an explicit max_tokens. Empirically, the listwise
# selection task produces responses well under 200 tokens (cf. the gpt-5.4
# run averaged ~130 output tokens). 512 leaves comfortable headroom while
# keeping a hard upper bound on output cost.
CLAUDE_MAX_TOKENS = 512


class APIError(RuntimeError):
    pass


def _retry_sleep(attempt: int) -> None:
    time.sleep(2 ** attempt)


def call_openai(model: str, prompt: str, timeout: int = 120, max_retries: int = 2) -> str | None:
    """Call OpenAI chat completions. Returns the assistant text, or None on failure."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise APIError("OPENAI_API_KEY is not set in the environment.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(OPENAI_URL, headers=headers, json=payload, timeout=timeout)
        except requests.RequestException as e:
            if attempt < max_retries:
                _retry_sleep(attempt)
                continue
            print(f"      [openai] network error: {e}")
            return None

        if resp.status_code == 200:
            try:
                return resp.json()["choices"][0]["message"]["content"]
            except (KeyError, IndexError, ValueError) as e:
                print(f"      [openai] unexpected response shape: {e} | {resp.text[:200]}")
                return None

        if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
            print(f"      [openai] {resp.status_code} backoff, retrying...")
            _retry_sleep(attempt)
            continue

        print(f"      [openai] error {resp.status_code}: {resp.text[:200]}")
        return None

    return None


def call_gemini(model: str, prompt: str, timeout: int = 120, max_retries: int = 2) -> str | None:
    """Call Gemini generateContent. Returns the text, or None on failure."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise APIError("GEMINI_API_KEY is not set in the environment.")

    url = GEMINI_URL.format(model=model)
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
    }
    # Disable internal reasoning ("thinking") for Gemini 2.5+ to (a) keep the
    # behavior comparable to the open-weight models which answer directly without
    # chain-of-thought, and (b) avoid paying the output rate for hidden reasoning
    # tokens. Models that do not support this field ignore it.
    if model.startswith("gemini-2.") or model.startswith("gemini-3"):
        payload["generationConfig"] = {"thinkingConfig": {"thinkingBudget": 0}}

    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                url, headers=headers, params={"key": api_key}, json=payload, timeout=timeout
            )
        except requests.RequestException as e:
            if attempt < max_retries:
                _retry_sleep(attempt)
                continue
            print(f"      [gemini] network error: {e}")
            return None

        if resp.status_code == 200:
            try:
                data = resp.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    finish = data.get("promptFeedback", {})
                    print(f"      [gemini] no candidates, feedback: {finish}")
                    return None
                parts = candidates[0].get("content", {}).get("parts") or []
                text = "".join(p.get("text", "") for p in parts)
                return text or None
            except (KeyError, IndexError, ValueError) as e:
                print(f"      [gemini] unexpected response shape: {e} | {resp.text[:200]}")
                return None

        if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
            print(f"      [gemini] {resp.status_code} backoff, retrying...")
            _retry_sleep(attempt)
            continue

        print(f"      [gemini] error {resp.status_code}: {resp.text[:200]}")
        return None

    return None


def call_claude(model: str, prompt: str, timeout: int = 120, max_retries: int = 2) -> str | None:
    """Call Anthropic Messages API. Returns the assistant text, or None on failure."""
    # Accept either ANTHROPIC_API_KEY (canonical, used by the official SDK)
    # or CLAUDE_API_KEY (commonly used informally); ANTHROPIC_API_KEY wins.
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        raise APIError(
            "Neither ANTHROPIC_API_KEY nor CLAUDE_API_KEY is set in the environment."
        )

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": CLAUDE_MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }

    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=timeout)
        except requests.RequestException as e:
            if attempt < max_retries:
                _retry_sleep(attempt)
                continue
            print(f"      [claude] network error: {e}")
            return None

        if resp.status_code == 200:
            try:
                data = resp.json()
                blocks = data.get("content") or []
                text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
                return text or None
            except (KeyError, IndexError, ValueError) as e:
                print(f"      [claude] unexpected response shape: {e} | {resp.text[:200]}")
                return None

        if resp.status_code in (429, 500, 502, 503, 504, 529) and attempt < max_retries:
            print(f"      [claude] {resp.status_code} backoff, retrying...")
            _retry_sleep(attempt)
            continue

        print(f"      [claude] error {resp.status_code}: {resp.text[:200]}")
        return None

    return None


def call_model(model: str, prompt: str, timeout: int = 120) -> str | None:
    """Dispatch to the right provider based on the model name."""
    if model.startswith("gpt-") or model.startswith("o1-") or model.startswith("o4-"):
        return call_openai(model, prompt, timeout=timeout)
    if model.startswith("gemini-"):
        return call_gemini(model, prompt, timeout=timeout)
    if model.startswith("claude-"):
        return call_claude(model, prompt, timeout=timeout)
    raise APIError(f"Unrecognized closed-weight model: {model!r}")
