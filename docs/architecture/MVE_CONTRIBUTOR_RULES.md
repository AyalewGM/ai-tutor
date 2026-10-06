# Mihur Visual Architecture Rules

These rules apply to ChatGPT, Devin, and all contributors working on math visuals, geometry, graphing, drawing, or animation.

1. Reuse MVE primitives before introducing feature-specific drawing code.
2. Do not create a second graphing/geometry/animation framework when the requirement fits the MVE.
3. Mathematical representation is renderer-independent.
4. VisualSpec controls presentation, not mathematical correctness.
5. Learner drawing is mathematical work. Record semantic math events, not only pointer traces or pixels.
6. Deterministic validators decide correctness and misconception state.
7. LLMs may explain but may not grade rendered drawings or establish mastery/progression.
8. Avoid answer leakage: a visual must not reveal a quantity or relationship the learner is supposed to infer or construct.
9. New animation must reuse mathematical objects/specs and include reduced-motion/static fallback.
10. New visual types need tests for mathematical correctness, accessibility labeling, and regression safety.
11. Persisted learner-work formats require explicit schema/version compatibility.
12. Exceptions require an ADR or architecture note linked to #175.

## Working mode during MVE refactor
- Preserve recently shipped curriculum behavior.
- Prefer refactoring behind compatibility adapters.
- Keep changes small enough to review and roll back.
- Migrate representative renderer families before bulk migration.
- Do not mix unrelated curriculum expansion with core MVE refactoring in the same PR.
