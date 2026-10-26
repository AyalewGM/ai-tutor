"""Signed, finite content pools using existing Problems and authorization metadata.

Keys belong to deployment configuration, never packages or client requests.
No learner records, mathematical generators or scoring engines are created here.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import uuid
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy import select

from app.content_models import ProblemContentMetadata
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping, ProblemFamily
from app.models import Curriculum, Problem, Skill
from app.services.fraction_assessment_registry import AssessmentMode, score_fraction
from app.services.fraction_scoring_handoff import ScoringDecision

SCHEMA = "MIHUR_CONTENT_PACKAGE_V1"
SCORER = "EXACT_VARIABLE_RATIONAL_V1"
FAMILY = "TWO_STEP_SIGNED_RATIONAL"
GENERATOR = "scripts/author_ontario_linear_depth.py"
ROLES = frozenset({"math", "pedagogy", "standards", "security", "qa", "release"})
MODE_COLUMNS = {
    "guided": "guided_eligible", "independent": "independent_eligible",
    "diagnostic": "diagnostic_eligible", "mastery": "mastery_eligible",
}
ROOT = Path(__file__).resolve().parents[2]
RUNTIME_FILES = (
    "app/services/content_publishing.py", "app/services/fraction_assessment_registry.py",
    "app/services/fraction_scoring_handoff.py", "app/services/attempt_evidence.py",
    "app/services/problem_selection.py", "app/adaptive_response_api.py", "app/diagnostic_api.py",
    "app/api.py", "scripts/ops/publish_content.py", "scripts/ops/content_learner_probe.py",
    "deploy/staging/publish_content.py", ".github/workflows/content-publisher.yml",
)


def runtime_digest():
    return digest({path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                   for path in RUNTIME_FILES})


class PublicationBlocked(ValueError):
    """Credential-free operator explanation."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def validate(manifest, *, require_approvals=True):
    required = {
        "schema", "package_id", "family_id", "content_revision", "generator_sha256",
        "canonical_skill", "curriculum", "curriculum_version", "local_skill", "modes",
        "scorer", "activation", "seed_count", "author_principals", "review_evidence",
        "runtime_sha256",
    }
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise PublicationBlocked("Manifest fields do not match V1 schema")
    if (
        manifest["schema"] != SCHEMA or manifest["family_id"] != FAMILY
        or manifest["canonical_skill"] != "MATH.EE.EQUATION.TWO"
        or manifest["curriculum"] != "MTH1W" or manifest["curriculum_version"] != "2021"
        or manifest["local_skill"] != "MTH1W.C.ALG.EQ2" or manifest["scorer"] != SCORER
        or manifest["package_id"] != "mth1w-signed-two-step-v1"
        or manifest["activation"] not in {"pending", "staging"}
        or not isinstance(manifest["modes"], list) or not manifest["modes"]
        or not all(isinstance(m, str) for m in manifest["modes"])
        or len(set(manifest["modes"])) != len(manifest["modes"])
        or not set(manifest["modes"]) <= {"diagnostic", "guided", "independent"}
        or type(manifest["seed_count"]) is not int or not 2 <= manifest["seed_count"] <= 100
        or not isinstance(manifest["author_principals"], list) or not manifest["author_principals"]
        or not all(isinstance(p, str) and p for p in manifest["author_principals"])
    ):
        raise PublicationBlocked("Unsupported identity, scope, modes or activation")
    revision = manifest["content_revision"]
    if not isinstance(revision, str) or len(revision) != 40 or any(
        c not in "0123456789abcdef" for c in revision
    ):
        raise PublicationBlocked("Exact content commit SHA required")
    if hashlib.sha256((ROOT / GENERATOR).read_bytes()).hexdigest() != manifest["generator_sha256"]:
        raise PublicationBlocked("Reviewed generator bytes differ from deployed content")
    if manifest["runtime_sha256"] != runtime_digest():
        raise PublicationBlocked("Runtime contract differs from reviewed package")
    if not isinstance(manifest["review_evidence"], list):
        raise PublicationBlocked("Review evidence must be a list")
    payload = {k: v for k, v in manifest.items() if k != "review_evidence"}
    if not require_approvals:
        return digest(payload)
    if manifest["activation"] != "staging":
        raise PublicationBlocked("Package pending; staging authorization required")
    try:
        policy_path = os.environ.get("MIHUR_CONTENT_REVIEW_POLICY_FILE")
        policy = json.loads(Path(policy_path).read_text()) if policy_path else json.loads(
            os.environ.get("MIHUR_CONTENT_REVIEW_POLICY", "{}"))
        keys = policy["keys"]
        if set(manifest["author_principals"]) != set(policy["authors"][manifest["generator_sha256"]]):
            raise PublicationBlocked("Authors must match deployment-owned provenance policy")
    except (ValueError, KeyError, OSError, TypeError) as exc:
        raise PublicationBlocked("Invalid deployment review-key configuration") from exc
    covered = set()
    for evidence in manifest["review_evidence"]:
        try:
            if set(evidence) != {"role", "key_id", "evidence_url", "signature"}:
                raise ValueError
            role = evidence["role"]
            key = keys[evidence["key_id"]]
            if (
                role not in ROLES or role in covered or role not in key["roles"]
                or key["principal"] in manifest["author_principals"]
                or not evidence["evidence_url"].startswith("https://github.com/AyalewGM/ai-tutor/")
            ):
                raise ValueError
            message = canonical({"manifest": payload, "role": role,
                                 "evidence_url": evidence["evidence_url"]})
            Ed25519PublicKey.from_public_bytes(base64.b64decode(key["public_key"], validate=True))\
                .verify(base64.b64decode(evidence["signature"], validate=True), message)
            covered.add(role)
        except (KeyError, ValueError, TypeError, InvalidSignature) as exc:
            raise PublicationBlocked("Invalid, untrusted, author-owned or duplicate review") from exc
    if covered != ROLES:
        raise PublicationBlocked("Missing independent gates: " + ", ".join(sorted(ROLES - covered)))
    return digest(payload)


