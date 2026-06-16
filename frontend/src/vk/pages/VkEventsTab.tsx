import { useEffect, useState } from "react";
import { EventCard, LiteraryEmptyState, LiteraryInlineLoader, LiterarySectionHead } from "@/components/literary";
import { api, EventRegion, PublicEvent } from "@/lib/api";
import { EMPTY_STATES } from "@/lib/literaryCopy";

const REGIONS: { id: "all" | EventRegion; label: string }[] = [
  { id: "all", label: "Все" },
  { id: "pushkin_gory", label: "Пушкинские Горы" },
  { id: "pskov", label: "Псков" },
];

export function VkEventsTab() {
  const [events, setEvents] = useState<PublicEvent[]>([]);
  const [region, setRegion] = useState<"all" | EventRegion>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .getPublicEvents({
        region: region === "all" ? undefined : region,
        limit: "30",
      })
      .then((r) => setEvents(r.items))
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, [region]);

  return (
    <section className="vk-tab-panel">
      <LiterarySectionHead kicker="📅 Афиша" title="События" lead="Концерты, кино и ярмарки в округе." />
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
      ) : events.length === 0 ? (
        <LiteraryEmptyState {...EMPTY_STATES.events} compact />
      ) : (
        <ol className="vk-event-list">
          {events.map((event) => (
            <li key={event.id}>
              <EventCard event={event} />
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
