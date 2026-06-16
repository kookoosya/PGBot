/** Shared constants for official/admin issue workbench. */

export const ISSUE_WORKBENCH_STATUSES = [
  "NEW",
  "UNDER_REVIEW",
  "ASSIGNED",
  "IN_PROGRESS",
  "RESOLVED",
  "REJECTED",
] as const;

export const ISSUE_WORKBENCH_PAGE_SIZE = 20;

export function issueWorkbenchTotalPages(
  total: number,
  pageSize: number = ISSUE_WORKBENCH_PAGE_SIZE,
): number {
  return Math.ceil(total / pageSize) || 1;
}
