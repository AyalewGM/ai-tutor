"""Ed25519-verified release declarations, without any signing authority.

Only a separately controlled release authority may possess the private signing
key. The backend receives the pinned public key via trusted deployment config.
No bundled key, implicit approval, fallback registry or learner writes.
"""
from __future__ import annotations

import hmac
import json
from dataclasses import asdict, dataclass
from typing import Final

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.services.family_activation_adapter import (
    SCHEMA_VERSION,
    FamilyRegistration,
    compile_registration,
)

_MAX_FAMILIES: Final[int] = 512


def canonical_release_payload(
    *,
    key_id: str,
    registrations: tuple[FamilyRegistration, ...],
) -> bytes:
    """Deterministic signed bytes covering every requested family, mode and gate."""
    if not isinstance(key_id, str) or not 1 <= len(key_id) <= 128:
        raise ValueError("invalid release key ID")
    if not isinstance(registrations, tuple) or len(registrations) > _MAX_FAMILIES:
        raise ValueError("invalid family count")
    compile_registration(SCHEMA_VERSION, registrations)
    records = []
    for entry in registrations:
        records.append({
            "family_id": entry.family.family_id,
            "canonical_skill_code": entry.family.canonical_skill_code,
            "content_sha": entry.family.content_sha,
            "modes": sorted(mode.value for mode in entry.family.modes),
            "answer_kind": entry.family.answer_kind.value,
            "scorer_revision": entry.scorer_revision,
            "source_mapping_revision": entry.source_mapping_revision,
            "review_evidence": asdict(entry.evidence),
        })
    return json.dumps(
        {"schema": SCHEMA_VERSION, "key_id": key_id, "registrations": records},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")


@dataclass(frozen=True)
class SignedReleaseDeclaration:
    key_id: str
    registrations: tuple[FamilyRegistration, ...]
    signature: bytes


class PinnedPublicKeyApprovalSource:
    """Offline verified records bound to a deployment-pinned signer and principal."""

    def __init__(
        self, *,
        trusted_key_id: str,
        public_key_bytes: bytes,
        trusted_service_principal: str,
        declaration: SignedReleaseDeclaration,
    ) -> None:
        if (
            not isinstance(trusted_service_principal, str)
            or not trusted_service_principal.strip()
            or not isinstance(declaration, SignedReleaseDeclaration)
            or not isinstance(public_key_bytes, bytes)
            or not isinstance(declaration.signature, bytes)
            or not hmac.compare_digest(trusted_key_id, declaration.key_id)
        ):
            raise ValueError("invalid release verifier configuration")
        self._principal = trusted_service_principal
        self._declaration = declaration
        self._public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)

    def approved_records(self, *, service_principal: str) -> tuple[FamilyRegistration, ...]:
        if (
            not isinstance(service_principal, str)
            or not hmac.compare_digest(self._principal, service_principal)
        ):
            raise PermissionError("unrecognized release service principal")
        payload = canonical_release_payload(
            key_id=self._declaration.key_id,
            registrations=self._declaration.registrations,
        )
        try:
            self._public_key.verify(self._declaration.signature, payload)
        except (InvalidSignature, ValueError) as exc:
            raise PermissionError("release signature invalid") from exc
        return self._declaration.registrations
