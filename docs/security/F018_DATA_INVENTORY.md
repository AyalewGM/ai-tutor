# F-018 Private Pilot Data Inventory and Lifecycle Contract

This document is the application-owned inventory for the private family pilot. It is an engineering/privacy control, not legal advice or a claim of COPPA, FERPA/PPRA, PIPEDA, Ontario, Maryland, or other legal compliance.

## Principles

- Collect the minimum data required for authentication, tutoring, curriculum-scoped progress, authorized parent visibility, reliability, and pilot economics.
- PostgreSQL and application services are authoritative. The browser must not create a shadow learner profile or persist authentication tokens.
- Application code owns pedagogy, mastery, prerequisite routing, intervention, curriculum identity, and assessment. LLM providers may render constrained language only from application decisions.
- Never place real child data, credentials, secrets, raw authentication tokens, or identity-verification documents in source control, issues, fixtures, screenshots, prompts, or normal telemetry.
- Curriculum evidence remains bound to its exact curriculum/version and may not be silently transferred across jurisdictions.

## Inventory

| Data class | Minimum fields / examples | Purpose | Authoritative storage | Access | Third-party / LLM flow | Lifecycle / deletion class | Less-data choice |
|---|---|---|---|---|---|---|---|
| Parent account | email, optional display name, role | account identity and family access | PostgreSQL `users` | authenticated parent; narrowly scoped operations | none required | account lifecycle; deletion workflow must revoke access and dispose/anonymize dependent data according to explicit rules | display name optional; no marketing profile |
| Credential | Argon2 password hash | authentication | PostgreSQL `user_credentials` | authentication service only | none | delete with account; never export in parent data summary | never store plaintext password |
| Session | opaque token digest, user id, expiry/revocation metadata | authenticated browser session | PostgreSQL auth-session records; HttpOnly cookie carries opaque token | authentication middleware | none | short-lived/revocable; revoke on logout/account deletion | no localStorage/sessionStorage token |
| Parent profile / family link | parent profile id, learner relationship, relationship status | family authorization | PostgreSQL parent relationship records | linked parent; authorization services | none | unlink/deletion lifecycle must be auditable without retaining unnecessary child content | no caller-supplied parent identity for authorization |
| Learner identity | first name, parent relationship | distinguish learners in family pilot | PostgreSQL `students` | authorized linked parent and tutoring services | no direct browser-to-provider flow | learner deletion workflow must cover dependent learning records explicitly | no child email, phone, password, school name, ad id |
| Curriculum enrollment | exact curriculum id/version/jurisdiction, grade/course | select authoritative content and isolate evidence | PostgreSQL curriculum/enrollment records | authorized family and application services | provider receives only data strictly needed for constrained rendering when applicable | historical evidence remains tied to exact curriculum/version until its owning learning record is deleted | no inferred cross-jurisdiction equivalence |
| Learning evidence | attempts, diagnostic/mastery evidence, hint/assistance class, intervention state | deterministic tutoring and progress | PostgreSQL authoritative learning tables | learner workflow and authorized linked parent summaries | constrained language generation may receive minimized structured context through server-side LLM gateway; never direct browser call | authoritative learning lifecycle; must not be deleted by disposable telemetry expiry | avoid unnecessary free-form transcript storage |
| Parent progress read model | evidence-backed summaries/reason codes | explain independent vs assisted progress | derived from authoritative application evidence | authorized linked parent only | LLM optional for wording only; structured fallback required | derived/recomputable; follows underlying evidence lifecycle | do not expose hidden prompts/reasoning |
| Pilot telemetry | pseudonymous IDs, event type, curriculum/version, skill/session metadata, assistance class, latency/error/model-cost metadata | reliability, learning KPI and unit-economics observation | first-party telemetry table | narrowly scoped operational/analytics access | provider billing metadata may originate from configured provider; no normal raw learner text | disposable/versioned retention policy; expiry must never mutate authoritative learning evidence | prohibit names/emails/raw answers/prompts/transcripts/auth tokens/precise location/ad ids/session replay |
| Notice acknowledgement (F-018) | notice version, parent user id, timestamp | prove which product notice was acknowledged | PostgreSQL first-party record | authenticated parent; narrowly scoped operations | none | retain only as needed for accountability; delete/anonymize consistently with account lifecycle and applicable obligations | do not collect ID/biometric/age-verification evidence in this slice |
| Deletion/audit metadata (F-018) | request/action type, timestamps, non-sensitive status/reason code | accountable execution of parent data controls | first-party audit record | narrowly scoped operations; parent may see safe status | none | minimize; do not retain deleted learner content in audit payload | store event metadata, not copied learner records |

## F-018 deletion safety contract

Deletion is not implemented as a blind cascade until every dependent table is classified. Engineering must first enumerate foreign-key/dependency behavior and choose, per data class, delete vs irreversible de-identification vs legally/operationally required minimal audit retention. The operation must be server-authorized to the linked family, explicit/confirmed, deterministic, testable, and non-enumerating across families.

Deleting disposable telemetry must never alter attempts, mastery, diagnostics, curriculum enrollment, or deterministic intervention state. Conversely, a parent-requested learner/account deletion must not leave a usable shadow learner profile in telemetry, browser storage, logs, or an LLM provider. Provider-side retention/configuration is a vendor/subprocessor release-gate question and must be documented before broader enrollment.

## Consent / age boundary

A notice acknowledgement is not represented as verifiable parental consent. Before a covered public/commercial under-13 enrollment, Product/Security must resolve the appropriate VPC method and jurisdictional applicability with qualified legal/privacy review. Before school deployment, separately assess FERPA/PPRA and school/board contractual/privacy requirements. Do not collect government ID, biometric, or similar age-verification material unless a separately approved design demonstrates necessity and lifecycle controls.

## F-018 acceptance evidence required

- parent data summary excludes password hashes, session/token material, secrets and hidden prompts;
- family/learner deletion is server-authorized and cross-family identifier substitution fails closed;
- post-deletion access behavior is tested with synthetic identities;
- curriculum/version isolation remains intact;
- telemetry lifecycle and authoritative-learning lifecycle remain demonstrably separate;
- no new direct browser-to-OpenAI/Gemini/provider flow;
- data inventory, notice version and acknowledgement behavior are versioned and tested;
- Security & Compliance, QA, PO and PM acceptance are recorded before merge.
