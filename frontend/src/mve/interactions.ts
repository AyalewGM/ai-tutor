import type { IntegerOperation } from "./integerNumberLine";
import type { MathObject, Point2D } from "./contracts";

/**
 * Renderer-independent learner interaction evidence.
 *
 * Raw pointer/touch coordinates belong to the UI adapter. Only normalized
 * mathematical actions cross this boundary or become persisted evidence.
 */
export interface MathInteractionBase {
  schema_version: 1;
  object_id?: string;
}

export interface PointPlacedEvent extends MathInteractionBase {
  type: "POINT_PLACED";
  point: Point2D;
}

export interface PointMovedEvent extends MathInteractionBase {
  type: "POINT_MOVED";
  from: Point2D;
  to: Point2D;
}

export interface SegmentCreatedEvent extends MathInteractionBase {
  type: "SEGMENT_CREATED";
  start: Point2D;
  end: Point2D;
}

export interface LineCreatedEvent extends MathInteractionBase {
  type: "LINE_CREATED";
  through: readonly [Point2D, Point2D];
}

export interface VertexMovedEvent extends MathInteractionBase {
  type: "VERTEX_MOVED";
  vertex_index: number;
  from: Point2D;
  to: Point2D;
}

export interface TransformationAppliedEvent extends MathInteractionBase {
  type: "TRANSFORMATION_APPLIED";
  transformation: "translation" | "rotation" | "reflection" | "dilation";
  parameters: Readonly<Record<string, number | string | Point2D>>;
}

export interface RegionSelectedEvent extends MathInteractionBase {
  type: "REGION_SELECTED";
  region: MathObject;
}

export interface PolygonCreatedEvent extends MathInteractionBase {
  type: "POLYGON_CREATED";
  vertices: readonly Point2D[];
}

/** Semantic algebra actions: never raw text, coordinates, or child identifiers. */
export interface DistributiveStepViewedEvent extends MathInteractionBase {
  type: "DISTRIBUTIVE_STEP_VIEWED";
  step_id: string;
}

export interface DistributiveCoefficientsCheckedEvent extends MathInteractionBase {
  type: "DISTRIBUTIVE_COEFFICIENTS_CHECKED";
  variable_coefficient: number;
  constant_term: number;
  correct: boolean;
  misconception: "MISSED_SECOND_TERM" | "DROPPED_NEGATIVE" | "COEFFICIENT_ERROR" | "CONSTANT_ERROR" | null;
}

export interface FractionShadingChangedEvent extends MathInteractionBase {
  type: "FRACTION_SHADING_CHANGED";
  numerator: number;
  denominator: number;
}

export interface IntegerDisplacementChangedEvent extends MathInteractionBase {
  type: "INTEGER_DISPLACEMENT_CHANGED";
  start: number;
  operand: number;
  operation: IntegerOperation;
  displacement: number;
  result: number;
}

export interface LinearParametersChangedEvent extends MathInteractionBase {
  type: "LINEAR_PARAMETERS_CHANGED";
  rise: number;
  run: number;
  intercept: number;
}

export interface BalanceOperationAppliedEvent extends MathInteractionBase {
  type: "BALANCE_OPERATION_APPLIED";
  operation: "add_unit" | "remove_unit" | "remove_x" | "divide_two" | "divide_three";
  left_x: number; left_units: number; right_x: number; right_units: number;
}

export interface EquationTransformationAppliedEvent extends MathInteractionBase {
  type: "EQUATION_TRANSFORMATION_APPLIED";
  operation: "ADD_CONSTANT_BOTH" | "ADD_VARIABLE_BOTH" | "SCALE_BOTH";
  amount_numerator: number;
  amount_denominator: number;
  preserved: true;
}

export interface EquationAttemptDiagnosedEvent extends MathInteractionBase {
  type: "EQUATION_ATTEMPT_DIAGNOSED";
  diagnosis: "EQ.OP.ONE_SIDE" | "EQ.DENOMINATOR_IGNORED" | "EQ.FALSE_EQUIVALENCE";
  phase: "MANIPULATE" | "FRESH_EXIT";
}

export interface ExactPolynomialTermEvidence {
  coefficient: { numerator: number; denominator: number };
  xExponent: number;
  yExponent: number;
}

export interface PolynomialTermDividedEvent extends MathInteractionBase {
  type: "POLYNOMIAL_TERM_DIVIDED";
  term_index: number;
  dividend: ExactPolynomialTermEvidence;
  divisor: ExactPolynomialTermEvidence;
  quotient: ExactPolynomialTermEvidence;
}

export interface PolynomialDivisionDiagnosedEvent extends MathInteractionBase {
  type: "POLYNOMIAL_DIVISION_DIAGNOSED";
  diagnosis: "POLY.DIV.COEFFICIENT_RECIPROCAL" | "POLY.DIV.ADD_EXPONENTS" |
    "POLY.DIV.ONE_TERM_ONLY" | "POLY.DIV.DOMAIN_OMITTED";
  phase: "DIAGNOSE" | "FRESH_EXIT";
}

