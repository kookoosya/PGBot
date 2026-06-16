import type { ReactNode, Ref } from "react";
import { Link } from "react-router-dom";
import type { Issue } from "@/lib/api";
import { formatDate, issueStatusHint, STATUS_COLORS, STATUS_LABELS } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

type LiteraryIssueCardVariant = "static" | "selectable" | "link";

interface LiteraryIssueCardProps {
  issue: Issue;
  variant?: LiteraryIssueCardVariant;
  selected?: boolean;
  highlighted?: boolean;
  href?: string;
  onClick?: () => void;
  cardRef?: Ref<HTMLElement>;
  showStatusHint?: boolean;
  showTimeline?: boolean;
  showResolution?: boolean;
  footer?: ReactNode;
}

function IssueCardBody({
  issue,
  showStatusHint,
}: {
  issue: Issue;
  showStatusHint?: boolean;
}) {
  return (
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
        <p className="literary-issue-summary mt-2">
          {issue.ai_analysis?.summary || issue.description}
        </p>
        {showStatusHint && issueStatusHint(issue.status) && (
          <p className="text-sm text-muted-foreground mt-1">{issueStatusHint(issue.status)}</p>
        )}
        {issue.address && (
          <p className="literary-issue-address">📍 {issue.address}</p>
        )}
      </div>
      <span className="literary-issue-date">{formatDate(issue.created_at)}</span>
    </div>
  );
}

function IssueTimeline({ issue }: { issue: Issue }) {
  if (!issue.status_timeline?.length) return null;
  return (
    <div className="mt-3 pt-3 border-t border-dashed border-border/60">
      <p className="event-detail-label mb-2">История статусов</p>
      <ol className="issue-status-timeline">
        {issue.status_timeline.map((event, index) => (
          <li
            key={`${event.at}-${event.status}-${index}`}
            className={index === issue.status_timeline!.length - 1 ? "issue-status-timeline-item--current" : ""}
          >
            <span className="issue-status-timeline-dot" aria-hidden />
            <div>
              <p className="issue-status-timeline-label">{event.label}</p>
              {event.previous_status && index > 0 && (
                <p className="issue-status-timeline-prev">
                  из «{STATUS_LABELS[event.previous_status] || event.previous_status}»
                </p>
              )}
              {event.resolution && (
                <p className="issue-status-timeline-resolution">{event.resolution}</p>
              )}
              <p className="issue-status-timeline-date">{formatDate(event.at)}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

/** Unified issue row for public, official and cabinet views. */
export function LiteraryIssueCard({
  issue,
  variant = "static",
  selected = false,
  highlighted = false,
  href,
  onClick,
  cardRef,
  showStatusHint = false,
  showTimeline = false,
  showResolution = false,
  footer,
}: LiteraryIssueCardProps) {
  const className = [
    variant === "link" ? "literary-cabinet-issue literary-cabinet-issue--link" : "literary-issue-card",
    variant === "static" ? "literary-issue-card--static" : "",
    variant === "selectable" ? "w-full text-left" : "",
    selected ? "literary-issue-card--selected" : "",
    highlighted ? "literary-issue-card--highlight" : "",
    variant === "link" ? "block no-underline text-inherit" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const content = (
    <>
      <IssueCardBody issue={issue} showStatusHint={showStatusHint} />
      {showTimeline && <IssueTimeline issue={issue} />}
      {showResolution && issue.resolution_text && (
        <div className="literary-page-note mt-3">
          <strong>Ответ службы:</strong>
          <p className="m-0 mt-1">{issue.resolution_text}</p>
        </div>
      )}
      {footer}
    </>
  );

  if (variant === "link" && href) {
    return (
      <Link to={href} className={className} ref={cardRef as Ref<HTMLAnchorElement>}>
        {content}
      </Link>
    );
  }

  if (variant === "selectable") {
    return (
      <button type="button" className={className} onClick={onClick} ref={cardRef as Ref<HTMLButtonElement>}>
        {content}
      </button>
    );
  }

  return (
    <article className={className} ref={cardRef as Ref<HTMLElement>}>
      {content}
    </article>
  );
}
