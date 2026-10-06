import { useMemo, useState } from "react";
import type { Point2D } from "./contracts";
import { geometryObjectFromInteraction } from "./geometryInteractions";
import type { MathInteractionEvent } from "./interactions";

export interface InteractiveGeometryWorkspaceProps {
  min?: number;
  max?: number;
  onObjectCreated?: (object: ReturnType<typeof geometryObjectFromInteraction>) => void;
}

export function InteractiveGeometryWorkspace({
  min = -5,
  max = 5,
  onObjectCreated,
}: InteractiveGeometryWorkspaceProps) {
  const [points, setPoints] = useState<Point2D[]>([]);
  const [message, setMessage] = useState("Select two points to create a segment.");
  const size = 320;
  const span = max - min;

  const grid = useMemo(
    () => Array.from({ length: span + 1 }, (_, index) => min + index),
    [min, span],
  );

  function toMathPoint(clientX: number, clientY: number, rect: DOMRect): Point2D {
    const x = Math.round(min + ((clientX - rect.left) / rect.width) * span);
    const y = Math.round(max - ((clientY - rect.top) / rect.height) * span);
    return [Math.max(min, Math.min(max, x)), Math.max(min, Math.min(max, y))];
  }

  function addPoint(point: Point2D) {
    const next = [...points, point];
    if (next.length < 2) {
      setPoints(next);
      setMessage(`First point selected at (${point[0]}, ${point[1]}). Select the endpoint.`);
      return;
    }

    const event: MathInteractionEvent = {
      schema_version: 1,
      type: "SEGMENT_CREATED",
      start: next[0],
      end: next[1],
    };
    const object = geometryObjectFromInteraction(event);
    onObjectCreated?.(object);
    setPoints([]);
    setMessage(
      object
        ? `Segment created from (${next[0][0]}, ${next[0][1]}) to (${next[1][0]}, ${next[1][1]}).`
        : "Unable to create segment.",
    );
  }

  return (
    <div>
      <svg
        viewBox={`0 0 ${size} ${size}`}
        role="application"
        aria-label="Interactive geometry workspace. Select two grid points to create a segment."
        tabIndex={0}
        onClick={(event) => addPoint(toMathPoint(event.clientX, event.clientY, event.currentTarget.getBoundingClientRect()))}
      >
        {grid.map((value) => {
          const position = ((value - min) / span) * size;
          return (
            <g key={value}>
              <line x1={position} y1={0} x2={position} y2={size} stroke="currentColor" opacity={0.15} />
              <line x1={0} y1={position} x2={size} y2={position} stroke="currentColor" opacity={0.15} />
            </g>
          );
        })}
        {points.map(([x, y], index) => (
          <circle
            key={index}
            cx={((x - min) / span) * size}
            cy={((max - y) / span) * size}
            r={5}
            fill="currentColor"
          />
        ))}
      </svg>
      <p aria-live="polite">{message}</p>
    </div>
  );
}
