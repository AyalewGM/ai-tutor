export type InkPoint = { x: number; y: number };

/** Quadratic segments stay inside the recorded points' convex hull. */
export function inkPath(points: InkPoint[]): string {
  if (!points.length) return "";
  const first = points[0];
  let path = `M ${first.x} ${first.y}`;
  if (points.length === 1) return `${path} l 0.01 0`;
  for (let i = 1; i < points.length - 1; i++) {
    const p = points[i],
      next = points[i + 1];
    path += ` Q ${p.x} ${p.y} ${(p.x + next.x) / 2} ${(p.y + next.y) / 2}`;
  }
  const last = points[points.length - 1];
  return `${path} L ${last.x} ${last.y}`;
}

/** Full preview snapshots recover from dropped frames without a growing queue. */
export function previewPoints(points: InkPoint[]): InkPoint[] {
  if (points.length <= 128) return points;
  return Array.from(
    { length: 128 },
    (_, i) => points[Math.round((i * (points.length - 1)) / 127)],
  );
}
