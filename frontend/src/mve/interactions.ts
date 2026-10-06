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

export type MathInteractionEvent =
  | PointPlacedEvent
  | PointMovedEvent
  | SegmentCreatedEvent
  | LineCreatedEvent
  | VertexMovedEvent
  | TransformationAppliedEvent
  | RegionSelectedEvent;

export function isMathInteractionEvent(value: unknown): value is MathInteractionEvent {
  if (!value || typeof value !== "object") return false;
  const event = value as { schema_version?: unknown; type?: unknown };
  return (
    event.schema_version === 1 &&
    typeof event.type === "string" &&
    [
      "POINT_PLACED",
      "POINT_MOVED",
      "SEGMENT_CREATED",
      "LINE_CREATED",
      "VERTEX_MOVED",
      "TRANSFORMATION_APPLIED",
      "REGION_SELECTED",
    ].includes(event.type)
  );
}
