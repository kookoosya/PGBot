import { useCallback, useState } from "react";
import { LiterarySectionHead } from "@/components/literary";
import { Badge } from "@/components/ui/badge";
import { api, Issue, IssueComment } from "@/lib/api";
import { STATUS_COLORS, STATUS_LABELS, formatDate } from "@/lib/utils";
import { VkBackBar } from "@/vk/components/VkBackBar";
import { VkErrorState } from "@/vk/components/VkErrorState";
import { VkSkeletonDetail } from "@/vk/components/VkSkeleton";
import { useAsyncData } from "@/vk/hooks/useAsyncData";
import { useVkAuth } from "@/vk/VkAuthContext";
import { useVkNavigation } from "@/vk/VkNavigationContext";
import { parseApiError } from "@/vk/lib/errors";

interface VkIssueDetailProps {
  issueId: number;
}

export function VkIssueDetail({ issueId }: VkIssueDetailProps) {
  const { goBack } = useVkNavigation();
  const { user } = useVkAuth();
  const [commentText, setCommentText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [commentError, setCommentError] = useState("");

  const loadIssue = useCallback(() => api.getIssue(issueId), [issueId]);
  const loadComments = useCallback(() => api.getIssueComments(issueId).then((r) => r.items), [issueId]);

  const { data: issue, loading, error, reload } = useAsyncData<Issue>(loadIssue, [issueId]);
  const {
    data: comments,
    loading: commentsLoading,
    reload: reloadComments,
    setData: setComments,
  } = useAsyncData<IssueComment[]>(loadComments, [issueId]);

  const submitComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || commentText.trim().length < 2) {
      setCommentError("Комментарий — минимум 2 символа.");
      return;
    }
    setSubmitting(true);
    setCommentError("");
    try {
      const comment = await api.addIssueComment(issueId, commentText.trim());
      setComments((prev) => [...(prev || []), comment]);
      setCommentText("");
    } catch (err) {
      setCommentError(parseApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <section className="vk-tab-panel vk-screen-enter">
        <VkBackBar title="Обращение" onBack={goBack} />
        <VkSkeletonDetail />
      </section>
    );
  }

  if (error || !issue) {
    return (
      <section className="vk-tab-panel">
        <VkBackBar title="Обращение" onBack={goBack} />
        <VkErrorState title="Обращение недоступно" message={error || "Не найдено"} onRetry={reload} />
      </section>
    );
  }

  const timeline = issue.status_timeline || [];

  return (
    <section className="vk-tab-panel vk-screen-enter">
      <VkBackBar title={`Обращение #${issue.id}`} onBack={goBack} />

      <article className="literary-issue-card literary-issue-card--static">
        <div className="flex items-center justify-between gap-2 mb-2">
          <span className="text-sm text-muted-foreground">#{issue.id}</span>
          <Badge className={STATUS_COLORS[issue.status]}>{STATUS_LABELS[issue.status]}</Badge>
        </div>
        <p className="m-0 text-sm leading-relaxed">{issue.description}</p>
        {issue.created_at && (
          <p className="text-xs text-muted-foreground mt-2 mb-0">Создано: {formatDate(issue.created_at)}</p>
        )}
        {timeline.length > 0 && (
          <ul className="issue-status-timeline mt-3">
            {timeline.map((step, idx) => (
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

      <LiterarySectionHead kicker="💬 Переписка" title="Комментарии" />
      {commentsLoading && !comments?.length ? (
        <p className="text-sm text-muted-foreground m-0">Загружаем комментарии…</p>
      ) : !comments?.length ? (
        <p className="text-sm text-muted-foreground m-0">Пока нет комментариев. Напишите, если нужно уточнить детали.</p>
      ) : (
        <ul className="vk-comment-list">
          {comments.map((comment) => (
            <li key={comment.id} className="vk-comment-item">
              <p className="vk-comment-meta">
                <strong>{comment.author_name || "Участник"}</strong>
                <span>{formatDate(comment.created_at)}</span>
              </p>
              <p className="m-0 text-sm">{comment.text}</p>
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={submitComment} className="page-panel page-panel--gold space-y-2 literary-form-comfort">
        <textarea
          className="literary-textarea w-full min-h-[72px]"
          placeholder="Дополните обращение…"
          value={commentText}
          onChange={(e) => setCommentText(e.target.value)}
          minLength={2}
        />
        {commentError && <p className="alert-error text-sm m-0">{commentError}</p>}
        <button type="button" className="literary-btn literary-btn--ghost text-sm" onClick={() => reloadComments()}>
          Обновить комментарии
        </button>
        <button type="submit" className="literary-btn literary-btn--primary w-full" disabled={submitting}>
          {submitting ? "Отправляем…" : "Добавить комментарий"}
        </button>
      </form>
    </section>
  );
}
