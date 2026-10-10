/** Pure deterministic guided practice: distinct from independent assessment generators.
 * No learner data, global RNG, or mastery writes. Existing canonical family: MATH.INT.ADD.
 */
export type IntegerTask = Readonly<{ seed: number; a: number; b: number; answer: number; prompt: string }>;
export type IntegerDiagnosis = "CORRECT" | "WRONG_DIRECTION" | "IGNORED_NEGATIVE" | "OTHER_ERROR" | "INVALID";

export function buildIntegerTask(seed: number): IntegerTask {
  if (!Number.isSafeInteger(seed) || seed < 0 || seed > 2147483647) {
    throw new RangeError("seed must be a nonnegative 31-bit integer");
  }
  // Integer mixing without hidden state: same seed -> same exact task.
  const a = (Math.imul(seed ^ 0x45d9f3b, 2654435761) >>> 0) % 17 - 8;
  const magnitude = ((Math.imul(seed ^ 0x27d4eb2d, 1597334677) >>> 0) % 8) + 1;
  const b = (seed & 1) === 0 ? magnitude : -magnitude;
  return Object.freeze({ seed, a, b, answer: a + b, prompt: `Find ${a} + (${b}).` });
}

/** Independent arithmetic oracle, intentionally does not call buildIntegerTask. */
export function exactIntegerSum(a: number, b: number): number {
  if (!Number.isSafeInteger(a) || !Number.isSafeInteger(b) || Math.abs(a) > 100 || Math.abs(b) > 100)
    throw new RangeError("integer inputs must be within -100..100");
  const result = a - (-b);
  if (!Number.isSafeInteger(result)) throw new RangeError("unsafe sum");
  return result;
}

export function checkIntegerAnswer(task: IntegerTask, response: string): Readonly<{correct:boolean; diagnosis:IntegerDiagnosis; guidance:string}> {
  const raw = response.trim();
  if (!/^(0|-?[1-9]\d*)$/.test(raw) || raw.length > 5) {
    return {correct:false,diagnosis:"INVALID",guidance:"Enter one integer, without decimals or symbols."};
  }
  const n = Number(raw);
  const correct = n === exactIntegerSum(task.a, task.b);
  if (correct) return {correct:true,diagnosis:"CORRECT",guidance:"Explain why the movement on the number line matches your result."};
  if (n === task.a - task.b) return {correct:false,diagnosis:"WRONG_DIRECTION",guidance:"What does the sign of the second number tell you about the direction of movement?"};
  if (n === Math.abs(task.a) + Math.abs(task.b) && task.answer < 0) return {correct:false,diagnosis:"IGNORED_NEGATIVE",guidance:"Where is zero relative to your starting position, and which direction are you moving?"};
  return {correct:false,diagnosis:"OTHER_ERROR",guidance:"Start at the first integer. Count the distance given by the second integer, then name the endpoint."};
}

export function socraticIntegerPrompts(task: IntegerTask): readonly string[] {
  return [
    `Where would you mark ${task.a} on a number line?`,
    "Does the sign on the second number ask you to move right or left?",
    `How many spaces does the second number ask you to travel?`,
    "Which endpoint did you reach, and how can you check without counting twice?"
  ];
}
