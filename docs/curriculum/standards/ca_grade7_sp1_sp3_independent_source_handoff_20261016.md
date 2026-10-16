# California 7.SP.1–3 — author source-fidelity handoff

Repository: AyalewGM/ai-tutor. Follow-up to merged PR #384.
Branch: `standards/ca7-sp1-sp3-statistical-inference-source-20261016`
Author correction commit: `189c0d25027daad26b8dbea18c755cd4e9e3fda0`.
Regression test commit: `e5b14f70cd4842d1bf4c9f11b3dcbe46e6053842`.
For the exact final head SHA, use the branch ref; this file's own commit changes that SHA.

## Official controlling evidence

California Department of Education, *California Common Core State Standards:
Mathematics*, modified January 2013 and corrected electronic edition (2014).
https://www.cde.ca.gov/be/st/ss/documents/ccssmathstandardaug2013.pdf
Printed page 50, zero-based PDF index 56.

- 7.SP.1: Population inference requires a representative sample. Random
  sampling **tends** to produce representative samples; it is not a guarantee.
- 7.SP.2: Infer unknown population features from a random sample; generate
  multiple real or simulated samples of **the same size** to gauge variation
  among estimates or predictions and their possible error.
- 7.SP.3: Informally compare the **degree of visual overlap** between two
  numerical distributions with **similar variabilities**. Quantify center
  separation as a multiple of a variability measure; mean absolute deviation
  appears as an example, not the sole authorized measure.

## Files and bounded checks

- `docs/curriculum/standards/ca_2013_grade7_24_source_author_slice.v1.json`
- `tests/test_ca_grade7_sp1_sp3_source_qualifiers.py`

Retain the 24 original Grade 7 parent expectation identifiers, page locators,
PENDING independent fidelity, UNVERIFIED canonical/assessment/mastery and
FORBIDDEN activation. No runtime mappings, learner data or mastery touched.

## Next gates

1. Standards Mapping / authorized operator: open a **draft** reviewable PR
   from this branch. GitHub connector safety checks rejected three PR creation
   attempts and comments on Issues #241 and #377 in the author session.
2. Run CI and AppSec at the exact PR head.
3. **Independent Standards Source-Fidelity Reviewer:** compare against CDE p.50,
   including non-guaranteed representativeness, same-size sample inference,
   population comparison and the distinction between an example and a rule.
   Record an exact-SHA scoped verdict; do not self-approve or merge.
4. Keep California's other historical/Grade 1–6 records and Texas/Washington
   publisher gates unaccepted pending independent evidence.
