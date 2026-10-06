import { useMemo, useState } from "react";
import type { MathSegment, Point2D } from "./contracts";
import { validateParallel, validatePerpendicular } from "./geometryValidation";
import { geometryObjectFromInteraction } from "./geometryInteractions";
import type { MathInteractionEvent } from "./interactions";

export interface InteractiveGeometryWorkspaceProps {
  min?: number;
  max?: number;
  onObjectCreated?: (object: ReturnType<typeof geometryObjectFromInteraction>) => void;
  referenceSegment?: MathSegment;
  relationship?: "parallel" | "perpendicular";
}

export function InteractiveGeometryWorkspace({
  min = -5,
  max = 5,
  onObjectCreated,
  referenceSegment,
  relationship,
}: InteractiveGeometryWorkspaceProps) {
  const [points, setPoints] = useState<Point2D[]>([]);
  const [cursor, setCursor] = useState<Point2D>([0, 0]);
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

  function moveCursor(dx: number, dy: number) {
    setCursor(([x, y]) => [
      Math.max(min, Math.min(max, x + dx)),
      Math.max(min, Math.min(max, y + dy)),
    ]);
  }

  function handleKeyDown(event: React.KeyboardEvent<SVGSVGElement>) {
    if (event.key === "ArrowLeft") { event.preventDefault(); moveCursor(-1, 0); }
    else if (event.key === "ArrowRight") { event.preventDefault(); moveCursor(1, 0); }
    else if (event.key === "ArrowUp") { event.preventDefault(); moveCursor(0, 1); }
    else if (event.key === "ArrowDown") { event.preventDefault(); moveCursor(0, -1); }
    else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      addPoint(cursor);
    }
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

    if (object?.kind === "segment" && referenceSegment && relationship) {
      const result =
        relationship === "parallel"
          ? validateParallel(object, referenceSegment)
          : validatePerpendicular(object, referenceSegment);
      setMessage(
        result.correct
          ? `Correct: the segment is ${relationship} to the reference segment.`
          : `Try again: ${result.misconception ?? "relationship not satisfied"}.`,
      );
      return;
    }

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
        aria-label={`Interactive geometry workspace. Keyboard cursor at (${cursor[0]}, ${cursor[1]}). Use arrow keys to move and Enter or Space to select two endpoints.`}
        tabIndex={0}
        onKeyDown={handleKeyDown}
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
        <circle
          cx={((cursor[0] - min) / span) * size}
          cy={((max - cursor[1]) / span) * size}
          r={7}
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        />
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
      <p>Keyboard: arrow keys move the mathematical cursor; Enter or Space selects a point.</p>
      <p aria-live="polite">{message}</p>
    </div>
  );
}
