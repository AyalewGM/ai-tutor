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

export interface FractionComparedEvent extends MathInteractionBase {
  type: "FRACTION_COMPARED";
  left: { numerator: number; denominator: number };
  right: { numerator: number; denominator: number };
  relation: "LESS_THAN" | "EQUAL_TO" | "GREATER_THAN";
}

export interface FractionEquivalenceExploredEvent extends MathInteractionBase {
  type: "FRACTION_EQUIVALENCE_EXPLORED";
  original: { numerator: number; denominator: number };
  scaled: { numerator: number; denominator: number };
  scale_factor: number;
}

export type MathInteractionEvent =
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
  | FractionShadingChangedEvent
  | FractionComparedEvent
  | FractionEquivalenceExploredEvent;

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
    case "FRACTION_COMPARED": {
      const valid = (v: unknown): v is { numerator: number; denominator: number } => {
        if (!v || typeof v !== "object") return false;
        const p = v as Record<string, unknown>;
        return Number.isSafeInteger(p.denominator) && (p.denominator as number) >= 1 &&
          (p.denominator as number) <= 12 && Number.isSafeInteger(p.numerator) &&
          (p.numerator as number) >= 0 && (p.numerator as number) <= (p.denominator as number);
      };
      if (!valid(event.left) || !valid(event.right)) return false;
      const a = event.left.numerator * event.right.denominator;
      const b = event.right.numerator * event.left.denominator;
      return event.relation === (a < b ? "LESS_THAN" : a > b ? "GREATER_THAN" : "EQUAL_TO");
    }
    case "FRACTION_EQUIVALENCE_EXPLORED": {
      const valid = (v: unknown): v is { numerator: number; denominator: number } => {
        if (!v || typeof v !== "object") return false;
        const p = v as Record<string, unknown>;
        return Number.isSafeInteger(p.denominator) && (p.denominator as number) >= 1 &&
          (p.denominator as number) <= 12 && Number.isSafeInteger(p.numerator) &&
          (p.numerator as number) >= 0 && (p.numerator as number) <= (p.denominator as number);
      };
      if (!valid(event.original) || !valid(event.scaled)) return false;
      const k = event.scale_factor;
      if (!Number.isSafeInteger(k) || (k as number) < 2) return false;
      // Fabricated equivalences fail: scaled parts must equal original * k exactly.
      return event.scaled.numerator === event.original.numerator * (k as number) &&
        event.scaled.denominator === event.original.denominator * (k as number);
    }
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
