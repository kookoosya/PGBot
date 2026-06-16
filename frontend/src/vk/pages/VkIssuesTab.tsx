import { useEffect, useState } from "react";
import { LiteraryEmptyState, LiteraryInlineLoader, LiterarySectionHead } from "@/components/literary";
import { Badge } from "@/components/ui/badge";
import { api, Issue } from "@/lib/api";
import { EMPTY_STATES } from "@/lib/literaryCopy";
import { STATUS_COLORS, STATUS_LABELS, formatDate } from "@/lib/utils";
import { useVkAuth } from "@/vk/VkAuthContext";

export function VkIssuesTab() {
  const { user, loading: authLoading, error: authError, refreshAuth } = useVkAuth();
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(false);
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");

  useEffect(() => {
    if (!user) {
      setIssues([]);
      return;
    }
    setLoading(true);
    api
      .getMyIssues({ limit: "20" })
      .then((r) => setIssues(r.items))
      .catch(() => setIssues([]))
      .finally(() => setLoading(false));
  }, [user]);

  const submitIssue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setSubmitting(true);
    setMsg("");
    try {
      const issue = await api.createIssue({ description });
      setMsgType("ok");
      setMsg(`Обращение #${issue.id} принято`);
      setDescription("");
      const list = await api.getMyIssues({ limit: "20" });
      setIssues(list.items);
    } catch (err) {
      setMsgType("err");
      setMsg(err instanceof Error ? err.message : "Не удалось отправить");
    } finally {
      setSubmitting(false);
    }
  };

  if (authLoading) {
    return <LiteraryInlineLoader label="Входим через VK…" />;
  }

  if (authError) {
    return (
      <section className="vk-tab-panel">
        <LiteraryEmptyState icon="🔐" title="Нужен вход VK" text={authError} compact>
          <button type="button" className="literary-btn literary-btn--primary mt-2" onClick={() => void refreshAuth()}>
            Повторить
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
        lead={user?.full_name ? `Здравствуйте, ${user.full_name}` : "Сообщите о проблеме в посёлке."}
      />

      <form onSubmit={submitIssue} className="page-panel page-panel--gold mb-4 space-y-3 literary-form-comfort">
        <textarea
          className="literary-textarea w-full min-h-[100px]"
          placeholder="Опишите проблему: фонарь, дорога, мусор…"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          minLength={5}
        />
        <button type="submit" className="literary-btn literary-btn--primary w-full" disabled={submitting}>
          {submitting ? "Отправляем…" : "Отправить обращение"}
        </button>
      </form>

      {msg && <p className={`text-sm mb-3 ${msgType === "ok" ? "alert-success" : "alert-error"}`}>{msg}</p>}

      {loading ? (
        <LiteraryInlineLoader label="Загружаем обращения…" compact />
      ) : issues.length === 0 ? (
        <LiteraryEmptyState {...EMPTY_STATES.complaintsMine} compact />
      ) : (
        <div className="space-y-3">
          {issues.map((issue) => (
            <article key={issue.id} className="literary-issue-card literary-issue-card--static">
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-sm text-muted-foreground">#{issue.id}</span>
                <Badge className={STATUS_COLORS[issue.status]}>{STATUS_LABELS[issue.status]}</Badge>
              </div>
              <p className="m-0 text-sm">{issue.description}</p>
              {issue.created_at && (
                <p className="text-xs text-muted-foreground mt-2 mb-0">{formatDate(issue.created_at)}</p>
              )}
              {issue.status_timeline && issue.status_timeline.length > 0 && (
                <ul className="issue-status-timeline mt-3">
                  {issue.status_timeline.slice(-3).map((step, idx) => (
                    <li key={`${issue.id}-${step.status}-${idx}`}>
                      <span className="issue-status-timeline-dot" aria-hidden />
                      <div>
                        <strong>{STATUS_LABELS[step.status as keyof typeof STATUS_LABELS] || step.status}</strong>
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
