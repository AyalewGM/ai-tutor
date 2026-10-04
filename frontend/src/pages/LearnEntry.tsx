import { FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BookOpen, ChevronDown, ClipboardCheck, Play, UserPlus, Compass } from "lucide-react";
import { ApiError, api, post } from "../api";
import NavBar from "../components/NavBar";
import Avatar from "../components/Avatar";
import AvatarPicker from "../components/AvatarPicker";
import LearnPanel from "../components/LearnPanel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { CurriculumChoice, DiagnosticOut, LearnerChoice, RegionsOut, SessionOut, SkillChoice } from "../types";

export default function LearnEntry() {
  const [learners, setLearners] = useState<LearnerChoice[]>([]);
  const [curricula, setCurricula] = useState<CurriculumChoice[]>([]);
  const [skills, setSkills] = useState<SkillChoice[]>([]);
  const [learnerId, setLearnerId] = useState("");
  const [skillId, setSkillId] = useState("");
  const [firstName, setFirstName] = useState("");
  const [curriculumId, setCurriculumId] = useState("");
  const [newAvatarId, setNewAvatarId] = useState("avatar-1");
  const [avatarPickerOpen, setAvatarPickerOpen] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [skillsLoading, setSkillsLoading] = useState(false);
  const [topicFilter, setTopicFilter] = useState("All topics");
  const [lessonOpen, setLessonOpen] = useState(false);
  const [regions, setRegions] = useState<RegionsOut | null>(null);
  const [regionPickerOpen, setRegionPickerOpen] = useState(false);
  const [regionSaving, setRegionSaving] = useState(false);
  const [pendingCountry, setPendingCountry] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    api<LearnerChoice[]>("/onboarding/learners")
      .then((rows) => { setLearners(rows); if (rows.length === 1) setLearnerId(rows[0].id); })
      .catch(() => setError("Could not load learners"));
    api<CurriculumChoice[]>("/onboarding/curricula").then(setCurricula).catch(() => {});
    api<RegionsOut>("/onboarding/regions")
      .then((out) => {
        setRegions(out);
        if (!out.family) setRegionPickerOpen(true);
      })
      .catch(() => {});
  }, []);

  const familyCountry = regions?.family?.country_code ?? "";
  const familyRegion = regions?.family?.region_code ?? "";
  const selectedCountry = regions?.countries.find((c) => c.code === familyCountry);
  const selectedRegion = selectedCountry?.regions.find((r) => r.code === familyRegion);
  const regionCovered = selectedRegion?.has_curriculum ?? false;

  async function saveRegion(countryCode: string, regionCode: string) {
    if (!countryCode || !regionCode) return;
    setRegionSaving(true);
    setError("");
    try {
      await api("/parents/region", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ country_code: countryCode, region_code: regionCode }),
      });
      setRegions((current) =>
        current ? { ...current, family: { country_code: countryCode, region_code: regionCode } } : current,
      );
      setRegionPickerOpen(false);
      setCurriculumId("");
      const rows = await api<CurriculumChoice[]>("/onboarding/curricula");
      setCurricula(rows);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save your state");
    } finally {
      setRegionSaving(false);
    }
  }

  useEffect(() => {
    setSkills([]); setSkillId("");
    if (!learnerId) return;
    setSkillsLoading(true);
    api<SkillChoice[]>(`/onboarding/learners/${learnerId}/skills`)
      .then(setSkills)
      .catch(() => setError("Could not load skills"))
      .finally(() => setSkillsLoading(false));
  }, [learnerId]);

  async function addLearner(event: FormEvent) {
    event.preventDefault(); setError(""); setNotice("");
    try {
      const created = await post<LearnerChoice & { id: string }>("/onboarding/learners", { first_name: firstName, curriculum_id: curriculumId, avatar_id: newAvatarId });
      const rows = await api<LearnerChoice[]>("/onboarding/learners");
      setLearners(rows); setLearnerId(created.id); setFirstName("");
      setNotice(`${created.first_name ?? "Learner"} is ready.`);
    } catch (err) { setError(err instanceof ApiError ? err.message : "Could not add learner"); }
  }

  async function startSession(event: FormEvent) {
    event.preventDefault(); setError("");
    try {
      const session = await post<SessionOut>("/adaptive-tutor/sessions", { student_id: learnerId, skill_id: skillId });
      navigate(`/learn/${session.session_id}`);
    } catch (err) { setError(err instanceof ApiError ? err.message : "Could not start session"); }
  }

  async function startPlacement() {
    setError("");
    // Anchor on the selected topic, or the most advanced ready skill — the
    // diagnostic descends the prerequisite graph until the learner is solid.
    const anchor = selectedSkill ?? [...skills].reverse().find((skill) => skill.content_ready);
    if (!anchor) return;
    try {
      const diagnostic = await post<DiagnosticOut>("/diagnostics/sessions", {
        student_id: learnerId,
        target_skill_id: anchor.id,
      });
      navigate(`/diagnostic/${diagnostic.session_id}?learner=${learnerId}`, {
        state: { diagnostic },
      });
    } catch (err) { setError(err instanceof ApiError ? err.message : "Could not start placement check"); }
  }

  async function changeAvatar(avatarId: string) {
    if (!learnerId) return;
    try {
      const updated = await api<LearnerChoice>(`/onboarding/learners/${learnerId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ avatar_id: avatarId }),
      });
      setLearners((rows) => rows.map((row) => (row.id === updated.id ? updated : row)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update avatar");
    }
  }

  const selectedLearner = learners.find((learner) => learner.id === learnerId);
  const selectedSkill = skills.find((skill) => skill.id === skillId);
  const readyCount = useMemo(() => skills.filter((skill) => skill.content_ready).length, [skills]);
  const topicFor = (skill: SkillChoice) => {
    const text = `${skill.code} ${skill.name}`.toLowerCase();
    if (/fraction|decimal/.test(text)) return "Fractions & decimals";
    if (/geometr|shape|angle|coordinate|area|perimeter|volume|line/.test(text)) return "Geometry";
    if (/measure|length|time|money|clock/.test(text)) return "Measurement & time";
    if (/graph|data|plot|table/.test(text)) return "Data & graphs";
    if (/pattern|equation|algebra|expression|distribut|linear|variable/.test(text)) return "Patterns & algebra";
    return "Numbers & operations";
  };
  const topics = useMemo(
    () => ["All topics", ...Array.from(new Set(skills.map(topicFor)))],
    [skills],
  );
  const visibleSkills = useMemo(
    () => topicFilter === "All topics" ? skills : skills.filter((skill) => topicFor(skill) === topicFilter),
    [skills, topicFilter],
  );

  return (
    <div className="min-h-screen bg-background">
      <NavBar />
      <main className="mx-auto max-w-6xl px-4 py-8">
        {/* Hero */}
        <div className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-widest text-primary">Learner home</p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight">
            {selectedLearner ? `Ready to learn, ${selectedLearner.first_name}?` : "Choose your learning path"}
          </h1>
          <p className="mt-1 text-muted-foreground">
            Continue learning or explore a topic you want to practice today.
          </p>
        </div>

        {/* Learner picker */}
        <Card className="mb-6">
          <CardContent className="flex flex-col gap-4 pt-6 sm:flex-row sm:items-end">
            <div className="flex-1 space-y-1.5">
              <Label htmlFor="learner">Who is learning?</Label>
              <Select value={learnerId} onValueChange={setLearnerId}>
                <SelectTrigger id="learner">
                  <SelectValue placeholder="Select learner" />
                </SelectTrigger>
                <SelectContent>
                  {learners.map((learner) => (
                    <SelectItem key={learner.id} value={learner.id}>
                      <span className="flex items-center gap-2">
                        <Avatar avatarId={learner.avatar_id ?? "avatar-1"} size={22} />
                        {learner.first_name} — {learner.curriculum_code}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Each learner stays connected to their exact curriculum and version.
              </p>
            </div>
            {selectedLearner && (
              <div className="flex flex-col items-start gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setAvatarPickerOpen((open) => !open)}
                    aria-expanded={avatarPickerOpen}
                    aria-label="Change avatar"
                    title="Change avatar"
                    className="rounded-full transition-transform hover:scale-105"
                  >
                    <Avatar avatarId={selectedLearner.avatar_id ?? "avatar-1"} size={44} />
                  </button>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="secondary">{selectedLearner.curriculum_code}</Badge>
                    <Badge variant="secondary">{selectedLearner.curriculum_version}</Badge>
                    {selectedLearner.jurisdiction && <Badge variant="secondary">{selectedLearner.jurisdiction}</Badge>}
                    <Badge variant="outline">{readyCount} ready skills</Badge>
                  </div>
                </div>
                {avatarPickerOpen && (
                  <div className="rounded-xl border border-border bg-card p-3">
                    <p className="mb-2 text-xs font-medium text-muted-foreground">
                      Pick {selectedLearner.first_name}&apos;s look
                    </p>
                    <AvatarPicker
                      value={selectedLearner.avatar_id ?? "avatar-1"}
                      onChange={(id) => {
                        changeAvatar(id);
                        setAvatarPickerOpen(false);
                      }}
                    />
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          {/* Explore Topics */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Compass className="h-5 w-5 text-primary" />
                  <CardTitle>Explore Topics</CardTitle>
                </div>
                {selectedSkill && <Badge>Selected</Badge>}
              </div>
              <CardDescription>
                Pick what you want to practice. Your progress is still earned from your work.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              {!learnerId && (
                <div className="rounded-lg border border-dashed border-border p-8 text-center">
                  <BookOpen className="mx-auto h-8 w-8 text-muted-foreground" />
                  <p className="mt-2 font-medium">Start by choosing a learner.</p>
                  <p className="text-sm text-muted-foreground">
                    We will show only skills assigned to that learner's curriculum.
                  </p>
                </div>
              )}
              {learnerId && skillsLoading && (
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                  {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-24" />)}
                </div>
              )}
              {learnerId && !skillsLoading && (
                <>
                  <div className="flex flex-wrap gap-2">
                    {topics.map((topic) => (
                      <button
                        key={topic}
                        type="button"
                        aria-pressed={topic === topicFilter}
                        onClick={() => setTopicFilter(topic)}
                        className={cn(
                          "rounded-full border px-4 py-1.5 text-sm font-medium transition-colors",
                          topic === topicFilter
                            ? "border-primary bg-primary text-primary-foreground"
                            : "border-border bg-card text-muted-foreground hover:bg-secondary",
                        )}
                      >
                        {topic}
                      </button>
                    ))}
                  </div>

                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {visibleSkills.map((skill) => (
                      <button
                        key={skill.id}
                        type="button"
                        data-testid="skill-choice"
                        disabled={!skill.content_ready}
                        aria-pressed={skill.id === skillId}
                        onClick={() => setSkillId(skill.id)}
                        className={cn(
                          "rounded-xl border p-4 text-left transition-all",
                          skill.id === skillId
                            ? "border-primary bg-primary/5 ring-2 ring-primary/30"
                            : "border-border bg-card hover:border-primary/40 hover:shadow-dashboard",
                          !skill.content_ready && "opacity-50",
                        )}
                      >
                        <span className="text-xs font-mono text-muted-foreground">{skill.code}</span>
                        <p className="mt-0.5 font-medium leading-snug">{skill.name}</p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {skill.content_ready ? "Ready to practice" : "Content in progress"}
                        </p>
                      </button>
                    ))}
                  </div>
                  {!visibleSkills.length && (
                    <div className="rounded-lg border border-dashed border-border p-8 text-center">
                      <p className="font-medium">No skills are available in this topic yet.</p>
                      <p className="text-sm text-muted-foreground">
                        This curriculum does not currently have learner-ready practice content.
                      </p>
                    </div>
                  )}
                </>
              )}

              {/* Learn this first — the selected skill's authored lesson */}
              {selectedSkill?.learn && (
                <div className="rounded-lg border border-accent/50 bg-accent/5">
                  <button
                    type="button"
                    onClick={() => setLessonOpen((o) => !o)}
                    aria-expanded={lessonOpen}
                    className="flex w-full items-center gap-2 px-4 py-2.5 text-sm font-semibold text-accent"
                  >
                    <BookOpen className="h-4 w-4 text-accent" />
                    Learn this first — how {selectedSkill.name} works
                    <ChevronDown
                      className={cn(
                        "ml-auto h-4 w-4 transition-transform",
                        lessonOpen && "rotate-180",
                      )}
                    />
                  </button>
                  {lessonOpen && (
                    <div className="border-t border-accent/30 px-4 py-3">
                      <LearnPanel learn={selectedSkill.learn} />
                    </div>
                  )}
                </div>
              )}

              {/* Start panel */}
              <form onSubmit={startSession} className="flex items-center justify-between gap-4 rounded-xl border border-border bg-secondary/50 p-4">
                <div className="min-w-0">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Your next session</p>
                  <p className="truncate font-semibold">{selectedSkill?.name ?? "Choose a skill to continue"}</p>
                </div>
                <Button type="submit" disabled={!learnerId || !skillId}>
                  <Play className="h-4 w-4" />
                  Start learning
                </Button>
              </form>

              <button
                type="button"
                onClick={startPlacement}
                disabled={!learnerId || !skills.some((skill) => skill.content_ready)}
                data-testid="placement-check"
                className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-primary/40 bg-primary/5 px-4 py-3 text-sm font-medium text-primary transition-colors hover:bg-primary/10 disabled:opacity-50"
              >
                <ClipboardCheck className="h-4 w-4" />
                {selectedSkill
                  ? `Not sure you're ready for ${selectedSkill.name}? Take a quick check`
                  : "Not sure where to start? Take a quick placement check"}
              </button>
            </CardContent>
          </Card>

          {/* Add learner */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <UserPlus className="h-5 w-5 text-primary" />
                <CardTitle>Add a learner</CardTitle>
              </div>
              <CardDescription>
                Use a short nickname or alias, not a full legal name. Then choose the exact curriculum.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={addLearner} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="firstName">Learner nickname</Label>
                  <Input
                    id="firstName"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    required
                    maxLength={32}
                    pattern="[A-Za-z0-9_-]+"
                    autoComplete="off"
                  />
                </div>
                {regions && (
                  <div className="space-y-1.5">
                    <Label>Your state or province</Label>
                    {regionPickerOpen ? (
                      <div className="grid grid-cols-2 gap-2">
                        <Select
                          value={pendingCountry}
                          onValueChange={(code) => {
                            setPendingCountry(code);
                          }}
                        >
                          <SelectTrigger aria-label="Country">
                            <SelectValue placeholder="Country" />
                          </SelectTrigger>
                          <SelectContent>
                            {regions.countries.map((country) => (
                              <SelectItem key={country.code} value={country.code}>
                                {country.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <Select
                          value=""
                          disabled={!pendingCountry || regionSaving}
                          onValueChange={(code) => saveRegion(pendingCountry, code)}
                        >
                          <SelectTrigger aria-label="State or province">
                            <SelectValue
                              placeholder={
                                pendingCountry ? "State / province" : "Pick a country first"
                              }
                            />
                          </SelectTrigger>
                          <SelectContent>
                            {regions.countries
                              .find((c) => c.code === pendingCountry)
                              ?.regions.map((region) => (
                                <SelectItem key={region.code} value={region.code}>
                                  {region.name}
                                  {!region.has_curriculum ? " (coming soon)" : ""}
                                </SelectItem>
                              ))}
                          </SelectContent>
                        </Select>
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={() => {
                          setPendingCountry(familyCountry);
                          setRegionPickerOpen(true);
                        }}
                        className="flex w-full items-center justify-between rounded-md border border-border bg-card px-3 py-2 text-sm hover:border-primary/40"
                      >
                        <span>
                          {selectedRegion?.name ?? familyRegion},{" "}
                          {selectedCountry?.name ?? familyCountry}
                        </span>
                        <span className="text-xs font-medium text-primary">Change</span>
                      </button>
                    )}
                  </div>
                )}
                <div className="space-y-1.5">
                  <Label htmlFor="curriculum">Exact curriculum</Label>
                  <Select value={curriculumId} onValueChange={setCurriculumId}>
                    <SelectTrigger id="curriculum">
                      <SelectValue placeholder="Select curriculum" />
                    </SelectTrigger>
                    <SelectContent>
                      {curricula.map((curriculum) => (
                        <SelectItem key={curriculum.id} value={curriculum.id}>
                          {curriculum.code}
                          {curriculum.grade_level ? ` — Grade ${curriculum.grade_level}` : ""}
                          {familyRegion && !regionCovered && curriculum.jurisdiction
                            ? ` · ${curriculum.jurisdiction}`
                            : ""}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {familyRegion && !regionCovered && selectedRegion && (
                    <p className="text-xs text-muted-foreground">
                      Mihur doesn't have a {selectedRegion.name} curriculum yet —
                      pick the closest grade-level fit.
                    </p>
                  )}
                </div>
                <div className="space-y-1.5">
                  <Label>Avatar</Label>
                  <AvatarPicker value={newAvatarId} onChange={setNewAvatarId} />
                </div>
                <Button type="submit" variant="secondary" className="w-full">Add learner</Button>
              </form>
              {notice && (
                <p className="mt-3 rounded-md bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700" role="status">
                  {notice}
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {error && (
          <p className="mt-6 rounded-md bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive" role="alert">
            {error}
          </p>
        )}
      </main>
    </div>
  );
}
