import MathText from "./MathText";
import type { LearnContent } from "../types";

export default function LearnPanel({ learn }: { learn: LearnContent }) {
  return (
    <div className="space-y-3">
      <MathText text={learn.summary} />
      {learn.examples.map((example, index) => (
        <div key={index} className="rounded-md bg-card p-3 text-sm">
          <p className="font-medium">
            Example {index + 1}: {example.title}
          </p>
          <ol className="mt-2 list-decimal space-y-1 pl-5">
            {example.steps.map((step, stepIndex) => (
              <li key={stepIndex}>
                <MathText text={step} />
              </li>
            ))}
          </ol>
          {example.answer && (
            <p className="mt-2 font-medium text-primary">
              Answer: <MathText text={example.answer} />
            </p>
          )}
        </div>
      ))}
      {(learn.key_terms?.length ?? 0) > 0 && (
        <div className="rounded-md bg-card p-3 text-sm">
          <p className="font-medium">Key words</p>
          <dl className="mt-2 space-y-1.5">
            {learn.key_terms!.map((item) => (
              <div key={item.term}>
                <dt className="inline font-semibold">{item.term}</dt>{" "}
                <dd className="inline text-muted-foreground">
                  — {item.definition}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      )}
      {(learn.watch_out?.length ?? 0) > 0 && (
        <div className="rounded-md border border-amber-300/60 bg-amber-50/50 p-3 text-sm dark:border-amber-500/30 dark:bg-amber-950/20">
          <p className="font-medium">Watch out for</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">
            {learn.watch_out!.map((item, i) => (
              <li key={i}>
                <MathText text={item} />
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
