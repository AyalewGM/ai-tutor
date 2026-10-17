export function isCurrentWorkspaceResponse(
  requestedSessionId: string | undefined,
  currentSessionId: string | undefined,
  payloadSessionId: string | undefined,
): boolean {
  return (
    typeof requestedSessionId === "string" &&
    requestedSessionId.length > 0 &&
    requestedSessionId === currentSessionId &&
    payloadSessionId === requestedSessionId
  );
}

export function isCurrentSessionResponse(
  requestedSessionId: string | undefined,
  currentSessionId: string | undefined,
): boolean {
  return (
    typeof requestedSessionId === "string" &&
    requestedSessionId.length > 0 &&
    requestedSessionId === currentSessionId
  );
}
