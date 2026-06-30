import { useCallback, useEffect, useMemo, useState } from "react";
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

async function loadEventsForRegion(
  regionFilter: RegionFilter,
  base: { search?: string; limit: "80"; source?: string },
  garnectOnly: boolean,
  sourceFilter: string | null,
): Promise<PublicEvent[]> {
  if (garnectOnly) {
    const r = await api.getPublicEvents({ ...base, region: "pushkin_gory" });
    return r.items;
  }
  if (sourceFilter) {
    const r = await api.getPublicEvents({
      ...base,
      region: regionFilter === "pskov" ? "pskov" : regionFilter === "pushkin_gory" ? "pushkin_gory" : undefined,
    });
    return r.items;
  }
  if (regionFilter === "pushkin_gory") {
    const r = await api.getPublicEvents({ ...base, region: "pushkin_gory" });
    return r.items;
  }
  if (regionFilter === "pskov") {
    const r = await api.getPublicEvents({ ...base, region: "pskov" });
    return r.items;
  }
  const [pushkin, pskov] = await Promise.all([
    api.getPublicEvents({ ...base, region: "pushkin_gory" }),
    api.getPublicEvents({ ...base, region: "pskov" }),
  ]);
  return mergePublicEvents(pskov.items, pushkin.items);
}

export function useEventsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { pathname } = useLocation();
  const isVkEvents = pathname.startsWith("/vk/events");
  const eventsBase = isVkEvents ? "/vk/events" : "/events";
  const festivalFilter = parseFestivalParam(searchParams.get("festival"));
  const garnectOnly = isGarnectFestivalFilter(festivalFilter);
  const sourceFilter = garnectOnly ? null : parseSourceParam(searchParams.get("source"));

  const [events, setEvents] = useState<PublicEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);
  const [regionFilter, setRegionFilterState] = useState<RegionFilter>(() =>
    parseRegionParam(searchParams.get("region")),
  );
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
  const eventsMeta = garnectOnly ? GARNECT_COPY.meta : EVENTS_COPY.meta;

  useDocumentTitle(pageTitle);
  usePageMeta(eventsMeta);

  useEffect(() => {
    setRegionFilterState(parseRegionParam(searchParams.get("region")));
  }, [searchParams]);

  useEffect(() => {
    const t = window.setTimeout(() => setSearch(searchInput.trim()), 400);
    return () => window.clearTimeout(t);
  }, [searchInput]);

  const setRegionFilter = useCallback(
    (region: RegionFilter) => {
      setRegionFilterState(region);
      const next = new URLSearchParams(searchParams);
      if (region === "all") next.delete("region");
      else next.set("region", region);
      setSearchParams(next, { replace: true });
    },
    [searchParams, setSearchParams],
  );

  const reload = useCallback(() => setReloadToken((t) => t + 1), []);

  useEffect(() => {
    setLoading(true);
    setLoadError(false);

    const base = { search: search || undefined, limit: "80" as const, source: sourceFilter || undefined };

    loadEventsForRegion(regionFilter, base, garnectOnly, sourceFilter)
      .then(setEvents)
      .catch(() => {
        setEvents([]);
        setLoadError(true);
      })
      .finally(() => setLoading(false));
  }, [garnectOnly, regionFilter, search, sourceFilter, reloadToken]);

  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === "visible") reload();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => document.removeEventListener("visibilitychange", onVisible);
  }, [reload]);

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

  const showPushkinBlock =
    !garnectOnly && !sourceFilter && pushkinEvents.length > 0 && regionFilter !== "pskov";
  const showCityRow =
    !garnectOnly &&
    !sourceFilter &&
    regionFilter === "all" &&
    (cinemaEvents.length > 0 || pskovEvents.length > 0);
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

  const resetSearch = () => {
    setSearch("");
    setSearchInput("");
  };

  return {
    EVENT_REGION_FILTERS,
    EVENTS_COPY,
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
    reload,
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
