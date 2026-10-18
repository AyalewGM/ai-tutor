"""Fail-closed compatibility authorization for reviewed legacy catalogs.

Legacy seeders predate per-problem mode metadata. Compatibility is granted
only when the complete ordinary curated catalog for a curriculum/version
matches an immutable content snapshot reviewed at the commit recorded below.
An added, removed, or edited task changes the snapshot and leaves every new
metadata-free row unauthorized. Provenance strings alone are never authority.

Existing metadata remains authoritative and is never widened or replaced.
Draft, generated, extension, QA-only, inactive, partial, and unknown catalogs
remain fail closed.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Collection
from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.content_models import ProblemContentMetadata
from app.models import Curriculum, Problem, Skill

ACTIVE_CATALOG_POLICY_VERSION = "REVIEWED_CATALOG_SNAPSHOT_V2_20261018"
REVIEWED_CATALOG_SOURCE_COMMIT = "ecb8ad8d6e0acf5388e03bbc6dea14a9f5bb2913"
_AUTHORIZED_ORIGIN = "AUTHORED"
_AUTHORIZED_AUTHOR = "AI Tutor curriculum team"
_AUTHORIZED_LICENSES = frozenset({"proprietary"})
_QA_ONLY_SKILL_CODES = frozenset({"M8.PROB.MARBLE_QA"})


@dataclass(frozen=True, order=True)
class CatalogSnapshot:
    problem_count: int
    digest: str


# Generated from a fresh two-pass execution of scripts/ops/seed_all_curricula.py
# at REVIEWED_CATALOG_SOURCE_COMMIT. The two smaller MCPS snapshots are the
# exact standalone seed_sprint1/seed_grade7 catalogs used by CI and local
# pilot setup before the complete seed plan adds its reviewed companion rows.
_REVIEWED_CATALOG_SNAPSHOTS: dict[tuple[str, str], frozenset[CatalogSnapshot]] = {
    ("DC_ALGEBRA_1_CCSS_M", "CCSS-M-2010"): frozenset(
        {CatalogSnapshot(10, "782b834f1c2aeec63f9e4b48602a6dc98f5c04199aca62336fbabb088067a5bc")}
    ),
    ("DC_MATH_1_2024_25", "CCSS-OSSE-2024-25"): frozenset(
        {CatalogSnapshot(64, "b9ff6db929450f94cacd2a8216b13e46f99648ec34c3961565da8c8912f04750")}
    ),
    ("DC_MATH_2_2024_25", "CCSS-OSSE-2024-25"): frozenset(
        {CatalogSnapshot(72, "21d0208dfb04fa93095d997da74e1ba12c2f8e2edac5199af252bb2b90f3f0b5")}
    ),
    ("DC_MATH_3_2024_25", "CCSS-OSSE-2024-25"): frozenset(
        {CatalogSnapshot(72, "32d3a78ad93db36b8f8b51468502ef998c0595dc5b6577c177196bb3f194c5b3")}
    ),
    ("DC_MATH_4_2024_25", "CCSS-OSSE-2024-25"): frozenset(
        {CatalogSnapshot(80, "831a6a33ca06b21f89c0638adef0de8a10a8abd358ce555cbf12a06cfdb71ef1")}
    ),
    ("DC_MATH_5_2024_25", "CCSS-OSSE-2024-25"): frozenset(
        {CatalogSnapshot(72, "458ddb006ac17debe931f2267d0857e4b9f4909e0f3a66e8e3c130a8b12b223f")}
    ),
    ("DC_MATH_6", "CCSS-2010-v1"): frozenset(
        {CatalogSnapshot(10, "5ee7e40a9dc1b49b968b0ca41741f91fc1a1756adb08641c5e2c9a7d3df76462")}
    ),
    ("DC_MATH_7", "CCSS-2010-v1"): frozenset(
        {CatalogSnapshot(10, "7f5c49d4c94ba306a159b634e071500a6ac19076e2daf5b292212f9274636913")}
    ),
    ("MCPS_MATH_6", "MSDE-2026-27-v1"): frozenset(
        {CatalogSnapshot(21, "15b3a05271432d30f2617d5fed4295990fcb2ec06b43c3c5f7993276b18d76ed")}
    ),
    ("MCPS_MATH_7", "1"): frozenset(
        {
            CatalogSnapshot(42, "043007206307acea509b0522e98a5b230d7c6dd0060c1dff363fc74cdd1aa2a3"),
            CatalogSnapshot(51, "64b82a59596bee30c7f685b8250a44ddbb9bb9c16ee45bf522bdbb5138405d61"),
        }
    ),
    ("MCPS_MATH_8", "1"): frozenset(
        {
            CatalogSnapshot(22, "a8aaf61253a560c38b446f22b817688dbb33cd1d0d26585331b60371985609e8"),
            CatalogSnapshot(39, "6530d5611f51d2ce13e1eda84ff42a6d66a2e8ec1d19d1ffe32ff38c7f35e782"),
        }
    ),
    ("MCPS_ALGEBRA_1_2026_27", "SY2026-27"): frozenset(
        {CatalogSnapshot(50, "807f3c056742591f61a8665b32be9139728e51b9ae6c16d0754b70dab28cedbc")}
    ),
    ("MD_ALGEBRA_1_2026_27", "MCCRS-revised-SY2026-27"): frozenset(
        {CatalogSnapshot(62, "f767b89698a69d29188773d25f4c1b68f78fbf74c22ecca5bf9731ead22c2877")}
    ),
    (
        "MD_INTEGRATED_ALGEBRA_1_2027_28",
        "MCCRS-2025-INTEGRATED-ALGEBRA-1-SY2027-28",
    ): frozenset(
        {CatalogSnapshot(13, "1835851d4b7405ea2abaae842906a337f6aff1edd8de5f2b9d5946c7694f8f78")}
    ),
    ("MD_MATH_1_2026_27", "MCCRS-revised-SY2026-27"): frozenset(
        {CatalogSnapshot(64, "e5d636f8da1e411564cd25958a86c9a04a4b3d2269fbd5631a6cc70f12ded53a")}
    ),
    ("MD_MATH_2_2026_27", "MCCRS-revised-SY2026-27"): frozenset(
        {CatalogSnapshot(72, "3fb96abbd5181541c0b846579fc43b85872d022f8894917d8dce6c7655fc40b0")}
    ),
    ("MD_MATH_3_2026_27", "MCCRS-revised-SY2026-27"): frozenset(
        {CatalogSnapshot(72, "d61dd45f3443944d2c5c3de89a179d7c28340a0659818d1c952a344e1d8940b0")}
    ),
    ("MD_MATH_4_2026_27", "MCCRS-revised-SY2026-27"): frozenset(
        {CatalogSnapshot(80, "e645e5e45b9cb4b7ae52e2166e36b6379de8b2e18112bda080b41bb44ec51408")}
    ),
    ("MD_MATH_5_2026_27", "MCCRS-revised-SY2026-27"): frozenset(
        {CatalogSnapshot(72, "6305b3857d51405e2e50d09e79c1675064dcdc21a27605ba42ad5fb080fe87b8")}
    ),
    ("MTH1W", "2021"): frozenset(
        {
            CatalogSnapshot(48, "8adc88a5b17ff0062fd835e8b43ca20d9c26a75c376cbc284f1c4c97433917ea"),
            CatalogSnapshot(64, "b75f48729b5cb8e1d937f83425ae991e1863ff93605ab5e98c412985242f15cc"),
        }
    ),
    ("VA_ALGEBRA_1_SOL_2023", "SOL-2023-v1"): frozenset(
        {CatalogSnapshot(10, "a5df474bdf74adcb77239eeda908d81aaee2ac15dd737e302228b313e4f3935e")}
    ),
    ("VA_MATH_1_2024_25", "VDOE-2023-SY2024-25"): frozenset(
        {CatalogSnapshot(64, "c03105cba0165c8a2d0d1c3f7bc4c45130f979392d6f97af75ae930a86584e68")}
    ),
    ("VA_MATH_2_2024_25", "VDOE-2023-SY2024-25"): frozenset(
        {CatalogSnapshot(72, "05e6af76cdf8545024718b5b6987b6a80a4a69d7fa77a9ff05f63b078762a2c4")}
    ),
    ("VA_MATH_3_2024_25", "VDOE-2023-SY2024-25"): frozenset(
        {CatalogSnapshot(72, "902ff40ffd99f174e29075188055e7d9c0843412f61c54745fe51ba4e95a4d20")}
    ),
    ("VA_MATH_4_2024_25", "VDOE-2023-SY2024-25"): frozenset(
        {CatalogSnapshot(80, "4cad2cb5412ef1d82310ae8f8a6df89ec8d8c139f988eba9dbe99463fb58e6f4")}
    ),
    ("VA_MATH_5_2024_25", "VDOE-2023-SY2024-25"): frozenset(
        {CatalogSnapshot(72, "6750a533e5756648520bc873d45783751284ccb801e53f857a144c715ca61253")}
    ),
    ("VA_MATH_6", "SOL-2023-v1"): frozenset(
        {CatalogSnapshot(10, "28d169f9291d2796a3ec174c5a53246e0ec2bb752377d91ce6572c9d053d98e8")}
    ),
    ("VA_MATH_7", "SOL-2023-v1"): frozenset(
        {CatalogSnapshot(10, "905b0013754543010cda3f5e96fbde7ce34b2ac6fde2e97047ff1e72814dda29")}
    ),
}


def authorize_active_authored_catalog(
    db: Session,
    *,
    curriculum_codes: Collection[str] | None = None,
) -> int:
    """Authorize metadata-free rows only when their whole catalog snapshot matches.

    The caller owns the transaction. Existing metadata is included in the
    snapshot but remains untouched, so narrower reviewed eligibility wins.
    """

    stmt = (
        select(Problem, Skill, Curriculum, ProblemContentMetadata)
        .join(Skill, Skill.id == Problem.primary_skill_id)
        .join(Curriculum, Curriculum.id == Skill.curriculum_id)
        .outerjoin(
            ProblemContentMetadata,
            ProblemContentMetadata.problem_id == Problem.id,
        )
        .where(
            Curriculum.active.is_(True),
            Problem.source_type == "CURATED",
            Skill.code.not_in(_QA_ONLY_SKILL_CODES),
            or_(
                ProblemContentMetadata.id.is_(None),
                ProblemContentMetadata.extension_eligible.is_not(True),
            ),
        )
    )
    if curriculum_codes is not None:
        codes = tuple(sorted(set(curriculum_codes)))
        if not codes:
            return 0
        stmt = stmt.where(Curriculum.code.in_(codes))

    grouped: dict[
        tuple[str, str],
        list[tuple[Problem, Skill, Curriculum, ProblemContentMetadata | None]],
    ] = defaultdict(list)
    for problem, skill, curriculum, metadata in db.execute(stmt):
        grouped[(curriculum.code, curriculum.version)].append(
            (problem, skill, curriculum, metadata)
        )

    authorized = 0
    for catalog_key, records in grouped.items():
        snapshot = _catalog_snapshot(records)
        if snapshot not in _REVIEWED_CATALOG_SNAPSHOTS.get(catalog_key, frozenset()):
            continue
        for problem, _skill, curriculum, metadata in records:
            if metadata is not None:
                continue
            provenance = (problem.solution or {}).get("provenance")
            if not _is_authorized_provenance(provenance):
                continue
            db.add(
                ProblemContentMetadata(
                    problem_id=problem.id,
                    curriculum_id=curriculum.id,
                    objective="Reviewed legacy catalog compatibility authorization.",
                    evaluation_type="EXACT_OR_DECLARED_CANONICAL",
                    diagnostic_eligible=True,
                    guided_eligible=True,
                    independent_eligible=True,
                    mastery_eligible=True,
                    extension_eligible=False,
                    llm_solution_required=False,
                    provenance_json={
                        "policy": ACTIVE_CATALOG_POLICY_VERSION,
                        "scope": "EXACT_REVIEWED_CATALOG_SNAPSHOT",
                        "catalog_problem_count": snapshot.problem_count,
                        "catalog_digest": snapshot.digest,
                        "reviewed_source_commit": REVIEWED_CATALOG_SOURCE_COMMIT,
                        "history_policy": "INSERT_METADATA_ONLY",
                        "new_draft_authorization": False,
                    },
                )
            )
            authorized += 1

    if authorized:
        db.flush()
    return authorized


def _catalog_snapshot(
    records: Collection[tuple[Problem, Skill, Curriculum, ProblemContentMetadata | None]],
) -> CatalogSnapshot:
    fingerprints = sorted(
        _problem_fingerprint(problem=problem, skill=skill, curriculum=curriculum)
        for problem, skill, curriculum, _metadata in records
    )
    digest = hashlib.sha256("\n".join(fingerprints).encode()).hexdigest()
    return CatalogSnapshot(problem_count=len(fingerprints), digest=digest)


def _problem_fingerprint(*, problem: Problem, skill: Skill, curriculum: Curriculum) -> str:
    payload = {
        "curriculum_code": curriculum.code,
        "curriculum_version": curriculum.version,
        "skill_code": skill.code,
        "problem_type": problem.problem_type,
        "difficulty": problem.difficulty,
        "prompt": problem.prompt,
        "canonical_answer": problem.canonical_answer,
        "choices": problem.choices,
        "solution": problem.solution,
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _is_authorized_provenance(provenance: object) -> bool:
    if not isinstance(provenance, dict):
        return False
    return (
        provenance.get("origin") == _AUTHORIZED_ORIGIN
        and provenance.get("author") == _AUTHORIZED_AUTHOR
        and provenance.get("license") in _AUTHORIZED_LICENSES
    )
