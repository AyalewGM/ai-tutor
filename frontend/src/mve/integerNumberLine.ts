/** Bounded integer arithmetic: exact, deterministic, and separate from mastery. */
export type IntegerOperation = "add" | "subtract";
export function integerModel(start: number, operand: number, operation: IntegerOperation) {
  if (![start, operand].every(v => Number.isSafeInteger(v) && Math.abs(v) <= 10) ||
      !["add", "subtract"].includes(operation)) throw new RangeError("Expected integers from -10 to 10 and a supported operation");
  const displacement = operation === "add" ? operand : -operand;
  const result = start + displacement;
  const direction = displacement === 0 ? "stay" : displacement > 0 ? "right" : "left";
  return { start, operand, operation, displacement, result, direction,
    expression: `${start} ${operation === "add" ? "+" : "−"} (${operand})`,
    explanation: displacement === 0 ? `Start at ${start}. Zero causes no movement.` :
      `Start at ${start}. ${operation === "subtract" ? `Subtracting ${operand} means adding its opposite, ${-operand}. ` : ""}Move ${Math.abs(displacement)} units ${direction} to ${result}.`,
  };
}

export const INTEGER_PRACTICE = [
  { id: "cross-zero", start: -3, operand: 5, operation: "add" },
  { id: "subtract-negative", start: -2, operand: -5, operation: "subtract" },
  { id: "add-negative", start: 4, operand: -7, operation: "add" },
  { id: "subtract-positive", start: 2, operand: 6, operation: "subtract" },
  { id: "zero", start: -4, operand: 0, operation: "subtract" },
] as const;

export function checkIntegerPractice(index: number, answer: string) {
  if (!Number.isInteger(index) || index < 0 || index >= INTEGER_PRACTICE.length) throw new RangeError("Unknown practice item");
  if (!/^-?\d{1,2}$/.test(answer.trim())) return { correct: false, feedback: "Enter a whole number from -20 to 20." };
  const value = Number(answer.trim());
  if (Math.abs(value) > 20) return { correct: false, feedback: "Enter a whole number from -20 to 20." };
  const item = INTEGER_PRACTICE[index];
  const model = integerModel(item.start, item.operand, item.operation);
  if (value === model.result) return { correct: true, feedback: "Correct. " + model.explanation };
  const wrongDirection = (value - item.start) * model.displacement < 0;
  const misconception = wrongDirection ? " Check the direction of movement on the number line." :
    item.operation === "subtract" && item.operand < 0 ? " Remember that subtracting a negative means moving right." :
    item.operation === "add" && item.operand < 0 ? " Remember that adding a negative means moving left." :
    " Recount the signed units from the starting integer.";
  return { correct: false, feedback: "Try again." + misconception };
}

/** Stable deterministic practice index for an externally supplied seed. */
export function integerPracticeIndexFromSeed(seed: number): number {
  if (!Number.isSafeInteger(seed)) throw new RangeError("Expected a safe integer seed");
  return ((seed % INTEGER_PRACTICE.length) + INTEGER_PRACTICE.length) % INTEGER_PRACTICE.length;
}

export function showIntegerExploration(state: string, skillName: string): boolean {
  return ["GUIDED_PRACTICE", "REMEDIATION"].includes(state) &&
    /^(?:(?:add|subtract) integers|integer operations|signed number operations)$/i.test(skillName);
}
