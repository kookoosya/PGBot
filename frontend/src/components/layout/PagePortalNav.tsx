import { PortalNavGrid } from "@/components/layout/PortalNavGrid";
import { LiterarySectionHead } from "@/components/literary";

/** Компактный футер-навигатор на публичных страницах. */
export function PagePortalNav({ title = "Другие разделы" }: { title?: string }) {
  return (
    <section className="page-panel page-panel--gold mt-8" aria-label={title}>
      <LiterarySectionHead kicker="🧭 Навигация" title={title} compact />
      <PortalNavGrid />
    </section>
  );
}
