import { LiterarySectionHead } from "@/components/literary";
import { PortalNavGrid } from "@/components/layout/PortalNavGrid";
import { usePushkinGarnectProgram } from "@/hooks/usePushkinGarnectProgram";
import { garnectEventsPath } from "@/lib/festivalFilters";
import { isFestivalImminent } from "@/lib/eventUtils";
import { LANDING_SECTIONS } from "@/lib/literaryCopy";

/** Компактная навигация по разделам — для главной. */
export function LandingQuickNav() {
  const copy = LANDING_SECTIONS.useful;
  const { program, loading } = usePushkinGarnectProgram();
  const garnectNav =
    !loading && program.length >= 2 && isFestivalImminent(program)
      ? [{ to: garnectEventsPath(), label: "Гарнец", icon: "🎭" }]
      : [];

  return (
    <nav className="page-panel page-panel--gold landing-block" aria-label="Разделы портала">
      <LiterarySectionHead kicker={copy.kicker} title={copy.title} compact />
      <PortalNavGrid prependItems={garnectNav} />
    </nav>
  );
}
