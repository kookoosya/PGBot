import { Link } from "react-router-dom";
import { usePushkinGarnectProgram } from "@/hooks/usePushkinGarnectProgram";
import { garnectEventsPath } from "@/lib/festivalFilters";
import { isFestivalImminent, isFestivalPast } from "@/lib/eventUtils";

interface LandingEventsCtaProps {
  defaultLabel: string;
}

export function LandingEventsCta({ defaultLabel }: LandingEventsCtaProps) {
  const { program, loading } = usePushkinGarnectProgram();

  if (!loading && program.length >= 2 && isFestivalImminent(program)) {
    return (
      <Link to={garnectEventsPath()} className="epic-btn epic-btn-glass epic-btn-lg">
        🎭 Программа гарнеца
      </Link>
    );
  }

  if (!loading && program.length >= 2 && isFestivalPast(program)) {
    return (
      <Link to={garnectEventsPath()} className="epic-btn epic-btn-glass epic-btn-lg">
        🎭 Архив программы
      </Link>
    );
  }

  return (
    <Link to="/events" className="epic-btn epic-btn-glass epic-btn-lg">
      📅 {defaultLabel}
    </Link>
  );
}
