import type { MathPoint, Point2D } from "./contracts";
import type { MathInteractionEvent } from "./interactions";

export type CoordinateMisconception =
  | "X_COORDINATE_ERROR"
  | "Y_COORDINATE_ERROR"
  | "COORDINATES_SWAPPED"
  | "SIGN_ERROR";

export interface CoordinateValidationResult {
  correct: boolean;
  expected: Point2D;
  actual: Point2D;
  misconception?: CoordinateMisconception;
}

export function pointFromInteraction(event: MathInteractionEvent): MathPoint | null {
  if (event.type === "POINT_PLACED") {
    return { kind: "point", id: event.object_id, x: event.point[0], y: event.point[1] };
  }
  if (event.type === "POINT_MOVED") {
    return { kind: "point", id: event.object_id, x: event.to[0], y: event.to[1] };
  }
  return null;
}

export function validateCoordinatePoint(
  actual: MathPoint,
  expected: Point2D,
): CoordinateValidationResult {
  const actualPoint: Point2D = [actual.x, actual.y];
  if (actual.x === expected[0] && actual.y === expected[1]) {
    return { correct: true, expected, actual: actualPoint };
  }

  let misconception: CoordinateMisconception | undefined;
  if (actual.x === expected[1] && actual.y === expected[0]) {
    misconception = "COORDINATES_SWAPPED";
  } else if (
    (actual.x === -expected[0] && actual.y === expected[1]) ||
    (actual.x === expected[0] && actual.y === -expected[1])
  ) {
    misconception = "SIGN_ERROR";
  } else if (actual.x !== expected[0] && actual.y === expected[1]) {
    misconception = "X_COORDINATE_ERROR";
  } else if (actual.x === expected[0] && actual.y !== expected[1]) {
    misconception = "Y_COORDINATE_ERROR";
  }

  return { correct: false, expected, actual: actualPoint, misconception };
}
