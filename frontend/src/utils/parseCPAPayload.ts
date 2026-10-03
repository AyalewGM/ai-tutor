import type {
  BalanceScaleData,
  CPAVisualizerPayload,
  FractionBarData,
} from "../components/chat/CPAVisualizer";

export interface CPAExtraction {
  textContent: string;
  cpaPayload: CPAVisualizerPayload | null;
}

// ```json:cpa { ... } ```  or  <cpa_visual>{ ... }</cpa_visual>
const FENCED_CPA = /```\s*json:cpa\s*([\s\S]*?)```/i;
const TAGGED_CPA = /<cpa_visual>([\s\S]*?)<\/cpa_visual>/i;

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isFractionBar(value: unknown): value is FractionBarData {
  if (typeof value !== "object" || value === null) return false;
  const bar = value as Record<string, unknown>;
  return isFiniteNumber(bar.numerator) && isFiniteNumber(bar.denominator);
}

function isBalanceScale(value: unknown): value is BalanceScaleData {
  if (typeof value !== "object" || value === null) return false;
  const scale = value as Record<string, unknown>;
  return typeof scale.leftExpr === "string" && typeof scale.rightExpr === "string";
}

function toPayload(raw: unknown): CPAVisualizerPayload | null {
  if (typeof raw !== "object" || raw === null) return null;
  const obj = raw as Record<string, unknown>;
  if (obj.type === "FRACTION_BARS") {
    const bars = Array.isArray(obj.fractionBars)
      ? obj.fractionBars.filter(isFractionBar)
      : [];
    if (!bars.length) return null;
    return {
      type: "FRACTION_BARS",
      title: typeof obj.title === "string" ? obj.title : undefined,
      fractionBars: bars,
    };
  }
  if (obj.type === "BALANCE_SCALE") {
    if (!isBalanceScale(obj.balanceScale)) return null;
    const scale = obj.balanceScale;
    return {
      type: "BALANCE_SCALE",
      title: typeof obj.title === "string" ? obj.title : undefined,
      balanceScale: {
        leftExpr: scale.leftExpr,
        rightExpr: scale.rightExpr,
        leftValue: isFiniteNumber(scale.leftValue) ? scale.leftValue : undefined,
        rightValue: isFiniteNumber(scale.rightValue) ? scale.rightValue : undefined,
      },
    };
  }
  return null;
}

/**
 * Extract a structured CPA payload embedded in tutor message text.
 *
 * The LLM layer may emit ```` ```json:cpa ```` fenced blocks or
 * `<cpa_visual>` tags; both are stripped from the display text so learners
 * never see raw JSON. Malformed or structurally invalid payloads are dropped
 * silently — the message text still renders (the tag/fence stays stripped so
 * it doesn't leak markup).
 */
export function extractCPAPayload(content: string): CPAExtraction {
  for (const pattern of [FENCED_CPA, TAGGED_CPA]) {
    const match = pattern.exec(content);
    if (!match) continue;
    const textContent = content.replace(pattern, "").trim();
    try {
      const payload = toPayload(JSON.parse(match[1].trim()));
      return { textContent, cpaPayload: payload };
    } catch {
      return { textContent, cpaPayload: null };
    }
  }
  return { textContent: content, cpaPayload: null };
}
