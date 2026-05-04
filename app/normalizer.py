import re
from app.models import ScreeningRequest
from app.security import hmac_identifier
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


def normalize_screening_request(payload: ScreeningRequest) -> dict:
    normalized_addresses = []
    countries = []
    for address in payload.addresses:
        normalized_country = normalize_text(address.country)
        normalized_addresses.append(
            {
                "line1": normalize_text(address.line1),
                "city": normalize_text(address.city),
                "state": normalize_text(address.state or ""),
                "postal_code": normalize_text(address.postal_code or ""),
                "country": normalized_country,
            }
        )
        if normalized_country:
            countries.append(normalized_country)

    normalized_identifiers = [
        {
            "type": identifier.type.value,
            "value_hash": hmac_identifier(identifier.value),
        }
        for identifier in payload.identifiers
    ]

    return {
        "normalized_name": normalize_text(payload.name.full_name),
        "normalized_entity_type": payload.entity_type.value.lower(),
        "dob": payload.dob.isoformat() if payload.dob else None,
        "identifiers": normalized_identifiers,
        "addresses": normalized_addresses,
        "countries": sorted(set(countries)),
        "screening_lists": list(payload.screening_lists),
    }