export interface ExplorerDatasetChangedEvent extends MathInteractionBase {
  type: "EXPLORER_DATASET_CHANGED";
  values: readonly number[];
}

export type MathInteractionEvent =
  | ExplorerDatasetChangedEvent
  | BalanceOperationAppliedEvent
  | EquationTransformationAppliedEvent
  | EquationAttemptDiagnosedEvent
  | PolynomialTermDividedEvent
  | PolynomialDivisionDiagnosedEvent
  | LinearParametersChangedEvent
  | IntegerDisplacementChangedEvent
  | PointPlacedEvent
  | PointMovedEvent
  | SegmentCreatedEvent
  | LineCreatedEvent
  | VertexMovedEvent
  | TransformationAppliedEvent
  | RegionSelectedEvent
  | PolygonCreatedEvent
  | DistributiveStepViewedEvent
  | DistributiveCoefficientsCheckedEvent
  | FractionShadingChangedEvent;

function isPoint2D(value: unknown): value is Point2D {
  return Array.isArray(value) &&
    value.length === 2 &&
    value.every((coordinate) => typeof coordinate === "number" && Number.isFinite(coordinate));
}

export function isMathInteractionEvent(value: unknown): value is MathInteractionEvent {
  if (!value || typeof value !== "object") return false;
  const event = value as Record<string, unknown>;
  if (event.schema_version !== 1 || typeof event.type !== "string") return false;
  switch (event.type) {
    case "POLYNOMIAL_DIVISION_DIAGNOSED":
      return Object.keys(event).every(key => ["schema_version", "type", "diagnosis", "phase"].includes(key)) &&
        ["POLY.DIV.COEFFICIENT_RECIPROCAL", "POLY.DIV.ADD_EXPONENTS", "POLY.DIV.ONE_TERM_ONLY", "POLY.DIV.DOMAIN_OMITTED"].includes(String(event.diagnosis)) &&
        ["DIAGNOSE", "FRESH_EXIT"].includes(String(event.phase));
    case "POLYNOMIAL_TERM_DIVIDED": {
      if (!Object.keys(event).every(key => ["schema_version", "type", "term_index", "dividend", "divisor", "quotient"].includes(key)) ||
          !Number.isSafeInteger(event.term_index) || (event.term_index as number) < 0 || (event.term_index as number) > 3) return false;
      const parseTerm = (value: unknown) => {
        if (!value || typeof value !== "object") return null;
        const candidate = value as Record<string, unknown>;
        if (!Object.keys(candidate).every(key => ["coefficient", "xExponent", "yExponent"].includes(key)) ||
            Object.keys(candidate).length !== 3 || !candidate.coefficient || typeof candidate.coefficient !== "object") return null;
        const coefficient = candidate.coefficient as Record<string, unknown>;
        if (!Object.keys(coefficient).every(key => ["numerator", "denominator"].includes(key)) || Object.keys(coefficient).length !== 2 ||
            !Number.isSafeInteger(coefficient.numerator) || !Number.isSafeInteger(coefficient.denominator) ||
            Math.abs(coefficient.numerator as number) > 10000 ||
            (coefficient.denominator as number) < 1 || (coefficient.denominator as number) > 10000 || coefficient.numerator === 0 ||
            !Number.isSafeInteger(candidate.xExponent) || Math.abs(candidate.xExponent as number) > 12 ||
            !Number.isSafeInteger(candidate.yExponent) || Math.abs(candidate.yExponent as number) > 12) return null;
        let a = Math.abs(coefficient.numerator as number), b = coefficient.denominator as number;
        while (b) { const remainder = a % b; a = b; b = remainder; }
        if (a !== 1) return null;
        return candidate as unknown as ExactPolynomialTermEvidence;
      };
      const dividend = parseTerm(event.dividend), divisor = parseTerm(event.divisor), quotient = parseTerm(event.quotient);
      if (!dividend || !divisor || !quotient) return false;
      const crossEqual = (leftNumerator: number, leftDenominator: number, rightNumerator: number, rightDenominator: number) =>
        leftNumerator * rightDenominator === rightNumerator * leftDenominator;
      return crossEqual(
        dividend.coefficient.numerator * divisor.coefficient.denominator,
        dividend.coefficient.denominator * divisor.coefficient.numerator,
        quotient.coefficient.numerator,
        quotient.coefficient.denominator,
      ) && quotient.xExponent === dividend.xExponent - divisor.xExponent &&
        quotient.yExponent === dividend.yExponent - divisor.yExponent;
    }
    case "EQUATION_ATTEMPT_DIAGNOSED":
      return Object.keys(event).every(key => ["schema_version", "type", "diagnosis", "phase"].includes(key)) &&
        ["EQ.OP.ONE_SIDE", "EQ.DENOMINATOR_IGNORED", "EQ.FALSE_EQUIVALENCE"].includes(String(event.diagnosis)) &&
        ["MANIPULATE", "FRESH_EXIT"].includes(String(event.phase));
    case "EQUATION_TRANSFORMATION_APPLIED":
      return Object.keys(event).every(key => ["schema_version", "type", "operation", "amount_numerator", "amount_denominator", "preserved"].includes(key)) &&
        ["ADD_CONSTANT_BOTH", "ADD_VARIABLE_BOTH", "SCALE_BOTH"].includes(String(event.operation)) &&
        Number.isSafeInteger(event.amount_numerator) && Math.abs(event.amount_numerator as number) <= 10000 &&
        Number.isSafeInteger(event.amount_denominator) && (event.amount_denominator as number) >= 1 && (event.amount_denominator as number) <= 10000 &&
        event.preserved === true && !(event.operation === "SCALE_BOTH" && event.amount_numerator === 0);
    case "EXPLORER_DATASET_CHANGED":
      return Object.keys(event).every(key => ["schema_version", "type", "values"].includes(key)) &&
        Array.isArray(event.values) && event.values.length >= 1 && event.values.length <= 6 &&
        Array.from(event.values).every(value => Number.isSafeInteger(value) && value >= 0 && value <= 12);
    case "BALANCE_OPERATION_APPLIED": {
      if (!Object.keys(event).every(key => ["schema_version", "type", "operation", "left_x", "left_units", "right_x", "right_units"].includes(key))) return false;
      const values = [event.left_x, event.left_units, event.right_x, event.right_units];
      if (!values.every(Number.isSafeInteger)) return false;
      const [lx, lu, rx, ru] = values as number[];
      if (rx < 0 || lx > 3 || lx <= rx || lu < 0 || ru > 12 || ru < lu) return false;
      if (event.operation === "add_unit") return ru < 12;
      if (event.operation === "remove_unit") return lu > 0;
      if (event.operation === "remove_x") return rx > 0;
      const divisor = event.operation === "divide_two" ? 2 : event.operation === "divide_three" ? 3 : 0;
      return divisor > 0 && (values as number[]).every(value => value % divisor === 0);
    }
    case "LINEAR_PARAMETERS_CHANGED":
      return Object.keys(event).every(key => ["schema_version", "type", "rise", "run", "intercept"].includes(key)) &&
        Number.isSafeInteger(event.rise) && Math.abs(event.rise as number) <= 6 &&
        Number.isSafeInteger(event.run) && (event.run as number) >= 1 && (event.run as number) <= 6 &&
        Number.isSafeInteger(event.intercept) && Math.abs(event.intercept as number) <= 4;
    case "INTEGER_DISPLACEMENT_CHANGED": {
      if (Object.keys(event).some(key => !["schema_version", "type", "start", "operand", "operation", "displacement", "result"].includes(key))) return false;
      if (![event.start, event.operand].every(v => Number.isSafeInteger(v) && Math.abs(v as number) <= 10) ||
          (event.operation !== "add" && event.operation !== "subtract")) return false;
      const delta = event.operation === "add" ? event.operand as number : -(event.operand as number);
      return event.displacement === delta && event.result === (event.start as number) + delta;
    }
    case "POINT_PLACED":
      return isPoint2D(event.point);
    case "POINT_MOVED":
      return isPoint2D(event.from) && isPoint2D(event.to);
    case "SEGMENT_CREATED":
      return isPoint2D(event.start) && isPoint2D(event.end);
    case "LINE_CREATED":
      return Array.isArray(event.through) && event.through.length === 2 &&
        event.through.every(isPoint2D);
    case "VERTEX_MOVED":
      return Number.isInteger(event.vertex_index) && (event.vertex_index as number) >= 0 &&
        isPoint2D(event.from) && isPoint2D(event.to);
    case "TRANSFORMATION_APPLIED":
      return ["translation", "rotation", "reflection", "dilation"].includes(String(event.transformation)) &&
        !!event.parameters && typeof event.parameters === "object";
    case "REGION_SELECTED":
      return !!event.region && typeof event.region === "object";
    case "POLYGON_CREATED":
      return Array.isArray(event.vertices) && event.vertices.length >= 3 &&
        event.vertices.every(isPoint2D);
    case "FRACTION_SHADING_CHANGED":
      return Number.isSafeInteger(event.denominator) &&
        (event.denominator as number) >= 1 && (event.denominator as number) <= 12 &&
        Number.isSafeInteger(event.numerator) &&
        (event.numerator as number) >= 0 &&
        (event.numerator as number) <= (event.denominator as number);
    case "DISTRIBUTIVE_STEP_VIEWED":
      return typeof event.step_id === "string" &&
        ["identify", "distribute_variable", "distribute_constant", "simplify"].includes(event.step_id);
    case "DISTRIBUTIVE_COEFFICIENTS_CHECKED":
      return Number.isSafeInteger(event.variable_coefficient) &&
        Number.isSafeInteger(event.constant_term) &&
        Math.abs(event.variable_coefficient as number) <= 10000 &&
        Math.abs(event.constant_term as number) <= 10000 &&
        typeof event.correct === "boolean" &&
        (event.misconception === null ||
          ["MISSED_SECOND_TERM", "DROPPED_NEGATIVE", "COEFFICIENT_ERROR", "CONSTANT_ERROR"].includes(String(event.misconception))) &&
        event.correct === (event.misconception === null);
    default:
      return false;
  }
}
