import type { MathAnimationSpec } from "./animation";
import { buildAnimationFrames } from "./animationFrames";
import type { MathPolygon, Point2D } from "./contracts";
import { PedagogicalAnimation } from "./PedagogicalAnimation";

const triangle: MathPolygon = {
  kind: "polygon",
  id: "triangle-a",
  vertices: [[1, 1], [3, 1], [2, 3]],
};

export const triangleTranslationAnimation: MathAnimationSpec = {
  schema_version: 1,
  purpose: "See how every vertex of a triangle moves by the same translation vector.",
  objects: [triangle],
  reduced_motion: "step_without_motion",
  steps: [
    {
      id: "identify-preimage",
      duration_ms: 1200,
      description: "Start with triangle A at (1,1), (3,1), and (2,3).",
    },
    {
      id: "translate",
      duration_ms: 1600,
      description: "Translate every vertex 2 units right and 1 unit up.",
      transformation: {
        kind: "transformation",
        transformation: "translation",
        source: triangle,
        parameters: { vector: [2, 1] as Point2D },
      },
    },
  ],
};

function polygonPoints(polygon: MathPolygon, min: number, max: number, size: number): string {
  const span = max - min;
  const posX = (x: number) => ((x - min) / span) * size;
  const posY = (y: number) => ((max - y) / span) * size;
  return polygon.vertices.map(([x, y]) => `${posX(x)},${posY(y)}`).join(" ");
}

export function TriangleTranslationExplanation() {
  const frames = buildAnimationFrames(triangleTranslationAnimation);
  const finalTriangle = frames.at(-1)?.objects.find(
    (object): object is MathPolygon => object.kind === "polygon" && object.id === triangle.id,
  );
  const size = 320;
  const min = 0;
  const max = 6;
  const ticks = Array.from({ length: max - min + 1 }, (_, index) => min + index);

  return (
    <section aria-label="Triangle translation explanation">
      <PedagogicalAnimation spec={triangleTranslationAnimation} />
      <svg
        viewBox={`0 0 ${size} ${size}`}
        role="img"
        aria-label="Triangle A translated two units right and one unit up to triangle A prime."
      >
        {ticks.map((tick) => {
          const position = ((tick - min) / (max - min)) * size;
          return (
            <g key={tick}>
              <line x1={position} y1={0} x2={position} y2={size} stroke="currentColor" opacity={0.12} />
              <line x1={0} y1={position} x2={size} y2={position} stroke="currentColor" opacity={0.12} />
            </g>
          );
        })}
        <polygon points={polygonPoints(triangle, min, max, size)} fill="none" stroke="currentColor" strokeWidth={2} strokeDasharray="6 4" />
        {finalTriangle && (
          <polygon points={polygonPoints(finalTriangle, min, max, size)} fill="none" stroke="currentColor" strokeWidth={3} />
        )}
      </svg>
      {finalTriangle && (
        <p>
          Final coordinates: {finalTriangle.vertices.map(([x, y]) => `(${x}, ${y})`).join(", ")}.
        </p>
      )}
    </section>
  );
}
