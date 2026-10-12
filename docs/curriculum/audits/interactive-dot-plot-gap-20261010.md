# Dot-plot explorer and browser stabilization

Existing `statistics_probability.py` and Grade 6 Center and Spread content cover
mean, median and outlier reasoning. The shared DotPlot renderer is static. The
inspected guided components have no observation manipulator. This addition reuses
that renderer and the existing exact rational helper, with no new canonical IDs.

## Activity

Move a selected synthetic observation using a native keyboard slider, add a repeated
observation or remove the selected one, and reset. Count, total, mean, median, range,
ordered data and a frequency table update immediately. The fixed axis is 0–12 and
the dataset contains 1–6 integer observations, keeping stacked dots visible.
Explanations distinguish mean sensitivity from middle-position reasoning and avoid
claiming that median is always unchanged by extreme observations. Four local practice
items cover mean, even-count unsorted median, repeated values and all-zero range.

Guided/remediation-only Workspace mounting, independent component assessment guard,
visible focus, labels, live feedback and no-motion behavior follow the prior explorers.
Events contain bounded synthetic values only; unknown fields and sparse/invalid arrays
are rejected. These are local guided exercises, not mastery evidence or approved
jurisdiction mappings.

## Evidence

Local: 36 MVE tests PASS, TypeScript/Vite build PASS. Tests cover exact known values,
all 169 two-observation combinations, empty/singleton/equal/repeated/sparse inputs,
immutability, events, count bounds, assessment isolation and real React handlers/SSR.
Browser harness extended for moving an extreme value, exact summaries, count limits,
assessment removal and fresh remount; new-head CI pending.

Prior balance head c571482: dedicated integer/linear/balance browser harness PASSED
in CI run 38058638466, AppSec 38058638480 PASSED. The containers job failed afterward
in photo OCR application E2E: it snapshot-read the work list after the first line
without awaiting the sequential second request. The test now awaits review dismissal
and retries both exact normalized content assertions; requirements are unchanged.
New-head CI must confirm this correction and the new data visualization.
Independent pedagogical review and screen-reader evaluation remain outstanding.
