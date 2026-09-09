import { readdir, readFile } from "node:fs/promises";
import { join, relative, resolve } from "node:path";

const root = resolve("src/components/dashboard");
const css = await readFile(resolve("src/app/globals.css"), "utf8");
const layout = await readFile(resolve("src/app/layout.tsx"), "utf8");
const failures = [];
const approvedLocalHeadings = new Set([
  "AvailabilityPage.tsx", "BrandingThemePage.tsx", "HomePage.tsx", "KioskExperiencePage.tsx",
  "KioskScreensPage.tsx", "ManageMenuPage.tsx", "PreviewKioskPage.tsx", "PublishHistoryPage.tsx",
  "TestPublishPage.tsx", "WelcomeScreenPage.tsx",
]);
const representativePages = [
  ["Home", "HomePage.tsx"], ["Sales & Orders", "BusinessInsightsPage.tsx"], ["Menu Performance", "BusinessInsightsPage.tsx"],
  ["Live Orders", "OperationsPage.tsx"], ["Devices", "OperationsPage.tsx"], ["Manage Menu", "ManageMenuPage.tsx"],
  ["Promotions", "KioskExperiencePage.tsx"], ["Payments", "AdministrationModule.tsx"], ["Locations", "AdministrationModule.tsx"],
  ["Business Settings", "AdministrationModule.tsx"],
];

async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) await walk(path);
    else if (path.endsWith(".tsx")) {
      const source = await readFile(path, "utf8");
      const name = relative(root, path);
      if (/<h1(?:\s|>)/.test(source) && !approvedLocalHeadings.has(name)) failures.push(`unapproved owner-dashboard h1: ${name}; use PageHeader or add it to the semantic heading contract`);
      if (/fontFamily\s*:|font-family\s*:/.test(source)) failures.push(`page-local font family: ${name}`);
    }
  }
}

await walk(root);
for (const [title, file] of representativePages) {
  const source = await readFile(join(root, file), "utf8");
  if (!source.includes("PageHeader") && !approvedLocalHeadings.has(file)) failures.push(`${title} does not use the page-heading semantic source`);
}
for (const selector of [".mt-home-hero h1", ".mt-menu-header h1", ".mt-promotions-header h1", ".mt-availability-header h1", ".mt-welcome-header h1"]) {
  if (!css.includes(selector)) failures.push(`semantic heading selector missing: ${selector}`);
}
if (!css.includes("--font-dashboard-display") || !css.includes("--font-dashboard-content")) failures.push("dashboard typography tokens are missing");
if (layout.includes("Instrument_Sans") || layout.includes("--font-instrument")) failures.push("unused Instrument Sans loading remains");

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log("Dashboard typography contract passed.");
