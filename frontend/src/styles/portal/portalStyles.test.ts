import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const PORTAL_DIR = resolve(__dirname);

const MODULES = [
  "base.css",
  "shell.css",
  "layout.css",
  "animations.css",
  "map.css",
  "epic-landing.css",
  "widgets.css",
  "content.css",
  "admin.css",
];

describe("portal styles", () => {
  it("index imports all split modules", () => {
    const index = readFileSync(resolve(PORTAL_DIR, "index.css"), "utf8");
    for (const mod of MODULES) {
      expect(index).toContain(`./${mod}`);
    }
  });

  it("each module is non-empty and wrapped in @layer components except base", () => {
    for (const mod of MODULES) {
      const content = readFileSync(resolve(PORTAL_DIR, mod), "utf8");
      expect(content.length).toBeGreaterThan(20);
      if (mod === "base.css") {
        expect(content).toContain("@tailwind base");
      } else {
        expect(content).toContain("@layer components");
      }
    }
  });
});
