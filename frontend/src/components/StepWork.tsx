import { useState } from "react";
import { Check, X } from "lucide-react";

import { ApiError, post } from "../api";
import type { StepStatus, WorkStepOut } from "../types";
import { cn } from "../lib/utils";
import MathText from "./MathText";
import { Button } from "./ui/button";
import { Input } from "./ui/input";

interface StepLine {
  id: number;
  text: string;
  status: StepStatus;
}

interface StepWorkProps {
  sessionId: string;
  problemId: string;
  disabled?: boolean;
  onSolved: (answer: string) => void;
  onError?: (message: string) => void;
}

export default function StepWork({
  sessionId,
  problemId,
  disabled,
  onSolved,
  onError,
}: StepWorkProps) {
  const [lines, setLines] = useState<StepLine[]>([]);
  const [draft, setDraft] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  async function submitLine() {
    if (!draft.trim() || busy || done) return;
    setBusy(true);
    setFeedback(null);
    try {
      const result = await post<WorkStepOut>(
        `/adaptive-tutor/sessions/${sessionId}/work-step`,
        { problem_id: problemId, line: draft.trim() },
      );
      const text = result.normalized_line ?? draft.trim();
      setLines((prev) => [
        ...prev,
        { id: prev.length, text, status: result.status },
      ]);
      setDraft("");
      setFeedback(result.feedback ?? null);
      if (result.status === "solved") {
        setDone(true);
        onSolved(result.normalized_line ?? text);
      }
    } catch (err) {
      onError?.(err instanceof ApiError ? err.message : "Step check failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3" data-testid="step-work">
      <p className="text-sm text-muted-foreground">
        Solve it line by line — write each step as an equation.
      </p>
      {lines.length > 0 && (
        <ol className="space-y-1.5" aria-label="Your work">
          {lines.map((line) => (
            <li
              key={line.id}
              className={cn(
                "flex items-center gap-2 rounded-md border px-3 py-2 text-base",
                line.status === "valid" || line.status === "solved"
                  ? "border-emerald-500/40 bg-emerald-500/5"
                  : "border-destructive/40 bg-destructive/5",
              )}
            >
              {line.status === "valid" || line.status === "solved" ? (
                <Check
                  className="h-4 w-4 shrink-0 text-emerald-600"
                  aria-label="step accepted"
                />
              ) : (
                <X
                  className="h-4 w-4 shrink-0 text-destructive"
                  aria-label="step rejected"
                />
              )}
              <MathText text={line.text} />
            </li>
          ))}
        </ol>
      )}
      {feedback && (
        <p
          className="rounded-md border border-amber-500/40 bg-amber-500/5 px-3 py-2 text-sm"
          role="status"
        >
          {feedback}
        </p>
      )}
      {!done && (
        <div className="flex gap-2">
          <Input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                void submitLine();
              }
            }}
            placeholder="Next line, e.g. 3x + 12 = 30"
            aria-label="Next work line"
            className="h-11 text-base"
            disabled={disabled || busy}
            autoComplete="off"
          />
          <Button
            type="button"
            variant="secondary"
            onClick={() => void submitLine()}
            disabled={disabled || busy || !draft.trim()}
          >
            Check step
          </Button>
        </div>
      )}
    </div>
  );
}
