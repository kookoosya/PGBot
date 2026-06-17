import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { CinemaSpotlight, EventCard, FestivalProgramBlock, LiteraryEmptyState, LiteraryInlineLoader, LiterarySectionHead } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { usePageMeta } from "@/hooks/usePageMeta";
import { useSiteInfo } from "@/hooks/useSiteInfo";
import { api, PublicEvent } from "@/lib/api";
import { EVENT_REGION_FILTERS, parseRegionParam, type RegionFilter } from "@/lib/eventRegionFilters";
import { parseSourceParam } from "@/lib/eventSourceFilters";
import { absoluteGarnectShareUrl, garnectEventsPath, GARNECT_FESTIVAL_TITLE, isGarnectFestivalFilter, parseFestivalParam } from "@/lib/festivalFilters";
import { groupEventsByShow, isRealCinemaEvent, mergePublicEvents, partitionGarnectProgram, sharePageUrl, eventSourceLabel } from "@/lib/eventUtils";
import { EMPTY_STATES, PAGE_SECTIONS } from "@/lib/literaryCopy";
import { siteOrigin } from "@/lib/siteUrl";

const copy = PAGE_SECTIONS.events;
const garnectCopy = {
  title: GARNECT_FESTIVAL_TITLE,
  lead: "Программа фестиваля в Пушкинских Горах",
  meta: "Программа всероссийского театрального фестиваля Бугровский гарнец в Пушкинских Горах — спектакли и расписание.",
};

