"""AI extraction adapter with pluggable providers."""

from __future__ import annotations

import json
import re
import socket
import urllib.parse
import urllib.request
from dataclasses import dataclass

from profile_backend.src.profile_backend.core.settings import settings
from profile_backend.src.profile_backend.domain.organize import normalize_dob


@dataclass
class AIExtractedFields:
    name: str = ""
    gender: str = ""
    dob: str = ""
    birth_place: str = ""
    birth_time: str = ""
    height: str = ""
    religion_caste: str = ""
    contact_number: str = ""
    email: str = ""
    address: str = ""
    occupation_work: str = ""
    salary: str = ""
    education: str = ""
    father_name: str = ""
    father_occupation: str = ""
    mother_name: str = ""
    mother_occupation: str = ""
    hobbies: str = ""
    preferences: str = ""
    diet_preference: str = ""
    brothers: str = ""
    sisters: str = ""


def _safe_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.strip().split())
    return str(value).strip()


def _to_fields(data: dict[str, object]) -> AIExtractedFields:
    normalized = {k: _safe_text(data.get(k)) for k in AIExtractedFields.__annotations__}
    normalized["dob"] = normalize_dob(normalized.get("dob")) or normalized.get("dob", "")
    return AIExtractedFields(**normalized)


def _schema_keys() -> list[str]:
    return list(AIExtractedFields.__annotations__.keys())


def _extract_openai(text: str) -> AIExtractedFields:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None)
    system = (
        "You extract structured biodata from profile documents in any language. "
        "Return ONLY valid JSON with empty string for missing values."
    )
    user = (
        "Extract fields and return JSON with exactly these keys:\n"
        + ", ".join(_schema_keys())
        + "\n\nDocument text:\n"
        + text[:120000]
    )
    response = client.chat.completions.create(
        model=settings.llm_model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    content = response.choices[0].message.content or "{}"
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise RuntimeError("AI model did not return a JSON object.")
    return _to_fields(payload)


def _extract_ollama(text: str) -> AIExtractedFields:
    request_payload = {
        "model": settings.ollama_model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": "Extract biodata fields and return JSON only."},
            {"role": "user", "content": "Fields: " + ", ".join(_schema_keys()) + "\n\n" + text[:120000]},
        ],
    }
    req = urllib.request.Request(
        settings.ollama_api_url,
        data=json.dumps(request_payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=480) as resp:
            envelope = json.loads(resp.read().decode("utf-8", errors="replace"))
    except TimeoutError as exc:
        raise RuntimeError(
            "Ollama request timed out after 480 seconds. Ensure Ollama is running and/or use a smaller/faster model."
        ) from exc
    except socket.timeout as exc:
        raise RuntimeError(
            "Ollama request timed out after 480 seconds. Ensure Ollama is running and/or use a smaller/faster model."
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama request failed: {exc.reason}") from exc
    msg = envelope.get("message") if isinstance(envelope, dict) else None
    content = _safe_text(msg.get("content")) if isinstance(msg, dict) else ""
    if not content:
        raise RuntimeError("Ollama response missing message content.")
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if not match:
            raise RuntimeError("Ollama did not return parseable field JSON.")
        payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise RuntimeError("Ollama field payload is not a JSON object.")
    return _to_fields(payload)


def _extract_deepai(text: str) -> AIExtractedFields:
    if not settings.deepai_api_key:
        raise RuntimeError("DEEPAI_API_KEY is not set.")
    prompt = "Extract JSON with keys: " + ", ".join(_schema_keys()) + "\n\n" + text[:120000]
    body = urllib.parse.urlencode({"text": prompt}).encode("utf-8")
    req = urllib.request.Request(
        settings.deepai_api_url,
        data=body,
        method="POST",
        headers={"api-key": settings.deepai_api_key},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode("utf-8", errors="replace"))
    candidate = payload.get("output") if isinstance(payload, dict) else None
    if isinstance(candidate, str):
        candidate = json.loads(candidate)
    if not isinstance(candidate, dict):
        raise RuntimeError("DeepAI did not return parseable field JSON.")
    return _to_fields(candidate)


def extract_fields_ai_provider(text: str) -> AIExtractedFields:
    provider = (settings.llm_provider or "ollama").strip().lower()
    if provider == "ollama":
        return _extract_ollama(text)
    if provider == "deepai":
        return _extract_deepai(text)
    return _extract_openai(text)
