export interface LearnerChoice {
  id: string;
  first_name: string;
  curriculum_id: string;
  curriculum_code: string;
  curriculum_version: string;
  jurisdiction: string | null;
  avatar_id?: string;
}

export interface CurriculumChoice {
  id: string;
  code: string;
  version: string;
  jurisdiction: string | null;
  grade_level: string | null;
}

export interface SkillChoice {
  id: string;
  code: string;
  name: string;
  content_ready: boolean;
  learn?: LearnContent | null;
}

export interface LearnerLaunchpad {
  recommended: {
    id: string;
    code: string;
    name: string;
    reason: "CONTINUE_SESSION" | "RESUME_IN_PROGRESS" | "READY_TO_START" | "PREREQUISITE_GAP";
    mastery_score: number;
    session_id: string | null;
  } | null;
  reviews_due: { skill_id: string; skill_name: string }[];
  mastered_count: number;
  learning_count: number;
  ready_skill_count: number;
  award_count: number;
}

export interface SessionOut {
  session_id: string;
}

export type TutorState =
  | "DIAGNOSE"
  | "GUIDED_PRACTICE"
  | "REMEDIATION"
  | "INDEPENDENT_PRACTICE"
  | "MASTERY_CHECK"
  | "COMPLETE"
  | "REVIEW";

export interface VisualSpec {
  type: string;
  a?: number;
  b?: number;
  result?: number;
  min?: number;
  max?: number;
  aria_label?: string;
}

export interface ProblemChoice {
  id: string;
  text: string;
}

export interface LearnExample {
  title: string;
  steps: string[];
  answer?: string | null;
}

export interface LearnTerm {
  term: string;
  definition: string;
}

export interface LearnContent {
  summary: string;
  examples: LearnExample[];
  key_terms?: LearnTerm[];
  watch_out?: string[];
}

export interface WorkspaceProblem {
  id: string;
  prompt: string;
  difficulty: number;
  visual?: VisualSpec | null;
  answer_kind?: string;
  choices?: ProblemChoice[] | null;
  problem_type?: string | null;
  supports_steps?: boolean;
}

export type StepStatus =
  | "solved"
  | "valid"
  | "invalid"
  | "unparseable"
  | "duplicate";

export interface ReverseChallenge {
  line: string;
  prompt: string;
}

export interface WorkStepOut {
  status: StepStatus;
  feedback?: string | null;
  misconception_code?: string | null;
  revealed_line?: string | null;
  normalized_line?: string | null;
  invalid_count: number;
  cpa_level?: string | null;
  step_visual?: VisualSpec | null;
  reverse_challenge?: ReverseChallenge | null;
  challenge_outcome?: "spotted" | "missed" | "unresolved" | null;
}

export interface PhotoLine {
  text: string;
  needs_review: boolean;
}

export interface PhotoScanOut {
  problem_id: string;
  lines: PhotoLine[];
  engine: string;
}

export interface DiagnosticOut {
  session_id: string;
  status: string;
  target_skill_id: string;
  current_skill_id: string;
  question_count: number;
  max_questions: number;
  problem?: WorkspaceProblem | null;
  last_answer_correct?: boolean | null;
  recommended_skill_id?: string | null;
  placement_reason?: string | null;
  message: string;
}

export interface LearnerGrowth {
  xp: number;
  level: number;
  level_title: string;
  xp_in_level: number;
  xp_for_next: number;
  xp_today?: number;
}

export interface LearnerWorkspace {
  session_id: string;
  state: TutorState;
  learner: { id: string; first_name: string; grade_level: string; avatar_id?: string };
  curriculum: { id: string; code: string; name: string; jurisdiction: string | null };
  focus: {
    primary_skill_id: string;
    primary_skill_name: string;
    active_skill_id: string;
    skill_name: string;
    in_remediation: boolean;
    remediation_reason?: string | null;
    learn?: LearnContent | null;
  };
  problem: WorkspaceProblem | null;
  coaching_message: string | null;
  allowed_actions: string[];
  evidence: {
    mastery_score: number;
    confidence_score: number;
    independent_correct_count: number;
    independent_attempt_count: number;
    hinted_correct_count: number;
    smartscore: number;
    streak_count: number;
    mastery_level: "practicing" | "proficient" | "mastered";
  };
  reviews_due: { skill_id: string; skill_name: string }[];
  awards: Award[];
  recommended_next: { skill_id: string; skill_code: string; skill_name: string } | null;
  streak_days?: number;
  growth?: LearnerGrowth | null;
  daily_goal?: DailyGoal | null;
}

