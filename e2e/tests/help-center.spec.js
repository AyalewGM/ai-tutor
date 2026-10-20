const { test, expect } = require("@playwright/test");

test("Help Center and five pilot articles are available without signing in", async ({ page }) => {
  await page.goto("/help");
  await expect(page.getByRole("heading", { name: "Find your way with Mihur" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Help navigation" })).toBeVisible();
  const articles = [
    ["welcome", "Welcome to Mihur — How It Works"],
    ["parent-first-day", "Parent Quick Start — Your First 10 Minutes"],
    ["student-first-session", "Student Quick Start — Your First Practice Session"],
    ["progress-and-mastery", "Understanding Progress, Hints & Mastery"],
    ["privacy-and-faq", "Privacy, Safety & Frequently Asked Questions"],
  ];
  for (const [slug, heading] of articles) {
    await page.goto(`/help/${slug}`);
    await expect(page.getByRole("heading", { name: heading, exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: "All help articles" })).toBeVisible();
  }
  await page.goto("/help/not-a-real-article");
  await expect(page.getByRole("heading", { name: "We couldn't find that guide" })).toBeVisible();
});

test("anonymous users can search and follow first-day practice-link instructions", async ({ page }) => {
  await page.goto("/help");
  await page.getByRole("searchbox", { name: "Search the Help Center" }).fill("Parent PIN");
  await expect(page.getByRole("link", { name: /Parent Quick Start/ })).toBeVisible();
  await page.getByRole("searchbox", { name: "Search the Help Center" }).fill("unlikely-token-that-never-matches");
  await expect(page.getByText("No matching guides. Try a different word.")).toBeVisible();
  await page.goto("/help/parent-first-day#3-share-each-childs-private-practice-link");
  await expect(page.getByRole("heading", { name: "3. Share each child's private practice link" })).toBeVisible();
  await expect(page.getByText(/Generate link/).first()).toBeVisible();
});

test("landing page exposes public Help Center route", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Help", exact: true }).first().click();
  await expect(page).toHaveURL(/\/help$/);
  await expect(page.getByRole("heading", { name: "Find your way with Mihur" })).toBeVisible();
});
