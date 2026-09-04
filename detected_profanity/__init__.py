"""detected_profanity — profanity detection for RU/EN/translit."""

from __future__ import annotations

from typing import Final

from .detector import ProfanityDetector, censor, contains_profanity, detect
from .normalizer import normalize_text

__version__: Final[str] = "1.0.0"
__all__ = [
    "ProfanityDetector",
    "contains_profanity",
    "detect",
    "censor",
    "normalize_text",
    "__version__",
]
