/** localStorage helpers for form draft persistence (tested in formDraftStorage.test.ts). */

export function readFormDraft<T extends Record<string, unknown>>(storageKey: string): Partial<T> | null {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return null;
    return JSON.parse(raw) as Partial<T>;
  } catch {
    return null;
  }
}

export function writeFormDraft<T extends Record<string, unknown>>(storageKey: string, value: T): void {
  try {
    localStorage.setItem(storageKey, JSON.stringify(value));
  } catch {
    // ignore quota errors
  }
}

export function clearFormDraft(storageKey: string): void {
  try {
    localStorage.removeItem(storageKey);
  } catch {
    // ignore storage errors
  }
}

export function mergeFormDraft<T extends Record<string, unknown>>(initial: T, patch: Partial<T> | null): T {
  if (!patch) return initial;
  return { ...initial, ...patch };
}
