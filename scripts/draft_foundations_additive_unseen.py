"""Draft-only unseen additive word-problem variants for Grades 2–5 review.

This authoring generator is isolated from the learner runtime. It does not
publish canonical identities, award mastery, or implement trusted scoring.
"""

from __future__ import annotations

import argparse
import json
import random

STATUS = "DRAFT_UNVERIFIED"
REVIEW_STATUS = "PENDING_INDEPENDENT_REVIEW"

STRUCTURES = (
    "result-unknown",
    "change-unknown",
    "start-unknown",
    "comparison-difference",
    "comparison-smaller-unknown",
    "comparison-larger-unknown",
    "two-change-unknown",
    "part-part-whole",
)

_SOURCE_IDS = {
    structure: f"draft-structures-additive_word_problems-{index:02d}"
    for index, structure in enumerate(STRUCTURES, start=1)
}

_CONTEXTS = (
    ("community pantry", "meal kits", "kits"),
    ("school garden", "seedling trays", "trays"),
    ("mobile library", "activity packs", "packs"),
    ("recycling centre", "sorted containers", "containers"),
)


def _diagnostic_routes(structure: str) -> list[dict]:
    shared = {
        "unknown_position": {
            "classification": "UNKNOWN_POSITION_CONFUSION",
            "evidence": "Learner calculates with the two visible numbers before naming the unknown.",
            "socratic_questions": [
                "Which quantity is unknown: the beginning, a change, a part, or the whole?",
                "Where would that unknown sit in a tape diagram?",
                "What equation preserves the relationship before you calculate?",
            ],
        },
        "surface_word": {
            "classification": "SURFACE_WORD_OPERATION",
            "evidence": "Learner chooses an operation from a keyword rather than the relationship.",
            "socratic_questions": [
                "What happened to the quantity in the story?",
                "Which amount contains the other amount?",
                "How can substitution check that your equation matches the story?",
            ],
        },
    }
    specific = {
        "result-unknown": {
            "classification": "CHANGE_TREATED_AS_TOTAL",
            "evidence": "Learner reports the added amount as the final total.",
            "socratic_questions": [
                "What amount was present before the change?",
                "How does the incoming amount alter that starting amount?",
                "Can the final amount equal only the incoming part? Why or why not?",
            ],
        },
        "change-unknown": {
            "classification": "START_PLUS_END",
            "evidence": "Learner adds the starting and ending amounts.",
            "socratic_questions": [
                "Which amount already includes the delivery?",
                "What part of the final amount was present at the start?",
                "What number added to the start reconstructs the final amount?",
            ],
        },
        "start-unknown": {
            "classification": "END_PLUS_CHANGE",
            "evidence": "Learner adds the change to the already-changed final amount.",
            "socratic_questions": [
                "Did the delivery happen before or after the unknown amount?",
                "Which bar is the whole after the delivery?",
                "What beginning plus the delivery recreates that whole?",
            ],
        },
        "comparison-difference": {
            "classification": "COMBINED_INSTEAD_OF_DIFFERENCE",
            "evidence": "Learner combines both collections instead of finding the gap.",
            "socratic_questions": [
                "Does the question ask for both collections together or the gap between them?",
                "What part remains when equal portions of the two bars are aligned?",
                "How can adding the gap to the smaller amount verify the larger amount?",
            ],
        },
        "comparison-smaller-unknown": {
            "classification": "MORE_RELATION_REVERSED",
            "evidence": "Learner adds the difference to the already larger amount.",
            "socratic_questions": [
                "Which named collection is larger?",
                "Does the unknown bar include or exclude the extra segment?",
                "What smaller amount plus the difference equals the larger amount?",
            ],
        },
        "comparison-larger-unknown": {
            "classification": "FEWER_RELATION_REVERSED",
            "evidence": "Learner subtracts the difference from the smaller amount.",
            "socratic_questions": [
                "Which collection has fewer items?",
                "What extra segment must be added to reach the larger collection?",
                "How can subtraction from the larger amount verify the smaller amount?",
            ],
        },
        "two-change-unknown": {
            "classification": "SECOND_CHANGE_SIGN_LOST",
            "evidence": "Learner treats both changes as increases or ignores the second change.",
            "socratic_questions": [
                "Which event increases the amount and which event decreases it?",
                "What intermediate amount exists after the first event?",
                "Can you reverse both changes to recover the start?",
            ],
        },
        "part-part-whole": {
            "classification": "ONE_KNOWN_PART_REMOVED",
            "evidence": "Learner subtracts only one known part from the whole.",
            "socratic_questions": [
                "How many disjoint parts make up the whole?",
                "Which parts are already known, and which part is unknown?",
                "Do the three parts recombine to the stated whole?",
            ],
        },
    }
    return [shared["unknown_position"], shared["surface_word"], specific[structure]]


