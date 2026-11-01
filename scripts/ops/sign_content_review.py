"""Offline reviewer utility. Never generates keys or awards a review automatically."""
import argparse
import base64
import json
from pathlib import Path

from cryptography.hazmat.primitives.serialization import load_pem_private_key

from app.services.content_publishing import ROLES, canonical, validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--role", choices=sorted(ROLES), required=True)
    parser.add_argument("--key-id", required=True)
    parser.add_argument("--evidence-url", required=True)
    parser.add_argument("--private-key", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    validate(manifest, require_approvals=False)
    if manifest["activation"] != "staging":
        parser.error("Review the staging manifest; change activation before collecting signatures")
    key = load_pem_private_key(args.private_key.read_bytes(), password=None)
    payload = {k: v for k, v in manifest.items() if k != "review_evidence"}
    signature = key.sign(canonical({"manifest": payload, "role": args.role,
                                    "evidence_url": args.evidence_url}))
    manifest["review_evidence"] = [e for e in manifest["review_evidence"] if e["role"] != args.role]
    manifest["review_evidence"].append({"role": args.role, "key_id": args.key_id,
        "evidence_url": args.evidence_url, "signature": base64.b64encode(signature).decode()})
    # Exclusive create avoids silently replacing an existing reviewed artifact.
    with args.output.open("x") as output:
        output.write(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
