const { test, expect } = require("@playwright/test");

const origin = process.env.E2E_BASE_URL || "http://127.0.0.1:3000";
const a = "11111111-1111-4111-8111-111111111111";
const b = "22222222-2222-4222-8222-222222222222";
const children = [
  { id: a, first_name: "PilotA", grade_level: "4" },
  { id: b, first_name: "PilotB", grade_level: "7" },
];
const json = (route, data, status = 200) =>
  route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });

test("parent manages separate per-child passes; only newly issued link is visible", async ({ page }) => {
  const active = new Map();
  const calls = [];
  await page.addInitScript(() => sessionStorage.setItem("parentUnlock", "synthetic-parent-unlock"));
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname.replace(/^\/api\/v1/, "");
    if (path === "/auth/me") return json(route, { role: "PARENT" });
    if (path === "/parents/profile") return json(route, { display_name: "Pilot Parent", email: "parent@example.test" });
    if (path === "/privacy/notice") return json(route, { version: "v1", title: "Privacy", summary: "Synthetic pilot", acknowledged: true });
    if (path === "/privacy/data-summary") return json(route, { active_learner_count: 2, stored_categories: [] });
    if (path === "/parents/children") return json(route, children);
    if (path === "/practice-pass" && request.method() === "GET") {
      return json(route, { passes: [...active.entries()].map(([id, record]) => ({
        student_id: id, created_at: "2026-10-16T00:00:00Z", expires_at: record.expires_at,
      })) });
    }
    if (path === "/practice-pass" && request.method() === "POST") {
      const body = JSON.parse(request.postData() || "{}");
      calls.push({ operation: "create", id: body.student_id, pin: request.headers()["x-parent-unlock"] });
      if (![a, b].includes(body.student_id)) return json(route, { detail: "Child not found" }, 404);
      const token = (body.student_id === a ? "A" : "B").repeat(43);
      const response = { student_id: body.student_id, expires_at: "2026-10-23T12:00:00Z", url: `/practice/${token}` };
      active.set(body.student_id, response);
      return json(route, response);
    }
    if (path === "/practice-pass" && request.method() === "DELETE") {
      const id = url.searchParams.get("student_id");
      calls.push({ operation: "revoke", id, pin: request.headers()["x-parent-unlock"] });
      active.delete(id);
      return route.fulfill({ status: 204 });
    }
    return json(route, { detail: "unhandled synthetic route" }, 404);
  });

  await page.goto(`${origin}/parent/settings`);
  await expect(page.getByRole("heading", { name: "Private practice links for each child" })).toBeVisible();
  await expect(page.getByText("No active link")).toHaveCount(2);
  await page.getByRole("button", { name: "Generate link" }).first().click();
  await expect(page.getByLabel("New link for PilotA — shown once")).toHaveValue(new RegExp("/practice/A{43}$"));
  expect(calls.at(-1)).toEqual({ operation: "create", id: a, pin: "synthetic-parent-unlock" });

  // Issuing B's link must not regenerate/revoke A's existing pass.
  await page.getByRole("button", { name: "Generate link" }).click();
  await expect(page.getByLabel("New link for PilotB — shown once")).toHaveValue(new RegExp("/practice/B{43}$"));
  await expect(page.getByLabel("New link for PilotA — shown once")).toHaveCount(0);
  expect([...active.keys()].sort()).toEqual([a, b].sort());

  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Revoke link" }).last().click();
  await expect(page.getByText("No active link")).toHaveCount(1);
  expect(calls.at(-1)).toEqual({ operation: "revoke", id: b, pin: "synthetic-parent-unlock" });
  expect([...active.keys()]).toEqual([a]);
});

test("child bearer URL is scrubbed before SPA asset requests; direct entry is learner-only", async ({ browser }) => {
  const context = await browser.newContext({ reducedMotion: "reduce" });
  const page = await context.newPage();
  const secret = "Z".repeat(43);
  let activation = null;
  await page.route("**/api/v1/**", async (route) => {
    const req = route.request();
    const path = new URL(req.url()).pathname.replace(/^\/api\/v1/, "");
    if (path === "/practice-pass/activate") {
      activation = JSON.parse(req.postData());
      return json(route, { student_id: a, nickname: "PilotA" });
    }
    if (path === "/auth/me") return json(route, { detail: "Authentication required" }, 401);
    if (path === "/onboarding/learners") return json(route, [{ id: a, first_name: "PilotA", curriculum_code: "SYNTH", curriculum_version: "pilot", avatar_id: "avatar-1" }]);
    if (path === "/onboarding/regions") return json(route, { countries: [], family: { country_code: "US", region_code: "MD" } });
    if (path === "/onboarding/curricula") return json(route, []);
    if (path === `/onboarding/learners/${a}/skills`) return json(route, []);
    return json(route, { detail: "unhandled synthetic route" }, 404);
  });
  await page.goto(`${origin}/practice/${secret}`);
  await expect(page).toHaveURL(/\/learn$/);
  expect(activation).toEqual({ token: secret });
  await expect(page.getByRole("heading", { name: "Ready to learn, PilotA?" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Add a learner" })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Parent", exact: true })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Plan" })).toHaveCount(0);
  expect(await page.evaluate(() => window.location.href.includes("Z".repeat(43)))).toBe(false);
  await context.close();
});

test("expired/revoked child link fails closed and shows no account information", async ({ page }) => {
  const secret = "R".repeat(43);
  await page.route("**/api/v1/practice-pass/activate", (route) => json(route, { detail: "invalid" }, 401));
  await page.goto(`${origin}/practice/${secret}`);
  await expect(page).toHaveURL(/\/practice\/claim$/);
  await expect(page.getByRole("alert")).toContainText("Ask your parent for a new link");
  await expect(page.getByText(secret)).toHaveCount(0);
});

test("parent pilot invite is carried into registration and removed from browser history", async ({ page }) => {
  const invite = "I".repeat(43);
  let registration = null;
  await page.route("**/api/v1/**", async (route) => {
    const req = route.request();
    const path = new URL(req.url()).pathname.replace(/^\\/api\\/v1/, "");
    if (path === "/auth/config") return json(route, { turnstile_site_key: null });
    if (path === "/auth/register-parent") {
      registration = JSON.parse(req.postData());
      return json(route, { id: "test-parent", role: "PARENT", display_name: "Test", approval_status: "APPROVED" }, 201);
    }
    return json(route, { detail: "not signed in" }, 401);
  });
  await page.goto(`${origin}/login?invite=${invite}`);
  await expect(page).toHaveURL(/\\/login$/);
  await expect(page.getByLabel("Private pilot invitation code")).toHaveValue(invite);
  await page.getByLabel("Email").fill("pilot@example.test");
  await page.getByLabel("Password").fill("SyntheticPassword!12345");
  await page.getByLabel("4-digit parent PIN").fill("1234");
  await page.getByLabel("I accept the Terms of Service.").check();
  await page.getByLabel(/I am the parent or guardian/).check();
  await page.getByRole("button", { name: "Create account" }).click();
  await expect.poll(() => registration?.invitation_token).toBe(invite);
});
