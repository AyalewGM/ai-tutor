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
  // Auth endpoints legitimately return 401 (bad credentials) — let callers
  // surface the real error instead of redirecting back to /login in a loop.
  if (response.status === 401 && !path.startsWith("/auth/") && !path.startsWith("/practice-pass/")) {
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.assign(`/login?next=${next}`);
    throw new ApiError(401, "Authentication required");
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    /* no JSON body */
  }
  if (!response.ok) {
    const rawDetail = (body as { detail?: unknown } | null)?.detail;
    // Pilot approval gate: any family-only route bounces a pending or
    // rejected family to the status page instead of showing a raw error.
    if (
      response.status === 403 &&
      (rawDetail === "FAMILY_PENDING_APPROVAL" || rawDetail === "FAMILY_REJECTED") &&
      window.location.pathname !== "/pending"
    ) {
      window.location.assign("/pending");
      throw new ApiError(403, rawDetail);
    }
    // Region restriction: the API blocked this request by country.
    if (
      response.status === 403 &&
      rawDetail === "REGION_NOT_SUPPORTED" &&
      window.location.pathname !== "/unavailable"
    ) {
      window.location.assign("/unavailable");
      throw new ApiError(403, rawDetail);
    }
    const detail =
      typeof rawDetail === "string"
        ? rawDetail
        : rawDetail && typeof rawDetail === "object" && "message" in rawDetail
          ? String((rawDetail as { message: unknown }).message)
          : `${response.status} ${response.statusText}`;
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

export function postForm<T>(path: string, form: FormData): Promise<T> {
  return api<T>(path, { method: "POST", body: form });
}
