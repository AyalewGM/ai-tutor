import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Settings } from "lucide-react";
import { api } from "../api";
import NavBar from "../components/NavBar";
import ParentUnlock from "../components/ParentUnlock";
import ParentProgressDashboard from "../components/dashboard/ParentProgressDashboard";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { ChildSummary } from "../types";

export default function ParentDashboard() {
  const [children, setChildren] = useState<ChildSummary[]>([]);
  const [childId, setChildId] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [unlockToken, setUnlockToken] = useState(
    () => sessionStorage.getItem("parentUnlock") || "",
  );

  useEffect(() => {
    api<ChildSummary[]>("/parents/children")
      .then((rows) => {
        setChildren(rows);
        if (rows.length) setChildId((current) => current || rows[0].id);
      })
      .catch(() => setError("Could not load family dashboard."))
      .finally(() => setLoading(false));
  }, []);



  return (
    <div className="min-h-screen bg-background">
      <NavBar />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-primary">Parent dashboard</p>
            <h1 className="mt-1 text-3xl font-bold tracking-tight">Family learning overview</h1>
            <p className="mt-1 max-w-xl text-muted-foreground">
              A clear weekly view of independent progress, learning activity, and areas where
              your child may need support.
            </p>
          </div>
          <Button variant="outline" asChild>
            <Link to="/parent/settings">
              <Settings className="h-4 w-4" /> Settings &amp; privacy
            </Link>
          </Button>
        </div>

        {!unlockToken && (
          <ParentUnlock onUnlocked={setUnlockToken} />
        )}

        {error && (
          <p className="mt-6 rounded-md bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive" role="alert">
            {error}
          </p>
        )}
        {loading && (
          <div className="mt-6 space-y-3" role="status" aria-label="Loading family profiles">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-48 w-full" />
          </div>
        )}
        {!loading && !children.length && (
          <Card className="mt-6">
            <CardContent className="py-10 text-center">
              <h2 className="text-lg font-semibold">No learners yet</h2>
              <p className="mt-1 text-muted-foreground">
                Add a learner from Practice to begin building an evidence-backed progress view.
              </p>
              <Button asChild className="mt-4" variant="secondary">
                <Link to="/learn">Go to Practice</Link>
              </Button>
            </CardContent>
          </Card>
        )}

        {!loading && unlockToken && children.length > 0 && childId && (
          <ParentProgressDashboard
            unlockToken={unlockToken}
            children={children}
            selectedStudentId={childId}
            onStudentChange={setChildId}
          />
        )}
      </main>
    </div>
  );
}
