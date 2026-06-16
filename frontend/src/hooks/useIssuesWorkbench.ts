import { useEffect, useState } from "react";
import { api, Issue } from "@/lib/api";
import { ISSUE_WORKBENCH_PAGE_SIZE } from "@/lib/issueWorkbench";

export function useIssuesWorkbench() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Issue | null>(null);
  const [resolution, setResolution] = useState("");

  const loadIssues = () => {
    const params: Record<string, string> = {
      page: String(page),
      page_size: String(ISSUE_WORKBENCH_PAGE_SIZE),
    };
    if (statusFilter) params.status_filter = statusFilter;
    if (search) params.search = search;
    api
      .getIssues(params)
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
  };

  const handleStatusChange = async (issue: Issue, status: string) => {
    await api.updateIssueStatus(
      issue.id,
      status,
      status === "RESOLVED" ? resolution || undefined : undefined,
    );
    loadIssues();
    if (selected?.id === issue.id) {
      setSelected(await api.getIssue(issue.id));
    }
  };

  const totalPages = Math.ceil(total / ISSUE_WORKBENCH_PAGE_SIZE) || 1;

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
  };
}
