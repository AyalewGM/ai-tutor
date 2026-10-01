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

function emptyWeekMetrics(): DailyMetric[] {
  const labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  return Array.from({ length: 7 }, (_, index) => {
    const day = new Date();
    day.setDate(day.getDate() - (6 - index));
    return {
      date: day.toISOString().slice(0, 10),
      label: labels[day.getDay()],
      minutes: 0,
      masteryScore: 0,
    };
  });
}

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
): StudentSummary {
  const syllabus = deriveSyllabus(dashboard);
  const gradeSummary = dashboard?.grade_level_summary ?? null;
  const topicsMastered = gradeSummary?.skills_mastered
    ?? syllabus.find((item) => item.status === "Mastered")?.count
    ?? 0;
  const totalTopics = gradeSummary?.skills_total
    ?? syllabus.reduce((sum, item) => sum + item.count, 0);
  const evidenceMastery =
    progress && progress.attempts > 0
      ? Math.round((progress.correct_attempts / progress.attempts) * 100)
      : 0;
  const backendMisconceptions = deriveMisconceptions(dashboard);

  return {
    studentId: child.id,
    displayName: child.first_name,
    gradeLevel: child.grade_level,
    totalLearningMinutes: gradeSummary?.minutes_last_7_days ?? 0,
    learningTimeTrend: null,
    topicsMastered,
    totalTopics,
    masteryScore: Math.round(
      gradeSummary?.mastery_percent
        ?? (progress?.average_mastery ?? evidenceMastery / 100) * 100,
    ),
    masteryTrend: null,
    activeMisconceptions: backendMisconceptions.length,
    dailyMetrics: [],
    syllabus,
    misconceptions: backendMisconceptions,
  };
}

function formatLearningTime(minutes: number): string {
  if (!minutes) return "0 min this week";
  if (minutes < 60) return `${minutes} min this week`;
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
        setUsingDemoFallback(!selected || selected.sessions_started === 0);
      })
      .catch((reason: unknown) => {
        if (cancelled) return;
        if (reason instanceof ApiError && reason.status === 403) {
          setError("Parent access expired. Enter your PIN again.");
          setUsingDemoFallback(false);
        } else {
          setError("Live analytics are temporarily unavailable.");
          setUsingDemoFallback(false);
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
        ? makeStudentSummary(child, selectedProgress, childDashboard)
        : null,
    [child, selectedProgress, childDashboard],
  );

  if (!summary) return null;

  const gradeSummary = childDashboard?.grade_level_summary ?? null;
  const activityData =
    summary.dailyMetrics.length > 0 ? summary.dailyMetrics : emptyWeekMetrics();

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
          {error || "No practice sessions recorded for this learner yet — the charts and stats fill in as they work."}
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

          {gradeSummary && (
            <section className="grid gap-6 xl:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-dashboard">
                <h2 className="text-base font-semibold text-slate-950">
                  {gradeSummary.curriculum_name ?? "Curriculum"} coverage
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  {gradeSummary.skills_mastered} of {gradeSummary.skills_total} skills
                  independently mastered
                </p>
                <div className="mt-4 space-y-3">
                  {gradeSummary.strands.map((strand) => (
                    <div key={strand.strand}>
                      <div className="flex items-baseline justify-between text-sm">
                        <span className="font-medium text-slate-700">{strand.strand}</span>
                        <span className="text-xs text-slate-500">
                          {strand.mastered}/{strand.total} mastered
                          {strand.in_progress > 0 && ` · ${strand.in_progress} in progress`}
                        </span>
                      </div>
                      <div className="mt-1 h-2 rounded-full bg-slate-100">
                        <div
                          className="h-2 rounded-full bg-emerald-500"
                          style={{
                            width: `${strand.total ? (100 * strand.mastered) / strand.total : 0}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-dashboard">
                <h2 className="text-base font-semibold text-slate-950">This week</h2>
                <p className="mt-1 text-sm text-slate-500">
                  {gradeSummary.sessions_last_7_days} practice{" "}
                  {gradeSummary.sessions_last_7_days === 1 ? "session" : "sessions"} ·{" "}
                  {gradeSummary.minutes_last_7_days} min
                </p>
                {gradeSummary.trouble_spots.length > 0 ? (
                  <>
                    <h3 className="mt-4 text-xs font-semibold uppercase tracking-wide text-amber-600">
                      Trouble spots
                    </h3>
                    <ul className="mt-2 flex flex-wrap gap-2">
                      {gradeSummary.trouble_spots.map((spot) => (
                        <li
                          key={spot}
                          className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-800"
                        >
                          {spot}
                        </li>
                      ))}
                    </ul>
                  </>
                ) : (
                  <p className="mt-4 text-sm text-slate-500">
                    No trouble spots flagged — independent work is going well.
                  </p>
                )}
              </div>
            </section>
          )}

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
