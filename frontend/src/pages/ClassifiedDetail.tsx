import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { api, ClassifiedAd } from "@/lib/api";
import { getCategoryVisual } from "@/lib/classifiedCategories";

const JOB_CATEGORIES = new Set(["job", "construction_vacancy"]);

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
      <div className="page-section max-w-3xl text-center py-16">
        <p className="text-muted-foreground mb-4">{error}</p>
        <Link to="/classifieds" className="epic-btn epic-btn-glass inline-flex no-underline">← К доске</Link>
      </div>
    );
  }

  if (!ad) {
    return <div className="page-section text-center text-muted-foreground py-16">Загрузка…</div>;
  }

  const visual = getCategoryVisual(ad.category);
  const isJob = JOB_CATEGORIES.has(ad.category);
  const backTo = isJob ? "/classifieds?jobs=1" : "/classifieds";
  const backLabel = isJob ? "← Все вакансии" : "← К доске";

  return (
    <div className="page-section max-w-3xl">
      <PageHeader icon={visual.icon} title={ad.title} subtitle={ad.category_label}>
        <Link to={backTo} className="btn-hero-secondary text-sm no-underline">{backLabel}</Link>
        <Button type="button" variant="outline" size="sm" onClick={share}>
          Поделиться
        </Button>
      </PageHeader>

      {shareMsg && <p className="text-sm text-green-700 mb-4">{shareMsg}</p>}

      <article className="classified-ad-card">
        <div className="classified-ad-image" style={{ background: visual.gradient, minHeight: "8rem" }}>
          <span className="classified-ad-icon text-4xl">{visual.icon}</span>
          <span className="classified-ad-badge">{ad.category_label}</span>
        </div>
        <div className="classified-ad-body p-6">
          {ad.price != null && (
            <p className="text-xl font-bold text-amber-700 mb-2">
              {ad.price} {ad.price_unit || "₽"}
            </p>
          )}
          <p className="text-sm text-muted-foreground mb-4">{ad.author_name}</p>
          <p className="text-base leading-relaxed whitespace-pre-wrap">{ad.description}</p>
          <p className="text-lg mt-6">
            📞 <a href={`tel:${ad.phone.replace(/\s/g, "")}`} className="clickable-phone font-semibold">{ad.phone}</a>
          </p>
          {ad.address && <p className="text-sm mt-2">📍 {ad.address}</p>}
        </div>
      </article>
    </div>
  );
}
