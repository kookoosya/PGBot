import { useCallback, useEffect, useRef, useState } from "react";
import { api, type WeatherResponse } from "@/lib/api";

const FALLBACK_REFRESH_MS = 30 * 60 * 1000;

let sharedData: WeatherResponse | null = null;
let sharedPromise: Promise<WeatherResponse | null> | null = null;
let sharedListeners = new Set<(data: WeatherResponse | null, error: string | null) => void>();

async function fetchWeatherShared(): Promise<WeatherResponse | null> {
  if (sharedPromise) {
    return sharedPromise;
  }

  sharedPromise = api
    .getWeather()
    .then((response) => {
      sharedData = response;
      sharedListeners.forEach((listener) => listener(response, null));
      return response;
    })
    .catch((err: unknown) => {
      const message = err instanceof Error ? err.message : "Не удалось загрузить погоду";
      sharedListeners.forEach((listener) => listener(sharedData, message));
      return sharedData;
    })
    .finally(() => {
      sharedPromise = null;
    });

  return sharedPromise;
}

export function useWeather() {
  const [data, setData] = useState<WeatherResponse | null>(sharedData);
  const [loading, setLoading] = useState(!sharedData);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);

  const load = useCallback(async () => {
    setLoading(!sharedData);
    const response = await fetchWeatherShared();
    setData(response);
    setLoading(false);
    return response;
  }, []);

  useEffect(() => {
    const listener = (nextData: WeatherResponse | null, nextError: string | null) => {
      setData(nextData);
      setError(nextError);
      setLoading(false);
    };
    sharedListeners.add(listener);
    void fetchWeatherShared().finally(() => setLoading(false));
    return () => {
      sharedListeners.delete(listener);
    };
  }, []);

  useEffect(() => {
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
    }
    const intervalMs = (data?.cache_ttl_seconds ?? 1800) * 1000 || FALLBACK_REFRESH_MS;
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

export function formatTemperature(value: number): string {
  const rounded = Math.round(value);
  return `${rounded > 0 ? "+" : ""}${rounded}°`;
}

export function formatUpdatedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
