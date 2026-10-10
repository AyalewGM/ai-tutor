import { useMemo, useState, type FormEvent } from "react";
import { buildIntegerTask, checkIntegerAnswer, socraticIntegerPrompts } from "./integerPractice";

/** Independent assessments must not mount instructional controls or reveal generated keys. */
export function GuidedIntegerNumberLine({seed = 17, independentAssessment = false}: {
  seed?: number; independentAssessment: boolean;
}) {
  if (independentAssessment) return null;
  return <IntegerActivity key={seed} seed={seed} />;
}

const control = "rounded border px-3 py-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2";

function IntegerActivity({seed}: {seed: number}) {
  const [offset, setOffset] = useState(0);
  const task = useMemo(() => buildIntegerTask((seed + offset) % 2147483648), [seed, offset]);
  const prompts = useMemo(() => socraticIntegerPrompts(task), [task]);
  const [position, setPosition] = useState(task.a);
  const [hint, setHint] = useState(0);
  const [response, setResponse] = useState("");
  const [feedback, setFeedback] = useState("");
  const [taskKey, setTaskKey] = useState(task.prompt);
  if (taskKey !== task.prompt) {
    setTaskKey(task.prompt);
    setPosition(task.a);
    setHint(0);
    setResponse("");
    setFeedback("");
  }
  const min = -20;
  const max = 20;
  const points = Array.from({length: max - min + 1}, (_, i) => i + min);
  const move = (delta:number) => setPosition(p => Math.max(min, Math.min(max, p + delta)));

  const travelled = position - task.a;
  const travelledText = travelled === 0
    ? `You are still at the start, ${task.a}.`
    : `You are at ${position}, ${Math.abs(travelled)} units ${travelled > 0 ? "right" : "left"} of your start at ${task.a}.`;

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const check = checkIntegerAnswer(task, response);
    if (!check.correct) {
      setFeedback(position === task.answer
        ? `Your marker already shows the answer. Compare it with what you typed. ${check.guidance}`
        : check.guidance);
      return;
    }
    setFeedback(position === task.answer
      ? "Your sum is correct, and your marker walk confirms it. Explain your number-line strategy."
      : "Your sum is correct. Walk the move on the line to see why it is true.");
  };

  return <section aria-label="Guided integer number line" data-mve-family="integer-addition"
    className="rounded-lg border p-4 space-y-3">
    <h3 className="font-semibold">Explore adding signed integers</h3>
    <p>Worked practice, separate from independent assessment: {task.prompt}</p>
    <p className="text-sm">Start at {task.a}. Move by the second number; use the controls or keyboard-accessible buttons.</p>
    <svg role="img" aria-label={`Number line from ${min} to ${max}; starting at ${task.a}, current position ${position}`}
      viewBox="0 0 620 105" className="w-full">
      <line x1="12" x2="608" y1="48" y2="48" stroke="currentColor" strokeWidth="2"/>
      {points.map(n => {
        const x = 12 + (n - min) * 596 / (max - min);
        return <g key={n}><line x1={x} x2={x} y1="42" y2="54" stroke="currentColor"/>
          {(n % 2 === 0 || n === task.a || n === position) &&
            <text x={x} y="76" textAnchor="middle" fontSize="11" fill="currentColor">{n}</text>}
          {n === task.a && <circle cx={x} cy="48" r="6" fill="#2563eb"/>}
          {n === position && <circle cx={x} cy="48" r="4" fill="#ea580c"/>}
        </g>;
      })}
    </svg>
    <div className="flex gap-2">
      <button type="button" className={control} onClick={() => move(-1)} disabled={position <= min}>Move left 1</button>
      <button type="button" className={control} onClick={() => move(1)} disabled={position >= max}>Move right 1</button>
      <button type="button" className={control} onClick={() => setPosition(task.a)}>Reset</button>
    </div>
    <p role="status" aria-live="polite">{travelledText} Starting position: {task.a}.</p>
    <div className="flex gap-2">
      <button type="button" className={control}
        onClick={() => setHint(i => Math.min(i + 1, prompts.length))} disabled={hint >= prompts.length}>
        Ask a guiding question
      </button>
      <button type="button" className={control} onClick={() => setOffset(o => o + 1)}>
        Try another task
      </button>
    </div>
    {hint > 0 && <p aria-live="polite">{prompts[hint - 1]}</p>}
    <form onSubmit={submit} className="space-y-2">
      <label className="block">What is the sum?
        <input type="text" inputMode="numeric" className="ml-2 rounded border p-2"
          value={response} onChange={e => setResponse(e.target.value)} />
      </label>
      <button type="submit" className={control}>Check my reasoning</button>
    </form>
    <p aria-live="polite" role="status">{feedback}</p>
  </section>;
}