export interface DailyGoal {
  target: number;
  done: number;
  reached: boolean;
}

export interface SessionSummary {
  attempts: number;
  correct: number;
  independent_correct: number;
  minutes: number;
  xp_earned: number;
  smartscore_start: number | null;
  smartscore_now: number;
  skills_practiced: string[];
  misconceptions: { code: string; name: string; resolved: boolean }[];
  awards: Award[];
  daily_goal: DailyGoal | null;
}

export interface Award {
  code: string;
  name: string;
  description: string;
  skill_name: string | null;
  awarded_at: string;
}

export interface EvaluationOut {
  correct: boolean;
  misconception_code: string | null;
}

export interface RespondOut {
  evaluation: EvaluationOut;
  new_awards?: Award[];
  xp_earned?: number;
  growth?: (LearnerGrowth & { leveled_up?: boolean }) | null;
}

export interface Badge {
  code: string;
  name: string;
  description: string;
  earned: boolean;
  times_earned: number;
  skill_names: string[];
  progress: { current: number; target: number } | null;
}

export interface SkillMapEntry {
  skill_id: string;
  code: string;
  name: string;
  difficulty_level: number;
  mastery_score: number;
  status: string;
  is_active: boolean;
}

export interface HintResponse {
  allowed: boolean;
  level: number;
  message: string;
}


export interface ChildSummary {
  id: string;
  first_name: string;
  grade_level: string;
  school_system: string | null;
  curriculum_name: string | null;
  curriculum_code: string | null;
  curriculum_version: string | null;
  jurisdiction: string | null;
}

export interface ParentSkillProgress {
  skill_id: string;
  skill_code: string;
  skill_name: string;
  status: string;
  attempt_count: number;
  independent_attempt_count: number;
  independent_correct_count: number;
  hinted_correct_count: number;
  evidence_status: string;
  learning_state: string;
  assistance_signal: string;
  reason_code: string;
  action_code: string;
}

export interface StrandSummary {
  strand: string;
  total: number;
  mastered: number;
  in_progress: number;
}

export interface GradeLevelSummary {
  curriculum_code: string | null;
  curriculum_name: string | null;
  skills_total: number;
  skills_mastered: number;
  skills_in_progress: number;
  skills_not_started: number;
  mastery_percent: number;
  strands: StrandSummary[];
  sessions_last_7_days: number;
  minutes_last_7_days: number;
  trouble_spots: string[];
}

export interface WorkStepLine {
  line: string;
  status: string;
  misconception_code: string | null;
  revealed: boolean;
}

export interface StepTrail {
  problem_id: string;
  prompt: string;
  skill_name: string;
  updated_at: string;
  status: string;
  lines: WorkStepLine[];
  misconception_names: string[];
}

export interface ChildDashboard {
  child: ChildSummary;
  active_skill_name: string | null;
  skills: ParentSkillProgress[];
  recent_activity: { session_id: string; skill_name: string; state: string; started_at: string; ended_at: string | null }[];
  support_areas: { code: string; name: string; occurrence_count: number }[];
  reviews_due: { skill_id: string; skill_code: string; skill_name: string; status: string; due_at: string; interval_index: number; mastery_score: number; projected_mastery_score: number }[];
  recommended_next: { skill_id: string; skill_code: string; skill_name: string; reason: string } | null;
  grade_level_summary?: GradeLevelSummary | null;
  daily_metrics?: { date: string; label: string; minutes: number; mastery_score: number }[];
  weekly_digest?: WeeklyDigest | null;
  step_trails?: StepTrail[];
  recent_patterns?: { code: string; name: string; count: number; source: string }[];
}

export interface WeeklyDigest {
  sessions: number;
  minutes: number;
  xp_earned: number;
  skills_mastered: number;
  badges_earned: number;
  prev_sessions: number;
  prev_minutes: number;
  minutes_delta: number;
  mastery_delta: number | null;
  days_since_practice: number | null;
  stall: boolean;
}

export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED";

export interface SessionUser {
  id: string;
  role: string;
  display_name: string | null;
  approval_status: ApprovalStatus | null;
  rejection_reason: string | null;
}
