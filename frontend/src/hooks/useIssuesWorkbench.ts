import { useEffect, useState } from "react";
import { api } from "@/lib/api/index";
import type { Issue } from "@/lib/api/types/issues";
import { buildIssueWorkbenchQuery, ISSUE_WORKBENCH_PAGE_SIZE, issueWorkbenchTotalPages } from "@/lib/issueWorkbench";

export function useIssuesWorkbench() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Issue | null>(null);
  const [resolution, setResolution] = useState("");
  const [statusError, setStatusError] = useState("");

  const loadIssues = () => {
    api
      .getIssues(buildIssueWorkbenchQuery(page, statusFilter, search))
      .then((r) => {
        setIssues(r.items);
        setTotal(r.total);
      })
      .catch(console.error);
  };

  useEffect(() => {
    loadIssues();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- search applies on explicit «Найти»
  }, [page, statusFilter]);

  const selectIssue = (issue: Issue) => {
    setSelected(issue);
    setResolution(issue.resolution_text || "");
    setStatusError("");
  };

  const handleStatusChange = async (issue: Issue, status: string) => {
    setStatusError("");
    try {
      await api.updateIssueStatus(
        issue.id,
        status,
        status === "RESOLVED" ? resolution || undefined : undefined,
      );
      loadIssues();
      if (selected?.id === issue.id) {
        setSelected(await api.getIssue(issue.id));
      }
    } catch (err) {
      setStatusError(err instanceof Error ? err.message : "Не удалось обновить статус");
    }
  };

  const totalPages = issueWorkbenchTotalPages(total);

  return {
    issues,
    total,
    page,
    setPage,
    statusFilter,
    setStatusFilter,
    search,
    setSearch,
    selected,
    resolution,
    setResolution,
    loadIssues,
    selectIssue,
    handleStatusChange,
    totalPages,
    pageSize: ISSUE_WORKBENCH_PAGE_SIZE,
    statusError,
  };
}
