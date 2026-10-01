import { FormEvent, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ApiError, post } from "../api";

export default function Login() {
  const [mode, setMode] = useState<"signin" | "register">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [parentPin, setParentPin] = useState("");
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [coppaConsent, setCoppaConsent] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get("next") || "/app/learn";

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      if (mode === "register") {
        await post("/auth/register-parent", {
          email,
          password,
          display_name: displayName || undefined,
          parent_pin: parentPin,
          terms_accepted: termsAccepted,
          coppa_consent_given: coppaConsent,
        });
      } else {
        await post("/auth/login", { email, password });
      }
      navigate(next.replace(/^\/app/, ""), { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    }
  }

  return (
    <div className="auth-shell">
      <div className="card auth-card">
        <h1 className="brand">AI Tutor</h1>
        <div className="tabs" role="tablist">
          <button
            role="tab"
            aria-selected={mode === "signin"}
            className={mode === "signin" ? "tab active" : "tab"}
            onClick={() => setMode("signin")}
          >
            Sign in
          </button>
          <button
            role="tab"
            aria-selected={mode === "register"}
            className={mode === "register" ? "tab active" : "tab"}
            onClick={() => setMode("register")}
          >
            Create account
          </button>
        </div>
        <form onSubmit={submit}>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            required
            minLength={mode === "register" ? 12 : 1}
            autoComplete={mode === "register" ? "new-password" : "current-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {mode === "register" && (
            <>
              <label htmlFor="displayName">Display name</label>
              <input
                id="displayName"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
              />
              <label htmlFor="parentPin">4-digit parent PIN</label>
              <input
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
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  required
                  checked={termsAccepted}
                  onChange={(e) => setTermsAccepted(e.target.checked)}
                />
                I accept the Terms of Service.
              </label>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  required
                  checked={coppaConsent}
                  onChange={(e) => setCoppaConsent(e.target.checked)}
                />
                I am the parent or guardian and consent to the privacy practices described for this family account.
              </label>
            </>
          )}
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          <button type="submit" className="primary">
            {mode === "register" ? "Create account" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
