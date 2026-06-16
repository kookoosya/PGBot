import type { ReactNode, Ref } from "react";

export type PostSubmitTone = "ok" | "err";
export type PostSubmitVariant = "alert" | "gold-panel";

interface PostSubmitPanelProps {
  tone: PostSubmitTone;
  message: string;
  entityId?: number | null;
  entityNoun?: string;
  hint?: string;
  variant?: PostSubmitVariant;
  actions?: ReactNode;
  panelRef?: Ref<HTMLDivElement>;
  className?: string;
}

function panelClass(tone: PostSubmitTone, variant: PostSubmitVariant): string {
  if (tone === "err") return "alert-error";
  if (variant === "gold-panel") {
    return "mb-6 page-panel space-y-2 page-panel--gold post-submit-panel";
  }
  return "alert-success space-y-3 post-submit-panel";
}

/** Единый блок успеха/ошибки после отправки формы */
export function PostSubmitPanel({
  tone,
  message,
  entityId,
  entityNoun = "Заявка",
  hint,
  variant = "alert",
  actions,
  panelRef,
  className = "",
}: PostSubmitPanelProps) {
  if (!message) return null;

  return (
    <div ref={panelRef} className={`${panelClass(tone, variant)} ${className}`.trim()}>
      {tone === "ok" && entityId != null && (
        <p className="post-submit-hero m-0">✓ {entityNoun} #{entityId} принята</p>
      )}
      <p className={`m-0 ${tone === "ok" && variant === "gold-panel" ? "font-medium" : ""}`}>{message}</p>
      {tone === "ok" && hint && <p className="text-sm text-muted-foreground m-0">{hint}</p>}
      {tone === "ok" && actions && <div className="flex flex-wrap gap-3">{actions}</div>}
    </div>
  );
}
