import { LiteraryEmptyState } from "@/components/literary";

interface VkErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
}

export function VkErrorState({
  title = "Не удалось загрузить",
  message,
  onRetry,
  retryLabel = "Повторить",
}: VkErrorStateProps) {
  return (
    <LiteraryEmptyState icon="⚠️" title={title} text={message} compact>
      {onRetry && (
        <button type="button" className="literary-btn literary-btn--primary mt-2" onClick={onRetry}>
          {retryLabel}
        </button>
      )}
    </LiteraryEmptyState>
  );
}
