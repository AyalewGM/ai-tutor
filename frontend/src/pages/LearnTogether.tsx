import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Eraser,
  FileDown,
  Hand,
  ImagePlus,
  Maximize,
  Minimize,
  MousePointer2,
  Pen,
  Redo2,
  Type,
  Undo2,
} from "lucide-react";
import { api, ApiError, post, postForm } from "../api";
import { inkPath, previewPoints } from "../liveInk";
import NavBar from "../components/NavBar";

const PDFImport = lazy(() => import("../components/PDFImport"));

type Point = { x: number; y: number };
type Mark = {
  operation_id: string;
  kind: "stroke" | "text" | "undo" | "erase" | "image" | "page";
  page_id?: string | null;
  image_id?: string;
  points?: Point[];
  text?: string;
  x?: number;
  y?: number;
  target?: string;
  author?: string;
  revision?: number;
};
type LiveFrame = {
  kind: "pointer" | "stroke" | "clear";
  page_id?: string | null;
  operation_id?: string;
  points?: Point[];
  point?: Point;
  source?: string;
  author?: string;
  seen?: number;
};
type Board = {
  id: string;
  student_id: string;
  author: string;
  closed: boolean;
  name: string;
  deleted?: boolean;
};
const color = (author?: string) =>
  author?.startsWith("parent:") ? "#6d28d9" : "#0369a1";
const button =
  "inline-flex min-h-10 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-800 shadow-sm transition-colors hover:bg-violet-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-600 disabled:cursor-not-allowed disabled:opacity-40";
const activeTool = "border-violet-400 bg-violet-100 text-violet-950";

function savedAgo(timestamp: number, now: number) {
  const seconds = Math.max(0, Math.floor((now - timestamp) / 1000));
  if (seconds < 15) return "Autosaved just now";
  if (seconds < 60) return `Autosaved ${seconds}s ago`;
  return `Autosaved ${Math.floor(seconds / 60)}m ago`;
}

