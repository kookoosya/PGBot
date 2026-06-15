import { Link } from "react-router-dom";
import { getSeasonalTip } from "@/lib/seasonalTip";

export function SeasonalTip() {
  const tip = getSeasonalTip();
  if (!tip) return null;

  return (
    <aside className="seasonal-tip seasonal-tip--literary seasonal-tip--landing" aria-label="Сезонная подсказка">
      <span className="seasonal-tip-icon" aria-hidden>{tip.icon}</span>
      <div className="seasonal-tip-body">
        <p className="seasonal-tip-title">{tip.title}</p>
        <p className="seasonal-tip-text">{tip.text}</p>
        {tip.link && tip.linkLabel && (
          <Link to={tip.link} className="literary-link text-sm">{tip.linkLabel} →</Link>
        )}
      </div>
    </aside>
  );
}
