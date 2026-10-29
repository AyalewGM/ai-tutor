import { forwardRef } from "react";

import { Input } from "./ui/input";

export interface ExactRationalEntryProps {
  answerKind: "RATIONAL" | "VARIABLE_VALUE";
  value: string;
  onValueChange: (value: string) => void;
  onKey: (token: string) => void;
  disabled?: boolean;
}

// Only offer tokens accepted by the exact-rational server response contract.
// The shared MathKeypad also offers decimals and symbolic operations and must
// remain available for other answer kinds, but not for this one. Until the
// server exposes an immutable reviewed variable binding, never guess x or y.
const EXACT_RATIONAL_KEYS = [
  [{ label: "7", token: "7" }, { label: "8", token: "8" }, { label: "9", token: "9" }],
  [{ label: "4", token: "4" }, { label: "5", token: "5" }, { label: "6", token: "6" }],
  [{ label: "1", token: "1" }, { label: "2", token: "2" }, { label: "3", token: "3" }],
  [
    { label: "0", token: "0" },
    { label: "−", token: "-", aria: "minus sign" },
    { label: "/", token: "/", aria: "fraction slash" },
    { label: "⌫", token: "\b", aria: "backspace" },
  ],
] as const;

function ExactRationalKeypad({
  onKey,
  disabled,
}: {
  onKey: (token: string) => void;
  disabled: boolean;
}) {
  return (
    <div
      role="group"
      aria-label="Exact rational keypad"
      className="math-keypad space-y-1"
      data-testid="exact-rational-keypad"
    >
      {EXACT_RATIONAL_KEYS.map((row, index) => (
        <div key={index} className="flex gap-1">
          {row.map((key) => (
            <button
              key={key.label}
              type="button"
              aria-label={"aria" in key ? key.aria : key.label}
              disabled={disabled}
              onClick={() => onKey(key.token)}
              className="h-9 min-w-10 flex-1 rounded-md border border-input bg-card text-base font-semibold shadow-sm transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            >
              {key.label}
            </button>
          ))}
        </div>
      ))}
    </div>
  );
}

/**
 * Syntax-only guidance; all equivalence checks remain server-authoritative.
 * This restricted keypad cannot suggest unsupported decimals or expressions.
 * VARIABLE_VALUE learners enter the question's variable and '=' using their
 * keyboard until a signed, server-owned variable shortcut contract exists.
 */
const ExactRationalEntry = forwardRef<HTMLInputElement, ExactRationalEntryProps>(
  function ExactRationalEntry(
    { answerKind, value, onValueChange, onKey, disabled = false },
    ref,
  ) {
    const isVariableValue = answerKind === "VARIABLE_VALUE";

    return (
      <div className="space-y-2">
        <Input
          id="answer"
          ref={ref}
          aria-label={isVariableValue ? "Exact variable value" : "Exact rational number"}
          aria-describedby="exact-rational-answer-format"
          className="h-12 text-lg"
          inputMode="text"
          value={value}
          onChange={(event) => onValueChange(event.target.value)}
          disabled={disabled}
          maxLength={64}
          autoComplete="off"
          autoCapitalize="off"
          autoCorrect="off"
          spellCheck={false}
        />
        <p
          id="exact-rational-answer-format"
          className="text-sm text-muted-foreground"
        >
          {isVariableValue
            ? "Type the variable shown in the question, then =, followed by an exact signed integer or fraction using /. Use your keyboard for the variable and equals sign."
            : "Enter an exact signed integer or fraction using / between numerator and denominator. Do not round to a decimal."}
        </p>
        <ExactRationalKeypad onKey={onKey} disabled={disabled} />
      </div>
    );
  },
);

export default ExactRationalEntry;
