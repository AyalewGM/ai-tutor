import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  Clock,
  Download,
  TrendingUp,
} from "lucide-react";
import { ApiError, api } from "../../api";
import type { ChildDashboard, ChildSummary } from "../../types";
import ActivityChart from "./ActivityChart";
import MisconceptionList from "./MisconceptionList";
import StatCard from "./StatCard";
import SyllabusProgressDonut from "./SyllabusProgressDonut";

export interface DailyMetric {
  date: string;
  label: string;
  minutes: number;
  masteryScore: number;
}

export interface SyllabusStatus {
  status: "Mastered" | "In Progress" | "Not Started";
  count: number;
}

export interface MisconceptionItem {
  id: string;
  topicName: string;
  misconception: string;
  flaggedAt: string;
  status: "Resolved" | "Needs Review";
  suggestion: string;
}

export interface StudentSummary {
  studentId: string;
  displayName: string;
  gradeLevel: string;
  totalLearningMinutes: number;
  learningTimeTrend: number | null;
  topicsMastered: number;
  totalTopics: number;
  masteryScore: number;
  masteryTrend: number | null;
  activeMisconceptions: number;
  dailyMetrics: DailyMetric[];
  syllabus: SyllabusStatus[];
  misconceptions: MisconceptionItem[];
}

interface ProgressStudentApi {
  student_id: string;
  display_name: string;
  sessions_started: number;
  sessions_completed: number;
  attempts: number;
  correct_attempts: number;
  average_mastery: number;
}

interface ProgressSummaryApi {
  window_days: number;
  students: ProgressStudentApi[];
}

interface ParentProgressDashboardProps {
  unlockToken: string;
  children: ChildSummary[];
  selectedStudentId: string;
  onStudentChange: (studentId: string) => void;
}

const demoDailyMetrics: DailyMetric[] = [
  { date: "2026-09-24", label: "Wed", minutes: 22, masteryScore: 68 },
  { date: "2026-09-25", label: "Thu", minutes: 34, masteryScore: 71 },
  { date: "2026-09-26", label: "Fri", minutes: 18, masteryScore: 73 },
  { date: "2026-09-27", label: "Sat", minutes: 46, masteryScore: 76 },
  { date: "2026-09-28", label: "Sun", minutes: 31, masteryScore: 79 },
  { date: "2026-09-29", label: "Mon", minutes: 29, masteryScore: 81 },
  { date: "2026-09-30", label: "Tue", minutes: 38, masteryScore: 84 },
];

const demoMisconceptions: MisconceptionItem[] = [
  {
    id: "demo-order-operations",
    topicName: "Multi-step expressions",
    misconception: "Applies addition before multiplication when grouping symbols are absent.",
    flaggedAt: "2026-09-29T18:30:00Z",
    status: "Needs Review",
    suggestion:
      "Ask the learner to explain which operation should happen first and why, then compare two worked examples without giving the answer.",
  },
  {
    id: "demo-negative-sign",
    topicName: "Integer operations",
    misconception: "Sometimes treats subtraction of a negative number as subtraction of its absolute value.",
    flaggedAt: "2026-09-27T17:10:00Z",
    status: "Needs Review",
    suggestion:
      "Use a number line and ask what direction changes when subtracting a negative quantity.",
  },
];

function deriveSyllabus(dashboard: ChildDashboard | null): SyllabusStatus[] {
  const skills = dashboard?.skills ?? [];
  const mastered = skills.filter((skill) => skill.learning_state === "INDEPENDENT_MASTERY").length;
  const inProgress = skills.filter((skill) =>
    ["INDEPENDENT_PROGRESS", "ASSISTED_SUCCESS"].includes(skill.learning_state),
  ).length;
  return [
    { status: "Mastered", count: mastered },
    { status: "In Progress", count: inProgress },
    { status: "Not Started", count: Math.max(skills.length - mastered - inProgress, 0) },
  ];
}

