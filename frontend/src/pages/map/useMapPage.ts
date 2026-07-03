import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  cachePlacesForOffline,
  downloadOfflineMapPack,
  getOfflinePlaces,
  isOfflineMapReady,
  offlineBundleAge,
  registerServiceWorker,
} from "@/lib/offlineMap";
import { api } from "@/lib/api/index";
import type { ComplaintType } from "@/lib/api/types/issues";
import type { MapFilterMode, MapRoute, MapStats, Place, PlaceDetail, TaxiService } from "@/lib/api/types/places";

import {
  boundsToQueryParams,
  createPlacesRequestController,
  isPlacesAbortError,
} from "./mapPlacesRequest";
import {
  buildPlacesFilterKey,
  deriveVisiblePlaces,
  isIncompatibleFilterLoading,
  isSnapshotFilterCompatible,
  type PlacesResultSnapshot,
} from "./mapResultSnapshot";

export function useMapPage() {
  const [snapshot, setSnapshot] = useState<PlacesResultSnapshot | null>(null);
  const [selected, setSelected] = useState<PlaceDetail | null>(null);
  const [highlight, setHighlight] = useState<Place | null>(null);
  const [taxi, setTaxi] = useState<TaxiService[]>([]);
  const [category, setCategory] = useState("");
  const [shopsOnly, setShopsOnly] = useState(false);
  const [usefulOnly, setUsefulOnly] = useState(false);
  const [routes, setRoutes] = useState<MapRoute[]>([]);
  const [activeRoute, setActiveRoute] = useState<MapRoute | null>(null);
  const [mapReportTypes, setMapReportTypes] = useState<ComplaintType[]>([]);
  const [search, setSearch] = useState("");
  const [searchDebounced, setSearchDebounced] = useState("");
  const [mapStyle, setMapStyle] = useState<"scheme" | "satellite">("scheme");
  const [mapModes, setMapModes] = useState<MapFilterMode[]>([]);
  const [complaintTypes, setComplaintTypes] = useState<ComplaintType[]>([]);
  const [tab, setTab] = useState<"info" | "review" | "complaint" | "report">("info");
  const [reviewForm, setReviewForm] = useState({ rating: 5, text: "", author_name: "" });
  const [complaintForm, setComplaintForm] = useState({
    complaint_type: "price_tag_fraud", description: "", price_tagged: "", price_charged: "", author_name: "",
  });
  const [reportForm, setReportForm] = useState({
    complaint_type: "map_wrong_hours", description: "", author_name: "",
  });
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");
  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);
  const [offlineReady, setOfflineReady] = useState(isOfflineMapReady());
  const [offlineBusy, setOfflineBusy] = useState(false);
  const [offlineMsg, setOfflineMsg] = useState("");
  const [mapStats, setMapStats] = useState<MapStats | null>(null);
  const [placesLoading, setPlacesLoading] = useState(true);
  const [placesError, setPlacesError] = useState(false);
  const [mobileTab, setMobileTab] = useState<"map" | "list">("map");
  const boundsRef = useRef<{ south: number; west: number; north: number; east: number } | null>(null);
  const boundsPausedRef = useRef(false);
  const placesRequestRef = useRef(createPlacesRequestController());

  useEffect(() => {
    registerServiceWorker();
    api.getComplaintTypes().then(setComplaintTypes).catch(console.error);
    api.getMapReportTypes().then(setMapReportTypes).catch(console.error);
    api.getPlaceCategories().then(setCategories).catch(console.error);
    api.getTaxiServices().then(setTaxi).catch(console.error);
    api.getMapFilterModes().then(setMapModes).catch(console.error);
    api.getMapRoutes().then(setRoutes).catch(console.error);
  }, []);

  const refreshMapStats = useCallback(() => {
    api.getMapStats().then(setMapStats).catch(console.error);
  }, []);

  useEffect(() => {
    refreshMapStats();
    const interval = window.setInterval(refreshMapStats, 5 * 60_000);
    const onVisible = () => {
      if (document.visibilityState === "visible") refreshMapStats();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [refreshMapStats]);

  useEffect(() => {
    const t = window.setTimeout(() => setSearchDebounced(search.trim()), 400);
    return () => window.clearTimeout(t);
  }, [search]);

  const isLodging = category === "hotel";

  const currentFilterKey = buildPlacesFilterKey({
    category,
    shopsOnly,
    usefulOnly,
    search: searchDebounced,
    isLodging,
  });

  const activeFilterId = shopsOnly
    ? "shops"
    : usefulOnly
      ? "useful"
      : mapModes.find((f) => f.category === category)?.id ?? "";

  const applyQuickFilter = (filter: MapFilterMode) => {
    const isActive = activeFilterId === filter.id;
    if (isActive) {
      setCategory("");
      setShopsOnly(false);
      setUsefulOnly(false);
      return;
    }
    setCategory(filter.category ?? "");
    setShopsOnly(Boolean(filter.shops_only));
    setUsefulOnly(Boolean(filter.useful_only));
  };

  const applyCategoryFilter = (cat: string) => {
    setCategory(cat);
    setShopsOnly(false);
    setUsefulOnly(false);
    setMobileTab("list");
  };

  const showRoute = (route: MapRoute) => {
    setActiveRoute(route);
    setSelected(null);
    setHighlight(null);
    setMobileTab("map");
  };

  const loadPlaces = useCallback((bounds?: { south: number; west: number; north: number; east: number }) => {
    if (boundsPausedRef.current) return;
    if (bounds) boundsRef.current = bounds;
    const exactBounds = bounds || boundsRef.current;
    if (!exactBounds && !isLodging) return;

    const filterKey = buildPlacesFilterKey({
      category,
      shopsOnly,
      usefulOnly,
      search: searchDebounced,
      isLodging,
    });

    const params: Record<string, string> = { page_size: "500", sort: "rating" };
    if (category) params.category = category;
    if (shopsOnly) params.shops_only = "true";
    if (usefulOnly) params.useful_only = "true";
    if (searchDebounced) params.search = searchDebounced;
    if (isLodging) {
      params.district = "true";
    } else if (exactBounds) {
      Object.assign(params, boundsToQueryParams(exactBounds));
    }

    const { requestId, signal } = placesRequestRef.current.start();
    setPlacesLoading(true);
    setPlacesError(false);
    api
      .getPlaces(params, { signal })
      .then((r) => {
        if (!placesRequestRef.current.isLatest(requestId)) return;
        setSnapshot({
          requestId,
          filterKey,
          exactBounds: isLodging ? null : exactBounds ? { ...exactBounds } : null,
          items: r.items,
        });
        cachePlacesForOffline(r.items);
        setPlacesLoading(false);
      })
      .catch((err) => {
        if (!placesRequestRef.current.isLatest(requestId)) return;
        if (isPlacesAbortError(err)) return;
        const cached = getOfflinePlaces();
        if (cached.length) {
          const filtered = category
            ? cached.filter((p) => p.category === category)
            : cached;
          setSnapshot({
            requestId,
            filterKey,
            exactBounds: isLodging ? null : exactBounds ? { ...exactBounds } : null,
            items: filtered,
          });
          setOfflineMsg("Нет сети — показаны сохранённые точки.");
          setPlacesLoading(false);
        } else {
          setSnapshot(null);
          setPlacesError(true);
          setPlacesLoading(false);
        }
      });
  }, [category, shopsOnly, usefulOnly, searchDebounced, isLodging]);

  const handleOfflineDownload = async () => {
    setOfflineBusy(true);
    setOfflineMsg("");
    try {
      const all = await api.getPlaces({ district: "true", page_size: "500", sort: "rating" });
      const n = await downloadOfflineMapPack(all.items);
      setOfflineReady(true);
      const age = offlineBundleAge();
      setOfflineMsg(`Офлайн готов: ${all.items.length} точек, ${n} тайлов карты${age ? ` · ${new Date(age).toLocaleString("ru")}` : ""}.`);
    } catch {
      setOfflineMsg("Не удалось скачать. Проверьте интернет.");
    } finally {
      setOfflineBusy(false);
    }
  };

  useEffect(() => {
    if (boundsRef.current || isLodging) loadPlaces(boundsRef.current ?? undefined);
  }, [category, shopsOnly, usefulOnly, searchDebounced, loadPlaces, isLodging]);

  const incompatibleFilterLoading = isIncompatibleFilterLoading(
    placesLoading,
    snapshot,
    currentFilterKey,
  );

  const snapshotCompatible = isSnapshotFilterCompatible(snapshot, currentFilterKey);

  const loadedPlaces = snapshotCompatible && snapshot ? snapshot.items : [];

  const visiblePlaces = useMemo(() => {
    if (incompatibleFilterLoading) return [];
    return deriveVisiblePlaces(snapshot, currentFilterKey, placesLoading, boundsRef.current);
  }, [snapshot, currentFilterKey, placesLoading, incompatibleFilterLoading]);

  const clusterPlaces = useMemo(() => {
    if (incompatibleFilterLoading) return [];
    return loadedPlaces;
  }, [incompatibleFilterLoading, loadedPlaces]);

  const sortedPlaces = useMemo(
    () => [...visiblePlaces].sort((a, b) =>
      b.display_rating - a.display_rating
      || b.display_review_count - a.display_review_count
      || a.name.localeCompare(b.name, "ru"),
    ),
    [visiblePlaces],
  );

  const visibleCount = incompatibleFilterLoading ? null : visiblePlaces.length;

  const openPlace = async (id: number) => {
    boundsPausedRef.current = true;
    try {
      const detail = await api.getPlace(id);
      setSelected(detail);
      setHighlight(detail);
      setTab("info");
      setMsg("");
      setMsgType("ok");
    } catch {
      setMsg("Не удалось загрузить организацию. Попробуйте ещё раз.");
      setMsgType("err");
    } finally {
      window.setTimeout(() => {
        boundsPausedRef.current = false;
      }, 800);
    }
  };

  const submitReview = async () => {
    if (!selected) return;
    try {
      await api.addReview(selected.id, reviewForm);
      setMsg("Отзыв добавлен!");
      setMsgType("ok");
      openPlace(selected.id);
      loadPlaces();
      setTab("info");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Не удалось отправить отзыв");
      setMsgType("err");
    }
  };

  const submitComplaint = async () => {
    if (!selected || complaintForm.description.length < 10) return;
    try {
      await api.addComplaint(selected.id, complaintForm);
      setMsg("Претензия принята!");
      setMsgType("ok");
      openPlace(selected.id);
      setTab("info");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Не удалось отправить претензию");
      setMsgType("err");
    }
  };

  const submitReport = async () => {
    if (!selected || reportForm.description.length < 10) return;
    try {
      await api.addComplaint(selected.id, reportForm);
      setMsg("Спасибо! Проверим и обновим карту.");
      setMsgType("ok");
      setReportForm({ complaint_type: "map_wrong_hours", description: "", author_name: "" });
      setTab("info");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Не удалось отправить сообщение");
      setMsgType("err");
    }
  };

  const clearSelection = () => {
    setSelected(null);
    setHighlight(null);
  };

  return {
    places: sortedPlaces,
    clusterPlaces,
    selected,
    highlight,
    taxi,
    category,
    setCategory,
    shopsOnly,
    setShopsOnly,
    usefulOnly,
    setUsefulOnly,
    routes,
    activeRoute,
    setActiveRoute,
    mapReportTypes,
    search,
    setSearch,
    searchDebounced,
    mapStyle,
    setMapStyle,
    mapModes,
    complaintTypes,
    tab,
    setTab,
    reviewForm,
    setReviewForm,
    complaintForm,
    setComplaintForm,
    reportForm,
    setReportForm,
    msg,
    msgType,
    categories,
    offlineReady,
    offlineBusy,
    offlineMsg,
    mapStats,
    placesLoading,
    placesError,
    incompatibleFilterLoading,
    visibleCount,
    currentAreaCount: visibleCount,
    mobileTab,
    setMobileTab,
    boundsRef,
    boundsPausedRef,
    activeFilterId,
    applyQuickFilter,
    applyCategoryFilter,
    showRoute,
    loadPlaces,
    handleOfflineDownload,
    openPlace,
    submitReview,
    submitComplaint,
    submitReport,
    clearSelection,
    snapshot,
    currentFilterKey,
  };
}

export type MapPageState = ReturnType<typeof useMapPage>;
