import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError, post } from "../api";
import NavBar from "../components/NavBar";

type Point = { x: number; y: number };
type Mark = {
  operation_id: string;
  kind: "stroke" | "text" | "undo";
  points?: Point[];
  text?: string;
  x?: number;
  y?: number;
  target?: string;
  author?: string;
  revision?: number;
};
type Board = {
  id: string;
  student_id: string;
  author: string;
  closed: boolean;
};
const color = (author?: string) =>
  author?.startsWith("parent:") ? "#6d28d9" : "#0369a1";
const button =
  "rounded-lg border px-3 py-2 disabled:opacity-40 bg-white text-slate-900";

export default function LearnTogether() {
  const { boardId } = useParams();
  const navigate = useNavigate();
  const [boards, setBoards] = useState<Board[]>([]);
  const [children, setChildren] = useState<
    { id: string; first_name: string }[]
  >([]);
  const [board, setBoard] = useState<Board | null>(null);
  const [marks, setMarks] = useState<Mark[]>([]);
  const [pending, setPending] = useState<Mark[]>([]);
  const [draft, setDraft] = useState<Point[]>([]);
  const [tool, setTool] = useState<"pen" | "text">("pen");
  const [text, setText] = useState("");
  const [status, setStatus] = useState("Connecting…");
  const [error, setError] = useState("");
  const [share, setShare] = useState("");
  const svg = useRef<SVGSVGElement>(null);
  const pointer = useRef<number | null>(null);
  const stroke = useRef<Point[]>([]);
  const queue = useRef<Mark[]>([]);
  const revision = useRef(0);
  const author = useRef("");

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
    let disposed = false;
    let socket: WebSocket | undefined;
    let reconnect: ReturnType<typeof setTimeout>;
    let retry: ReturnType<typeof setTimeout>;
    let sending = false;
    setError("");
    setBoard(null);
    setMarks([]);
    setDraft([]);
    setPending([]);
    queue.current = [];
    revision.current = 0;
    function merge(batch: Mark[]) {
      if (disposed || !batch.length) return;
      revision.current = Math.max(
        revision.current,
        ...batch.map((m) => m.revision || 0),
      );
      const ids = new Set(batch.map((m) => m.operation_id));
      queue.current = queue.current.filter((m) => !ids.has(m.operation_id));
      persistQueue();
      setPending([...queue.current]);
      setMarks((old) =>
        [...old.filter((m) => !ids.has(m.operation_id)), ...batch].sort(
          (a, b) => (a.revision || 0) - (b.revision || 0),
        ),
      );
    }
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
      socket.onopen = () => {
        if (!disposed) setStatus("Connected · work saves automatically");
      };
      socket.onmessage = (event) => {
        if (disposed) return;
        const data = JSON.parse(event.data);
        merge(data.operations);
        if (data.closed) {
          setBoard((old) => old && { ...old, closed: true });
          setStatus("Board closed · saved work is available");
        }
      };
      socket.onclose = (event) => {
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
      if (queue.current.length) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    const guardNavigation = (event: MouseEvent) => {
      if (
        queue.current.length &&
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
      socket?.close();
      clearTimeout(reconnect);
      clearTimeout(retry);
      window.removeEventListener("beforeunload", beforeUnload);
      document.removeEventListener("click", guardNavigation, true);
    };
  }, [boardId]);

  function enqueue(mark: Mark) {
    if (!board || board.closed || queue.current.length >= 50) return;
    queue.current.push({ ...mark, author: author.current });
    persistQueue();
    setPending([...queue.current]);
  }
  function point(event: React.PointerEvent): Point {
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
    all.filter((m) => m.kind === "undo").map((m) => m.target),
  );
  const visible = all.filter(
    (m) => m.kind !== "undo" && !undone.has(m.operation_id),
  );
  const lastOwn = [...visible]
    .reverse()
    .find((m) => m.author === board?.author);
  const disabled = !board || board.closed || pending.length >= 50;

  return (
    <>
      <NavBar />
      <main className="mx-auto max-w-6xl p-4 space-y-4">
        <h1 className="text-2xl font-bold">Learn Together</h1>
        <p className="text-sm text-muted-foreground">
          A private family whiteboard. Work here is guided practice and does not
          earn independent mastery credit.
        </p>
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
                    Board {boards.length - i}
                    {b.closed ? " · closed" : " · open"}
                  </Link>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <>
            <div className="flex flex-wrap gap-2 items-center">
              <button
                className={button}
                aria-pressed={tool === "pen"}
                onClick={() => setTool("pen")}
              >
                Pen
              </button>
              <button
                className={button}
                aria-pressed={tool === "text"}
                onClick={() => setTool("text")}
              >
                Type
              </button>
              <button
                className={button}
                disabled={disabled || !lastOwn}
                onClick={() =>
                  enqueue({
                    operation_id: crypto.randomUUID(),
                    kind: "undo",
                    target: lastOwn!.operation_id,
                  })
                }
              >
                Undo my last mark
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
                Copy board link
              </button>
              {board?.author.startsWith("parent:") && !board.closed && (
                <button
                  className={button}
                  disabled={pending.length > 0}
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
            {share && <p role="status">{share}</p>}
            <p role="status" className="text-sm">
              {status}
              {pending.length
                ? ` · ${pending.length} marks waiting to save`
                : ""}
            </p>
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
            <p className="text-sm">
              Parent: purple · Child: blue. Scroll outside the board to move the
              page. Rotate your device for more writing space.
            </p>
            <div className="overflow-auto rounded-xl border bg-white">
              <svg
                ref={svg}
                viewBox="0 0 1600 1000"
                className="w-full"
                style={{
                  minWidth: 600,
                  touchAction: tool === "pen" ? "none" : "auto",
                }}
                role="img"
                aria-label="Shared family whiteboard. Use Type to add text, or Pen to draw."
                onPointerDown={(e) => {
                  if (disabled || pointer.current !== null) return;
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
                  stroke.current = [point(e)];
                  setDraft([...stroke.current]);
                }}
                onPointerMove={(e) => {
                  if (
                    pointer.current !== e.pointerId ||
                    stroke.current.length >= 4000
                  )
                    return;
                  stroke.current.push(point(e));
                  setDraft([...stroke.current]);
                }}
                onPointerUp={(e) => {
                  if (pointer.current !== e.pointerId) return;
                  enqueue({
                    operation_id: crypto.randomUUID(),
                    kind: "stroke",
                    points: stroke.current,
                  });
                  pointer.current = null;
                  stroke.current = [];
                  setDraft([]);
                }}
                onPointerCancel={() => {
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
                {visible.map((m) =>
                  m.kind === "stroke" ? (
                    m.points?.length === 1 ? (
                      <circle
                        key={m.operation_id}
                        cx={m.points[0].x}
                        cy={m.points[0].y}
                        r="2"
                        fill={color(m.author)}
                      />
                    ) : (
                      <polyline
                        key={m.operation_id}
                        points={m.points?.map((p) => `${p.x},${p.y}`).join(" ")}
                        fill="none"
                        stroke={color(m.author)}
                        strokeWidth="4"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    )
                  ) : (
                    <text
                      key={m.operation_id}
                      x={m.x}
                      y={m.y}
                      fill={color(m.author)}
                      fontSize="28"
                    >
                      {m.text}
                    </text>
                  ),
                )}
                <polyline
                  points={draft.map((p) => `${p.x},${p.y}`).join(" ")}
                  fill="none"
                  stroke={color(board?.author)}
                  strokeWidth="4"
                  strokeLinecap="round"
                />
              </svg>
            </div>
            <details>
              <summary>Written work (accessible text)</summary>
              <ul>
                {visible.map((m) => (
                  <li key={m.operation_id}>
                    {m.author?.startsWith("parent:") ? "Parent" : "Child"}:{" "}
                    {m.kind === "text" ? m.text : "Handwritten mark"}
                  </li>
                ))}
              </ul>
            </details>
            <p className="text-sm">
              Before leaving, wait until all marks are saved. For conversation,
              use your usual voice calling app.
            </p>
          </>
        )}
      </main>
    </>
  );
}
