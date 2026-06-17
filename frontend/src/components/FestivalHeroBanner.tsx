import { Link } from "react-router-dom";
import { usePushkinGarnectProgram } from "@/hooks/usePushkinGarnectProgram";
import { formatFestivalDateRange, festivalPromoKicker, isFestivalImminent, isFestivalPast, pluralPerformances } from "@/lib/eventUtils";
import { garnectEventsPath } from "@/lib/festivalFilters";

export function FestivalHeroBanner() {
  const { program, loading } = usePushkinGarnectProgram();

  if (loading || program.length < 2) {
    return null;
  }

  const dateRange = formatFestivalDateRange(program);
  const imminent = isFestivalImminent(program, 3);
  const past = isFestivalPast(program, 3);

  if (!imminent && !past) {
    return null;
  }

  const kicker = festivalPromoKicker(program, 3);
  const ctaLabel = past ? "Архив программы →" : "Программа →";

  return (
    <div className={`festival-hero-banner${past ? " festival-hero-banner--past" : ""}`} role="status">
      <p className="festival-hero-banner__text">
        <span className="festival-hero-banner__kicker">{kicker}</span>
        <strong className="festival-hero-banner__title">Бугровский гарнец</strong>
        <span className="festival-hero-banner__meta">
          {dateRange} · {program.length} {pluralPerformances(program.length)}
        </span>
      </p>
      <Link to={garnectEventsPath()} className="festival-hero-banner__cta">
        {ctaLabel}
      </Link>
    </div>
  );
}
