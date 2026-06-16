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

export function buildIssueWorkbenchQuery(
  page: number,
  statusFilter: string,
  search: string,
): Record<string, string> {
  const params: Record<string, string> = {
    page: String(page),
    page_size: String(ISSUE_WORKBENCH_PAGE_SIZE),
  };
  if (statusFilter) params.status_filter = statusFilter;
  if (search) params.search = search;
  return params;
}
