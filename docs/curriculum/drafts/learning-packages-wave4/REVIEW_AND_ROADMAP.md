# Learning Package Production — Wave 4 review handoff

This Wave 4 expansion stays on **draft PR #328**, with no runtime activation or changes to production canonical identifiers, student attempts, diagnostics or historical mastery.

Five instructional-depth additions: Grades 2–4 measurement and conversions; Grades 3–5 area/perimeter/composite shapes; Grades 6–8 histogram construction and interval boundaries; Grades 6–8 rectangular-prism nets, surface area and volume distinction; Grade 9 additive vs multiplicative/exponential modeling.

**Draft Wave 4 totals:** 5 packages, 25 worked examples, 15 misconception pathways, 20 guided practice questions, 10 independently presented assessment/transfer questions, 5 interactive specifications. These are candidate content, not demonstrated standards coverage or deployable interactive widgets. The included teaching-step descriptions are concise; Mathematical Review must require more rigorous explanation and deeper targeted misconception probes before approval.

**Mapping:** independently link each item to exact official expectation/version and appropriate grade; PR #325 is only a provisional priority source. **Math Review:** verify exact arithmetic, histogram half-open intervals, face counts for open/closed prisms, unit conversions, and linear/exponential distinctions. **Engineering:** deduplicate with current domain generators and PRs #309, #315, #316, #317, #319 and #327. **MVE:** interactive spec requires keyboard and equivalent textual state. **Muse QA:** verify independent assessment isolation, mathematical correctness and no runtime activation.

Run `pytest -q tests/test_learning_packages_wave4.py`. Tests check static safety and selected arithmetic; no full independent oracle, CI success, acceptance or production suitability is claimed.

Across PR #327 and evolving #328 Wave 1–4 authored totals, **21 draft packages, 105 worked examples, 63 draft misconception pathways, 84 guided practice items and 58 independently presented assessment items**; there may be overlaps and none represent verified coverage.
