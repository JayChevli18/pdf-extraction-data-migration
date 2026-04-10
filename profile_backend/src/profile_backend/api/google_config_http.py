"""Resolve registered Google cloud config from request (tenant / per-user credentials)."""

from __future__ import annotations

from flask import Request

from profile_backend.src.profile_backend.application.google_cloud_config import GoogleCloudRuntimeConfig
from profile_backend.src.profile_backend.infrastructure.google.config_store import load_google_cloud_config


def require_registered_google_cloud_config(req: Request) -> GoogleCloudRuntimeConfig:
    """Require `X-Profile-Google-Config` header or `config_id` query param; load stored bundle."""
    cid = (req.headers.get("X-Profile-Google-Config") or req.args.get("config_id") or "").strip()
    if not cid:
        raise ValueError(
            "Missing config_id: set header X-Profile-Google-Config or query parameter config_id "
            "(register via POST /cloud/config/register first)."
        )
    return load_google_cloud_config(cid)
