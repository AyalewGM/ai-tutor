export type ScaleDirection = "COEFFICIENT_DIVIDE_BY_TEN" | "COEFFICIENT_MULTIPLY_BY_TEN";
export type ScalePrediction = "INVERSE_CHANGES_PRESERVE_VALUE" | "SAME_DIRECTION_PRESERVES_VALUE" | "";
export type ScaleExplanation = "COEFFICIENT_AND_POWER_ARE_INVERSE_FACTORS" | "DECIMAL_MOVES_WITHOUT_POWER_CHANGE" | "";

export interface ScientificScaleExample {
  significant_digits: number;
  coefficient_power: number;
  exponent: number;
}

export interface ScientificScaleState extends ScientificScaleExample {
  invariant_power: number;
}

export const SCIENTIFIC_SCALE_EXAMPLES: readonly ScientificScaleExample[] = [
  { significant_digits: 45, coefficient_power: 2, exponent: 0 },
  { significant_digits: 72, coefficient_power: -6, exponent: 0 },
  { significant_digits: 63, coefficient_power: 4, exponent: 0 },
  { significant_digits: 81, coefficient_power: -7, exponent: 0 },
];

export function scientificScaleExampleFromSeed(seed: number): ScientificScaleExample {
  if (!Number.isSafeInteger(seed) || seed < 0) throw new RangeError("seed must be a non-negative safe integer");
  return SCIENTIFIC_SCALE_EXAMPLES[seed % SCIENTIFIC_SCALE_EXAMPLES.length];
}

export function initialScientificScaleState(example: ScientificScaleExample): ScientificScaleState {
  assertExample(example);
  return { ...example, invariant_power: example.coefficient_power + example.exponent };
}

export function movePowerOfTen(state: ScientificScaleState, direction: ScaleDirection): ScientificScaleState {
  assertState(state);
  const delta = direction === "COEFFICIENT_DIVIDE_BY_TEN" ? -1 :
    direction === "COEFFICIENT_MULTIPLY_BY_TEN" ? 1 : NaN;
  if (!Number.isSafeInteger(delta)) throw new RangeError("unsupported scale direction");
  const next = {
    ...state,
    coefficient_power: state.coefficient_power + delta,
    exponent: state.exponent - delta,
  };
  assertState(next);
  return next;
}

export function isNormalizedScientificState(state: ScientificScaleState): boolean {
  assertState(state);
  return state.coefficient_power === 1 - String(state.significant_digits).length;
}

export function formatScaleCoefficient(significantDigits: number, coefficientPower: number): string {
  assertExample({ significant_digits: significantDigits, coefficient_power: coefficientPower, exponent: 0 });
  const digits = String(significantDigits);
  if (coefficientPower >= 0) return digits + "0".repeat(coefficientPower);
  const point = digits.length + coefficientPower;
  if (point > 0) return `${digits.slice(0, point)}.${digits.slice(point)}`;
  return `0.${"0".repeat(-point)}${digits}`;
}

export function formatScaleExpression(state: ScientificScaleState): string {
  assertState(state);
  return `${formatScaleCoefficient(state.significant_digits, state.coefficient_power)} × 10^${state.exponent}`;
}

export function formatScaleOrdinaryValue(example: ScientificScaleExample): string {
  assertExample(example);
  return formatScaleCoefficient(example.significant_digits, example.coefficient_power + example.exponent);
}

export function evaluateScaleReasoning(
  state: ScientificScaleState,
  prediction: ScalePrediction,
  explanation: ScaleExplanation,
) {
  assertState(state);
  if (!isNormalizedScientificState(state)) return {
    correct: false,
    diagnosis: "SCI.NOT_NORMALIZED",
    feedback: "The coefficient is not normalized yet. Keep its magnitude at least 1 and less than 10 while preserving the value.",
  };
  if (prediction !== "INVERSE_CHANGES_PRESERVE_VALUE") return {
    correct: false,
    diagnosis: "SCI.EXPONENT.DIRECTION",
    feedback: "Reconsider direction: when the coefficient changes by a factor of ten, the power of ten must compensate in the inverse direction.",
  };
  if (explanation !== "COEFFICIENT_AND_POWER_ARE_INVERSE_FACTORS") return {
    correct: false,
    diagnosis: "SCI.EXPLANATION_EVIDENCE",
    feedback: "Connect the coefficient change to an inverse power-of-ten change that keeps the exact value fixed.",
  };
  return {
    correct: true,
    diagnosis: "NO_REMEDIATION",
    feedback: "Correct. The coefficient is normalized and the inverse scale changes preserve the exact value.",
  };
}

