import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Scratch pad for learners to sketch work.
 *
 * - Touch and mouse drawing
 * - Clear button
 * - Toggle visibility to save screen space
 * - No data persistence — purely a scratch space
 * - No handwriting recognition or submission
 */

const PEN_COLOR = "#211c35";
const PEN_WIDTH = 2.5;
const ERASER_WIDTH = 18;

interface ScratchPadProps {
  defaultVisible?: boolean;
}

export default function ScratchPad({ defaultVisible = false }: ScratchPadProps) {
  const [visible, setVisible] = useState(defaultVisible);
  const [drawing, setDrawing] = useState(false);
  const [tool, setTool] = useState<"pen" | "eraser">("pen");
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const lastPoint = useRef<{ x: number; y: number } | null>(null);

  const getCtx = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    return canvas.getContext("2d");
  }, []);

  // Resize canvas to match its display size
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !visible) return;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      const ctx = canvas.getContext("2d");
      if (ctx) ctx.scale(dpr, dpr);
    };

    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, [visible]);

  const getPoint = useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
      const canvas = canvasRef.current;
      if (!canvas) return null;
      const rect = canvas.getBoundingClientRect();

      if ("touches" in e) {
        const touch = e.touches[0];
        return { x: touch.clientX - rect.left, y: touch.clientY - rect.top };
      }
      return { x: e.clientX - rect.left, y: e.clientY - rect.top };
    },
    [],
  );

  const startStroke = useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
      e.preventDefault();
      setDrawing(true);
      lastPoint.current = getPoint(e);
    },
    [getPoint],
  );

  const moveStroke = useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
      if (!drawing) return;
      e.preventDefault();
      const point = getPoint(e);
      const ctx = getCtx();
      if (!point || !ctx || !lastPoint.current) return;

      ctx.beginPath();
      ctx.moveTo(lastPoint.current.x, lastPoint.current.y);
      ctx.lineTo(point.x, point.y);
      ctx.strokeStyle = tool === "pen" ? PEN_COLOR : "#f7f8fc";
      ctx.lineWidth = tool === "pen" ? PEN_WIDTH : ERASER_WIDTH;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.stroke();

      lastPoint.current = point;
    },
    [drawing, getPoint, getCtx, tool],
  );

  const endStroke = useCallback(() => {
    setDrawing(false);
    lastPoint.current = null;
  }, []);

  const clear = useCallback(() => {
    const ctx = getCtx();
    const canvas = canvasRef.current;
    if (!ctx || !canvas) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }, [getCtx]);

  if (!visible) {
    return (
      <button
        type="button"
        className="scratch-toggle secondary"
        onClick={() => setVisible(true)}
        aria-expanded="false"
        aria-controls="scratchpad"
      >
        Scratch pad
      </button>
    );
  }

  return (
    <div className="scratch-panel" id="scratchpad">
      <div className="scratch-toolbar">
        <button
          type="button"
          className={`tool-btn ${tool === "pen" ? "active" : ""}`}
          onClick={() => setTool("pen")}
          aria-label="Pen"
          title="Pen"
        >
          ✏️
        </button>
        <button
          type="button"
          className={`tool-btn ${tool === "eraser" ? "active" : ""}`}
          onClick={() => setTool("eraser")}
          aria-label="Eraser"
          title="Eraser"
        >
          🧹
        </button>
        <button
          type="button"
          className="tool-btn clear-btn"
          onClick={clear}
          aria-label="Clear scratch pad"
        >
          Clear
        </button>
        <button
          type="button"
          className="tool-btn close-btn"
          onClick={() => setVisible(false)}
          aria-label="Hide scratch pad"
        >
          ×
        </button>
      </div>
      <canvas
        ref={canvasRef}
        className="scratch-canvas"
        onMouseDown={startStroke}
        onMouseMove={moveStroke}
        onMouseUp={endStroke}
        onMouseLeave={endStroke}
        onTouchStart={startStroke}
        onTouchMove={moveStroke}
        onTouchEnd={endStroke}
        onTouchCancel={endStroke}
        role="img"
        aria-label="Drawing area — sketch your work here"
      />
    </div>
  );
}
