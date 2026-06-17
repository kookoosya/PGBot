import { Link } from "react-router-dom";
import type { ClassifiedAd } from "@/lib/api/types/classifieds";
import { getCategoryVisual } from "@/lib/classifiedCategories";

/** Карточка вакансии в стиле «Пушкиногорский альбом». */
export function LiteraryJobCard({ ad }: { ad: ClassifiedAd }) {
  const visual = getCategoryVisual(ad.category);

  return (
    <Link to={`/classifieds/${ad.id}`} className="literary-job-card no-underline text-inherit">
      <div className="literary-job-icon" style={{ background: visual.gradient }}>
        {visual.icon}
      </div>
      <div className="literary-job-body">
        <span className="literary-card-kicker">{ad.category_label}</span>
        <h3 className="literary-job-title">{ad.title}</h3>
        <p className="literary-job-desc">{ad.description}</p>
        {ad.price != null && (
          <p className="literary-job-pay">{ad.price} {ad.price_unit || "₽"}</p>
        )}
        <p className="literary-job-contact">
          📞 <span className="clickable-phone">{ad.phone}</span>
          {ad.address && ` · 📍 ${ad.address}`}
        </p>
      </div>
    </Link>
  );
}
