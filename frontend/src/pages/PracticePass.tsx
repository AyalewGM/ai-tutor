import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, ApiError, post } from "../api";
import Brand from "../components/Brand";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type Activated = { student_id: string; nickname: string | null };
type Learner = { id: string };
const tokenPattern = /^[A-Za-z0-9_-]{32,256}$/;

function initialToken(urlToken: string | undefined): string {
  // index.html captures the private URL and removes it from browser history
  // before loading scripts, styles, icons or other resources.
  const browser = window as Window & { __mihurPracticeToken?: string };
  const token = browser.__mihurPracticeToken ?? urlToken ?? "";
  // A client-side transition to an old-style URL still removes the token.
  if (urlToken) window.history.replaceState(window.history.state, "", "/practice/claim");
  return tokenPattern.test(token) ? token : "";
}

export default function PracticePass() {
  const { token: urlToken } = useParams();
  const [token] = useState(() => initialToken(urlToken));
  const [error, setError] = useState(token ? "" : "This practice link is invalid or has already been used on this page.");
  const [inUse, setInUse] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const activation = useRef<Promise<void> | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) return;
    // Reuse one activation request across React StrictMode's effect remount.
    if (!activation.current) {
      activation.current = (async () => {
        const result = await post<Activated>("/practice-pass/activate", { token });
        // Fail closed if the activated browser identity is not exactly one
        // learner matching the server-returned child ID.
        const learners = await api<Learner[]>("/onboarding/learners");
        if (!Array.isArray(learners) || learners.length !== 1 || learners[0].id !== result.student_id) {
          throw new Error("Learner identity mismatch");
        }
      })();
    }
    let mounted = true;
    activation.current
      .then(() => { if (mounted) navigate("/learn", { replace: true }); })
      .catch((err) => {
        if (!mounted) return;
        if (err instanceof ApiError && err.status === 409) {
          setInUse(true);
          activation.current = null;
        } else {
          setError("This practice link is invalid, expired or revoked. Ask your parent for a new link.");
        }
      })
      .finally(() => {
        // Do not persist bearer credentials in localStorage/sessionStorage.
        delete (window as Window & { __mihurPracticeToken?: string }).__mihurPracticeToken;
      });
    return () => { mounted = false; };
  }, [token, attempt, navigate]);

  if (inUse) {
    return (
      <main className="mx-auto flex min-h-screen max-w-lg flex-col items-center justify-center gap-6 px-4 py-10">
        <Brand size="lg" />
        <Card className="w-full">
          <CardHeader>
            <CardTitle>Someone is practicing on this link</CardTitle>
            <CardDescription>
              This practice link is open on another device right now.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-slate-600">
            <p>
              If this is your link, you can try again once the other device is
              done — or ask your grown-up for your own link if this one belongs
              to a brother or sister.
            </p>
            <Button
              className="w-full"
              variant="secondary"
              onClick={() => {
                setInUse(false);
                setAttempt((a) => a + 1);
              }}
            >
              Try again
            </Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col items-center justify-center gap-6 px-4 py-10">
      <Brand size="lg" />
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Ready to practice?</CardTitle>
          <CardDescription>
            Your private link opens your own Mihur practice space. You do not need
            an email address or a password.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error ? (
            <p className="text-sm text-destructive" role="alert">{error}</p>
          ) : (
            <p role="status" aria-live="polite" className="text-sm">
              Opening your practice space…
            </p>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
