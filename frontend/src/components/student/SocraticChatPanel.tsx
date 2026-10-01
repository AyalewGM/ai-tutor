import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useWebSpeech } from "../../hooks/useWebSpeech";

export type ChatMessage = { id: string; role: "student" | "tutor"; text: string };
type Props = {
  topic: string;
  masteryPercent: number;
  messages: ChatMessage[];
  disabled?: boolean;
  onSend: (text: string) => Promise<void> | void;
  onSendCanvas: (text: string) => Promise<void> | void;
};

export default function SocraticChatPanel({ topic, masteryPercent, messages, disabled, onSend, onSendCanvas }: Props) {
  const [value, setValue] = useState("");
  const textarea = useRef<HTMLTextAreaElement>(null);
  const speech = useWebSpeech();

  useEffect(() => { if (speech.transcript) setValue(speech.transcript); }, [speech.transcript]);
  useEffect(() => {
    const last = messages[messages.length - 1];
    if (last?.role === "tutor") speech.speakText(last.text);
  }, [messages, speech.speakText]);

  const resize = useCallback(() => {
    const el = textarea.current; if (!el) return;
    el.style.height = "0px"; el.style.height = `${Math.min(el.scrollHeight, 144)}px`;
  }, []);
  useEffect(resize, [value, resize]);

  async function submit(event: FormEvent) {
    event.preventDefault(); const text = value.trim(); if (!text || disabled) return;
    setValue(""); await onSend(text);
  }

  const quick = ["I need a hint", "Can you explain that differently?", "What should I try first?"];

  return <section className="flex h-full min-h-0 flex-col rounded-3xl border border-slate-200 bg-white shadow-sm">
    <header className="flex flex-wrap items-center gap-2 border-b border-slate-200 p-4">
      <div className="min-w-0 flex-1"><p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Learning now</p><h1 className="truncate text-lg font-bold text-slate-900">{topic}</h1></div>
      <span className="rounded-full bg-indigo-50 px-3 py-1 text-sm font-semibold text-indigo-700">{masteryPercent}% mastery</span>
      <button type="button" onClick={speech.toggleAudio} aria-pressed={speech.audioEnabled} className="rounded-xl border border-slate-200 px-3 py-2 text-sm">{speech.audioEnabled ? "🔊 Audio on" : "🔇 Audio off"}</button>
      <Link to="/learn" className="rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-700 no-underline">Switch profile</Link>
    </header>

    <div className="min-h-0 flex-1 space-y-3 overflow-y-auto bg-slate-50 p-4" aria-live="polite">
      {messages.map((message) => <article key={message.id} className={message.role === "tutor" ? "mr-8 rounded-3xl rounded-tl-md border border-indigo-100 bg-white p-4 text-slate-800 shadow-sm" : "ml-8 rounded-3xl rounded-tr-md bg-indigo-600 p-4 text-white"}>
        <div className="mb-1 text-xs font-semibold opacity-70">{message.role === "tutor" ? "Tutor" : "You"}</div>
        <div className="whitespace-pre-wrap leading-7">{message.text}</div>
      </article>)}
    </div>

    <div className="border-t border-slate-200 p-3">
      <div className="mb-2 flex flex-wrap gap-2">{quick.map((q) => <button key={q} type="button" disabled={disabled} onClick={() => setValue(q)} className="rounded-full bg-violet-50 px-3 py-1.5 text-xs font-medium text-violet-700">{q}</button>)}</div>
      <form onSubmit={submit} className="flex items-end gap-2">
        <textarea ref={textarea} value={value} onChange={(e) => setValue(e.target.value)} rows={1} disabled={disabled} aria-label="Message your tutor" placeholder="Show your thinking…" className="min-h-11 flex-1 resize-none rounded-2xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500" />
        {speech.speechSupported && <button type="button" disabled={disabled} onClick={speech.isListening ? speech.stopListening : speech.startListening} aria-pressed={speech.isListening} className="h-11 rounded-xl border border-slate-200 px-3" aria-label="Voice input">{speech.isListening ? "■" : "🎙️"}</button>}
        <button type="button" disabled={disabled} onClick={() => onSendCanvas(value.trim())} className="h-11 rounded-xl border border-indigo-200 px-3 text-sm text-indigo-700" title="Share the current scratchpad with your tutor">Send canvas</button>
        <button type="submit" disabled={disabled || !value.trim()} className="h-11 rounded-xl bg-indigo-600 px-4 text-sm font-semibold text-white disabled:opacity-50">Send</button>
      </form>
      {speech.error && <p className="mt-2 text-xs text-rose-700" role="status">{speech.error}</p>}
    </div>
  </section>;
}
