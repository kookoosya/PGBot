import { telHref } from "@/components/VkBotLink";
import { LiterarySectionHead } from "@/components/literary";
import type { TaxiService } from "@/lib/api";
import { PAGE_SECTIONS } from "@/lib/literaryCopy";

type TaxiPanelProps = {
  taxi: TaxiService[];
  taxiMode: boolean;
};

export function TaxiPanel({ taxi, taxiMode }: TaxiPanelProps) {
  if (taxi.length === 0) return null;

  return (
    <div className="page-section pb-3">
      <div className={`page-panel page-panel--forest taxi-panel${taxiMode ? " taxi-panel-active" : ""}`}>
        <LiterarySectionHead
          kicker={PAGE_SECTIONS.map.taxi.kicker}
          title={`${PAGE_SECTIONS.map.taxi.title}${taxiMode ? " в посёлке" : ""}`}
          lead={PAGE_SECTIONS.map.taxi.lead}
        />
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
              <div className="taxi-meta">
                {t.rating > 0 && <span>★ {t.rating}</span>}
                {t.price_from != null && <span>от {t.price_from} ₽</span>}
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
