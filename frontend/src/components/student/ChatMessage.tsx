import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { sanitizeMathString } from "../../utils/sanitizeMathString";

type Props = {
  text: string;
  role: "student" | "tutor";
};

export default function ChatMessage({ text, role }: Props) {
  return (
    <article className={role === "tutor" ? "mr-8 rounded-3xl rounded-tl-md border border-indigo-100 bg-white p-4 text-slate-800 shadow-sm" : "ml-8 rounded-3xl rounded-tr-md bg-indigo-600 p-4 text-white"}>
      <div className="mb-1 text-xs font-semibold opacity-70">{role === "tutor" ? "Tutor" : "You"}</div>
      <div className="chat-markdown leading-7">
        <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
          {sanitizeMathString(text)}
        </ReactMarkdown>
      </div>
    </article>
  );
}
