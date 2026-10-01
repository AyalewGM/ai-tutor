import { FormEvent, useState } from "react";
import { Lock } from "lucide-react";
import { ApiError, post } from "../api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface ParentUnlockProps {
  onUnlocked: (token: string) => void;
  description?: string;
}

/**
 * PIN-gated unlock for parent surfaces. Falls back to account-password
 * re-authentication when the account has no PIN configured (the API
 * returns 409 "use password re-authentication").
 */
export default function ParentUnlock({ onUnlocked, description }: ParentUnlockProps) {
  const [pin, setPin] = useState("");
  const [password, setPassword] = useState("");
  const [usePassword, setUsePassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function unlock(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const result = usePassword
        ? await post<{ verified: boolean; unlock_token: string }>(
            "/parents/verify-password",
            { password },
          )
        : await post<{ verified: boolean; unlock_token: string }>(
            "/parents/verify-pin",
            { parent_pin: pin },
          );
      sessionStorage.setItem("parentUnlock", result.unlock_token);
      setPin("");
      setPassword("");
      onUnlocked(result.unlock_token);
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 409 && !usePassword) {
        setUsePassword(true);
        setError("");
      } else {
        setError(
          reason instanceof ApiError
            ? reason.message
            : "Could not verify parent access.",
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card className="mx-auto max-w-md">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Lock className="h-5 w-5 text-primary" />
          <CardTitle>Parent access</CardTitle>
        </div>
        <CardDescription>
          {description ??
            (usePassword
              ? "This account has no PIN configured. Re-enter your account password to continue."
              : "Enter your 4-digit parent PIN to view progress and adult settings.")}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={unlock} className="space-y-4">
          {usePassword ? (
            <div className="space-y-1.5">
              <Label htmlFor="parent-password">Account password</Label>
              <Input
                id="parent-password"
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </div>
          ) : (
            <div className="space-y-1.5">
              <Label htmlFor="parent-pin">Parent PIN</Label>
              <Input
                id="parent-pin"
                type="password"
                inputMode="numeric"
                pattern="[0-9]{4}"
                minLength={4}
                maxLength={4}
                required
                autoComplete="off"
                value={pin}
                onChange={(event) => setPin(event.target.value)}
              />
            </div>
          )}
          {error && (
            <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive" role="alert">
              {error}
            </p>
          )}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? "Verifying…" : "Unlock parent view"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
