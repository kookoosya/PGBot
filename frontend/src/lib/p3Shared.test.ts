import { describe, expect, it } from "vitest";
import { ISSUE_WORKBENCH_PAGE_SIZE, ISSUE_WORKBENCH_STATUSES, issueWorkbenchTotalPages } from "@/lib/issueWorkbench";
import {
  CLASSIFIED_FORM_INITIAL,
  CLASSIFIED_FORM_TEMPLATES,
  CLASSIFIEDS_DRAFT_KEY,
  JOBS_DRAFT_KEY,
  JOBS_FORM_INITIAL,
} from "@/lib/classifiedForm";

describe("issueWorkbench", () => {
  it("exports workbench statuses", () => {
    expect(ISSUE_WORKBENCH_STATUSES).toContain("NEW");
    expect(ISSUE_WORKBENCH_STATUSES).toContain("RESOLVED");
    expect(ISSUE_WORKBENCH_PAGE_SIZE).toBe(20);
  });

  it("excludes archived from workbench filters", () => {
    expect(ISSUE_WORKBENCH_STATUSES).not.toContain("ARCHIVED");
  });

  it("calculates total pages", () => {
    expect(issueWorkbenchTotalPages(0)).toBe(1);
    expect(issueWorkbenchTotalPages(1)).toBe(1);
    expect(issueWorkbenchTotalPages(21)).toBe(2);
    expect(issueWorkbenchTotalPages(40, ISSUE_WORKBENCH_PAGE_SIZE)).toBe(2);
  });
});

describe("classifiedForm", () => {
  it("jobs form defaults to job category", () => {
    expect(JOBS_FORM_INITIAL.category).toMatch(/^job_/);
    expect(CLASSIFIED_FORM_INITIAL.category).toBe("firewood");
  });

  it("uses distinct draft keys", () => {
    expect(CLASSIFIEDS_DRAFT_KEY).not.toBe(JOBS_DRAFT_KEY);
  });

  it("provides starter templates", () => {
    expect(CLASSIFIED_FORM_TEMPLATES.length).toBeGreaterThanOrEqual(2);
    expect(CLASSIFIED_FORM_TEMPLATES[0]).toMatch(/Продам|Услуга|Сосед/i);
  });

  it("requires agree_rules default false", () => {
    expect(CLASSIFIED_FORM_INITIAL.agree_rules).toBe(false);
    expect(JOBS_FORM_INITIAL.agree_rules).toBe(false);
  });
});
