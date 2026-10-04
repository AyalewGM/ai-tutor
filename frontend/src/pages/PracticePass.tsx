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
  const navigate = useNavigate();

  async function activate(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await post<Activated>("/practice-pass/activate", { token, nickname });
      // Replace removes the bearer credential from browser history.
      navigate("/learn", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not open this practice pass.");
    }
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
