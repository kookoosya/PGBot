import { Link } from "react-router-dom";
import { usePushkinGarnectProgram } from "@/hooks/usePushkinGarnectProgram";
import { formatFestivalDateRange, isFestivalImminent, pluralPerformances } from "@/lib/eventUtils";

export function FestivalHeroBanner() {
  const { program, loading } = usePushkinGarnectProgram();

  if (loading || program.length < 2 || !isFestivalImminent(program, 3)) {
    return null;
  }

  const dateRange = formatFestivalDateRange(program);

  return (
    <div className="festival-hero-banner" role="status">
      <p className="festival-hero-banner__text">
        <span className="festival-hero-banner__kicker">🎭 На этих выходных</span>
        <strong className="festival-hero-banner__title">Бугровский гарнец</strong>
        <span className="festival-hero-banner__meta">
          {dateRange} · {program.length} {pluralPerformances(program.length)}
        </span>
      </p>
      <Link to="/events" className="festival-hero-banner__cta">
        Программа →
      </Link>
    </div>
  );
}
