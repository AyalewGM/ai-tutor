import type { VisualSpec } from "../types";
import ProblemVisual from "./ProblemVisual";

interface CPAVisualizerProps {
  spec: VisualSpec | null | undefined;
  level?: string | null;
}

const LEVEL_LABEL: Record<string, string> = {
  PICTORIAL: "Working with the picture",
  CONCRETE: "Let's build it together",
};

/**
 * Renders the pedagogy layer's step-context visual — the balance scale,
 * fraction bars, or number line anchored at the learner's current line.
 * Returns nothing at ABSTRACT level or when no spec was emitted.
 */
export default function CPAVisualizer({ spec, level }: CPAVisualizerProps) {
  if (!spec || level === "ABSTRACT") return null;
  return (
    <div
      className="space-y-1 rounded-md border border-indigo-500/30 bg-indigo-500/5 p-3"
      data-testid="cpa-visual"
    >
      {level && LEVEL_LABEL[level] && (
        <p className="text-xs font-medium text-indigo-700">{LEVEL_LABEL[level]}</p>
      )}
      <ProblemVisual spec={spec} />
    </div>
  );
}
