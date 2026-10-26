import { forwardRef } from "react";

import MathKeypad from "./MathKeypad";
import { Input } from "./ui/input";

export interface ExactRationalEntryProps {
  answerKind: "RATIONAL" | "VARIABLE_VALUE";
  value: string;
  onValueChange: (value: string) => void;
  onKey: (token: string) => void;
  disabled?: boolean;
}

/**
 * Format guidance only. The server owns the answer key and equivalence check.
 *
 * Unlike the existing legacy FRACTION numerator/denominator control, this
 * field also accepts an integer and, for VARIABLE_VALUE, the variable binding
 * expected by the backend's exact rational answer contract (e.g. x=1/2).
 * Neither hints nor client-side answer validation belong in this component.
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
            ? "Enter the variable, equals sign, then an exact integer or fraction (format: x=numerator/denominator). Use the variable in the question."
            : "Enter an exact integer or fraction using / between numerator and denominator. Do not round to a decimal."}
        </p>
        <MathKeypad onKey={onKey} variables={isVariableValue} disabled={disabled} />
      </div>
    );
  },
);

export default ExactRationalEntry;
