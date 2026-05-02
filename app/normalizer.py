import re
from unidecode import unidecode


WHITESPACE_RE = re.compile(r"\s+")
PUNCT_RE = re.compile(r"[^\w\s]")


def normalize_text(value: str) -> str:
    if not value:
        return ""
    normalized = unidecode(value).lower()
    normalized = PUNCT_RE.sub(" ", normalized)
    normalized = WHITESPACE_RE.sub(" ", normalized).strip()
    return normalized