def candidates(manifest):
    from scripts.author_ontario_linear_depth import create_candidate

    result, fingerprints = [], set()
    for mode in manifest["modes"]:
        count = 0
        for seed in range(10000):
            item = create_candidate(FAMILY, seed=f"publisher-v1:{seed}", mode=mode.upper())
            if item["task_fingerprint"] in fingerprints:
                continue
            fingerprints.add(item["task_fingerprint"])
            result.append((mode, item))
            count += 1
            if count == manifest["seed_count"]:
                break
        if count != manifest["seed_count"]:
            raise PublicationBlocked("Unable to build disjoint mode pools")
    return result


def resolve_skill(db, manifest):
    row = db.execute(
        select(Skill, CanonicalSkill).join(Curriculum, Curriculum.id == Skill.curriculum_id)
        .join(CurriculumSkillMapping, CurriculumSkillMapping.skill_id == Skill.id)
        .join(CanonicalSkill, CanonicalSkill.id == CurriculumSkillMapping.canonical_skill_id)
        .where(Curriculum.code == manifest["curriculum"],
               Curriculum.version == manifest["curriculum_version"], Curriculum.active.is_(True),
               Skill.code == manifest["local_skill"],
               CanonicalSkill.code == manifest["canonical_skill"])
    ).one_or_none()
    if row is None:
        raise PublicationBlocked("Active curriculum and existing canonical skill mapping required")
    return row


def expected_problem(manifest, mode, item, skill_id):
    package_digest = validate(manifest)
    return {
        "id": uuid.uuid5(uuid.NAMESPACE_URL, f"mihur:{package_digest}:{item['variant_id']}"),
        "primary_skill_id": skill_id, "problem_type": "PUBLISHED_RATIONAL", "difficulty": 3,
        "prompt": item["prompt"] + " Enter x=p/q (an exact fraction).",
        "canonical_answer": item["canonical_answer"], "answer_kind": "VARIABLE_VALUE",
        "source_type": "PUBLISHED", "choices": None,
        "solution": {"publisher": SCHEMA, "package_digest": package_digest,
                  "manifest": manifest, "mode": mode, "variant_id": item["variant_id"],
                  "task_fingerprint": item["task_fingerprint"], "problem_family": FAMILY},
    }