function deriveMisconceptions(dashboard: ChildDashboard | null): MisconceptionItem[] {
  return (dashboard?.support_areas ?? []).map((area, index) => ({
    id: `${area.code}-${index}`,
    topicName: area.name,
    misconception: `This learning pattern was observed ${area.occurrence_count} ${
      area.occurrence_count === 1 ? "time" : "times"
    } and may need another independent check.`,
    flaggedAt: new Date().toISOString(),
    status: "Needs Review" as const,
    suggestion:
      "Ask the learner to explain their reasoning aloud. Use a simpler example and questions that reveal the next step instead of supplying the answer.",
  }));
}

function makeStudentSummary(
  child: ChildSummary,
  progress: ProgressStudentApi | undefined,
  dashboard: ChildDashboard | null,
  useDemoFallback: boolean,
): StudentSummary {
  const syllabus = deriveSyllabus(dashboard);
  const topicsMastered = syllabus.find((item) => item.status === "Mastered")?.count ?? 0;
  const totalTopics = syllabus.reduce((sum, item) => sum + item.count, 0);
  const evidenceMastery =
    progress && progress.attempts > 0
      ? Math.round((progress.correct_attempts / progress.attempts) * 100)
      : 0;
  const backendMisconceptions = deriveMisconceptions(dashboard);

  return {
    studentId: child.id,
    displayName: child.first_name,
    gradeLevel: child.grade_level,
    totalLearningMinutes: useDemoFallback ? 218 : 0,
    learningTimeTrend: useDemoFallback ? 15 : null,
    topicsMastered: topicsMastered || (useDemoFallback ? 12 : 0),
    totalTopics: totalTopics || (useDemoFallback ? 18 : 0),
    masteryScore: Math.round((progress?.average_mastery ?? evidenceMastery / 100) * 100),
    masteryTrend: useDemoFallback ? 6 : null,
    activeMisconceptions:
      backendMisconceptions.length || (useDemoFallback ? demoMisconceptions.length : 0),
    dailyMetrics: useDemoFallback ? demoDailyMetrics : [],
    syllabus:
      totalTopics > 0
        ? syllabus
        : useDemoFallback
          ? [
              { status: "Mastered", count: 12 },
              { status: "In Progress", count: 4 },
              { status: "Not Started", count: 2 },
            ]
          : syllabus,
    misconceptions:
      backendMisconceptions.length > 0
        ? backendMisconceptions
        : useDemoFallback
          ? demoMisconceptions
          : [],
  };
}

function formatLearningTime(minutes: number): string {
  if (!minutes) return "Not available";
  const hours = minutes / 60;
  return `${hours.toFixed(hours >= 10 ? 0 : 1)} hrs this week`;
}

