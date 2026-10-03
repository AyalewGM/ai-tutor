import { useMemo } from "react";

import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import remarkMath from "remark-math";

import { extractCPAPayload } from "../../utils/parseCPAPayload";
import CPAVisualizer from "./CPAVisualizer";

interface ChatMessageProps {
  content: string;
}

/**
 * Sanitization schema extended for KaTeX output. rehype-katex emits MathML
 * (math/semantics/mrow/…) plus classed, styled spans — all stripped by the
 * default schema, so the whitelist is widened for exactly the tag/attribute
 * set KaTeX produces. Raw HTML still can't enter the tree: no rehype-raw is
 * registered, so markup in the message is escaped to text, and sanitize is
 * defense-in-depth if a raw-HTML plugin is ever added later.
 */
const SANITIZE_SCHEMA = {
  ...defaultSchema,
  tagNames: [
    ...(defaultSchema.tagNames ?? []),
    "math",
    "semantics",
    "annotation",
    "mrow",
    "mi",
    "mo",
    "mn",
    "mfrac",
    "msqrt",
    "msup",
    "msub",
    "msubsup",
    "mtext",
    "mstyle",
    "mspace",
    "mpadded",
    "menclose",
    "munder",
    "mover",
    "munderover",
  ],
  attributes: {
    ...defaultSchema.attributes,
    "*": [
      ...((defaultSchema.attributes ?? {})["*"] ?? []),
      "className",
      "style",
      "ariaHidden",
    ],
    annotation: [
      ...((defaultSchema.attributes ?? {})["annotation"] ?? []),
      "encoding",
    ],
    math: [...((defaultSchema.attributes ?? {})["math"] ?? []), "xmlns"],
  },
};

/**
 * One tutor message in the workspace coach thread.
 *
 * Text renders through ReactMarkdown (GFM-less) with $...$ math via KaTeX.
 * rehype-sanitize runs after rehype-katex so rendered math survives while
 * anything off-whitelist is dropped. When the backend embeds a structured
 * CPA payload (`json:cpa` fence or `<cpa_visual>` tag), the manipulative
 * renders beneath the text and the raw JSON is stripped from what the
 * learner sees.
 */
export default function ChatMessage({ content }: ChatMessageProps) {
  const { textContent, cpaPayload } = useMemo(() => extractCPAPayload(content), [content]);

  return (
    <div
      className="rounded-xl rounded-tl-sm bg-secondary px-4 py-3 text-sm leading-relaxed [&_ol]:list-decimal [&_ol]:pl-5 [&_p]:my-1 [&_ul]:list-disc [&_ul]:pl-5"
      aria-live="polite"
    >
      <ReactMarkdown
        remarkPlugins={[remarkMath]}
        rehypePlugins={[rehypeKatex, [rehypeSanitize, SANITIZE_SCHEMA]]}
      >
        {textContent}
      </ReactMarkdown>
      {cpaPayload && <CPAVisualizer payload={cpaPayload} />}
    </div>
  );
}
