import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const pagesRoot = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(pagesRoot, "..", "..", "..");

describe("module 18 complaints integrity", () => {
  it("audit doc records acceptance scenario", () => {
    const audit = readFileSync(
      join(repoRoot, "docs/factual-integrity/module-18-public-complaints-flow.md"),
      "utf8",
    );
    expect(audit).toContain("268613b");
    expect(audit).toContain("Complaints.tsx");
    expect(audit).toContain("NEW");
  });

  it("Complaints form uses anti double-submit and pending disable", () => {
    const src = readFileSync(join(pagesRoot, "Complaints.tsx"), "utf8");
    expect(src).toContain("submittingRef");
    expect(src).toContain("disabled={loading}");
    expect(src).toContain("createIssue");
    expect(src).toContain("minLength={5}");
    expect(src).toContain("website_url");
    expect(src).toContain("PostSubmitPanel");
  });

  it("issues API client posts to /issues", () => {
    const src = readFileSync(join(pagesRoot, "../lib/api/issues.ts"), "utf8");
    expect(src).toContain('"/issues"');
    expect(src).toContain("method: \"POST\"");
  });

  it("module 13 gemini fallback remains in backend", () => {
    const src = readFileSync(
      join(repoRoot, "backend/app/services/issue/gemini_analysis.py"),
      "utf8",
    );
    expect(src).toContain("_gemini_fallback_result");
    expect(src).toContain("Rule fallback accepted complaint");
  });
});
