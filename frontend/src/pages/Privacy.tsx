import { Link } from "react-router-dom";
import { ArrowLeft, Database, Lock, ShieldCheck, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const PRACTICES = [
  {
    icon: ShieldCheck,
    title: "What we collect",
    body: "A parent's email, a learner nickname (never a legal name), grade level, and practice answers used to adapt instruction. That is the whole list.",
  },
  {
    icon: Lock,
    title: "What we never do",
    body: "No advertising, no tracking pixels, no session replay, no selling or sharing learner data with third parties. Learner work stays in the product.",
  },
  {
    icon: Database,
    title: "How tutoring works",
    body: "Correctness, mastery, and progression are decided by the application's own logic — never by an AI model. AI may only help phrase hints and explanations after the system decides what is pedagogically correct.",
  },
  {
    icon: Trash2,
    title: "Your control",
    body: "Parent dashboards are PIN-gated. You can delete a learner and all of their evidence at any time from Settings & privacy — deletion is immediate and complete.",
  },
];

export default function Privacy() {
  return (
    <div className="min-h-screen bg-background">
      <main className="mx-auto max-w-3xl px-4 py-10">
        <Button variant="ghost" asChild className="mb-6">
          <Link to="/login">
            <ArrowLeft className="h-4 w-4" /> Back
          </Link>
        </Button>
        <h1 className="text-3xl font-bold tracking-tight">Privacy practices</h1>
        <p className="mt-2 text-muted-foreground">
          AI Tutor is built family-first: minimum data, no ads, and full
          parental control over learner information.
        </p>
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {PRACTICES.map((practice) => (
            <Card key={practice.title}>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <practice.icon className="h-5 w-5 text-primary" />
                  {practice.title}
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                {practice.body}
              </CardContent>
            </Card>
          ))}
        </div>
        <p className="mt-8 text-sm text-muted-foreground">
          Questions about privacy during the pilot? Contact your pilot
          coordinator directly — we answer every question personally.
        </p>
      </main>
    </div>
  );
}
