import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const pagesRoot = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(pagesRoot, "..", "..", "..");

describe("module 19 admin complaints integrity", () => {
  it("audit doc references baseline and admin routes", () => {
    const audit = readFileSync(
      join(repoRoot, "docs/factual-integrity/module-19-admin-complaints-flow.md"),
      "utf8",
    );
    expect(audit).toContain("48384d9");
    expect(audit).toContain("/admin/issues");
  });

  it("admin issues page uses workbench with status error support", () => {
    const issuesPage = readFileSync(join(pagesRoot, "Issues.tsx"), "utf8");
    const hook = readFileSync(join(pagesRoot, "../hooks/useIssuesWorkbench.ts"), "utf8");
    const workbench = readFileSync(
      join(pagesRoot, "../components/literary/IssuesWorkbench.tsx"),
      "utf8",
    );
    expect(issuesPage).toContain('shell="admin"');
    expect(issuesPage).toContain("statusError");
    expect(hook).toContain("statusError");
    expect(workbench).toContain("statusError");
  });

  it("issues API exposes status and archive endpoints", () => {
    const api = readFileSync(join(pagesRoot, "../lib/api/issues.ts"), "utf8");
    expect(api).toContain("/status");
    expect(api).toContain("getIssues");
    expect(api).toContain("getIssue");
  });

  it("sidebar links to admin issues", () => {
    const sidebar = readFileSync(
      join(pagesRoot, "../components/layout/Sidebar.tsx"),
      "utf8",
    );
    expect(sidebar).toContain("/admin/issues");
  });
});
