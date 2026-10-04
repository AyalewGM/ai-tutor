import base64

from app.services import totp
from app.services.permissions import Permission, has_permission, permissions_for

# RFC 6238 Appendix B: ASCII "12345678901234567890", SHA-1, T=59s -> 94287082.
RFC_SECRET = base64.b32encode(b"12345678901234567890").decode().rstrip("=")


def test_totp_matches_rfc6238_vector() -> None:
    assert totp._code_at(RFC_SECRET, 59 // 30) == "287082"  # last 6 of 94287082
    assert totp.verify(RFC_SECRET, "287082", now=59) == 1


def test_totp_rejects_replay_wrong_and_malformed_codes() -> None:
    step = totp.verify(RFC_SECRET, "287082", now=59)
    assert totp.verify(RFC_SECRET, "287082", last_used_step=step, now=59) is None
    assert totp.verify(RFC_SECRET, "000000", now=59) is None
    assert totp.verify(RFC_SECRET, "28708", now=59) is None
    assert totp.verify(RFC_SECRET, "abcdef", now=59) is None


def test_totp_tolerates_one_step_of_clock_drift_only() -> None:
    code = totp._code_at(RFC_SECRET, 10)
    assert totp.verify(RFC_SECRET, code, now=11 * 30) == 10
    assert totp.verify(RFC_SECRET, code, now=12 * 30) is None


def test_generated_secret_round_trips_and_uri_is_scannable() -> None:
    secret = totp.generate_secret()
    assert totp.verify(secret, totp._code_at(secret, totp.current_step())) is not None
    uri = totp.provisioning_uri(secret, "admin@example.com")
    assert uri.startswith("otpauth://totp/") and f"secret={secret}" in uri


def test_only_staff_roles_hold_permissions() -> None:
    assert has_permission("ADMIN", Permission.ADMIN_ACCESS)
    assert has_permission("admin", Permission.PLANS_MANAGE)
    for role in ("PARENT", "GUARDIAN", "STAFF_REVOKED", "", None):
        assert permissions_for(role) == frozenset()
