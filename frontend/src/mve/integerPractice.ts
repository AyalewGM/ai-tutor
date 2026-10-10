/** Deterministic guided integer practice. This module never scores mastery. */
export type IntegerTask = Readonly<{ seed: number; a: number; b: number; answer: number; prompt: string }>;
export type IntegerDiagnosis =
  | "CORRECT" | "WRONG_DIRECTION" | "IGNORED_NEGATIVE" | "SIGN_REVERSAL"
  | "OFF_BY_ONE" | "OTHER_ERROR" | "INVALID";

export function buildIntegerTask(seed: number): IntegerTask {
  if (!Number.isSafeInteger(seed) || seed < 0 || seed > 2147483647) {
    throw new RangeError("seed must be a nonnegative 31-bit integer");
  }
  const a = (Math.imul(seed ^ 0x45d9f3b, 2654435761) >>> 0) % 17 - 8;
  const magnitude = ((Math.imul(seed ^ 0x27d4eb2d, 1597334677) >>> 0) % 8) + 1;
  const b = (seed & 1) === 0 ? magnitude : -magnitude;
  return Object.freeze({ seed, a, b, answer: a + b, prompt: `Find ${a} + (${b}).` });
}

/** Separate arithmetic oracle: ignores task.answer and rejects unsafe operands. */
export function exactIntegerSum(a: number, b: number): number {
  if (!Number.isSafeInteger(a) || !Number.isSafeInteger(b) || Math.abs(a) > 100 || Math.abs(b) > 100) {
    throw new RangeError("integer inputs must be within -100..100");
  }
  return a - (-b);
}

export function checkIntegerAnswer(
  task: IntegerTask, response: string
): Readonly<{correct: boolean; diagnosis: IntegerDiagnosis; guidance: string}> {
  const expected = exactIntegerSum(task.a, task.b);
  const raw = response.trim();
  if (!/^(0|-?[1-9]\d*)$/.test(raw) || raw.length > 5 || !Number.isSafeInteger(Number(raw))) {
    return { correct: false, diagnosis: "INVALID", guidance: "Enter one whole integer, without decimals, extra signs or leading zeroes." };
  }
  const n = Number(raw);
  if (n === expected) {
    return { correct: true, diagnosis: "CORRECT", guidance: "Explain how the direction and distance of your move support your result." };
  }
  if (task.b !== 0 && n === task.a - task.b) {
    return { correct: false, diagnosis: "WRONG_DIRECTION", guidance: `You started at ${task.a}. Does adding ${task.b} mean moving right or left? Try that direction without changing the distance.` };
  }
  if (expected < 0 && n === Math.abs(task.a) + Math.abs(task.b)) {
    return { correct: false, diagnosis: "IGNORED_NEGATIVE", guidance: "Your result is positive. When you start below zero and move left, can your endpoint be positive?" };
  }
  if (expected !== 0 && n === -expected) {
    return { correct: false, diagnosis: "SIGN_REVERSAL", guidance: "You found a point the same distance from zero on the opposite side. Which side did your movement actually reach?" };
  }
  if (Math.abs(n - expected) === 1) {
    return { correct: false, diagnosis: "OFF_BY_ONE", guidance: "Count jumps, not tick marks. Is your starting point jump zero or jump one?" };
  }
  return { correct: false, diagnosis: "OTHER_ERROR", guidance: `Mark ${task.a}, decide the direction from the sign of ${task.b}, then count ${Math.abs(task.b)} jumps.` };
}

export function socraticIntegerPrompts(task: IntegerTask): readonly string[] {
  return [
    `Where would you mark ${task.a} on a number line?`,
    "Does the sign on the second number ask you to move right or left?",
    `How many spaces does ${task.b} ask you to travel?`,
    "Which endpoint did you reach, and how can you check without counting twice?"
  ];
}

/** Deterministic seed from an opaque identifier, inside buildIntegerTask's range. */
export function integerSeedFromString(value: string): number {
  let hash = 0;
  for (const ch of value) hash = (Math.imul(hash, 31) + ch.charCodeAt(0)) | 0;
  return hash >>> 1;
}

/** Signed-integer guided practice teaches addition for integer skills only. */
export function integerPracticeEligible(state: string, skillName: string): boolean {
  return ["GUIDED_PRACTICE", "REMEDIATION"].includes(state) &&
    /^(?:add integers|integer addition|integer operations|signed number operations)$/i.test(skillName);
}
