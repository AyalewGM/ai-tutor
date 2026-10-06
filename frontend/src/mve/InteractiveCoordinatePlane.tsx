import { useState, type KeyboardEvent } from "react";

import type { Point2D } from "./contracts";
import { pointFromInteraction, validateCoordinatePoint, type CoordinateValidationResult } from "./coordinateValidation";
import type { PointPlacedEvent } from "./interactions";

export interface InteractiveCoordinatePlaneProps {
  expected: Point2D;
  min?: number;
  max?: number;
  onResult?: (result: CoordinateValidationResult) => void;
}

export function InteractiveCoordinatePlane({
  expected,
  min = -5,
  max = 5,
  onResult,
}: InteractiveCoordinatePlaneProps) {
  const [point, setPoint] = useState<Point2D | null>(null);
  const [result, setResult] = useState<CoordinateValidationResult | null>(null);
  const [cursor, setCursor] = useState<Point2D>([0, 0]);
  const size = 320;
  const pad = 28;
  const span = max - min;
  const scale = (size - 2 * pad) / span;
  const pos = (v: number) => pad + (v - min) * scale;
  const yPos = (v: number) => size - pos(v);
  const ticks = Array.from({ length: span + 1 }, (_, i) => min + i);

  function selectPoint(placed: Point2D) {
    const event: PointPlacedEvent = { schema_version: 1, type: "POINT_PLACED", point: placed };
    const mathPoint = pointFromInteraction(event);
    if (!mathPoint) return;
    const nextResult = validateCoordinatePoint(mathPoint, expected);
    setPoint(placed);
    setResult(nextResult);
    onResult?.(nextResult);
  }

  function handleKeyDown(event: KeyboardEvent<SVGSVGElement>) {
    const [x, y] = cursor;
    if (event.key === "ArrowLeft") { event.preventDefault(); setCursor([Math.max(min, x - 1), y]); }
    else if (event.key === "ArrowRight") { event.preventDefault(); setCursor([Math.min(max, x + 1), y]); }
    else if (event.key === "ArrowUp") { event.preventDefault(); setCursor([x, Math.min(max, y + 1)]); }
    else if (event.key === "ArrowDown") { event.preventDefault(); setCursor([x, Math.max(min, y - 1)]); }
    else if (event.key === "Enter" || event.key === " ") { event.preventDefault(); selectPoint(cursor); }
  }

  function placePoint(clientX: number, clientY: number, svg: SVGSVGElement) {
    const rect = svg.getBoundingClientRect();
    const sx = ((clientX - rect.left) / rect.width) * size;
    const sy = ((clientY - rect.top) / rect.height) * size;
    const x = Math.max(min, Math.min(max, Math.round(min + (sx - pad) / scale)));
    const y = Math.max(min, Math.min(max, Math.round(min + (size - sy - pad) / scale)));
    selectPoint([x, y]);
  }

  return (
    <div>
      <svg
        viewBox={`0 0 ${size} ${size}`}
        className="visual"
        role="application"
        aria-label={`Interactive coordinate plane. Keyboard cursor at (\${cursor[0]}, \${cursor[1]}). Use arrow keys to move and Enter or Space to place the point.`}
        tabIndex={0}
        onKeyDown={handleKeyDown}
        onClick={(event) => placePoint(event.clientX, event.clientY, event.currentTarget)}
      >
        {ticks.map((t) => (
          <g key={t}>
            <line x1={pad} y1={yPos(t)} x2={size - pad} y2={yPos(t)} className="viz-grid" />
            <line x1={pos(t)} y1={pad} x2={pos(t)} y2={size - pad} className="viz-grid" />
          </g>
        ))}
        <line x1={pad} y1={yPos(0)} x2={size - pad} y2={yPos(0)} className="viz-axis" />
        <line x1={pos(0)} y1={pad} x2={pos(0)} y2={size - pad} className="viz-axis" />
        <circle cx={pos(cursor[0])} cy={yPos(cursor[1])} r="8" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" />
        {point && <circle cx={pos(point[0])} cy={yPos(point[1])} r="6" className="viz-point viz-point-a" />}
      </svg>
      <p>Keyboard: arrow keys move the mathematical cursor; Enter or Space places the point.</p>
      {point && (
        <p aria-live="polite">
          Point ({point[0]}, {point[1]}): {result?.correct ? "correct" : "try again"}
        </p>
      )}
    </div>
  );
}
