import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { Badge } from "@/components/ui/badge";
import { api, Issue } from "@/lib/api";
import { EMPTY_STATES, LITERARY_VERSES, PAGE_SECTIONS } from "@/lib/literaryCopy";
import { useUserAuth } from "@/lib/userAuth";
import { formatDate, STATUS_COLORS, STATUS_LABELS } from "@/lib/utils";

const STATUSES = ["NEW", "UNDER_REVIEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "REJECTED"];

const ROLE_LABELS: Record<string, string> = {
  administration: "Администрация",
  social_service: "ЖКХ / соцслужбы",
  moderator: "Модератор",
};

const copy = PAGE_SECTIONS.official;

export function OfficialIssues() {
  const { user, logout } = useUserAuth();
  const [issues, setIssues] = useState<Issue[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Issue | null>(null);
  const [resolution, setResolution] = useState("");

  const loadIssues = () => {
    const params: Record<string, string> = { page: String(page), page_size: "20" };
    if (statusFilter) params.status_filter = statusFilter;
    if (search) params.search = search;
    api.getIssues(params).then((r) => {
      setIssues(r.items);
      setTotal(r.total);
    }).catch(console.error);
  };

  useEffect(() => { loadIssues(); }, [page, statusFilter]);

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

  return (
    <div className="literary-page page-section max-w-6xl space-y-6">
      <PageHeader
        icon="🏛"
        title={copy.title}
        subtitle={`${user?.organization || user?.full_name || ""}${user?.role ? ` · ${ROLE_LABELS[user.role] || user.role}` : ""}`}
      >
        <Link to="/" className="literary-btn literary-btn--ghost text-sm no-underline">На главную</Link>
        <Link to="/complaints" className="literary-btn literary-btn--ghost text-sm no-underline">Форма жалобы</Link>
        <button type="button" className="literary-btn literary-btn--ghost text-sm" onClick={logout}>Выйти</button>
      </PageHeader>

      <section className="page-panel page-panel--gold">
        <LiterarySectionHead kicker={copy.kicker} title="Фильтр обращений" lead={copy.lead} />
        <div className="flex flex-wrap gap-3">
          <select
            className="pushkin-select"
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          >
            <option value="">Все статусы</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>{STATUS_LABELS[s]}</option>
            ))}
          </select>
          <input
            className="pushkin-select flex-1 min-w-[12rem]"
            placeholder="Поиск по тексту…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && loadIssues()}
          />
          <button type="button" className="literary-btn literary-btn--primary" onClick={loadIssues}>
            Найти
          </button>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-3">
          {issues.map((issue) => (
            <button
              key={issue.id}
              type="button"
              className={`literary-issue-card w-full text-left${selected?.id === issue.id ? " literary-issue-card--selected" : ""}`}
              onClick={() => { setSelected(issue); setResolution(issue.resolution_text || ""); }}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="literary-issue-id">#{issue.id}</span>
                    <Badge className={STATUS_COLORS[issue.status]}>
                      {STATUS_LABELS[issue.status]}
                    </Badge>
                    {issue.category && (
                      <Badge className="bg-gray-100 text-gray-700">{issue.category}</Badge>
                    )}
                  </div>
                  <p className="literary-issue-summary mt-2">{issue.ai_analysis?.summary || issue.description}</p>
                  {issue.address && (
                    <p className="literary-issue-address">📍 {issue.address}</p>
                  )}
                </div>
                <span className="literary-issue-date">
                  {formatDate(issue.created_at)}
                </span>
              </div>
            </button>
          ))}
          {issues.length === 0 && (
            <LiteraryEmptyState {...EMPTY_STATES.official} compact />
          )}
          <div className="flex justify-between pt-2">
            <button type="button" className="literary-btn literary-btn--ghost text-sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
              Назад
            </button>
            <span className="landing-muted self-center text-sm">
              Стр. {page} из {Math.ceil(total / 20) || 1}
            </span>
            <button type="button" className="literary-btn literary-btn--ghost text-sm" disabled={page * 20 >= total} onClick={() => setPage(page + 1)}>
              Далее
            </button>
          </div>
        </div>

        {selected && (
          <div className="page-panel page-panel--forest h-fit sticky top-8 space-y-4">
            <LiterarySectionHead
              kicker="📬 Обращение"
              title={`#${selected.id}`}
              lead={formatDate(selected.created_at)}
            />
            <div>
              <p className="event-detail-label">Описание</p>
              <p className="event-detail-text">{selected.description}</p>
            </div>
            {selected.ai_analysis && (
              <div className="literary-page-note">
                <p className="m-0 text-sm"><strong>AI:</strong> {selected.ai_analysis.summary}</p>
                <p className="m-0 text-sm mt-1">Категория: {selected.ai_analysis.category}</p>
                <p className="m-0 text-sm">Приоритет: {selected.ai_analysis.priority}</p>
              </div>
            )}
            <div>
              <p className="event-detail-label mb-2">Комментарий при закрытии</p>
              <textarea
                className="literary-textarea w-full min-h-[60px]"
                value={resolution}
                onChange={(e) => setResolution(e.target.value)}
                placeholder="Что сделано…"
              />
            </div>
            <div>
              <p className="event-detail-label mb-2">Статус</p>
              <div className="flex flex-wrap gap-2">
                {STATUSES.map((s) => (
                  <button
                    key={s}
                    type="button"
                    className={`literary-btn text-xs py-1 px-2 ${selected.status === s ? "literary-btn--primary" : "literary-btn--ghost"}`}
                    onClick={() => handleStatusChange(selected, s)}
                  >
                    {STATUS_LABELS[s]}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      <p className="literary-page-verse" aria-hidden>{LITERARY_VERSES.official}</p>
    </div>
  );
}
