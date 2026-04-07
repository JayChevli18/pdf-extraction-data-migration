"""Lazy-loaded spaCy pipeline."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

from profile_backend.config import SPACY_MODEL

if TYPE_CHECKING:
    import spacy.language

logger = logging.getLogger("profile_backend.nlp")


@lru_cache(maxsize=1)
def get_nlp() -> "spacy.language.Language":
    import spacy

    try:
        return spacy.load(SPACY_MODEL)
    except OSError:
        logger.error(
            "spaCy model %r not found. Install with: python -m spacy download %s",
            SPACY_MODEL,
            SPACY_MODEL,
        )
        raise
