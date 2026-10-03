import { useRef, useState } from "react";
import { Camera, Check, X } from "lucide-react";

import { ApiError, post, postForm } from "../api";
import type {
  PhotoScanOut,
  ReverseChallenge,
  StepStatus,
  VisualSpec,
  WorkStepOut,
} from "../types";
import { cn } from "../lib/utils";
import CPAVisualizer from "./CPAVisualizer";
import MathKeypad from "./MathKeypad";
import MathText from "./MathText";
import { Button } from "./ui/button";
import { Input } from "./ui/input";

interface StepLine {
  id: number;
  text: string;
  status: StepStatus;
}

interface ScannedLine {
  id: number;
  text: string;
  needsReview: boolean;
}

interface StepWorkProps {
  sessionId: string;
  problemId: string;
  problemType?: string | null;
  disabled?: boolean;
  onSolved: (answer: string) => void;
  onError?: (message: string) => void;
}

export default function StepWork({
  sessionId,
  problemId,
  problemType,
  disabled,
  onSolved,
  onError,
}: StepWorkProps) {
  const wordProblem = problemType === "WORD_PROBLEM";
  const algebraWordProblem = problemType === "ALGEBRA_WORD_PROBLEM";
  const [lines, setLines] = useState<StepLine[]>([]);
  const [draft, setDraft] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [scanned, setScanned] = useState<ScannedLine[] | null>(null);
  const [cpaLevel, setCpaLevel] = useState<string | null>(null);
  const [stepVisual, setStepVisual] = useState<VisualSpec | null>(null);
  const [challenge, setChallenge] = useState<ReverseChallenge | null>(null);
  const draftRef = useRef<HTMLInputElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const nextId = useRef(0);

  function insertToken(token: string) {
    const el = draftRef.current;
    const s = el?.selectionStart ?? draft.length;
    const e = el?.selectionEnd ?? s;
    let next: string;
    let cursor: number;
    if (token === "\b") {
      const from = s === e ? Math.max(0, s - 1) : s;
      next = draft.slice(0, from) + draft.slice(e);
      cursor = from;
    } else {
      next = draft.slice(0, s) + token + draft.slice(e);
      cursor = s + token.length;
    }
    setDraft(next);
    requestAnimationFrame(() => {
      el?.focus();
      el?.setSelectionRange(cursor, cursor);
    });
  }

  async function checkLine(text: string): Promise<StepStatus> {
    const result = await post<WorkStepOut>(
      `/adaptive-tutor/sessions/${sessionId}/work-step`,
      { problem_id: problemId, line: text },
    );
    const shown = result.normalized_line ?? text;
    setLines((prev) => [...prev, { id: nextId.current++, text: shown, status: result.status }]);
    setFeedback(result.feedback ?? null);
    setCpaLevel(result.cpa_level ?? null);
    setStepVisual(result.step_visual ?? null);
    setChallenge(result.reverse_challenge ?? null);
    if (result.status === "solved") {
      setDone(true);
      onSolved(shown);
    }
    return result.status;
  }

  async function submitLine() {
    if (!draft.trim() || busy || done) return;
    setBusy(true);
    setFeedback(null);
    try {
      await checkLine(draft.trim());
      setDraft("");
    } catch (err) {
      onError?.(err instanceof ApiError ? err.message : "Step check failed");
    } finally {
      setBusy(false);
    }
  }

  async function scanPhoto(file: File) {
    setScanning(true);
    setFeedback(null);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("problem_id", problemId);
      const result = await postForm<PhotoScanOut>(
        `/adaptive-tutor/sessions/${sessionId}/work-photo/scan`,
        form,
      );
      setScanned(
        result.lines.map((l) => ({
          id: nextId.current++,
          text: l.text,
          needsReview: l.needs_review,
        })),
      );
    } catch (err) {
      onError?.(err instanceof ApiError ? err.message : "Could not read the photo");
    } finally {
      setScanning(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function checkScannedLines() {
    if (!scanned || busy || done) return;
    const toCheck = scanned.map((l) => l.text.trim()).filter(Boolean);
    setBusy(true);
    setFeedback(null);
    try {
      for (const text of toCheck) {
        const status = await checkLine(text);
        if (status === "solved") break;
      }
      setScanned(null);
    } catch (err) {
      onError?.(err instanceof ApiError ? err.message : "Step check failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3" data-testid="step-work">
      <p className="text-sm text-muted-foreground">
        {algebraWordProblem
          ? "Name the unknown first (like x = miles driven), then write the equation, then solve it line by line."
          : wordProblem
            ? "Work it out step by step — write the calculation, then your answer."
            : "Solve it line by line — write each step as an equation."}
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
                  : line.status === "invalid"
                    ? "border-destructive/40 bg-destructive/5"
                    : "border-border bg-muted/30",
              )}
            >
              {line.status === "valid" || line.status === "solved" ? (
                <Check
                  className="h-4 w-4 shrink-0 text-emerald-600"
                  aria-label="step accepted"
                />
              ) : line.status === "invalid" ? (
                <X
                  className="h-4 w-4 shrink-0 text-destructive"
                  aria-label="step rejected"
                />
              ) : (
                <span
                  className="h-4 w-4 shrink-0 text-center text-xs leading-4 text-muted-foreground"
                  aria-label={
                    line.status === "duplicate"
                      ? "same as an earlier line"
                      : "could not parse"
                  }
                >
                  –
                </span>
              )}
              <MathText text={line.text} />
            </li>
          ))}
        </ol>
      )}
      {stepVisual && <CPAVisualizer spec={stepVisual} level={cpaLevel} />}
      {challenge && (
        <div
          className="space-y-1 rounded-md border border-violet-500/40 bg-violet-500/5 px-3 py-2"
          data-testid="reverse-challenge"
        >
          <p className="text-sm">{challenge.prompt}</p>
          <p className="text-sm font-medium">
            Tutor's attempt: <MathText text={challenge.line} />
          </p>
          <p className="text-xs text-muted-foreground">
            Write the step the way it should go — or copy mine if you think it's right.
          </p>
        </div>
      )}
      {feedback && (
        <p
          className="rounded-md border border-amber-500/40 bg-amber-500/5 px-3 py-2 text-sm"
          role="status"
        >
          {feedback}
        </p>
      )}
      {scanned && (
        <div className="space-y-2 rounded-md border border-border p-3" data-testid="scan-review">
          <p className="text-sm text-muted-foreground">
            Here's what we read — fix anything that looks off, then check the steps:
          </p>
          <ol className="space-y-1.5" aria-label="Scanned lines">
            {scanned.map((line, index) => (
              <li key={line.id} className="flex items-center gap-2">
                <Input
                  value={line.text}
                  aria-label={`Scanned line ${index + 1}`}
                  className={cn(
                    "h-10 text-base",
                    line.needsReview && "border-amber-500/60",
                  )}
                  onChange={(e) =>
                    setScanned((prev) =>
                      prev
                        ? prev.map((l) => (l.id === line.id ? { ...l, text: e.target.value } : l))
                        : prev,
                    )
                  }
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  aria-label={`Remove scanned line ${index + 1}`}
                  onClick={() =>
                    setScanned((prev) => (prev ? prev.filter((l) => l.id !== line.id) : prev))
                  }
                >
                  <X className="h-4 w-4" />
                </Button>
              </li>
            ))}
          </ol>
          <div className="flex gap-2">
            <Button
              type="button"
              onClick={() => void checkScannedLines()}
              disabled={busy || scanned.every((l) => !l.text.trim())}
            >
              Check these steps
            </Button>
            <Button type="button" variant="ghost" onClick={() => setScanned(null)}>
              Cancel
            </Button>
          </div>
        </div>
      )}
      {!done && (
        <div className="space-y-2">
          <div className="flex gap-2">
            <Input
              ref={draftRef}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                void submitLine();
              }
            }}
            placeholder={
              wordProblem ? "e.g. 0.2 * 60, then 12 dollars" : "Next line, e.g. 3x + 12 = 30"
            }
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
          <MathKeypad onKey={insertToken} disabled={disabled || busy} />
          <input
            ref={fileRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            className="hidden"
            aria-label="Photo of written work"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void scanPhoto(file);
            }}
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-2"
            disabled={disabled || busy || scanning}
            onClick={() => fileRef.current?.click()}
          >
            <Camera className="h-4 w-4" />
            {scanning ? "Reading your work…" : "Check a photo of written work"}
          </Button>
        </div>
      )}
    </div>
  );
}
