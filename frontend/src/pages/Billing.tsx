import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { CreditCard, ExternalLink, Loader2 } from "lucide-react";

import { api, post } from "../api";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";

interface PlanOption {
  code: string;
  name: string;
  max_students: number;
  price: { currency: string; amount: string };
}

interface Subscription {
  tier: string;
  status: string | null;
  trial_ends_at: string | null;
  can_manage: boolean;
  billing_enabled: boolean;
}

export default function Billing() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [plans, setPlans] = useState<PlanOption[]>([]);
  const [sub, setSub] = useState<Subscription | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const status = params.get("status");

  useEffect(() => {
    api<{ plans: PlanOption[] }>("/onboarding/plans").then((r) => setPlans(r.plans));
    api<Subscription>("/billing/subscription").then(setSub);
  }, []);

  async function subscribe(code: string) {
    setBusy(code);
    setError(null);
    try {
      const { url } = await post<{ url: string }>("/billing/checkout", { plan_code: code });
      window.location.href = url;
    } catch {
      setError("Checkout isn't available for this plan yet.");
      setBusy(null);
    }
  }

  async function manage() {
    setBusy("portal");
    try {
      const { url } = await post<{ url: string }>("/billing/portal");
      window.location.href = url;
    } catch {
      setError("Couldn't open the billing portal.");
      setBusy(null);
    }
  }

  if (!sub) {
    return <div className="flex justify-center py-20"><Loader2 className="animate-spin" /></div>;
  }

  const trialing = sub.status === "trialing" && sub.trial_ends_at;

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <CreditCard className="h-6 w-6" /> Plan &amp; billing
        </h1>
        <Button variant="ghost" onClick={() => navigate("/learn")}>Back to learners</Button>
      </div>

      {status === "success" && (
        <div className="rounded-lg border border-green-300 bg-green-50 p-3 text-sm text-green-800">
          Subscription started — your plan benefits are active.
        </div>
      )}
      {status === "cancel" && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
          Checkout cancelled — nothing was charged.
        </div>
      )}
      {error && <div className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</div>}

      {trialing && (
        <Card className="p-4">
          <p className="text-sm">
            Free trial until <strong>{new Date(sub.trial_ends_at!).toLocaleDateString()}</strong>.
            Your card is on file and won't be charged until the trial ends.
          </p>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {plans.map((plan) => {
          const current = plan.code === sub.tier;
          const free = plan.price.amount === "0" || plan.price.amount === "0.00";
          return (
            <Card key={plan.code} className="flex flex-col gap-3 p-5">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">{plan.name}</h2>
                {current && <Badge>Current</Badge>}
              </div>
              <p className="text-2xl font-bold">
                {free ? "Free" : `${plan.price.amount} ${plan.price.currency}`}
                {!free && <span className="text-sm font-normal text-muted-foreground">/month</span>}
              </p>
              <p className="text-sm text-muted-foreground">
                Up to {plan.max_students} learner{plan.max_students === 1 ? "" : "s"}
              </p>
              <div className="mt-auto pt-2">
                {current ? (
                  sub.can_manage ? (
                    <Button variant="outline" className="w-full" onClick={manage} disabled={busy !== null}>
                      <ExternalLink className="mr-2 h-4 w-4" /> Manage billing
                    </Button>
                  ) : (
                    <Button variant="outline" className="w-full" disabled>Current plan</Button>
                  )
                ) : free ? (
                  <Button variant="outline" className="w-full" disabled>Free tier</Button>
                ) : (
                  <Button className="w-full" onClick={() => subscribe(plan.code)} disabled={busy !== null || !sub.billing_enabled}>
                    {busy === plan.code ? "Redirecting…" : "Start free trial"}
                  </Button>
                )}
              </div>
            </Card>
          );
        })}
      </div>

      {!sub.billing_enabled && (
        <p className="text-center text-sm text-muted-foreground">
          Online billing isn't enabled on this deployment yet.
        </p>
      )}
    </div>
  );
}
