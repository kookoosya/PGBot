import { describe, expect, it, beforeEach } from "vitest";
import {
  CLASSIFIEDS_DRAFT_KEY,
  CLASSIFIED_FORM_INITIAL,
} from "@/lib/classifiedForm";
import {
  clearFormDraft,
  mergeFormDraft,
  readFormDraft,
  writeFormDraft,
} from "@/lib/formDraftStorage";

const storage = new Map<string, string>();

function mockLocalStorage() {
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => {
        storage.set(key, value);
      },
      removeItem: (key: string) => {
        storage.delete(key);
      },
      clear: () => storage.clear(),
    },
  });
}

describe("formDraftStorage", () => {
  beforeEach(() => {
    storage.clear();
    mockLocalStorage();
  });

  it("round-trips draft JSON", () => {
    writeFormDraft(CLASSIFIEDS_DRAFT_KEY, { ...CLASSIFIED_FORM_INITIAL, title: "Дрова" });
    const draft = readFormDraft<typeof CLASSIFIED_FORM_INITIAL>(CLASSIFIEDS_DRAFT_KEY);
    expect(draft?.title).toBe("Дрова");
  });

  it("mergeFormDraft overlays saved fields", () => {
    const merged = mergeFormDraft(CLASSIFIED_FORM_INITIAL, { title: "Услуга", phone: "+7999" });
    expect(merged.title).toBe("Услуга");
    expect(merged.category).toBe(CLASSIFIED_FORM_INITIAL.category);
  });

  it("clearFormDraft removes key", () => {
    writeFormDraft(CLASSIFIEDS_DRAFT_KEY, CLASSIFIED_FORM_INITIAL);
    clearFormDraft(CLASSIFIEDS_DRAFT_KEY);
    expect(readFormDraft(CLASSIFIEDS_DRAFT_KEY)).toBeNull();
  });

  it("readFormDraft returns null for broken JSON", () => {
    storage.set(CLASSIFIEDS_DRAFT_KEY, "{not-json");
    expect(readFormDraft(CLASSIFIEDS_DRAFT_KEY)).toBeNull();
  });
});
