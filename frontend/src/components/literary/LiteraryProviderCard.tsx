import type { ServiceProvider } from "@/lib/api/types/services";
const STATUS: Record<string, { label: string; className: string }> = {
  free: { label: "🟢 Свободен", className: "literary-provider-status--free" },
  busy: { label: "🔴 Занят", className: "literary-provider-status--busy" },
  off: { label: "⚫ Выходной", className: "literary-provider-status--off" },
};

interface LiteraryProviderCardProps {
  provider: ServiceProvider;
  onBook: (provider: ServiceProvider) => void;
}

/** Карточка мастера с онлайн-записью */
export function LiteraryProviderCard({ provider, onBook }: LiteraryProviderCardProps) {
  const status = STATUS[provider.status_today] ?? STATUS.off;
  const isOff = provider.status_today === "off";

  return (
    <article
      className={`literary-provider-card literary-card literary-card--forest${isOff ? " literary-provider-card--off" : ""}`}
      role="button"
      tabIndex={isOff ? -1 : 0}
      onClick={() => !isOff && onBook(provider)}
      onKeyDown={(e) => e.key === "Enter" && !isOff && onBook(provider)}
    >
      <div className="literary-provider-header">
        <div>
          <h3 className="literary-provider-name">{provider.full_name}</h3>
          <p className={`literary-provider-status ${status.className}`}>
            {status.label}
            {provider.next_free_slot && ` · ${provider.next_free_slot}`}
          </p>
        </div>
        {provider.avg_rating > 0 && (
          <span className="literary-provider-rating">⭐ {provider.avg_rating}</span>
        )}
      </div>
      {provider.address && <p className="literary-provider-address">📍 {provider.address}</p>}
      <div className="literary-provider-services">
        {provider.services.map((s) => (
          <span key={s.id} className="literary-provider-chip">
            {s.name}{s.price ? ` — ${s.price} ₽` : ""}
          </span>
        ))}
      </div>
      <button
        type="button"
        className="literary-btn literary-btn--primary w-full mt-3 text-sm"
        onClick={(e) => { e.stopPropagation(); onBook(provider); }}
        disabled={isOff}
      >
        {isOff ? "Выходной" : "Записаться →"}
      </button>
    </article>
  );
}
