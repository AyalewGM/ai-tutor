import { cn } from "../../lib/utils";

export type CPAVisualType = "FRACTION_BARS" | "BALANCE_SCALE";

export interface FractionBarData {
  numerator: number;
  denominator: number;
  label?: string;
  color?: string;
}

export interface BalanceScaleData {
  leftExpr: string;
  rightExpr: string;
  leftValue?: number;
  rightValue?: number;
}

export interface CPAVisualizerPayload {
  type: CPAVisualType;
  title?: string;
  fractionBars?: FractionBarData[];
  balanceScale?: BalanceScaleData;
}

const MAX_SEGMENTS = 24;
const BAR_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ec4899"];

// The LLM contract sends Tailwind classes ("bg-indigo-500"); inline styles
// need real colors, so map the contract set and pass raw CSS values through.
const TAILWIND_FILLS: Record<string, string> = {
  "bg-indigo-500": "#6366f1",
  "bg-emerald-500": "#10b981",
  "bg-amber-500": "#f59e0b",
  "bg-rose-500": "#f43f5e",
};

// Payload colors land in style.backgroundColor. Allowlist the contract's
// Tailwind classes, hex colors, and plain CSS color names; anything else
// (url(), expressions) falls back to the palette. Defense in depth for
// messages persisted before backend validation existed.
const SAFE_COLOR_RE = /^(bg-[a-z]+-\d{3}|#[0-9a-fA-F]{3,8}|[a-zA-Z]{1,24})$/;

function barColor(color: string | undefined, index: number): string {
  if (!color) return BAR_COLORS[index % BAR_COLORS.length];
  if (!SAFE_COLOR_RE.test(color)) return BAR_COLORS[index % BAR_COLORS.length];
  return TAILWIND_FILLS[color] ?? color;
}

function safeCount(value: number | undefined, fallback: number): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return Math.max(0, Math.floor(value));
}

function FractionBarsView({ bars }: { bars: FractionBarData[] }) {
  return (
    <div className="space-y-2" role="list" aria-label="Fraction bars">
      {bars.map((bar, i) => {
        const denominator = Math.min(
          MAX_SEGMENTS,
          Math.max(1, safeCount(bar.denominator, 1)),
        );
        const numerator = Math.min(denominator, safeCount(bar.numerator, 0));
        const color = barColor(bar.color, i);
        return (
          <div key={i} role="listitem" className="space-y-1">
            <div
              className="flex h-8 w-full overflow-hidden rounded-md border border-slate-300 bg-white"
              aria-label={`${bar.label ?? "Fraction"}: ${numerator} of ${denominator} parts shaded`}
            >
              {Array.from({ length: denominator }, (_, seg) => (
                <div
                  key={seg}
                  className={cn(
                    "h-full flex-1 border-slate-300 transition-colors duration-300",
                    seg > 0 && "border-l",
                  )}
                  style={{
                    backgroundColor: seg < numerator ? color : "transparent",
                  }}
                />
              ))}
            </div>
            <p className="text-xs text-slate-600">
              {bar.label && <span className="font-medium">{bar.label} </span>}
              {numerator}/{denominator}
            </p>
          </div>
        );
      })}
    </div>
  );
}

function BalanceScaleView({ scale }: { scale: BalanceScaleData }) {
  const left = scale.leftValue;
  const right = scale.rightValue;
  const measured =
    typeof left === "number" &&
    Number.isFinite(left) &&
    typeof right === "number" &&
    Number.isFinite(right);
  const diff = measured ? left - right : 0;
  const tilt = Math.max(-12, Math.min(12, diff * 3));
  const balanced = !measured || diff === 0;

  return (
    <div className="space-y-2">
      <svg
        viewBox="0 0 240 150"
        className="mx-auto w-full max-w-xs"
        role="img"
        aria-label={
          balanced
            ? `Balance scale showing ${scale.leftExpr} equals ${scale.rightExpr}`
            : `Balance scale tilted: ${scale.leftExpr} versus ${scale.rightExpr}`
        }
      >
        <polygon points="120,50 105,80 135,80" fill="#94a3b8" />
        <rect x="116" y="78" width="8" height="56" fill="#94a3b8" />
        <rect x="92" y="132" width="56" height="6" rx="3" fill="#64748b" />
        <g
          style={{
            transform: `rotate(${-tilt}deg)`,
            transformOrigin: "120px 50px",
            transition: "transform 0.5s ease",
          }}
        >
          <rect x="30" y="46" width="180" height="7" rx="3.5" fill="#475569" />
          <line x1="45" y1="53" x2="45" y2="75" stroke="#475569" strokeWidth="2" />
          <line x1="195" y1="53" x2="195" y2="75" stroke="#475569" strokeWidth="2" />
          <path d="M25,75 Q45,95 65,75 Z" fill="#6366f1" opacity="0.85" />
          <path d="M175,75 Q195,95 215,75 Z" fill="#10b981" opacity="0.85" />
        </g>
        <text x="45" y="112" textAnchor="middle" fontSize="11" fill="#334155">
          {scale.leftExpr}
        </text>
        <text x="195" y="112" textAnchor="middle" fontSize="11" fill="#334155">
          {scale.rightExpr}
        </text>
      </svg>
      <p
        className={cn(
          "text-center text-xs font-medium",
          balanced ? "text-emerald-700" : "text-amber-700",
        )}
        role="status"
      >
        {balanced ? "✓ Balanced" : "⚖ Out of Balance"}
      </p>
    </div>
  );
}

/**
 * Renders a CPA manipulative emitted as a structured payload inside a tutor
 * message — fraction bars or a balance scale. Returns null for payloads that
 * don't carry the data their type requires (defense in depth past the parser).
 */
export default function CPAVisualizer({ payload }: { payload: CPAVisualizerPayload }) {
  if (payload.type === "FRACTION_BARS" && !payload.fractionBars?.length) return null;
  if (payload.type === "BALANCE_SCALE" && !payload.balanceScale) return null;

  return (
    <div
      className="mt-2 space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-3"
      data-testid="cpa-visualizer"
    >
      {payload.title && (
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          {payload.title}
        </p>
      )}
      {payload.type === "FRACTION_BARS" && (
        <FractionBarsView bars={payload.fractionBars ?? []} />
      )}
      {payload.type === "BALANCE_SCALE" && payload.balanceScale && (
        <BalanceScaleView scale={payload.balanceScale} />
      )}
    </div>
  );
}
