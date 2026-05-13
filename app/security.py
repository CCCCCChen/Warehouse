import hashlib
import secrets
from typing import Optional


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str, salt: Optional[str] = None) -> str:
    s = (salt or "").strip()
    raw = f"{s}:{token}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

