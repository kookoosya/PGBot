import { useEffect, useRef, useState } from "react";
import { clearFormDraft, mergeFormDraft, readFormDraft, writeFormDraft } from "@/lib/formDraftStorage";

export function useFormDraft<T extends Record<string, unknown>>(storageKey: string, initialValue: T) {
  const [value, setValue] = useState<T>(initialValue);
  const hydrated = useRef(false);

  useEffect(() => {
    const patch = readFormDraft<T>(storageKey);
    if (patch) setValue((prev) => mergeFormDraft(prev, patch));
    hydrated.current = true;
  }, [storageKey]);

  useEffect(() => {
    if (!hydrated.current) return;
    writeFormDraft(storageKey, value);
  }, [storageKey, value]);

  const clearDraft = () => clearFormDraft(storageKey);

  return { value, setValue, clearDraft };
}
