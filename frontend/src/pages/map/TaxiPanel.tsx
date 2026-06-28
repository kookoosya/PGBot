import { telHref } from "@/components/VkBotLink";
import { LiterarySectionHead } from "@/components/literary";
import type { TaxiService } from "@/lib/api/types/places";
import { PAGE_SECTIONS } from "@/lib/literaryCopy";

type TaxiPanelProps = {
  taxi: TaxiService[];
  compact?: boolean;
};

export function TaxiPanel({ taxi, compact = false }: TaxiPanelProps) {
  if (taxi.length === 0) return null;

  const copy = PAGE_SECTIONS.map.taxi;

  return (
    <div className={compact ? "taxi-compact" : "page-section pb-3"}>
      <div className={`page-panel page-panel--forest taxi-panel${compact ? " taxi-panel-compact" : ""}`}>
        {!compact && (
          <LiterarySectionHead kicker={copy.kicker} title={copy.title} lead={copy.lead} />
        )}
        <div className="taxi-grid">
          {taxi.map((t) => (
            <a key={t.id} href={telHref(t.phone)} className="taxi-card">
              <div className="taxi-card-top">
                <strong>{t.name}</strong>
                {t.is_24h && <span className="taxi-24h">24/7</span>}
              </div>
              <p className="taxi-phone">{t.phone}</p>
              {t.phones_extra && <p className="taxi-phone-extra">{t.phones_extra}</p>}
              <p className="taxi-desc">{t.description}</p>
              {t.price_from != null && (
                <div className="taxi-meta">
                  <span>от {t.price_from} ₽</span>
                </div>
              )}
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
