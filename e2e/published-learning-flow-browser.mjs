/** Synthetic authenticated-stage UI protocol check; NOT Muse AT acceptance. */
import assert from "node:assert/strict";
import { mkdtemp, writeFile, rm } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { chromium } from "@playwright/test";
import { createServer } from "../frontend/node_modules/vite/dist/node/index.js";

const frontend = fileURLToPath(new URL("../frontend/", import.meta.url));
const dir = await mkdtemp(path.join(frontend, ".published-browser-"));
let server, browser;
const base = { independent_evidence_eligible: false, mastery_eligible: false, xp_earned: 0 };
const task = (mode, prompt) => ({ variant_id: "server-generated", mode, prompt });
const reply = (stage, extra = {}) => ({ ...base, stage, ...extra });
let authorized = false;
let recoverStage = "CONFIRM_REASONING";
let exactStage = 0;
let guidedCalls = 0;
try {
  await writeFile(path.join(dir, "index.html"),
    '<html lang="en"><body><main id="root"></main><script type="module" src="./entry.tsx"></script></body></html>');
  await writeFile(path.join(dir, "entry.tsx"), [
    'import React, { useState } from "react";',
    'import { createRoot } from "react-dom/client";',
    'import PublishedLearningRecovery from "/src/components/PublishedLearningRecovery";',
    'function Harness() {',
    ' const [active,setActive] = useState(false);',
    ' return <><button aria-pressed={active} onClick={() => setActive(true)}>Offer recovery</button>',
    ' {active && <PublishedLearningRecovery sessionId="session-1" problemId="source-1"',
    ' onUnavailable={() => setActive(false)} onClose={() => setActive(false)} />}</>;',
    '}',
    'createRoot(document.getElementById("root")!).render(<Harness />);',
  ].join("\n"));
  server = await createServer({ root: frontend, server: { host: "127.0.0.1", port: 0 } });
  await server.listen();
  const address = server.httpServer.address();
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ reducedMotion: "reduce" });
  const pageErrors = [];
  page.on("pageerror", error => pageErrors.push(error.message));
  await page.route("**/api/v1/adaptive-tutor/**", async route => {
    const req = route.request();
    const url = new URL(req.url());
    const endpoint = url.pathname;
    const data = req.method() === "POST" && !endpoint.endsWith("/start") ?
      JSON.parse(req.postData() || "{}") : {};
    const send = body => route.fulfill({
      status: 200, contentType: "application/json", body: JSON.stringify(body),
    });
    if (endpoint.endsWith("/published-recovery") && req.method() === "GET") {
      if (!authorized) return route.fulfill({ status: 409,
        contentType: "application/json", body: '{"detail":"Unavailable"}' });
      assert.equal(url.searchParams.get("problem_id"), "source-1");
      if (recoverStage === "GUIDED_RETEST") return send(reply("GUIDED_RETEST", {
        guided_retest_task: task("GUIDED", "Persisted guided retest") }));
      if (recoverStage === "INDEPENDENT_EXIT") return send(reply("INDEPENDENT_EXIT", {
        independent_task: task("INDEPENDENT", "Persisted independent task"), hints_allowed: false }));
      if (recoverStage === "MASTERY_VERIFICATION_FEEDBACK_ONLY") return send(reply(
        "MASTERY_VERIFICATION_FEEDBACK_ONLY", {
          verification_task: task("MASTERY", "Persisted verification task"), hints_allowed: false }));
      if (recoverStage === "COMPLETE_FEEDBACK_ONLY") return send(reply("COMPLETE_FEEDBACK_ONLY"));
      return send(reply("CONFIRM_REASONING", {
        problem_id: "source-1", prompt: "Why are the two sides equal?",
        choices: [{ id: "CHOICE_1", text: "One side only" }, { id: "CHOICE_2", text: "Same operation on both sides" }],
      }));
    }
    assert.equal(data.problem_id ?? url.searchParams.get("problem_id"), "source-1");
    if (endpoint.endsWith("/published-reasoning")) {
      assert.equal(data.choice_id, "CHOICE_2");
      return send(reply("SOCRATIC_REPAIR", {
        repair_check: "How do you preserve equality?",
        repair_choices: [{ id: "OPTION_1", text: "Ignore both sides" },
          { id: "OPTION_2", text: "Act on both sides" }],
        socratic_repair_questions: ["Think about the equality of both sides."],
      }));
    }
    if (endpoint.endsWith("/published-repair")) {
      if (exactStage === 0 && data.response === "OPTION_1") {
        return send(reply("SOCRATIC_REPAIR_RETRY", { correct: false,
          repair_check: "Try the two-sided operation again.",
          repair_choices: [{ id: "OPTION_1", text: "Ignore both sides" },
            { id: "OPTION_2", text: "Act on both sides" }] }));
      }
      if (exactStage === 0) {
        assert.equal(data.response, "OPTION_2");
        exactStage++;
        return send(reply("SOCRATIC_REPAIR", { correct: true,
          repair_check: "What coefficient remains on the left?" }));
      }
      if (exactStage === 1) {
        assert.equal(data.response, "3/2");
        exactStage++;
        return send(reply("SOCRATIC_REPAIR", { correct: true,
          repair_check: "What constant remains on the right?" }));
      }
      assert.equal(data.response, "5/4");
      exactStage++;
      return send(reply("GUIDED_RETEST", { correct: true,
        guided_retest_task: task("GUIDED", "Fresh guided equation") }));
    }
    if (endpoint.endsWith("/published-guided-retest")) {
      guidedCalls++;
      if (guidedCalls === 1) return send(reply("GUIDED_RETEST_RETRY", {
        correct: false, guided_retest_task: task("GUIDED", "Different guided equation"),
      }));
      assert.equal(data.answer, "1/2");
      return send(reply("READY_FOR_TRANSFER_CONFIRMATION", { correct: true }));
    }
    if (endpoint.endsWith("/published-transfer/start")) return send(reply("INDEPENDENT_EXIT", {
      independent_task: task("INDEPENDENT", "Unseen transfer equation"), hints_allowed: false,
    }));
    if (endpoint.endsWith("/published-transfer/respond")) {
      assert.equal(data.answer, "2/3");
      return send(reply("TRANSFER_FEEDBACK_ONLY", { correct: true }));
    }
    if (endpoint.endsWith("/published-mastery/start")) return send(reply(
      "MASTERY_VERIFICATION_FEEDBACK_ONLY", {
        verification_task: task("MASTERY", "New verification equation"), hints_allowed: false,
      }));
    if (endpoint.endsWith("/published-mastery/respond")) {
      assert.equal(data.answer, "-3/4");
      return send(reply("MASTERY_VERIFICATION_FEEDBACK_ONLY", { correct: true }));
    }
    return route.fulfill({ status: 404, body: "{}" });
  });
  await page.goto("http://127.0.0.1:" + address.port + "/" + path.basename(dir) + "/index.html");
  const region = page.getByRole("region", { name: "Published learning recovery" });
  await page.getByRole("button", { name: "Offer recovery" }).click();
  assert.equal(await region.count(), 0, "unapproved published family must stay invisible");
  await page.waitForFunction(() => document.querySelector("button")?.getAttribute("aria-pressed") === "false");
  authorized = true;
  await page.getByRole("button", { name: "Offer recovery" }).click();
  await region.getByText("Why are the two sides equal?").waitFor();
  await region.getByRole("radio", { name: "Same operation on both sides" }).check();
  await region.getByRole("button", { name: "Check response" }).click();
  await region.getByText("How do you preserve equality?").waitFor();
  await region.getByRole("radio", { name: "Ignore both sides" }).check();
  await region.getByRole("button", { name: "Check response" }).click();
  await region.getByText("Try the two-sided operation again.").waitFor();
  await region.getByRole("radio", { name: "Act on both sides" }).check();
  await region.getByRole("button", { name: "Check response" }).click();
  await region.getByLabel("Your exact answer").fill("3/2");
  await region.getByRole("button", { name: "Check response" }).click();
  await region.getByText("What constant remains on the right?").waitFor();
  await region.getByLabel("Your exact answer").fill("5/4");
  await region.getByRole("button", { name: "Check response" }).click();
  await region.getByText("Fresh guided equation").waitFor();
  await region.getByLabel("Your exact answer").fill("0");
  await region.getByRole("button", { name: "Check response" }).click();
  await region.getByText("Different guided equation").waitFor();
  await region.getByLabel("Your exact answer").fill("1/2");
  await region.getByRole("button", { name: "Check response" }).click();
  await region.getByRole("button", { name: "Start unhinted transfer" }).click();
  await region.getByText("Unseen transfer equation").waitFor();
  assert.equal(await region.getByText("How do you preserve equality?").count(), 0);
  assert.equal(await region.getByText("Fresh guided equation").count(), 0);
  await region.getByLabel("Your exact answer").fill("2/3");
  await region.getByRole("button", { name: "Check response" }).click();
  await region.getByRole("button", { name: "Begin separate feedback-only verification" }).click();
  await region.getByText("New verification equation").waitFor();
  await region.getByLabel("Your exact answer").fill("-3/4");
  await region.getByRole("button", { name: "Check response" }).click();
  await region.getByText(/Verification recorded/).waitFor();
  assert.equal(await region.getByText(/mastery badge earned/i).count(), 0);
  // Reload/remount is a fresh server-owned stage fetch, never browser-local replay.
  recoverStage = "GUIDED_RETEST";
  await page.reload();
  await page.getByRole("button", { name: "Offer recovery" }).click();
  await region.getByText("Persisted guided retest").waitFor();
  // Latest backend validates persisted issuance identity before returning each task.
  recoverStage = "INDEPENDENT_EXIT";
  await page.reload();
  await page.getByRole("button", { name: "Offer recovery" }).click();
  await region.getByText("Persisted independent task").waitFor();
  assert.equal(await region.getByText("Persisted guided retest").count(), 0);
  recoverStage = "MASTERY_VERIFICATION_FEEDBACK_ONLY";
  await page.reload();
  await page.getByRole("button", { name: "Offer recovery" }).click();
  await region.getByText("Persisted verification task").waitFor();
  assert.equal(await region.getByText("Persisted independent task").count(), 0);
  recoverStage = "COMPLETE_FEEDBACK_ONLY";
  await page.reload();
  await page.getByRole("button", { name: "Offer recovery" }).click();
  await region.getByText(/Verification recorded/).waitFor();
  assert.deepEqual(pageErrors, []);
  console.log("PASS: server-gated diagnosis, targeted repair, retry, unhinted transfer, no-credit verification and hidden guided content");
} finally {
  await browser?.close();
  await server?.close();
  await rm(dir, { recursive: true, force: true });
}
