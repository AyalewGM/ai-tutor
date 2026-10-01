const LATEX_COMMANDS = /\\\\(?=(?:frac|sqrt|sum|prod|int|left|right|times|div|cdot|pm|leq|geq|neq|alpha|beta|gamma|theta|pi|infty|text|mathbf|mathrm)\b)/g;

/**
 * Normalize common model-produced LaTeX without changing arbitrary user text.
 * - converts escaped known LaTeX commands (\\\\frac -> \\frac)
 * - converts \\[...\\] to $$...$$
 * - converts \\(...\\) to $...$
 */
export function sanitizeMathString(input: string): string {
  return input
    .replace(/\\\\\[([\s\S]*?)\\\\\]/g, (_match, math: string) => `$$${math.trim()}$$`)
    .replace(/\\\\\(([\s\S]*?)\\\\\)/g, (_match, math: string) => `$${math.trim()}$`)
    .replace(/\\\[([\s\S]*?)\\\]/g, (_match, math: string) => `$$${math.trim()}$$`)
    .replace(/\\\(([\s\S]*?)\\\)/g, (_match, math: string) => `$${math.trim()}$`)
    .replace(LATEX_COMMANDS, "\\");
}
