import { useCallback, useEffect, useState } from "react";
import { EventCard, LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { api, EventRegion, PublicEvent } from "@/lib/api";
import { EMPTY_STATES } from "@/lib/literaryCopy";
import { VkErrorState } from "@/vk/components/VkErrorState";
import { VkSkeletonList } from "@/vk/components/VkSkeleton";
import { useAsyncData } from "@/vk/hooks/useAsyncData";
import { useVkNavigation } from "@/vk/VkNavigationContext";

const REGIONS: { id: "all" | EventRegion; label: string }[] = [
  { id: "all", label: "Все" },
  { id: "pushkin_gory", label: "Пушкинские Горы" },
  { id: "pskov", label: "Псков" },
];

const CATEGORIES = [
  { id: "", label: "Все жанры" },
  { id: "concert", label: "Концерты" },
  { id: "cinema", label: "Кино" },
  { id: "fair", label: "Ярмарки" },
  { id: "exhibition", label: "Выставки" },
  { id: "other", label: "Другое" },
];

export function VkEventsTab() {
  const { openEvent } = useVkNavigation();
  const [region, setRegion] = useState<"all" | EventRegion>("all");
  const [category, setCategory] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");

  const loader = useCallback(async () => {
    const r = await api.getPublicEvents({
      region: region === "all" ? undefined : region,
      search: search || undefined,
      limit: "40",
    });
    let items = r.items;
    if (category) {
      items = items.filter((e) => e.category === category);
    }
    return items;
  }, [region, search, category]);

  const { data: events, loading, error, reload } = useAsyncData<PublicEvent[]>(loader, [region, search, category]);

  useEffect(() => {
    const timer = window.setTimeout(() => setSearch(searchInput.trim()), 400);
    return () => window.clearTimeout(timer);
  }, [searchInput]);

  return (
    <section className="vk-tab-panel">
      <LiterarySectionHead kicker="📅 Афиша" title="События" lead="Концерты, кино и ярмарки в округе." />

      <div className="vk-search-row">
        <Input
          placeholder="Поиск: концерт, кино…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="pushkin-select flex-1"
        />
        {searchInput && (
          <button
            type="button"
            className="literary-btn literary-btn--ghost shrink-0 text-sm"
            onClick={() => {
              setSearch("");
              setSearchInput("");
            }}
          >
            Сбросить
          </button>
        )}
      </div>

      <div className="vk-filter-row">
        {REGIONS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`vk-filter-chip${region === item.id ? " vk-filter-chip--active" : ""}`}
            onClick={() => setRegion(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div className="vk-filter-row">
        {CATEGORIES.map((item) => (
          <button
            key={item.id || "all"}
            type="button"
            className={`vk-filter-chip vk-filter-chip--sm${category === item.id ? " vk-filter-chip--active" : ""}`}
            onClick={() => setCategory(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {loading ? (
        <VkSkeletonList count={4} />
      ) : error ? (
        <VkErrorState message={error} onRetry={reload} />
      ) : !events?.length ? (
        <LiteraryEmptyState {...(search ? EMPTY_STATES.eventsSearch : EMPTY_STATES.events)} compact />
      ) : (
        <ol className="vk-event-list">
          {events.map((event) => (
            <EventCard key={event.id} event={event} onOpen={() => openEvent(event.id)} />
          ))}
        </ol>
      )}
    </section>
  );
}
