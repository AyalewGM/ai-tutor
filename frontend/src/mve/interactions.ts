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

export type MathInteractionEvent =
  | PointPlacedEvent
  | PointMovedEvent
  | SegmentCreatedEvent
  | LineCreatedEvent
  | VertexMovedEvent
  | TransformationAppliedEvent
  | RegionSelectedEvent
  | PolygonCreatedEvent;

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
    default:
      return false;
  }
}
