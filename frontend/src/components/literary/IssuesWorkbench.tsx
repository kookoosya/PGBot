import type { ReactNode } from "react";
import type { Issue } from "@/lib/api/types/issues";
import { EMPTY_STATES } from "@/lib/literaryCopy";
import { ISSUE_WORKBENCH_STATUSES } from "@/lib/issueWorkbench";
import { formatDate, STATUS_LABELS } from "@/lib/utils";
import { LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { LiteraryIssueCard } from "./LiteraryIssueCard";

type IssuesWorkbenchShell = "literary" | "admin";

interface IssuesWorkbenchProps {
  shell: IssuesWorkbenchShell;
  issues: Issue[];
  total: number;
  page: number;
  totalPages: number;
  statusFilter: string;
  search: string;
  selected: Issue | null;
  resolution: string;
  onStatusFilterChange: (value: string) => void;
  onSearchChange: (value: string) => void;
  onSearch: () => void;
  onPageChange: (page: number) => void;
  onSelectIssue: (issue: Issue) => void;
  onResolutionChange: (value: string) => void;
  onStatusChange: (issue: Issue, status: string) => void;
  showResolution?: boolean;
  showAdminExtras?: boolean;
  filterLead?: string;
  headerExtra?: ReactNode;
}

function FilterBar({
  shell,
  statusFilter,
  search,
  onStatusFilterChange,
  onSearchChange,
  onSearch,
  onPageReset,
}: {
  shell: IssuesWorkbenchShell;
  statusFilter: string;
  search: string;
  onStatusFilterChange: (value: string) => void;
  onSearchChange: (value: string) => void;
  onSearch: () => void;
  onPageReset: () => void;
}) {
  const selectClass = shell === "literary" ? "pushkin-select" : "issues-workbench-select";
  const inputClass = shell === "literary" ? "pushkin-select flex-1 min-w-[12rem]" : "issues-workbench-input";
  const btnClass = shell === "literary" ? "literary-btn literary-btn--primary" : "issues-workbench-btn issues-workbench-btn--primary";

  return (
    <div className="flex flex-wrap gap-3">
      <select
        className={selectClass}
        value={statusFilter}
        onChange={(e) => {
          onStatusFilterChange(e.target.value);
          onPageReset();
        }}
      >
        <option value="">Все статусы</option>
        {ISSUE_WORKBENCH_STATUSES.map((s) => (
          <option key={s} value={s}>{STATUS_LABELS[s]}</option>
        ))}
      </select>
      <input
        className={inputClass}
        placeholder={shell === "literary" ? "Поиск по тексту…" : "Поиск..."}
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && onSearch()}
      />
      <button type="button" className={btnClass} onClick={onSearch}>
        Найти
      </button>
    </div>
  );
}

