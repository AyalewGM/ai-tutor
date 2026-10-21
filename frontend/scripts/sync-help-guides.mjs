// Public help articles are generated from the repository source of truth.
// Usage (repository root): node frontend/scripts/sync-help-guides.mjs [--check]
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const entries = [
  ["welcome", "welcome.md", "Start here", "A tour of Mihur and how its learning approach works."],
  ["parent-first-day", "parent-first-day.md", "Parents", "Create your account, add learners and share private practice links."],
  ["student-first-session", "student-first-session.md", "Students", "Your first Mihur practice session, step by step."],
  ["progress-and-mastery", "progress-and-mastery.md", "How Mihur teaches", "Guided help, conceptual learning and independent mastery evidence."],
  ["privacy-and-faq", "privacy-and-faq.md", "Safety & FAQs", "Private links, family controls, privacy and common questions."],
];
const guides = entries.map(([slug, filename, audience, summary]) => {
  const body = readFileSync(path.join(root, "docs/user-guides", filename), "utf8");
  const title = body.match(/^# (.+)$/m)?.[1];
  if (!title) throw new Error(`Guide is missing a primary heading: ${filename}`);
  if (!body.endsWith("\n")) throw new Error(`Guide requires a trailing newline: ${filename}`);
  return { slug, title, audience, summary, body };
});
const target = path.join(root, "frontend/src/help/guides.generated.json");
const expected = JSON.stringify({ schemaVersion: 1, guides }, null, 2) + "\n";
if (process.argv.includes("--check")) {
  if (readFileSync(target, "utf8") !== expected) {
    throw new Error("Help Center content is not synchronized. Run: node frontend/scripts/sync-help-guides.mjs");
  }
  process.stdout.write("Help Center source parity: PASS\n");
} else {
  writeFileSync(target, expected, "utf8");
  process.stdout.write("Generated Help Center content from docs/user-guides\n");
}
