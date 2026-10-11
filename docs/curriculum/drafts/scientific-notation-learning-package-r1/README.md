# Scientific notation learning package R1

This draft deepens the accepted exact generator in PR #344 without editing its
mathematics, inventing a new identity, or entering Frontend, MVE, or Assessment
Backend ownership.

| Existing work | Actual gap | Planned improvement | Verification |
| --- | --- | --- | --- |
| Exact deterministic conversion, reverse-conversion, multiplication and division generator | No complete student journey | Full Observe → Predict → Manipulate → Explain → Practice → Diagnose → Transfer → Verify contract | Phase/order and representation tests |
| Accepted exponent-direction and non-normalization paths | Product, quotient, coefficient and inexact-response errors were not package-specific | Six evidence-specific Socratic branches with fresh exits | Routing tests, no generic-wrong fallback |
| Exact generator oracle | No independent package-level reconstruction | Recompute operation value and normalized equality independently from typed parameters | 400 seeded variants across both modes |
| Draft backend scorer and no scientific MVE | Risk of answer leakage or implied wiring | Independent payload excludes parameters/oracle; guided evaluator refuses independent variants; accessibility is a handoff contract | Public-payload and isolation tests |
| Exact-only source generator | Issue row also mentions rounded forms | Mark rounding, zero and negative-coefficient coverage as explicit noncoverage | Provenance and response-policy assertions |

Status is `DRAFT_UNVERIFIED`; `runtime_activation` is false. This package does
not award mastery, mutate learner history, register a route, or claim Ontario
expectation coverage.
