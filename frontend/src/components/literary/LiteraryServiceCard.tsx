import { telHref } from "@/components/VkBotLink";
import type { CatalogItem } from "@/lib/api";

interface LiteraryServiceCardProps {
  item: CatalogItem;
  icon: string;
}

/** Карточка услуги из справочника в стиле «Пушкиногорский альбом» */
export function LiteraryServiceCard({ item, icon }: LiteraryServiceCardProps) {
  return (
    <article className="literary-service-card literary-card literary-card--gold">
      <div className="literary-service-card-inner">
        <span className="literary-service-icon" aria-hidden>{icon}</span>
        <div className="literary-service-body">
          <h3 className="literary-service-title">{item.name}</h3>
          <p className="literary-card-kicker">{item.category_label}</p>
          {item.description && <p className="literary-service-desc">{item.description}</p>}
          {item.price_hint && <p className="literary-service-price">{item.price_hint}</p>}
          {item.address && <p className="literary-service-address">📍 {item.address}</p>}
          <div className="literary-service-actions">
            {item.phone && (
              <a href={telHref(item.phone)} className="literary-btn literary-btn--primary text-xs px-3 py-1.5 no-underline">
                📞 Позвонить
              </a>
            )}
            {item.external_url && (
              <a
                href={item.external_url}
                target="_blank"
                rel="noopener noreferrer"
                className="literary-btn literary-btn--ghost text-xs px-3 py-1.5 no-underline"
              >
                Подробнее →
              </a>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}
