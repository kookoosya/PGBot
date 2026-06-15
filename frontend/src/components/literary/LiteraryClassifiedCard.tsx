import { Link } from "react-router-dom";
import type { ClassifiedAd } from "@/lib/api";
import { getCategoryVisual } from "@/lib/classifiedCategories";

interface LiteraryClassifiedCardProps {
  ad: ClassifiedAd;
  /** Компактный вид — меньше текста */
  compact?: boolean;
}

/** Карточка объявления в стиле «Пушкиногорский альбом» */
export function LiteraryClassifiedCard({ ad, compact = false }: LiteraryClassifiedCardProps) {
  const visual = getCategoryVisual(ad.category);

  return (
    <Link to={`/classifieds/${ad.id}`} className="literary-classified-card no-underline text-inherit">
      <div className="literary-classified-icon" style={{ background: visual.gradient }}>
        {visual.icon}
      </div>
      <div className="literary-classified-body">
        <span className="literary-job-badge">{ad.category_label}</span>
        <h3 className="literary-classified-title">{ad.title}</h3>
        {!compact && <p className="literary-classified-desc">{ad.description}</p>}
        <div className="literary-classified-meta">
          {ad.price != null && (
            <span className="literary-classified-price">
              {ad.price} {ad.price_unit || "₽"}
            </span>
          )}
          <span className="literary-classified-author">{ad.author_name}</span>
        </div>
        {!compact && (
          <p className="literary-classified-contact">
            📞 <span className="clickable-phone">{ad.phone}</span>
            {ad.address && ` · 📍 ${ad.address}`}
          </p>
        )}
      </div>
    </Link>
  );
}
