"""
OpenRouter AI Client — Reusable chat-completion helper.

Uses the OpenAI-compatible API exposed by OpenRouter to route requests
to Mistral 7B Instruct (or any other model available on OpenRouter).

Environment variables consumed:
    OPENROUTER_API_KEY  – your "sk-or-v1-…" key
    OPENROUTER_BASE_URL – defaults to https://openrouter.ai/api/v1
    OPENROUTER_MODEL    – defaults to mistralai/mistral-7b-instruct-v0.1
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL: str = os.getenv(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
)
OPENROUTER_MODEL: str = os.getenv(
    "OPENROUTER_MODEL", "mistralai/mistral-7b-instruct-v0.1"
)


# ── Reusable chat-completion function ─────────────────────────────────
async def chat_completion(
    messages: List[Dict[str, str]],
    *,
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    top_p: float = 1.0,
    **extra_body: Any,
) -> str:
    """
    Send a chat-completion request to OpenRouter and return the assistant
    reply as a plain string.

    Parameters
    ----------
    messages : list[dict]
        OpenAI-style message list, e.g.
        [{"role": "system", "content": "…"}, {"role": "user", "content": "…"}]
    model : str | None
        Override the default model for this call.
    temperature : float
        Sampling temperature (0 = deterministic).
    max_tokens : int
        Maximum tokens in the response.
    top_p : float
        Nucleus-sampling parameter.
    **extra_body
        Any additional fields forwarded to the request body.

    Returns
    -------
    str
        The content of the first assistant choice.

    Raises
    ------
    RuntimeError
        If the API returns a non-2xx status or the response is malformed.
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. "
            "Add it to your .env file or export it as an environment variable."
        )

    url = f"{OPENROUTER_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "CivicConnect AI",
    }
    payload: Dict[str, Any] = {
        "model": model or OPENROUTER_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        **extra_body,
    }

    logger.debug("OpenRouter request → model=%s, msgs=%d", payload["model"], len(messages))

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text
            logger.error("OpenRouter HTTP %s: %s", exc.response.status_code, body)
            raise RuntimeError(
                f"OpenRouter API error ({exc.response.status_code}): {body}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("OpenRouter request failed: %s", exc)
            raise RuntimeError(f"OpenRouter connection error: {exc}") from exc

    data = resp.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        logger.error("Unexpected OpenRouter response shape: %s", json.dumps(data)[:500])
        raise RuntimeError(
            f"Malformed OpenRouter response: {json.dumps(data)[:300]}"
        ) from exc

    logger.debug("OpenRouter reply (%d chars)", len(content))
    return content


# ── Convenience: parse JSON from the reply ────────────────────────────
async def chat_completion_json(
    messages: List[Dict[str, str]],
    **kwargs: Any,
) -> Dict:
    """
    Wrapper around ``chat_completion`` that attempts to parse the reply as
    JSON (stripping any ```json fences).
    """
    import re

    raw = await chat_completion(messages, **kwargs)

    # Strip markdown code fences
    cleaned = raw.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # Remove JS-style comments & trailing commas
    cleaned = re.sub(r"//.*", "", cleaned)
    cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)

    return json.loads(cleaned)


# ── Quick sanity-check when run directly ──────────────────────────────
if __name__ == "__main__":
    import asyncio

    async def _demo():
        reply = await chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello in three languages."},
            ],
            temperature=0.7,
        )
        print("=== OpenRouter Demo Reply ===")
        print(reply)

    asyncio.run(_demo())
