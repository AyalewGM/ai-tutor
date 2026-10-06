import type { MathLine, MathSegment, Point2D } from "./contracts";

const EPSILON = 1e-9;

export type GeometryMisconception =
  | "NOT_COLLINEAR"
  | "NOT_PARALLEL"
  | "NOT_PERPENDICULAR"
  | "DEGENERATE_CONSTRUCTION";

export interface GeometryValidationResult {
  correct: boolean;
  misconception?: GeometryMisconception;
}

function vector(start: Point2D, end: Point2D): Point2D {
  return [end[0] - start[0], end[1] - start[1]];
}

function isZero([x, y]: Point2D): boolean {
  return Math.abs(x) < EPSILON && Math.abs(y) < EPSILON;
}

function cross([ax, ay]: Point2D, [bx, by]: Point2D): number {
  return ax * by - ay * bx;
}

function dot([ax, ay]: Point2D, [bx, by]: Point2D): number {
  return ax * bx + ay * by;
}

export function validateCollinear(points: readonly [Point2D, Point2D, Point2D]): GeometryValidationResult {
  const a = vector(points[0], points[1]);
  const b = vector(points[0], points[2]);
  if (isZero(a) || isZero(b)) return { correct: false, misconception: "DEGENERATE_CONSTRUCTION" };
  return Math.abs(cross(a, b)) < EPSILON
    ? { correct: true }
    : { correct: false, misconception: "NOT_COLLINEAR" };
}

type LinearObject = MathSegment | MathLine;

function direction(object: LinearObject): Point2D | null {
  if (object.kind === "segment") return vector(object.start, object.end);
  if (object.through) return vector(object.through[0], object.through[1]);
  if (object.slope !== undefined) return [1, object.slope];
  return null;
}

export function validateParallel(a: LinearObject, b: LinearObject): GeometryValidationResult {
  const av = direction(a);
  const bv = direction(b);
  if (!av || !bv || isZero(av) || isZero(bv)) {
    return { correct: false, misconception: "DEGENERATE_CONSTRUCTION" };
  }
  return Math.abs(cross(av, bv)) < EPSILON
    ? { correct: true }
    : { correct: false, misconception: "NOT_PARALLEL" };
}

export function validatePerpendicular(a: LinearObject, b: LinearObject): GeometryValidationResult {
  const av = direction(a);
  const bv = direction(b);
  if (!av || !bv || isZero(av) || isZero(bv)) {
    return { correct: false, misconception: "DEGENERATE_CONSTRUCTION" };
  }
  return Math.abs(dot(av, bv)) < EPSILON
    ? { correct: true }
    : { correct: false, misconception: "NOT_PERPENDICULAR" };
}
