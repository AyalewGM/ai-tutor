export interface EquivalenceModel {
  numerator: number;
  denominator: number;
  scale: number;
  expandedNumerator: number;
  expandedDenominator: number;
}
export interface RatioModel {
  firstParts: number;
  secondParts: number;
  unitValue: number;
  totalParts: number;
  total: number;
  firstShare: number;
}
export interface GuidedAnswerResult {
  correct: boolean;
  misconception: string | null;
}
export function equivalenceModel(
  numerator: number, denominator: number, scale: number,
): EquivalenceModel;
export function classifyEquivalentAnswer(
  model: EquivalenceModel, submitted: string,
): GuidedAnswerResult;
export function ratioPartitionModel(
  firstParts: number, secondParts: number, unitValue: number,
): RatioModel;
export function classifyRatioAnswer(
  model: RatioModel, submitted: string,
): GuidedAnswerResult;
