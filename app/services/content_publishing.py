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
PARTIAL_PRACTICE_ACCEPTANCE = "ACCEPTED_PARTIAL_PRACTICE"
STANDARDS_PROVENANCE = {
    "authority": "Ontario Ministry of Education",
    "document_title": "The Ontario Curriculum: Mathematics, Grade 9, De-streamed (MTH1W), 2021",
    "document_version": "Course issued 2021-06-09; teacher supports completed 2022-05-03; PDF copyright 2022",
    "official_course_url": "https://www.dcp.edu.gov.on.ca/en/curriculum/secondary-mathematics/courses/mth1w/c/c1",
    "official_pdf_url": "https://assets-us-01.kc-usercontent.com/fbd574c4-da36-0066-a0c5-849ffb2de96e/73cd68ae-6f54-46e4-85c6-73103f44875e/The%20Ontario%20Curriculum%20-%20Mathematics%20Grade%209%20De-streamed%20Course%202021_with%20Teacher%20Supports_v2.pdf",
    "access_date": "2026-10-25",
    "standard_id": "MTH1W.C1.5",
    "printed_pages": [
        118,
        119
    ],
    "disposition": "PARTIAL_NON_EXHAUSTIVE",
    "acceptance": "PROVISIONAL_NOT_ACCEPTED",
    "coverage_credit": False,
    "production_taxonomy_activation": False,
    "inclusions": [
        "signed two-step linear equations",
        "exact rational solutions"
    ],
    "exclusions": [
        "learner creation of equations from varied contexts",
        "contextual interpretation of solutions",
        "learner-performed solution verification",
        "MTH1W.C1.4 simplification coverage"
    ],
    "not_mapped": [
        {
            "standard_id": "MTH1W.C1.4",
            "disposition": "NOT_MAPPED"
        }
    ],
    "adaptation_rationale": "Official wording was consulted only to verify the expectation identifier and mathematical boundary; all package tasks and wording are original.",
    "source_review": {
        "url": "https://github.com/AyalewGM/ai-tutor/pull/489#issuecomment-6401201029",
        "reviewed_head": "b632d15febb623d90092527d9197dba7d726d7dc",
        "candidate_document_blob": "28bbe00dd7a5aa6bee780e01edf0d90ff92d4111",
        "generator_blob": "2b31031e20a114d1d37d2b9af465993243b2a836"
    }
}
MODE_COLUMNS = {
    "guided": "guided_eligible", "independent": "independent_eligible",
    "diagnostic": "diagnostic_eligible", "mastery": "mastery_eligible",
}
ROOT = Path(__file__).resolve().parents[2]
RUNTIME_FILES = (
    "app/services/content_publishing.py", "app/services/fraction_assessment_registry.py",
    "app/services/fraction_scoring_handoff.py", "app/services/attempt_evidence.py",
    "app/services/awards.py", "app/services/problem_selection.py", "app/services/published_reasoning_probe.py",
    "app/adaptive_response_api.py", "app/hint_api.py", "app/workspace_api.py",
    "app/identity.py", "app/diagnostic_api.py",
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


def _bounded_standards_provenance(provenance):
    """Source fit for practice is distinct from full expectation/coverage approval.

    The accepted partial disposition is still inside the six-role signed manifest;
    this function grants no authority to an unsigned or provisional package.
    """
    return (
        isinstance(provenance, dict)
        and provenance in (
            STANDARDS_PROVENANCE,
            {**STANDARDS_PROVENANCE, "acceptance": PARTIAL_PRACTICE_ACCEPTANCE},
        )
        and provenance.get("coverage_credit") is False
        and provenance.get("production_taxonomy_activation") is False
    )


def validate(manifest, *, require_approvals=True):
    required = {
        "schema", "package_id", "family_id", "content_revision", "generator_sha256",
        "canonical_skill", "curriculum", "curriculum_version", "local_skill", "modes",
        "scorer", "activation", "seed_count", "author_principals", "review_evidence",
        "runtime_sha256", "standards_provenance",
    }
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise PublicationBlocked("Manifest fields do not match V1 schema")
    if (
        manifest["schema"] != SCHEMA or manifest["family_id"] != FAMILY
        or manifest["canonical_skill"] != "MATH.EE.EQUATION.TWO"
        or manifest["curriculum"] != "MTH1W" or manifest["curriculum_version"] != "2021"
        or manifest["local_skill"] != "MTH1W.C.ALG.EQ2" or manifest["scorer"] != SCORER
        or manifest["package_id"] != "mth1w-signed-two-step-v1"
        or not _bounded_standards_provenance(manifest["standards_provenance"])
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
    if manifest["standards_provenance"].get("acceptance") != PARTIAL_PRACTICE_ACCEPTANCE:
        raise PublicationBlocked("Bounded practice standards disposition not independently accepted")
    if manifest["activation"] != "staging":
        raise PublicationBlocked("Package pending; staging authorization required")
    try:
        policy_path = os.environ.get("MIHUR_CONTENT_REVIEW_POLICY_FILE")
        policy = json.loads(Path(policy_path).read_text()) if policy_path else json.loads(
            os.environ.get("MIHUR_CONTENT_REVIEW_POLICY", "{}"))
        keys = policy["keys"]
        generator_authors = policy["authors"][manifest["generator_sha256"]]
        runtime_authors = policy["runtime_authors"][manifest["runtime_sha256"]]
        if not all(isinstance(values, list) and values and
                   all(isinstance(principal, str) and principal for principal in values)
                   for values in (generator_authors, runtime_authors)):
            raise ValueError("Invalid author provenance")
        if set(manifest["author_principals"]) != set(generator_authors) | set(runtime_authors):
            raise PublicationBlocked("Authors must match deployment-owned provenance policy")
    except (ValueError, KeyError, OSError, TypeError) as exc:
        raise PublicationBlocked("Invalid deployment review-key configuration") from exc
    covered, reviewer_principals, reviewer_keys = set(), set(), set()
    for evidence in manifest["review_evidence"]:
        try:
            if set(evidence) != {"role", "key_id", "evidence_url", "signature"}:
                raise ValueError
            role = evidence["role"]
            key = keys[evidence["key_id"]]
            principal = key["principal"]
            public_key = base64.b64decode(key["public_key"], validate=True)
            if (
                role not in ROLES or role in covered or role not in key["roles"]
                or not isinstance(principal, str) or not principal
                or principal in manifest["author_principals"]
                or principal in reviewer_principals or public_key in reviewer_keys
                or not evidence["evidence_url"].startswith("https://github.com/AyalewGM/ai-tutor/")
            ):
                raise ValueError
            message = canonical({"manifest": payload, "role": role,
                                 "evidence_url": evidence["evidence_url"]})
            Ed25519PublicKey.from_public_bytes(public_key)\
                .verify(base64.b64decode(evidence["signature"], validate=True), message)
            covered.add(role)
            reviewer_principals.add(principal)
            reviewer_keys.add(public_key)
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
            provenance_json={
                "publisher": SCHEMA,
                "package_digest": values["solution"]["package_digest"],
                "standards": manifest["standards_provenance"],
            },
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
    # Correctness alone is not proof of independently issued, unassisted,
    # replay-safe work. Only the established mastery evidence pipeline may
    # authorize credit after trusted journey verification.
    return ScoringDecision(True, correct, False)


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
