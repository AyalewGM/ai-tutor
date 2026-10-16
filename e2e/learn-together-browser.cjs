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
  const photo = await p.evaluate(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 800;
    canvas.height = 500;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, 800, 500);
    ctx.fillStyle = "#222";
    ctx.font = "36px sans-serif";
    ctx.fillText("Homework: 2x + 3 = 11", 50, 80);
    return canvas.toDataURL("image/png").split(",")[1];
  });
  await p.locator('input[type="file"]').setInputFiles({
    name: "homework.png",
    mimeType: "image/png",
    buffer: Buffer.from(photo, "base64"),
  });
  await c.getByTestId("homework-photo").waitFor();
  const imageUrl = await c.getByTestId("homework-photo").getAttribute("href");
  const imageResponse = await child.request.get(
    "http://127.0.0.1:5173" + imageUrl,
  );
  assert.equal(imageResponse.status(), 200);
  assert.equal(imageResponse.headers()["content-type"], "image/jpeg");
  assert.equal(imageResponse.headers()["cache-control"], "no-store");
  const beforeZoom = await c
    .getByRole("img", { name: /Shared family whiteboard/ })
    .boundingBox();
  await c.getByRole("button", { name: "Zoom in", exact: true }).click();
  const afterZoom = await c
    .getByRole("img", { name: /Shared family whiteboard/ })
    .boundingBox();
  assert.ok(afterZoom.width > beforeZoom.width);
  await c.getByRole("button", { name: "Move page", exact: true }).click();
  const viewport = c.getByRole("region", { name: "Whiteboard viewport" });
  await viewport.scrollIntoViewIfNeeded();
  const viewportBox = await viewport.boundingBox();
  await c.mouse.move(viewportBox.x + 250, viewportBox.y + 100);
  await c.mouse.down();
  await c.mouse.move(viewportBox.x + 120, viewportBox.y + 100, { steps: 5 });
  await c.mouse.up();
  assert.ok((await viewport.evaluate((element) => element.scrollLeft)) > 0);
  await c.getByRole("button", { name: "Fit page", exact: true }).click();
  await c
    .getByRole("button", { name: "Eraser (my marks)", exact: true })
    .click();
  await c.locator("svg text").filter({ hasText: "x = 4" }).click();
  await p
    .locator("svg text")
    .filter({ hasText: "x = 4" })
    .waitFor({ state: "detached" });
  await c.locator("svg text").filter({ hasText: "2x + 3 = 11" }).click();
  await c
    .getByRole("alert")
    .filter({ hasText: "eraser removes your own marks" })
    .waitFor();
  assert.equal(
    await p.locator("svg text").filter({ hasText: "2x + 3 = 11" }).count(),
    1,
  );
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
    "PASS: parent/child sync, author undo, drawing, offline queued edit + reload recovery, photo synchronization, zoom, own-mark eraser, phone layout; no page errors.",
  );
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
