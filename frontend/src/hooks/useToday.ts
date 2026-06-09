import { useCallback, useEffect, useRef, useState } from "react";
import { api, type EventRegion, type TodayResponse } from "@/lib/api";

const FALLBACK_REFRESH_MS = 5 * 60 * 1000;

type CacheEntry = {
  data: TodayResponse | null;
  promise: Promise<TodayResponse | null> | null;
};

const cacheByRegion = new Map<string, CacheEntry>();
const listenersByRegion = new Map<string, Set<(data: TodayResponse | null, error: string | null) => void>>();

function regionKey(region?: EventRegion): string {
  return region ?? "all";
}

function getCache(region?: EventRegion): CacheEntry {
  const key = regionKey(region);
  let entry = cacheByRegion.get(key);
  if (!entry) {
    entry = { data: null, promise: null };
    cacheByRegion.set(key, entry);
  }
  return entry;
}

function getListeners(region?: EventRegion): Set<(data: TodayResponse | null, error: string | null) => void> {
  const key = regionKey(region);
  let listeners = listenersByRegion.get(key);
  if (!listeners) {
    listeners = new Set();
    listenersByRegion.set(key, listeners);
  }
  return listeners;
}

async function fetchTodayShared(region?: EventRegion): Promise<TodayResponse | null> {
  const cache = getCache(region);
  if (cache.promise) {
    return cache.promise;
  }

  cache.promise = api
    .getToday(region)
    .then((response) => {
      cache.data = response;
      getListeners(region).forEach((listener) => listener(response, null));
      return response;
    })
    .catch((err: unknown) => {
      const message = err instanceof Error ? err.message : "Не удалось загрузить сводку";
      getListeners(region).forEach((listener) => listener(cache.data, message));
      return cache.data;
    })
    .finally(() => {
      cache.promise = null;
    });

  return cache.promise;
}

export function useToday(eventRegion?: EventRegion) {
  const cache = getCache(eventRegion);
  const [data, setData] = useState<TodayResponse | null>(cache.data);
  const [loading, setLoading] = useState(!cache.data);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);

  const load = useCallback(async () => {
    const currentCache = getCache(eventRegion);
    setLoading(!currentCache.data);
    const response = await fetchTodayShared(eventRegion);
    setData(response);
    setLoading(false);
    return response;
  }, [eventRegion]);

  useEffect(() => {
    const listeners = getListeners(eventRegion);
    const listener = (nextData: TodayResponse | null, nextError: string | null) => {
      setData(nextData);
      setError(nextError);
      setLoading(false);
    };
    listeners.add(listener);
    const currentCache = getCache(eventRegion);
    setData(currentCache.data);
    setLoading(!currentCache.data);
    void fetchTodayShared(eventRegion).finally(() => setLoading(false));
    return () => {
      listeners.delete(listener);
    };
  }, [eventRegion]);

  useEffect(() => {
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
    }
    const intervalMs = (data?.cache_ttl_seconds ?? 300) * 1000 || FALLBACK_REFRESH_MS;
    timerRef.current = window.setInterval(() => {
      void load();
    }, intervalMs);
    return () => {
      if (timerRef.current) {
        window.clearInterval(timerRef.current);
      }
    };
  }, [data?.cache_ttl_seconds, load]);

  return { data, loading, error, refresh: load };
}

export function formatTodayUpdatedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
