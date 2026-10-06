import type { MathObject, MathPoint, MathPolygon, MathSegment, MathTransformation, Point2D } from "./contracts";

function point(value: unknown, fallback: Point2D = [0, 0]): Point2D {
  return Array.isArray(value) && value.length === 2 &&
    typeof value[0] === "number" && typeof value[1] === "number"
    ? [value[0], value[1]]
    : fallback;
}

function transformPoint([x, y]: Point2D, transform: MathTransformation): Point2D {
  const p = transform.parameters;
  switch (transform.transformation) {
    case "translation": {
      const [dx, dy] = point(p.vector, [
        typeof p.dx === "number" ? p.dx : 0,
        typeof p.dy === "number" ? p.dy : 0,
      ]);
      return [x + dx, y + dy];
    }
    case "rotation": {
      const angle = typeof p.angle === "number" ? p.angle : 0;
      const [cx, cy] = point(p.center);
      const radians = angle * Math.PI / 180;
      const dx = x - cx;
      const dy = y - cy;
      return [
        cx + dx * Math.cos(radians) - dy * Math.sin(radians),
        cy + dx * Math.sin(radians) + dy * Math.cos(radians),
      ];
    }
    case "reflection": {
      const axis = p.axis;
      if (axis === "x") return [x, -y];
      if (axis === "y") return [-x, y];
      if (axis === "y=x") return [y, x];
      return [x, y];
    }
    case "dilation": {
      const scale = typeof p.scale === "number" ? p.scale : 1;
      const [cx, cy] = point(p.center);
      return [cx + (x - cx) * scale, cy + (y - cy) * scale];
    }
  }
}

export function applyMathTransformation(transform: MathTransformation): MathObject {
  const source = transform.source;
  if (source.kind === "point") {
    const [x, y] = transformPoint([source.x, source.y], transform);
    return { ...source, x, y } satisfies MathPoint;
  }
  if (source.kind === "segment") {
    return {
      ...source,
      start: transformPoint(source.start, transform),
      end: transformPoint(source.end, transform),
    } satisfies MathSegment;
  }
  if (source.kind === "polygon") {
    return {
      ...source,
      vertices: source.vertices.map((vertex) => transformPoint(vertex, transform)),
    } satisfies MathPolygon;
  }
  return source;
}
