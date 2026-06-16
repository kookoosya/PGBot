import { describe, expect, it } from "vitest";
import {
  buildIssueWorkbenchQuery,
  ISSUE_WORKBENCH_PAGE_SIZE,
  ISSUE_WORKBENCH_STATUSES,
  issueWorkbenchTotalPages,
} from "@/lib/issueWorkbench";

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

  it("builds query params with filters", () => {
    expect(buildIssueWorkbenchQuery(2, "", "")).toEqual({ page: "2", page_size: "20" });
    expect(buildIssueWorkbenchQuery(1, "NEW", "фонарь")).toEqual({
      page: "1",
      page_size: "20",
      status_filter: "NEW",
      search: "фонарь",
    });
  });
});
