import { FormEvent, useEffect, useLayoutEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Sparkles, ShieldCheck, LineChart } from "lucide-react";
import { api, ApiError, post } from "../api";
import Brand from "../components/Brand";
import Turnstile from "../components/Turnstile";
import type { AuthConfig, CountryOption, RegionsOut, SessionUser } from "../types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function Login() {
  const [mode, setMode] = useState<"signin" | "register">(
    () => window.location.pathname === "/register" ? "register" : "signin",
  );
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [parentPin, setParentPin] = useState("");
  const [invitationToken, setInvitationToken] = useState(
    () => (
      new URLSearchParams(window.location.hash.slice(1)).get("invite")
      ?? new URLSearchParams(window.location.search).get("invite")
      ?? ""
    ),
  );
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [coppaConsent, setCoppaConsent] = useState(false);
  const [countries, setCountries] = useState<CountryOption[]>([]);
  const [countryCode, setCountryCode] = useState("");
  const [regionCode, setRegionCode] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [siteKey, setSiteKey] = useState<string | null>(null);
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [turnstileReset, setTurnstileReset] = useState(0);
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = (params.get("next") || "/learn").replace(/^\/app/, "");

  useLayoutEffect(() => {
    // The invitation code must not remain in the address bar/history.
    const url = new URL(window.location.href);
    const hasInviteQuery = url.searchParams.has("invite");
    const hasInviteFragment = url.hash.startsWith("#invite=");
    if (hasInviteQuery || hasInviteFragment) {
      url.searchParams.delete("invite");
      if (hasInviteFragment) url.hash = "";
      window.history.replaceState(window.history.state, "", url.pathname + url.search + url.hash);
    }
  }, []);

  useEffect(() => { if (invitationToken) setMode("register"); }, [invitationToken]);

  useEffect(() => {
    api<AuthConfig>("/auth/config")
      .then((config) => setSiteKey(config.turnstile_site_key))
      .catch(() => setSiteKey(null));
  }, []);

  const selectedCountry = countries.find((c) => c.code === countryCode);
  const selectedRegion = selectedCountry?.regions.find((r) => r.code === regionCode);

  useEffect(() => {
    // Public catalog for the registration form (pre-auth). Loaded lazily —
    // the sign-in path never needs it.
    if (mode !== "register" || countries.length > 0) return;
    api<RegionsOut>("/auth/regions")
      .then((out) => setCountries(out.countries))
      .catch(() => setCountries([]));
  }, [mode, countries.length]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      let session: SessionUser;
      if (mode === "register") {
        // Radix Select doesn't participate in native form validation.
        if (!countryCode || !regionCode) {
          setError("Choose your country and state or province.");
          return;
        }
        session = await post<SessionUser>("/auth/register-parent", {
          email,
          password,
          display_name: displayName || undefined,
          parent_pin: parentPin,
          country_code: countryCode,
          region_code: regionCode,
          invitation_token: invitationToken.trim() || undefined,
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
      navigate(next, { replace: true });
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
                      <Label htmlFor="invitationToken">Private pilot invitation code</Label>
                      <Input
                        id="invitationToken"
                        value={invitationToken}
                        onChange={(e) => setInvitationToken(e.target.value)}
                        placeholder="Paste the code from your invitation"
                        autoComplete="off"
                        maxLength={256}
                      />
                      <p className="text-xs text-muted-foreground">
                        Only families with an invitation can register for the private pilot.
                      </p>
                    </div>
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
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1.5">
                        <Label htmlFor="country">Country</Label>
                        <Select
                          value={countryCode}
                          onValueChange={(v) => {
                            setCountryCode(v);
                            setRegionCode("");
                          }}
                        >
                          <SelectTrigger id="country">
                            <SelectValue placeholder="Select country" />
                          </SelectTrigger>
                          <SelectContent>
                            {countries.map((c) => (
                              <SelectItem key={c.code} value={c.code}>
                                {c.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-1.5">
                        <Label htmlFor="region">State / Province</Label>
                        <Select value={regionCode} onValueChange={setRegionCode} disabled={!countryCode}>
                          <SelectTrigger id="region">
                            <SelectValue placeholder={countryCode ? "Select state" : "Choose a country first"} />
                          </SelectTrigger>
                          <SelectContent>
                            {(selectedCountry?.regions ?? []).map((r) => (
                              <SelectItem key={r.code} value={r.code}>
                                {r.name}
                                {r.has_curriculum ? "" : " *"}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      We use this to show your state's curriculum.
                      {selectedRegion && !selectedRegion.has_curriculum
                        ? " * No state-specific curriculum yet — you'll see your country's catalog."
                        : ""}
                    </p>
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
