export interface LearnerChoice {
  id: string;
  first_name: string;
  curriculum_id: string;
  curriculum_code: string;
  curriculum_version: string;
  jurisdiction: string | null;
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

export interface WorkspaceProblem {
  id: string;
  prompt: string;
  difficulty: number;
  visual?: VisualSpec | null;
}

export interface LearnerWorkspace {
  session_id: string;
  state: TutorState;
  learner: { id: string; first_name: string; grade_level: string };
  curriculum: { id: string; code: string; name: string; jurisdiction: string | null };
  focus: { skill_id: string; skill_code: string; skill_name: string };
  problem: WorkspaceProblem | null;
  coaching_message: string | null;
  allowed_actions: string[];
  evidence: {
    mastery_score: number;
    confidence_score: number;
    independent_correct_count: number;
    independent_attempt_count: number;
    hinted_correct_count: number;
  };
  reviews_due: { skill_id: string; skill_name: string }[];
  awards: Award[];
  recommended_next: { skill_id: string; skill_code: string; skill_name: string } | null;
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
