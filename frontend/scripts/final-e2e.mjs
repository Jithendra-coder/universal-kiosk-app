import { chromium } from "playwright";

const base = "http://localhost:3000";
const email = process.env.MENUTAP_E2E_EMAIL;
const password = process.env.MENUTAP_E2E_PASSWORD;
if (!email || !password) throw new Error("MENUTAP_E2E_EMAIL and MENUTAP_E2E_PASSWORD are required.");

const browser = await chromium.launch({ headless: true, channel: "chrome" });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
const errors = [];
const failedRequests = [];
const evidence = { setup: [], layouts: [], live: null };

function observe(page) {
  page.on("pageerror", (error) => errors.push({ url: page.url(), error: String(error) }));
  page.on("requestfailed", (request) => failedRequests.push({ url: request.url(), error: request.failure()?.errorText }));
}

async function api(path, options = {}) {
  const response = await context.request.fetch(`${base}/api${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const text = await response.text();
  const body = text ? JSON.parse(text) : null;
  if (!response.ok()) throw new Error(`${options.method || "GET"} ${path}: ${response.status()} ${text}`);
  return body;
}

async function settle(page, path) {
  await page.waitForURL(`**${path}`, { timeout: 30_000 });
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(800);
}

async function runOrder(page) {
  const start = page.getByRole("button", { name: /^(Start|Browse Menu|View Menu)$/ }).first();
  await start.waitFor({ timeout: 30_000 });
  await start.click();
  const category = page.getByRole("button", { name: "Cafe favourites", exact: true });
  if (await category.count()) await category.click();
  const add = page.getByRole("button", { name: "Add", exact: true }).first();
  await add.waitFor({ timeout: 30_000 });
  await add.click();
  await page.getByRole("button", { name: /^Cart \(1\)$/ }).click();
  await page.getByRole("button", { name: "Checkout", exact: true }).click();
  await page.getByRole("button", { name: "Review order", exact: true }).click();
  await page.getByRole("button", { name: "Confirm order", exact: true }).click();
  await page.getByRole("heading", { name: "Order confirmed", exact: true }).waitFor({ timeout: 30_000 });
  const confirmation = await page.locator("body").innerText();
  await start.waitFor({ timeout: 15_000 });
  return confirmation.match(/Order [^\n]+/)?.[0] || "Order confirmed";
}

try {
  const page = await context.newPage();
  observe(page);
  await page.goto(`${base}/auth/sign-in`, { waitUntil: "domcontentloaded", timeout: 30_000 });
  await page.waitForTimeout(1_000);
  await page.locator("input[name=identifier]").fill(email);
  await page.locator("input[name=password]").fill(password);
  await page.getByRole("button", { name: "Sign In", exact: true }).click();
  await page.waitForURL(/\/(setup|dashboard)/, { timeout: 30_000 });

  await page.goto(`${base}/setup/business-type`);
  await page.locator(".mt-business-type-option", { hasText: "Cafe" }).click();
  await page.locator(".mt-onboarding-topbar__continue").click();
  await settle(page, "/setup/business-details");
  evidence.setup.push("business-type");

  await page.locator(".mt-onboarding-topbar__continue").click();
  await settle(page, "/setup/menu-items");
  await page.locator(".mt-menu-selection-card").first().waitFor({ timeout: 30_000 });
  for (const card of await page.locator(".mt-menu-selection-card").all()) {
    if (await page.locator(".mt-menu-selection-card[aria-pressed=true]").count() >= 4) break;
    await card.click();
  }
  evidence.setup.push("business-details");

  await page.locator(".mt-onboarding-topbar__continue").click();
  await settle(page, "/setup/kiosk-layout");
  evidence.setup.push("menu-items");

  await page.locator(".mt-kiosk-layout-card", { hasText: "Side Navigation" }).click();
  await page.locator(".mt-onboarding-topbar__continue").click();
  await settle(page, "/setup/welcome-screen");
  evidence.setup.push("kiosk-layout");

  await page.locator(".mt-welcome-selection-card", { hasText: "Welcome screen" }).click();
  await page.locator(".mt-onboarding-topbar__continue").click();
  await settle(page, "/setup/test-kiosk");
  evidence.setup.push("welcome-screen", "test-kiosk");

  const business = (await api("/businesses/me")).business;
  for (const layout of ["side-navigation", "top-navigation", "category-first"]) {
    await api(`/businesses/${business.id}`, { method: "PATCH", data: { kiosk_layout_id: layout, onboarding_step: 5 } });
    const session = await api(`/businesses/${business.id}/setup/test-sessions`, { method: "POST" });
    const kiosk = await context.newPage();
    observe(kiosk);
    await kiosk.goto(`${base}/kiosk/test#${encodeURIComponent(session.session.token)}`, { waitUntil: "domcontentloaded", timeout: 30_000 });
    const confirmation = await runOrder(kiosk);
    evidence.layouts.push({ layout, confirmation });
    await kiosk.close();
  }

  await api(`/businesses/${business.id}/setup/preview-attestations`, { method: "POST", data: { event_version: 1 } });
  const overview = await api(`/businesses/${business.id}/setup`);
  await api(`/businesses/${business.id}/setup/publish`, { method: "POST", data: { expected_revision: overview.setup.revision, allow_untested: false } });

  await page.goto(`${base}/dashboard`, { waitUntil: "domcontentloaded", timeout: 30_000 });
  await page.getByPlaceholder("Search").waitFor({ timeout: 30_000 });

  const live = await context.newPage();
  observe(live);
  await live.goto(`${base}/kiosk/${business.slug}`, { waitUntil: "domcontentloaded", timeout: 30_000 });
  const liveStart = live.getByRole("button", { name: /^(Start|Browse Menu|View Menu)$/ }).first();
  await liveStart.waitFor({ timeout: 30_000 });
  await liveStart.click();
  const liveCategory = live.getByRole("button", { name: "Cafe favourites", exact: true });
  if (await liveCategory.count()) await liveCategory.click();
  const liveItems = await live.getByRole("button", { name: "Add", exact: true }).count();
  if (!liveItems) throw new Error("The published live kiosk has no orderable menu items.");
  const orders = await api(`/businesses/${business.id}/orders?limit=12`);
  evidence.live = { slug: business.slug, menuItems: liveItems, orderCount: orders.orders.length };
  await live.close();

  if (errors.length || failedRequests.length) throw new Error(`Browser errors: ${JSON.stringify({ errors, failedRequests })}`);
  console.log(JSON.stringify({ passed: true, ...evidence }, null, 2));
} catch (error) {
  throw error;
} finally {
  await browser.close();
}
