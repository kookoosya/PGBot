import { useCallback, useEffect, useState } from "react";
import { EventCard, LiteraryEmptyState, LiteraryInlineLoader, LiterarySectionHead } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { api, EventRegion, PublicEvent } from "@/lib/api";
import { EMPTY_STATES } from "@/lib/literaryCopy";
import { VkErrorState } from "@/vk/components/VkErrorState";
import { useVkNavigation } from "@/vk/VkNavigationContext";
import { parseApiError } from "@/vk/lib/errors";

const REGIONS: { id: "all" | EventRegion; label: string }[] = [
  { id: "all", label: "Все" },
  { id: "pushkin_gory", label: "Пушкинские Горы" },
  { id: "pskov", label: "Псков" },
];

export function VkEventsTab() {
  const { openEvent } = useVkNavigation();
  const [events, setEvents] = useState<PublicEvent[]>([]);
  const [region, setRegion] = useState<"all" | EventRegion>("all");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    api
      .getPublicEvents({
        region: region === "all" ? undefined : region,
        search: search || undefined,
        limit: "40",
      })
      .then((r) => setEvents(r.items))
      .catch((err) => {
        setEvents([]);
        setError(parseApiError(err));
      })
      .finally(() => setLoading(false));
  }, [region, search]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <section className="vk-tab-panel">
      <LiterarySectionHead kicker="📅 Афиша" title="События" lead="Концерты, кино и ярмарки в округе." />

      <div className="vk-search-row">
        <Input
          placeholder="Поиск: концерт, кино…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && setSearch(searchInput.trim())}
          className="pushkin-select flex-1"
        />
        <button type="button" className="literary-btn literary-btn--ghost shrink-0" onClick={() => setSearch(searchInput.trim())}>
          Найти
        </button>
        {(search || searchInput) && (
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

      {loading ? (
        <LiteraryInlineLoader label="Собираем афишу…" compact />
      ) : error ? (
        <VkErrorState message={error} onRetry={load} />
      ) : events.length === 0 ? (
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
