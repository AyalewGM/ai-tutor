import { useEffect, useMemo, useRef } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

/**
 * Renders a text string with math notation converted to KaTeX.
 *
 * Detects math segments automatically:
 * - Fractions: `a/b` → `\frac{a}{b}`
 * - Mixed numbers: `a b/c` → `a\frac{b}{c}`
 * - Operators: `*`, `×` → `\times`; `÷` → `\div`; `-` → `-`
 * - Exponents: `a^b` → `a^{b}`
 * - Comparisons: `=`, `<`, `>`, `≤`, `≥`, `≠`
 * - Equations: `a = b`, `x = ?`
 *
 * Everything else is rendered as plain text via React's escaping.
 * Math segments are rendered with katex.render() into a DOM node, so no
 * HTML string is ever reinterpreted — no dangerouslySetInnerHTML.
 */

// Patterns that indicate a segment is math
const MATH_RE = /[\d\-+×÷*^=<>≤≥≠√]|\\[a-z]+/;

// Fractions like "3/4", "12/7"
const FRACTION_RE = /\b(\d+)\s*\/\s*(\d+)\b/g;

// Mixed numbers like "2 1/3"
const MIXED_RE = /\b(\d+)\s+(\d+)\s*\/\s*(\d+)\b/g;

// Exponents like "x^2", "2^3"
const EXPONENT_RE = /\b(\w+)\s*\^\s*(\d+)\b/g;

// Simple math expressions: numbers and operators between spaces or at boundaries
const MATH_SEGMENT_RE = /(?:^|\s)((?:\d+(?:\s*[×÷*+\-=<>≤≥≠]\s*\d+)+|\d+\s*\/\s*\d+|\w+\s*\^\s*\d+|[√∛]\s*\d+)[\s]*(?:[×÷*+\-=<>≤≥≠]\s*\d+(?:\s*\/\s*\d+)*)*)/g;

function toLatex(text: string): string {
  let result = text;

  // Convert fractions first (before exponent detection would grab the slash)
  result = result.replace(FRACTION_RE, (_, num, den) => `\\frac{${num}}{${den}}`);

  // Convert exponents
  result = result.replace(EXPONENT_RE, (_, base, exp) => `${base}^{${exp}}`);

  // Convert operators
  result = result
    .replace(/×/g, "\\times")
    .replace(/÷/g, "\\div")
    .replace(/≤/g, "\\leq")
    .replace(/≥/g, "\\geq")
    .replace(/≠/g, "\\neq")
    .replace(/\*/g, "\\times")
    .replace(/√(\d+)/g, "\\sqrt{$1}");

  return result;
}

function KatexSpan({ latex, fallback }: { latex: string; fallback: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    try {
      katex.render(latex, el, {
        throwOnError: false,
        displayMode: false,
        strict: false,
      });
    } catch {
      el.textContent = fallback; // fallback to plain text on error
    }
  }, [latex, fallback]);
  return <span ref={ref}>{fallback}</span>;
}

interface MathTextProps {
  text: string;
  className?: string;
}

export default function MathText({ text, className }: MathTextProps) {
  const segments = useMemo(() => {
    const out: Array<{ type: "text" | "math"; content: string }> = [];
    if (!text) return out;
    let lastEnd = 0;
    let match: RegExpExecArray | null;

    MATH_SEGMENT_RE.lastIndex = 0;
    while ((match = MATH_SEGMENT_RE.exec(text)) !== null) {
      const segStart = match.index + match[0].indexOf(match[1]);
      if (segStart > lastEnd) {
        out.push({ type: "text", content: text.slice(lastEnd, segStart) });
      }
      out.push({ type: "math", content: match[1].trim() });
      lastEnd = segStart + match[1].length;
    }
    if (lastEnd < text.length) {
      out.push({ type: "text", content: text.slice(lastEnd) });
    }
    return out;
  }, [text]);

  return (
    <span className={`math-text ${className ?? ""}`}>
      {segments.map((seg, i) =>
        seg.type === "text" ? (
          seg.content
        ) : (
          <KatexSpan key={i} latex={toLatex(seg.content)} fallback={seg.content} />
        ),
      )}
    </span>
  );
}
