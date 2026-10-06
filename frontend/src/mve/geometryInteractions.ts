import type { MathPolygon, MathSegment } from "./contracts";
import type { MathInteractionEvent } from "./interactions";

export function geometryObjectFromInteraction(
  event: MathInteractionEvent,
): MathSegment | MathPolygon | null {
  if (event.type === "SEGMENT_CREATED") {
    return {
      kind: "segment",
      id: event.object_id,
      start: event.start,
      end: event.end,
    };
  }
  if (event.type === "POLYGON_CREATED") {
    return {
      kind: "polygon",
      id: event.object_id,
      vertices: event.vertices,
    };
  }
  return null;
}
