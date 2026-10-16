const { chromium, expect } = require("@playwright/test");
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
  await c.getByRole("combobox", { name: "Worksheet page" }).selectOption("");
  await c.locator("svg text").filter({ hasText: "x = 4" }).waitFor();
  await p.locator("svg text").filter({ hasText: "x = 4" }).waitFor();
  await p.locator("svg text").filter({ hasText: "2x + 3 = 11" }).waitFor();
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
  // Minimal synthetic two-page PDF, kept in memory rather than a document artifact.
  function testPDF() {
    const contents = [
      "BT /F1 24 Tf 50 700 Td (Worksheet A: solve 2x + 3 = 11) Tj ET",
      "BT /F1 24 Tf 50 700 Td (Worksheet B: solve 3y - 4 = 8) Tj ET",
    ];
    const objects = [
      "<< /Type /Catalog /Pages 2 0 R >>",
      "<< /Type /Pages /Kids [3 0 R 5 0 R] /Count 2 >>",
      "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] /Resources << /Font << /F1 7 0 R >> >> /Contents 4 0 R >>",
      `<< /Length ${contents[0].length} >>\nstream\n${contents[0]}\nendstream`,
      "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] /Resources << /Font << /F1 7 0 R >> >> /Contents 6 0 R >>",
      `<< /Length ${contents[1].length} >>\nstream\n${contents[1]}\nendstream`,
      "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ];
    let data = "%PDF-1.4\n%PRIVATE-ORIGINAL-WORKSHEET\n";
    const offsets = [0];
    objects.forEach((object, index) => {
      offsets.push(Buffer.byteLength(data));
      data += `${index + 1} 0 obj\n${object}\nendobj\n`;
    });
    const xref = Buffer.byteLength(data);
    data += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
    for (const offset of offsets.slice(1))
      data += `${String(offset).padStart(10, "0")} 00000 n \n`;
    data += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF`;
    return Buffer.from(data);
  }
  const postedOriginals = [];
  p.on("request", (request) => {
    if (
      request.method() === "POST" &&
      request.url().includes("/together/boards/")
    ) {
      const data = request.postDataBuffer();
      if (data?.includes(Buffer.from("PRIVATE-ORIGINAL-WORKSHEET")))
        postedOriginals.push(request.url());
    }
  });
  await p.getByRole("button", { name: "Import PDF", exact: true }).click();
  const importer = p.getByRole("region", { name: "PDF homework importer" });
  await importer.locator('input[type="file"]').setInputFiles({
    name: "private.pdf",
    mimeType: "application/pdf",
    buffer: testPDF(),
  });
  await importer.getByText("PDF page 1 of 2", { exact: true }).waitFor();
  await importer
    .getByRole("button", { name: "Add selected PDF page", exact: true })
    .waitFor({ state: "visible" });
  await expect(
    importer.getByRole("button", {
      name: "Add selected PDF page",
      exact: true,
    }),
  ).toBeEnabled();
  const previewPixels = await importer
    .locator("canvas")
    .evaluate((canvas) => canvas.toDataURL());
  if (process.env.MIHUR_PDF_PREVIEW)
    await importer.screenshot({ path: process.env.MIHUR_PDF_PREVIEW });
  await importer
    .getByRole("button", { name: "Add selected PDF page", exact: true })
    .click();
  await importer
    .getByText("Page added to your shared board.", { exact: true })
    .waitFor();
  await c
    .getByRole("combobox", { name: "Worksheet page" })
    .locator("option[value]")
    .filter({ hasText: "Page 2" })
    .waitFor({ state: "attached" });
  await c.getByTestId("homework-photo").waitFor();
  await p.getByRole("button", { name: "Type", exact: true }).click();
  await p
    .getByPlaceholder("Type, then tap the board to place")
    .fill("PDF first-page note");
  await p
    .getByRole("button", { name: "Add text to board", exact: true })
    .click();
  await c
    .locator("svg text")
    .filter({ hasText: "PDF first-page note" })
    .waitFor();
  const firstPDFPage = await c
    .getByRole("combobox", { name: "Worksheet page" })
    .inputValue();
  await importer
    .getByRole("button", { name: "Next PDF page", exact: true })
    .click();
  await importer.getByText("PDF page 2 of 2", { exact: true }).waitFor();
  await expect(
    importer.getByRole("button", {
      name: "Add selected PDF page",
      exact: true,
    }),
  ).toBeEnabled();
  assert.ok(
    (await importer
      .locator("canvas")
      .evaluate((canvas) => canvas.toDataURL())) !== previewPixels,
    "PDF preview must change before the next page can be imported",
  );
  await importer
    .getByRole("button", { name: "Add selected PDF page", exact: true })
    .click();
  await importer
    .getByText("Page added to your shared board.", { exact: true })
    .waitFor();
  await c
    .locator("svg text")
    .filter({ hasText: "PDF first-page note" })
    .waitFor({ state: "detached" });
  await c
    .getByRole("combobox", { name: "Worksheet page" })
    .selectOption(firstPDFPage);
  await p
    .locator("svg text")
    .filter({ hasText: "PDF first-page note" })
    .waitFor();
  await c.reload();
  await c
    .locator("svg text")
    .filter({ hasText: "PDF first-page note" })
    .waitFor();
  assert.deepEqual(postedOriginals, []);
  await importer.locator('input[type="file"]').setInputFiles({
    name: "broken.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("not a PDF"),
  });
  await importer.getByRole("alert").filter({ hasText: "valid PDF" }).waitFor();
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
    "PASS: parent/child sync, author undo, drawing, offline queued edit + reload recovery, photo/PDF synchronization, per-page notes and navigation replay, local-only PDF bytes, zoom, own-mark eraser, phone layout; no page errors.",
  );
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
