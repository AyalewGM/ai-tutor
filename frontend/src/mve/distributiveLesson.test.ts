import { describe, expect, it } from "vitest";
import { buildDistributiveLesson, checkDistributiveCoefficients } from "./distributiveLesson";
import { isMathAnimationSpec } from "./animation";

describe("canonical distributive lesson", () => {
  it("generates reusable semantic steps and existing MVE animation spec", () => {
    const lesson = buildDistributiveLesson(3, 4);
    expect(lesson.original).toBe("3(x + 4)");
    expect(lesson.expanded).toBe("3 × x + 3 × 4");
    expect(lesson.simplified).toBe("3x + 12");
    expect(isMathAnimationSpec(lesson.animation)).toBe(true);
    expect(lesson.animation.steps).toHaveLength(4);
    expect(lesson.animation.reduced_motion).toBe("step_without_motion");
    expect(lesson.areaModel.a).toBe(3);
    expect(lesson.areaModel.b).toBe(4);
  });

  it("classifies missed distribution and correct solutions deterministically", () => {
    const lesson = buildDistributiveLesson(5, 3);
    expect(checkDistributiveCoefficients(lesson, 5, 3).misconception).toBe("MISSED_SECOND_TERM");
    expect(checkDistributiveCoefficients(lesson, 5, 15).correct).toBe(true);
    expect(checkDistributiveCoefficients(lesson, 4, 15).misconception).toBe("COEFFICIENT_ERROR");
  });

  it("rejects invalid mathematical inputs", () => {
    expect(() => buildDistributiveLesson(0, 4)).toThrow();
    expect(() => buildDistributiveLesson(3, -4)).toThrow();
    expect(() => buildDistributiveLesson(3, 4, "<script>")).toThrow();
  });
});
