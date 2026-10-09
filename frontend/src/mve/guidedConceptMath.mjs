/** Pure guided-learning math, never an independent mastery scorer. */
export function equivalenceModel(numerator, denominator, scale) {
  if (![numerator, denominator, scale].every(Number.isSafeInteger) ||
      numerator < 1 || denominator < 2 || numerator >= denominator ||
      denominator > 6 || scale < 2 || scale > 3 || denominator * scale > 12) {
    throw new RangeError("Guided fraction parameters are outside supported bounds");
  }
  return {
    numerator, denominator, scale,
    expandedNumerator: numerator * scale,
    expandedDenominator: denominator * scale,
  };
}

export function classifyEquivalentAnswer(model, submitted) {
  if (!/^(0|[1-9]\d{0,2})$/.test(submitted.trim())) {
    return { correct: false, misconception: "INVALID_INPUT" };
  }
  const answer = Number(submitted.trim());
  if (answer === model.expandedNumerator) {
    return { correct: true, misconception: null };
  }
  if (answer === model.numerator) {
    return { correct: false, misconception: "NUMERATOR_NOT_SCALED" };
  }
  if (answer === model.numerator + model.scale) {
    return { correct: false, misconception: "ADDITIVE_SCALING" };
  }
  return { correct: false, misconception: "RECHECK_EQUAL_PARTS" };
}

export function ratioPartitionModel(firstParts, secondParts, unitValue) {
  if (![firstParts, secondParts, unitValue].every(Number.isSafeInteger) ||
      firstParts < 1 || firstParts > 5 || secondParts < 1 ||
      secondParts > 5 || unitValue < 1 || unitValue > 20) {
    throw new RangeError("Guided ratio parameters are outside supported bounds");
  }
  return {
    firstParts, secondParts, unitValue,
    totalParts: firstParts + secondParts,
    total: (firstParts + secondParts) * unitValue,
    firstShare: firstParts * unitValue,
  };
}

export function classifyRatioAnswer(model, submitted) {
  if (!/^(0|[1-9]\d{0,3})$/.test(submitted.trim())) {
    return { correct: false, misconception: "INVALID_INPUT" };
  }
  const answer = Number(submitted.trim());
  if (answer === model.firstShare) {
    return { correct: true, misconception: null };
  }
  if (answer === model.total) {
    return { correct: false, misconception: "WHOLE_INSTEAD_OF_SHARE" };
  }
  if (answer === model.total / model.firstParts) {
    return { correct: false, misconception: "WRONG_PART_COUNT" };
  }
  return { correct: false, misconception: "RECHECK_UNIT_VALUE" };
}
