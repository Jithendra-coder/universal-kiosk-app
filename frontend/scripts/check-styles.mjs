import { readdir, readFile } from "node:fs/promises";
import { extname, join, relative, resolve } from "node:path";

const root = resolve("src");
const allowedCss = new Set([resolve("src/app/globals.css"), resolve("src/app/landing.css")]);
const failures = [];

async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      await walk(path);
      continue;
    }
    if (extname(path) === ".css" && !allowedCss.has(resolve(path))) failures.push(`unauthorized stylesheet: ${relative(process.cwd(), path)}`);
    if (/\.[jt]sx?$/.test(path)) {
      const source = await readFile(path, "utf8");
      if (/<style(?:\s|>)/.test(source) || /styled-jsx/.test(source)) failures.push(`embedded stylesheet: ${relative(process.cwd(), path)}`);
    }
  }
}

await walk(root);
if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log("Style policy passed: src/app/globals.css is the only application stylesheet.");
