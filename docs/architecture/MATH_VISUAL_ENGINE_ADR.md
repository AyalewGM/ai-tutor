# ADR: Mihur Math Visual Engine

Status: Proposed for adoption
Parent epic: #175

## Context
Mihur has accumulated deterministic visuals for algebra, graphs, geometry, statistics, fractions, transformations, sequences, and other curricula. The existing path already has a valuable property: the backend derives declarative visual data and the frontend renders it without asking an LLM to decide mathematical truth.

However, the current VisualSpec surface is becoming a broad collection of optional fields and ProblemVisual is becoming a monolithic renderer. Upcoming interactive drawing and pedagogical animation will make this architecture harder to scale if every curriculum slice adds one-off drawing logic.

## Decision
Mihur will use one Math Visual Engine (MVE) contract:

Problem Model
→ Mathematical Representation
→ Visual Specification
→ Renderer

For learner-created mathematical work:

Gesture/Input
→ Semantic Mathematical Event
→ Mathematical Object/State
→ Deterministic Validation
→ Pedagogical Interpretation
→ Visual Feedback
→ optional AI explanation

Rendering capability evolves through:

Static Visual
→ Interactive Visual
→ Animated Explanation

## Trust invariant
Student-created mathematical objects are structured mathematical evidence first and visual representations second.

Correctness, mastery, progression, and misconception decisions MUST NOT depend on:
- screenshots or canvas pixels,
- computer-vision interpretation of a drawing,
- an LLM deciding whether a rendered image is mathematically correct.

AI may phrase hints and explanations after deterministic application logic establishes the mathematical state.

## Architecture boundaries

### Mathematical Representation
Renderer-independent mathematical truth. Examples include points, vectors, lines, segments, polygons, functions, transformations, intervals, regions, tables, algebraic structures, and relationships such as perpendicular/parallel/congruent.

SVG paths, CSS values, animation coordinates, and pointer traces are not domain truth unless the coordinate itself has mathematical meaning.

### Visual Specification
Presentation instructions derived from the mathematical representation. It may contain viewport, labels, axes, visibility, emphasis, interaction affordances, accessibility text, and answer-reveal constraints.

VisualSpec must evolve toward discriminated unions instead of an indefinitely growing flat object of optional properties.

### Renderer
A registry of focused renderers keyed by spec kind. SVG remains appropriate for most current deterministic math visuals. Canvas or other technologies may be introduced only behind the same MVE contracts when justified by interaction/performance needs.

### Interaction
Raw mouse/touch/pointer movement is UI input. Persisted/evaluated evidence should be normalized into semantic events such as POINT_PLACED, POINT_MOVED, SEGMENT_CREATED, LINE_CREATED, VERTEX_MOVED, TRANSFORMATION_APPLIED, REGION_SELECTED.

### Validation
Validators consume structured mathematical objects/events and return deterministic outcomes plus structured misconception evidence. They do not inspect pixels.

### Animation
Animation is a timeline over existing mathematical objects and visual specs. It must not encode a second copy of curriculum truth. Every instructional animation requires a pedagogical purpose, static/reduced-motion fallback, and answer-leak review.

## Migration
1. Do not rewrite working visuals wholesale.
2. Introduce typed mathematical objects and discriminated specs incrementally.
3. Create a renderer registry and migrate representative families first.
4. New visualization work should use MVE primitives when representable.
5. Existing feature-specific visuals become migration candidates.
6. Curriculum delivery may continue while MVE refactoring proceeds, but new parallel visualization frameworks require an explicit architecture decision.

## Scalability constraints
- Shared primitives over curriculum-specific renderers.
- Renderer-independent domain objects.
- Schema/version compatibility for persisted learner work.
- Deterministic validation reusable across curricula.
- Accessibility and reduced-motion support are part of the contract.
- Geometry, graphs, drawing, and animation should converge on the same engine.
- Performance budgets and rendering limits must be testable.

## First reference vertical slice
Interactive coordinate-plane task:
1. Problem supplies structured line/point/function target.
2. Static renderer displays the coordinate system.
3. Learner places points or constructs a line.
4. UI emits semantic math events.
5. Engine builds normalized mathematical objects.
6. Validator checks slope/intercept/relationship deterministically.
7. Pedagogy maps error structure to misconception codes.
8. Renderer shows feedback.
9. Optional AI turns structured feedback into language.
10. The same mathematical representation may drive an animated explanation.

## Definition of Done for MVE
A representative problem can use one mathematical representation to:
- render statically,
- accept semantic learner interaction,
- validate learner-created mathematics deterministically,
- return structured misconception evidence,
- drive an animated explanation without duplicating mathematical truth,
- support accessibility and reduced motion,
- persist/replay learner work with schema/version guarantees.
