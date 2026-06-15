import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { api, ClassifiedAd } from "@/lib/api";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import { JOB_CATEGORY_IDS } from "@/lib/jobs";
import { EMPTY_STATES, LITERARY_VERSES } from "@/lib/literaryCopy";

export function ClassifiedDetail() {
  const { id } = useParams();
  const [ad, setAd] = useState<ClassifiedAd | null>(null);
  const [error, setError] = useState("");
  const [shareMsg, setShareMsg] = useState("");

  useEffect(() => {
    const num = Number(id);
    if (!num) return;
    api.getClassified(num)
      .then(setAd)
      .catch(() => setError("Объявление не найдено"));
  }, [id]);

  const share = async () => {
    const url = window.location.href;
    const text = ad ? `${ad.title} — Пушкинские Горы` : "Объявление";
    try {
      if (navigator.share) {
        await navigator.share({ title: text, url });
        return;
      }
      await navigator.clipboard.writeText(url);
      setShareMsg("Ссылка скопирована");
      window.setTimeout(() => setShareMsg(""), 2500);
    } catch {
      setShareMsg("Не удалось поделиться");
    }
  };

  if (error) {
    return (
      <div className="literary-page page-section max-w-3xl">
        <LiteraryEmptyState {...EMPTY_STATES.classifiedNotFound} text={error}>
          <Link to="/classifieds" className="literary-btn literary-btn--ghost mt-2 no-underline">← К доске</Link>
        </LiteraryEmptyState>
      </div>
    );
  }

  if (!ad) {
    return (
      <div className="literary-page page-section max-w-3xl">
        <p className="landing-muted text-center py-16">Загрузка…</p>
      </div>
    );
  }

  const visual = getCategoryVisual(ad.category);
  const isJob = JOB_CATEGORY_IDS.has(ad.category);
  const backTo = isJob ? "/jobs" : "/classifieds";
  const backLabel = isJob ? "← Все вакансии" : "← К доске";

  return (
    <div className="literary-page page-section max-w-3xl">
      <PageHeader icon={visual.icon} title={ad.title} subtitle={ad.category_label}>
        <Link to={backTo} className="literary-btn literary-btn--ghost text-sm no-underline">{backLabel}</Link>
        <button type="button" className="literary-btn literary-btn--ghost text-sm" onClick={share}>
          Поделиться
        </button>
      </PageHeader>

      {shareMsg && <p className="alert-success mb-4">{shareMsg}</p>}

      <article className="page-panel page-panel--gold literary-classified-detail">
        <div className="literary-classified-detail-hero" style={{ background: visual.gradient }}>
          <span className="literary-classified-detail-icon">{visual.icon}</span>
          <span className="literary-classified-detail-badge">{ad.category_label}</span>
        </div>

        <div className="literary-classified-detail-body">
          {ad.price != null && (
            <p className="literary-classified-price literary-classified-price--large">
              {ad.price} {ad.price_unit || "₽"}
            </p>
          )}

          <LiterarySectionHead
            kicker="🪶 От соседа"
            title={ad.author_name}
            lead={ad.address ? `📍 ${ad.address}` : undefined}
          />

          <div className="literary-classified-detail-desc">
            <p className="event-detail-text">{ad.description}</p>
          </div>

          <div className="literary-classified-detail-contact">
            <p className="event-detail-label">Связаться</p>
            <p className="event-detail-value">
              📞 <a href={`tel:${ad.phone.replace(/\s/g, "")}`} className="clickable-phone literary-link">{ad.phone}</a>
            </p>
          </div>

          <p className="landing-section-verse literary-classified-detail-verse" aria-hidden>
            {LITERARY_VERSES.classifieds}
          </p>
        </div>
      </article>
    </div>
  );
}
