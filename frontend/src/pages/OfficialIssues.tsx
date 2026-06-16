import { Link } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { IssuesWorkbench } from "@/components/literary";
import { PAGE_SECTIONS } from "@/lib/literaryCopy";
import { useUserAuth } from "@/lib/userAuth";
import { useIssuesWorkbench } from "@/hooks/useIssuesWorkbench";

const ROLE_LABELS: Record<string, string> = {
  administration: "Администрация",
  social_service: "ЖКХ / соцслужбы",
  moderator: "Модератор",
};

const copy = PAGE_SECTIONS.official;

export function OfficialIssues() {
  const { user, logout } = useUserAuth();
  const workbench = useIssuesWorkbench();

  return (
    <div className="literary-page page-section max-w-6xl space-y-6">
      <PageHeader
        icon="🏛"
        title={copy.title}
        subtitle={`${user?.organization || user?.full_name || ""}${user?.role ? ` · ${ROLE_LABELS[user.role] || user.role}` : ""}`}
      >
        <Link to="/" className="literary-btn literary-btn--ghost text-sm no-underline">На главную</Link>
        <Link to="/complaints" className="literary-btn literary-btn--ghost text-sm no-underline">Подать обращение</Link>
        <button type="button" className="literary-btn literary-btn--ghost text-sm" onClick={logout}>Выйти</button>
      </PageHeader>

      <IssuesWorkbench
        shell="literary"
        showResolution
        filterLead={copy.lead}
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
      />
    </div>
  );
}
