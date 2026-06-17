import { useEffect, useMemo, useState } from "react";
import { useLocation, useSearchParams } from "react-router-dom";

import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { usePageMeta } from "@/hooks/usePageMeta";
import { useSiteInfo } from "@/hooks/useSiteInfo";
import { api } from "@/lib/api/index";
import type { PublicEvent } from "@/lib/api/types/events";
import { EVENT_REGION_FILTERS, parseRegionParam, type RegionFilter } from "@/lib/eventRegionFilters";
import { parseSourceParam } from "@/lib/eventSourceFilters";
import {
  absoluteGarnectShareUrl,
  garnectEventsPath,
  isGarnectFestivalFilter,
  parseFestivalParam,
} from "@/lib/festivalFilters";
import {
  groupEventsByShow,
  isRealCinemaEvent,
  mergePublicEvents,
  partitionGarnectProgram,
  sharePageUrl,
  eventSourceLabel,
} from "@/lib/eventUtils";
import { siteOrigin } from "@/lib/siteUrl";

import { EVENTS_COPY, GARNECT_COPY } from "./constants";
import { buildCategoryFilters } from "./utils";

export function useEventsPage() {
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
  const [regionFilter, setRegionFilter] = useState<RegionFilter>(() => parseRegionParam(searchParams.get("region")));
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [shareMsg, setShareMsg] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");

  const { info } = useSiteInfo();
  const garnectShareUrl = absoluteGarnectShareUrl(info?.site_url ?? siteOrigin());

  const pageTitle = garnectOnly ? GARNECT_COPY.title : sourceFilter ? eventSourceLabel(sourceFilter) : EVENTS_COPY.title;
  const pageSubtitle = garnectOnly
    ? GARNECT_COPY.lead
    : sourceFilter
      ? "События из выбранного источника афиши"
      : EVENTS_COPY.lead;
  const pageIcon = garnectOnly ? "🎭" : "📅";

  useDocumentTitle(pageTitle);
  usePageMeta(garnectOnly ? GARNECT_COPY.meta : undefined);

  useEffect(() => {
    setLoading(true);
    setLoadError(false);

    const base = { search: search || undefined, limit: "80" as const, source: sourceFilter || undefined };

    const load = garnectOnly
      ? api.getPublicEvents({ ...base, region: "pushkin_gory" }).then((r) => r.items)
      : sourceFilter
        ? api
            .getPublicEvents({
              ...base,
              region: regionFilter === "pskov" ? "pskov" : regionFilter === "pushkin_gory" ? "pushkin_gory" : undefined,
            })
            .then((r) => r.items)
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

  const categoryFilters = useMemo(() => buildCategoryFilters(events), [events]);

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
  const showCityRow =
    !garnectOnly && !sourceFilter && regionFilter !== "pskov" && (cinemaEvents.length > 0 || pskovEvents.length > 0);
  const showPskovOnlyBlock = !garnectOnly && !sourceFilter && regionFilter === "pskov" && pskovEvents.length > 0;
  const showSourceOnlyBlock = !!sourceFilter && visibleEvents.length > 0;
  const showGarnectOnlyBlock = garnectOnly && garnectProgram.length > 0;

  const shareGarnect = async () => {
    const msg = await sharePageUrl(`${GARNECT_COPY.title} — Пушкинские Горы`, garnectShareUrl);
    if (msg) {
      setShareMsg(msg);
      window.setTimeout(() => setShareMsg(""), 2500);
    }
  };

  const applySearch = () => setSearch(searchInput.trim());
  const resetSearch = () => {
    setSearch("");
    setSearchInput("");
  };

  return {
    EVENT_REGION_FILTERS,
    EVENTS_COPY,
    applySearch,
    categoryFilter,
    categoryFilters,
    cinemaEvents,
    eventsBase,
    garnectEventsPath: garnectEventsPath(isVkEvents),
    garnectOnly,
    garnectProgram,
    garnectShareUrl,
    isVkEvents,
    loadError,
    loading,
    pageIcon,
    pageSubtitle,
    pageTitle,
    pskovEvents,
    pushkinOtherEvents,
    regionFilter,
    resetSearch,
    search,
    searchInput,
    setCategoryFilter,
    setRegionFilter,
    setSearchInput,
    shareGarnect,
    shareMsg,
    showCityRow,
    showGarnectOnlyBlock,
    showPushkinBlock,
    showPskovOnlyBlock,
    showSourceOnlyBlock,
    sourceFilter,
    visibleEvents,
  };
}

export type EventsPageState = ReturnType<typeof useEventsPage>;
