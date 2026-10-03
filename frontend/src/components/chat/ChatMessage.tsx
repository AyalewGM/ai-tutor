import { useMemo } from "react";

import { extractCPAPayload } from "../../utils/parseCPAPayload";
import MathText from "../MathText";
import CPAVisualizer from "./CPAVisualizer";

interface ChatMessageProps {
  content: string;
}

/**
 * One tutor message in the workspace coach thread.
 *
 * Message text renders through MathText (inline math → KaTeX). When the
 * backend embeds a structured CPA payload (`json:cpa` fence or
 * `<cpa_visual>` tag), the manipulative renders beneath the text and the
 * raw JSON is stripped from what the learner sees.
 */
export default function ChatMessage({ content }: ChatMessageProps) {
  const { textContent, cpaPayload } = useMemo(() => extractCPAPayload(content), [content]);

  return (
    <div
      className="rounded-xl rounded-tl-sm bg-secondary px-4 py-3 text-sm leading-relaxed"
      aria-live="polite"
    >
      <MathText text={textContent} />
      {cpaPayload && <CPAVisualizer payload={cpaPayload} />}
    </div>
  );
}
