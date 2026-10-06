/**
 * Mihur Math Visual Engine contracts.
 *
 * This module is intentionally renderer-independent. It is the compatibility
 * boundary while the legacy flat visual payloads are migrated incrementally
 * to discriminated specifications (MVE #177).
 */

export type Point2D = readonly [number, number];

export interface MathPoint {
  kind: "point";
  id?: string;
  x: number;
  y: number;
}

export interface MathLine {
  kind: "line";
  id?: string;
  through?: readonly [Point2D, Point2D];
  slope?: number;
  yIntercept?: number;
}

export interface MathSegment {
  kind: "segment";
  id?: string;
  start: Point2D;
  end: Point2D;
}

export interface MathPolygon {
  kind: "polygon";
  id?: string;
  vertices: readonly Point2D[];
}

export interface MathTransformation {
  kind: "transformation";
  id?: string;
  transformation: "translation" | "rotation" | "reflection" | "dilation";
  source: MathObject;
  parameters: Readonly<Record<string, number | string | Point2D>>;
}

export type MathObject =
  | MathPoint
  | MathLine
  | MathSegment
  | MathPolygon
  | MathTransformation;

export interface VisualSpecBase {
  type: string;
  aria_label?: string;
  /** Optional renderer-independent mathematical source for migrated specs. */
  math?: MathObject | readonly MathObject[];
  /** Contract version for persisted/replayed visual work. */
  schema_version?: 1;
}

export interface CoordinatePlaneSpec extends VisualSpecBase {
  type: "coordinate_plane" | "coordinate_point";
  x?: number;
  y?: number;
  min?: number;
  max?: number;
}

export interface LinearGraphSpec extends VisualSpecBase {
  type: "linear_graph";
  m_num?: number;
  m_den?: number;
  b?: number;
  min?: number;
  max?: number;
}

export interface TransformationSpec extends VisualSpecBase {
  type: "transformation";
  preimage: number[][];
  image?: number[][];
  labels?: string[];
  image_labels?: string[];
}

export interface XYTableSpec extends VisualSpecBase {
  type: "xy_table";
  pairs?: number[][];
  col_labels?: string[];
}

/**
 * Compatibility spec for existing deterministic renderers.
 *
 * New MVE work should add a discriminated interface above and include it in
 * KnownVisualSpec. Existing renderers continue to accept this legacy shape
 * until migrated behind #178 rather than forcing a risky wholesale rewrite.
 */
export interface LegacyVisualSpec extends VisualSpecBase {
  [key: string]: unknown;
}

export type KnownVisualSpec =
  | CoordinatePlaneSpec
  | LinearGraphSpec
  | TransformationSpec
  | XYTableSpec;

/**
 * Public transition type. The intersection keeps existing call sites source
 * compatible while KnownVisualSpec provides the typed migration target.
 */
export type VisualSpec = KnownVisualSpec | LegacyVisualSpec;

export function isKnownVisualSpec(spec: VisualSpec): spec is KnownVisualSpec {
  return (
    spec.type === "coordinate_plane" ||
    spec.type === "coordinate_point" ||
    spec.type === "linear_graph" ||
    spec.type === "transformation" ||
    spec.type === "xy_table"
  );
}
