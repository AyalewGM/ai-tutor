import { FormEvent, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, post } from "../api";
import Brand from "../components/Brand";

type Activated = { student_id: string; nickname: string };

export default function PracticePass() {
  const { token = "" } = useParams();
  const [nickname, setNickname] = useState("");
  const [error, setError] = useState("");
  const [inUse, setInUse] = useState(false);
  const navigate = useNavigate();

  async function activate(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await post<Activated>("/practice-pass/activate", { token, nickname });
      // Replace removes the bearer credential from browser history.
      navigate("/learn", { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setInUse(true);
        return;
      }
      setError(
        err instanceof ApiError && err.status === 401
          ? "This link isn't working — it may be old. Ask your grown-up for a fresh one."
          : "Could not open this practice pass.",
      );
    }
  }

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
                setNickname("");
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
            Enter a short nickname. You do not need an email or password.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={activate} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="nickname">What should we call you?</Label>
              <Input id="nickname" value={nickname} onChange={(e) => setNickname(e.target.value)}
                minLength={1} maxLength={32} pattern="[A-Za-z0-9_-]+" autoComplete="off" required />
            </div>
            <Button className="w-full" type="submit">Start learning</Button>
          </form>
          {error && <p className="mt-4 text-sm text-destructive" role="alert">{error}</p>}
        </CardContent>
      </Card>
    </main>
  );
}
