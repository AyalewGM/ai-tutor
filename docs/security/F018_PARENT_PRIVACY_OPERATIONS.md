# F-018 Parent Privacy Operations

This runbook covers the private pilot's parent access/deletion workflow. It is an engineering and incident-readiness control, not legal advice or a representation of compliance with any particular law.

## Parent requests

Authenticated parents can view the current privacy notice and a minimized data-category summary from Parent Settings. Learner erasure requires selecting an authorized learner, typing `DELETE`, and confirming the destructive action. Removing/unlinking a child from the dashboard is a different operation and preserves learning evidence.

The API must fail closed for cross-family identifiers and must not reveal whether another family's learner exists. Do not fulfill identity-sensitive requests from GitHub issues, email screenshots, logs, or other untrusted artifacts.

## Deletion execution

Learner deletion is authorization-first and transactional. Learner-scoped tutoring evidence, diagnostics, interventions, curriculum enrollment, family link artifacts, and associated disposable session telemetry are removed in dependency order. Shared curriculum, standards, skills, problems, and provenance remain intact. Any database failure rolls the transaction back.

Do not manually delete individual tables to work around a failed request. Investigate the dependency, preserve rollback safety, add a synthetic regression test, then rerun through the application-owned deletion service.

## Incident / unexpected behavior

If deletion returns an unexpected server error, do not retry with ad-hoc SQL. Record only a non-sensitive request/time/error reference; never copy learner names, answers, transcripts, tokens, credentials, or screenshots containing real child data into GitHub. Review application/database logs using least-privilege operational access and verify whether the transaction rolled back before any retry.

Suspected cross-family access, incomplete deletion, exposed credentials/tokens, or unintended third-party learner-data transmission is a release blocker. Disable the affected operation if necessary and escalate for Security/Compliance review.

## Third parties and LLMs

F-018 introduces no new OpenAI, Gemini, advertising, analytics-vendor, or browser-to-model data flow. The deletion workflow is first-party. If provider data flows later change, vendor/subprocessor retention and deletion obligations must be re-audited before relying on this runbook.

## Verification

Before release, CI/QA must prove with synthetic identities:
- unauthorized parent deletion fails before mutation;
- target learner records are erased across all classified learner-scoped tables;
- sibling/other-family and shared curriculum/content survive;
- old learner/session access fails after deletion;
- injected transaction failure rolls back fully;
- telemetry lifecycle cannot alter authoritative mastery/intervention state.

## Legal/product boundary

Privacy-notice acknowledgement is not represented as verifiable parental consent. Under-13 public/commercial enrollment and school deployment remain separately gated for applicable COPPA, FERPA/PPRA, Canadian/PIPEDA youth privacy, state/provincial obligations, contracts, and qualified legal/privacy review where required.
