# Interactive curriculum audit and integer implementation

Baseline: e84a739. Scope: the supplied K–9 domain checklist, repository catalogs,
registered/static renderers, guided components and relevant unmerged branches.
This is a capability inventory, not a claim of complete state/provincial alignment.

| Domain | Existing evidence | Interactive depth finding |
| --- | --- | --- |
| Number sense | `app/domains/integers.py`, `fractions.py`, `decimals.py`, `advanced_number.py`; number-line, fraction, decimal renderers | Main has fraction shading, but no signed-operation explorer. Fraction equivalence already exists on `feature/mve-fraction-math-contract-02` and `feature/mve-conceptual-guided-depth-20261009`; do not duplicate. |
| Algebra and coding | `algebra_functions.py`; linear/exponential graphs, balance scale, guided distributive activity | Static renderers do not establish interactive slope/balance coverage. Coding/loop coverage needs a deeper follow-up trace. |
| Spatial and geometry | Geometry and transformation domain modules; interactive coordinate/geometry workspaces; solid/area renderers | Existing interactive foundations are reusable; each transformation and volume sequence needs separate depth review. |
| Data and probability | `statistics_probability.py`, `bivariate_sampling.py`; dot plots, scatterplots, frequency tables, spinners, marble bags | Static representations exist; manipulable plots, best-fit investigation and probability-tree depth remain unverified. |
| Financial literacy | Simple-interest, percent and budget domain modules | Dynamic budgeting and simple-versus-compound interactive coverage remain unverified. |

## Selected verified gap

Integer addition/subtraction are existing canonical families (`MATH.INT.ADD`,
`MATH.INT.SUB`, under `MATH.NS.INTEGER_OPERATIONS`), with existing server problems.
The missing piece is guided manipulation and explanation, not a new canonical skill.
This foundational concept supports later rational arithmetic and algebra.

The new component reuses the registered number-line renderer. Subtraction supplies
its additive displacement to that renderer, so subtracting -3 correctly draws +3.
Operands are bounded to [-10,10], results to [-20,20]; integer operations are exact.
No animation or timers are introduced, so reduced-motion users get identical behavior.
Native range inputs support arrows/Home/End; labels, visible focus and live status
provide keyboard and screen-reader access. Zero displacement is explained explicitly.

Observe → Manipulate → Explain → Practice includes five fixed specifications:
crossing zero, subtracting a negative, adding a negative, subtracting a positive,
and subtracting zero. Feedback is deterministic and local; it does not submit mastery.
The allowlisted semantic event contains only integer state and rejects unknown fields.
An optional callback exposes events; no telemetry endpoint or student identifier is added.

Workspace mounts only in guided/remediation states and matching existing integer skill
names (the workspace API does not expose a canonical code). The component independently
fails closed unless `independentAssessment` is explicitly false. Assessment transitions
remove the guided subtree and its state. Examples are separate from assigned problems.

## Verification

- `npm run test:mve`: 20 tests pass, including six new behavioral test groups.
- Exhaustive checking of all 882 bounded operation combinations.
- Actual React server rendering, real SVG renderer, label/live-status assertions.
- Real handlers exercised with a minimal hook driver, event validation and practice reset.
- Assessment/unknown-mode empty rendering; workspace selection tested as a pure predicate.
- `npm run build`: TypeScript and production bundling pass.

Browser keyboard execution, assistive-technology testing, and a full application
assessment-transition E2E run are not performed here. Existing build warnings concern
bundle size and tool configuration. No new dependencies, schema changes or mastery writes.
