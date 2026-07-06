import { IssuesWorkbench } from "@/components/literary";
import { useIssuesWorkbench } from "@/hooks/useIssuesWorkbench";

export function Issues() {
  const workbench = useIssuesWorkbench();

  return (
    <IssuesWorkbench
      shell="admin"
      showAdminExtras
      issues={workbench.issues}
      total={workbench.total}
      page={workbench.page}
      totalPages={workbench.totalPages}
      statusFilter={workbench.statusFilter}
      search={workbench.search}
      selected={workbench.selected}
      resolution={workbench.resolution}
      onStatusFilterChange={(value) => workbench.setStatusFilter(value)}
      onSearchChange={workbench.setSearch}
      onSearch={workbench.loadIssues}
      onPageChange={workbench.setPage}
      onSelectIssue={workbench.selectIssue}
      onResolutionChange={workbench.setResolution}
        onStatusChange={workbench.handleStatusChange}
        statusError={workbench.statusError}
      />
  );
}
