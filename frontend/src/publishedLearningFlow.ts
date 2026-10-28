/**
 * Frontend-only parser for the authenticated published recovery API (#501).
 * Server ownership, problem eligibility, scoring and task issuance remain backend gates.
 */
export type PublishedStep =
  | "CONFIRM_REASONING" | "PRACTICE_RETRY"
  | "SOCRATIC_REPAIR" | "SOCRATIC_REPAIR_RETRY"
  | "GUIDED_RETEST" | "GUIDED_RETEST_RETRY" | "GUIDED_RETEST_EXHAUSTED"
  | "READY_FOR_TRANSFER_CONFIRMATION" | "INDEPENDENT_EXIT"
  | "TRANSFER_FEEDBACK_ONLY" | "MASTERY_VERIFICATION_FEEDBACK_ONLY";

export interface PublishedChoice { id: string; text: string }
export interface PublishedTask { variant_id: string; mode: "GUIDED" | "INDEPENDENT" | "MASTERY"; prompt: string }
export interface PublishedStage {
  stage: PublishedStep;
  problem_id?: string;
  prompt?: string;
  choices?: PublishedChoice[];
  neutral_prompt?: string;
  socratic_repair_questions?: string[];
  repair_check?: string;
  repair_choices?: PublishedChoice[];
  guided_retest_task?: PublishedTask;
  independent_task?: PublishedTask;
  verification_task?: PublishedTask;
  correct?: boolean;
  hints_allowed?: false;
  independent_evidence_eligible: false;
  mastery_eligible?: false;
  xp_earned?: 0;
}

const stages = new Set<string>([
  "CONFIRM_REASONING", "PRACTICE_RETRY", "SOCRATIC_REPAIR",
  "SOCRATIC_REPAIR_RETRY", "GUIDED_RETEST", "GUIDED_RETEST_RETRY",
  "GUIDED_RETEST_EXHAUSTED", "READY_FOR_TRANSFER_CONFIRMATION",
  "INDEPENDENT_EXIT", "TRANSFER_FEEDBACK_ONLY",
  "MASTERY_VERIFICATION_FEEDBACK_ONLY",
]);
const isRecord = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === "object" && !Array.isArray(value);
const isText = (value: unknown): value is string =>
  typeof value === "string" && value.length > 0 && value.length <= 2000;
const choicesOk = (value: unknown) =>
  Array.isArray(value) && value.length > 0 && value.length <= 8 &&
  value.every((choice: unknown) => isRecord(choice) &&
    isText(choice.id) && isText(choice.text));
const taskOk = (value: unknown, mode: PublishedTask["mode"]) =>
  isRecord(value) && isText(value.variant_id) &&
  isText(value.prompt) && value.mode === mode;

/** Reject changed/malformed stage contracts rather than showing guessed steps. */
export function parsePublishedStage(value: unknown): PublishedStage | null {
  if (!isRecord(value) || !stages.has(String(value.stage)) ||
    value.independent_evidence_eligible !== false ||
    value.mastery_eligible === true ||
    (value.xp_earned !== undefined && value.xp_earned !== 0)) return null;
  if (value.correct !== undefined && typeof value.correct !== "boolean") return null;
  switch (value.stage) {
    case "CONFIRM_REASONING":
      if (!isText(value.prompt) || !choicesOk(value.choices) || !isText(value.problem_id)) return null;
      break;
    case "SOCRATIC_REPAIR":
    case "SOCRATIC_REPAIR_RETRY":
      if (!isText(value.repair_check)) return null;
      if (value.repair_choices !== undefined &&
          (!Array.isArray(value.repair_choices) ||
           (value.repair_choices.length > 0 && !choicesOk(value.repair_choices)))) return null;
      break;
    case "GUIDED_RETEST":
    case "GUIDED_RETEST_RETRY":
      if (!taskOk(value.guided_retest_task, "GUIDED")) return null;
      break;
    case "INDEPENDENT_EXIT":
      if (!taskOk(value.independent_task, "INDEPENDENT") ||
          value.hints_allowed !== false) return null;
      break;
    case "MASTERY_VERIFICATION_FEEDBACK_ONLY":
      if (value.verification_task !== undefined &&
        (!taskOk(value.verification_task, "MASTERY") || value.hints_allowed !== false)) return null;
      break;
  }
  return value as unknown as PublishedStage;
}

/** Presentation only: never infer identity from grade, labels or a provisional skill code. */
export function canOfferPublishedRecovery(
  state: string | null | undefined,
  hasCurrentProblem: boolean,
  submittedWasCorrect: boolean,
  isExtension: boolean,
): boolean {
  return (state === "DIAGNOSE" || state === "GUIDED_PRACTICE") &&
    hasCurrentProblem && !submittedWasCorrect && !isExtension;
}