def _build(structure: str, variant: int, seed: int) -> dict:
    rng = random.Random(f"mihur-foundations-additive-unseen-v1:{seed}:{structure}:{variant}")
    place, collection, unit = _CONTEXTS[rng.randrange(len(_CONTEXTS))]
    start = rng.randint(58, 480)
    increase = rng.randint(19, 170)
    final = start + increase

    if structure == "result-unknown":
        operands = {"start": start, "increase": increase}
        answer = final
        question = (
            f"A {place} begins the day with {start} {collection} and prepares {increase} "
            f"more. How many {collection} are ready now?"
        )
        operation = "add"
        relation = "start + increase = final"
        verify = {"substituted_left": start + increase, "substituted_right": answer}
    elif structure == "change-unknown":
        operands = {"start": start, "final": final}
        answer = increase
        question = (
            f"A {place} had {start} {collection} at first and later had {final}. "
            f"How many new {collection} were prepared?"
        )
        operation = "subtract"
        relation = "start + increase = final"
        verify = {"substituted_left": start + answer, "substituted_right": final}
    elif structure == "start-unknown":
        operands = {"increase": increase, "final": final}
        answer = start
        question = (
            f"After a {place} prepared {increase} additional {collection}, it had {final}. "
            f"How many {collection} did it have beforehand?"
        )
        operation = "subtract"
        relation = "start + increase = final"
        verify = {"substituted_left": answer + increase, "substituted_right": final}
    elif structure == "comparison-difference":
        smaller = rng.randint(45, 360)
        gap = rng.randint(16, 145)
        larger = smaller + gap
        operands = {"larger": larger, "smaller": smaller}
        answer = gap
        question = (
            f"One {place} prepared {larger} {collection}; another prepared {smaller}. "
            f"How many more {collection} did the first prepare?"
        )
        operation = "subtract"
        relation = "smaller + difference = larger"
        verify = {"substituted_left": smaller + answer, "substituted_right": larger}
    elif structure == "comparison-smaller-unknown":
        smaller = rng.randint(45, 360)
        gap = rng.randint(16, 145)
        larger = smaller + gap
        operands = {"larger": larger, "difference": gap}
        answer = smaller
        question = (
            f"A larger {place} collection has {larger} {collection}, which is {gap} more "
            f"than a smaller collection. How many {collection} are in the smaller collection?"
        )
        operation = "subtract"
        relation = "smaller + difference = larger"
        verify = {"substituted_left": answer + gap, "substituted_right": larger}
    elif structure == "comparison-larger-unknown":
        smaller = rng.randint(45, 360)
        gap = rng.randint(16, 145)
        larger = smaller + gap
        operands = {"smaller": smaller, "difference": gap}
        answer = larger
        question = (
            f"One {place} collection has {smaller} {collection}, which is {gap} fewer than "
            f"a larger collection. How many {collection} are in the larger collection?"
        )
        operation = "add"
        relation = "smaller + difference = larger"
        verify = {"substituted_left": smaller + gap, "substituted_right": answer}
    elif structure == "two-change-unknown":
        leave = rng.randint(10, min(120, start + increase - 1))
        answer = start + increase - leave
        operands = {"start": start, "increase": increase, "decrease": leave}
        question = (
            f"A {place} starts with {start} {collection}, prepares {increase} more, and sends "
            f"{leave} away. How many {collection} remain?"
        )
        operation = "add_subtract"
        relation = "start + increase - decrease = final"
        verify = {"substituted_left": answer + leave - increase, "substituted_right": start}
    elif structure == "part-part-whole":
        part_a = rng.randint(35, 170)
        part_b = rng.randint(25, 150)
        answer = rng.randint(20, 140)
        whole = part_a + part_b + answer
        operands = {"whole": whole, "known_part_a": part_a, "known_part_b": part_b}
        question = (
            f"A {place} sorted {whole} {collection}: {part_a} need labels and {part_b} need "
            f"repairs. The rest are ready to distribute. How many {collection} are ready?"
        )
        operation = "subtract_two_parts"
        relation = "known part A + known part B + unknown part = whole"
        verify = {
            "substituted_left": part_a + part_b + answer,
            "substituted_right": whole,
        }
    else:
        raise ValueError(f"unknown structure: {structure}")

    item_id = f"foundations-additive-unseen-{structure}-{seed}-{variant:02d}"
    return {
        "assessment_item_id": item_id,
        "linked_practice_item_id": _SOURCE_IDS[structure],
        "problem_structure": structure,
        "grade_band": "2-5_PROVISIONAL_NOT_STANDARDS_MAPPED",
        "status": STATUS,
        "review_status": REVIEW_STATUS,
        "runtime_activation": False,
        "learner_payload": {
            "assessment_item_id": item_id,
            "question": question,
            "response_contract": {
                "answer_kind": "integer_with_unit",
                "required_evidence": [
                    "name the unknown and write a relationship model",
                    f"give an exact answer in {unit}",
                    "verify by substituting the answer into the relationship",
                ],
            },
        },
        "learner_payload_contract": {
            "fields": ["assessment_item_id", "question", "response_contract"],
            "omit": [
                "exact_answer",
                "operands",
                "operation",
                "relation",
                "verification_evidence",
                "diagnostic_routes_server_only",
                "hints",
                "worked_solution",
            ],
        },
        "teacher_oracle_server_only": {
            "operation": operation,
            "operands": operands,
            "exact_answer": str(answer),
            "relation": relation,
            "verification_evidence": verify,
        },
        "diagnostic_routes_server_only": _diagnostic_routes(structure),
    }


