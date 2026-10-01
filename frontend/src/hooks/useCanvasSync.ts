import { useCallback, useState } from "react";
import { post } from "../api";

export type CanvasPoint = { x: number; y: number; pressure: number };
export type CanvasStroke = {
  id: string;
  tool: "pen" | "eraser";
  color: string;
  width: number;
  points: CanvasPoint[];
};
export type CanvasDocument = { version: 1; strokes: CanvasStroke[] };

type MultimodalPayload = {
  session_id: string;
  prompt: string;
  canvas: CanvasDocument;
  snapshot_data_url: string;
};

export function useCanvasSync(initial: CanvasDocument = { version: 1, strokes: [] }) {
  const [document, setDocument] = useState<CanvasDocument>(initial);
  const [past, setPast] = useState<CanvasDocument[]>([]);
  const [future, setFuture] = useState<CanvasDocument[]>([]);
  const [isSending, setIsSending] = useState(false);

  const commit = useCallback((next: CanvasDocument) => {
    setDocument((current) => {
      setPast((items) => [...items.slice(-49), current]);
      setFuture([]);
      return next;
    });
  }, []);

  const undo = useCallback(() => {
    setPast((items) => {
      if (!items.length) return items;
      const previous = items[items.length - 1];
      setDocument((current) => {
        setFuture((next) => [current, ...next].slice(0, 50));
        return previous;
      });
      return items.slice(0, -1);
    });
  }, []);

  const redo = useCallback(() => {
    setFuture((items) => {
      if (!items.length) return items;
      const next = items[0];
      setDocument((current) => {
        setPast((previous) => [...previous.slice(-49), current]);
        return next;
      });
      return items.slice(1);
    });
  }, []);

  const clear = useCallback(() => commit({ version: 1, strokes: [] }), [commit]);

  const serialize = useCallback(() => JSON.stringify(document), [document]);

  const sendSnapshot = useCallback(async <T,>(
    endpoint: string | null,
    payload: Omit<MultimodalPayload, "canvas">,
  ): Promise<T | null> => {
    if (!endpoint) return null;
    setIsSending(true);
    try {
      return await post<T>(endpoint, { ...payload, canvas: document });
    } finally {
      setIsSending(false);
    }
  }, [document]);

  return { document, commit, undo, redo, clear, serialize, canUndo: past.length > 0, canRedo: future.length > 0, isSending, sendSnapshot };
}
