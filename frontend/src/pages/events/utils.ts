import type { PublicEvent } from "@/lib/api/types/events";

/** Category chips: Pushkin Hills categories first, then the rest alphabetically. */
export function buildCategoryFilters(events: PublicEvent[]): string[] {
  const pushkinCats = new Set(
    events
      .filter((e) => e.region_label === "Пушкинские Горы")
      .map((e) => e.category_label)
      .filter(Boolean),
  );
  const allCats = new Set(events.map((e) => e.category_label).filter(Boolean));
  const pushkinOrdered = Array.from(pushkinCats).sort();
  const remaining = Array.from(allCats)
    .filter((c) => !pushkinCats.has(c))
    .sort();
  return [...pushkinOrdered, ...remaining];
}
