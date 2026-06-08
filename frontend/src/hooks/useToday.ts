import { useCallback, useEffect, useRef, useState } from "react";
import { api, type TodayResponse } from "@/lib/api";

const FALLBACK_REFRESH_MS = 5 * 60 * 1000;

let sharedData: TodayResponse | null = null;
let sharedPromise: Promise<TodayResponse | null> | null = null;
let sharedListeners = new Set<(data: TodayResponse | null, error: string | null) => void>();

async function fetchTodayShared(): Promise<TodayResponse | null> {
  if (sharedPromise) {
    return sharedPromise;
  }

  sharedPromise = api
    .getToday()
    .then((response) => {
      sharedData = response;
      sharedListeners.forEach((listener) => listener(response, null));
      return response;
    })
    .catch((err: unknown) => {
      const message = err instanceof Error ? err.message : "Не удалось загрузить сводку";
      sharedListeners.forEach((listener) => listener(sharedData, message));
      return sharedData;
    })
    .finally(() => {
      sharedPromise = null;
    });

  return sharedPromise;
}

export function useToday() {
  const [data, setData] = useState<TodayResponse | null>(sharedData);
  const [loading, setLoading] = useState(!sharedData);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);

  const load = useCallback(async () => {
    setLoading(!sharedData);
    const response = await fetchTodayShared();
    setData(response);
    setLoading(false);
    return response;
  }, []);

  useEffect(() => {
    const listener = (nextData: TodayResponse | null, nextError: string | null) => {
      setData(nextData);
      setError(nextError);
      setLoading(false);
    };
    sharedListeners.add(listener);
    void fetchTodayShared().finally(() => setLoading(false));
    return () => {
      sharedListeners.delete(listener);
    };
  }, []);

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