def publish(db, manifest):
    """Caller owns transaction and deployment preflight. Insert only; never overwrite."""
    validate(manifest)
    skill, canonical_skill = resolve_skill(db, manifest)
    family = db.scalar(select(ProblemFamily).where(ProblemFamily.code == FAMILY))
    if family is None:
        db.add(ProblemFamily(code=FAMILY, name="Signed exact-rational two-step equations",
                             canonical_skill_id=canonical_skill.id, generator_key=GENERATOR,
                             active=True))
    elif (not family.active or family.canonical_skill_id != canonical_skill.id
          or family.generator_key != GENERATOR):
        raise PublicationBlocked("Canonical family registration conflict")
    for mode, item in candidates(manifest):
        values = expected_problem(manifest, mode, item, skill.id)
        problem = db.get(Problem, values["id"])
        if problem is not None:
            if any(getattr(problem, k) != v for k, v in values.items()):
                raise PublicationBlocked("Existing variant differs; refusing to overwrite")
            if not permitted(db, problem, mode):
                raise PublicationBlocked("Existing variant disabled; new reviewed release required")
            continue
        problem = Problem(**values)
        db.add(problem)
        db.flush()
        db.add(ProblemContentMetadata(
            problem_id=problem.id, curriculum_id=skill.curriculum_id,
            objective="Approved signed exact-rational equation practice", evaluation_type=SCORER,
            extension_eligible=False, llm_solution_required=False,
            **{column: key == mode for key, column in MODE_COLUMNS.items()},
            provenance_json={"publisher": SCHEMA, "package_digest": values["solution"]["package_digest"]},
        ))
    db.flush()
    return report(db, manifest)


def permitted(db, problem, mode):
    if problem.source_type != "PUBLISHED":
        return True
    try:
        manifest = problem.solution["manifest"]
        validate(manifest)
        skill, canonical_skill = resolve_skill(db, manifest)
        family = db.scalar(select(ProblemFamily).where(ProblemFamily.code == FAMILY))
        if (family is None or not family.active or family.canonical_skill_id != canonical_skill.id
            or family.generator_key != GENERATOR):
            return False
        if mode not in manifest["modes"] or problem.solution["mode"] != mode:
            return False
        meta = db.scalar(select(ProblemContentMetadata).where(
            ProblemContentMetadata.problem_id == problem.id))
        if (meta is None or meta.extension_eligible or meta.evaluation_type != SCORER
            or not getattr(meta, MODE_COLUMNS[mode])):
            return False
        for candidate_mode, item in candidates(manifest):
            if candidate_mode == mode and item["variant_id"] == problem.solution["variant_id"]:
                expected = expected_problem(manifest, mode, item, skill.id)
                return all(getattr(problem, k) == v for k, v in expected.items())
    except (PublicationBlocked, KeyError, TypeError, AttributeError, OSError):
        return False
    return False


def score_published(db, problem, answer, mode, *, assisted):
    if (problem.source_type != "PUBLISHED" or not isinstance(mode, AssessmentMode)
        or not permitted(db, problem, mode.value)):
        raise PublicationBlocked("Published item is not authorized for this session mode")
    correct = score_fraction(answer, problem.canonical_answer, variable="x")
    return ScoringDecision(True, correct, correct and not assisted and mode in {
        AssessmentMode.INDEPENDENT, AssessmentMode.MASTERY})


def report(db, manifest):
    skill, _ = resolve_skill(db, manifest)
    package_digest = validate(manifest, require_approvals=False)
    rows = db.scalars(select(Problem).where(Problem.primary_skill_id == skill.id,
                                          Problem.source_type == "PUBLISHED")).all()
    rows = [p for p in rows if (p.solution or {}).get("package_digest") == package_digest]
    return {"skill": skill.code, "package_digest": package_digest, "stored": len(rows),
            "generated": len(rows), "authorized": sum(permitted(db, p, p.solution["mode"]) for p in rows),
            "learner_selectable": {mode: sum(permitted(db, p, mode) for p in rows)
                                   for mode in manifest["modes"]},
            "staging_learner_verified": False}


def rollback(db, package_digest):
    """Disable package flags only; retain every variant and all learner evidence."""
    count = 0
    for meta in db.scalars(select(ProblemContentMetadata).join(
        Problem, Problem.id == ProblemContentMetadata.problem_id
    ).where(Problem.source_type == "PUBLISHED")):
        if (meta.provenance_json or {}).get("package_digest") == package_digest:
            for column in MODE_COLUMNS.values():
                setattr(meta, column, False)
            count += 1
    db.flush()
    return count
