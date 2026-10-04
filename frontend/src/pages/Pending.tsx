import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Clock, LogOut, MailCheck } from "lucide-react";
import { api, post } from "../api";
import Brand from "../components/Brand";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { SessionUser } from "../types";

/**
 * Shown to families waiting on pilot approval (or declined). Reads
 * /auth/me, which stays available while the rest of the app is gated.
 */
export default function Pending() {
  const navigate = useNavigate();
  const [me, setMe] = useState<SessionUser | null>(null);

  useEffect(() => {
    api<SessionUser>("/auth/me")
      .then((user) => {
        if (user.approval_status === "APPROVED") navigate("/learn", { replace: true });
        else setMe(user);
      })
      .catch(() => navigate("/login", { replace: true }));
  }, [navigate]);

  async function signOut() {
    try {
      await post("/auth/logout");
    } finally {
      navigate("/login", { replace: true });
    }
  }

  const rejected = me?.approval_status === "REJECTED";

  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col items-center justify-center gap-6 px-4 py-10">
      <Brand size="lg" />
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {rejected ? (
              <MailCheck className="h-5 w-5 text-primary" />
            ) : (
              <Clock className="h-5 w-5 text-primary" />
            )}
            {rejected ? "An update on your pilot request" : "Thanks for signing up!"}
          </CardTitle>
          <CardDescription>
            {rejected
              ? "We're not able to include your family in the current pilot."
              : "Mihur is in a private pilot, so we review each new family before access opens."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-muted-foreground">
          {me === null ? (
            <p>Checking your account…</p>
          ) : rejected ? (
            <>
              {me.rejection_reason && (
                <p className="rounded-md bg-secondary px-3 py-2">{me.rejection_reason}</p>
              )}
              <p>We'll be in touch as Mihur opens to more families.</p>
            </>
          ) : (
            <p>
              We'll email you as soon as your account is approved. After that, sign in
              here to add your learner and start practicing.
            </p>
          )}
          <Button variant="outline" className="w-full" onClick={signOut}>
            <LogOut className="h-4 w-4" /> Sign out
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}
