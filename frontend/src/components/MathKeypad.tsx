import { Delete } from "lucide-react";

import { cn } from "../lib/utils";

export interface MathKeypadProps {
  onKey: (token: string) => void;
  disabled?: boolean;
  variables?: boolean;
}

interface Key {
  label: string;
  token: string;
  aria?: string;
  varKey?: boolean;
}

// Display label -> inserted text. The keypad writes ASCII the parser already
// understands; multiplication/division symbols are for readability only.
const FUNCTION_KEYS: Key[] = [
  { label: "x", token: "x", varKey: true },
  { label: "y", token: "y", varKey: true },
  { label: "(", token: "(" },
  { label: ")", token: ")" },
  { label: "^", token: "^", aria: "exponent" },
  { label: "=", token: "=" },
  { label: "⌫", token: "\b", aria: "backspace" },
];

// Digits on the left, operators on the right rail — calculator style.
const GRID_ROWS: { digits: Key[]; op: Key }[] = [
  {
    digits: [
      { label: "7", token: "7" },
      { label: "8", token: "8" },
      { label: "9", token: "9" },
    ],
    op: { label: "÷", token: "/", aria: "divide" },
  },
  {
    digits: [
      { label: "4", token: "4" },
      { label: "5", token: "5" },
      { label: "6", token: "6" },
    ],
    op: { label: "×", token: "*", aria: "multiply" },
  },
  {
    digits: [
      { label: "1", token: "1" },
      { label: "2", token: "2" },
      { label: "3", token: "3" },
    ],
    op: { label: "−", token: "-", aria: "subtract" },
  },
  {
    digits: [
      { label: "0", token: "0" },
      { label: ".", token: "." },
      { label: "/", token: "/", aria: "fraction slash" },
    ],
    op: { label: "+", token: "+" },
  },
];

const KEY_BASE =
  "rounded-md border font-semibold shadow-sm transition-colors " +
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
  "disabled:cursor-not-allowed disabled:opacity-50";

export default function MathKeypad({ onKey, disabled, variables = true }: MathKeypadProps) {
  return (
    <div className="math-keypad space-y-1.5" data-testid="math-keypad">
      <div className="flex gap-1.5">
        {FUNCTION_KEYS.map((key) => {
          if (key.varKey && !variables) return null;
          return (
            <button
              key={key.label}
              type="button"
              aria-label={key.aria ?? key.label}
              disabled={disabled}
              onClick={() => onKey(key.token)}
              className={cn(
                KEY_BASE,
                "h-8 min-w-10 flex-1 border-input bg-secondary/70 text-sm text-secondary-foreground hover:bg-secondary",
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
      <div className="space-y-1.5">
        {GRID_ROWS.map((row, i) => (
          <div key={i} className="grid grid-cols-4 gap-1.5">
            {row.digits.map((key) => (
              <button
                key={key.label}
                type="button"
                aria-label={key.aria ?? key.label}
                disabled={disabled}
                onClick={() => onKey(key.token)}
                className={cn(
                  KEY_BASE,
                  "h-10 border-input bg-card text-base hover:bg-accent",
                )}
              >
                {key.label}
              </button>
            ))}
            <button
              type="button"
              aria-label={row.op.aria ?? row.op.label}
              disabled={disabled}
              onClick={() => onKey(row.op.token)}
              className={cn(
                KEY_BASE,
                "h-10 border-primary/25 bg-primary/10 text-lg text-primary hover:bg-primary/20",
              )}
            >
              {row.op.label}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
