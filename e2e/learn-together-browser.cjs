const { chromium } = require("@playwright/test");
const fs = require("fs");
const assert = require("node:assert/strict");
(async () => {
  const f = JSON.parse(
    fs.readFileSync(process.env.MIHUR_TOGETHER_FIXTURE, "utf8"),
  );
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.MIHUR_CHROMIUM_PATH || undefined,
    args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
  });
  const parent = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
  });
  const child = await browser.newContext({
    viewport: { width: 820, height: 1180 },
    hasTouch: true,
  });
  await parent.addCookies([
    { name: "ai_tutor_session", value: f.parent, url: "http://127.0.0.1:5173" },
  ]);
  await child.addCookies([
    {
      name: "ai_tutor_learner",
      value: "child-cookie",
      url: "http://127.0.0.1:5173",
    },
  ]);
  const p = await parent.newPage(),
    c = await child.newPage();
  const errors = [];
  [p, c].forEach((page) =>
    page.on("pageerror", (error) => errors.push(error.message)),
  );
  const url = `http://127.0.0.1:5173/together/${f.board}`;
  await Promise.all([p.goto(url), c.goto(url)]);
  await Promise.all([
    p
      .getByText("Connected · work saves automatically", { exact: true })
      .waitFor(),
    c
      .getByText("Connected · work saves automatically", { exact: true })
      .waitFor(),
  ]);
  await p.getByRole("button", { name: "Type", exact: true }).click();
  await p
    .getByPlaceholder("Type, then tap the board to place")
    .fill("2x + 3 = 11");
  await p.getByRole("button", { name: "Add text to board" }).click();
  await c.locator("svg text").filter({ hasText: "2x + 3 = 11" }).waitFor();
  await c.getByRole("button", { name: "Type", exact: true }).click();
  await c.getByPlaceholder("Type, then tap the board to place").fill("2x = 8");
  await c.getByRole("button", { name: "Add text to board" }).click();
  await p.locator("svg text").filter({ hasText: "2x = 8" }).waitFor();
  await c.getByRole("button", { name: "Undo my last mark" }).click();
  await p
    .locator("svg text")
    .filter({ hasText: "2x = 8" })
    .waitFor({ state: "detached" });
  assert.equal(
    await p.locator("svg text").filter({ hasText: "2x + 3 = 11" }).count(),
    1,
  );
  await c.getByRole("button", { name: "Pen", exact: true }).click();
  const box = await c
    .getByRole("img", { name: /Shared family whiteboard/ })
    .boundingBox();
  await c.mouse.move(box.x + 100, box.y + 100);
  await c.mouse.down();
  await c.mouse.move(box.x + 200, box.y + 150, { steps: 8 });
  await c.mouse.up();
  await p.locator('polyline[stroke="#0369a1"]').waitFor();
  await child.setOffline(true);
  await c.getByRole("button", { name: "Type", exact: true }).click();
  await c.getByPlaceholder("Type, then tap the board to place").fill("x = 4");
  await c.getByRole("button", { name: "Add text to board" }).click();
  await c.getByText(/1 marks waiting to save/).waitFor();
  await child.setOffline(false);
  await c.reload();
  await p.locator("svg text").filter({ hasText: "x = 4" }).waitFor();
  await c.locator("svg text").filter({ hasText: "x = 4" }).waitFor();
  await c.setViewportSize({ width: 390, height: 844 });
  assert.equal(
    await c.getByRole("button", { name: "Type", exact: true }).isVisible(),
    true,
  );
  assert.equal(
    await c.evaluate(() => document.documentElement.scrollWidth > innerWidth),
    false,
  );
  assert.deepEqual(errors, []);
  await browser.close();
  console.log(
    "PASS: parent/child sync, author undo, drawing, offline queued edit + reload recovery, phone layout; no page errors.",
  );
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
