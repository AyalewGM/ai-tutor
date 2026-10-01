import { useCallback, useEffect, useRef, useState } from "react";
import { Eraser, PenLine, Trash2, X, PenTool } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * Scratch pad for learners to sketch work.
 *
 * - Unified pointer events (mouse, touch, stylus)
 * - Pen and eraser tools, clear, hide
 * - No data persistence — purely a scratch space
 * - No handwriting recognition or submission; nothing leaves the browser
 */

const PEN_COLOR = "#211c35";
const PEN_WIDTH = 2.5;
const ERASER_WIDTH = 18;

interface ScratchPadProps {
  defaultVisible?: boolean;
}

export default function ScratchPad({ defaultVisible = false }: ScratchPadProps) {
  const [visible, setVisible] = useState(defaultVisible);
  const [tool, setTool] = useState<"pen" | "eraser">("pen");
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const lastPoint = useRef<{ x: number; y: number } | null>(null);

  // Resize canvas to match its display size, preserving existing strokes.
  const resize = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0) return;
    const dpr = window.devicePixelRatio || 1;

    const snapshot = document.createElement("canvas");
    snapshot.width = canvas.width;
    snapshot.height = canvas.height;
    snapshot.getContext("2d")?.drawImage(canvas, 0, 0);

    canvas.width = Math.round(rect.width * dpr);
    canvas.height = Math.round(rect.height * dpr);
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    if (snapshot.width > 0) ctx.drawImage(snapshot, 0, 0, rect.width, rect.height);
  }, []);

  useEffect(() => {
    if (!visible) return;
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, [visible, resize]);

  const pointFrom = (e: React.PointerEvent) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    return rect ? { x: e.clientX - rect.left, y: e.clientY - rect.top } : null;
  };

  const onPointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    canvasRef.current?.setPointerCapture(e.pointerId);
    drawing.current = true;
    lastPoint.current = pointFrom(e);
  };

  const onPointerMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!drawing.current) return;
    e.preventDefault();
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    const point = pointFrom(e);
    if (!ctx || !point || !lastPoint.current) return;

    ctx.strokeStyle = tool === "pen" ? PEN_COLOR : "#ffffff";
    ctx.lineWidth = tool === "pen" ? PEN_WIDTH : ERASER_WIDTH;
    ctx.beginPath();
    ctx.moveTo(lastPoint.current.x, lastPoint.current.y);
    ctx.lineTo(point.x, point.y);
    ctx.stroke();
    lastPoint.current = point;
  };

  const onPointerEnd = () => {
    drawing.current = false;
    lastPoint.current = null;
  };

  const clear = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (canvas && ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
  };

  if (!visible) {
    return (
      <Button
        type="button"
        variant="outline"
        onClick={() => setVisible(true)}
        aria-expanded="false"
        aria-controls="scratchpad"
      >
        <PenTool className="h-4 w-4" /> Scratch pad
      </Button>
    );
  }

  const toolButton = (
    name: "pen" | "eraser",
    label: string,
    Icon: typeof PenLine,
  ) => (
    <button
      type="button"
      aria-label={label}
      aria-pressed={tool === name}
      title={label}
      onClick={() => setTool(name)}
      className={cn(
        "flex h-9 w-9 items-center justify-center rounded-md border transition-colors",
        tool === name
          ? "border-primary bg-primary/10 text-primary"
          : "border-border bg-card text-muted-foreground hover:bg-secondary",
      )}
    >
      <Icon className="h-4 w-4" />
    </button>
  );

  return (
    <div className="rounded-xl border border-border bg-card p-3" id="scratchpad">
      <div className="mb-2 flex items-center gap-1.5">
        {toolButton("pen", "Pen", PenLine)}
        {toolButton("eraser", "Eraser", Eraser)}
        <span className="mx-1 h-5 w-px bg-border" aria-hidden="true" />
        <button
          type="button"
          aria-label="Clear scratch pad"
          title="Clear"
          onClick={clear}
          className="flex h-9 items-center gap-1.5 rounded-md border border-border bg-card px-3 text-sm text-muted-foreground transition-colors hover:bg-secondary"
        >
          <Trash2 className="h-4 w-4" /> Clear
        </button>
        <button
          type="button"
          aria-label="Hide scratch pad"
          title="Hide"
          onClick={() => setVisible(false)}
          className="ml-auto flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-secondary"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <canvas
        ref={canvasRef}
        className="scratch-canvas"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerEnd}
        onPointerCancel={onPointerEnd}
        role="img"
        aria-label="Drawing area — sketch your work here"
      />
    </div>
  );
}
