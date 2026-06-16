import { useCallback, useEffect, useRef, useState } from "react";
import { parseApiError } from "@/vk/lib/errors";

const DEFAULT_RETRIES = 2;
const RETRY_BASE_MS = 800;

interface UseAsyncDataOptions {
  enabled?: boolean;
  retries?: number;
}

export function useAsyncData<T>(
  loader: () => Promise<T>,
  deps: unknown[],
  options: UseAsyncDataOptions = {},
) {
  const { enabled = true, retries = DEFAULT_RETRIES } = options;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState("");
  const attemptRef = useRef(0);

  const reload = useCallback(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    attemptRef.current = 0;

    const run = async () => {
      try {
        const result = await loader();
        setData(result);
        setError("");
      } catch (err) {
        if (attemptRef.current < retries) {
          attemptRef.current += 1;
          const delay = RETRY_BASE_MS * attemptRef.current;
          await new Promise((resolve) => setTimeout(resolve, delay));
          return run();
        }
        setData(null);
        setError(parseApiError(err));
      } finally {
        setLoading(false);
      }
    };

    void run();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- deps passed explicitly
  }, [enabled, loader, retries, ...deps]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { data, loading, error, reload, setData };
}
