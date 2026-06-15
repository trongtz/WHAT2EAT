from __future__ import annotations

import json
from typing import Any

import httpx

from core.config import settings


class OpenAIResponsesError(RuntimeError):
    pass


def request_structured_json(
    *,
    schema_name: str,
    schema: dict[str, Any],
    payload: dict[str, Any],
    instructions: str,
) -> dict[str, Any]:
    if not settings.OPENAI_API_KEY:
        raise OpenAIResponsesError("OPENAI_API_KEY is missing.")

    try:
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.OPENAI_MODEL,
                "instructions": instructions,
                "input": json.dumps(payload, ensure_ascii=False),
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": schema_name,
                        "strict": True,
                        "schema": schema,
                    }
                },
            },
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise OpenAIResponsesError("OpenAI request failed or timed out.") from exc

    if response.status_code >= 400:
        raise OpenAIResponsesError(f"OpenAI request failed: {response.status_code}")

    return _extract_json(_extract_response_text(response.json()))


def _extract_response_text(response: dict[str, Any]) -> str:
    if response.get("output_text"):
        return str(response["output_text"])

    parts: list[str] = []
    for output_item in response.get("output", []) or []:
        for content_item in output_item.get("content", []) or []:
            text = content_item.get("text")
            if text:
                parts.append(str(text))
    if not parts:
        raise OpenAIResponsesError("OpenAI response did not contain text.")
    return "\n".join(parts)


def _extract_json(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text.strip())
    except json.JSONDecodeError as exc:
        raise OpenAIResponsesError("OpenAI response was not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise OpenAIResponsesError("OpenAI response JSON was not an object.")
    return payload
