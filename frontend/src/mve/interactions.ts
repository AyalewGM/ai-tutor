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
  misconception: "MISSED_SECOND_TERM" | "COEFFICIENT_ERROR" | "CONSTANT_ERROR" | null;
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

export interface ExplorerDatasetChangedEvent extends MathInteractionBase {
  type: "EXPLORER_DATASET_CHANGED";
  values: readonly number[];
}

export interface ProbabilityTreeChangedEvent extends MathInteractionBase {
  type: "PROBABILITY_TREE_CHANGED";
  first_favorable: number;
  first_total: number;
  second_favorable: number;
  second_total: number;
}

export type MathInteractionEvent =
  | ProbabilityTreeChangedEvent
  | ExplorerDatasetChangedEvent
  | BalanceOperationAppliedEvent
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
    case "PROBABILITY_TREE_CHANGED":
      return Object.keys(event).every(key => [
        "schema_version", "type", "first_favorable", "first_total", "second_favorable", "second_total",
      ].includes(key)) &&
        [event.first_favorable, event.first_total, event.second_favorable, event.second_total].every(Number.isSafeInteger) &&
        (event.first_total as number) >= 2 && (event.first_total as number) <= 12 &&
        (event.second_total as number) >= 2 && (event.second_total as number) <= 12 &&
        (event.first_favorable as number) >= 1 && (event.first_favorable as number) < (event.first_total as number) &&
        (event.second_favorable as number) >= 1 && (event.second_favorable as number) < (event.second_total as number);
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
          ["MISSED_SECOND_TERM", "COEFFICIENT_ERROR", "CONSTANT_ERROR"].includes(String(event.misconception))) &&
        event.correct === (event.misconception === null);
    default:
      return false;
  }
}
