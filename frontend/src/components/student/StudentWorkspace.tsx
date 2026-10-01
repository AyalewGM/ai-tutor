import { useRef, useState } from "react";
import SocraticChatPanel, { type ChatMessage } from "./SocraticChatPanel";
import WhiteboardCanvas, { type WhiteboardHandle } from "./WhiteboardCanvas";
import { useCanvasSync } from "../../hooks/useCanvasSync";

type Props = {
  sessionId: string;
  topic: string;
  masteryPercent: number;
  initialMessages: ChatMessage[];
  onSendText: (text: string) => Promise<void>;
  multimodalEndpoint?: string | null;
};

export default function StudentWorkspace({ sessionId, topic, masteryPercent, initialMessages, onSendText, multimodalEndpoint = "/tutor/multimodal-step" }: Props) {
  const boardRef = useRef<WhiteboardHandle>(null);
  const canvas = useCanvasSync();
  const [messages, setMessages] = useState(initialMessages);
  const [mobileTab, setMobileTab] = useState<"chat" | "board">("chat");
  const [busy, setBusy] = useState(false);

  async function send(text: string) {
    if (!text.trim()) return;
    const student: ChatMessage = { id: crypto.randomUUID(), role: "student", text };
    setMessages((items) => [...items, student]);
    setBusy(true);
    try { await onSendText(text); } finally { setBusy(false); }
  }

  async function sendCanvas(text: string) {
    const snapshot = boardRef.current?.exportImage() ?? "";
    if (!snapshot) return;
    if (!multimodalEndpoint) {
      setMessages((items) => [...items, { id: crypto.randomUUID(), role: "tutor", text: "Canvas sharing is not enabled for this learning session yet." }]);
      return;
    }
    setBusy(true);
    try {
      const result = await canvas.sendSnapshot<{ message: string; overlays: { kind: "highlight" | "label"; text: string; x: number; y: number }[] }>(multimodalEndpoint, { session_id: sessionId, prompt: text || "Please help me with the work shown on my scratchpad.", snapshot_data_url: snapshot });
      setMessages((items) => [...items,
        { id: crypto.randomUUID(), role: "student", text: text || "I shared my scratchpad." },
        ...(result ? [{ id: crypto.randomUUID(), role: "tutor" as const, text: result.message }] : []),
      ]);
    } finally { setBusy(false); }
  }

  return <main className="h-screen overflow-hidden bg-slate-50 p-2 md:p-4">
    <nav className="mb-2 grid grid-cols-2 gap-2 md:hidden" aria-label="Workspace panels">
      <button type="button" onClick={() => setMobileTab("chat")} aria-pressed={mobileTab === "chat"} className="rounded-2xl bg-white p-3 shadow-sm">💬 Chat</button>
      <button type="button" onClick={() => setMobileTab("board")} aria-pressed={mobileTab === "board"} className="rounded-2xl bg-white p-3 shadow-sm">🎨 Scratchpad</button>
    </nav>
    <div className="grid h-[calc(100%-4rem)] min-h-0 grid-cols-1 gap-3 md:h-full md:grid-cols-[minmax(320px,40fr)_minmax(420px,60fr)]">
      <div className={mobileTab === "chat" ? "min-h-0" : "hidden min-h-0 md:block"}><SocraticChatPanel topic={topic} masteryPercent={masteryPercent} messages={messages} disabled={busy} onSend={send} onSendCanvas={sendCanvas} /></div>
      <div className={mobileTab === "board" ? "min-h-0" : "hidden min-h-0 md:block"}><WhiteboardCanvas ref={boardRef} document={canvas.document} onCommit={canvas.commit} onUndo={canvas.undo} onRedo={canvas.redo} onClear={canvas.clear} canUndo={canvas.canUndo} canRedo={canvas.canRedo} /></div>
    </div>
  </main>;
}
