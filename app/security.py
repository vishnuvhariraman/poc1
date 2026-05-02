import hashlib
import hmac

from app.config import settings


def hmac_identifier(value: str) -> str:
    return hmac.new(
        settings.hmac_secret.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
