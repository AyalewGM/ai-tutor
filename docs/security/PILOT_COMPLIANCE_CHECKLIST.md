# Pilot Compliance & Mobile Readiness Checklist

Status tracker for the private family pilot. This is an engineering control
register — it is **not** legal advice and does not claim COPPA/FERPA
certification. See `F018_DATA_INVENTORY.md` for the full data lifecycle contract.

## COPPA readiness (under-13 learners)

| Requirement | State | Evidence / gap |
|---|---|---|
| Collect minimum child data | Done | Learner = nickname only; no email/phone/school/location; display names reject contact-like strings (`app/schemas.py`) |
| Verifiable parental consent | Partial | `coppa_consent_given` flag recorded at signup + notice acknowledgement (`auth_api.py`, `privacy_api.py`). **Gap:** flag is a checkbox, not a verifiable VPC method — needs legal review before public under-13 enrollment |
| Parent can review child's data | Done | `/privacy/data-summary` endpoint + Parent dashboard |
| Parent can delete child's data | Done | `DELETE /privacy/learners/{id}` via `learner_deletion.py`; dependency audit in `F018_DELETION_DEPENDENCY_AUDIT.md` |
| No third-party sharing of child data | Done | No ads, no analytics SDKs, no session replay; LLM gateway is server-side only with minimized context |
| Retention/deletion policy | Done | F-018 lifecycle table + deletion safety contract |
| Privacy policy visible | Done | `/privacy` route; notice acknowledgement persisted with version |

**Remaining for certification:** qualified legal review of the VPC method,
jurisdictional applicability, and subprocessor (LLM provider) data-handling terms.

## FERPA readiness (school deployment)

| Requirement | State | Evidence / gap |
|---|---|---|
| Data minimization | Done | F-018 inventory |
| School-authorized access | N/A | Family pilot only — no school contracts yet |
| Breach/audit procedures | Partial | Operational logging exists without learner PII; incident-response runbook not yet written |
| Data-use agreement | Gap | Requires legal counsel — not a code task |

**Remaining:** FERPA applies once schools enroll students under a school/board
agreement — defer until that contract exists.

## Mobile / install readiness

| Item | State | Evidence |
|---|---|---|
| Installable PWA | Done | `manifest.webmanifest` with PNG icons (192/512 + maskable), `display: standalone`, apple-touch-icon, theme color |
| Responsive learner UI | Done | Workspace/SkillMap/LearnEntry use mobile-first layouts |
| Offline support | Gap | No service worker — requires network. Acceptable for pilot; revisit for app-store |
| Native iOS/Android | Gap | Path: Capacitor wrapper around the React build (shared UI, native shell) or Play Store TWA. Deferred — PWA covers pilot distribution |

## Operational controls (in place)

- Structured logging without learner PII or answer content
- Auth session tokens stored hashed; HttpOnly cookies only
- Database backup/restore documented in `docs/operations/PRIVATE_PILOT_RUNBOOK.md`
- Curriculum evidence isolated per curriculum/version

## Before families are invited

- [ ] Educator review of `docs/learn-content-review.md`
- [ ] Legal/privacy review of consent language shown at signup
- [ ] VPS deployment verified per `docs/operations/PILOT_DEPLOYMENT.md`
- [ ] Backup restore drill executed once on the pilot VPS
