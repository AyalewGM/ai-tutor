export type StaffMe = {
  email: string;
  role: string;
  permissions: string[];
  mfa_enrolled: boolean;
  mfa_verified: boolean;
};

export type MfaSetup = {
  secret: string;
  otpauth_uri: string;
};

export type WindowCounts = { "1d": number; "7d": number; "30d": number };

export type MetricsOverview = {
  as_of: string;
  active_learners: WindowCounts;
  active_families: WindowCounts;
  attempts: WindowCounts;
  tutor_sessions: WindowCounts;
  signups: { "1d": number; "7d": number; "30d": number; total: number };
  signups_daily: { date: string; count: number }[];
  learners_total: number;
};

export type RegionActivity = {
  country_code: string;
  region_code: string;
  families: number;
  active_learners: number;
  attempts: number;
};

export type CurriculumActivity = {
  code: string;
  name: string;
  learners_total: number;
  active_learners: number;
  attempts: number;
};

export type AdminFamily = {
  parent_profile_id: string;
  email: string;
  display_name: string | null;
  approval_status: "PENDING" | "APPROVED" | "REJECTED";
  registered_at: string;
  decided_at: string | null;
  rejection_reason: string | null;
  learner_count: number;
};

export type AiUsageSummary = {
  month: string;
  generations: number;
  denied: number;
  spend_usd: string;
  cap_usd: string;
  families: {
    family_user_id: string | null;
    generations: number;
    denied: number;
    spend_usd: string;
  }[];
};

export type AdminPlan = {
  code: string;
  name: string;
  monthly_price_usd: string;
  monthly_price_cad: number;
  max_students: number;
  ai_daily_generations: number;
  active: boolean;
  updated_at: string;
};

export type PlansAdmin = {
  usd_to_cad_rate: string;
  plans: AdminPlan[];
};

export type AuditEvent = {
  id: string;
  actor_label: string;
  action: string;
  target_type: string | null;
  target_id: string | null;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  created_at: string;
};
