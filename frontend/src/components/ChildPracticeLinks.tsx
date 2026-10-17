import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Child = { id: string; first_name: string; grade_level: string };
type PassSummary = { student_id: string; expires_at: string; created_at: string };
type IssuedPass = { student_id: string; expires_at: string; url: string };
const privatePath = /^\/practice\/[A-Za-z0-9_-]{32,256}$/;

function privateParentHeaders(): HeadersInit {
  const token = sessionStorage.getItem("parentUnlock");
  return {
    "Content-Type": "application/json",
    ...(token ? { "X-Parent-Unlock": token } : {}),
  };
}

function displayExpiry(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Unknown expiry" : date.toLocaleString();
}

export default function ChildPracticeLinks({ children }: { children: Child[] }) {
  const [passes, setPasses] = useState<PassSummary[] | null>(null);
  const [issued, setIssued] = useState<{ childId: string; url: string; expiresAt: string } | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function refresh() {
    const data = await api<{ passes: PassSummary[] }>("/practice-pass");
    if (!Array.isArray(data.passes) ||
        data.passes.some((p) => !children.some((child) => child.id === p.student_id))) {
      throw new Error("The practice-link response did not match this family.");
    }
    setPasses(data.passes);
  }

  useEffect(() => {
    let active = true;
    api<{ passes: PassSummary[] }>("/practice-pass")
      .then((data) => {
        if (!active) return;
        if (!Array.isArray(data.passes) ||
            data.passes.some((p) => !children.some((child) => child.id === p.student_id))) {
          throw new Error("Unrecognized practice-link data");
        }
        setPasses(data.passes);
      })
      .catch(() => {
        if (active) {
          setPasses(null);
          setError("Practice links are unavailable. Ask the Mihur pilot team for help.");
        }
      });
    return () => { active = false; };
  }, [children]);

  async function generate(child: Child, regenerating: boolean) {
    if (busy || !children.some((c) => c.id === child.id)) return;
    if (regenerating && !window.confirm(
      `Replace the link for ${child.first_name}? Their existing link and any practice sessions issued by it will stop working.`,
    )) return;
    setBusy(child.id);
    setError("");
    setNotice("");
    setIssued(null);
    try {
      const pass = await api<IssuedPass>("/practice-pass", {
        method: "POST",
        headers: privateParentHeaders(),
        body: JSON.stringify({ student_id: child.id }),
      });
      if (pass.student_id !== child.id || !privatePath.test(pass.url)) {
        throw new Error("Unexpected child identity or link format");
      }
      setIssued({
        childId: child.id,
        url: new URL(pass.url, window.location.origin).toString(),
        expiresAt: pass.expires_at,
      });
      await refresh();
      setNotice(`A new private link for ${child.first_name} was created. Copy it now; Mihur will not show it again.`);
    } catch {
      setIssued(null);
      setError("Could not create a practice link. Verify your parent PIN and try again.");
    } finally {
      setBusy(null);
    }
  }

  async function revoke(child: Child) {
    if (busy || !children.some((c) => c.id === child.id)) return;
    if (!window.confirm(`Revoke the link for ${child.first_name}? Their current link sessions will end.`)) return;
    setBusy(child.id);
    setError("");
    setNotice("");
    setIssued(null);
    try {
      await api<void>(`/practice-pass?student_id=${encodeURIComponent(child.id)}`, {
        method: "DELETE",
        headers: privateParentHeaders(),
      });
      await refresh();
      setNotice(`The link for ${child.first_name} was revoked. Other children's links were not changed.`);
    } catch (err) {
      setError(err instanceof ApiError && err.status === 403
        ? "Please unlock parent settings again before changing links."
        : "Could not revoke the link. Please try again.");
    } finally {
      setBusy(null);
    }
  }

  async function copyLink() {
    if (!issued) return;
    try {
      await navigator.clipboard.writeText(issued.url);
      setNotice("Link copied. Share it privately with this child's device.");
    } catch {
      setError("Copy was blocked by your browser. Select the link and copy it manually.");
    }
  }

  return (
    <Card id="child-practice-links">
      <CardHeader>
        <CardTitle role="heading" aria-level={2}>Private practice links for each child</CardTitle>
        <CardDescription>
          Each child gets a different link and can practice without a password. Generate a new
          link to replace that child's previous link. Links expire after seven days; a child
          already signed in stays active until their learner session expires or is revoked.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!children.length && <p className="text-sm text-muted-foreground">
          Add a learner from Practice, then return here to create their private link.
        </p>}
        {children.length > 0 && passes === null && !error && (
          <p role="status">Loading child practice links…</p>
        )}
        {passes !== null && children.map((child) => {
          const pass = passes.find((p) => p.student_id === child.id);
          const isBusy = busy !== null;
          return (
            <div key={child.id} className="space-y-3 rounded-lg border p-4">
              <div>
                <h3 className="font-semibold">{child.first_name}</h3>
                <p className="text-sm text-muted-foreground">Grade {child.grade_level}</p>
                <p className="text-sm text-muted-foreground">
                  {pass ? `Link active until ${displayExpiry(pass.expires_at)}` : "No active link"}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button type="button" disabled={isBusy} onClick={() => generate(child, Boolean(pass))}>
                  {busy === child.id ? "Working…" : pass ? "Regenerate link" : "Generate link"}
                </Button>
                {pass && <Button type="button" variant="secondary" disabled={isBusy} onClick={() => revoke(child)}>
                  Revoke link
                </Button>}
              </div>
              {issued?.childId === child.id && (
                <div className="space-y-2 rounded-md bg-secondary/50 p-3">
                  <Label htmlFor={`practice-link-${child.id}`}>New link for {child.first_name} — shown once</Label>
                  <Input id={`practice-link-${child.id}`} readOnly autoComplete="off" value={issued.url} />
                  <Button type="button" variant="secondary" onClick={copyLink}>Copy private link</Button>
                  <p className="text-xs text-muted-foreground">
                    Expires {displayExpiry(issued.expiresAt)}. Anyone with this link could open
                    this child's practice area. Send it privately; do not post publicly.
                  </p>
                </div>
              )}
            </div>
          );
        })}
        {notice && <p role="status" className="text-sm text-primary">{notice}</p>}
        {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      </CardContent>
    </Card>
  );
}
