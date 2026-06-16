/**
 * @vitest-environment jsdom
 */
import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { useFormDraft } from "./useFormDraft";

const KEY = "test-form-draft-hook";

afterEach(() => {
  localStorage.removeItem(KEY);
});

describe("useFormDraft", () => {
  it("hydrates from localStorage on mount", async () => {
    localStorage.setItem(KEY, JSON.stringify({ title: "saved" }));

    const { result } = renderHook(() =>
      useFormDraft(KEY, { title: "", body: "" }),
    );

    await waitFor(() => {
      expect(result.current.value.title).toBe("saved");
    });
    expect(result.current.value.body).toBe("");
  });

  it("persists updates after hydration", async () => {
    const { result } = renderHook(() =>
      useFormDraft(KEY, { title: "", body: "" }),
    );

    await waitFor(() => {
      expect(result.current.value.title).toBe("");
    });

    act(() => {
      result.current.setValue({ title: "draft", body: "text" });
    });

    await waitFor(() => {
      const stored = JSON.parse(localStorage.getItem(KEY) ?? "{}");
      expect(stored.title).toBe("draft");
      expect(stored.body).toBe("text");
    });
  });

  it("clearDraft removes storage", async () => {
    localStorage.setItem(KEY, JSON.stringify({ title: "old" }));

    const { result } = renderHook(() =>
      useFormDraft(KEY, { title: "", body: "" }),
    );

    await waitFor(() => {
      expect(result.current.value.title).toBe("old");
    });

    act(() => {
      result.current.clearDraft();
    });

    expect(localStorage.getItem(KEY)).toBeNull();
  });
});
