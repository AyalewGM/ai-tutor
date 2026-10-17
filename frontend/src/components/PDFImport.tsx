import { useEffect, useRef, useState } from "react";
import {
  getDocument,
  GlobalWorkerOptions,
  type PDFDocumentProxy,
} from "pdfjs-dist/legacy/build/pdf.mjs";
import workerURL from "pdfjs-dist/legacy/build/pdf.worker.mjs?url";

GlobalWorkerOptions.workerSrc = workerURL;
const button =
  "rounded-lg border bg-white px-3 py-2 text-slate-900 disabled:opacity-40";
const MAX_BYTES = 5 * 1024 * 1024;

function bounded<T>(promise: Promise<T>, milliseconds = 15000): Promise<T> {
  let timer: ReturnType<typeof setTimeout>;
  return Promise.race([
    promise,
    new Promise<never>((_, reject) => {
      timer = setTimeout(
        () =>
          reject(
            new Error(
              "This PDF took too long to render. Try a simpler file or a photo.",
            ),
          ),
        milliseconds,
      );
    }),
  ]).finally(() => clearTimeout(timer));
}

export default function PDFImport({
  disabled,
  onImport,
}: {
  disabled: boolean;
  onImport: (page: File) => Promise<boolean>;
}) {
  const [document, setDocument] = useState<PDFDocumentProxy | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [rendered, setRendered] = useState<{
    document: PDFDocumentProxy;
    page: number;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [rendering, setRendering] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const canvas = useRef<HTMLCanvasElement>(null);
  const generation = useRef(0);
  const current = useRef<PDFDocumentProxy | null>(null);
  const loadingTask = useRef<ReturnType<typeof getDocument> | null>(null);

  useEffect(
    () => () => {
      generation.current++;
      void loadingTask.current?.destroy();
      void current.current?.loadingTask.destroy();
    },
    [],
  );

  async function openPDF(file: File) {
    if (file.size > MAX_BYTES) {
      setError("Choose a PDF smaller than 5 MB.");
      return;
    }
    const request = ++generation.current;
    setLoading(true);
    setError("");
    setMessage("");
    setDocument(null);
    setRendered(null);
    let task: ReturnType<typeof getDocument> | undefined;
    try {
      await loadingTask.current?.destroy();
      await current.current?.loadingTask.destroy();
      current.current = null;
      const bytes = new Uint8Array(await file.arrayBuffer());
      if (new TextDecoder().decode(bytes.subarray(0, 5)) !== "%PDF-")
        throw new Error("Choose a valid PDF file.");
      const base = `${import.meta.env.BASE_URL}pdfjs/`;
      task = getDocument({
        data: bytes,
        cMapUrl: `${base}cmaps/`,
        cMapPacked: true,
        standardFontDataUrl: `${base}standard_fonts/`,
        wasmUrl: `${base}wasm/`,
        enableXfa: false,
        stopAtErrors: true,
        maxImageSize: 16_000_000,
        canvasMaxAreaInBytes: 16_000_000,
      });
      loadingTask.current = task;
      task.onPassword = () => {
        void task?.destroy();
      };
      const pdf = await bounded(task.promise);
      if (request !== generation.current) {
        await pdf.loadingTask.destroy();
        return;
      }
      if (pdf.numPages > 50) {
        await pdf.loadingTask.destroy();
        throw new Error("Choose a PDF with at most 50 pages.");
      }
      loadingTask.current = null;
      current.current = pdf;
      setPageNumber(1);
      setDocument(pdf);
    } catch (err) {
      await task?.destroy();
      if (request === generation.current)
        setError(
          err instanceof Error &&
            /valid PDF|50 pages|too long/.test(err.message)
            ? err.message
            : "Could not open this PDF. Use an unlocked PDF or a homework photo.",
        );
    } finally {
      if (request === generation.current) setLoading(false);
    }
  }

  useEffect(() => {
    if (!document || !canvas.current) return;
    let disposed = false;
    let renderTask:
      | ReturnType<Awaited<ReturnType<PDFDocumentProxy["getPage"]>>["render"]>
      | undefined;
    setRendering(true);
    setRendered(null);
    setError("");
    setMessage("");
    (async () => {
      try {
        const page = await bounded(document.getPage(pageNumber));
        if (disposed || !canvas.current) return;
        const original = page.getViewport({ scale: 1 });
        const scale = Math.min(1600 / original.width, 1000 / original.height);
        const viewport = page.getViewport({ scale });
        const surface = canvas.current;
        surface.width = Math.ceil(viewport.width);
        surface.height = Math.ceil(viewport.height);
        const context = surface.getContext("2d");
        if (!context) throw new Error("Canvas is unavailable");
        renderTask = page.render({
          canvas: surface,
          canvasContext: context,
          viewport,
          background: "white",
        });
        await bounded(renderTask.promise);
        if (!disposed) setRendered({ document, page: pageNumber });
      } catch (err) {
        renderTask?.cancel();
        if (!disposed)
          setError(
            err instanceof Error && err.message.includes("too long")
              ? err.message
              : "This page could not be rendered. Try a photo instead.",
          );
      } finally {
        if (!disposed) setRendering(false);
      }
    })();
    return () => {
      disposed = true;
      renderTask?.cancel();
    };
  }, [document, pageNumber]);

  const busy = disabled || loading || rendering || importing;
  const renderReady =
    rendered?.document === document && rendered?.page === pageNumber;
  return (
    <section
      className="space-y-3 rounded-xl border bg-white p-4 text-slate-900"
      aria-label="PDF homework importer"
    >
      <label className="block">
        Choose a homework PDF (up to 5 MB)
        <input
          className="block max-w-full"
          type="file"
          accept="application/pdf,.pdf"
          disabled={busy}
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void openPDF(file);
            event.target.value = "";
          }}
        />
      </label>
      <p className="text-sm">
        Your original PDF stays on this device. Import one selected page at a
        time to work on it together.
      </p>
      {error && <p role="alert">{error}</p>}
      {(loading || rendering) && <p role="status">Preparing PDF page…</p>}
      {document && (
        <div className="flex flex-wrap items-center gap-2">
          <button
            className={button}
            disabled={busy || pageNumber <= 1}
            onClick={() => setPageNumber((value) => value - 1)}
          >
            Previous PDF page
          </button>
          <span aria-live="polite">
            PDF page {pageNumber} of {document.numPages}
          </span>
          <button
            className={button}
            disabled={busy || pageNumber >= document.numPages}
            onClick={() => setPageNumber((value) => value + 1)}
          >
            Next PDF page
          </button>
          <button
            className={button}
            disabled={busy || !!error || !renderReady}
            onClick={async () => {
              if (!canvas.current) return;
              setImporting(true);
              setMessage("");
              try {
                const blob = await new Promise<Blob | null>((resolve) =>
                  canvas.current!.toBlob(resolve, "image/jpeg", 0.9),
                );
                if (!blob) throw new Error("The page could not be exported");
                if (
                  await onImport(
                    new File([blob], "worksheet-page.jpg", {
                      type: "image/jpeg",
                    }),
                  )
                )
                  setMessage("Page added to your shared board.");
              } catch {
                setError("The page could not be imported. Try again.");
              } finally {
                setImporting(false);
              }
            }}
          >
            Add selected PDF page
          </button>
        </div>
      )}
      <canvas
        ref={canvas}
        hidden={!document}
        className="max-w-full max-h-[50vh] w-auto h-auto border"
        role="img"
        aria-label={`PDF preview page ${pageNumber}`}
      />
      {message && <p role="status">{message}</p>}
    </section>
  );
}
