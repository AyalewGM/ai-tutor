import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import {
  ArrowLeft, ArrowRight, BookOpen, GraduationCap, HeartHandshake,
  HelpCircle, House, LockKeyhole, Search, ShieldCheck, Users,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import Brand from "../components/Brand";
import data from "../help/guides.generated.json";

type Guide = (typeof data.guides)[number];
const guides: Guide[] = data.guides;
const categories = [
  { slug: "welcome", icon: House },
  { slug: "parent-first-day", icon: Users },
  { slug: "student-first-session", icon: GraduationCap },
  { slug: "progress-and-mastery", icon: BookOpen },
  { slug: "privacy-and-faq", icon: ShieldCheck },
] as const;

function headingId(children: React.ReactNode): string {
  const label = String(children);
  return label.toLowerCase().normalize("NFKD").replace(/[^a-z0-9\s-]/g, "").trim().replace(/\s+/g, "-");
}

function GuideArticle({ guide }: { guide: Guide }) {
  return (
    <article aria-label={guide.title} className="min-w-0">
      <p className="text-sm font-semibold uppercase tracking-widest text-primary">{guide.audience}</p>
      <p className="mb-5 mt-1 text-sm text-muted-foreground">{guide.summary}</p>
      <div className="space-y-4 text-base leading-7 text-foreground">
        <ReactMarkdown
          components={{
            h1: ({ children }) => <h1 className="mb-5 text-3xl font-bold leading-tight tracking-tight sm:text-4xl">{children}</h1>,
            h2: ({ children }) => <h2 id={headingId(children)} className="scroll-mt-24 pt-6 text-xl font-semibold tracking-tight sm:text-2xl">{children}</h2>,
            h3: ({ children }) => <h3 id={headingId(children)} className="scroll-mt-24 pt-4 text-lg font-semibold">{children}</h3>,
            p: ({ children }) => <p className="leading-7">{children}</p>,
            ul: ({ children }) => <ul className="list-disc space-y-2 pl-6">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal space-y-2 pl-6">{children}</ol>,
            li: ({ children }) => <li className="pl-1">{children}</li>,
            strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
            blockquote: ({ children }) => <blockquote className="border-l-4 border-primary/40 pl-4 italic text-muted-foreground">{children}</blockquote>,
            a: ({ href, children }) =>
              href?.startsWith("/") && !href.startsWith("//")
                ? <Link to={href} className="font-medium text-primary underline underline-offset-4 hover:text-primary/80 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2">{children}</Link>
                : <a href={href} rel="noopener noreferrer" className="text-primary underline underline-offset-4">{children}</a>,
          }}
        >{guide.body}</ReactMarkdown>
      </div>
    </article>
  );
}

export default function HelpCenter() {
  const { slug } = useParams();
  const location = useLocation();
  const [query, setQuery] = useState("");
  const guide = slug ? guides.find((item) => item.slug === slug) : undefined;
  const filtered = useMemo(() => {
    const term = query.trim().toLocaleLowerCase();
    return term
      ? guides.filter((item) => `${item.title} ${item.summary} ${item.body}`.toLocaleLowerCase().includes(term))
      : guides;
  }, [query]);

  useEffect(() => {
    if (!slug || !location.hash) return;
    const id = decodeURIComponent(location.hash.slice(1));
    const frame = window.requestAnimationFrame(() => document.getElementById(id)?.scrollIntoView());
    return () => window.cancelAnimationFrame(frame);
  }, [slug, location.hash]);

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4">
          <Link to="/" aria-label="Mihur home"><Brand size="sm" /></Link>
          <nav aria-label="Help navigation" className="flex items-center gap-3 text-sm font-medium">
            <Link to="/help" aria-current={!slug ? "page" : undefined} className="text-primary hover:underline">Help Center</Link>
            <Link to="/privacy" className="text-muted-foreground hover:text-foreground">Privacy</Link>
            <Link to="/login" className="rounded-lg border border-border px-3 py-2 hover:bg-secondary">Sign in</Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-10">
        {!slug ? (
          <>
            <div className="max-w-3xl">
              <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-widest text-primary">
                <HeartHandshake size={18} aria-hidden="true" /> Mihur Help & Learning Guide
              </p>
              <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">Find your way with Mihur</h1>
              <p className="mt-3 text-muted-foreground">Friendly guides for families, learners and educators. No sign-in needed to read.</p>
              <label htmlFor="help-search" className="mt-7 block text-sm font-medium">Search the Help Center</label>
              <div className="relative mt-2">
                <Search aria-hidden="true" className="pointer-events-none absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
                <input
                  id="help-search"
                  type="search"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Try: parent PIN, hints, practice link, privacy"
                  className="w-full rounded-xl border border-input bg-card py-3 pl-11 pr-4 text-foreground outline-offset-2 focus-visible:outline-2 focus-visible:outline-primary"
                />
              </div>
            </div>
            <section aria-label="Help articles" className="mt-9 grid gap-4 md:grid-cols-2">
              {filtered.map((item) => {
                const category = categories.find((c) => c.slug === item.slug);
                const Icon = category?.icon ?? HelpCircle;
                return (
                  <Link key={item.slug} to={`/help/${item.slug}`} className="group rounded-xl border border-border bg-card p-6 transition-shadow hover:shadow-dashboard focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">
                    <Icon aria-hidden="true" className="h-6 w-6 text-primary" />
                    <span className="mt-3 block text-xs font-semibold uppercase tracking-wider text-muted-foreground">{item.audience}</span>
                    <h2 className="mt-2 text-lg font-semibold">{item.title}</h2>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.summary}</p>
                    <span className="mt-4 flex items-center gap-2 text-sm font-semibold text-primary">Read guide <ArrowRight size={16} aria-hidden="true" /></span>
                  </Link>
                );
              })}
            </section>
            {!filtered.length && <p role="status" className="mt-6 text-muted-foreground">No matching guides. Try a different word.</p>}
            <section className="mt-8 rounded-xl border border-border bg-secondary/50 p-5" aria-label="For educators">
              <div className="flex items-center gap-2 font-semibold"><BookOpen aria-hidden="true" size={20} /> For educators</div>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">Read the teaching approach now. Dedicated classroom and educator-account guides will follow only when those experiences have been verified.</p>
              <Link className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-primary underline-offset-4 hover:underline" to="/help/progress-and-mastery">How Mihur teaches <ArrowRight size={16} /></Link>
            </section>
          </>
        ) : guide ? (
          <>
            <Link to="/help" className="mb-7 inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"><ArrowLeft size={16} aria-hidden="true" /> All help articles</Link>
            <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_250px]">
              <GuideArticle guide={guide} />
              <aside className="self-start rounded-xl border border-border bg-card p-5 lg:sticky lg:top-6" aria-label="Other help articles">
                <h2 className="font-semibold">Explore other guides</h2>
                <nav className="mt-3 flex flex-col gap-3 text-sm">
                  {guides.filter((item) => item.slug !== guide.slug).map((item) =>
                    <Link key={item.slug} className="text-primary underline-offset-4 hover:underline" to={`/help/${item.slug}`}>{item.title}</Link>,
                  )}
                </nav>
              </aside>
            </div>
          </>
        ) : (
          <div role="alert" className="max-w-2xl">
            <HelpCircle className="h-8 w-8 text-primary" aria-hidden="true" />
            <h1 className="mt-4 text-2xl font-bold">We couldn't find that guide</h1>
            <p className="mt-2 text-muted-foreground">That address may be out of date.</p>
            <Link to="/help" className="mt-4 inline-flex items-center gap-2 text-primary underline"><ArrowLeft size={16} /> Back to Help Center</Link>
          </div>
        )}
      </main>
      <footer className="border-t border-border bg-card">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-6 text-sm text-muted-foreground">
          <span>Understanding first. Mastery follows.</span>
          <div className="flex gap-4">
            <Link className="hover:underline" to="/help">Help Center</Link>
            <Link className="hover:underline" to="/privacy">Privacy</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
