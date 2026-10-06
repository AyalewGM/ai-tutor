import { describe, expect, it } from "vitest";

import type { MathAnimationSpec } from "./animation";
import { buildAnimationFrames, replayAnimationFrame } from "./animationFrames";
import type { MathPolygon } from "./contracts";
import { parseMathWork, serializeMathWork, type PersistedMathWorkV1 } from "./persistence";

const triangle: MathPolygon = {
  kind: "polygon",
  id: "triangle",
  vertices: [[1, 1], [3, 1], [2, 3]],
};

const animation: MathAnimationSpec = {
  schema_version: 1,
  purpose: "Translate a triangle using structured mathematical truth.",
  objects: [triangle],
  reduced_motion: "step_without_motion",
  steps: [
    { id: "start", duration_ms: 0, description: "Start." },
    {
      id: "translate",
      duration_ms: 0,
      description: "Move right 2 and up 1.",
      transformation: {
        kind: "transformation",
        transformation: "translation",
        source: triangle,
        parameters: { vector: [2, 1] },
      },
    },
  ],
};

describe("MVE mathematical truth regression", () => {
  it("derives animation and replay from the same deterministic objects", () => {
    const frames = buildAnimationFrames(animation);
    expect(frames[1].objects[0]).toEqual({
      kind: "polygon",
      id: "triangle",
      vertices: [[3, 2], [5, 2], [4, 4]],
    });
    expect(replayAnimationFrame(animation, 1)).toEqual(frames[1]);
  });

  it("round-trips semantic work without rendered or pointer evidence", () => {
    const work: PersistedMathWorkV1 = {
      schema_version: 1,
      session_id: "synthetic-session",
      interaction_events: [
        { schema_version: 1, type: "POINT_PLACED", point: [3, 2] },
      ],
      animation,
      animation_step_index: 1,
    };
    expect(parseMathWork(serializeMathWork(work))).toEqual(work);
  });

  it("fails closed for unsupported persisted schema versions", () => {
    expect(parseMathWork(JSON.stringify({
      schema_version: 2,
      session_id: "synthetic-session",
      interaction_events: [],
    }))).toBeNull();
  });
});
