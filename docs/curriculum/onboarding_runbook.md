# Curriculum onboarding runbook

This runbook is the operating procedure for adding a U.S. state or Canadian province to Mihur without forking mathematical truth.

## Principle

Implement mathematics once; map curricula many times. A jurisdiction may define its own standards, terminology, sequence, coverage, version, and authority. It must not receive a new validator, Math Visual Engine framework, mastery algorithm, or problem family merely because its curriculum code differs.

## Onboarding procedure

1. Register the jurisdiction and authoritative education authority with official source provenance.
2. Register the curriculum identity/version. Do not infer or invent official identifiers.
3. Extract standards or expectations from the authoritative source into the versioned ingestion-pack contract.
4. Propose mappings to existing CanonicalSkill identities. Unknown or ambiguous mappings fail closed and go to review; ingestion must not invent canonical mathematics.
5. Run deterministic pack validation before any database write.
6. Ingest as DRAFT. Re-running the same pack must be idempotent.
7. Review every proposed mapping against the authoritative source. Publication requires a named human reviewer, source URI, and review basis.
8. Publish mappings, then publish the curriculum version only when the review gate is satisfied.
9. Verify learner evidence remains curriculum-local. Never copy StudentSkill/mastery merely because two standards map to the same canonical skill.
10. Run the no-fork regression gate before enabling the jurisdiction.

## No-fork gate

A new jurisdiction passes when it can be onboarded through data, canonical mappings, and review while:
- reusing shared deterministic validators and MVE;
- introducing no jurisdiction-specific mastery/evidence semantics;
- introducing no duplicate problem family solely for a curriculum code;
- preserving authoritative source/version provenance;
- preserving curriculum-local sequencing and coverage;
- leaving existing learner evidence unchanged.

If genuinely new mathematics is discovered, add the canonical concept/skill/problem family once, with its own correctness tests, then map jurisdictions to it.

## Expansion proof sequence

Maryland + Ontario prove the end-to-end pipeline. Virginia + Alberta are the first explicit no-fork onboarding test. British Columbia follows as a structural stress test because its competency-oriented organization may require a different curriculum mapping shape without changing the shared mathematics engine.
