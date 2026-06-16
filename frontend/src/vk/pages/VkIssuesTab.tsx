import { useCallback, useState } from "react";
import { LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { Badge } from "@/components/ui/badge";
import { api, Issue } from "@/lib/api";
import { EMPTY_STATES } from "@/lib/literaryCopy";
import { ISSUE_ACTIVE_STATUSES, ISSUE_DONE_STATUSES, STATUS_COLORS, STATUS_LABELS, formatDate } from "@/lib/utils";
import { VkErrorState } from "@/vk/components/VkErrorState";
import { VkSkeletonList } from "@/vk/components/VkSkeleton";
import { useAsyncData } from "@/vk/hooks/useAsyncData";
import { useVkAuth } from "@/vk/VkAuthContext";
import { useVkNavigation } from "@/vk/VkNavigationContext";
import { parseApiError } from "@/vk/lib/errors";

type IssueFilter = "all" | "active" | "done";

export function VkIssuesTab() {
  const { user, loading: authLoading, error: authError, refreshAuth } = useVkAuth();
  const { openIssue } = useVkNavigation();
  const [issueFilter, setIssueFilter] = useState<IssueFilter>("all");
  const [showForm, setShowForm] = useState(true);
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");

  const loader = useCallback(async () => {
    if (!user) return [];
    const r = await api.getMyIssues({ limit: "30" });
    return r.items;
  }, [user]);

  const { data: issues, loading, error, reload } = useAsyncData<Issue[]>(loader, [user?.id], { enabled: Boolean(user) });

  const filteredIssues = (issues || []).filter((issue) => {
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
      reload();
    } catch (err) {
      setMsgType("err");
      setMsg(parseApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (authLoading) {
    return <VkSkeletonList count={2} />;
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
          <p className="text-xs text-muted-foreground m-0">ИИ подскажет категорию. Ответ и комментарии — в карточке обращения.</p>
          <button type="submit" className="literary-btn literary-btn--primary w-full" disabled={submitting}>
            {submitting ? "Отправляем…" : "Отправить обращение"}
          </button>
        </form>
      )}

      {msg && <p className={`text-sm ${msgType === "ok" ? "alert-success" : "alert-error"}`}>{msg}</p>}

      {(issues?.length || 0) > 0 && (
        <div className="vk-filter-row">
          <button
            type="button"
            className={`vk-filter-chip${issueFilter === "all" ? " vk-filter-chip--active" : ""}`}
            onClick={() => setIssueFilter("all")}
          >
            Все ({issues?.length || 0})
          </button>
          <button
            type="button"
            className={`vk-filter-chip${issueFilter === "active" ? " vk-filter-chip--active" : ""}`}
            onClick={() => setIssueFilter("active")}
          >
            В работе ({issues?.filter((i) => ISSUE_ACTIVE_STATUSES.has(i.status)).length || 0})
          </button>
          <button
            type="button"
            className={`vk-filter-chip${issueFilter === "done" ? " vk-filter-chip--active" : ""}`}
            onClick={() => setIssueFilter("done")}
          >
            Завершённые ({issues?.filter((i) => ISSUE_DONE_STATUSES.has(i.status)).length || 0})
          </button>
        </div>
      )}

      {loading ? (
        <VkSkeletonList count={3} />
      ) : error ? (
        <VkErrorState message={error} onRetry={reload} />
      ) : filteredIssues.length === 0 ? (
        <LiteraryEmptyState
          {...(issueFilter === "all" ? EMPTY_STATES.complaintsMine : { icon: "🔍", title: "Нет по фильтру", text: "Попробуйте другой статус." })}
          compact
        />
      ) : (
        <div className="space-y-3">
          {filteredIssues.map((issue) => (
            <button
              key={issue.id}
              type="button"
              className="vk-card-button"
              onClick={() => openIssue(issue.id)}
            >
              <article className="literary-issue-card">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-sm text-muted-foreground">#{issue.id}</span>
                  <Badge className={STATUS_COLORS[issue.status]}>{STATUS_LABELS[issue.status]}</Badge>
                </div>
                <p className="m-0 text-sm leading-relaxed line-clamp-3">{issue.description}</p>
                {issue.created_at && (
                  <p className="text-xs text-muted-foreground mt-2 mb-0">Создано: {formatDate(issue.created_at)}</p>
                )}
                {issue.status_timeline && issue.status_timeline.length > 0 && (
                  <p className="text-xs text-muted-foreground mt-2 mb-0">
                    Последний статус: {STATUS_LABELS[issue.status_timeline[issue.status_timeline.length - 1].status as keyof typeof STATUS_LABELS] || issue.status}
                  </p>
                )}
                <span className="vk-issue-open-hint">Открыть →</span>
              </article>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