export function evaluateScientificTransfer(example: ScientificScaleExample, coefficient: string, exponent: string) {
  assertExample(example);
  try {
    const observedCoefficient = parseExactDecimal(coefficient);
    const observedExponent = parseBoundedInteger(exponent);
    if (!isNormalizedFraction(observedCoefficient)) return {
      correct: false,
      diagnosis: "SCI.NOT_NORMALIZED",
      feedback: "Use a coefficient whose magnitude is at least 1 and less than 10.",
    };
    const expectedCoefficient = { numerator: BigInt(example.significant_digits), denominator: 1n };
    const observedValue = applyPowerOfTen(observedCoefficient, observedExponent);
    const expectedValue = applyPowerOfTen(
      expectedCoefficient,
      example.coefficient_power + example.exponent,
    );
    if (!sameFraction(observedValue, expectedValue)) return {
      correct: false,
      diagnosis: "SCI.EXPONENT.DIRECTION",
      feedback: "The normalized form does not preserve the starting value. Check that coefficient and exponent changes compensate inversely.",
    };
    return {
      correct: true,
      diagnosis: "NO_REMEDIATION",
      feedback: "Correct. Your normalized coefficient and exponent preserve the exact value.",
    };
  } catch {
    return {
      correct: false,
      diagnosis: "SCI.INVALID_EXACT_RESPONSE",
      feedback: "Enter an exact decimal coefficient and an integer exponent within the displayed scale.",
    };
  }
}

function assertExample(example: ScientificScaleExample) {
  if (!example || !Number.isSafeInteger(example.significant_digits) ||
      example.significant_digits < 1 || example.significant_digits > 999 ||
      example.significant_digits % 10 === 0 ||
      !Number.isSafeInteger(example.coefficient_power) || Math.abs(example.coefficient_power) > 8 ||
      !Number.isSafeInteger(example.exponent) || Math.abs(example.exponent) > 8 ||
      Math.abs(example.coefficient_power + example.exponent) > 8) {
    throw new RangeError("expected a bounded positive nonzero scientific-scale example");
  }
}

function assertState(state: ScientificScaleState) {
  assertExample(state);
  if (!Number.isSafeInteger(state.invariant_power) ||
      state.invariant_power !== state.coefficient_power + state.exponent) {
    throw new RangeError("scale state must preserve its invariant power");
  }
}

function parseBoundedInteger(value: string) {
  const trimmed = value.trim();
  if (!/^-?(0|[1-9]\d*)$/.test(trimmed)) throw new RangeError("expected integer");
  const parsed = Number(trimmed);
  if (!Number.isSafeInteger(parsed) || Math.abs(parsed) > 8) throw new RangeError("integer out of range");
  return parsed;
}

function parseExactDecimal(value: string) {
  const trimmed = value.trim();
  if (!/^(0|[1-9]\d*)(\.\d+)?$/.test(trimmed) || trimmed.length > 12) {
    throw new RangeError("expected exact nonnegative decimal");
  }
  const [whole, decimal = ""] = trimmed.split(".");
  return reduceFraction({
    numerator: BigInt(whole + decimal),
    denominator: 10n ** BigInt(decimal.length),
  });
}

function isNormalizedFraction(value: { numerator: bigint; denominator: bigint }) {
  return value.numerator >= value.denominator && value.numerator < 10n * value.denominator;
}

function applyPowerOfTen(value: { numerator: bigint; denominator: bigint }, exponent: number) {
  return reduceFraction(exponent >= 0 ? {
    numerator: value.numerator * 10n ** BigInt(exponent), denominator: value.denominator,
  } : {
    numerator: value.numerator, denominator: value.denominator * 10n ** BigInt(-exponent),
  });
}

function reduceFraction(value: { numerator: bigint; denominator: bigint }) {
  const divisor = bigintGcd(value.numerator, value.denominator);
  return { numerator: value.numerator / divisor, denominator: value.denominator / divisor };
}

function bigintGcd(left: bigint, right: bigint) {
  while (right !== 0n) [left, right] = [right, left % right];
  return left < 0n ? -left : left;
}

function sameFraction(left: { numerator: bigint; denominator: bigint }, right: { numerator: bigint; denominator: bigint }) {
  return left.numerator === right.numerator && left.denominator === right.denominator;
}
