import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import type { CanvasDocument, CanvasPoint, CanvasStroke } from "../../hooks/useCanvasSync";

export type WhiteboardHandle = { exportImage: () => string };
type Props = {
  document: CanvasDocument;
  onCommit: (document: CanvasDocument) => void;
  onUndo: () => void;
  onRedo: () => void;
  onClear: () => void;
  canUndo: boolean;
  canRedo: boolean;
};

const COLORS = [
  ["Indigo", "#4f46e5"], ["Emerald", "#059669"], ["Coral", "#f97360"], ["Dark slate", "#1e293b"],
] as const;

function drawStroke(ctx: CanvasRenderingContext2D, stroke: CanvasStroke) {
  if (stroke.points.length < 2) return;
  ctx.save();
  ctx.lineCap = "round"; ctx.lineJoin = "round";
  ctx.strokeStyle = stroke.tool === "eraser" ? "#ffffff" : stroke.color;
  ctx.globalCompositeOperation = stroke.tool === "eraser" ? "destination-out" : "source-over";
  ctx.lineWidth = stroke.width;
  ctx.beginPath();
  const first = stroke.points[0]; ctx.moveTo(first.x, first.y);
  for (let i = 1; i < stroke.points.length - 1; i += 1) {
    const p = stroke.points[i]; const n = stroke.points[i + 1];
    ctx.quadraticCurveTo(p.x, p.y, (p.x + n.x) / 2, (p.y + n.y) / 2);
  }
  const last = stroke.points[stroke.points.length - 1]; ctx.lineTo(last.x, last.y); ctx.stroke(); ctx.restore();
}

const WhiteboardCanvas = forwardRef<WhiteboardHandle, Props>(function WhiteboardCanvas(props, ref) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const activeRef = useRef<CanvasStroke | null>(null);
  const [tool, setTool] = useState<"pen" | "eraser">("pen");
  const [color, setColor] = useState("#4f46e5");

  const render = () => {
    const canvas = canvasRef.current; if (!canvas) return;
    const ctx = canvas.getContext("2d"); if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    props.document.strokes.forEach((stroke) => drawStroke(ctx, stroke));
    if (activeRef.current) drawStroke(ctx, activeRef.current);
  };

  useEffect(render, [props.document]);

  useEffect(() => {
    const canvas = canvasRef.current; if (!canvas) return;
    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.floor(rect.width * dpr));
      canvas.height = Math.max(1, Math.floor(rect.height * dpr));
      const ctx = canvas.getContext("2d"); ctx?.setTransform(dpr, 0, 0, dpr, 0, 0);
      render();
    };
    const observer = new ResizeObserver(resize); observer.observe(canvas); resize();
    return () => observer.disconnect();
  }, [props.document]);

  useImperativeHandle(ref, () => ({
    exportImage: () => canvasRef.current?.toDataURL("image/png", 0.85) ?? "",
  }), []);

  const point = (event: React.PointerEvent<HTMLCanvasElement>): CanvasPoint => {
    const rect = event.currentTarget.getBoundingClientRect();
    return { x: event.clientX - rect.left, y: event.clientY - rect.top, pressure: event.pressure || 0.5 };
  };
  const start = (event: React.PointerEvent<HTMLCanvasElement>) => {
    event.currentTarget.setPointerCapture(event.pointerId);
    activeRef.current = { id: crypto.randomUUID(), tool, color, width: tool === "eraser" ? 22 : Math.max(2, 3 * (event.pressure || 0.7)), points: [point(event)] };
  };
  const move = (event: React.PointerEvent<HTMLCanvasElement>) => {
    if (!activeRef.current) return;
    activeRef.current.points.push(point(event)); render();
  };
  const end = () => {
    const stroke = activeRef.current; activeRef.current = null;
    if (stroke && stroke.points.length > 1) props.onCommit({ ...props.document, strokes: [...props.document.strokes, stroke] });
  };

  return <section className="flex h-full min-h-0 flex-col rounded-3xl border border-slate-200 bg-white shadow-sm">
    <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 p-3" role="toolbar" aria-label="Scratchpad tools">
      <button type="button" onClick={() => setTool("pen")} aria-pressed={tool === "pen"} className="rounded-xl px-3 py-2 text-sm">✏️ Pen</button>
      <button type="button" onClick={() => setTool("eraser")} aria-pressed={tool === "eraser"} className="rounded-xl px-3 py-2 text-sm">⌫ Eraser</button>
      {COLORS.map(([name, value]) => <button key={value} type="button" aria-label={name} aria-pressed={color === value} onClick={() => { setColor(value); setTool("pen"); }} className="h-8 w-8 rounded-full border-2 border-white shadow ring-1 ring-slate-300" style={{ backgroundColor: value }} />)}
      <span className="mx-1 h-6 w-px bg-slate-200" />
      <button type="button" disabled={!props.canUndo} onClick={props.onUndo} className="rounded-xl px-3 py-2 text-sm">Undo</button>
      <button type="button" disabled={!props.canRedo} onClick={props.onRedo} className="rounded-xl px-3 py-2 text-sm">Redo</button>
      <button type="button" onClick={props.onClear} className="rounded-xl px-3 py-2 text-sm text-rose-700">Clear</button>
      <div className="ml-auto flex gap-1" aria-label="Math symbols">
        {["a/b", "√x", "Σ"].map((symbol) => <button key={symbol} type="button" className="rounded-lg bg-slate-100 px-2 py-1 text-sm" title="Copy symbol" onClick={() => navigator.clipboard?.writeText(symbol)}>{symbol}</button>)}
      </div>
    </div>
    <div className="relative min-h-[420px] flex-1 overflow-hidden rounded-b-3xl bg-white">
      <canvas ref={canvasRef} className="h-full w-full touch-none cursor-crosshair" aria-label="Interactive math scratchpad" onPointerDown={start} onPointerMove={move} onPointerUp={end} onPointerCancel={end} />
    </div>
  </section>;
});
export default WhiteboardCanvas;
