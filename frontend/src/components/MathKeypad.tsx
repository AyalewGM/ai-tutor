import { Delete } from "lucide-react";

import { cn } from "../lib/utils";

export interface MathKeypadProps {
  onKey: (token: string) => void;
  disabled?: boolean;
  variables?: boolean;
}

// Display label -> inserted text. The keypad writes ASCII the parser already
// understands; multiplication/division symbols are for readability only.
const ROWS: { label: string; token: string; aria?: string; varKey?: boolean }[][] = [
  [
    { label: "x", token: "x", varKey: true },
    { label: "y", token: "y", varKey: true },
    { label: "^", token: "^", aria: "exponent" },
    { label: "(", token: "(" },
    { label: ")", token: ")" },
  ],
  [
    { label: "7", token: "7" },
    { label: "8", token: "8" },
    { label: "9", token: "9" },
    { label: "÷", token: "/", aria: "divide" },
    { label: "⌫", token: "\b", aria: "backspace" },
  ],
  [
    { label: "4", token: "4" },
    { label: "5", token: "5" },
    { label: "6", token: "6" },
    { label: "×", token: "*", aria: "multiply" },
    { label: "=", token: "=" },
  ],
  [
    { label: "1", token: "1" },
    { label: "2", token: "2" },
    { label: "3", token: "3" },
    { label: "−", token: "-", aria: "subtract" },
    { label: "+", token: "+" },
  ],
  [
    { label: "0", token: "0" },
    { label: ".", token: "." },
    { label: "/", token: "/", aria: "fraction slash" },
  ],
];

export default function MathKeypad({ onKey, disabled, variables = true }: MathKeypadProps) {
  return (
    <div className="math-keypad space-y-1" data-testid="math-keypad">
      {ROWS.map((row, i) => (
        <div key={i} className="flex gap-1">
          {row.map((key) => {
            if (key.varKey && !variables) return null;
            return (
              <button
                key={key.label}
                type="button"
                aria-label={key.aria ?? key.label}
                disabled={disabled}
                onClick={() => onKey(key.token)}
                className={cn(
                  "h-9 min-w-10 flex-1 rounded-md border border-input bg-card text-base font-semibold shadow-sm",
                  "transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  "disabled:cursor-not-allowed disabled:opacity-50",
                )}
              >
                {key.token === "\b" ? (
                  <Delete className="mx-auto h-4 w-4" aria-hidden="true" />
                ) : (
                  key.label
                )}
              </button>
            );
          })}
        </div>
      ))}
    </div>
  );
}