function Pagination({
  shell,
  page,
  totalPages,
  onPageChange,
}: {
  shell: IssuesWorkbenchShell;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  const prevClass = shell === "literary"
    ? "literary-btn literary-btn--ghost text-sm"
    : "issues-workbench-btn issues-workbench-btn--ghost";
  const labelClass = shell === "literary" ? "landing-muted self-center text-sm" : "issues-workbench-muted";

  return (
    <div className="flex justify-between pt-2">
      <button type="button" className={prevClass} disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
        Назад
      </button>
      <span className={labelClass}>
        Стр. {page} из {totalPages}
      </span>
      <button type="button" className={prevClass} disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
        Далее
      </button>
    </div>
  );
}

function DetailPanel({
  shell,
  selected,
  resolution,
  showResolution,
  showAdminExtras,
  onResolutionChange,
  onStatusChange,
}: {
  shell: IssuesWorkbenchShell;
  selected: Issue;
  resolution: string;
  showResolution: boolean;
  showAdminExtras: boolean;
  onResolutionChange: (value: string) => void;
  onStatusChange: (issue: Issue, status: string) => void;
}) {
  const statusBtnClass = (active: boolean) =>
    shell === "literary"
      ? `literary-btn text-xs py-1 px-2 ${active ? "literary-btn--primary" : "literary-btn--ghost"}`
      : `issues-workbench-btn text-xs py-1 px-2 ${active ? "issues-workbench-btn--primary" : "issues-workbench-btn--ghost"}`;

  const aiBlock = selected.ai_analysis && (
    <div className={shell === "literary" ? "literary-page-note" : "issues-workbench-note"}>
      <p className="m-0 text-sm"><strong>AI:</strong> {selected.ai_analysis.summary}</p>
      <p className="m-0 text-sm mt-1">Категория: {selected.ai_analysis.category}</p>
      <p className="m-0 text-sm">Приоритет: {selected.ai_analysis.priority}</p>
      {showAdminExtras && selected.ai_analysis.suggested_department && (
        <p className="m-0 text-sm">Отдел: {selected.ai_analysis.suggested_department}</p>
      )}
      {showAdminExtras && selected.ai_analysis.duplicate_probability != null && (
        <p className="m-0 text-sm">
          Дубликат: {(selected.ai_analysis.duplicate_probability * 100).toFixed(0)}%
        </p>
      )}
    </div>
  );

  const panelClass = shell === "literary"
    ? "page-panel page-panel--forest h-fit sticky top-8 space-y-4"
    : "issues-workbench-detail sticky top-8 space-y-4";

  return (
    <div className={panelClass}>
      {shell === "literary" ? (
        <LiterarySectionHead
          kicker="📬 Обращение"
          title={`#${selected.id}`}
          lead={formatDate(selected.created_at)}
        />
      ) : (
        <div>
          <h3 className="issues-workbench-detail-title">Обращение #{selected.id}</h3>
          <p className="issues-workbench-muted text-sm">{formatDate(selected.created_at)}</p>
        </div>
      )}
      <div>
        <p className="event-detail-label">Описание</p>
        <p className={shell === "literary" ? "event-detail-text" : "issues-workbench-text"}>{selected.description}</p>
      </div>
      {aiBlock}
      {showAdminExtras && selected.photos.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {selected.photos.map((p) => (
            <img key={p.id} src={p.url} alt="" className="h-20 w-20 rounded object-cover" />
          ))}
        </div>
      )}
      {showResolution && (
        <div>
          <p className="event-detail-label mb-2">Комментарий при закрытии</p>
          <textarea
            className={shell === "literary" ? "literary-textarea w-full min-h-[60px]" : "issues-workbench-textarea"}
            value={resolution}
            onChange={(e) => onResolutionChange(e.target.value)}
            placeholder="Что сделано…"
          />
        </div>
      )}
      <div>
        <p className="event-detail-label mb-2">{shell === "literary" ? "Статус" : "Изменить статус"}</p>
        <div className="flex flex-wrap gap-2">
          {ISSUE_WORKBENCH_STATUSES.map((s) => (
            <button
              key={s}
              type="button"
              className={statusBtnClass(selected.status === s)}
              onClick={() => onStatusChange(selected, s)}
            >
              {STATUS_LABELS[s]}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/** Shared list + detail layout for official and admin issue workbenches. */
export function IssuesWorkbench({
  shell,
  issues,
  total: _total,
  page,
  totalPages,
  statusFilter,
  search,
  selected,
  resolution,
  onStatusFilterChange,
  onSearchChange,
  onSearch,
  onPageChange,
  onSelectIssue,
  onResolutionChange,
  onStatusChange,
  showResolution = false,
  showAdminExtras = false,
  filterLead,
  headerExtra,
}: IssuesWorkbenchProps) {
  const filterWrap = shell === "literary" ? (
    <section className="page-panel page-panel--gold">
      {filterLead && (
        <LiterarySectionHead kicker="Фильтр" title="Фильтр обращений" lead={filterLead} />
      )}
      <FilterBar
        shell={shell}
        statusFilter={statusFilter}
        search={search}
        onStatusFilterChange={onStatusFilterChange}
        onSearchChange={onSearchChange}
        onSearch={onSearch}
        onPageReset={() => onPageChange(1)}
      />
      {headerExtra}
    </section>
  ) : (
    <div className="issues-workbench-filters space-y-3">
      <div>
        <h2 className="issues-workbench-title">Обращения</h2>
        <p className="issues-workbench-muted">Управление обращениями жителей</p>
      </div>
      <FilterBar
        shell={shell}
        statusFilter={statusFilter}
        search={search}
        onStatusFilterChange={onStatusFilterChange}
        onSearchChange={onSearchChange}
        onSearch={onSearch}
        onPageReset={() => onPageChange(1)}
      />
    </div>
  );

  return (
    <div className={shell === "admin" ? "issues-workbench space-y-6" : "space-y-6"}>
      {filterWrap}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-3">
          {issues.map((issue) => (
            <LiteraryIssueCard
              key={issue.id}
              issue={issue}
              variant="selectable"
              selected={selected?.id === issue.id}
              onClick={() => onSelectIssue(issue)}
            />
          ))}
          {issues.length === 0 && (
            shell === "literary" ? (
              <LiteraryEmptyState {...EMPTY_STATES.official} compact />
            ) : (
              <p className="issues-workbench-empty">Обращения не найдены</p>
            )
          )}
          <Pagination shell={shell} page={page} totalPages={totalPages} onPageChange={onPageChange} />
        </div>
        {selected && (
          <DetailPanel
            shell={shell}
            selected={selected}
            resolution={resolution}
            showResolution={showResolution}
            showAdminExtras={showAdminExtras}
            onResolutionChange={onResolutionChange}
            onStatusChange={onStatusChange}
          />
        )}
      </div>
    </div>
  );
}