export default function ParentProgressDashboard({
  unlockToken,
  children,
  selectedStudentId,
  onStudentChange,
}: ParentProgressDashboardProps) {
  const [progress, setProgress] = useState<ProgressSummaryApi | null>(null);
  const [childDashboard, setChildDashboard] = useState<ChildDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [usingDemoFallback, setUsingDemoFallback] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!unlockToken || !selectedStudentId) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError("");

    Promise.all([
      api<ProgressSummaryApi>("/parents/progress-summary", {
        headers: { "X-Parent-Unlock": unlockToken },
      }),
      api<ChildDashboard>(`/parents/children/${selectedStudentId}/dashboard`, {
        headers: { "X-Parent-Unlock": unlockToken },
      }),
    ])
      .then(([summary, dashboard]) => {
        if (cancelled) return;
        setProgress(summary);
        setChildDashboard(dashboard);
        const selected = summary.students.find((item) => item.student_id === selectedStudentId);
        const lacksTimeSeries = !selected || selected.sessions_started === 0;
        setUsingDemoFallback(lacksTimeSeries);
      })
      .catch((reason: unknown) => {
        if (cancelled) return;
        if (reason instanceof ApiError && reason.status === 403) {
          setError("Parent access expired. Enter your PIN again.");
          setUsingDemoFallback(false);
        } else {
          setError("Live analytics are temporarily unavailable. Preview data is shown below.");
          setUsingDemoFallback(true);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedStudentId, unlockToken]);

  const child = children.find((item) => item.id === selectedStudentId) ?? children[0];
  const selectedProgress = progress?.students.find(
    (item) => item.student_id === selectedStudentId,
  );

  const summary = useMemo(
    () =>
      child
        ? makeStudentSummary(child, selectedProgress, childDashboard, usingDemoFallback)
        : null,
    [child, selectedProgress, childDashboard, usingDemoFallback],
  );

  if (!summary) return null;

  const activityData =
    summary.dailyMetrics.length > 0
      ? summary.dailyMetrics
      : demoDailyMetrics.map((item) => ({ ...item, minutes: 0, masteryScore: summary.masteryScore }));

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-dashboard sm:p-5">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-indigo-600">
              Parent progress
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950">
              {summary.displayName}&apos;s learning snapshot
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Grade {summary.gradeLevel} · A quick view of progress, practice, and support areas.
            </p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
            <div className="min-w-52">
              <label
                htmlFor="parent-progress-student"
                className="m-0 text-xs font-semibold text-slate-600"
              >
                Student
              </label>
              <select
                id="parent-progress-student"
                value={selectedStudentId}
                onChange={(event) => onStudentChange(event.target.value)}
                className="mt-1 min-h-11 rounded-xl border-slate-200 bg-slate-50 px-3 text-sm font-medium"
              >
                {children.map((student) => (
                  <option key={student.id} value={student.id}>
                    {student.first_name} · Grade {student.grade_level}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="button"
              onClick={() => window.print()}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
            >
              <Download size={16} />
              Save weekly PDF
            </button>
          </div>
        </div>
      </section>

      {(usingDemoFallback || error) && (
        <div
          className={`rounded-xl border px-4 py-3 text-sm ${
            error && !usingDemoFallback
              ? "border-rose-200 bg-rose-50 text-rose-800"
              : "border-indigo-200 bg-indigo-50 text-indigo-800"
          }`}
          role="status"
        >
          {error || "Some chart fields are not yet supplied by the live API. Clearly labeled preview data fills those visualization-only gaps."}
        </div>
      )}

      {loading ? (
        <div className="grid min-h-64 place-items-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-500">
          Loading parent analytics…
        </div>
      ) : (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Total learning time"
              value={formatLearningTime(summary.totalLearningMinutes)}
              helper="Active tutoring time in the last 7 days"
              trend={summary.learningTimeTrend}
              accent="indigo"
              icon={<Clock size={21} />}
            />
            <StatCard
              label="Topics mastered"
              value={`${summary.topicsMastered} / ${summary.totalTopics || "—"}`}
              helper="Syllabus topics with independent mastery evidence"
              accent="emerald"
              icon={<CheckCircle2 size={21} />}
            />
            <StatCard
              label="Current mastery"
              value={summary.masteryScore ? `${summary.masteryScore}%` : "Building evidence"}
              helper="Average demonstrated retention from available evidence"
              trend={summary.masteryTrend}
              accent="slate"
              icon={<TrendingUp size={21} />}
            />
            <StatCard
              label="Active misconceptions"
              value={`${summary.activeMisconceptions}`}
              helper="Learning patterns currently needing review"
              accent="amber"
              icon={<AlertTriangle size={21} />}
            />
          </section>

          <section className="grid gap-6 xl:grid-cols-[minmax(0,1.8fr)_minmax(300px,0.8fr)]">
            <ActivityChart data={activityData} />
            <SyllabusProgressDonut data={summary.syllabus} />
          </section>

          <MisconceptionList items={summary.misconceptions} />

          <section className="flex flex-col justify-between gap-4 rounded-2xl bg-slate-950 p-5 text-white sm:flex-row sm:items-center">
            <div className="flex gap-3">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white/10">
                <BookOpen size={20} />
              </span>
              <div>
                <h2 className="font-semibold">A two-minute weekly check-in</h2>
                <p className="mt-1 max-w-2xl text-sm text-slate-300">
                  Focus on independent mastery and one active support area. The dashboard intentionally
                  hides technical tutoring logs and raw learner conversations.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => window.print()}
              className="inline-flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-xl bg-white px-4 text-sm font-semibold text-slate-900 hover:bg-slate-100"
            >
              <Download size={16} />
              Export summary
            </button>
          </section>
        </>
      )}
    </div>
  );
}
