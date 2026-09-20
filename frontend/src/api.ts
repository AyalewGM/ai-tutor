const API = "/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    credentials: "same-origin",
    ...options,
  });
  if (response.status === 401) {
    const next = encodeURIComponent(window.location.pathname);
    window.location.assign(`/app/login?next=${next}`);
    throw new ApiError(401, "Authentication required");
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    /* no JSON body */
  }
  if (!response.ok) {
    const detail =
      (body as { detail?: string } | null)?.detail ??
      `${response.status} ${response.statusText}`;
    throw new ApiError(response.status, detail);
  }
  return body as T;
}

export function post<T>(path: string, payload?: unknown): Promise<T> {
  return api<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload === undefined ? undefined : JSON.stringify(payload),
  });
}
