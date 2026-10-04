import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Sparkles, ShieldCheck, LineChart } from "lucide-react";
import { api, ApiError, post } from "../api";
import Brand from "../components/Brand";
import Turnstile from "../components/Turnstile";
import type { AuthConfig, SessionUser } from "../types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function Login() {
  const [mode, setMode] = useState<"signin" | "register">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [parentPin, setParentPin] = useState("");
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [coppaConsent, setCoppaConsent] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [siteKey, setSiteKey] = useState<string | null>(null);
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [turnstileReset, setTurnstileReset] = useState(0);
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = (params.get("next") || "/learn").replace(/^\/app/, "");

  useEffect(() => {
    api<AuthConfig>("/auth/config")
      .then((config) => setSiteKey(config.turnstile_site_key))
      .catch(() => setSiteKey(null));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      let session: SessionUser;
      if (mode === "register") {
        session = await post<SessionUser>("/auth/register-parent", {
          email,
          password,
          display_name: displayName || undefined,
          parent_pin: parentPin,
          terms_accepted: termsAccepted,
          coppa_consent_given: coppaConsent,
          turnstile_token: turnstileToken || undefined,
        });
      } else {
        session = await post<SessionUser>("/auth/login", {
          email,
          password,
          turnstile_token: turnstileToken || undefined,
        });
      }
      const awaitingApproval =
        session.approval_status === "PENDING" || session.approval_status === "REJECTED";
      navigate(awaitingApproval ? "/pending" : next, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
      setTurnstileToken(null);
      setTurnstileReset((n) => n + 1);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Brand header */}
      <header className="flex items-center px-6 py-4">
        <Link to="/" aria-label="Mihur home">
          <Brand size="md" />
        </Link>
      </header>

      <div className="flex flex-1 items-center justify-center px-4 pb-16">
        <div className="grid w-full max-w-4xl gap-10 md:grid-cols-[1.1fr_1fr] md:items-center">
          {/* Value proposition */}
          <div className="hidden md:block">
            <p className="text-sm font-semibold uppercase tracking-widest text-primary">Family learning</p>
            <h1 className="mt-2 text-4xl font-bold leading-tight tracking-tight">
              Learn what matters.
              <br />
              Know what sticks.
            </h1>
            <p className="mt-4 text-muted-foreground leading-relaxed">
              Curriculum-aware tutoring that keeps guided work separate from what your
              child can demonstrate independently.
            </p>
            <ul className="mt-8 space-y-4">
              <li className="flex items-start gap-3">
                <Sparkles className="mt-0.5 h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium">Adaptive practice</p>
                  <p className="text-sm text-muted-foreground">Sessions adjust to your child's exact curriculum and current mastery.</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <LineChart className="mt-0.5 h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium">Evidence-backed progress</p>
                  <p className="text-sm text-muted-foreground">Independent mastery stays visibly separate from assisted success.</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <ShieldCheck className="mt-0.5 h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium">Family privacy first</p>
                  <p className="text-sm text-muted-foreground">Server-side authorization controls all learner data access.</p>
                </div>
              </li>
            </ul>
          </div>

          {/* Auth card */}
          <Card className="w-full shadow-raised">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl">{mode === "signin" ? "Welcome back" : "Create your family account"}</CardTitle>
              <CardDescription>
                {mode === "signin"
                  ? "Sign in to continue your child's learning."
                  : "Parents manage the account — learners don't need passwords."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-5 grid grid-cols-2 rounded-lg bg-secondary p-1" role="tablist">
                <button
                  role="tab"
                  aria-selected={mode === "signin"}
                  className={`rounded-md py-2 text-sm font-medium transition-colors ${mode === "signin" ? "bg-card shadow-sm" : "text-muted-foreground"}`}
                  onClick={() => setMode("signin")}
                >
                  Sign in
                </button>
                <button
                  role="tab"
                  aria-selected={mode === "register"}
                  className={`rounded-md py-2 text-sm font-medium transition-colors ${mode === "register" ? "bg-card shadow-sm" : "text-muted-foreground"}`}
                  onClick={() => setMode("register")}
                >
                  Create account
                </button>
              </div>

              <form onSubmit={submit} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    required
                    autoComplete="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    required
                    minLength={mode === "register" ? 12 : 1}
                    autoComplete={mode === "register" ? "new-password" : "current-password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  {mode === "register" && (
                    <p className="text-xs text-muted-foreground">At least 12 characters.</p>
                  )}
                </div>

                {mode === "register" && (
                  <>
                    <div className="space-y-1.5">
                      <Label htmlFor="displayName">Display name</Label>
                      <Input
                        id="displayName"
                        value={displayName}
                        onChange={(e) => setDisplayName(e.target.value)}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="parentPin">4-digit parent PIN</Label>
                      <Input
                        id="parentPin"
                        type="password"
                        inputMode="numeric"
                        pattern="[0-9]{4}"
                        minLength={4}
                        maxLength={4}
                        required
                        autoComplete="off"
                        value={parentPin}
                        onChange={(e) => setParentPin(e.target.value)}
                      />
                      <p className="text-xs text-muted-foreground">Unlocks parent settings and the progress dashboard.</p>
                    </div>
                    <label className="flex items-start gap-2.5 text-sm">
                      <input
                        type="checkbox"
                        required
                        className="mt-0.5 h-4 w-4 accent-primary"
                        checked={termsAccepted}
                        onChange={(e) => setTermsAccepted(e.target.checked)}
                      />
                      I accept the Terms of Service.
                    </label>
                    <label className="flex items-start gap-2.5 text-sm">
                      <input
                        type="checkbox"
                        required
                        className="mt-0.5 h-4 w-4 accent-primary"
                        checked={coppaConsent}
                        onChange={(e) => setCoppaConsent(e.target.checked)}
                      />
                      I am the parent or guardian and consent to the privacy practices described for this family account.
                    </label>
                    <p className="rounded-md bg-secondary px-3 py-2 text-xs text-muted-foreground">
                      Mihur uses AI to help word hints and explanations. It never
                      grades your child's work or gives answers, and it never
                      receives your child's name.{" "}
                      <Link to="/privacy#ai" className="font-medium text-primary underline-offset-2 hover:underline">
                        How we use AI
                      </Link>
                    </p>
                  </>
                )}

                {siteKey && (
                  <Turnstile
                    siteKey={siteKey}
                    onToken={setTurnstileToken}
                    resetSignal={turnstileReset}
                  />
                )}

                {error && (
                  <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive" role="alert">
                    {error}
                  </p>
                )}

                <Button type="submit" className="w-full" size="lg" disabled={submitting}>
                  {submitting ? "Please wait…" : mode === "register" ? "Create account" : "Sign in"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
