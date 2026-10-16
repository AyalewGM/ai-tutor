# Learn Together — first milestone

Private standalone whiteboards for a parent and one child, including multiple
family devices. Entry point: **Together** in the navigation, `/together`.
The parent starts a board for an existing child; the child signs in with their
usual Mihur learner access and opens Together or the copied board link. The
board URL is an identifier, not a bearer invitation. It does not grant access.

## Included

- Shared pen strokes and plain typed math/text, fixed 1600 × 1000 page coordinates.
- Purple parent marks, blue learner marks, author-scoped undo.
- Durable ordered operations, incremental replay, idempotent write retries.
- Pending writes retained in tab session storage until confirmed by the server.
- Cookie-authenticated WebSocket delivery with same-origin enforcement and live
  expiry/revocation/ownership checks; writes use the existing HTTP JSON controls.
- Saved-board list, parent closure, read-only access after closure.
- Learner deletion cascades through boards and marks; privacy disclosures include
  saved board content. Existing PII filtering applies to typed text. Handwritten
  marks are not recognized or scanned, and boards are not sent to AI providers.

These boards have no tutor-session/attempt/mastery linkage. Opening, writing,
replaying, or closing a board cannot award mastery. Do not add assessment problem
sharing without a separate server-enforced assistance-evidence design.

## Deployment

Apply `alembic upgrade head` before starting the updated API. Revision
`0036_collaboration` follows `0035_extension_mode`. The frontend nginx proxy and
Vite development proxy forward WebSockets and preserve the browser Host header,
including the port. Outer proxies must preserve Host and support WebSocket
upgrades. Existing HTTPS/cookie deployment requirements continue to apply.

Rollback: stop the updated application before `alembic downgrade
0035_extension_mode`. Downgrading deletes all board content; back up first if
content must be retained. Deploy the preceding frontend/API together.

## Validation

Run:

```sh
python -m pytest -q tests/test_collaboration.py tests/test_learner_deletion.py
python -m ruff check app/collaboration_api.py app/collaboration_models.py tests/test_collaboration.py
npm ci --prefix frontend
npm run build --prefix frontend
```

Two-browser validation (synthetic in-memory family only; ports 8002 and 5173 must
be available):

```sh
npm ci --prefix e2e
cd e2e && npx playwright install chromium && cd ..
python e2e/run-learn-together-check.py
```

Optionally set `MIHUR_CHROMIUM_PATH` to a local Chromium executable. This check
covers parent/child text synchronization, child undo preserving parent work,
handwriting delivery, offline edit recovery after refresh, and phone viewport
overflow. It uses Chromium touch emulation, not a physical iPad.

Executed author-side: 11 API/deletion tests passed, Ruff passed, production
frontend build passed, and the two-browser check passed. PostgreSQL concurrency
is covered by `tests/integration/test_collaboration_postgres.py` for CI execution;
it was not executed locally because no PostgreSQL server was available.

The isolated API suite exercises real cookie identities and SQL persistence with
SQLite, plus origin rejection, replay/retry, author-only undo, learner scope,
revocation, closure, validation, PII filtering, migration upgrade/downgrade, and
learner-erasure cascades. SQLite timezone normalization is confined to the test
fixture. It does not prove PostgreSQL concurrency behavior.

Before pilot activation, verify concurrent writers against PostgreSQL, staging
WebSocket forwarding, and real iPad/Safari + Chromebook handwriting. Measure
resource use on the target VPS. Current live readers query revisions every 500ms;
this is a bounded first implementation, not a scale-tested room broker.

## Deliberate limits

- One fixed page; completed strokes are synchronized, not each in-progress point.
- No PDF/photo import, pressure-sensitive widths, gesture zoom, eraser, pointer,
  participant presence, follow-parent navigation, integrated voice, or AI reading.
- Typed math is plain text; no claim of equation parsing or scoring.
- Fifty pending writes per tab, 4,000 points per stroke, 1,000 characters per text
  mark, and 10,000 operations per board. Start another board when full.
- Pending recovery is scoped to the same browser tab and authenticated identity;
  it is not cross-device offline synchronization.
- No student email/password or anonymous public room joining is introduced.
