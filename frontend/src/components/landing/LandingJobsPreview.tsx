import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { api, type ClassifiedAd } from "@/lib/api";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import { EMPTY_STATES, LANDING_SECTIONS, LITERARY_VERSES } from "@/lib/literaryCopy";

const PREVIEW_LIMIT = 3;

export function LandingJobsPreview() {
  const [jobAds, setJobAds] = useState<ClassifiedAd[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getClassifieds({ jobs_only: "true", page_size: String(PREVIEW_LIMIT) })
      .then((r) => setJobAds(r.items))
      .catch(() => setJobAds([]))
      .finally(() => setLoading(false));
  }, []);

  const copy = LANDING_SECTIONS.jobs;

  return (
    <div className="page-panel page-panel--forest landing-block">
      <LiterarySectionHead
        kicker={copy.kicker}
        title={copy.title}
        lead={copy.lead}
        linkTo="/jobs"
        linkLabel="Все вакансии →"
      />

      {loading ? (
        <p className="landing-muted">Ищем вакансии в округе…</p>
      ) : jobAds.length === 0 ? (
        <LiteraryEmptyState {...EMPTY_STATES.jobs} compact>
          <div className="landing-inline-actions">
            <Link to="/jobs" className="literary-btn literary-btn--primary no-underline">
              Разместить вакансию
            </Link>
            <Link to="/services" className="literary-btn literary-btn--ghost no-underline">
              Услуги мастеров →
            </Link>
          </div>
        </LiteraryEmptyState>
      ) : (
        <>
          <div className="landing-jobs-grid">
            {jobAds.map((ad) => {
              const visual = getCategoryVisual(ad.category);
              return (
                <Link
                  key={ad.id}
                  to={`/classifieds/${ad.id}`}
                  className="literary-job-card no-underline text-inherit"
                >
                  <div className="literary-job-icon" style={{ background: visual.gradient }}>
                    {visual.icon}
                  </div>
                  <div>
                    <span className="literary-job-badge">{ad.category_label}</span>
                    <h3 className="literary-job-title">{ad.title}</h3>
                    <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{ad.description}</p>
                    {ad.price != null && (
                      <p className="literary-job-pay">{ad.price} {ad.price_unit || "₽"}</p>
                    )}
                  </div>
                </Link>
              );
            })}
          </div>
          <div className="landing-block-footer">
            <Link to="/services" className="literary-link text-sm">
              Мастера и помощь соседей →
            </Link>
            <p className="landing-verse">{LITERARY_VERSES.jobs}</p>
          </div>
        </>
      )}
    </div>
  );
}
