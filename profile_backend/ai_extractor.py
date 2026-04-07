"""AI-only extractor for multilingual profile documents."""

from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass

from profile_backend.config import (
    DEEPAI_API_KEY,
    DEEPAI_API_URL,
    LLM_MODEL,
    LLM_PROVIDER,
    OLLAMA_API_URL,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    TEXTRAZOR_API_KEY,
    TEXTRAZOR_API_URL,
)

logger = logging.getLogger("profile_backend.ai_extractor")


@dataclass
class AIExtractedFields:
    name: str = ""
    gender: str = ""
    dob: str = ""  # YYYY-MM-DD preferred
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


def _safe_text(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return " ".join(v.strip().split())
    return str(v).strip()


def _to_fields(data: dict[str, object]) -> AIExtractedFields:
    return AIExtractedFields(
        name=_safe_text(data.get("name")),
        gender=_safe_text(data.get("gender")),
        dob=_safe_text(data.get("dob")),
        birth_place=_safe_text(data.get("birth_place")),
        birth_time=_safe_text(data.get("birth_time")),
        height=_safe_text(data.get("height")),
        religion_caste=_safe_text(data.get("religion_caste")),
        contact_number=_safe_text(data.get("contact_number")),
        email=_safe_text(data.get("email")),
        address=_safe_text(data.get("address")),
        occupation_work=_safe_text(data.get("occupation_work")),
        salary=_safe_text(data.get("salary")),
        education=_safe_text(data.get("education")),
        father_name=_safe_text(data.get("father_name")),
        father_occupation=_safe_text(data.get("father_occupation")),
        mother_name=_safe_text(data.get("mother_name")),
        mother_occupation=_safe_text(data.get("mother_occupation")),
        hobbies=_safe_text(data.get("hobbies")),
        preferences=_safe_text(data.get("preferences")),
        diet_preference=_safe_text(data.get("diet_preference")),
        brothers=_safe_text(data.get("brothers")),
        sisters=_safe_text(data.get("sisters")),
    )


def extract_fields_ai(text: str) -> AIExtractedFields:
    """
    Extract all profile fields from raw text using an LLM.
    Multilingual support is delegated to the model.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    from openai import OpenAI

    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL or None,
    )

    system = (
        "You extract structured biodata from profile documents in any language. "
        "Return ONLY valid JSON. "
        "Do not guess missing values. Use empty string for missing fields. "
        "If DOB can be normalized, output YYYY-MM-DD. "
        "Map multilingual labels/terms automatically to the schema keys."
    )
    schema_keys = [
        "name",
        "gender",
        "dob",
        "birth_place",
        "birth_time",
        "height",
        "religion_caste",
        "contact_number",
        "email",
        "address",
        "occupation_work",
        "salary",
        "education",
        "father_name",
        "father_occupation",
        "mother_name",
        "mother_occupation",
        "hobbies",
        "preferences",
        "diet_preference",
        "brothers",
        "sisters",
    ]
    user = (
        "Extract the fields below from this document text and return JSON with exactly these keys:\n"
        + ", ".join(schema_keys)
        + "\n\nDocument text:\n"
        + text[:120000]
    )

    response = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = response.choices[0].message.content or "{}"
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON from AI extractor: %s", e)
        raise RuntimeError("AI model returned invalid JSON.") from e
    if not isinstance(payload, dict):
        raise RuntimeError("AI model did not return a JSON object.")
    return _to_fields(payload)


def _extract_fields_ai_deepai(text: str) -> AIExtractedFields:
    if not DEEPAI_API_KEY:
        raise RuntimeError("DEEPAI_API_KEY is not set.")

    schema_keys = [
        "name",
        "gender",
        "dob",
        "birth_place",
        "birth_time",
        "height",
        "religion_caste",
        "contact_number",
        "email",
        "address",
        "occupation_work",
        "salary",
        "education",
        "father_name",
        "father_occupation",
        "mother_name",
        "mother_occupation",
        "hobbies",
        "preferences",
        "diet_preference",
        "brothers",
        "sisters",
    ]
    prompt = (
        "Extract biodata from this profile document text in any language. "
        "Return only valid JSON with exactly these keys and empty string for missing values: "
        + ", ".join(schema_keys)
        + ". Normalize DOB to YYYY-MM-DD when possible.\n\nDocument text:\n"
        + text[:120000]
    )

    body = urllib.parse.urlencode({"text": prompt}).encode("utf-8")
    req = urllib.request.Request(
        DEEPAI_API_URL,
        data=body,
        method="POST",
        headers={"api-key": DEEPAI_API_KEY},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        raise RuntimeError(f"DeepAI request failed: {e}") from e

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError("DeepAI returned invalid JSON response envelope.") from e

    # DeepAI may return generated text in "output"
    if isinstance(payload, dict):
        if all(k in payload for k in schema_keys):
            return _to_fields(payload)
        candidate = payload.get("output") or payload.get("result") or payload.get("response")
        if isinstance(candidate, dict):
            return _to_fields(candidate)
        if isinstance(candidate, str):
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return _to_fields(parsed)
            except json.JSONDecodeError:
                match = re.search(r"\{.*\}", candidate, flags=re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, dict):
                        return _to_fields(parsed)

    raise RuntimeError("DeepAI did not return parseable field JSON.")


def _extract_fields_ai_textrazor(text: str) -> AIExtractedFields:
    if not TEXTRAZOR_API_KEY:
        raise RuntimeError("TEXTRAZOR_API_KEY is not set.")

    form = {
        "text": text[:120000],
        "extractors": "entities,topics,relations,dependency-trees",
        "cleanup.mode": "raw",
    }
    body = urllib.parse.urlencode(form).encode("utf-8")
    req = urllib.request.Request(
        TEXTRAZOR_API_URL,
        data=body,
        method="POST",
        headers={
            "x-textrazor-key": TEXTRAZOR_API_KEY,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        raise RuntimeError(f"TextRazor request failed: {e}") from e

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError("TextRazor returned invalid JSON.") from e

    response = payload.get("response") if isinstance(payload, dict) else None
    if not isinstance(response, dict):
        raise RuntimeError("TextRazor response missing 'response' object.")

    entities = response.get("entities")
    fields = AIExtractedFields()

    if isinstance(entities, list):
        # Best-effort extraction from typed entities
        for ent in entities:
            if not isinstance(ent, dict):
                continue
            eid = _safe_text(ent.get("entityId") or ent.get("matchedText"))
            etypes = ent.get("type", [])
            if isinstance(etypes, str):
                etypes = [etypes]
            etypes_str = " ".join(str(t).lower() for t in etypes)

            if not fields.name and ("person" in etypes_str or "/people/person" in etypes_str):
                fields.name = eid
            if not fields.birth_place and ("location" in etypes_str or "place" in etypes_str):
                fields.birth_place = eid
            if not fields.religion_caste and ("religion" in etypes_str):
                fields.religion_caste = eid

    return fields


def _extract_fields_ai_ollama(text: str) -> AIExtractedFields:
    schema_keys = [
        "name",
        "gender",
        "dob",
        "birth_place",
        "birth_time",
        "height",
        "religion_caste",
        "contact_number",
        "email",
        "address",
        "occupation_work",
        "salary",
        "education",
        "father_name",
        "father_occupation",
        "mother_name",
        "mother_occupation",
        "hobbies",
        "preferences",
        "diet_preference",
        "brothers",
        "sisters",
    ]
    system = (
        "You extract structured biodata from profile documents in any language. "
        "Return ONLY valid JSON object. "
        "Do not guess missing values; use empty string. "
        "Infer semantically (e.g. Sex => gender, Demo/Birthdate/DOB => dob). "
        "Normalize dob to YYYY-MM-DD when possible."
    )
    user = (
        "Extract these fields and return JSON with exactly these keys:\n"
        + ", ".join(schema_keys)
        + "\n\nDocument text:\n"
        + text[:120000]
    )
    request_payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    body = json.dumps(request_payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_API_URL,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        raise RuntimeError(f"Ollama request failed: {e}") from e

    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError("Ollama returned invalid JSON response envelope.") from e

    msg = envelope.get("message") if isinstance(envelope, dict) else None
    content = ""
    if isinstance(msg, dict):
        content = _safe_text(msg.get("content"))
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


def extract_fields_ai_provider(text: str) -> AIExtractedFields:
    provider = (LLM_PROVIDER or "ollama").strip().lower()
    if provider == "ollama":
        return _extract_fields_ai_ollama(text)
    if provider == "textrazor":
        return _extract_fields_ai_textrazor(text)
    if provider == "deepai":
        return _extract_fields_ai_deepai(text)
    return extract_fields_ai(text)

