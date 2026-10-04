import { Link } from "react-router-dom";
import { ArrowLeft, Camera, Database, Lock, ShieldCheck, Sparkles, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Brand from "../components/Brand";

const PRACTICES = [
  {
    icon: ShieldCheck,
    title: "What we collect",
    body: "A parent's email, a learner nickname (never a legal name), grade level, and practice answers used to adapt instruction. That is the whole list.",
  },
  {
    icon: Lock,
    title: "What we never do",
    body: "No advertising, no tracking pixels, no session replay, and we never sell learner data. Learner work is shared only with the service providers listed below, and only to deliver tutoring.",
  },
  {
    icon: Database,
    title: "How tutoring works",
    body: "Correctness, mastery, and progression are decided by Mihur's own mathematics engine — never by an AI model. AI may only help phrase hints and explanations after the system decides what is pedagogically correct.",
  },
  {
    icon: Trash2,
    title: "Your control",
    body: "Parent dashboards are PIN-gated. You can delete a learner and all of their evidence at any time from Settings & privacy — deletion is immediate and complete.",
  },
];

const AI_RECEIVES = [
  "The grade level, curriculum, and skill being practiced",
  "The math problem your child is working on",
  "The step your child wrote, when the hint is about their work",
  "Which kind of mistake our math engine detected, and how much help to give",
];

const AI_NEVER_RECEIVES = [
  "Your child's name or nickname",
  "Your email address or any account details",
  "Mastery scores, progress history, or other learners' work",
];

export default function Privacy() {
  return (
    <div className="min-h-screen bg-background">
      <main className="mx-auto max-w-3xl px-4 py-10">
        <div className="mb-6 flex items-center justify-between">
          <Button variant="ghost" asChild>
            <Link to="/login">
              <ArrowLeft className="h-4 w-4" /> Back
            </Link>
          </Button>
          <Link to="/" aria-label="Mihur home">
            <Brand size="sm" />
          </Link>
        </div>
        <h1 className="text-3xl font-bold tracking-tight">Privacy practices</h1>
        <p className="mt-2 text-muted-foreground">
          Mihur is built family-first: minimum data, no ads, and full
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

        <section id="ai" className="mt-12" aria-labelledby="ai-heading">
          <h2 id="ai-heading" className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Sparkles className="h-6 w-6 text-primary" /> How Mihur uses AI
          </h2>
          <p className="mt-2 text-muted-foreground">
            Mihur uses an AI language model to put hints and explanations into
            clear, encouraging words. It is instructed to guide with questions
            and never give the answer — and if a message would reveal the
            answer anyway, Mihur replaces it with a built-in hint before your
            child sees it. If the AI is unavailable, built-in hints take over.
          </p>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">What the AI receives</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="list-disc space-y-1.5 pl-5 text-sm text-muted-foreground">
                  {AI_RECEIVES.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">What the AI never receives</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="list-disc space-y-1.5 pl-5 text-sm text-muted-foreground">
                  {AI_NEVER_RECEIVES.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </CardContent>
            </Card>
          </div>
          <h3 className="mt-8 flex items-center gap-2 text-lg font-semibold">
            <Camera className="h-5 w-5 text-primary" /> Photos of written work
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            If your child uploads a photo of their work, it is sent to Mathpix,
            a handwriting-recognition service, to read the math. Mihur processes
            the photo in memory and never stores or logs it.
          </p>
        </section>

        <p className="mt-8 text-sm text-muted-foreground">
          Questions about privacy during the pilot? Contact your pilot
          coordinator directly — we answer every question personally.
        </p>
      </main>
    </div>
  );
}
