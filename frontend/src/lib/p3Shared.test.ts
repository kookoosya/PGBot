import { describe, expect, it } from "vitest";
import { ISSUE_WORKBENCH_PAGE_SIZE, ISSUE_WORKBENCH_STATUSES } from "@/lib/issueWorkbench";
import { CLASSIFIED_FORM_INITIAL, JOBS_FORM_INITIAL } from "@/lib/classifiedForm";

describe("issueWorkbench", () => {
  it("exports workbench statuses", () => {
    expect(ISSUE_WORKBENCH_STATUSES).toContain("NEW");
    expect(ISSUE_WORKBENCH_STATUSES).toContain("RESOLVED");
    expect(ISSUE_WORKBENCH_PAGE_SIZE).toBe(20);
  });
});

describe("classifiedForm", () => {
  it("jobs form defaults to job category", () => {
    expect(JOBS_FORM_INITIAL.category).toMatch(/^job_/);
    expect(CLASSIFIED_FORM_INITIAL.category).toBe("firewood");
  });
});
