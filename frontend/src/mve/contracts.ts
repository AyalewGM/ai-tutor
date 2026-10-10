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

export interface MathAngle {
  kind: "angle";
  id?: string;
  vertex: Point2D;
  start: Point2D;
  end: Point2D;
}

export interface MathFunctionGraph {
  kind: "function_graph";
  id?: string;
  family: "linear" | "quadratic" | "polynomial" | "exponential";
  coefficients?: readonly number[];
  domain?: readonly [number, number];
}

export interface MathRegion {
  kind: "region";
  id?: string;
  boundary: readonly Point2D[];
}

export interface MathNumberLine {
  kind: "number_line";
  id?: string;
  min: number;
  max: number;
  points?: readonly number[];
}

export interface MathFraction {
  kind: "fraction";
  id?: string;
  numerator: number;
  denominator: number;
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
  | MathAngle
  | MathFunctionGraph
  | MathRegion
  | MathNumberLine
  | MathFraction
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

export interface AngleVisualSpec extends VisualSpecBase {
  type: "angle" | "angle_diagram";
  angle?: number;
}

export interface NumberLineVisualSpec extends VisualSpecBase {
  type: "number_line" | "number_line_compare";
  min?: number;
  max?: number;
  point?: number;
  markers?: Array<{ label: string; position: number }>;
}

export interface FractionBarVisualSpec extends VisualSpecBase {
  type: "fraction_bar" | "ratio_bar";
  numerator?: number;
  denominator?: number;
}

export interface AlgebraTilesVisualSpec extends VisualSpecBase {
  type: "algebra_tiles";
  terms?: AlgebraTerm[];
  groups?: Array<{ key: string; terms: AlgebraTerm[] }>;
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

export type SolidKind =
  | "rectangular_prism"
  | "square_pyramid"
  | "rectangular_pyramid"
  | "triangular_prism"
  | "cylinder"
  | "cone"
  | "sphere";

export interface SolidSpec extends VisualSpecBase {
  type: "volume_model" | "volume" | "solid";
  solid: SolidKind;
  l?: number;
  w?: number;
  h?: number;
  b?: number;
  r?: number;
}

export interface XYTableSpec extends VisualSpecBase {
  type: "xy_table";
  pairs?: number[][];
  col_labels?: string[];
}

export interface ProbabilityTreeSpec extends VisualSpecBase {
  type: "probability_tree";
  first_label?: string;
  first_favorable?: number;
  first_total?: number;
  second_label?: string;
  second_favorable?: number;
  second_total?: number;
}

/**
 * Compatibility spec for existing deterministic renderers.
 *
 * New MVE work should add a discriminated interface above and include it in
 * KnownVisualSpec. Existing renderers continue to accept this legacy shape
 * until migrated behind #178 rather than forcing a risky wholesale rewrite.
 */
export interface PanSpec {
  x_count: number;
  units: number;
}

export interface FractionSpec {
  numerator: number;
  denominator: number;
}

export interface TapeSegment {
  label: string;
  span: number;
  highlight: boolean;
}

export interface AlgebraTerm {
  coefficient: number;
  variable?: string | null;
  degree: number;
  label: string;
  sign_changed?: boolean;
}

export interface LegacyVisualSpec extends VisualSpecBase {
  type: string;
  a?: number;
  b?: number;
  result?: number;
  min?: number;
  max?: number;
  numerator?: number;
  denominator?: number;
  x?: number;
  y?: number;
  angle?: number;
  rows?: number;
  columns?: number;
  whole?: number;
  tenths?: number;
  hundredths?: number;
  length?: number;
  width?: number;
  height?: number;
  mode?: "counters" | "squares";
  aria_label?: string;
  operation?: "+" | "-";
  terms?: AlgebraTerm[];
  groups?: Array<{ key: string; terms: AlgebraTerm[] }>;
  left_terms?: AlgebraTerm[];
  right_terms?: AlgebraTerm[];
  transformed_right_terms?: AlgebraTerm[];
  left?: PanSpec;
  right?: PanSpec;
  first?: FractionSpec;
  second?: FractionSpec;
  common_denominator?: number;
  total_label?: string;
  segments?: TapeSegment[];
  m_num?: number;
  m_den?: number;
  labeled?: boolean;
  mark_lattice?: boolean;
  show_slope_triangle?: boolean;
  a_num?: number;
  a_den?: number;
  h?: number;
  k?: number;
  coeffs?: number[];
  roots?: number[];
  mark_roots?: boolean;
  solid?: string;
  l?: number;
  w?: number;
  r?: number;
  kind?: string;
  mark?: string;
  preimage?: number[][];
  image?: number[][];
  labels?: string[];
  image_labels?: string[];
  pre_edge_labels?: (string | null)[];
  image_edge_labels?: (string | null)[];
  lines?: Array<{ m_num: number; m_den: number; i_num: number; i_den: number }>;
  points?: number[][];
  x_max?: number;
  y_max?: number;
  x_min?: number;
  y_min?: number;
  fit?: { m_num: number; m_den: number; i_num: number; i_den: number };
  b_num?: number;
  b_den?: number;
  mark_points?: number[][];
  row_labels?: string[];
  col_labels?: string[];
  cells?: number[][];
  row_totals?: number[];
  col_totals?: number[];
  grand_total?: number;
  sections?: string[];
  marbles?: string[];
  leg_a?: string;
  leg_b?: string;
  hyp?: string;
  markers?: Array<{ label: string; position: number }>;
  point?: number;
  direction?: "left" | "right";
  closed?: boolean;
  data?: number[];
  highlight?: number;
  pairs?: number[][];
  shape?: string;
  base?: number;
  top?: number;
  slant?: number;
  first_label?: string;
  first_favorable?: number;
  first_total?: number;
  second_label?: string;
  second_favorable?: number;
  second_total?: number;
}


export type KnownVisualSpec =
  | CoordinatePlaneSpec
  | AngleVisualSpec
  | NumberLineVisualSpec
  | FractionBarVisualSpec
  | AlgebraTilesVisualSpec
  | LinearGraphSpec
  | TransformationSpec
  | SolidSpec
  | XYTableSpec
  | ProbabilityTreeSpec;

/**
 * Public transition type. The intersection keeps existing call sites source
 * compatible while KnownVisualSpec provides the typed migration target.
 */
export type VisualSpec = LegacyVisualSpec;

export function isKnownVisualSpec(spec: VisualSpec): spec is VisualSpec & KnownVisualSpec {
  return (
    spec.type === "coordinate_plane" ||
    spec.type === "coordinate_point" ||
    spec.type === "angle" ||
    spec.type === "angle_diagram" ||
    spec.type === "number_line" ||
    spec.type === "number_line_compare" ||
    spec.type === "fraction_bar" ||
    spec.type === "ratio_bar" ||
    spec.type === "algebra_tiles" ||
    spec.type === "linear_graph" ||
    spec.type === "transformation" ||
    spec.type === "volume_model" ||
    spec.type === "volume" ||
    spec.type === "solid" ||
    spec.type === "xy_table" ||
    spec.type === "probability_tree"
  );
}
