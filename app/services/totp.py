"""RFC 6238 TOTP (30-second, 6-digit, SHA-1) — compatible with Google
Authenticator, 1Password, Authy, and Microsoft Authenticator.

Implemented on the standard library so the second factor has no extra
dependency surface.
"""

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

PERIOD_SECONDS = 30
DIGITS = 6
# Accept one step either side to absorb clock drift on the admin's phone.
DRIFT_STEPS = 1


def generate_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def _code_at(secret: str, step: int) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    digest = hmac.new(key, struct.pack(">Q", step), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(value % 10**DIGITS).zfill(DIGITS)


def current_step(now: float | None = None) -> int:
    return int((time.time() if now is None else now) // PERIOD_SECONDS)


def verify(
    secret: str, code: str, *, last_used_step: int | None = None, now: float | None = None
) -> int | None:
    """Return the matched time step, or None.

    Steps at or before ``last_used_step`` are rejected so a code observed
    once (shoulder-surfed, phished) cannot be replayed.
    """
    code = (code or "").strip().replace(" ", "")
    if len(code) != DIGITS or not code.isdigit():
        return None
    step = current_step(now)
    for candidate in range(step - DRIFT_STEPS, step + DRIFT_STEPS + 1):
        if last_used_step is not None and candidate <= last_used_step:
            continue
        if hmac.compare_digest(_code_at(secret, candidate), code):
            return candidate
    return None


def provisioning_uri(secret: str, account: str, issuer: str = "Mihur Admin") -> str:
    label = quote(f"{issuer}:{account}")
    return (
        f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}"
        f"&algorithm=SHA1&digits={DIGITS}&period={PERIOD_SECONDS}"
    )