export default function LearnTogether() {
  const { boardId } = useParams();
  const navigate = useNavigate();
  const [boards, setBoards] = useState<Board[]>([]);
  const [trashedBoards, setTrashedBoards] = useState<Board[]>([]);
  const [boardMenu, setBoardMenu] = useState(false);
  const [newBoardOpen, setNewBoardOpen] = useState(false);
  const [newBoardChild, setNewBoardChild] = useState("");
  const [boardAction, setBoardAction] = useState<"clear" | "delete" | "rename" | "clearpage" | null>(null);
  const [boardActionPage, setBoardActionPage] = useState<string | null>(null);
  const [boardTitle, setBoardTitle] = useState("");
  const [managingBoard, setManagingBoard] = useState(false);
  const [children, setChildren] = useState<
    { id: string; first_name: string }[]
  >([]);
  const [board, setBoard] = useState<Board | null>(null);
  const [selectedPage, setSelectedPage] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [showPDF, setShowPDF] = useState(false);
  const [marks, setMarks] = useState<Mark[]>([]);
  const [pending, setPending] = useState<Mark[]>([]);
  const [draft, setDraft] = useState<Point[]>([]);
  const [peers, setPeers] = useState<Record<string, LiveFrame>>({});
  const [pointerPosition, setPointerPosition] = useState<Point | null>(null);
  const pointerVisible = useRef(false);
  const inkPage = useRef<string | null>(null);
  const [liveAvailable, setLiveAvailable] = useState(false);
  const liveSocket = useRef<WebSocket | null>(null);
  const liveEnabled = useRef(false);
  const lastLiveSend = useRef(0);
  const liveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const waitingLive = useRef<LiveFrame | null>(null);
  const confirmed = useRef(new Set<string>());
  const inkID = useRef<string | null>(null);
  const localPointer = useRef<Point>({ x: 800, y: 500 });
  const draftFrame = useRef<number | null>(null);
  const [tool, setTool] = useState<
    "pen" | "text" | "erase" | "pan" | "pointer"
  >("pen");
  const [zoom, setZoom] = useState(1);
  const [uploading, setUploading] = useState(false);
  const uploadBusy = useRef(false);
  const uploadAttempt = useRef<{ file: File; id: string } | null>(null);
  const [uploadFailed, setUploadFailed] = useState(false);
  const [text, setText] = useState("");
  const [status, setStatus] = useState("Connecting…");
  const [error, setError] = useState("");
  const [share, setShare] = useState("");
  const [clearConfirm, setClearConfirm] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [pagesOpen, setPagesOpen] = useState(true);
  const [lastSavedAt, setLastSavedAt] = useState<number | null>(null);
  const [now, setNow] = useState(Date.now());
  const [fullscreen, setFullscreen] = useState(false);
  const photoInput = useRef<HTMLInputElement>(null);
  const viewport = useRef<HTMLDivElement>(null);
  const svg = useRef<SVGSVGElement>(null);
  const pointer = useRef<number | null>(null);
  const panStart = useRef<{
    id: number;
    x: number;
    y: number;
    left: number;
    top: number;
  } | null>(null);
  const stroke = useRef<Point[]>([]);
  const queue = useRef<Mark[]>([]);
  const revision = useRef(0);
  const ingest = useRef<(batch: Mark[]) => void>(() => {});
  const author = useRef("");

  async function newBlankPage() {
    if (!board || board.closed || !ready || uploading || pending.length ||
        managingBoard || clearing) return;
    const canvas = document.createElement("canvas");
    canvas.width = 1600;
    canvas.height = 1000;
    const context = canvas.getContext("2d");
    if (!context) {
      setError("This browser cannot create a new page.");
      return;
    }
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, "image/jpeg", 0.85),
    );
    if (!blob) {
      setError("Unable to create a blank page.");
      return;
    }
    await uploadPhoto(new File([blob], "blank-worksheet.jpg", { type: "image/jpeg" }),
      crypto.randomUUID());
  }

  // Board management uses parent-authorized server endpoints only; never
  // erase another participant's marks through client-side filtering.
  async function refreshBoardList() {
    const active = await api<Board[]>("/together/boards");
    setBoards(active);
    if (active.some((item) => item.author.startsWith("parent:"))) {
      const trash = await api<Board[]>("/together/boards/trash");
      setTrashedBoards(trash);
    } else {
      setTrashedBoards([]);
    }
  }

  async function createNewBoard(studentId: string) {
    if (!studentId || managingBoard) return;
    setManagingBoard(true);
    setError("");
    try {
      const created = await post<Board>("/together/boards", { student_id: studentId });
      setNewBoardOpen(false);
      navigate("/together/" + created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create board.");
    } finally {
      setManagingBoard(false);
    }
  }

  async function manageCurrentBoard() {
    if (!boardId || !board || !board.author.startsWith("parent:") ||
        !boardAction || managingBoard) return;
    if ((boardAction === "clear" || boardAction === "clearpage") && !canClear) return;
    if (boardAction === "delete" && (!canClear || !ready)) return;
    setManagingBoard(true);
    setError("");
    try {
      if (boardAction === "rename") {
        const next = await post<Board>("/together/boards/" + boardId + "/rename", {
          name: boardTitle.trim(),
        });
        setBoard(next);
      } else if (boardAction === "delete") {
        await post("/together/boards/" + boardId + "/trash", {});
        setBoardAction(null);
        navigate("/together");
        return;
      } else {
        const pageRevision = revision.current;
        const result = await post<{ result_revision: number; cleared_count: number }>(
          "/together/boards/" + boardId +
            (boardAction === "clearpage" ? "/clear-page" : "/clear-board"), {
              operation_id: crypto.randomUUID(),
              expected_revision: pageRevision,
              ...(boardAction === "clearpage" ? { page_id: boardActionPage } : {}),
            },
        );
        let cursor = revision.current;
        while (cursor < result.result_revision) {
          const batch = await api<Mark[]>(
            "/together/boards/" + boardId + "/operations?after=" + cursor,
          );
          if (!batch.length) throw new Error("Board is still synchronizing. Refresh.");
          ingest.current(batch);
          const next = Math.max(cursor, ...batch.map((mark) => mark.revision || 0));
          if (next === cursor) throw new Error("Board update stalled. Refresh.");
          cursor = next;
        }
        setStatus("Cleared " + result.cleared_count + " saved marks " +
          (boardAction === "clearpage" ? "on this page." : "across all pages."));
      }
      setBoardAction(null);
      setBoardMenu(false);
      await refreshBoardList();
    } catch (err) {
      setError(err instanceof ApiError && err.status === 409
        ? "The board changed or the operation was already handled. Refresh and review it before retrying."
        : err instanceof Error ? err.message : "Board action failed.");
    } finally {
      setManagingBoard(false);
    }
  }

  function sendLive(frame: LiveFrame, force = false) {
    if (force) {
      if (liveTimer.current !== null) clearTimeout(liveTimer.current);
      liveTimer.current = null;
      waitingLive.current = null;
    }
    const socket = liveSocket.current;
    if (
      !liveEnabled.current ||
      !socket ||
      socket.readyState !== WebSocket.OPEN ||
      socket.bufferedAmount > 32768
    )
      return;
    const now = performance.now();
    if (!force && now - lastLiveSend.current < 50) {
      waitingLive.current = frame;
      if (liveTimer.current === null)
        liveTimer.current = setTimeout(
          () => {
            const latest = waitingLive.current;
            liveTimer.current = null;
            waitingLive.current = null;
            if (latest) sendLive(latest, true);
          },
          50 - (now - lastLiveSend.current),
        );
      return;
    }
    lastLiveSend.current = now;
    socket.send(JSON.stringify(frame));
  }
  function paintDraft() {
    if (draftFrame.current !== null) return;
    draftFrame.current = requestAnimationFrame(() => {
      draftFrame.current = null;
      setDraft([...stroke.current]);
      setPointerPosition(pointerVisible.current ? localPointer.current : null);
    });
  }
  useEffect(() => {
    const tick = setInterval(() => setNow(Date.now()), 15000);
    const onFullscreen = () => setFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", onFullscreen);
    return () => {
      clearInterval(tick);
      document.removeEventListener("fullscreenchange", onFullscreen);
    };
  }, []);
  useEffect(() => {
    const timer = setInterval(
      () =>
        setPeers((old) =>
          Object.fromEntries(
            Object.entries(old).filter(
              ([, value]) => Date.now() - (value.seen || 0) < 2500,
            ),
          ),
        ),
      250,
    );
    return () => {
      clearInterval(timer);
      if (liveTimer.current !== null) clearTimeout(liveTimer.current);
      if (draftFrame.current !== null) cancelAnimationFrame(draftFrame.current);
    };
  }, []);
  useEffect(() => {
    if (inkID.current && stroke.current.length)
      enqueue({
        operation_id: inkID.current,
        kind: "stroke",
        page_id: inkPage.current,
        points: [...stroke.current],
      });
    sendLive({ kind: "clear" }, true);
    pointerVisible.current = false;
    setPointerPosition(null);
    pointer.current = null;
    inkID.current = null;
    stroke.current = [];
    setDraft([]);
    setPeers({});
  }, [selectedPage, tool]);

  function persistQueue() {
    if (!boardId || !author.current) return;
    try {
      const key = `mihur-board-pending:${boardId}:${author.current}`;
      if (queue.current.length)
        sessionStorage.setItem(key, JSON.stringify(queue.current));
      else sessionStorage.removeItem(key);
    } catch {
      /* The server remains authoritative if browser storage is unavailable. */
    }
  }

  useEffect(() => {
    if (!boardId) return;
    // The active-board route previously never loaded the board switcher or
    // parent child list; do so without changing existing WebSocket state.
    void refreshBoardList().catch(() => {});
    void api<{ id: string; first_name: string }[]>("/parents/children")
      .then(setChildren).catch(() => setChildren([]));
  }, [boardId]);

  useEffect(() => {
    let disposed = false;
    let socket: WebSocket | undefined;
    let reconnect: ReturnType<typeof setTimeout>;
    let retry: ReturnType<typeof setTimeout>;
    let sending = false;
    setError("");
    setReady(false);
    setSelectedPage(null);
    setShowPDF(false);
    setBoard(null);
    setMarks([]);
    setDraft([]);
    setPending([]);
    queue.current = [];
    revision.current = 0;
    confirmed.current.clear();
    setPeers({});
    liveEnabled.current = false;
    setLiveAvailable(false);
    function merge(batch: Mark[]) {
      if (disposed || !batch.length) return;
      const previousRevision = revision.current;
      revision.current = Math.max(
        revision.current,
        ...batch.map((m) => m.revision || 0),
      );
      const ids = new Set(batch.map((m) => m.operation_id));
      for (const id of ids) confirmed.current.add(id);
      setPeers((old) =>
        Object.fromEntries(
          Object.entries(old).filter(
            ([, frame]) => !frame.operation_id || !ids.has(frame.operation_id),
          ),
        ),
      );
      const ownConfirmed = queue.current.some((m) => ids.has(m.operation_id));
      queue.current = queue.current.filter((m) => !ids.has(m.operation_id));
      persistQueue();
      if (ownConfirmed) setLastSavedAt(Date.now());
      setPending([...queue.current]);
      const navigation = batch
        .filter((m) => (m.revision || 0) > previousRevision)
        .reverse()
        .find((m) => m.kind === "page" || m.kind === "image");
      if (navigation)
        setSelectedPage(
          navigation.kind === "image"
            ? navigation.operation_id
            : navigation.target || null,
        );
      setMarks((old) =>
        [...old.filter((m) => !ids.has(m.operation_id)), ...batch].sort(
          (a, b) => (a.revision || 0) - (b.revision || 0),
        ),
      );
    }
    ingest.current = merge;
    async function send() {
      if (disposed || !boardId || sending) return;
      sending = true;
      const mark = queue.current[0];
      try {
        if (mark) {
          const { author: _author, ...payload } = mark;
          await post(`/together/boards/${boardId}/operations`, payload);
          // Keep pending until the server's ordered stream confirms the mark.
          const batch = await api<Mark[]>(
            `/together/boards/${boardId}/operations?after=${revision.current}`,
          );
          merge(batch);
        }
      } catch (err) {
        if (!disposed) {
          setStatus("Waiting to save — keep this page open");
          if (
            err instanceof ApiError &&
            err.status >= 400 &&
            err.status < 500
          ) {
            setError(err.message);
            queue.current = [];
            persistQueue();
            setPending([]);
          }
        }
      } finally {
        sending = false;
        if (!disposed) retry = setTimeout(send, 700);
      }
    }
    function connect() {
      if (disposed || !boardId) return;
      socket = new WebSocket(
        `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/api/v1/together/boards/${boardId}/live?after=${revision.current}`,
      );
      liveSocket.current = socket;
      socket.onopen = () => {
        if (!disposed) setStatus("Connected · work saves automatically");
      };
      socket.onmessage = (event) => {
        if (disposed) return;
        const data = JSON.parse(event.data);
        if (data.ephemeral) {
          const frame = data.ephemeral as LiveFrame;
          if (!frame.source) return;
          setPeers((old) => {
            const next = { ...old };
            if (
              frame.kind === "clear" ||
              (frame.operation_id && confirmed.current.has(frame.operation_id))
            )
              delete next[frame.source!];
            else next[frame.source!] = { ...frame, seen: Date.now() };
            return Object.fromEntries(Object.entries(next).slice(-16));
          });
          return;
        }
        liveEnabled.current = !!data.live_available;
        setLiveAvailable(!!data.live_available);
        merge(data.operations);
        if (data.operations.length < 200) setReady(true);
        if (data.closed) {
          setBoard((old) => old && { ...old, closed: true });
          setStatus("Board closed · saved work is available");
        }
      };
      socket.onclose = (event) => {
        liveEnabled.current = false;
        setLiveAvailable(false);
        setPeers({});
        if (!disposed && event.code !== 1000 && event.code !== 1008) {
          setStatus("Reconnecting — keep this page open");
          reconnect = setTimeout(connect, 2000);
        } else if (!disposed && event.code === 1008)
          setError("Access unavailable. Refresh or sign in again.");
      };
    }
    if (boardId) {
      api<Board>(`/together/boards/${boardId}`)
        .then((value) => {
          if (disposed) return;
          setBoard(value);
          author.current = value.author;
          try {
            const saved = JSON.parse(
              sessionStorage.getItem(
                `mihur-board-pending:${boardId}:${value.author}`,
              ) || "[]",
            );
            if (Array.isArray(saved))
              queue.current = saved
                .filter((m) => m.author === value.author)
                .slice(0, 50);
          } catch {
            queue.current = [];
          }
          setPending([...queue.current]);
          connect();
          send();
        })
        .catch((err) => {
          if (!disposed) setError(err.message);
        });
    } else {
      api<Board[]>("/together/boards")
        .then(async (values) => {
          if (disposed) return;
          setBoards(values);
          // A parent must still be able to recover a board after deleting
          // their LAST active board. Learners cannot browse family Trash.
          void api<Board[]>("/together/boards/trash")
            .then((trash) => { if (!disposed) setTrashedBoards(trash); })
            .catch(() => { if (!disposed) setTrashedBoards([]); });
          if (!values.length || values[0].author.startsWith("parent:")) {
            try {
              const values =
                await api<{ id: string; first_name: string }[]>(
                  "/parents/children",
                );
              if (!disposed) setChildren(values);
            } catch {
              /* Learners can join existing boards only. */
            }
          }
        })
        .catch((err) => {
          if (!disposed) setError(err.message);
        });
    }
    const beforeUnload = (event: BeforeUnloadEvent) => {
      if (queue.current.length || uploadBusy.current) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    const guardNavigation = (event: MouseEvent) => {
      if (
        (queue.current.length || uploadBusy.current) &&
        (event.target as Element).closest?.("a[href]")
      ) {
        event.preventDefault();
        event.stopPropagation();
        setError(
          "Please wait for your marks to save before leaving the board.",
        );
      }
    };
    document.addEventListener("click", guardNavigation, true);
    window.addEventListener("beforeunload", beforeUnload);
    return () => {
      disposed = true;
      ingest.current = () => {};
      liveSocket.current = null;
      liveEnabled.current = false;
      socket?.close();
      clearTimeout(reconnect);
      clearTimeout(retry);
      window.removeEventListener("beforeunload", beforeUnload);
      document.removeEventListener("click", guardNavigation, true);
    };
  }, [boardId]);

  function enqueue(mark: Mark) {
    if (!board || board.closed || clearing || queue.current.length >= 50) return;
    queue.current.push({
      ...mark,
      ...(mark.kind === "page"
        ? {}
        : {
            page_id: mark.page_id === undefined ? selectedPage : mark.page_id,
          }),
      author: author.current,
    });
    persistQueue();
    setPending([...queue.current]);
  }
  function point(event: { clientX: number; clientY: number }): Point {
    const matrix = svg.current!.getScreenCTM()!.inverse();
    const p = new DOMPoint(event.clientX, event.clientY).matrixTransform(
      matrix,
    );
    return {
      x: Math.max(0, Math.min(1600, p.x)),
      y: Math.max(0, Math.min(1000, p.y)),
    };
  }
  const all = [
    ...marks,
    ...pending.filter(
      (m) => !marks.some((saved) => saved.operation_id === m.operation_id),
    ),
  ];
  const undone = new Set(
    all
      .filter((m) => m.kind === "undo" || m.kind === "erase")
      .map((m) => m.target),
  );
  const visible = all.filter(
    (m) =>
      m.kind !== "undo" &&
      m.kind !== "erase" &&
      m.kind !== "page" &&
      !undone.has(m.operation_id) &&
      (m.kind === "image"
        ? m.operation_id === selectedPage
        : (m.page_id || null) === selectedPage),
  );
  const lastOwn = [...visible]
    .reverse()
    .find((m) => m.author === board?.author);
  const pages = marks.filter((m) => m.kind === "image");
  const background = visible.find((m) => m.kind === "image");
  function changePage(value: string) {
    setClearConfirm(false);
    const page = value || null;
    setSelectedPage(page);
    setZoom(1);
    if (!board?.closed)
      enqueue({
        operation_id: crypto.randomUUID(),
        kind: "page",
        target: page || undefined,
      });
  }
  async function uploadPhoto(file: File, id: string) {
    if (!boardId) return false;
    if (file.size > 5 * 1024 * 1024) {
      setError("Choose a JPEG or PNG photo smaller than 5 MB.");
      return false;
    }
    uploadBusy.current = true;
    setUploading(true);
    setUploadFailed(false);
    setError("");
    uploadAttempt.current = { file, id };
    const form = new FormData();
    form.append("photo", file);
    form.append("operation_id", id);
    try {
      const result = await postForm<{ revision: number }>(
        `/together/boards/${boardId}/photos`,
        form,
      );
      while (revision.current < result.revision) {
        const batch = await api<Mark[]>(
          `/together/boards/${boardId}/operations?after=${revision.current}`,
        );
        if (!batch.length)
          throw new Error(
            "Waiting to synchronize the imported worksheet page. Retry the upload.",
          );
        ingest.current(batch);
      }
      uploadAttempt.current = null;
      setLastSavedAt(Date.now());
      return true;
    } catch (err) {
      setError((err as Error).message);
      setUploadFailed(true);
      return false;
    } finally {
      uploadBusy.current = false;
      setUploading(false);
    }
  }
  function eraseMark(event: React.PointerEvent, mark: Mark) {
    if (tool !== "erase") return;
    event.preventDefault();
    event.stopPropagation();
    if (mark.author !== board?.author) {
      setError(
        "The eraser removes your own marks. Ask the other person to edit theirs.",
      );
      return;
    }
    enqueue({
      operation_id: crypto.randomUUID(),
      kind: "erase",
      target: mark.operation_id,
    });
  }
  const disabled = !board || !ready || board.closed || clearing || pending.length >= 50;
  const canClear = !disabled && !clearing && !uploading
    && !queue.current.length && !inkID.current && !stroke.current.length;
  const ownVisibleCount = visible.filter(
    (m) => m.author === board?.author && (m.kind === "stroke" || m.kind === "text"),
  ).length;
  const pageIndex = selectedPage
    ? Math.max(0, pages.findIndex((p) => p.operation_id === selectedPage) + 1)
    : 0;

  function stepPage(direction: -1 | 1) {
    const next = pageIndex + direction;
    changePage(next === 0 ? "" : pages[next - 1].operation_id);
  }

  function toggleFullscreen() {
    if (document.fullscreenElement) {
      void document.exitFullscreen();
    } else {
      void viewport.current
        ?.requestFullscreen()
        .catch(() => setError("Full screen is not available in this browser."));
    }
  }

  async function clearMyWriting() {
    if (!boardId || !board || !canClear || ownVisibleCount === 0) return;
    const pageAtConfirmation = selectedPage;
    const expectedRevision = revision.current;
    const operationId = crypto.randomUUID();
    setClearing(true);
    setClearConfirm(false);
    setError("");
    try {
      const response = await post<{
        result_revision: number;
        cleared_count: number;
        page_id: string | null;
      }>(`/together/boards/${boardId}/clear-my-writing`, {
        operation_id: operationId,
        page_id: pageAtConfirmation,
        expected_revision: expectedRevision,
      });
      if (response.page_id !== pageAtConfirmation) {
        throw new Error("The board page changed during clearing. Refresh the board.");
      }
      // The endpoint writes durable erase events. Reconcile from the server's
      // revision stream, never hide strokes only in React/local state.
      let cursor = revision.current;
      while (cursor < response.result_revision) {
        const batch = await api<Mark[]>(
          `/together/boards/${boardId}/operations?after=${cursor}`,
        );
        if (!batch.length) throw new Error("Board changes are still synchronizing. Refresh.");
        ingest.current(batch);
        const next = Math.max(cursor, ...batch.map((mark) => mark.revision || 0));
        if (next === cursor) throw new Error("Board updates are not advancing. Refresh.");
        cursor = next;
      }
      setStatus(`Cleared ${response.cleared_count} of your marks on this page.`);
    } catch (err) {
      setError(err instanceof ApiError && err.status === 409
        ? "The board changed before your clear was applied. Review the page and try again."
        : err instanceof Error ? err.message : "Unable to clear writing. Try again.");
    } finally {
      setClearing(false);
    }
  }

  return (
    <>
      <NavBar />
      <main className="mx-auto max-w-[1800px] space-y-3 bg-slate-50/60 p-3 sm:p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-violet-950 sm:text-3xl">Learn Together</h1>
            <p className="text-xs text-slate-600 sm:text-sm">
              A private family whiteboard for homework and practice. Guided work does not earn independent mastery credit.
            </p>
          </div>
          {boardId && <div className="flex flex-wrap items-center gap-2">
            {lastSavedAt && (
              <span role="status" className="text-xs text-slate-500">
                {savedAgo(lastSavedAt, now)}
              </span>
            )}
            <div role="status" className="flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-800">
              <span aria-hidden="true" className="h-2 w-2 rounded-full bg-emerald-500" />
              {liveAvailable ? "Connected · autosaving" : status}
            </div>
          </div>}
        </div>
        {error && (
          <p role="alert" className="text-red-700">
            {error}
          </p>
        )}
        {!boardId ? (
          <>
            <h2 className="font-semibold">Start a board</h2>
            <div className="flex flex-wrap gap-2">
              {children.map((child) => (
                <button
                  className={button}
                  key={child.id}
                  onClick={async () => {
                    try {
                      const b = await post<Board>("/together/boards", {
                        student_id: child.id,
                      });
                      navigate(`/together/${b.id}`);
                    } catch (err) {
                      setError((err as Error).message);
                    }
                  }}
                >
                  Work with {child.first_name}
                </button>
              ))}
            </div>
            <button type="button" className={button}
              onClick={() => void refreshBoardList().catch(() => {})}>
              Refresh boards
            </button>
            <h2 className="font-semibold">Saved family boards</h2>
            {!boards.length && (
              <p>
                Your parent can start a board here. Sign in through your usual
                Mihur access to join.
              </p>
            )}
            <ul className="space-y-2">
              {boards.map((b, i) => (
                <li key={b.id}>
                  <Link className="underline" to={`/together/${b.id}`}>
                    {b.name || `Board ${boards.length - i}`}
                    {b.closed ? " · closed" : " · open"}
                  </Link>
                </li>
              ))}
            </ul>
            {trashedBoards.length > 0 && (
              <section aria-label="Board trash" className="rounded-xl border p-4 space-y-2">
                <h3 className="font-semibold">Trash — recoverable boards</h3>
                {trashedBoards.map((item) => <div key={item.id}
                  className="flex items-center justify-between gap-3">
                  <span>{item.name}</span>
                  <button type="button" className={button}
                    onClick={async () => {
                      try {
                        await post("/together/boards/" + item.id + "/restore", {});
                        await refreshBoardList();
                      } catch (err) {
                        setError(err instanceof Error ? err.message : "Restore failed.");
                      }
                    }}>Restore board</button>
                </div>)}
              </section>
            )}
          </>
        ) : (
          <>
            <div className="relative rounded-2xl border border-slate-200 bg-white p-2.5 shadow-sm sm:p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex min-w-0 flex-wrap items-center gap-2">
                <label className="sr-only" htmlFor="board-picker">Open board</label>
                <select id="board-picker" className={`${button} w-full max-w-80 font-semibold sm:w-auto`} value={boardId}
                  disabled={managingBoard || pending.length > 0}
                  onChange={(event) => navigate("/together/" + event.target.value)}>
                  {!boards.some((item) => item.id === boardId) &&
                    <option value={boardId}>{board?.name || "Current board"}</option>}
                  {boards.map((item) =>
                    <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
                {board?.author.startsWith("parent:") && (
                  <button type="button" className="inline-flex min-h-10 items-center rounded-xl bg-violet-700 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-violet-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-600 disabled:opacity-40"
                    disabled={managingBoard || pending.length > 0}
                    onClick={() => { setNewBoardOpen(true); setNewBoardChild(board.student_id); }}>
                    + New board
                  </button>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Link to="/together" className={button}>All boards</Link>
              <button
                type="button"
                className={button}
                disabled
                title="Sharing controls are coming soon"
              >
                Share
              </button>
              <button
                className={button}
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(location.href);
                    setShare(
                      "Link copied. Your child joins with their usual Mihur access.",
                    );
                  } catch {
                    setShare(location.href);
                  }
                }}
              >
                Copy link
              </button>
                {board?.author.startsWith("parent:") && (
                  <button type="button" className={button} aria-expanded={boardMenu}
                    onClick={() => setBoardMenu((value) => !value)}>
                    Board actions <span aria-hidden="true">▾</span>
                  </button>
                )}
              </div>
              </div>
              {boardMenu && board?.author.startsWith("parent:") && (
                <div className="absolute right-2 top-full z-30 mt-1 w-[min(21rem,calc(100vw-2rem))] space-y-2 rounded-2xl border border-slate-200 bg-white p-3 shadow-xl" role="group" aria-label="Board actions">
                <button type="button" className={`${button} w-full justify-start`}
                  onClick={() => { setBoardTitle(board.name); setBoardAction("rename"); setBoardMenu(false); }}>
                  Rename board
                </button>
                <button type="button" className={`${button} w-full justify-start`} disabled
                  title="Board duplication is coming soon">
                  Duplicate board
                </button>
                <button type="button" className={`${button} w-full justify-start`} disabled
                  title="Board folders are coming soon">
                  Move to folder…
                </button>
                <div className="border-t border-slate-200 pt-2 space-y-2">
                <button type="button" className={`${button} w-full justify-start border-red-100 bg-red-50 text-red-800`}
                  disabled={!canClear}
                  onClick={() => { setBoardActionPage(selectedPage); setBoardAction("clearpage"); setBoardMenu(false); }}>
                  <span className="text-left">
                    <span className="block font-medium">Clear page</span>
                    <span className="block text-xs opacity-80">Erase marks on this page.</span>
                  </span>
                </button>
                <button type="button" className={`${button} w-full justify-start border-red-100 bg-red-50 text-red-800`}
                  disabled={!canClear} onClick={() => { setBoardAction("clear"); setBoardMenu(false); }}>
                  <span className="text-left">
                    <span className="block font-medium">Clear board</span>
                    <span className="block text-xs opacity-80">Erase marks on all pages of this board.</span>
                  </span>
                </button>
                <button type="button" className={`${button} w-full justify-start border-red-200 bg-red-50 text-red-800`}
                  disabled={!canClear || !ready}
                  onClick={() => { setBoardAction("delete"); setBoardMenu(false); }}>
                  <span className="text-left">
                    <span className="block font-medium">Delete board</span>
                    <span className="block text-xs opacity-80">Remove this board from your account.</span>
                  </span>
                </button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Clearing removes all saved pen and text marks, including other participants' marks.
                  Imported worksheet pages stay. Deleted boards move to Trash for recovery.
                </p>
                <div className="border-t border-slate-200 pt-2">
              {board?.author.startsWith("parent:") && !board.closed && (
                <button
                  className={button}
                  disabled={pending.length > 0 || uploading}
                  onClick={async () => {
                    try {
                      setBoard(
                        await post<Board>(`/together/boards/${boardId}/close`),
                      );
                    } catch (err) {
                      setError((err as Error).message);
                    }
                  }}
                >
                  Close board
                </button>
              )}
                </div>
                </div>
              )}
            </div>
            <p className="flex items-center gap-2 rounded-xl border border-violet-100 bg-violet-50 px-3 py-2 text-xs text-violet-900">
              <span aria-hidden="true">✦</span>
              <span><strong>Family board</strong> · A shared space for parents and kids to learn, practice, and do homework together.</span>
            </p>
            {newBoardOpen && <section className="rounded-xl border bg-violet-50 p-4 space-y-3"
              aria-label="Create new family board">
              <h2 className="font-semibold">New board</h2>
              <label className="block">Choose learner
                <select className={button + " ml-2"} value={newBoardChild}
                  onChange={(event) => setNewBoardChild(event.target.value)}>
                  {children.map((child) => <option key={child.id} value={child.id}>{child.first_name}</option>)}
                </select>
              </label>
              <div className="flex gap-2">
                <button type="button" className={button} onClick={() => setNewBoardOpen(false)}>Cancel</button>
                <button type="button" className="rounded-lg bg-violet-700 px-4 py-2 text-white"
                  disabled={!newBoardChild || managingBoard}
                  onClick={() => void createNewBoard(newBoardChild)}>Create board</button>
              </div>
            </section>}
            {boardAction && <section className="rounded-xl border border-red-300 bg-red-50 p-4 space-y-3"
              role="group" aria-label="Confirm board action">
              <h2 className="font-semibold">
                {boardAction === "clear" ? "Clear every page?" :
                 boardAction === "clearpage" ? "Clear this page?" :
                 boardAction === "delete" ? "Move this board to Trash?" : "Rename this board"}
              </h2>
              {boardAction === "clear" && <p className="text-sm">
                All pen and text marks by every participant will be cleared across this board.
                Imported homework pages will remain. This bulk action cannot be undone.
              </p>}
              {boardAction === "clearpage" && <p className="text-sm">
                All pen and text marks by every participant will be cleared
                {boardActionPage ? " on the selected worksheet page" : " on the blank page"}.
                The imported page image and all other pages will remain. This bulk action cannot be undone.
              </p>}
              {boardAction === "delete" && <p className="text-sm">
                This board will disappear from family access but remain in the parent's Trash for restoration.
              </p>}
              {boardAction === "rename" && <label className="block">
                Board name <input className="ml-2 rounded border p-2" maxLength={100}
                  value={boardTitle} onChange={(event) => setBoardTitle(event.target.value)} />
              </label>}
              <div className="flex gap-2">
                <button type="button" className={button}
                  onClick={() => setBoardAction(null)}>Cancel</button>
                <button type="button" className="rounded-lg bg-red-700 px-4 py-2 font-semibold text-white disabled:opacity-40"
                  disabled={managingBoard || (boardAction === "rename" && !boardTitle.trim())}
                  onClick={() => void manageCurrentBoard()}>
                  {boardAction === "clear" ? "Clear all saved marks" :
                   boardAction === "clearpage" ? "Clear this page" :
                   boardAction === "delete" ? "Move board to Trash" : "Save name"}
                </button>
              </div>
            </section>}
            <div className="grid min-h-[65vh] items-start gap-3 lg:grid-cols-[250px_minmax(0,1fr)]">
              <aside className="min-w-0" aria-label="Page navigation">
            <nav aria-label="Board pages" className="space-y-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
              <div className="flex items-center justify-between gap-2">
                <h2 className="flex items-center gap-2 font-semibold">
                  Pages
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                    {pages.length + 1}
                  </span>
                </h2>
                <button type="button" aria-expanded={pagesOpen}
                  aria-label={pagesOpen ? "Collapse page list" : "Expand page list"}
                  onClick={() => setPagesOpen((value) => !value)}
                  className="rounded-lg p-1.5 text-slate-500 transition-colors hover:bg-slate-100">
                  {pagesOpen
                    ? <ChevronUp size={16} aria-hidden="true" />
                    : <ChevronDown size={16} aria-hidden="true" />}
                </button>
              </div>
              {pagesOpen && (<>
              <button type="button" disabled={disabled || uploading || pages.length >= 10}
                onClick={() => void newBlankPage()}
                className="w-full rounded-xl border border-dashed border-violet-300 bg-violet-50/60 px-3 py-2 text-sm font-medium text-violet-800 transition-colors hover:bg-violet-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-600 disabled:cursor-not-allowed disabled:opacity-40">
                + New page
              </button>
              <div className="flex gap-2 overflow-x-auto pb-2 lg:flex-col lg:overflow-visible">
                <button type="button" aria-current={selectedPage === null ? "page" : undefined}
                  className={"min-w-32 w-full rounded-xl border p-3 text-left " + (selectedPage === null ? "border-violet-700 bg-violet-50" : "bg-white")}
                  disabled={!ready || pending.length > 0} onClick={() => changePage("")}>
                  <span className="block text-xs text-muted-foreground">Base page</span>
                  <span className="font-medium">Blank page</span>
                </button>
                {pages.map((page, index) => (
                  <button key={page.operation_id} type="button"
                    aria-current={selectedPage === page.operation_id ? "page" : undefined}
                    className={"min-w-32 w-full rounded-xl border p-2 text-left lg:flex lg:items-center lg:gap-2 " +
                      (selectedPage === page.operation_id ? "border-violet-700 bg-violet-50" : "bg-white")}
                    disabled={!ready || pending.length > 0}
                    onClick={() => changePage(page.operation_id)}>
                    <img className="mb-1 h-14 w-20 shrink-0 rounded border object-contain lg:mb-0"
                      alt="" src={`/api/v1/together/boards/${boardId}/photos/${page.image_id}`} />
                    <span className="font-medium">Page {index + 1}</span>
                  </button>
                ))}
              </div>
              <details className="border-t border-slate-200 pt-2">
                <summary className="cursor-pointer text-sm font-medium">Page actions</summary>
                <div className="mt-2 space-y-2">
                  <button type="button" className={`${button} w-full justify-start`} disabled
                    title="Page duplication is coming soon">
                    Duplicate page
                  </button>
                  <button type="button" className={`${button} w-full justify-start`} disabled
                    title="Page deletion is coming soon">
                    Delete page
                  </button>
                  <p className="text-xs text-slate-500">
                    Page duplication and deletion are coming soon.
                  </p>
                </div>
              </details>
              </>)}
            </nav>
              </aside>
              <section className="min-w-0 space-y-3" aria-label="Whiteboard editor">
            <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm" role="toolbar" aria-label="Whiteboard drawing tools">
              <button
                className={`${button} ${tool === "pen" ? activeTool : ""}`}
                aria-pressed={tool === "pen"}
                onClick={() => setTool("pen")}
              >
                <Pen size={16} aria-hidden="true" /> Pen
              </button>
              <button type="button" className={`${button} ${tool === "erase" ? activeTool : ""}`}
                disabled={disabled} aria-label="Eraser (my marks)" aria-pressed={tool === "erase"}
                onClick={() => setTool("erase")}><Eraser size={16} aria-hidden="true" /> Eraser</button>
              <button
                className={`${button} ${tool === "text" ? activeTool : ""}`}
                aria-pressed={tool === "text"}
                onClick={() => setTool("text")}
              >
                <Type size={16} aria-hidden="true" /> Type
              </button>
              <button
                className={`${button} ${tool === "pointer" ? activeTool : ""}`}
                disabled={disabled || !liveAvailable}
                aria-pressed={tool === "pointer"}
                onClick={() => setTool("pointer")}
              >
                <MousePointer2 size={16} aria-hidden="true" /> Live pointer
              </button>
              <button type="button" className={`${button} ${tool === "pan" ? activeTool : ""}`}
                aria-pressed={tool === "pan"} aria-label="Move page" onClick={() => setTool("pan")}><Hand size={16} aria-hidden="true" /> Move</button>
              <span aria-hidden="true" className="mx-1 hidden h-7 w-px bg-slate-200 sm:block" />
              <button
                className={button}
                disabled={disabled || !lastOwn}
                aria-label="Undo my last mark"
                onClick={() =>
                  enqueue({
                    operation_id: crypto.randomUUID(),
                    kind: "undo",
                    target: lastOwn!.operation_id,
                  })
                }
              >
                <Undo2 size={16} aria-hidden="true" /> Undo
              </button>
              <button type="button" className={button} disabled
                aria-label="Redo" title="Redo is not yet available">
                <Redo2 size={16} aria-hidden="true" /> Redo
              </button>
              <span aria-hidden="true" className="mx-1 hidden h-7 w-px bg-slate-200 sm:block" />
              <button
                className={button}
                disabled={disabled || uploading}
                onClick={() => setShowPDF((value) => !value)}
              >
                <FileDown size={16} aria-hidden="true" /> Import PDF
              </button>
              <button type="button" className={button}
                disabled={disabled || uploading} onClick={() => photoInput.current?.click()}>
                <ImagePlus size={16} aria-hidden="true" /> Add homework photo
              </button>
              <input ref={photoInput} aria-label="Choose homework photo"
                className="sr-only" type="file" accept="image/jpeg,image/png"
                disabled={disabled || uploading}
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) void uploadPhoto(file, crypto.randomUUID());
                  event.target.value = "";
                }} />
            </div>

            <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
              <label className="sr-only">
                Worksheet page{" "}
                <select
                  aria-label="Worksheet page"
                  className={button}
                  disabled={!ready || uploading || pending.length > 0}
                  value={selectedPage || ""}
                  onChange={(event) => changePage(event.target.value)}
                >
                  <option value="">Blank page</option>
                  {pages.map((page, index) => (
                    <option key={page.operation_id} value={page.operation_id}>
                      Page {index + 1}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                className={button}
                disabled={!canClear || ownVisibleCount === 0}
                onClick={() => setClearConfirm(true)}
              >
                Clear My Writing
              </button>
            </div>
            {clearConfirm && (
              <div
                role="group"
                aria-labelledby="clear-my-writing-title"
                aria-describedby="clear-my-writing-description"
                className="rounded-xl border border-amber-300 bg-amber-50 p-4 space-y-3 text-slate-900"
              >
                <h2 id="clear-my-writing-title" className="font-semibold">
                  Clear your writing on this page?
                </h2>
                <p id="clear-my-writing-description" className="text-sm">
                  This removes {ownVisibleCount} of your saved text and pen marks
                  {selectedPage ? " on the selected worksheet page" : " on the blank page"}.
                  The other person's writing, worksheet pages and imported images stay.
                  You cannot undo this batch from this control.
                </p>
                <div className="flex flex-wrap gap-2">
                  <button type="button" className={button} onClick={() => setClearConfirm(false)}>
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="rounded-lg bg-red-700 px-4 py-2 font-semibold text-white disabled:opacity-40"
                    disabled={!canClear || ownVisibleCount === 0}
                    onClick={() => void clearMyWriting()}
                  >
                    Clear {ownVisibleCount} of my marks
                  </button>
                </div>
              </div>
            )}
            {showPDF && (
              <Suspense fallback={<p role="status">Loading PDF importer…</p>}>
                <PDFImport
                  disabled={disabled || uploading}
                  onImport={(file) => uploadPhoto(file, crypto.randomUUID())}
                />
              </Suspense>
            )}
            {uploading && <p role="status">Uploading worksheet page…</p>}
            {uploadFailed && uploadAttempt.current && (
              <button
                className={button}
                disabled={uploading}
                onClick={() => {
                  const attempt = uploadAttempt.current;
                  if (attempt) void uploadPhoto(attempt.file, attempt.id);
                }}
              >
                Retry photo upload
              </button>
            )}
            {share && <p role="status">{share}</p>}
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600" role="status">
              <span>{status}{pending.length ? ` · ${pending.length} marks waiting to save` : ""}</span>
              <span>{liveAvailable ? "Live pointer and handwriting connected" : "Live previews unavailable; finished marks still save"}</span>
            </div>
            {tool === "pointer" && (
              <p className="text-sm">
                Move or tap the board to point. Keyboard: focus the board and
                use arrow keys; Escape hides the pointer.
              </p>
            )}
            {tool === "text" && (
              <label className="block">
                Text or math (for example: 2x + 3 = 11)
                <input
                  className="block w-full border rounded p-2"
                  maxLength={1000}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Type, then tap the board to place"
                />
              </label>
            )}
            {tool === "text" && (
              <button
                className={button}
                disabled={disabled || !text.trim()}
                onClick={() => {
                  enqueue({
                    operation_id: crypto.randomUUID(),
                    kind: "text",
                    text,
                    x: 40,
                    y: Math.min(
                      960,
                      60 + visible.filter((m) => m.kind === "text").length * 40,
                    ),
                  });
                  setText("");
                }}
              >
                Add text to board
              </button>
            )}
            <div
              ref={viewport}
              className="overflow-auto rounded-2xl border border-slate-200 bg-white shadow-sm"
              tabIndex={0}
              role="region"
              aria-label="Whiteboard viewport"
              style={{ height: "min(74vh, 780px)", minHeight: "430px" }}
              onPointerDown={(event) => {
                if (tool !== "pan" || event.pointerType !== "mouse") return;
                event.preventDefault();
                event.currentTarget.setPointerCapture(event.pointerId);
                panStart.current = {
                  id: event.pointerId,
                  x: event.clientX,
                  y: event.clientY,
                  left: event.currentTarget.scrollLeft,
                  top: event.currentTarget.scrollTop,
                };
              }}
              onPointerMove={(event) => {
                const start = panStart.current;
                if (!start || start.id !== event.pointerId) return;
                event.currentTarget.scrollLeft =
                  start.left - (event.clientX - start.x);
                event.currentTarget.scrollTop =
                  start.top - (event.clientY - start.y);
              }}
              onPointerUp={() => {
                panStart.current = null;
              }}
              onPointerCancel={() => {
                panStart.current = null;
              }}
            >
              <svg
                ref={svg}
                viewBox="0 0 1600 1000"
                className="block"
                width={`${zoom * 100}%`}
                style={{
                  minWidth: 600,
                  touchAction: tool === "pen" ? "none" : "auto",
                }}
                tabIndex={tool === "pointer" ? 0 : undefined}
                onKeyDown={(event) => {
                  if (tool !== "pointer" || disabled) return;
                  if (event.key === "Escape") {
                    pointerVisible.current = false;
                    paintDraft();
                    sendLive({ kind: "clear" }, true);
                    return;
                  }
                  const delta: Record<string, Point> = {
                    ArrowLeft: { x: -15, y: 0 },
                    ArrowRight: { x: 15, y: 0 },
                    ArrowUp: { x: 0, y: -15 },
                    ArrowDown: { x: 0, y: 15 },
                  };
                  if (!delta[event.key]) return;
                  event.preventDefault();
                  const d = delta[event.key];
                  localPointer.current = {
                    x: Math.max(
                      0,
                      Math.min(1600, localPointer.current.x + d.x),
                    ),
                    y: Math.max(
                      0,
                      Math.min(1000, localPointer.current.y + d.y),
                    ),
                  };
                  pointerVisible.current = true;
                  paintDraft();
                  sendLive(
                    {
                      kind: "pointer",
                      page_id: selectedPage,
                      point: localPointer.current,
                    },
                    true,
                  );
                }}
                onPointerLeave={() => {
                  if (tool === "pointer") {
                    pointerVisible.current = false;
                    paintDraft();
                    sendLive({ kind: "clear" }, true);
                  }
                }}
                role="img"
                aria-label="Shared family whiteboard. Use Type to add text, or Pen to draw."
                onPointerDown={(e) => {
                  if (
                    disabled ||
                    pointer.current !== null ||
                    tool === "erase" ||
                    tool === "pan"
                  )
                    return;
                  if (tool === "pointer") {
                    localPointer.current = point(e);
                    pointerVisible.current = true;
                    paintDraft();
                    sendLive(
                      {
                        kind: "pointer",
                        page_id: selectedPage,
                        point: localPointer.current,
                      },
                      true,
                    );
                    return;
                  }
                  if (tool === "text") {
                    if (text.trim()) {
                      enqueue({
                        operation_id: crypto.randomUUID(),
                        kind: "text",
                        text,
                        ...point(e),
                      });
                      setText("");
                    }
                    return;
                  }
                  e.preventDefault();
                  e.currentTarget.setPointerCapture(e.pointerId);
                  pointer.current = e.pointerId;
                  inkPage.current = selectedPage;
                  inkID.current = crypto.randomUUID();
                  stroke.current = [point(e)];
                  paintDraft();
                  sendLive(
                    {
                      kind: "stroke",
                      page_id: selectedPage,
                      operation_id: inkID.current,
                      points: previewPoints(stroke.current),
                    },
                    true,
                  );
                }}
                onPointerMove={(e) => {
                  if (tool === "pointer" && !disabled) {
                    localPointer.current = point(e);
                    pointerVisible.current = true;
                    paintDraft();
                    sendLive({
                      kind: "pointer",
                      page_id: selectedPage,
                      point: localPointer.current,
                    });
                    return;
                  }
                  if (
                    pointer.current !== e.pointerId ||
                    stroke.current.length >= 4000
                  )
                    return;
                  const samples = e.nativeEvent.getCoalescedEvents?.() || [];
                  for (const sample of samples.length
                    ? samples
                    : [e.nativeEvent]) {
                    if (stroke.current.length >= 4000) break;
                    const p = point(sample),
                      previous = stroke.current[stroke.current.length - 1];
                    if (Math.hypot(p.x - previous.x, p.y - previous.y) >= 0.35)
                      stroke.current.push(p);
                  }
                  paintDraft();
                  if (inkID.current)
                    sendLive({
                      kind: "stroke",
                      page_id: selectedPage,
                      operation_id: inkID.current,
                      points: previewPoints(stroke.current),
                    });
                }}
                onPointerUp={(e) => {
                  if (pointer.current !== e.pointerId) return;
                  enqueue({
                    operation_id: inkID.current || crypto.randomUUID(),
                    kind: "stroke",
                    points: stroke.current,
                  });
                  if (inkID.current)
                    sendLive(
                      {
                        kind: "stroke",
                        page_id: selectedPage,
                        operation_id: inkID.current,
                        points: previewPoints(stroke.current),
                      },
                      true,
                    );
                  inkID.current = null;
                  pointer.current = null;
                  stroke.current = [];
                  setDraft([]);
                }}
                onPointerCancel={() => {
                  sendLive({ kind: "clear" }, true);
                  inkID.current = null;
                  pointer.current = null;
                  stroke.current = [];
                  setDraft([]);
                }}
              >
                <defs>
                  <pattern
                    id="grid"
                    width="40"
                    height="40"
                    patternUnits="userSpaceOnUse"
                  >
                    <path
                      d="M 40 0 L 0 0 0 40"
                      fill="none"
                      stroke="#e2e8f0"
                      strokeWidth="1"
                    />
                  </pattern>
                </defs>
                <rect width="1600" height="1000" fill="url(#grid)" />
                {background && (
                  <image
                    data-testid="homework-photo"
                    href={`/api/v1/together/boards/${boardId}/photos/${background.image_id}`}
                    x="0"
                    y="0"
                    width="1600"
                    height="1000"
                    preserveAspectRatio="xMidYMid meet"
                    onPointerDown={(event) => eraseMark(event, background)}
                  />
                )}
                {visible
                  .filter((m) => m.kind !== "image")
                  .map((m) => (
                    <g
                      key={m.operation_id}
                      onPointerDown={(event) => eraseMark(event, m)}
                      style={{
                        cursor: tool === "erase" ? "crosshair" : undefined,
                      }}
                    >
                      {m.kind === "stroke" ? (
                        m.points?.length === 1 ? (
                          <circle
                            cx={m.points[0].x}
                            cy={m.points[0].y}
                            r="2"
                            fill={color(m.author)}
                          />
                        ) : (
                          <path
                            data-testid="saved-stroke"
                            data-operation-id={m.operation_id}
                            d={inkPath(m.points || [])}
                            fill="none"
                            stroke={color(m.author)}
                            strokeWidth="4"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        )
                      ) : (
                        <text
                          x={m.x}
                          y={m.y}
                          fill={color(m.author)}
                          fontSize="28"
                        >
                          {m.text}
                        </text>
                      )}
                    </g>
                  ))}
                {pointerPosition && (
                  <circle
                    data-testid="local-pointer"
                    cx={pointerPosition.x}
                    cy={pointerPosition.y}
                    r="12"
                    fill={color(board?.author)}
                    fillOpacity="0.25"
                    stroke={color(board?.author)}
                    strokeWidth="3"
                    pointerEvents="none"
                  />
                )}
                {Object.values(peers)
                  .filter((frame) => (frame.page_id || null) === selectedPage)
                  .map((frame) =>
                    frame.kind === "stroke" ? (
                      <path
                        key={frame.source}
                        data-testid="live-stroke"
                        data-operation-id={frame.operation_id}
                        d={inkPath(frame.points || [])}
                        fill="none"
                        stroke={color(frame.author)}
                        strokeWidth="4"
                        strokeLinecap="round"
                        pointerEvents="none"
                      />
                    ) : frame.point ? (
                      <g
                        key={frame.source}
                        data-testid="live-pointer"
                        pointerEvents="none"
                      >
                        <circle
                          cx={frame.point.x}
                          cy={frame.point.y}
                          r="12"
                          fill={color(frame.author)}
                          fillOpacity="0.25"
                          stroke={color(frame.author)}
                          strokeWidth="3"
                        />
                        <text
                          x={Math.min(frame.point.x + 18, 1470)}
                          y={Math.max(24, frame.point.y - 15)}
                          fill={color(frame.author)}
                          fontSize="24"
                        >
                          {frame.author?.startsWith("parent:")
                            ? "Parent"
                            : "Child"}
                        </text>
                      </g>
                    ) : null,
                  )}
                <path
                  d={inkPath(draft)}
                  fill="none"
                  stroke={color(board?.author)}
                  strokeWidth="4"
                  strokeLinecap="round"
                />
              </svg>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
              <div className="flex items-center gap-2" role="navigation" aria-label="Page position">
                <button
                  type="button"
                  className={button}
                  aria-label="Previous page"
                  disabled={pageIndex <= 0 || !ready || pending.length > 0}
                  onClick={() => stepPage(-1)}
                >
                  <ChevronLeft size={16} aria-hidden="true" />
                </button>
                <span aria-live="polite" className="min-w-24 text-center text-sm">
                  Page {pageIndex + 1} of {pages.length + 1}
                </span>
                <button
                  type="button"
                  className={button}
                  aria-label="Next page"
                  disabled={pageIndex >= pages.length || !ready || pending.length > 0}
                  onClick={() => stepPage(1)}
                >
                  <ChevronRight size={16} aria-hidden="true" />
                </button>
              </div>
              <div className="flex items-center gap-2">
                <button
                  className={button}
                  aria-label="Zoom out"
                  disabled={zoom <= 1}
                  onClick={() => setZoom((value) => Math.max(1, value - 0.5))}
                >
                  −
                </button>
                <span aria-live="polite" className="min-w-12 text-center text-sm">
                  {Math.round(zoom * 100)}%
                </span>
                <button
                  className={button}
                  aria-label="Zoom in"
                  disabled={zoom >= 3}
                  onClick={() => setZoom((value) => Math.min(3, value + 0.5))}
                >
                  +
                </button>
                <button className={button} onClick={() => setZoom(1)}>
                  Fit page
                </button>
                <button
                  type="button"
                  className={button}
                  aria-label={fullscreen ? "Exit full screen" : "Full screen"}
                  onClick={toggleFullscreen}
                >
                  {fullscreen
                    ? <Minimize size={16} aria-hidden="true" />
                    : <Maximize size={16} aria-hidden="true" />}
                </button>
              </div>
            </div>
            <details className="text-xs text-slate-600">
              <summary className="cursor-pointer">Supported worksheet files and privacy</summary>
              Photos are private to this board. JPEG/PNG up to 5 MB; PDF imports one page at a time.
            </details>
            <details className="text-xs text-slate-600">
              <summary className="cursor-pointer">Board controls and participant colors</summary>
              Parent marks are purple; child marks are blue. Scroll outside the board to move the page. Rotate your device for more writing space.
            </details>
            <details>
              <summary>Written work (accessible text)</summary>
              <ul>
                {visible.map((m) => (
                  <li key={m.operation_id}>
                    {m.author?.startsWith("parent:") ? "Parent" : "Child"}:{" "}
                    {m.kind === "text"
                      ? m.text
                      : m.kind === "image"
                        ? "Homework photo"
                        : "Handwritten mark"}
                    {m.author === board?.author && (
                      <button
                        className={`${button} ml-2`}
                        disabled={disabled}
                        onClick={() =>
                          enqueue({
                            operation_id: crypto.randomUUID(),
                            kind: "erase",
                            target: m.operation_id,
                          })
                        }
                      >
                        Erase this mark
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            </details>
            <p className="text-xs text-slate-600">
              Before leaving, confirm that all marks have saved. Use your usual calling app for conversation.
            </p>
              </section>
            </div>
          </>
        )}
      </main>
    </>
  );
}