def generate(seed: int = 20261011, variants_per_structure: int = 6) -> dict:
    """Return reproducible authored assessment candidates without runtime effects."""
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be an integer")
    if not isinstance(variants_per_structure, int) or isinstance(
        variants_per_structure, bool
    ):
        raise TypeError("variants_per_structure must be an integer")
    if not 1 <= variants_per_structure <= 20:
        raise ValueError("variants_per_structure must be between 1 and 20")
    return {
        "package_id": "draft-word-problem-structures-v0",
        "revision": "foundations-additive-unseen-generator-v1",
        "status": STATUS,
        "review_status": REVIEW_STATUS,
        "runtime_activation": False,
        "mastery_activation": False,
        "server_trusted_scoring": "PENDING_ASSESSMENT_BACKEND_IMPLEMENTATION",
        "canonical_skill_ids": [],
        "curriculum_mappings": [],
        "seed": seed,
        "variants_per_structure": variants_per_structure,
        "structure_count": len(STRUCTURES),
        "items": [
            _build(structure, variant, seed)
            for structure in STRUCTURES
            for variant in range(variants_per_structure)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261011)
    parser.add_argument("--variants", type=int, default=6)
    args = parser.parse_args()
    print(json.dumps(generate(args.seed, args.variants), indent=2))


if __name__ == "__main__":
    main()