export function EventsPage() {
  const [searchParams] = useSearchParams();
  const { pathname } = useLocation();
  const isVkEvents = pathname.startsWith("/vk/events");
  const eventsBase = isVkEvents ? "/vk/events" : "/events";
  const festivalFilter = parseFestivalParam(searchParams.get("festival"));
  const garnectOnly = isGarnectFestivalFilter(festivalFilter);
  const sourceFilter = garnectOnly ? null : parseSourceParam(searchParams.get("source"));
  const [events, setEvents] = useState<PublicEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  // По умолчанию — посёлок, но кино и Псков всё равно подтягиваем в верхний блок.
  const [regionFilter, setRegionFilter] = useState<RegionFilter>(() => parseRegionParam(searchParams.get("region")));
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [shareMsg, setShareMsg] = useState("");
  const { info } = useSiteInfo();
  const garnectShareUrl = absoluteGarnectShareUrl(info?.site_url ?? siteOrigin());

  useDocumentTitle(garnectOnly ? garnectCopy.title : copy.title);
  usePageMeta(garnectOnly ? garnectCopy.meta : undefined);

  useEffect(() => {
    setLoading(true);
    setLoadError(false);

    const base = { search: search || undefined, limit: "80" as const, source: sourceFilter || undefined };

    const load =
      garnectOnly
        ? api.getPublicEvents({ ...base, region: "pushkin_gory" }).then((r) => r.items)
        : sourceFilter
          ? api.getPublicEvents({ ...base, region: regionFilter === "pskov" ? "pskov" : regionFilter === "pushkin_gory" ? "pushkin_gory" : undefined }).then((r) => r.items)
          : regionFilter === "pskov"
            ? api.getPublicEvents({ ...base, region: "pskov" }).then((r) => r.items)
            : Promise.all([
                api.getPublicEvents({ ...base, region: "pushkin_gory" }),
                api.getPublicEvents({ ...base, region: "pskov" }),
              ]).then(([pushkin, pskov]) => mergePublicEvents(pskov.items, pushkin.items));

    load
      .then(setEvents)
      .catch(() => {
        setEvents([]);
        setLoadError(true);
      })
      .finally(() => setLoading(false));
  }, [garnectOnly, regionFilter, search, sourceFilter]);

  const categoryFilters = useMemo(() => {
    const pushkinCats = new Set(
      events
        .filter((e) => e.region_label === "Пушкинские Горы")
        .map((e) => e.category_label)
        .filter(Boolean),
    );
    const allCats = new Set(events.map((e) => e.category_label).filter(Boolean));

    // "Все категории" — начинаем с тех, что встречаются в Пушкинских Горах.
    const pushkinOrdered = Array.from(pushkinCats).sort();
    const remaining = Array.from(allCats)
      .filter((c) => !pushkinCats.has(c))
      .sort();
    return [...pushkinOrdered, ...remaining];
  }, [events]);

  const [categoryFilter, setCategoryFilter] = useState("");

  useEffect(() => {
    if (categoryFilter && !categoryFilters.includes(categoryFilter)) {
      setCategoryFilter("");
    }
  }, [categoryFilter, categoryFilters]);

  const visibleEvents = useMemo(() => {
    if (!categoryFilter) return events;
    return events.filter((e) => e.category_label === categoryFilter);
  }, [events, categoryFilter]);

  const cinemaEvents = useMemo(
    () => groupEventsByShow(visibleEvents.filter(isRealCinemaEvent)),
    [visibleEvents],
  );
  const pushkinEvents = useMemo(
    () => visibleEvents.filter((e) => e.region_label === "Пушкинские Горы" && !isRealCinemaEvent(e)),
    [visibleEvents],
  );
  const { program: garnectProgram, rest: pushkinOtherEvents } = useMemo(
    () => partitionGarnectProgram(pushkinEvents),
    [pushkinEvents],
  );
  const pskovEvents = useMemo(
    () => visibleEvents.filter((e) => e.region_label === "Псков" && !isRealCinemaEvent(e)),
    [visibleEvents],
  );
  const showPushkinBlock = !garnectOnly && !sourceFilter && pushkinEvents.length > 0 && regionFilter !== "pskov";
  const showCityRow = !garnectOnly && !sourceFilter && regionFilter !== "pskov" && (cinemaEvents.length > 0 || pskovEvents.length > 0);
  const showPskovOnlyBlock = !garnectOnly && !sourceFilter && regionFilter === "pskov" && pskovEvents.length > 0;
  const showSourceOnlyBlock = !!sourceFilter && visibleEvents.length > 0;
  const showGarnectOnlyBlock = garnectOnly && garnectProgram.length > 0;

  const shareGarnect = async () => {
    const msg = await sharePageUrl(`${GARNECT_FESTIVAL_TITLE} — Пушкинские Горы`, garnectShareUrl);
    if (msg) {
      setShareMsg(msg);
      window.setTimeout(() => setShareMsg(""), 2500);
    }
  };

  const cinemaBlock = (
    <CinemaSpotlight linkTo="/events" linkLabel="Все сеансы →" empty={cinemaEvents.length === 0}>
      {cinemaEvents.length > 0 ? (
        <ol className="events-grid events-grid--cinema">
          {cinemaEvents.map((event) => (
            <EventCard key={event.id} event={event} spotlight />
          ))}
        </ol>
      ) : (
        <LiteraryEmptyState {...EMPTY_STATES.cinema} compact tone="dark" />
      )}
    </CinemaSpotlight>
  );

  const pskovBlock = (
    <section className="page-panel page-panel--gold events-city-pskov">
      <LiterarySectionHead
        kicker={copy.pskov.kicker}
        title={copy.pskov.title}
        compact
      />
      <ol className="events-grid">
        {pskovEvents.map((event) => (
          <EventCard key={event.id} event={event} />
        ))}
      </ol>
    </section>
  );

  return (
    <div className="literary-page page-section max-w-6xl events-page">
      <PageHeader
        icon={garnectOnly ? "🎭" : "📅"}
        title={garnectOnly ? garnectCopy.title : sourceFilter ? eventSourceLabel(sourceFilter) : copy.title}
        subtitle={garnectOnly ? garnectCopy.lead : sourceFilter ? "События из выбранного источника афиши" : copy.lead}
      >
        {garnectOnly && (
          <button type="button" className="literary-btn literary-btn--ghost text-sm" onClick={shareGarnect}>
            Поделиться
          </button>
        )}
      </PageHeader>

      {shareMsg && <p className="alert-success mb-4">{shareMsg}</p>}

      <section className="page-panel page-panel--gold mb-6">
        <LiterarySectionHead
          kicker="🔍 Поиск"
          title={garnectOnly ? "Найти в программе" : "Найти в афише"}
          compact
        />
        <div className="flex flex-col sm:flex-row gap-2 mb-4">
          <Input
            placeholder="Поиск: концерт, кино, ярмарка…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && setSearch(searchInput.trim())}
            className="flex-1 pushkin-select"
          />
          <button type="button" className="literary-btn literary-btn--primary shrink-0" onClick={() => setSearch(searchInput.trim())}>
            Найти
          </button>
          {search && (
            <button
              type="button"
              className="literary-btn literary-btn--ghost shrink-0 text-sm"
              onClick={() => { setSearch(""); setSearchInput(""); }}
            >
              Сбросить
            </button>
          )}
        </div>

        {garnectOnly ? (
          <div className="literary-filter-bar mt-4">
            <Link to={eventsBase} className="filter-chip filter-chip-active no-underline">
              Бугровский гарнец ×
            </Link>
          </div>
        ) : (
          <div className="events-region-filters mb-0" role="group" aria-label="Регион">
            {EVENT_REGION_FILTERS.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`events-region-filter${regionFilter === item.id ? " events-region-filter--active" : ""}`}
                onClick={() => setRegionFilter(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>
        )}

        {sourceFilter && (
          <div className="literary-filter-bar mt-4">
            <Link to={eventsBase} className="filter-chip filter-chip-active no-underline">
              {eventSourceLabel(sourceFilter)} ×
            </Link>
          </div>
        )}

        {!garnectOnly && !sourceFilter && categoryFilters.length > 1 && (
          <div className="literary-filter-bar mt-4">
            <button
              type="button"
              className={`filter-chip${!categoryFilter ? " filter-chip-active" : ""}`}
              onClick={() => setCategoryFilter("")}
            >
              Все категории
            </button>
            {categoryFilters.map((cat) => (
              <button
                key={cat}
                type="button"
                className={`filter-chip${categoryFilter === cat ? " filter-chip-active" : ""}`}
                onClick={() => setCategoryFilter(cat)}
              >
                {cat}
              </button>
            ))}
          </div>
        )}
      </section>

      {loading ? (
        <LiteraryInlineLoader label="Собираем афишу Пушкиногорья…" />
      ) : loadError ? (
        <LiteraryEmptyState
          icon="⚠️"
          title="Афиша временно недоступна"
          text="Не удалось загрузить события. Попробуйте обновить страницу через минуту."
        />
      ) : garnectOnly && garnectProgram.length === 0 ? (
        <LiteraryEmptyState
          {...(search
            ? EMPTY_STATES.eventsSearch
            : {
                icon: "🎭",
                title: "Программа пока не опубликована",
                text: "Следите за обновлениями афиши — спектакли фестиваля появятся здесь, как только источник их опубликует.",
              })}
        />
      ) : visibleEvents.length === 0 ? (
        <LiteraryEmptyState {...(search ? EMPTY_STATES.eventsSearch : EMPTY_STATES.events)} />
      ) : (
        <div className="literary-dashboard">
          {showCityRow && (
            <div className="events-city-row">
              {cinemaBlock}
              {pskovEvents.length > 0 && pskovBlock}
            </div>
          )}

          {regionFilter === "pskov" && !garnectOnly && cinemaBlock}

          {showPskovOnlyBlock && pskovBlock}

          {showSourceOnlyBlock && (
            <section className="page-panel page-panel--forest">
              <ol className="events-grid events-grid--wide">
                {visibleEvents.map((event) => (
                  <EventCard key={event.id} event={event} />
                ))}
              </ol>
            </section>
          )}

          {showGarnectOnlyBlock && (
            <section className="page-panel page-panel--forest">
              <div className="events-festival-program-wrap">
                <FestivalProgramBlock
                  events={garnectProgram}
                  shareUrl={garnectShareUrl}
                  eventQuerySuffix="?from=garnect"
                />
              </div>
            </section>
          )}

          {showPushkinBlock && (
            <section className="page-panel page-panel--forest">
              <LiterarySectionHead
                kicker={copy.pushkin.kicker}
                title={copy.pushkin.title}
                compact
              />
              <ol className="events-grid events-grid--wide">
                {garnectProgram.length > 0 && (
                  <li className="events-festival-program-wrap">
                    <FestivalProgramBlock
                      events={garnectProgram}
                      linkTo={garnectEventsPath(isVkEvents)}
                      shareUrl={garnectShareUrl}
                      eventQuerySuffix="?from=garnect"
                    />
                  </li>
                )}
                {pushkinOtherEvents.map((event) => (
                  <EventCard key={event.id} event={event} />
                ))}
              </ol>
            </section>
          )}
        </div>
      )}

    </div>
  );
}
