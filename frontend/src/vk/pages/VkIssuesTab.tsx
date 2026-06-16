import { useCallback, useEffect, useState } from "react";
import { LiteraryEmptyState, LiteraryInlineLoader, LiterarySectionHead } from "@/components/literary";
import { Badge } from "@/components/ui/badge";
import { api, Issue } from "@/lib/api";
import { EMPTY_STATES } from "@/lib/literaryCopy";
import { ISSUE_ACTIVE_STATUSES, ISSUE_DONE_STATUSES, STATUS_COLORS, STATUS_LABELS, formatDate } from "@/lib/utils";
import { VkErrorState } from "@/vk/components/VkErrorState";
import { useVkAuth } from "@/vk/VkAuthContext";
import { parseApiError } from "@/vk/lib/errors";

type IssueFilter = "all" | "active" | "done";

export function VkIssuesTab() {
  const { user, loading: authLoading, error: authError, refreshAuth } = useVkAuth();
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [issueFilter, setIssueFilter] = useState<IssueFilter>("all");
  const [showForm, setShowForm] = useState(true);
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");

  const load = useCallback(() => {
    if (!user) return;
    setLoading(true);
    setError("");
    api
      .getMyIssues({ limit: "30" })
      .then((r) => setIssues(r.items))
      .catch((err) => setError(parseApiError(err)))
      .finally(() => setLoading(false));
  }, [user]);

  useEffect(() => {
    load();
  }, [load]);

  const filteredIssues = issues.filter((issue) => {
    if (issueFilter === "active") return ISSUE_ACTIVE_STATUSES.has(issue.status);
    if (issueFilter === "done") return ISSUE_DONE_STATUSES.has(issue.status);
    return true;
  });

  const submitIssue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    if (description.trim().length < 5) {
      setMsgType("err");
      setMsg("Опишите проблему чуть подробнее (минимум 5 символов).");
      return;
    }
    setSubmitting(true);
    setMsg("");
    try {
      const issue = await api.createIssue({ description: description.trim() });
      setMsgType("ok");
      setMsg(`Обращение #${issue.id} принято. Мы сообщим о смене статуса.`);
      setDescription("");
      setShowForm(false);
      load();
    } catch (err) {
      setMsgType("err");
      setMsg(parseApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (authLoading) {
    return <LiteraryInlineLoader label="Входим через VK…" compact />;
  }

  if (authError || !user) {
    return (
      <section className="vk-tab-panel">
        <LiteraryEmptyState
          icon="🔐"
          title="Вход через VK"
          text={authError || "Откройте мини-приложение из ВКонтакте, чтобы видеть и отправлять обращения."}
          compact
        >
          <button type="button" className="literary-btn literary-btn--primary mt-2" onClick={() => void refreshAuth()}>
            Войти снова
          </button>
        </LiteraryEmptyState>
      </section>
    );
  }

  return (
    <section className="vk-tab-panel">
      <LiterarySectionHead
        kicker="⚠️ Обращения"
        title="Мои заявки"
        lead={`Здравствуйте, ${user.full_name || "житель"}!`}
      />

      <button type="button" className="literary-btn literary-btn--primary w-full" onClick={() => setShowForm(!showForm)}>
        {showForm ? "✕ Скрыть форму" : "+ Новое обращение"}
      </button>

      {showForm && (
        <form onSubmit={submitIssue} className="page-panel page-panel--gold space-y-3 literary-form-comfort">
          <textarea
            className="literary-textarea w-full min-h-[100px]"
            placeholder="Опишите проблему: фонарь, дорога, мусор…"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
            minLength={5}
          />
          <p className="text-xs text-muted-foreground m-0">ИИ подскажет категорию. Ответ придёт в этом списке.</p>
          <button type="submit" className="literary-btn literary-btn--primary w-full" disabled={submitting}>
            {submitting ? "Отправляем…" : "Отправить обращение"}
          </button>
        </form>
      )}

      {msg && <p className={`text-sm ${msgType === "ok" ? "alert-success" : "alert-error"}`}>{msg}</p>}

      {issues.length > 0 && (
        <div className="vk-filter-row">
          <button
            type="button"
            className={`vk-filter-chip${issueFilter === "all" ? " vk-filter-chip--active" : ""}`}
            onClick={() => setIssueFilter("all")}
          >
            Все ({issues.length})
          </button>
          <button
            type="button"
            className={`vk-filter-chip${issueFilter === "active" ? " vk-filter-chip--active" : ""}`}
            onClick={() => setIssueFilter("active")}
          >
            В работе ({issues.filter((i) => ISSUE_ACTIVE_STATUSES.has(i.status)).length})
          </button>
          <button
            type="button"
            className={`vk-filter-chip${issueFilter === "done" ? " vk-filter-chip--active" : ""}`}
            onClick={() => setIssueFilter("done")}
          >
            Завершённые ({issues.filter((i) => ISSUE_DONE_STATUSES.has(i.status)).length})
          </button>
        </div>
      )}

      {loading ? (
        <LiteraryInlineLoader label="Загружаем обращения…" compact />
      ) : error ? (
        <VkErrorState message={error} onRetry={load} />
      ) : filteredIssues.length === 0 ? (
        <LiteraryEmptyState
          {...(issueFilter === "all" ? EMPTY_STATES.complaintsMine : { icon: "🔍", title: "Нет по фильтру", text: "Попробуйте другой статус." })}
          compact
        />
      ) : (
        <div className="space-y-3">
          {filteredIssues.map((issue) => (
            <article key={issue.id} className="literary-issue-card literary-issue-card--static">
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-sm text-muted-foreground">#{issue.id}</span>
                <Badge className={STATUS_COLORS[issue.status]}>{STATUS_LABELS[issue.status]}</Badge>
              </div>
              <p className="m-0 text-sm leading-relaxed">{issue.description}</p>
              {issue.created_at && (
                <p className="text-xs text-muted-foreground mt-2 mb-0">Создано: {formatDate(issue.created_at)}</p>
              )}
              {issue.status_timeline && issue.status_timeline.length > 0 && (
                <ul className="issue-status-timeline mt-3">
                  {issue.status_timeline.map((step, idx) => (
                    <li key={`${issue.id}-${step.status}-${idx}`}>
                      <span className="issue-status-timeline-dot" aria-hidden />
                      <div>
                        <strong>{STATUS_LABELS[step.status as keyof typeof STATUS_LABELS] || step.label || step.status}</strong>
                        {step.resolution && <p className="text-xs m-0 mt-0.5">{step.resolution}</p>}
                        {step.at && <div className="text-xs text-muted-foreground">{formatDate(step.at)}</div>}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
