import { useEffect, useRef, useState } from "react";

export function useFormDraft<T extends Record<string, unknown>>(storageKey: string, initialValue: T) {
  const [value, setValue] = useState<T>(initialValue);
  const hydrated = useRef(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) {
        const parsed = JSON.parse(raw) as T;
        setValue((prev) => ({ ...prev, ...parsed }));
      }
    } catch {
      // ignore broken draft payload
    } finally {
      hydrated.current = true;
    }
  }, [storageKey]);

  useEffect(() => {
    if (!hydrated.current) return;
    try {
      localStorage.setItem(storageKey, JSON.stringify(value));
    } catch {
      // ignore quota errors
    }
  }, [storageKey, value]);

  const clearDraft = () => {
    try {
      localStorage.removeItem(storageKey);
    } catch {
      // ignore storage errors
    }
  };

  return { value, setValue, clearDraft };
}
