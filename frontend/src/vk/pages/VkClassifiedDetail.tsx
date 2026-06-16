import { useEffect, useState } from "react";
import { LiteraryInlineLoader, LiterarySectionHead } from "@/components/literary";
import { api, ClassifiedAd } from "@/lib/api";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import { formatShortDate } from "@/lib/utils";
import { VkBackBar } from "@/vk/components/VkBackBar";
import { VkErrorState } from "@/vk/components/VkErrorState";
import { useVkNavigation } from "@/vk/VkNavigationContext";
import { parseApiError } from "@/vk/lib/errors";

interface VkClassifiedDetailProps {
  adId: number;
}

export function VkClassifiedDetail({ adId }: VkClassifiedDetailProps) {
  const { goBack } = useVkNavigation();
  const [ad, setAd] = useState<ClassifiedAd | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    setError("");
    api
      .getClassified(adId)
      .then(setAd)
      .catch((err) => {
        setAd(null);
        setError(parseApiError(err));
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, [adId]);

  if (loading) {
    return <LiteraryInlineLoader label="Загружаем объявление…" compact />;
  }

  if (error || !ad) {
    return (
      <section className="vk-tab-panel">
        <VkBackBar title="Объявление" onBack={goBack} />
        <VkErrorState message={error || "Объявление не найдено"} onRetry={load} />
      </section>
    );
  }

  const visual = getCategoryVisual(ad.category);

  return (
    <section className="vk-tab-panel">
      <VkBackBar title="Объявление" onBack={goBack} />

      <article className="page-panel page-panel--forest">
        <div className="flex items-start gap-3 mb-3">
          <div className="literary-classified-icon shrink-0" style={{ background: visual.gradient }}>
            {visual.icon}
          </div>
          <div>
            <span className="literary-job-badge">{ad.category_label}</span>
            <h3 className="literary-classified-title mt-1 mb-0">{ad.title}</h3>
            {ad.created_at && (
              <p className="text-xs text-muted-foreground m-0 mt-1">{formatShortDate(ad.created_at)}</p>
            )}
          </div>
        </div>

        <LiterarySectionHead kicker="📝 Описание" title="Подробности" />
        <p className="m-0 text-sm leading-relaxed">{ad.description}</p>

        <div className="vk-detail-facts mt-4">
          {ad.price != null && (
            <p className="m-0">
              <strong>Цена:</strong> {ad.price} {ad.price_unit || "₽"}
            </p>
          )}
          <p className="m-0 mt-2">
            <strong>Контакт:</strong>{" "}
            <a href={`tel:${ad.phone}`} className="literary-link">
              {ad.phone}
            </a>
          </p>
          <p className="m-0 mt-2">
            <strong>Автор:</strong> {ad.author_name}
          </p>
          {ad.address && (
            <p className="m-0 mt-2">
              <strong>Адрес:</strong> {ad.address}
            </p>
          )}
        </div>
      </article>
    </section>
  );
}
